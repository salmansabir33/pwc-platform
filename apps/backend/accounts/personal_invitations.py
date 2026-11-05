"""Full ordinary personal enrollment, hard-closed outside tests.

No HTTP issuer, runtime authority configuration or grant installer. All public functions fence before I/O. An accepted future
source adapter must lock authority/revocation rows through transaction commit;
this deliberately unavailable adapter cannot be replaced by a settings flag.
"""

import json
from datetime import timedelta

import pyotp
import re
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.debug import sensitive_variables

from .email_identity import normalize_email
from .flow_security import FlowProblem, configured, new_secret, seal, unseal
from .models import (
    PersonalInvitation,
    SecurityEvent,
    User,
    UserContact,
    AuthSession,
    MfaFactor,
)
from .registration import legacy_match, spend


def gate():
    if settings.PWC_ENVIRONMENT != "test":
        raise FlowProblem("AUTH_UNAVAILABLE", 503)
    configured()


def authorize_source(issuer, source_digest, recipient, operation):
    # Actual officer/root/source acceptance is absent. Staff/superuser, names,
    # repository ownership and environment settings are never substitutes.
    return False


def audit(invitation, action, actor=None, result="success", subject=None):
    SecurityEvent.objects.create(
        event="auth.invitation_" + action,
        result=result,
        actor=actor,
        subject=subject,
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


def erase_mail(invitation, state="cancelled"):
    invitation.mail_key = ""
    invitation.mail_payload = None
    invitation.mail_state = state
    invitation.mail_lease_at = None


def erase_ceremony(invitation):
    invitation.ceremony_key = ""
    invitation.ceremony_payload = None
    invitation.ceremony_expires_at = None


def erase(invitation):
    erase_mail(invitation)
    erase_ceremony(invitation)
    invitation.control_digest = ""
    invitation.proof_digest = ""
    invitation.proof_expires_at = None


@sensitive_variables()
def queue(invitation, purpose, value):
    invitation.mail_generation += 1
    invitation.mail_state = "pending"
    invitation.mail_attempts = 0
    invitation.mail_next_at = timezone.now()
    invitation.mail_lease_at = None
    invitation.mail_key, invitation.mail_payload = seal(
        {
            "invitation_id": str(invitation.pk),
            "recipient": invitation.recipient,
            "purpose": purpose,
            "secret": value,
            "generation": invitation.mail_generation,
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
        and not invitation.consumed_at
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
                consumed_at__isnull=True,
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
        # Continuation capability goes only to the proof submitter, never the
        # issuer or mailbox worker. A stolen invitation link alone is insufficient.
        # Re-proving the same inbox rotates continuation authority, but a still
        # valid encrypted authenticator ceremony may be resumed by re-entering
        # its password (e.g. after switching to an authenticator app).
        erase_mail(invitation)
        invitation.proof_digest = ""
        invitation.proof_expires_at = None
        control = new_secret()
        invitation.control_digest = digest(invitation, "control", control)
        invitation.save()
        audit(invitation, "email_verified")
        return {
            "status": "email_verified",
            "enrollment_control": control,
            "expires_at": invitation.expires_at.isoformat(),
        }


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
        if invitation.consumed_at:
            return FlowProblem("STATE_CONFLICT", 409)
        if not invitation.cancelled_at:
            invitation.cancelled_at = timezone.now()
            erase(invitation)
            invitation.save()
            audit(invitation, "cancelled", issuer)
        return {"status": "cancelled"}


def controlled(invitation, token, recipient, control):
    return (
        bound(invitation, token, recipient)
        and invitation.email_verified_at
        and matches(invitation, "control", control, invitation.control_digest)
    )


@sensitive_variables()
def set_password(invitation_id, token, recipient, control, password, ip):
    """Stage credentials only; no login identity exists before TOTP activation."""
    gate()
    from . import mfa

    mfa.configured()
    problem = spend(ip, "invitation_password", flow=str(invitation_id))
    if problem:
        return problem
    try:
        recipient = normalize_email(recipient)
    except ValidationError:
        recipient = "invalid"
    with transaction.atomic():
        issuer, invitation = lock(invitation_id)
        if not controlled(invitation, token, recipient, control) or not source_live(
            invitation, issuer, "complete"
        ):
            return invalid(invitation)
        user = User(email=recipient, username="pwc_" + uuid.uuid4().hex)
        try:
            if not isinstance(password, str) or not 1 <= len(password) <= 128:
                raise ValidationError("Invalid password")
            validate_password(password, user)
        except ValidationError:
            return FlowProblem("VALIDATION_ERROR")
        previous = None
        if (
            invitation.ceremony_payload
            and invitation.ceremony_expires_at > timezone.now()
        ):
            candidate = unseal(invitation.ceremony_key, invitation.ceremony_payload)
            if (
                candidate.get("invitation_id") == str(invitation.pk)
                and candidate.get("recipient") == recipient
                and check_password(password, candidate.get("password_hash", ""))
            ):
                previous = candidate
        if previous is None:
            user.set_password(password)
        if not controlled(invitation, token, recipient, control) or not source_live(
            invitation, issuer, "complete"
        ):
            return invalid(invitation)
        if legacy_match(recipient, recipient):
            return invalid(invitation)
        now = timezone.now()
        if previous is not None and now < invitation.ceremony_expires_at:
            return {
                "status": "mfa_required",
                "secret": previous["secret"],
                "otpauth_uri": pyotp.TOTP(previous["secret"]).provisioning_uri(
                    name=previous["user_id"], issuer_name="PWC"
                ),
                "expires_at": invitation.ceremony_expires_at.isoformat(),
            }
        secret = pyotp.random_base32()
        invitation.ceremony_expires_at = min(
            invitation.expires_at, now + timedelta(minutes=5)
        )
        invitation.ceremony_key, invitation.ceremony_payload = seal(
            {
                "invitation_id": str(invitation.pk),
                "recipient": recipient,
                "user_id": str(user.pk),
                "username": user.username,
                "password_hash": user.password,
                "secret": secret,
                "created_at": now.isoformat(),
                "expires_at": invitation.ceremony_expires_at.isoformat(),
            }
        )
        invitation.save()
        audit(invitation, "password_staged")
        return {
            "status": "mfa_required",
            "secret": secret,
            "otpauth_uri": pyotp.TOTP(secret).provisioning_uri(
                name=str(user.pk), issuer_name="PWC"
            ),
            "expires_at": invitation.ceremony_expires_at.isoformat(),
        }


@sensitive_variables()
def create_account(invitation, issuer, ceremony, code):
    """Caller holds issuer/invitation locks; all new auth rows share a savepoint.

    Existing MFA confirmation supplies TOTP verification, replay protection,
    encryption format, factor activation and recovery-code hashing. Its internal
    enrollment session has no browser key or bearer ever issued to a client.
    It is revoked before commit; recipient explicitly logs in afterward.
    """
    from . import mfa, sessions

    now = timezone.now()
    user = User(
        id=identifier(ceremony["user_id"]),
        username=ceremony["username"],
        email=invitation.recipient,
        password=ceremony["password_hash"],
    )
    user.save(force_insert=True)
    UserContact.objects.create(
        user=user,
        kind="email",
        display_value=invitation.recipient,
        normalized_value=invitation.recipient,
        verified_at=now,
        is_primary=True,
    )
    session = AuthSession.objects.create(
        user=user,
        transport="web",
        portal="ngo_web",
        web_key_digest=sessions.web_digest(new_secret()),
        device_label="Invitation enrollment",
        auth_epoch=user.auth_epoch,
        created_at=now,
        last_interactive_at=now,
        absolute_expires_at=invitation.ceremony_expires_at,
    )
    factor = MfaFactor(
        user=user,
        state="pending",
        enrollment_session=session,
        auth_epoch=user.auth_epoch,
        recovery_generation=user.recovery_generation,
        created_at=now,
        expires_at=invitation.ceremony_expires_at,
        key_id=settings.PWC_AUTH_MFA_ACTIVE_KEY,
    )
    factor.encrypted_secret = mfa.cipher(factor.key_id).encrypt(
        json.dumps(
            {
                "purpose": "totp-v1",
                "user": str(user.pk),
                "factor": str(factor.pk),
                "secret": ceremony["secret"],
            }
        ).encode()
    )
    factor.save()
    result = mfa.enrollment_confirm(
        user, session, {"enrollment_id": str(factor.pk), "code": code}
    )
    if isinstance(result, FlowProblem):
        return result
    if (
        timezone.now() >= invitation.expires_at
        or timezone.now() >= invitation.ceremony_expires_at
        or not source_live(invitation, issuer, "complete")
    ):
        return FlowProblem("CHALLENGE_INVALID")
    session.revoked_at, session.revocation_reason = (
        timezone.now(),
        "enrollment_complete",
    )
    session.save(update_fields=["revoked_at", "revocation_reason"])
    invitation.user = user
    invitation.consumed_at = timezone.now()
    erase(invitation)
    invitation.save()
    audit(invitation, "completed", subject=user)
    if (
        timezone.now() >= invitation.expires_at
        or timezone.now() >= session.absolute_expires_at
        or not source_live(invitation, issuer, "complete")
    ):
        return FlowProblem("CHALLENGE_INVALID")
    return {"status": "complete", "recovery_codes": result["recovery_codes"]}


@sensitive_variables()
def activate(invitation_id, token, recipient, control, code, ip):
    gate()
    from . import mfa

    mfa.configured()
    problem = spend(ip, "invitation_activate", flow=str(invitation_id))
    if problem:
        return problem
    try:
        recipient = normalize_email(recipient)
    except ValidationError:
        recipient = "invalid"
    with transaction.atomic():
        issuer, invitation = lock(invitation_id)
        if (
            not controlled(invitation, token, recipient, control)
            or not source_live(invitation, issuer, "complete")
            or not invitation.ceremony_expires_at
            or timezone.now() >= invitation.ceremony_expires_at
        ):
            return invalid(invitation)
        ceremony = unseal(invitation.ceremony_key, invitation.ceremony_payload)
        if (
            ceremony.get("invitation_id") != str(invitation.pk)
            or ceremony.get("recipient") != recipient
            or ceremony.get("expires_at") != invitation.ceremony_expires_at.isoformat()
        ):
            return FlowProblem("AUTH_UNAVAILABLE", 503)
        if legacy_match(recipient, recipient):
            return invalid(invitation)
        try:
            with transaction.atomic():
                result = create_account(invitation, issuer, ceremony, code)
                if isinstance(result, FlowProblem):
                    transaction.set_rollback(True)
        except IntegrityError:
            result = FlowProblem("CHALLENGE_INVALID")
        if isinstance(result, FlowProblem):
            # Discard in-memory mutations from the rolled-back savepoint.
            invitation.refresh_from_db()
            return invalid(invitation)
        return result


def expire_one():
    """Bounded secret erasure, not metadata retention/account deletion."""
    gate()
    now = timezone.now()
    candidate = (
        PersonalInvitation.objects.filter(
            Q(expires_at__lte=now)
            | Q(ceremony_expires_at__lte=now)
            | Q(proof_expires_at__lte=now),
            cancelled_at__isnull=True,
            consumed_at__isnull=True,
        )
        .order_by("expires_at", "id")
        .first()
    )
    if not candidate:
        return False
    with transaction.atomic():
        _, invitation = lock(candidate.pk)
        now = timezone.now()
        if invitation.consumed_at or invitation.cancelled_at:
            return True
        if now >= invitation.expires_at:
            invitation.cancelled_at = now
            erase(invitation)
            audit(invitation, "expired")
        else:
            if invitation.ceremony_expires_at and now >= invitation.ceremony_expires_at:
                erase_ceremony(invitation)
                audit(invitation, "setup_expired")
            if invitation.proof_expires_at and now >= invitation.proof_expires_at:
                invitation.proof_digest = ""
                invitation.proof_expires_at = None
                erase_mail(invitation, "expired")
        invitation.save()
    return True
