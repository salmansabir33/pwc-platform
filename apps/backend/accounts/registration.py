"""Transactional registration/reset services. No login or credential issuance.

Services enforce ownership even if callers never use model.full_clean(). Failed
proofs return FlowProblem after committing counters; don't raise inside atomic.
"""

import copy
import ipaddress
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .email_identity import normalize_email
from .flow_security import (
    FlowProblem,
    abuse_digest,
    configured,
    digest,
    matches,
    new_secret,
    seal,
)
from .models import (
    AssuranceIntent,
    AuthAbuseBucket,
    AuthChallenge,
    AuthSession,
    DeliveryIntent,
    MfaFactor,
    SecurityEvent,
    UserContact,
)

User = get_user_model()
LIFETIMES = {"registration": 1800, "reset": 900}


def flow_uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def event(code, result="success", user=None, **details):
    SecurityEvent.objects.create(subject=user, event=code, result=result, **details)


def spend(ip, route, *, target=None, flow=None, delivery=False):
    """Commit shared bounded counters independently of workflow rollback."""
    try:
        address = ipaddress.ip_address(str(ip).split("%", 1)[0])
        ip = (
            str(address.ipv4_mapped)
            if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped
            else address.compressed
        )
    except ValueError:
        ip = "unknown"
    now = timezone.now()
    dimensions = [("ip", ip, route, 900, 30)]
    if delivery:
        dimensions.extend(
            [
                ("target", target, "email_send", 60, 1),
                ("target", target, "email_send", 3600, 5),
                (
                    "global",
                    "global",
                    "email_send",
                    3600,
                    settings.PWC_AUTH_GLOBAL_SENDS_PER_HOUR,
                ),
            ]
        )
    if flow:
        dimensions.append(("flow", str(flow), route, 900, 30))
    keys = []
    for dimension, value, name, seconds, limit in dimensions:
        start = datetime.fromtimestamp(
            int(now.timestamp()) // seconds * seconds, tz=dt_timezone.utc
        )
        keys.append(
            (
                dimension,
                abuse_digest(str(value)),
                f"{name}:{seconds}",
                start,
                seconds,
                limit,
            )
        )
    limited = False
    first_limit = False
    retry = 1
    with transaction.atomic():
        for dimension, key, name, start, seconds, limit in sorted(
            keys,
            key=lambda row: (
                {"ip": 0, "global": 1, "target": 2, "flow": 3}[row[0]],
                row[1],
                row[4],
                row[2],
                row[3],
            ),
        ):
            lookup = dict(
                dimension=dimension, key_digest=key, route=name, window_start=start
            )
            bucket, _ = AuthAbuseBucket.objects.select_for_update().get_or_create(
                **lookup, defaults={"expires_at": start + timedelta(seconds=seconds)}
            )
            crossed = bucket.count == limit
            bucket.count = min(bucket.count + 1, limit + 1)
            bucket.save(update_fields=["count"])
            if bucket.count > limit:
                limited = True
                first_limit = crossed
                retry = max(retry, int((bucket.expires_at - now).total_seconds()) + 1)
                break  # no new target/flow buckets after an upstream denial
        if first_limit:
            event("auth.rate_limited", "denied")
    return FlowProblem("RATE_LIMITED", 429, retry_after=retry) if limited else None


def legacy_match(canonical, original):
    # A legacy email is a reservation, NEVER a recovery/merge authority. Normal
    # ASCII cases use the DB lookup; bounded anomaly inventory handles IDNA and
    # whitespace aliases without an unbounded Python scan in a public endpoint.
    if User.objects.filter(
        Q(email__iexact=canonical) | Q(email__iexact=original.strip())
    ).exists():
        return True
    candidates = list(
        User.objects.filter(Q(email__regex=r"[^!-~]") | Q(email__endswith="."))
        .exclude(email="")
        .values_list("email", flat=True)[:101]
    )
    if len(candidates) > 100:
        return True  # fail closed until reviewed legacy inventory/enrollment
    for value in candidates:
        try:
            if normalize_email(value) == canonical:
                return True
        except ValidationError:
            # Do not silently free an ambiguous legacy reservation (e.g. a DNS
            # trailing-dot spelling). Hold registration inert pending inventory;
            # this is an availability gate, never ownership/merging authority.
            return True
    return False


