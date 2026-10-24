"""Transport adapters; no implicit session/bearer principal fallback."""

import json
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import logout as django_logout
from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError, transaction
from django.middleware.csrf import CsrfViewMiddleware
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables

from .flow_security import FlowProblem
from .models import AuthSession
from .registration import event, flow_uuid
from .registration_views import reply, protected_marker, MESSAGES
from . import sessions

MESSAGES.update(
    {
        "SESSION_INVALID": "The session is invalid or no longer available.",
        "INVALID_CREDENTIALS": "The credentials are invalid.",
        "MFA_REQUIRED": "Multi-factor authentication is required.",
        "STEP_UP_REQUIRED": "Operation-bound recent assurance is required.",
        "NOT_FOUND": "The requested resource was not found.",
    }
)


def mixed(request):
    if (
        settings.SESSION_COOKIE_NAME in request.COOKIES
        and "HTTP_AUTHORIZATION" in request.META
    ):
        return FlowProblem("AMBIGUOUS_CREDENTIALS")


def browser_csrf(request):
    _, expected = sessions.portal(request)
    origin = request.META.get("HTTP_ORIGIN")
    if not origin:
        try:
            parsed = urlsplit(request.META.get("HTTP_REFERER", ""))
            origin = f"https://{parsed.netloc}" if parsed.scheme == "https" else None
        except ValueError:
            origin = None
    if origin != expected:
        return FlowProblem("CSRF_FAILED", 403)
    if (
        CsrfViewMiddleware(lambda r: None).process_view(
            request, protected_marker, (), {}
        )
        is not None
    ):
        return FlowProblem("CSRF_FAILED", 403)


def native(request):
    return not (
        settings.SESSION_COOKIE_NAME in request.COOKIES
        or "HTTP_AUTHORIZATION" in request.META
        or any(
            name in request.META
            for name in ("HTTP_ORIGIN", "HTTP_REFERER", "HTTP_SEC_FETCH_SITE")
        )
    )


@sensitive_variables()
def body(request, required, optional=()):
    if (
        request.content_type != "application/json"
        or int(request.META.get("CONTENT_LENGTH") or 0) > 8192
        or len(request.body) > 8192
    ):
        raise FlowProblem("VALIDATION_ERROR")
    value = json.loads(request.body)
    if (
        not isinstance(value, dict)
        or not set(required) <= set(value)
        or set(value) - set(required) - set(optional)
        or any(not isinstance(v, str) for v in value.values())
    ):
        raise FlowProblem("VALIDATION_ERROR")
    return value


def endpoint(operation):
    @csrf_exempt
    @sensitive_variables()
    def view(request, session_id=None):
        problem = mixed(request)
        if problem:
            return reply(problem)
        method = (
            "GET"
            if operation in ("me", "list")
            else "DELETE" if operation == "revoke" else "POST"
        )
        if request.method != method:
            response = reply(FlowProblem("METHOD_NOT_ALLOWED", 405))
            response["Allow"] = method
            return response
        try:
            sessions.configured()
            if not request.is_secure():
                return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
            if operation == "web_login":
                if "HTTP_AUTHORIZATION" in request.META:
                    return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
                portal_name, _ = sessions.portal(request)
                problem = browser_csrf(request)
                if problem:
                    return reply(problem)
            elif operation in ("mobile_login", "refresh"):
                if not native(request):
                    return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
                portal_name = "mobile"
            elif (
                settings.SESSION_COOKIE_NAME in request.COOKIES
                and request.method not in ("GET", "HEAD")
            ):
                problem = browser_csrf(request)
                if problem:
                    return reply(problem)
            if operation in ("web_login", "mobile_login"):
                data = body(request, {"email", "password"}, {"device_label"})
                label = data.get("device_label", "")
                if len(label) > 100 or any(ord(c) < 32 or ord(c) == 127 for c in label):
                    return reply(FlowProblem("VALIDATION_ERROR"))
                if len(data["password"]) > 128:
                    return reply(FlowProblem("INVALID_CREDENTIALS", 401))
                return reply(
                    sessions.login(
                        request,
                        data["email"],
                        data["password"],
                        label,
                        "web" if operation == "web_login" else "mobile",
                        portal_name,
                    )
                )
            if operation == "refresh":
                data = body(request, {"refresh_token"})
                return reply(
                    sessions.refresh(
                        data["refresh_token"],
                        request.META.get("REMOTE_ADDR", "unknown"),
                    )
                )
            snapshot = sessions.locate(request)
            if not snapshot:
                return reply(sessions.invalid())
            # Buffer bounded command bodies BEFORE acquiring owner locks. Do
            # not hold an account lock while waiting on client upload/network.
            if operation not in ("me", "list"):
                if (
                    int(request.META.get("CONTENT_LENGTH") or 0) > 8192
                    or len(request.body) > 8192
                ):
                    return reply(FlowProblem("VALIDATION_ERROR"))
            with transaction.atomic():
                context = sessions.authenticate_locked(request, snapshot)
                if not context:
                    return reply(sessions.invalid())
                user, session = context
                if operation == "me":
                    result = sessions.envelope(user, session)
                    result["email_verified"] = True
                    return reply(result)
                if operation == "list":
                    now = timezone.now()
                    rows = AuthSession.objects.filter(
                        user=user,
                        revoked_at__isnull=True,
                        auth_epoch=user.auth_epoch,
                        absolute_expires_at__gt=now,
                    ).order_by("id")
                    return reply(
                        {
                            "results": [
                                {
                                    "id": str(row.pk),
                                    "device_label": row.device_label,
                                    "transport": row.transport,
                                    "created_at": row.created_at.isoformat(),
                                    "last_interactive_at": row.last_interactive_at.isoformat(),
                                    "is_current": row.pk == session.pk,
                                }
                                for row in rows
                                if row.portal in sessions.DURATIONS
                                and now < sessions.idle_deadline(row)
                            ]
                        }
                    )
                if operation in ("all", "revoke"):
                    if operation == "revoke":
                        target = flow_uuid(session_id)
                        if (
                            not target
                            or not AuthSession.objects.filter(
                                pk=target, user=user
                            ).exists()
                        ):
                            return reply(FlowProblem("NOT_FOUND", 404))
                    body(request, {"assurance_proof"})
                    # No authenticated password shortcut, cached MFA, generic
                    # proof or future placeholder can bypass operation assurance.
                    return reply(FlowProblem("STEP_UP_REQUIRED", 403))
                if request.body and body(request, set()) != {}:
                    return reply(FlowProblem("VALIDATION_ERROR"))
                if not sessions.authenticate_locked(request, snapshot):
                    return reply(sessions.invalid())
                now = timezone.now()
                session.revoked_at, session.revocation_reason = now, "logout"
                session.save(update_fields=["revoked_at", "revocation_reason"])
                event("auth.logout", user=user, session=session)
                if session.transport == "web":
                    django_logout(request)
                return reply(None, 204)
        except FlowProblem as exc:
            return reply(exc)
        except (ValueError, UnicodeError, RecursionError, RequestDataTooBig):
            return reply(FlowProblem("VALIDATION_ERROR"))
        except DatabaseError:
            return reply(FlowProblem("AUTH_UNAVAILABLE", 503))

    return view


web_login = endpoint("web_login")
mobile_login = endpoint("mobile_login")
refresh = endpoint("refresh")
me = endpoint("me")
logout = endpoint("logout")
logout_all = endpoint("all")
session_list = endpoint("list")
revoke = endpoint("revoke")
