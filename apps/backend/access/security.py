"""Shared transaction primitives. No runtime role can issue synthetic grants."""
from django.conf import settings
from django.db import connection


class KernelProblem(Exception):
    def __init__(self, code, status):
        self.code, self.status = code, status
        super().__init__(code)


def require_synthetic_environment():
    name = str(connection.settings_dict["NAME"])
    if not (
        settings.PWC_SYNTHETIC_AUTHORIZATION_ENABLED
        and settings.PWC_AUTHORIZATION_ENVIRONMENT in ("synthetic_test", "synthetic_development")
        and (name.startswith("test_") or name.startswith("pwc_synthetic_"))
        and connection.vendor == "postgresql"
        and not settings.DATABASE_ROUTERS
    ):
        raise KernelProblem("authorization_unavailable", 503)


def transaction_limits():
    with connection.cursor() as cursor:
        cursor.execute("SHOW transaction_isolation")
        if cursor.fetchone()[0] != "read committed":
            raise KernelProblem("authorization_unavailable", 503)
        cursor.execute("SET LOCAL lock_timeout = '2s'")
        cursor.execute("SET LOCAL statement_timeout = '5s'")


def db_clock():
    with connection.cursor() as cursor:
        cursor.execute("SELECT clock_timestamp()")
        return cursor.fetchone()[0]


def require_revision(current, expected):
    if expected is None:
        raise KernelProblem("precondition_required", 428)
    if type(expected) is not int or expected < 1:
        raise KernelProblem("invalid_context", 400)
    if current != expected:
        raise KernelProblem("revision_mismatch", 412)
