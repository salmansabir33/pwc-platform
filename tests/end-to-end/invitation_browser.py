"""NONSHIPPED synthetic browser fixtures, never imported by application code.

The trusted-source mock is test evidence ONLY, not an issuer adapter/acceptance.
Mailbox capture is temporary test IPC, not a deployed proof-retrieval endpoint.
"""

from datetime import timedelta
import json
import re
from unittest.mock import patch

from django.core import mail
from django.utils import timezone
from accounts import personal_invitations as invitations
from accounts.flow_security import unseal
from accounts.invitation_delivery import dispatch_one
from accounts.models import PersonalInvitation, MfaFactor, AuthSession


def seed_invitations(issuer, mailbox):
    mailbox.write_text("{}")
    result = []
    for locale in ("en", "ur"):
        recipient = f"invitation-{locale}@example.invalid"
        # Pass the existing shared email cooldown without weakening it.
        past = timezone.now() - timedelta(seconds=61)
        with (patch("accounts.personal_invitations.authorize_source", return_value=True),
              patch("accounts.personal_invitations.timezone.now", return_value=past)):
            value = invitations.issue(issuer.pk, recipient, "b" * 64, "192.0.2.90")
        row = PersonalInvitation.objects.get(pk=value["invitation_id"])
        payload = unseal(row.mail_key, row.mail_payload)
        result.append({"recipient": recipient, "id": str(row.pk), "token": payload["secret"]})
    with patch("accounts.personal_invitations.authorize_source", return_value=True):
        while dispatch_one():
            pass
    return result


def capture_mail(mailbox):
    while dispatch_one():
        pass
    proofs = {}
    for message in mail.outbox:
        if message.to[0] not in {"invitation-en@example.invalid", "invitation-ur@example.invalid"}:
            continue
        value = message.body.splitlines()[-1]
        if re.fullmatch(r"[A-Za-z0-9_-]{43}", value):
            proofs[message.to[0]] = value
    mailbox.write_text(json.dumps(proofs))


def assert_completed(fixtures):
    for fixture in fixtures:
        row = PersonalInvitation.objects.get(pk=fixture["id"])
        assert row.user_id and row.consumed_at < row.expires_at
        assert not row.user.is_staff and not row.user.is_superuser
        assert MfaFactor.objects.filter(user=row.user, state="active").count() == 1
        assert not AuthSession.objects.filter(user=row.user, revoked_at__isnull=True).exists()
        assert row.ceremony_payload is None and row.mail_payload is None
