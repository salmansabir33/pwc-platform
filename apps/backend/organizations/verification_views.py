"""04B owner-scoped synthetic preparation and permanently unavailable file adapters."""

import uuid
from django.conf import settings
from django.db import connection, transaction
from rest_framework.response import Response
from accounts import sessions
from accounts.flow_security import FlowProblem
from accounts.registration import spend
from accounts.session_authentication import PersonalAuthentication
from .registry_views import RegistryView, problem
from .registry_serializers import RevisionInput
from . import registry, verification
from .models import VerificationCase, EvidencePreparation, VerificationEvent
from .verification_serializers import (
    CaseInput,
    CaseOutput,
    PreparationInput,
    PreparationEdit,
    PreparationOutput,
    HistoryOutput,
)


class VerificationView(RegistryView):
    command = "case"
    http_method_names = ["get", "post", "patch"]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not settings.PWC_VERIFICATION_ENABLED:
            raise problem("AUTH_UNAVAILABLE", 503)

    def execute(self, request, pk=None, item_id=None):
        raw = request._request
        sessions.configured()
        if "HTTP_AUTHORIZATION" in raw.META and any(
            k in raw.META
            for k in ("HTTP_ORIGIN", "HTTP_REFERER", "HTTP_SEC_FETCH_SITE")
        ):
            raise FlowProblem("TRANSPORT_NOT_ALLOWED")
        limited = spend(raw.META.get("REMOTE_ADDR"), "verification")
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
            paged = request.method == "GET" and (
                pk is None
                or self.command == "history"
                or self.command == "preparation"
                and item_id is None
            )
            if set(request.query_params) - ({"cursor"} if paged else set()) or any(
                len(request.query_params.getlist(k)) != 1
                or len(request.query_params[k]) > 1024
                for k in request.query_params
            ):
                raise FlowProblem("VALIDATION_ERROR")
            if self.command == "reviewer-queue":
                # No IAM bootstrap/assignment or private case enumeration exists.
                raise FlowProblem("REVIEW_UNAVAILABLE", 503)
            case = verification.own(user, pk) if pk else None
            if self.command in ("upload", "download"):
                if (
                    item_id is not None
                    and not EvidencePreparation.objects.filter(
                        case=case, pk=item_id
                    ).exists()
                ):
                    registry.fail("NOT_FOUND", 404)
                # Do not parse, read, scan, persist or log request body/filenames.
                raise FlowProblem("EVIDENCE_UNAVAILABLE", 503)
            if request.method == "GET":
                if raw.body:
                    raise FlowProblem("VALIDATION_ERROR")
                if case is None:
                    result = registry.page(
                        VerificationCase.objects.filter(claimant=user),
                        request.query_params,
                        user,
                        "verification:cases",
                        CaseOutput,
                    )
                elif self.command == "requirements":
                    result = verification.requirements(case)
                elif self.command == "history":
                    result = registry.page(
                        VerificationEvent.objects.filter(case=case, actor=user),
                        request.query_params,
                        user,
                        "verification:history:" + str(pk),
                        HistoryOutput,
                    )
                elif self.command == "preparation" and item_id is not None:
                    marker = EvidencePreparation.objects.filter(
                        case=case, pk=item_id
                    ).first()
                    if marker is None:
                        registry.fail("NOT_FOUND", 404)
                    result = PreparationOutput(marker).data
                elif self.command == "preparation":
                    result = registry.page(
                        EvidencePreparation.objects.filter(case=case),
                        request.query_params,
                        user,
                        "verification:preparation:" + str(pk),
                        PreparationOutput,
                    )
                else:
                    result = CaseOutput(case).data
            else:
                if len(raw.body) > 8192:
                    raise FlowProblem("VALIDATION_ERROR")
                schema = (
                    CaseInput
                    if case is None
                    else PreparationEdit
                    if item_id
                    else PreparationInput
                    if self.command == "preparation"
                    else RevisionInput
                )
                parsed = schema(data=request.data)
                parsed.is_valid(raise_exception=True)
                data = dict(parsed.validated_data)
                key = None
                if case is None or self.command == "preparation" and item_id is None:
                    try:
                        key = uuid.UUID(request.headers.get("Idempotency-Key", ""))
                    except ValueError:
                        raise FlowProblem("VALIDATION_ERROR") from None
                if case is None:
                    result = verification.create(user, session, data, key)
                elif self.command in ("preparation", "preparation-withdraw"):
                    result = verification.prepare(
                        user,
                        session,
                        pk,
                        data,
                        key=key,
                        item_id=item_id,
                        withdraw=self.command == "preparation-withdraw",
                    )
                else:
                    result = verification.transition(
                        user, session, pk, self.command, data
                    )
            if PersonalAuthentication().authenticate(request) is None:
                raise FlowProblem("SESSION_INVALID", 401)
            return Response(
                result,
                status=201
                if request.method == "POST"
                and (pk is None or self.command == "preparation" and item_id is None)
                else 200,
            )

    def get(self, request, pk=None, item_id=None):
        if self.command not in (
            "case",
            "requirements",
            "history",
            "preparation",
            "download",
            "reviewer-queue",
        ):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk, item_id)

    def post(self, request, pk=None, item_id=None):
        if (
            self.command
            not in (
                "case",
                "submit",
                "withdraw",
                "preparation",
                "preparation-withdraw",
                "upload",
            )
            or self.command == "case"
            and pk is not None
            or item_id
            and self.command == "preparation"
        ):
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk, item_id)

    def patch(self, request, pk=None, item_id=None):
        if self.command != "preparation" or item_id is None:
            raise problem("METHOD_NOT_ALLOWED", 405)
        return self.execute(request, pk, item_id)
