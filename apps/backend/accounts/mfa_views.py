"""Explicit transport adapters, sharing 03A.3's live authority and envelopes."""

import json
from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import transaction, DatabaseError
from django.middleware.csrf import rotate_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables
from . import mfa, sessions
from .flow_security import FlowProblem
from .models import User, MfaFactor
from .registration import spend
from .registration_views import reply, MESSAGES
from .session_views import mixed, browser_csrf, native

MESSAGES.update(
    {
        "RECOVERY_RESTRICTED": "Recovery assurance does not permit this operation.",
        "STATE_CONFLICT": "The account security state changed.",
    }
)


@sensitive_variables()
def payload(request, required, optional=(), nested=()):
    if (
        request.content_type != "application/json"
        or int(request.META.get("CONTENT_LENGTH") or 0) > 8192
        or len(request.body) > 8192
    ):
        raise FlowProblem("VALIDATION_ERROR")
    data = json.loads(request.body)
    if (
        not isinstance(data, dict)
        or not set(required) <= set(data)
        or set(data) - set(required) - set(optional)
        or any(
            not isinstance(value, dict if key in nested else str)
            for key, value in data.items()
        )
    ):
        raise FlowProblem("VALIDATION_ERROR")
    return data


def endpoint(operation):
    @csrf_exempt
    @sensitive_variables()
    def view(request):
        denial = mixed(request)
        if denial:
            return reply(denial)
        method = "GET" if operation == "status" else "POST"
        if request.method != method:
            response = reply(FlowProblem("METHOD_NOT_ALLOWED", 405))
            response["Allow"] = method
            return response
        prior_web_session = None
        try:
            mfa.configured()
            if not request.is_secure():
                return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
            if operation in ("web_confirm", "mobile_confirm"):
                if operation == "web_confirm":
                    if "HTTP_AUTHORIZATION" in request.META:
                        return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
                    portal, _ = sessions.portal(request)
                    denial = browser_csrf(request)
                    if denial:
                        return reply(denial)
                else:
                    portal = "mobile"
                    if not native(request):
                        return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
                data = payload(
                    request, {"challenge_id", "preauth_control", "method", "code"}
                )
                denial = spend(request.META.get("REMOTE_ADDR", "unknown"), "mfa_login")
                return reply(
                    denial
                    if denial
                    else mfa.complete_login(
                        request,
                        data,
                        "web" if operation == "web_confirm" else "mobile",
                        portal,
                    )
                )
            if settings.SESSION_COOKIE_NAME in request.COOKIES and method == "POST":
                denial = browser_csrf(request)
                if denial:
                    return reply(denial)
            fields = {
                "intent": (
                    {"operation", "context", "command"},
                    {"object_id", "version"},
                    {"context", "command"},
                ),
                "step": ({"intent_id", "password"}, {"totp_code"}, ()),
                "enroll": ({"assurance_proof"}, (), ()),
                "confirm": ({"enrollment_id", "code"}, (), ()),
                "remove": ({"assurance_proof"}, (), ()),
                "rotate": ({"assurance_proof"}, (), ()),
                "clear": ({"intent_id", "password", "totp_code"}, (), ()),
            }
            data = payload(request, *fields[operation]) if method == "POST" else {}
            if method == "POST":
                denial = spend(request.META.get("REMOTE_ADDR", "unknown"), "mfa")
                if denial:
                    return reply(denial)
            snapshot = sessions.locate(request)
            if not snapshot:
                return reply(sessions.invalid())
            with transaction.atomic():
                owner = (
                    User.objects.select_for_update()
                    .filter(pk=snapshot[0].user_id)
                    .first()
                )
                if not owner:
                    return reply(sessions.invalid())
                list(
                    MfaFactor.objects.select_for_update()
                    .filter(user=owner)
                    .order_by("id")
                )
                context = sessions.authenticate_locked(request, snapshot)
                if not context:
                    return reply(sessions.invalid())
                user, session = context
                if operation == "status":
                    factor = mfa.active(user)
                    return reply(
                        {
                            "enabled": bool(factor),
                            "pending": MfaFactor.objects.filter(
                                user=user,
                                state="pending",
                                expires_at__gt=mfa.timezone.now(),
                            ).exists(),
                            "recovery_hold_state": user.recovery_hold_state,
                        }
                    )
                # Credentials may expire during hashing, OTP verification or DB
                # waits. Check their original deadline after the action, before
                # commit; rollback provisional proofs/factor changes on expiry.
                # Do not re-authenticate after mutations: removal/replacement
                # intentionally revoke the caller, while enrollment promotes it.
                deadline = sessions.authorization_deadline(session, snapshot)
                if deadline is None:
                    return reply(sessions.invalid())
                with transaction.atomic():
                    response = personal_command(operation, user, session, data)
                    if (
                        operation in ("step", "clear")
                        and response.status_code < 400
                        and session.transport == "web"
                    ):
                        # Rotate the cookie, not the logical session: exact
                        # intent/proof bindings stay valid, old cookies do not.
                        # Both Django's DB session and registry mapping share
                        # this savepoint and the final original-deadline gate.
                        prior_web_session = request.session.__class__(
                            request.session.session_key
                        )
                        request.session.cycle_key()
                        request.session.save()
                        session.web_key_digest = sessions.web_digest(
                            request.session.session_key
                        )
                        session.save(update_fields=["web_key_digest"])
                    if mfa.timezone.now() >= deadline:
                        transaction.set_rollback(True)
                        if prior_web_session is not None:
                            request.session = prior_web_session
                        return reply(sessions.invalid())
                if prior_web_session is not None:
                    rotate_token(request)
                return response
        except FlowProblem as exc:
            return reply(exc)
        except (ValueError, UnicodeError, RecursionError, RequestDataTooBig):
            return reply(FlowProblem("VALIDATION_ERROR"))
        except DatabaseError:
            # A rolled-back cycle_key no longer exists in PostgreSQL. Restore
            # the request store too, or SessionMiddleware's later save raises
            # SessionInterrupted and replaces our fail-closed JSON response.
            if prior_web_session is not None:
                request.session = prior_web_session
            return reply(FlowProblem("AUTH_UNAVAILABLE", 503))

    return view


@sensitive_variables()
def personal_command(operation, user, session, data):
    """Dispatch only inside the authenticated owner transaction/savepoint."""
    if operation == "intent":
        return reply(mfa.intent_request(user, session, data), 201)
    if operation == "step":
        return reply(mfa.step_up(user, session, data))
    if operation == "enroll":
        return reply(
            mfa.enrollment_request(user, session, data["assurance_proof"]),
            201,
        )
    if operation == "confirm":
        return reply(mfa.enrollment_confirm(user, session, data))
    if operation == "remove":
        return reply(mfa.remove(user, session, data["assurance_proof"]), 204)
    if operation == "rotate":
        denial = mfa.consume(
            user,
            session,
            "mfa.recovery_codes.rotate",
            {},
            data["assurance_proof"],
        )
        return reply(
            denial if denial else {"recovery_codes": mfa.codes(user, mfa.active(user))}
        )
    if operation == "clear":
        return reply(mfa.clear_hold(user, session, data), 204)
    return reply(FlowProblem("VALIDATION_ERROR"))