@sensitive_variables()
def queue_proof(challenge, proof):
    key_id, ciphertext = seal(
        {
            "purpose": challenge.purpose,
            "recipient": challenge.normalized_target,
            "flow_id": str(challenge.pk),
            "proof": proof,
            "generation": challenge.generation,
        }
    )
    DeliveryIntent.objects.create(
        challenge=challenge,
        generation=challenge.generation,
        template=challenge.purpose if challenge.eligible else "placeholder",
        key_id=key_id,
        encrypted_payload=ciphertext,
        next_attempt_at=timezone.now(),
    )


@sensitive_variables()
def request_flow(purpose, email, ip):
    configured()
    if purpose not in LIFETIMES:
        return FlowProblem("VALIDATION_ERROR")
    try:
        target = normalize_email(email)
    except ValidationError:
        return FlowProblem(
            "VALIDATION_ERROR", fields={"email": ["Supply a valid email address."]}
        )
    problem = spend(ip, "request", target=target, delivery=True)
    if problem:
        return problem
    control, proof = new_secret(), new_secret()
    with transaction.atomic():
        user = contact = None
        eligible = False
        if purpose == "reset":
            # Locate without lock; then acquire User -> Contact and recheck.
            candidate = UserContact.objects.filter(
                kind="email",
                normalized_value=target,
                verified_at__isnull=False,
                retired_at__isnull=True,
                is_primary=True,
            ).first()
            if candidate:
                user = (
                    User.objects.select_for_update()
                    .filter(pk=candidate.user_id)
                    .first()
                )
                contact = (
                    UserContact.objects.select_for_update()
                    .filter(pk=candidate.pk)
                    .first()
                )
                eligible = bool(
                    user
                    and contact
                    and user.is_active
                    and contact.user_id == user.pk
                    and contact.normalized_value == target
                    and contact.verified_at
                    and not contact.retired_at
                    and contact.is_primary
                )
                if not eligible:
                    user = contact = None  # identical inert reset ownership shape
        else:
            eligible = not (
                UserContact.objects.filter(
                    kind="email",
                    normalized_value=target,
                    verified_at__isnull=False,
                    retired_at__isnull=True,
                ).exists()
                or legacy_match(target, email)
            )
        now = timezone.now()
        challenge = AuthChallenge.objects.create(
            purpose=purpose,
            user=user,
            target_contact=contact,
            auth_epoch=user.auth_epoch if user else None,
            normalized_target=target,
            flow_control_digest=digest(control),
            proof_digest=digest(proof),
            eligible=eligible,
            created_at=now,
            last_issued_at=now,
            expires_at=now + timedelta(seconds=LIFETIMES[purpose]),
        )
        queue_proof(challenge, proof)  # ciphertext path also used for inert requests
        event(f"auth.{purpose}_requested")
    return {
        "status": "accepted",
        "flow_id": str(challenge.pk),
        "flow_control": control,
        "expires_in": LIFETIMES[purpose],
    }


def cancel_deliveries(challenge_ids, now):
    DeliveryIntent.objects.filter(
        challenge_id__in=challenge_ids, state__in=["pending", "leased"]
    ).update(
        state="cancelled",
        encrypted_payload=None,
        key_id="",
        secret_deleted_at=now,
        lease_expires_at=None,
    )


def failed(challenge, now):
    if challenge.consumed_at is None and challenge.invalidated_at is None:
        challenge.failure_count = min(challenge.failure_count + 1, 5)
        if challenge.failure_count >= 5 or challenge.expires_at <= now:
            challenge.invalidated_at = now
            cancel_deliveries([challenge.pk], now)
        challenge.save(update_fields=["failure_count", "invalidated_at"])
    event("auth.proof_denied", "denied")
    return FlowProblem("CHALLENGE_INVALID")


def usable(challenge, purpose, proof, now):
    return bool(
        challenge.purpose == purpose
        and challenge.eligible
        and challenge.consumed_at is None
        and challenge.invalidated_at is None
        and challenge.failure_count < 5
        and now < challenge.expires_at
        and matches(proof, challenge.proof_digest)
    )


