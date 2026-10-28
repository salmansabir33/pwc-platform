"""Bounded search over EXACTLY the existing verified four-field public projection.

No publication writer, consent inference, hidden target counts or personal auth.
"""

import uuid
from django.core import signing
from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.registration import spend
from . import registry
from .registry_serializers import normalize
from .registry_views import RegistryView
from .views import PublicOrganizationSerializer


class DirectoryView(RegistryView):
    http_method_names = ["get"]

    def initial(self, request, *args, **kwargs):
        # Public projection already exists without login; never consult cookies,
        # grants or account state. Personal registry flags do not gate this read.
        APIView.initial(self, request, *args, **kwargs)

    def get(self, request):
        params = request.query_params
        if (
            request._request.body
            or set(params) - {"q", "city", "classification", "cursor"}
            or any(len(params.getlist(k)) != 1 for k in params)
            or any(len(v) > (1024 if k == "cursor" else 250) for k, v in params.items())
        ):
            registry.fail("VALIDATION_ERROR", 400)
        category = params.get("classification", "")
        if category not in ("", "registered", "unregistered"):
            registry.fail("VALIDATION_ERROR", 400)
        query, city = normalize(params.get("q", "")), normalize(params.get("city", ""))
        limited = spend(request.META.get("REMOTE_ADDR"), "public-directory")
        if limited:
            raise limited
        binding = {
            "filters": registry.digest(
                {"q": query, "city": city, "classification": category}
            )
        }
        with transaction.atomic():
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            values = registry.matches(query, city)
            if category:
                values = values.filter(classification=category)
            if params.get("cursor"):
                try:
                    token = signing.loads(
                        params["cursor"], salt="pwc.public-directory.v1", max_age=3600
                    )
                    if any(token[k] != v for k, v in binding.items()):
                        raise ValueError()
                    values = values.filter(id__gt=uuid.UUID(token["after"]))
                except (signing.BadSignature, ValueError, KeyError, TypeError):
                    registry.fail("VALIDATION_ERROR", 400)
            rows = list(values.order_by("id")[:21])
            more = len(rows) > 20
            rows = rows[:20]
            return Response(
                {
                    "results": PublicOrganizationSerializer(rows, many=True).data,
                    "next_cursor": signing.dumps(
                        dict(binding, after=str(rows[-1].pk)),
                        salt="pwc.public-directory.v1",
                    )
                    if more
                    else None,
                }
            )
