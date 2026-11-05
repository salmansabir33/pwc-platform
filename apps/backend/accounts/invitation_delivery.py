"""Bounded invitation outbox worker; synthetic default, SMTP adapter-compatible.

Non-test profiles fail before configuration/DB/I/O. No SMTP configuration switch
or operational acceptance is inferred by accepting a prepared adapter instance.
"""

from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .delivery import deliver_message
from .flow_security import unseal
from .models import PersonalInvitation
from .personal_invitations import (
    gate,
    lock,
    pending,
    source_live,
    erase_mail,
    audit,
    matches,
)


class SyntheticAdapter:
    def send(self, recipient, subject, body, *, expires_at):
        deliver_message(recipient, subject, body)


@sensitive_variables()
def dispatch_one(*, adapter=None):
    gate()
    now = timezone.now()
    candidate = (
        PersonalInvitation.objects.filter(
            Q(mail_state="pending", mail_next_at__lte=now)
            | Q(mail_state="leased", mail_lease_at__lte=now)
        )
        .order_by("mail_next_at", "id")
        .first()
    )
    if not candidate:
        return False
    with transaction.atomic():
        issuer, invitation = lock(candidate.pk)
        now = timezone.now()
        eligible = (
            invitation.mail_state == "pending"
            and invitation.mail_next_at <= now
            or invitation.mail_state == "leased"
            and invitation.mail_lease_at <= now
        )
        if not eligible:
            return True
        if not pending(invitation) or not source_live(invitation, issuer, "deliver"):
            erase_mail(
                invitation, "expired" if now >= invitation.expires_at else "cancelled"
            )
            invitation.save()
            return True
        if invitation.mail_attempts >= 5:
            erase_mail(invitation, "failed")
            invitation.save()
            audit(invitation, "delivery_failed", result="failure")
            return True
        invitation.mail_state = "leased"
        invitation.mail_attempts += 1
        invitation.mail_lease_at = now + timedelta(seconds=60)
        invitation.save()
        generation, attempt = invitation.mail_generation, invitation.mail_attempts
    expiry = invitation.expires_at
    try:
        with transaction.atomic():
            issuer, invitation = lock(candidate.pk)
            if (
                invitation.mail_state != "leased"
                or invitation.mail_generation != generation
                or invitation.mail_attempts != attempt
            ):
                return True
            payload = unseal(invitation.mail_key, invitation.mail_payload)
            purpose, secret = payload.get("purpose"), payload.get("secret")
            expiry = (
                invitation.expires_at
                if purpose == "token"
                else invitation.proof_expires_at
            )
            stored = (
                invitation.token_digest
                if purpose == "token"
                else invitation.proof_digest
            )
            if (
                purpose not in {"token", "email-proof"}
                or not expiry
                or timezone.now() >= expiry
                or payload.get("invitation_id") != str(invitation.pk)
                or payload.get("recipient") != invitation.recipient
                or payload.get("generation") != generation
                or not pending(invitation)
                or not source_live(invitation, issuer, "deliver")
                or not matches(invitation, purpose, secret, stored)
            ):
                erase_mail(invitation, "cancelled")
                invitation.save()
                return True
            recipient = invitation.recipient
            if purpose == "token":
                fragment = urlencode(
                    {"invitation_id": str(invitation.pk), "token": secret}
                )
                subject = "PWC personal invitation / ذاتی دعوت"
                message = (
                    "Complete email, password and authenticator setup within 24 hours. "
                    "No Founder, verifier or NGO authority is granted. Opening does not accept this invitation.\n"
                    "۲۴ گھنٹوں میں ای میل، پاس ورڈ اور آتھنٹیکیٹر مکمل کریں۔ کوئی انتظامی اختیار نہیں ملتا۔\n"
                    + settings.PWC_AUTH_LINK_ORIGIN
                    + "/account/invite#"
                    + fragment
                )
            else:
                subject = "PWC email confirmation / ای میل کی تصدیق"
                message = (
                    "Enter this proof only in your own PWC invitation form. Never share it.\n"
                    "یہ تصدیقی کوڈ صرف اپنے دعوتی فارم میں درج کریں۔ کسی کو نہ دیں۔\n"
                    + secret
                )
        # No locks across I/O. Cancellation during an in-flight send cannot retract
        # mail; server-side token/proof/expiry checks still prevent its acceptance.
        (adapter or SyntheticAdapter()).send(
            recipient, subject, message, expires_at=expiry
        )
        success = True
    except Exception:
        success = False  # Never stringify provider failures or decrypted material.
    with transaction.atomic():
        _, invitation = lock(candidate.pk)
        if (
            invitation.mail_state != "leased"
            or invitation.mail_generation != generation
            or invitation.mail_attempts != attempt
        ):
            return True
        if not pending(invitation) or timezone.now() >= expiry:
            erase_mail(invitation, "expired")
        elif success:
            erase_mail(invitation, "sent")
            audit(invitation, "delivery_sent")
        elif attempt == 5:
            erase_mail(invitation, "failed")
            audit(invitation, "delivery_failed", result="failure")
        else:
            invitation.mail_state = "pending"
            invitation.mail_lease_at = None
            invitation.mail_next_at = timezone.now() + timedelta(
                minutes=2 ** (attempt - 1)
            )
            audit(invitation, "delivery_retry", result="failure")
        invitation.save()
    return True
