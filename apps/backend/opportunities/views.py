"""Anonymous read foundation. Live reads/publication remain unavailable.

Only an explicit test-profile exercise can expose fictional database fixtures.
There is no environment flag, writer, Django admin or privileged-role shortcut.
"""

import hashlib
import json
import uuid
from django.conf import settings
from django.core import signing
from django.db import connection, transaction
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from accounts.registration import spend
from organizations.models import OrganizationWorkspace
from organizations.registry_serializers import normalize
from organizations.registry_views import RegistryView
from .models import Opportunity
from .serializers import PublicOpportunitySerializer


SALT = "pwc.public-opportunities.v1"


def fail(code, status):
    error = APIException(
        {
            "error": {
                "code": code,
                "message": "The opportunity request could not be completed.",
                "field_errors": {},
                "request_id": str(uuid.uuid4()),
            }
        }
    )
    error.status_code = status
    raise error


def public_rows():
    # Deliberately mirrors the existing NGO public-eligibility floor, not consent.
    # Re-evaluated for every list, cursor page and detail; grants are irrelevant.
    return Opportunity.objects.filter(
        state=Opportunity.State.PUBLISHED,
        organization__workspace__state=OrganizationWorkspace.State.VERIFIED,
    ).select_related("organization")


class OpportunityReadView(RegistryView):
    http_method_names = ["get"]

    def initial(self, request, *args, **kwargs):
        APIView.initial(self, request, *args, **kwargs)
        if request.method.lower() not in self.http_method_names:
            self.http_method_not_allowed(request, *args, **kwargs)
        # Not parsed from environment; cannot activate in development/staging/prod.
        if not (
            settings.PWC_ENVIRONMENT == "test"
            and getattr(settings, "PWC_OPPORTUNITIES_TEST_EXERCISE", False) is True
        ):
            fail("OPPORTUNITIES_UNAVAILABLE", 503)

    def guard(self, request, allowed):
        params = request.query_params
        if (
            request._request.body
            or set(params) - allowed
            or any(
                len(params.getlist(key)) != 1
                or len(value) > (1024 if key == "cursor" else 250)
                for key, value in params.items()
            )
        ):
            fail("VALIDATION_ERROR", 400)
        limited = spend(request.META.get("REMOTE_ADDR"), "public-opportunities")
        if limited:
            raise limited
        return params

    def handle_exception(self, exc):
        # Reuse bounded/redacted registry error handling; only rename its generic
        # text/code so unrelated authentication availability is not implied.
        response = super().handle_exception(exc)
        if isinstance(response.data, dict) and "error" in response.data:
            if response.data["error"]["code"] == "AUTH_UNAVAILABLE":
                response.data["error"]["code"] = "OPPORTUNITIES_UNAVAILABLE"
            response.data["error"]["message"] = (
                "The opportunity request could not be completed."
            )
        return response


class OpportunityListView(OpportunityReadView):
    def get(self, request):
        params = self.guard(request, {"q", "city", "type", "organization_id", "cursor"})
        query, city = normalize(params.get("q", "")), normalize(params.get("city", ""))
        kind = params.get("type", "")
        if kind not in ("", *Opportunity.Type.values):
            fail("VALIDATION_ERROR", 400)
        owner = params.get("organization_id", "")
        if owner:
            try:
                owner = str(uuid.UUID(owner))
            except ValueError:
                fail("VALIDATION_ERROR", 400)
        binding = hashlib.sha256(
            json.dumps([query, city, kind, owner], separators=(",", ":")).encode()
        ).hexdigest()
        after = None
        if params.get("cursor"):
            try:
                token = signing.loads(params["cursor"], salt=SALT, max_age=3600)
                if (
                    not isinstance(token, dict)
                    or set(token) != {"filters", "after"}
                    or token["filters"] != binding
                ):
                    raise ValueError()
                if not isinstance(token["after"], str):
                    raise ValueError()
                after = uuid.UUID(token["after"])
            except (signing.BadSignature, ValueError, TypeError, KeyError):
                fail("VALIDATION_ERROR", 400)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            rows = public_rows()
            if query:
                rows = rows.filter(lookup_title__contains=query)
            if city:
                rows = rows.filter(organization__lookup_city__contains=city)
            if kind:
                rows = rows.filter(type=kind)
            if owner:
                rows = rows.filter(organization_id=owner)
            if after:
                rows = rows.filter(id__gt=after)
            batch = list(rows.order_by("id")[:21])
            values = batch[:20]
            return Response(
                {
                    "results": PublicOpportunitySerializer(values, many=True).data,
                    "next_cursor": signing.dumps(
                        {"filters": binding, "after": str(values[-1].pk)}, salt=SALT
                    )
                    if len(batch) > 20
                    else None,
                }
            )


class OpportunityDetailView(OpportunityReadView):
    def get(self, request, pk):
        self.guard(request, set())
        try:
            identifier = uuid.UUID(pk)
        except ValueError:
            fail("NOT_FOUND", 404)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            row = public_rows().filter(pk=identifier).first()
            if row is None:
                fail("NOT_FOUND", 404)
            return Response(PublicOpportunitySerializer(row).data)
