"""Unavailable privileged adapters, not a writable operator authorization system."""

from django.db import connection, transaction
from rest_framework.response import Response
from accounts import sessions
from accounts.flow_security import FlowProblem
from accounts.registration import spend
from accounts.session_authentication import PersonalAuthentication
from .registry_views import RegistryView, problem
from .onboarding_policy import POLICY
from .controlled_onboarding import command_available


class ControlledOnboardingView(RegistryView):
    command = "records"
    http_method_names = ["get", "post", "patch"]

    def execute(self, request, pk=None):
        raw = request._request
        sessions.configured()
        if "HTTP_AUTHORIZATION" in raw.META and any(
            k in raw.META
            for k in ("HTTP_ORIGIN", "HTTP_REFERER", "HTTP_SEC_FETCH_SITE")
        ):
            raise FlowProblem("TRANSPORT_NOT_ALLOWED")
        limited = spend(raw.META.get("REMOTE_ADDR"), "controlled-onboarding")
        if limited:
            raise limited
        with transaction.atomic(durable=True):
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '2s'")
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            identity = PersonalAuthentication().authenticate(request)
            if identity is None:
                raise FlowProblem("SESSION_INVALID", 401)
            user, _ = identity
            if user.recovery_hold_state != "clear":
                raise FlowProblem("RECOVERY_RESTRICTED", 403)
            if request.query_params:
                raise FlowProblem("VALIDATION_ERROR")
            if request.method == "GET" and self.command == "requirements":
                if raw.body:
                    raise FlowProblem("VALIDATION_ERROR")
                if PersonalAuthentication().authenticate(request) is None:
                    raise FlowProblem("SESSION_INVALID", 401)
                return Response(POLICY)
            # No object lookup, body read/parse, side effect, token or role inference.
            if not command_available(user, self.command):
                raise FlowProblem("CONTROLLED_ONBOARDING_UNAVAILABLE", 503)
            # No writable implementation even if a caller monkeypatches a boolean.
            raise FlowProblem("CONTROLLED_ONBOARDING_UNAVAILABLE", 503)

    def get(self, request, pk=None):
        if self.command not in ("requirements", "records", "record"):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)

    def post(self, request, pk=None):
        if self.command in ("requirements", "record"):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)

    def patch(self, request, pk=None):
        if self.command != "record":
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)