@sensitive_variables()
def resend_flow(purpose, flow_id, flow_control, ip):
    configured()
    problem = spend(ip, "resend")
    if problem:
        return problem
    flow_id = flow_uuid(flow_id)
    if not flow_id:
        return {"status": "accepted"}
    # Only the holder of this flow control can spend the target resend budget.
    snapshot = AuthChallenge.objects.filter(pk=flow_id, purpose=purpose).first()
    if not snapshot or not matches(flow_control, snapshot.flow_control_digest):
        return {"status": "accepted"}
    if (
        snapshot.consumed_at
        or snapshot.invalidated_at
        or snapshot.expires_at <= timezone.now()
    ):
        return {"status": "accepted"}
    if timezone.now() < snapshot.last_issued_at + timedelta(seconds=60):
        return {"status": "accepted"}  # coalesce this flow inside cooldown
    problem = spend(
        ip, "delivery_resend", target=snapshot.normalized_target, delivery=True
    )
    if problem:
        return problem
    with transaction.atomic():
        # No User mutation here, so this only locks the flow. Never acquires User
        # after it, preserving User -> challenge order in confirmations/reset.
        challenge = AuthChallenge.objects.select_for_update().filter(pk=flow_id).first()
        now = timezone.now()
        if (
            challenge is None
            or challenge.purpose != purpose
            or not matches(flow_control, challenge.flow_control_digest)
            or now < challenge.last_issued_at + timedelta(seconds=60)
            or challenge.consumed_at
            or challenge.invalidated_at
            or challenge.expires_at <= now
        ):
            return {"status": "accepted"}
        cancel_deliveries([challenge.pk], now)
        challenge.generation += 1
        proof = new_secret()
        challenge.proof_digest = digest(proof)
        challenge.delivery_state = "pending"
        challenge.last_issued_at = now
        challenge.save(
            update_fields=[
                "generation",
                "proof_digest",
                "delivery_state",
                "last_issued_at",
            ]
        )
        queue_proof(challenge, proof)
        event("auth.proof_resent")
    return {"status": "accepted"}


