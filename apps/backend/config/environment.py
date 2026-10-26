"""Fail-closed environment parsing; errors name keys, never configuration values.

Staging/production are disabled-service readiness profiles, not rollout approval.
This module has no Django/database/network dependency and is safe to unit test.
"""

import ipaddress
import json
import re
from urllib.parse import urlsplit

FLAGS = (
    "DJANGO_DEBUG",
    "PWC_AUTH_FLOWS_ENABLED",
    "PWC_AUTH_SESSIONS_ENABLED",
    "PWC_AUTH_MFA_ENABLED",
    "PWC_SYNTHETIC_AUTHORIZATION_ENABLED",
    "PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED",
)
MAPS = ("PWC_AUTH_DELIVERY_KEYS", "PWC_AUTH_MFA_KEYS", "PWC_AUTH_PORTALS")


class EnvironmentError(ValueError):
    """Intentionally redacted configuration failure."""


def fail(key):
    raise EnvironmentError(f"Invalid or unsafe configuration: {key}") from None


def hostname(value):
    try:
        ipaddress.ip_address(value.strip("[]"))
        return True
    except ValueError:
        return len(value) <= 253 and all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in value.split(".")
        )


def origin(value, key):
    """Exact ASCII HTTPS origin, no path (including slash), secrets or wildcards."""
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or not hostname(parsed.hostname)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or parsed.port == 0
            or "*" in value
            or "\\" in value
            or any(ord(c) <= 32 or ord(c) >= 127 for c in value)
        ):
            fail(key)
    except (TypeError, ValueError):
        fail(key)
    return value


def load_environment(env):
    profile = env.get("PWC_ENVIRONMENT", "development")
    if profile not in {"development", "test", "staging", "production"}:
        fail("PWC_ENVIRONMENT")
    result = {"PWC_ENVIRONMENT": profile}
    for key in FLAGS:
        value = env.get(key, "0")
        if value not in {"0", "1"}:
            fail(key)
        result[key] = value == "1"
    for key in MAPS:
        try:
            # Duplicate keys must not silently choose a different trusted origin/key.
            def pairs(items):
                mapping = {}
                for name, value in items:
                    if name in mapping:
                        fail(key)
                    mapping[name] = value
                return mapping

            value = json.loads(env.get(key, "{}"), object_pairs_hook=pairs)
        except (TypeError, ValueError):
            fail(key)
        if not isinstance(value, dict) or any(
            not isinstance(v, str) or not v for v in value.values()
        ):
            fail(key)
        result[key] = value
    portals = result["PWC_AUTH_PORTALS"]
    if len(set(portals.values())) != len(portals) or any(
        name not in {"ngo_web", "pwc_ops"} for name in portals.values()
    ):
        fail("PWC_AUTH_PORTALS")
    for value in portals:
        origin(value, "PWC_AUTH_PORTALS")
    origin(
        env.get("PWC_AUTH_LINK_ORIGIN", "https://pwc.invalid"), "PWC_AUTH_LINK_ORIGIN"
    )
    if env.get("PWC_AUTHORIZATION_ENVIRONMENT", "disabled") not in {
        "disabled",
        "synthetic_test",
        "synthetic_development",
    }:
        fail("PWC_AUTHORIZATION_ENVIRONMENT")
    if env.get("PWC_AUTH_DELIVERY_MODE", "synthetic") != "synthetic":
        fail("PWC_AUTH_DELIVERY_MODE")
    port = env.get("DB_PORT", "5432")
    if not re.fullmatch(r"[0-9]{1,5}", port) or not 1 <= int(port) <= 65535:
        fail("DB_PORT")
    sslmode = env.get("DB_SSLMODE", "prefer")
    if sslmode not in {
        "disable",
        "allow",
        "prefer",
        "require",
        "verify-ca",
        "verify-full",
    }:
        fail("DB_SSLMODE")
    result["DB_OPTIONS"] = {"sslmode": sslmode}
    if env.get("DB_SSLROOTCERT"):
        result["DB_OPTIONS"]["sslrootcert"] = env["DB_SSLROOTCERT"]
    hosts = [
        h.strip()
        for h in env.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if h.strip()
    ]
    if not hosts or any(not hostname(h) for h in hosts):
        fail("DJANGO_ALLOWED_HOSTS")
    result["DJANGO_ALLOWED_HOSTS"] = hosts
    if profile in {"staging", "production"}:
        for key in FLAGS:
            if result[key]:
                fail(key)
        if env.get("PWC_AUTHORIZATION_ENVIRONMENT", "disabled") != "disabled":
            fail("PWC_AUTHORIZATION_ENVIRONMENT")
        for key, minimum in (("DJANGO_SECRET_KEY", 50), ("DB_PASSWORD", 16)):
            value = env.get(key, "")
            if len(value) < minimum or any(
                word in value.lower() for word in ("replace-", "test-only", "example")
            ):
                fail(key)
        for key in ("DB_NAME", "DB_USER", "DB_HOST"):
            if not env.get(key, "").strip():
                fail(key)
        if sslmode != "verify-full" or not env.get("DB_SSLROOTCERT"):
            fail("DB_SSLMODE/DB_SSLROOTCERT")
        if any(
            h.lower() in {"localhost", "backend", "127.0.0.1"}
            or h.lower().endswith(".invalid")
            for h in hosts
        ):
            fail("DJANGO_ALLOWED_HOSTS")
        for host in hosts:
            try:
                address = ipaddress.ip_address(host.strip("[]"))
            except ValueError:
                continue
            if address.is_loopback or address.is_unspecified:
                fail("DJANGO_ALLOWED_HOSTS")
    return result
