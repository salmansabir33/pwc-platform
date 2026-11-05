"""Invitation issuance/email-proof slice, hard-closed outside tests.

No HTTP issuer, runtime authority configuration, delivery worker, account writer
or grant installer. All public functions fence before I/O. An accepted future
source adapter must lock authority/revocation rows through transaction commit;
this deliberately unavailable adapter cannot be replaced by a settings flag.
"""

from datetime import timedelta
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.debug import sensitive_variables

from .email_identity import normalize_email
from .flow_security import FlowProblem, configured, new_secret, seal
from .models import PersonalInvitation, SecurityEvent, User, UserContact
from .registration import legacy_match, spend


def gate():
    if settings.PWC_ENVIRONMENT != "test":
        raise FlowProblem("AUTH_UNAVAILABLE", 503)
    configured()


def authorize_source(issuer, source_digest, recipient, operation):
    # Actual officer/root/source acceptance is absent. Staff/superuser, names,
    # repository ownership and environment settings are never substitutes.
    return False


def audit(invitation, action, actor=None, result="success"):
    SecurityEvent.objects.create(
        event="auth.invitation_" + action,
        result=result,
        actor=actor,
        reason="invitation:" + str(invitation.pk),
    )


def identifier(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


@sensitive_variables()
def digest(invitation, purpose, secret):
    return salted_hmac(
        "pwc.personal-invitation.v1." + str(invitation.pk) + "." + purpose,
        secret,
        secret=settings.PWC_AUTH_ABUSE_KEY,
        algorithm="sha256",
    ).hexdigest()


@sensitive_variables()
def matches(invitation, purpose, value, stored):
    return bool(
        isinstance(value, str)
        and re.fullmatch(r"[A-Za-z0-9_-]{43}", value)
        and constant_time_compare(digest(invitation, purpose, value), stored)
    )


def erase(invitation):
    invitation.mail_key = ""
    invitation.mail_payload = None
    invitation.proof_digest = ""
    invitation.proof_expires_at = None


@sensitive_variables()
def queue(invitation, purpose, value):
    invitation.mail_key, invitation.mail_payload = seal(
        {
            "invitation_id": str(invitation.pk),
            "recipient": invitation.recipient,
            "purpose": purpose,
            "secret": value,
        }
    )


def source_live(invitation, issuer, operation):
    return issuer.is_active and authorize_source(
        issuer, invitation.source_digest, invitation.recipient, operation
    )


def lock(invitation_id):
    snapshot = PersonalInvitation.objects.filter(pk=identifier(invitation_id)).first()
    if not snapshot:
        return None, None
    # Common lock order for issuance, proof and cancellation: issuer -> invitation.
    issuer = User.objects.select_for_update().get(pk=snapshot.issuer_id)
    invitation = PersonalInvitation.objects.select_for_update().get(pk=snapshot.pk)
    return issuer, invitation


def pending(invitation):
    return bool(
        invitation
        and not invitation.cancelled_at
        and not invitation.email_verified_at
        and invitation.failures < 5
        and timezone.now() < invitation.expires_at
    )


def invalid(invitation):
    if invitation and pending(invitation):
        invitation.failures += 1
        if invitation.failures == 5:
            invitation.cancelled_at = timezone.now()
            erase(invitation)
        invitation.save()
        audit(invitation, "denied", result="denied")
    return FlowProblem("CHALLENGE_INVALID")


def bound(invitation, token, recipient):
    return (
        pending(invitation)
        and recipient == invitation.recipient
        and matches(invitation, "token", token, invitation.token_digest)
    )


@sensitive_variables()
def issue(issuer_id, recipient, source_digest, ip):
    gate()
    try:
        recipient = normalize_email(recipient)
    except ValidationError:
        return FlowProblem("VALIDATION_ERROR")
    if not isinstance(source_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", source_digest
    ):
        return FlowProblem("AUTH_UNAVAILABLE", 503)
    with transaction.atomic():
        issuer = (
            User.objects.select_for_update().filter(pk=identifier(issuer_id)).first()
        )
        if (
            not issuer
            or not issuer.is_active
            or not authorize_source(issuer, source_digest, recipient, "issue")
        ):
            return FlowProblem("AUTH_UNAVAILABLE", 503)
        problem = spend(ip, "invitation_issue", target=recipient, delivery=True)
        if problem:
            return problem
        if (
            legacy_match(recipient, recipient)
            or UserContact.objects.filter(
                kind="email",
                normalized_value=recipient,
                retired_at__isnull=True,
                verified_at__isnull=False,
            ).exists()
        ):
            return FlowProblem("STATE_CONFLICT", 409)
        now = timezone.now()
        for old in (
            PersonalInvitation.objects.select_for_update()
            .filter(
                recipient=recipient,
                cancelled_at__isnull=True,
                expires_at__lte=now,
            )
            .order_by("id")
        ):
            old.cancelled_at = now
            erase(old)
            old.save()
            audit(old, "expired")
        invitation = PersonalInvitation(
            issuer=issuer,
            source_digest=source_digest,
            recipient=recipient,
            created_at=now,
            expires_at=now + timedelta(hours=24),
        )
        token = new_secret()
        invitation.token_digest = digest(invitation, "token", token)
        queue(invitation, "token", token)
        try:
            with transaction.atomic():
                invitation.save(force_insert=True)
        except IntegrityError:
            return FlowProblem("STATE_CONFLICT", 409)
        audit(invitation, "issued", issuer)
        return {
            "invitation_id": str(invitation.pk),
            "expires_at": invitation.expires_at.isoformat(),
            "status": "pending",
        }


@sensitive_variables()
def request_confirmation(invitation_id, token, recipient, ip):
    gate()
    try:
        recipient = normalize_email(recipient)
    except ValidationError:
        recipient = "invalid"
    problem = spend(ip, "invitation_proof", target=recipient, delivery=True)
    if problem:
        return problem
    with transaction.atomic():
        issuer, invitation = lock(invitation_id)
        if not bound(invitation, token, recipient) or not source_live(
            invitation, issuer, "email-proof"
        ):
            return invalid(invitation)
        proof = new_secret()
        invitation.proof_digest = digest(invitation, "email-proof", proof)
        invitation.proof_expires_at = min(
            invitation.expires_at, timezone.now() + timedelta(minutes=30)
        )
        queue(invitation, "email-proof", proof)
        invitation.save()
        audit(invitation, "confirmation_requested")
        return {"status": "accepted"}


@sensitive_variables()
def confirm_email(invitation_id, token, recipient, proof, ip):
    gate()
    problem = spend(ip, "invitation_confirm", flow=str(invitation_id))
    if problem:
        return problem
    try:
        recipient = normalize_email(recipient)
    except ValidationError:
        recipient = "invalid"
    with transaction.atomic():
        issuer, invitation = lock(invitation_id)
        if (
            not bound(invitation, token, recipient)
            or not source_live(invitation, issuer, "email-proof")
            or not invitation.proof_expires_at
            or timezone.now() >= invitation.proof_expires_at
            or not matches(invitation, "email-proof", proof, invitation.proof_digest)
        ):
            return invalid(invitation)
        invitation.email_verified_at = timezone.now()
        # Proof is single-use; token cannot turn mailbox proof into account/grants.
        erase(invitation)
        invitation.save()
        audit(invitation, "email_verified")
        return {"status": "email_verified"}


def cancel(issuer_id, invitation_id):
    gate()
    with transaction.atomic():
        issuer, invitation = lock(invitation_id)
        if (
            not invitation
            or str(issuer.pk) != str(issuer_id)
            or not source_live(invitation, issuer, "cancel")
        ):
            return FlowProblem("AUTH_UNAVAILABLE", 503)
        if not invitation.cancelled_at:
            invitation.cancelled_at = timezone.now()
            erase(invitation)
            invitation.save()
            audit(invitation, "cancelled", issuer)
        return {"status": "cancelled"}