@sensitive_variables()
def confirm_flow(purpose, flow_id, proof, password, ip):
    configured()
    flow_id = flow_uuid(flow_id)
    problem = spend(ip, "confirm", flow=flow_id or "invalid")
    if problem:
        return problem
    snapshot = AuthChallenge.objects.filter(pk=flow_id).first() if flow_id else None
    if not snapshot or snapshot.purpose != purpose:
        event("auth.proof_denied", "denied")
        return FlowProblem("CHALLENGE_INVALID")
    with transaction.atomic():
        user = contact = factor = None
        if purpose == "reset":
            if not snapshot.user_id or not snapshot.target_contact_id:
                challenge = (
                    AuthChallenge.objects.select_for_update()
                    .filter(pk=snapshot.pk)
                    .first()
                )
                return (
                    failed(challenge, timezone.now())
                    if challenge
                    else FlowProblem("CHALLENGE_INVALID")
                )
            user = User.objects.select_for_update().filter(pk=snapshot.user_id).first()
            contact = (
                UserContact.objects.select_for_update()
                .filter(pk=snapshot.target_contact_id)
                .first()
            )
            if user is None or contact is None:
                return FlowProblem("CHALLENGE_INVALID")
            factor = (
                MfaFactor.objects.select_for_update()
                .filter(user=user, state="active")
                .first()
            )
            # Acquire all session locks now, before the challenge/intent locks.
            list(
                AuthSession.objects.select_for_update().filter(user=user).order_by("id")
            )
        challenge = (
            AuthChallenge.objects.select_for_update().filter(pk=snapshot.pk).first()
        )
        if challenge is None:
            return FlowProblem("CHALLENGE_INVALID")
        now = timezone.now()
        if not usable(challenge, purpose, proof, now):
            return failed(challenge, now)
        if purpose == "reset" and not (
            user.is_active
            and challenge.user_id == user.pk
            and challenge.target_contact_id == contact.pk
            and contact.user_id == user.pk
            and challenge.auth_epoch == user.auth_epoch
            and contact.kind == "email"
            and contact.is_primary
            and contact.verified_at
            and not contact.retired_at
            and contact.normalized_value == challenge.normalized_target
        ):
            return failed(challenge, now)
        if (
            factor
            and not AuthSession.objects.filter(
                pk=factor.enrollment_session_id, user=user
            ).exists()
        ):
            return failed(challenge, now)
        candidate = (
            copy.copy(user)
            if user
            else User(username="", email=challenge.normalized_target)
        )
        candidate.email = challenge.normalized_target
        try:
            if not isinstance(password, str):
                raise ValidationError("Supply a valid password.")
            validate_password(password, candidate)
        except ValidationError as exc:
            return FlowProblem(
                "VALIDATION_ERROR",
                fields={
                    (
                        "password" if purpose == "registration" else "new_password"
                    ): exc.messages
                },
            )
        if purpose == "registration":
            if (
                challenge.user_id
                or challenge.target_contact_id
                or legacy_match(
                    challenge.normalized_target, challenge.normalized_target
                )
            ):
                return failed(challenge, now)
            try:
                with transaction.atomic():  # unique collision rolls back User too
                    user = User(
                        username=f"pwc_{uuid.uuid4().hex}",
                        email=challenge.normalized_target,
                    )
                    user.set_password(password)
                    user.save(force_insert=True)
                    UserContact.objects.create(
                        user=user,
                        kind="email",
                        display_value=challenge.normalized_target,
                        normalized_value=challenge.normalized_target,
                        verified_at=now,
                        is_primary=True,
                    )
            except IntegrityError:
                return failed(challenge, now)
        else:
            previous_hold_state = user.recovery_hold_state
            user.set_password(password)
            user.auth_epoch += 1
            user.recovery_generation += 1
            if user.recovery_hold_state == "clear":
                user.recovery_hold_state = "restricted"
                user.hold_set_at = now
                user.hold_reason = "password_reset"
                user.hold_factor = factor
                user.hold_factor_revision = factor.revision if factor else None
            user.hold_cleared_event = None
            # Defensive ownership validation independent of full_clean().
            if user.hold_factor_id and user.hold_factor.user_id != user.pk:
                return failed(challenge, now)
            user.save(
                update_fields=[
                    "password",
                    "auth_epoch",
                    "recovery_generation",
                    "recovery_hold_state",
                    "hold_set_at",
                    "hold_reason",
                    "hold_factor",
                    "hold_factor_revision",
                    "hold_cleared_event",
                ]
            )
            AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
                revoked_at=now, revocation_reason="password_reset"
            )
            AssuranceIntent.objects.filter(
                user=user, consumed_at__isnull=True, invalidated_at__isnull=True
            ).update(invalidated_at=now)
            others = AuthChallenge.objects.filter(
                user=user, consumed_at__isnull=True, invalidated_at__isnull=True
            ).exclude(pk=challenge.pk)
            ids = list(others.values_list("pk", flat=True))
            others.update(invalidated_at=now)
            cancel_deliveries(ids, now)
        challenge.consumed_at = now
        challenge.save(update_fields=["consumed_at"])
        cancel_deliveries([challenge.pk], now)
        if purpose == "reset":
            event(
                "auth.reset_completed",
                user=user,
                reason="password_reset",
                auth_epoch=user.auth_epoch,
                recovery_generation=user.recovery_generation,
                previous_hold_state=previous_hold_state,
                new_hold_state=user.recovery_hold_state,
                factor_id_snapshot=user.hold_factor_id,
                factor_revision=user.hold_factor_revision,
            )
        else:
            event("auth.registration_completed", user=user)
        if purpose == "reset":
            key_id, ciphertext = seal(
                {
                    "purpose": "password_changed",
                    "recipient": contact.normalized_value,
                    "flow_id": str(challenge.pk),
                    "generation": challenge.generation + 1,
                }
            )
            DeliveryIntent.objects.create(
                challenge=challenge,
                generation=challenge.generation + 1,
                template="reset",
                key_id=key_id,
                encrypted_payload=ciphertext,
            )
    return {"status": "verified"} if purpose == "registration" else None
