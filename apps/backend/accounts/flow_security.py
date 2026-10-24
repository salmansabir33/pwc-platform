"""Reviewed primitives/configuration only; no custom cryptographic algorithms."""

import hashlib
import json
import secrets
from urllib.parse import urlsplit

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.debug import sensitive_variables


class FlowProblem(Exception):
    def __init__(self, code, status=400, fields=None, retry_after=None):
        self.code, self.status, self.fields, self.retry_after = (
            code,
            status,
            fields or {},
            retry_after,
        )


def unavailable():
    return FlowProblem("AUTH_UNAVAILABLE", 503)


def configured():
    if (
        not settings.PWC_AUTH_FLOWS_ENABLED
        or not isinstance(settings.PWC_AUTH_ABUSE_KEY, str)
        or len(settings.PWC_AUTH_ABUSE_KEY) < 32
    ):
        raise unavailable()
    if settings.PWC_AUTH_DELIVERY_MODE != "synthetic":
        raise unavailable()  # live sending is not approved/implemented
    budget = settings.PWC_AUTH_GLOBAL_SENDS_PER_HOUR
    if type(budget) is not int or budget < 1:
        raise unavailable()
    origin = settings.PWC_AUTH_LINK_ORIGIN
    if (
        not isinstance(origin, str)
        or any(ord(c) <= 32 or ord(c) >= 127 for c in origin)
        or "\\" in origin
    ):
        raise unavailable()
    try:
        base = urlsplit(origin)
        base.port  # range/syntax check; urlsplit alone doesn't validate the port
        URLValidator(schemes=["https"])(origin)
    except (ValueError, TypeError, ValidationError):
        raise unavailable() from None
    if (
        base.scheme != "https"
        or not base.hostname
        or base.username
        or base.password
        or base.path
        or base.query
        or base.fragment
    ):
        raise unavailable()
    active = settings.PWC_AUTH_DELIVERY_ACTIVE_KEY
    if (
        not isinstance(settings.PWC_AUTH_DELIVERY_KEYS, dict)
        or not isinstance(active, str)
        or not active
        or len(active) > 100
        or not settings.PWC_AUTH_DELIVERY_KEYS.get(active)
    ):
        raise unavailable()
    cipher(active)  # check key validity before recording/sending requests


@sensitive_variables()
def cipher(key_id):
    try:
        return Fernet(settings.PWC_AUTH_DELIVERY_KEYS[key_id])
    except (KeyError, ValueError, TypeError):
        raise unavailable() from None


def new_secret():
    return secrets.token_urlsafe(32)


def digest(secret):
    return hashlib.sha256(secret.encode("ascii")).hexdigest()


def matches(secret, stored):
    if not isinstance(secret, str) or len(secret) != 43 or not secret.isascii():
        return False
    return constant_time_compare(digest(secret), stored)


def abuse_digest(value):
    return salted_hmac(
        "pwc.auth.abuse.v1",
        value,
        secret=settings.PWC_AUTH_ABUSE_KEY,
        algorithm="sha256",
    ).hexdigest()


@sensitive_variables()
def seal(payload):
    key_id = settings.PWC_AUTH_DELIVERY_ACTIVE_KEY
    return key_id, cipher(key_id).encrypt(
        json.dumps(payload, separators=(",", ":")).encode()
    )


@sensitive_variables()
def unseal(key_id, payload):
    try:
        return json.loads(cipher(key_id).decrypt(bytes(payload)))
    except (InvalidToken, ValueError, TypeError, UnicodeError):
        raise unavailable() from None
