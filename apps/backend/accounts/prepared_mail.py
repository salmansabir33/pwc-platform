"""Unwired SMTP adapter preparation, NOT a live delivery/enrollment switch.

The dispatcher remains hardcoded locmem and flow_security rejects live modes.
Do not wire this adapter before O1/O2/O4 and exact enrollment acceptance. The
existing encrypted outbox owns leases, retries, rate limits and terminal erasure;
this adapter performs exactly one bounded delivery attempt, with mandatory TLS.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import re

from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from django.views.decorators.debug import sensitive_variables

from .email_identity import normalize_email


class PreparedMailError(Exception):
    """Bounded code only; no provider response, address, payload or credential."""


def scalar(value, maximum):
    return (
        isinstance(value, str)
        and 0 < len(value) <= maximum
        and not any(c in value for c in "\r\n\x00")
    )


@dataclass(frozen=True, repr=False)
class MailConfiguration:
    host: str
    port: int
    mode: str
    username: str
    password: str
    sender: str

    def __repr__(self):
        return "MailConfiguration(<redacted>)"

    def __post_init__(self):
        try:
            if (
                not scalar(self.host, 253)
                or not re.fullmatch(r"[a-zA-Z0-9.-]+", self.host)
                or type(self.port) is not int
                or not 1 <= self.port <= 65535
                or self.mode not in {"starttls", "tls"}
                or not scalar(self.username, 320)
                or not scalar(self.password, 1024)
                or not scalar(self.sender, 254)
            ):
                raise ValueError()
            normalize_email(self.sender)
        except (ValueError, ValidationError, TypeError):
            raise PreparedMailError("MAIL_CONFIGURATION_INVALID") from None

    @classmethod
    @sensitive_variables()
    def from_environment(cls, environment=None):
        env = os.environ if environment is None else environment
        try:
            return cls(
                host=env["PWC_MAIL_HOST"],
                port=int(env["PWC_MAIL_PORT"]),
                mode=env["PWC_MAIL_TLS_MODE"],
                username=env["PWC_MAIL_USERNAME"],
                password=env["PWC_MAIL_PASSWORD"],
                sender=env["PWC_MAIL_FROM"],
            )
        except (KeyError, ValueError, TypeError):
            raise PreparedMailError("MAIL_CONFIGURATION_INVALID") from None


class PreparedSmtpAdapter:
    """No ambient backend selection, plaintext fallback, logging or auto-retry."""

    def __init__(self, configuration, *, _backend_factory=EmailBackend):
        self._configuration = configuration
        self._backend_factory = _backend_factory

    @sensitive_variables()
    def send(self, recipient, subject, body, *, expires_at):
        try:
            if (
                not scalar(recipient, 254)
                or not scalar(subject, 120)
                or not isinstance(body, str)
                or not 1 <= len(body) <= 8192
                or not isinstance(expires_at, datetime)
                or expires_at.tzinfo is None
            ):
                raise PreparedMailError("MAIL_MESSAGE_INVALID")
            recipient = normalize_email(recipient)
            if expires_at <= datetime.now(timezone.utc):
                raise PreparedMailError("MAIL_EXPIRED")
            config = self._configuration
            # Django's SMTP backend verifies the peer certificate/hostname for
            # both TLS modes. No environment option can disable verification.
            connection = self._backend_factory(
                host=config.host,
                port=config.port,
                username=config.username,
                password=config.password,
                use_tls=config.mode == "starttls",
                use_ssl=config.mode == "tls",
                timeout=20,
                fail_silently=False,
            )
            with connection:
                message = EmailMessage(
                    subject, body, config.sender, [recipient], connection=connection
                )
                if connection.send_messages([message]) != 1:
                    raise PreparedMailError("MAIL_UNAVAILABLE")
        except PreparedMailError:
            raise
        except Exception:
            # SMTP failures can contain whole messages/credentials. Outbox
            # scheduling must handle this code, never stringify provider errors.
            raise PreparedMailError("MAIL_UNAVAILABLE") from None
