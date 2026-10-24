"""Public, proof-based auth endpoints only. No DRF/session login side effects."""

import json
import uuid
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError
from django.http import JsonResponse
from django.middleware.csrf import CsrfViewMiddleware, get_token
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables

from .flow_security import FlowProblem
from .registration import confirm_flow, request_flow, resend_flow

MESSAGES = {
    "CHALLENGE_INVALID": "The proof is invalid or no longer available.",
    "VALIDATION_ERROR": "Check the supplied fields.",
    "RATE_LIMITED": "Please retry later.",
    "AUTH_UNAVAILABLE": "Authentication service is unavailable.",
    "CSRF_FAILED": "Browser request verification failed.",
    "AMBIGUOUS_CREDENTIALS": "Supply only one credential transport.",
    "TRANSPORT_NOT_ALLOWED": "This endpoint does not accept these credentials.",
    "METHOD_NOT_ALLOWED": "This method is not available.",
}


def reply(value, status=200):
    if isinstance(value, FlowProblem):
        response = JsonResponse(
            {
                "error": {
                    "code": value.code,
                    "message": MESSAGES[value.code],
                    "field_errors": value.fields,
                    "request_id": str(uuid.uuid4()),
                }
            },
            status=value.status,
        )
        if value.retry_after:
            response["Retry-After"] = str(value.retry_after)
    elif status == 204:
        response = JsonResponse({}, status=204)
        response.content = b""
    else:
        response = JsonResponse(value, status=status)
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


def credential_problem(request):
    auth = "HTTP_AUTHORIZATION" in request.META
    if auth and settings.SESSION_COOKIE_NAME in request.COOKIES:
        return FlowProblem("AMBIGUOUS_CREDENTIALS")
    if auth:
        return FlowProblem("TRANSPORT_NOT_ALLOWED")


def browser_request(request):
    return bool(
        request.META.get("HTTP_ORIGIN")
        or request.META.get("HTTP_REFERER")
        or request.META.get("HTTP_SEC_FETCH_SITE")
        or settings.SESSION_COOKIE_NAME in request.COOKIES
    )


def protected_marker(request):
    pass


def public_command(operation, purpose):
    fields = {
        "request": {"email"},
        "resend": {"flow_id", "flow_control"},
        "confirm": {
            "flow_id",
            "proof",
            "password" if purpose == "registration" else "new_password",
        },
    }[operation]

    @csrf_exempt  # Native cookie-less JSON has no ambient authority. Browser
    @sensitive_variables()  # mode is explicitly checked below, even anonymously.
    def view(request):
        problem = credential_problem(request)
        if problem:
            return reply(problem)
        if request.method != "POST":
            response = reply(FlowProblem("METHOD_NOT_ALLOWED", 405))
            response["Allow"] = "POST"
            return response
        # Public proofs and new passwords are secrets too. Do not accept
        # plaintext ingress or trust an arbitrary forwarded-proto header.
        if not request.is_secure():
            return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
        if browser_request(request):
            origin = request.META.get("HTTP_ORIGIN")
            allowed = {f"{request.scheme}://{request.get_host()}"} | {
                value for value in settings.CSRF_TRUSTED_ORIGINS if "*" not in value
            }
            if not origin:
                try:
                    referer = urlsplit(request.META.get("HTTP_REFERER", ""))
                    origin = (
                        f"https://{referer.netloc}"
                        if referer.scheme == "https"
                        else None
                    )
                except ValueError:
                    origin = None
            if origin not in allowed:
                return reply(FlowProblem("CSRF_FAILED", 403))
            denied = CsrfViewMiddleware(lambda r: None).process_view(
                request, protected_marker, (), {}
            )
            if denied is not None:
                return reply(FlowProblem("CSRF_FAILED", 403))
        if request.content_type != "application/json":
            return reply(FlowProblem("VALIDATION_ERROR"))
        try:
            if (
                int(request.META.get("CONTENT_LENGTH") or 0) > 8192
                or len(request.body) > 8192
            ):
                return reply(FlowProblem("VALIDATION_ERROR"))
            data = json.loads(request.body)
            if (
                not isinstance(data, dict)
                or set(data) != fields
                or any(not isinstance(v, str) for v in data.values())
            ):
                return reply(FlowProblem("VALIDATION_ERROR"))
            # No forwarded-header trust until production proxy policy is approved.
            ip = request.META.get("REMOTE_ADDR", "unknown")
            if operation == "request":
                result = request_flow(purpose, data["email"], ip)
            elif operation == "resend":
                result = resend_flow(purpose, data["flow_id"], data["flow_control"], ip)
            else:
                result = confirm_flow(
                    purpose,
                    data["flow_id"],
                    data["proof"],
                    data["password" if purpose == "registration" else "new_password"],
                    ip,
                )
            status = (
                202
                if operation in ("request", "resend")
                else (201 if purpose == "registration" else 204)
            )
            return reply(result, status)
        except FlowProblem as exc:
            return reply(exc)
        except (ValueError, UnicodeError, RecursionError, RequestDataTooBig):
            return reply(FlowProblem("VALIDATION_ERROR"))
        except DatabaseError:
            return reply(FlowProblem("AUTH_UNAVAILABLE", 503))

    return view


@csrf_exempt
def csrf_bootstrap(request):
    problem = credential_problem(request)
    if problem:
        return reply(problem)
    if request.method != "GET":
        response = reply(FlowProblem("METHOD_NOT_ALLOWED", 405))
        response["Allow"] = "GET"
        return response
    return reply({"csrf_token": get_token(request)})


registration_request = public_command("request", "registration")
registration_confirm = public_command("confirm", "registration")
registration_resend = public_command("resend", "registration")
reset_request = public_command("request", "reset")
reset_confirm = public_command("confirm", "reset")
reset_resend = public_command("resend", "reset")
