"""Browser-only invitation ceremonies; never issuance or live activation."""

import json

from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_variables

from . import personal_invitations as invitations
from . import mfa
from .flow_security import FlowProblem
from .registration_views import reply
from .session_views import browser_csrf, body


def endpoint(operation):
    @csrf_exempt  # Explicit CSRF checks protect anonymous recipients too.
    @sensitive_variables()
    def view(request):
        try:
            invitations.gate()
            mfa.configured()
            if not request.is_secure() or "HTTP_AUTHORIZATION" in request.META:
                return reply(FlowProblem("TRANSPORT_NOT_ALLOWED"))
            if request.method != "POST":
                response = reply(FlowProblem("METHOD_NOT_ALLOWED", 405))
                response["Allow"] = "POST"
                return response
            denial = browser_csrf(request)
            if denial:
                return reply(denial)
            extra = {
                "request-proof": (),
                "confirm-email": ("proof",),
                "password": ("enrollment_control", "password"),
                "activate": ("enrollment_control", "code"),
            }[operation]
            data = body(request, {"invitation_id", "token", "recipient", *extra})
            base = [data["invitation_id"], data["token"], data["recipient"]]
            ip = request.META.get("REMOTE_ADDR", "unknown")
            functions = {
                "request-proof": invitations.request_confirmation,
                "confirm-email": invitations.confirm_email,
                "password": invitations.set_password,
                "activate": invitations.activate,
            }
            result = functions[operation](*base, *(data[key] for key in extra), ip)
            return reply(
                result,
                status={"request-proof": 202, "activate": 201}.get(operation, 200),
            )
        except FlowProblem as error:
            return reply(error)
        except (ValueError, TypeError, json.JSONDecodeError, RequestDataTooBig):
            return reply(FlowProblem("VALIDATION_ERROR"))
        except DatabaseError:
            return reply(FlowProblem("AUTH_UNAVAILABLE", 503))

    return view
