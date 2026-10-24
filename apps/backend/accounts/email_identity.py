"""B1 canonicalization: ASCII dot-atom mailbox + IDNA2008/UTS46 domain."""

import re

import idna
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

LOCAL = re.compile(
    r"[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*\Z"
)


def normalize_email(value):
    if not isinstance(value, str) or len(value) > 1024:
        raise ValidationError("Supply a valid email address.")
    value = value.strip()
    if value.count("@") != 1:
        raise ValidationError("Supply a valid email address.")
    local, domain = value.split("@")
    if not LOCAL.fullmatch(local) or len(local) > 64 or domain.endswith("."):
        raise ValidationError("Supply a valid email address.")
    try:
        if any(
            idna.uts46_remap(char, std3_rules=True, transitional=False) == ""
            for char in domain
        ):
            raise idna.IDNAError("Ignored domain character")
        domain = (
            idna.encode(domain, uts46=True, transitional=False, std3_rules=True)
            .decode("ascii")
            .lower()
        )
    except (idna.IDNAError, UnicodeError):
        raise ValidationError("Supply a valid email address.") from None
    if domain.endswith("."):
        raise ValidationError("Supply a valid email address.")
    canonical = f"{local.lower()}@{domain}"
    if len(canonical) > 254:
        raise ValidationError("Supply a valid email address.")
    validate_email(canonical)
    return canonical
