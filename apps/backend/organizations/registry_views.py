"""Claimant-only DRF adapters. Authentication and mutation share a User-first lock.

All new routes default off; staging/production fail closed even on unsafe settings
injection. No real evidence intake, review, publication or grant operations exist.
"""

import uuid
import json
from django.conf import settings
from django.core.exceptions import RequestDataTooBig
from django.db import DatabaseError, IntegrityError, connection, transaction
from django.utils.cache import patch_vary_headers
from rest_framework.exceptions import APIException
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts import sessions
from accounts.flow_security import FlowProblem
from accounts.registration import spend
from accounts.session_authentication import PersonalAuthentication
from access.views import FixedJSON
from . import registry
from .onboarding_policy import historical_test_exercise
from .models import OrganizationDraft, OrganizationClaim, RegistryEvent
from .registry_serializers import (
    DraftInput,
    DraftEdit,
    RevisionInput,
    ClaimInput,
    DraftOutput,
    ClaimOutput,
    EventOutput,
    normalize,
)
from .views import PublicOrganizationSerializer


def problem(code, status):
    exc = APIException(
        {
            "error": {
                "code": code,
                "message": "The registry request could not be completed.",
                "field_errors": {},
                "request_id": str(uuid.uuid4()),
            }
        }
    )
    exc.status_code = status
    return exc


class RegistryParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result

        # The adapter bounds the raw body before parsing; reject duplicate JSON keys.
        return json.loads(stream.read().decode("utf-8"), object_pairs_hook=unique)


class RegistryJSON(FixedJSON):
    def select_parser(self, request, parsers):
        return parsers[0] if request.content_type == "application/json" else None


class RegistryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [RegistryParser]
    renderer_classes = [JSONRenderer]
    content_negotiation_class = RegistryJSON
    http_method_names = ["get", "post", "patch"]
    resource = None
    command = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not settings.PWC_REGISTRY_ENABLED or settings.PWC_ENVIRONMENT not in {
            "development",
            "test",
        }:
            raise problem("AUTH_UNAVAILABLE", 503)

    def handle_exception(self, exc):
        if isinstance(exc, FlowProblem):
            exc = problem(exc.code, exc.status)
        elif isinstance(exc, IntegrityError):
            exc = problem("STATE_CONFLICT", 409)
        elif isinstance(exc, DatabaseError):
            exc = problem("AUTH_UNAVAILABLE", 503)
        elif isinstance(
            exc,
            (RequestDataTooBig, UnicodeError, ValueError, TypeError, RecursionError),
        ):
            exc = problem("VALIDATION_ERROR", 400)
        elif isinstance(exc, APIException):
            # Never echo serializer instances, contacts or exception/DB details.
            if not (isinstance(exc.detail, dict) and "error" in exc.detail):
                exc = problem(
                    "METHOD_NOT_ALLOWED"
                    if exc.status_code == 405
                    else "VALIDATION_ERROR",
                    exc.status_code,
                )
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "no-referrer"
        patch_vary_headers(response, ("Cookie", "Authorization"))
        if response.status_code == 401:
            response["WWW-Authenticate"] = "Bearer"
        return response

    def execute(self, request, pk=None):
        raw = request._request
        # Shared persisted IP budget commits before any workflow transaction.
        sessions.configured()
        if "HTTP_AUTHORIZATION" in raw.META and any(
            k in raw.META
            for k in ("HTTP_ORIGIN", "HTTP_REFERER", "HTTP_SEC_FETCH_SITE")
        ):
            raise FlowProblem("TRANSPORT_NOT_ALLOWED")
        limited = spend(raw.META.get("REMOTE_ADDR"), "registry")
        if limited:
            raise limited
        with transaction.atomic(durable=True):
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL lock_timeout = '2s'")
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            identity = PersonalAuthentication().authenticate(request)
            if identity is None:
                raise FlowProblem("SESSION_INVALID", 401)
            user, session = identity
            if user.recovery_hold_state != "clear":
                raise FlowProblem("RECOVERY_RESTRICTED", 403)
            if (
                request.method != "GET"
                and self.command != "withdraw"
                and not historical_test_exercise()
            ):
                raise FlowProblem("SELF_SERVICE_UNAVAILABLE", 503)
            allowed_query = (
                {"q", "city", "cursor"}
                if self.resource == "search"
                else {"cursor"}
                if pk is None and request.method == "GET" or self.command == "history"
                else set()
            )
            if (
                set(request.query_params) - allowed_query
                or any(
                    len(request.query_params.getlist(k)) != 1
                    for k in request.query_params
                )
                or any(
                    len(v) > (1024 if k == "cursor" else 250)
                    for k, v in request.query_params.items()
                )
            ):
                raise FlowProblem("VALIDATION_ERROR")
            if request.method == "GET":
                if raw.body:
                    raise FlowProblem("VALIDATION_ERROR")
                data = self.read(request, user, pk)
            else:
                if len(raw.body) > 8192:
                    raise FlowProblem("VALIDATION_ERROR")
                schema = (
                    (DraftInput if self.resource == "draft" else ClaimInput)
                    if pk is None
                    else DraftEdit
                    if request.method == "PATCH"
                    else RevisionInput
                )
                parsed = schema(data=request.data)
                parsed.is_valid(raise_exception=True)
                data = dict(parsed.validated_data)
                if pk is None:
                    try:
                        key = uuid.UUID(request.headers.get("Idempotency-Key", ""))
                    except ValueError:
                        raise FlowProblem("VALIDATION_ERROR") from None
                    data = registry.create(self.resource, data, key, user, session)
                else:
                    data = registry.change(
                        self.resource,
                        pk,
                        "edit" if request.method == "PATCH" else self.command,
                        data,
                        user,
                        session,
                    )
            # Bound decision validity at completion; no idle renewal or proof reuse.
            if PersonalAuthentication().authenticate(request) is None:
                raise FlowProblem("SESSION_INVALID", 401)
            return Response(
                data, status=201 if request.method == "POST" and pk is None else 200
            )

    def read(self, request, user, pk):
        if self.resource == "search":
            q, city = (
                request.query_params.get("q", ""),
                request.query_params.get("city", ""),
            )
            if len(normalize(q)) < 2:
                raise FlowProblem("VALIDATION_ERROR")
            return registry.page(
                registry.matches(q, city),
                request.query_params,
                user,
                "search:"
                + registry.digest({"q": normalize(q), "city": normalize(city)}),
                PublicOrganizationSerializer,
            )
        model, output = (
            (OrganizationDraft, DraftOutput)
            if self.resource == "draft"
            else (OrganizationClaim, ClaimOutput)
        )
        if pk is None:
            return registry.page(
                model.objects.filter(claimant=user),
                request.query_params,
                user,
                self.resource,
            )
        value = registry.own(model, user, pk)
        if self.command == "history":
            history = RegistryEvent.objects.filter(actor=user, **{self.resource: value})
            # Events are UUID-keyset paginated; revision establishes causal order.
            return registry.page(
                history,
                request.query_params,
                user,
                self.resource + ":history:" + str(pk),
                EventOutput,
            )
        return output(value).data

    def get(self, request, pk=None):
        if self.command not in (None, "history"):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)

    def post(self, request, pk=None):
        if (
            self.resource == "search"
            or self.command == "history"
            or pk is not None
            and self.command is None
        ):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)

    def patch(self, request, pk=None):
        if self.resource != "draft" or pk is None or self.command is not None:
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk)
