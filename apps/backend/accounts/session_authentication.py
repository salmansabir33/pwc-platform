"""Explicit future DRF adapter; not an NGO authorization permission class."""

from django.conf import settings
import uuid
from django.db import DatabaseError, transaction
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import APIException
from .flow_security import FlowProblem
from . import sessions
from .session_views import mixed, browser_csrf
from .registration_views import MESSAGES


class PersonalAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        raw = request._request
        if not (
            settings.SESSION_COOKIE_NAME in raw.COOKIES
            or "HTTP_AUTHORIZATION" in raw.META
        ):
            return None
        try:
            if mixed(raw):
                raise FlowProblem("AMBIGUOUS_CREDENTIALS")
            sessions.configured()
            if not raw.is_secure():
                raise FlowProblem("TRANSPORT_NOT_ALLOWED")
            if settings.SESSION_COOKIE_NAME in raw.COOKIES and raw.method not in (
                "GET",
                "HEAD",
                "OPTIONS",
            ):
                problem = browser_csrf(raw)
                if problem:
                    raise problem
            with transaction.atomic():
                snapshot = sessions.locate(raw)
                result = (
                    sessions.authenticate_locked(raw, snapshot) if snapshot else None
                )
                if not result:
                    raise sessions.invalid()
                return result
        except (FlowProblem, DatabaseError) as exc:
            problem = (
                exc
                if isinstance(exc, FlowProblem)
                else FlowProblem("AUTH_UNAVAILABLE", 503)
            )
            error = APIException(
                detail={
                    "error": {
                        "code": problem.code,
                        "message": MESSAGES[problem.code],
                        "field_errors": {},
                        "request_id": str(uuid.uuid4()),
                    }
                }
            )
            error.status_code = problem.status
            raise error from None
