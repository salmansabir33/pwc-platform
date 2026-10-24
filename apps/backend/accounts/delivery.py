"""Bounded encrypted PostgreSQL outbox; synthetic Django mail adapter only."""

from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .flow_security import FlowProblem, configured, unseal
from .models import AuthChallenge, DeliveryIntent, UserContact
from .registration import event

MAX_ATTEMPTS = 5


def erase(intent, state, now):
    intent.state = state
    intent.encrypted_payload = None
    intent.key_id = ""
    intent.secret_deleted_at = now
    intent.lease_expires_at = None
    intent.save(
        update_fields=[
            "state",
            "encrypted_payload",
            "key_id",
            "secret_deleted_at",
            "lease_expires_at",
        ]
    )


def deliver_message(recipient, subject, body):
    # Deliberately cannot select an SMTP provider with EMAIL_BACKEND. Production
    # adapter enablement is a separate operational/code review gate.
    connection = get_connection("django.core.mail.backends.locmem.EmailBackend")
    sent = send_mail(
        subject, body, "no-reply@pwc.invalid", [recipient], connection=connection
    )
    if sent != 1:
        raise RuntimeError("Synthetic delivery did not accept the message.")


@sensitive_variables()
def dispatch_one():
    configured()
    now = timezone.now()
    with transaction.atomic():
        intent = (
            DeliveryIntent.objects.select_for_update(skip_locked=True)
            .filter(
                Q(state="pending", next_attempt_at__lte=now)
                | Q(state="leased", lease_expires_at__lte=now)
            )
            .order_by("next_attempt_at", "id")
            .first()
        )
        if intent is None:
            return False
        if intent.attempts >= MAX_ATTEMPTS:
            erase(intent, "failed", now)
            event("auth.delivery_failed", "failure")
            return True
        intent.attempts += 1
        intent.state = "leased"
        intent.lease_expires_at = now + timedelta(seconds=60)
        intent.save(update_fields=["attempts", "state", "lease_expires_at"])
        intent_id, challenge_id, attempt = (
            intent.pk,
            intent.challenge_id,
            intent.attempts,
        )
    # Lease is committed; no locks are held across I/O, including decrypt/send.
    try:
        with transaction.atomic():
            challenge = (
                AuthChallenge.objects.select_for_update()
                .filter(pk=challenge_id)
                .first()
            )
            intent = (
                DeliveryIntent.objects.select_for_update().filter(pk=intent_id).first()
            )
            if challenge is None or intent is None:
                return True
            if intent.state != "leased" or intent.attempts != attempt:
                return True
            payload = unseal(intent.key_id, intent.encrypted_payload)
            if not isinstance(payload, dict):
                raise FlowProblem("AUTH_UNAVAILABLE", 503)
            notice = payload.get("purpose") == "password_changed"
            now = timezone.now()
            deadline = (
                (challenge.consumed_at + timedelta(minutes=15))
                if notice and challenge.consumed_at
                else challenge.expires_at
            )
            valid = (
                payload.get("flow_id") == str(challenge.pk)
                and payload.get("generation") == intent.generation
                and payload.get("recipient") == challenge.normalized_target
            )
            if notice:
                valid = (
                    valid
                    and challenge.purpose == "reset"
                    and intent.template == "reset"
                    and challenge.consumed_at is not None
                    and intent.generation == challenge.generation + 1
                )
            else:
                valid = (
                    valid
                    and payload.get("purpose") == challenge.purpose
                    and intent.generation == challenge.generation
                    and challenge.consumed_at is None
                    and challenge.invalidated_at is None
                    and challenge.eligible
                    and intent.template == challenge.purpose
                )
                if challenge.purpose == "reset":
                    valid = (
                        valid
                        and UserContact.objects.filter(
                            pk=challenge.target_contact_id,
                            user_id=challenge.user_id,
                            normalized_value=challenge.normalized_target,
                            kind="email",
                            verified_at__isnull=False,
                            retired_at__isnull=True,
                            is_primary=True,
                            user__is_active=True,
                            user__auth_epoch=challenge.auth_epoch,
                        ).exists()
                    )
                elif challenge.purpose == "registration":
                    valid = (
                        valid
                        and challenge.user_id is None
                        and challenge.target_contact_id is None
                    )
            if now >= deadline or not valid:
                erase(intent, "expired" if now >= deadline else "cancelled", now)
                return True
            recipient = payload["recipient"]
            if notice:
                subject, body = (
                    "PWC password changed",
                    "Your PWC account password was changed. If this was not you, use the reviewed support channel. No NGO authority was changed.",
                )
            else:
                proof = payload.get("proof")
                if (
                    not isinstance(proof, str)
                    or len(proof) != 43
                    or not proof.isascii()
                ):
                    raise FlowProblem("AUTH_UNAVAILABLE", 503)
                subject = (
                    "Verify your PWC email"
                    if challenge.purpose == "registration"
                    else "Reset your PWC password"
                )
                fragment = urlencode(
                    {
                        "flow_id": str(challenge.pk),
                        "proof": proof,
                        "purpose": challenge.purpose,
                    }
                )
                body = f"Complete this request explicitly in the PWC client. Do not share this link.\n{settings.PWC_AUTH_LINK_ORIGIN}/account/confirm#{fragment}\nOpening or previewing this link alone does not change your account."
        deliver_message(recipient, subject, body)
        success = True
    except Exception:
        # Do not log exception payloads (an adapter may embed the entire email).
        # Failure is recorded as a bounded code; DB failure still propagates if
        # even the recovery transaction cannot access PostgreSQL.
        success = False
    with transaction.atomic():
        challenge = (
            AuthChallenge.objects.select_for_update().filter(pk=challenge_id).first()
        )
        intent = DeliveryIntent.objects.select_for_update().filter(pk=intent_id).first()
        if challenge is None or intent is None:
            return True
        if intent.state != "leased" or intent.attempts != attempt:
            return True  # stale worker never overwrites a resend/reset/reclaim
        now = timezone.now()
        # No resend can reuse this row's generation. A consumed proof row is
        # cancelled by confirmation; password-changed notice is separate N+1.
        deadline = (
            (challenge.consumed_at + timedelta(minutes=15))
            if (
                challenge.purpose == "reset"
                and challenge.consumed_at
                and intent.generation == challenge.generation + 1
            )
            else challenge.expires_at
        )
        if now >= deadline:
            erase(intent, "expired", now)
        elif success:
            erase(intent, "sent", now)
            if intent.generation == challenge.generation:
                challenge.delivery_state = "sent"
                challenge.save(update_fields=["delivery_state"])
            event("auth.delivery_sent")
        elif intent.attempts >= MAX_ATTEMPTS:
            erase(intent, "failed", now)
            event("auth.delivery_failed", "failure")
        else:
            intent.state = "pending"
            intent.lease_expires_at = None
            intent.next_attempt_at = now + timedelta(minutes=2 ** (intent.attempts - 1))
            intent.save(update_fields=["state", "lease_expires_at", "next_attempt_at"])
            event("auth.delivery_retry", "failure")
    return True
