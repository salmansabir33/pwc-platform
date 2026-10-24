"""Closed input grammar for the synthetic GET adapters; no permission decisions."""
from django.core.exceptions import RequestDataTooBig, TooManyFieldsSent
from .security import KernelProblem

FORBIDDEN_PREFIXES = (
    "ORGANIZATION", "NGO", "TENANT", "CONTEXT", "SELECTED_ORGANIZATION",
    "ROLE", "PERMISSION", "CAPABILIT", "ACTION",
)


def validate_input(request, *, discovery):
    try:
        # GET bodies never assign ownership, roles or fields, even if they match URL.
        if request.body:
            raise KernelProblem("invalid_context", 400)
        allowed = {"cursor"} if discovery else set()
        if set(request.GET) - allowed:
            raise KernelProblem("invalid_context", 400)
        cursor = None
        if "cursor" in request.GET:
            values = request.GET.getlist("cursor")
            if len(values) != 1 or not values[0] or len(values[0]) > 512:
                raise KernelProblem("invalid_context", 400)
            cursor = values[0]
        for name in request.META:
            if not name.startswith("HTTP_"):
                continue
            header = name[5:]
            if header.startswith("X_"):
                header = header[2:]
            if header.startswith(FORBIDDEN_PREFIXES):
                raise KernelProblem("invalid_context", 400)
        return cursor
    except (RequestDataTooBig, TooManyFieldsSent, UnicodeError):
        raise KernelProblem("invalid_context", 400) from None
