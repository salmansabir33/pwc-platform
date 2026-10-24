"""Thin synthetic-only DRF adapters. All auth/authority checks live in services."""
import logging
import uuid

from django.conf import settings
from django.db import DatabaseError
from django.utils.cache import patch_vary_headers
from rest_framework.exceptions import APIException
from rest_framework.negotiation import BaseContentNegotiation
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .registry import ENTER, READ, SETTINGS

logger = logging.getLogger(__name__)


class ContractError(APIException):
    def __init__(self, code, status):
        self.status_code = status
        super().__init__({"error": {"code": code, "correlation_id": str(uuid.uuid4())}})


class FixedJSON(BaseContentNegotiation):
    def select_renderer(self, request, renderers, format_suffix=None):
        # No browsable API, format query override or debug renderer.
        return renderers[0], "application/json"


class SyntheticReadView(APIView):
    # Intentionally not DRF default auth/permissions: the kernel reauthenticates
    # in the SAME durable transaction as scoped projection/audit. Never trust user.
    authentication_classes = []
    permission_classes = [AllowAny]
    renderer_classes = [JSONRenderer]
    parser_classes = []
    content_negotiation_class = FixedJSON
    http_method_names = ["get", "head"]
    action = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not settings.PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED:
            raise ContractError("not_found", 404)

    def handle_exception(self, exc):
        if isinstance(exc, DatabaseError):
            correlation = uuid.uuid4()
            logger.warning("Context adapter dependency unavailable; correlation=%s", correlation)
            return Response({"error": {"code": "authorization_unavailable",
                                       "correlation_id": str(correlation)}}, status=503)
        if isinstance(exc, APIException) and not isinstance(exc, ContractError):
            exc = ContractError("method_not_allowed" if exc.status_code == 405 else "invalid_context", exc.status_code)
        return super().handle_exception(exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        response["Referrer-Policy"] = "no-referrer"
        patch_vary_headers(response, ("Cookie", "Authorization"))
        if response.status_code == 401:
            response["WWW-Authenticate"] = "Bearer"
        return response

    def get(self, request, organization_uuid=None):
        if self.action is None:
            decision = services.discover(request)
        else:
            decision = services.evaluate(request, kind="ngo", identifier=organization_uuid,
                action=self.action, http_contract=True,
                object_organization_id=organization_uuid if self.action in (READ, SETTINGS) else None)
        if not decision.allowed:
            return Response({"error": {"code": decision.code,
                                       "correlation_id": str(decision.correlation_id)}}, status=decision.status)
        if self.action is None:
            data = {"results": [{"kind": "ngo", "organization_id": str(item.organization_id),
                                 "context_revision": item.context_revision} for item in decision.contexts],
                    "next_cursor": decision.next_cursor}
        elif self.action == ENTER:
            data = {"context": {"kind": "ngo", "organization_id": str(decision.context_id)},
                    "registry_version": decision.registry_version,
                    "context_revision": decision.context_revision,
                    "actions": list(decision.actions),
                    "earliest_grant_expires_at": decision.earliest_grant_expires_at.isoformat()}
        else:
            data = dict(decision.projection)
            data["context_revision"] = decision.context_revision
        return Response(data)


class WorkspaceDiscoveryView(SyntheticReadView):
    pass


class CapabilitiesView(SyntheticReadView):
    action = ENTER


class PrivateProbeView(SyntheticReadView):
    action = READ


class KernelSettingsView(SyntheticReadView):
    action = SETTINGS
