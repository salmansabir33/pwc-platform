"""Prevent legacy Django/DRF cookie authentication bypassing the live registry.

Lazy for public views; no identity lookup on mixed credentials. The session API
still rechecks under locks for each command rather than trusting this read.
"""

from django.contrib.auth.models import AnonymousUser
from asgiref.sync import sync_to_async
from django.db import DatabaseError, transaction
from django.utils.functional import SimpleLazyObject
from .flow_security import FlowProblem
from . import sessions


def registry_user(request):
    try:
        sessions.configured()
        with transaction.atomic():
            snapshot = sessions.locate(request)
            context = (
                sessions.authenticate_locked(request, snapshot) if snapshot else None
            )
            return context[0] if context else AnonymousUser()
    except (FlowProblem, DatabaseError):
        return AnonymousUser()  # never fall back to an unregistered Django cookie


class PersonalSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # This bridge is cookie-only. Mobile APIs explicitly select Bearer mode;
        # future DRF private views use the adapter, never cookie fallback.
        request.user = (
            SimpleLazyObject(lambda: registry_user(request))
            if ("HTTP_AUTHORIZATION" not in request.META)
            else AnonymousUser()
        )

        async def auser():
            if "HTTP_AUTHORIZATION" in request.META:
                return AnonymousUser()
            return await sync_to_async(registry_user, thread_sensitive=True)(request)

        request.auser = auser
        return self.get_response(request)
