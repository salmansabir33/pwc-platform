"""Personal MFA/assurance. Caller holds User then factor/session locks.

Normal denial returns preserve attempt counters and replay evidence. No domain
permission registry is implied: unmapped operations are never authorized.
"""

import json
import re
import uuid
from datetime import timedelta

import pyotp
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.middleware.csrf import rotate_token
from django.utils import timezone
from django.utils.crypto import salted_hmac, constant_time_compare
from django.views.decorators.debug import sensitive_variables

from . import sessions
from .flow_security import FlowProblem, new_secret, abuse_digest
from .models import (
    User,
    AuthSession,
    AuthChallenge,
    MfaFactor,
    MfaRecoveryCode,
    AssuranceIntent,
    AuthAbuseBucket,
    SecurityEvent,
)
from .registration import event

OPERATIONS = frozenset(
    (
        "mfa.enroll",
        "mfa.remove",
        "mfa.recovery_codes.rotate",
        "sessions.logout_all",
        "sessions.revoke",
        "recovery_hold.clear",
    )
)


def problem(code="CHALLENGE_INVALID", status=400):
    return FlowProblem(code, status)


def configured():
    sessions.configured()
    if (
        not settings.PWC_AUTH_MFA_ENABLED
        or not isinstance(settings.PWC_AUTH_MFA_PROOF_KEY, str)
        or len(settings.PWC_AUTH_MFA_PROOF_KEY) < 43
    ):
        raise problem("AUTH_UNAVAILABLE", 503)
    cipher(settings.PWC_AUTH_MFA_ACTIVE_KEY)


@sensitive_variables()
def cipher(key):
    try:
        if not isinstance(key, str) or not key or len(key) > 100:
            raise ValueError()
        return Fernet(settings.PWC_AUTH_MFA_KEYS[key])
    except (KeyError, TypeError, ValueError):
        raise problem("AUTH_UNAVAILABLE", 503) from None


@sensitive_variables()
def keyed(purpose, value):
    return salted_hmac(
        "pwc.mfa." + purpose + ".v1",
        value,
        secret=settings.PWC_AUTH_MFA_PROOF_KEY,
        algorithm="sha256",
    ).hexdigest()


def active(user):
    factor = MfaFactor.objects.filter(user=user, state="active").first()
    if factor and factor.enrollment_session.user_id != user.pk:
        raise problem("AUTH_UNAVAILABLE", 503)
    return factor


@sensitive_variables()
def open_secret(factor):
    try:
        if factor.enrollment_session.user_id != factor.user_id:
            raise ValueError()
        data = json.loads(cipher(factor.key_id).decrypt(bytes(factor.encrypted_secret)))
        if (
            data.get("user") != str(factor.user_id)
            or data.get("factor") != str(factor.pk)
            or data.get("purpose") != "totp-v1"
            or not re.fullmatch(r"[A-Z2-7]{32}", data.get("secret", ""))
        ):
            raise ValueError()
        return data["secret"]
    except (InvalidToken, ValueError, TypeError, UnicodeError, AttributeError):
        raise problem("AUTH_UNAVAILABLE", 503) from None


def attempt(key, start=None):
    now = timezone.now()
    start = start or now.replace(minute=now.minute // 5 * 5, second=0, microsecond=0)
    row, _ = AuthAbuseBucket.objects.select_for_update().get_or_create(
        dimension="flow",
        key_digest=abuse_digest("mfa:" + str(key)),
        route="mfa:300",
        window_start=start,
        defaults={"expires_at": start + timedelta(minutes=5)},
    )
    row.count = min(row.count + 1, 6)
    row.save(update_fields=["count"])
    return row.count <= 5


@sensitive_variables()
def verify_totp(factor, code):
    secret = open_secret(factor)
    if (
        not attempt(factor.pk, factor.created_at if factor.state == "pending" else None)
        or not isinstance(code, str)
        or not re.fullmatch(r"[0-9]{6}", code)
    ):
        return False
    step = int(timezone.now().timestamp()) // 30
    otp = pyotp.TOTP(secret)
    for candidate in (step, step - 1, step + 1):
        if (
            candidate >= 0
            and (
                factor.last_accepted_timestep is None
                or candidate > factor.last_accepted_timestep
            )
            and otp.verify(code, for_time=candidate * 30)
        ):
            factor.last_accepted_timestep = candidate
            factor.save(update_fields=["last_accepted_timestep"])
            return True
    event("auth.mfa_denied", "denied", user=factor.user)
    return False


def observe(session, factor):
    if (
        session.user_id != factor.user_id
        or factor.enrollment_session.user_id != factor.user_id
    ):
        raise problem("AUTH_UNAVAILABLE", 503)
    session.last_mfa_at = timezone.now()
    session.mfa_method = "totp"
    session.factor_revision = factor.revision
    session.save(update_fields=["last_mfa_at", "mfa_method", "factor_revision"])


def recent(session, factor):
    now = timezone.now()
    return bool(
        session.mfa_method == "totp"
        and session.factor_revision == factor.revision
        and session.last_mfa_at
        and now - timedelta(minutes=5) < session.last_mfa_at <= now
    )


@sensitive_variables()
def codes(user, factor):
    if (
        factor.user_id != user.pk
        or factor.enrollment_session.user_id != user.pk
        or factor.state != "active"
    ):
        raise problem("AUTH_UNAVAILABLE", 503)
    MfaRecoveryCode.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    set_id = uuid.uuid4()
    result = []
    for _ in range(10):
        code = new_secret()
        MfaRecoveryCode.objects.create(
            user=user,
            factor=factor,
            factor_revision=factor.revision,
            set_id=set_id,
            code_digest=keyed(
                "recovery", f"{user.pk}:{factor.pk}:{factor.revision}:{code}"
            ),
        )
        result.append(code)
    event("auth.recovery_codes_issued", user=user)
    return result


@sensitive_variables()
def begin_login(request, user, factor, label, transport, portal, contact):
    configured()
    if factor.user_id != user.pk or factor.enrollment_session.user_id != user.pk:
        raise problem("AUTH_UNAVAILABLE", 503)
    now = timezone.now()
    control = new_secret()
    flow = AuthChallenge(
        id=uuid.uuid4(),
        user=user,
        purpose="preauth_mfa",
        target_contact=contact,
        transport=transport,
        portal=portal,
        device_label=label,
        auth_epoch=user.auth_epoch,
        factor_revision=factor.revision,
        created_at=now,
        last_issued_at=now,
        expires_at=now + timedelta(minutes=5),
        eligible=True,
        delivery_state="cancelled",
    )
    if transport == "web":
        request.session.flush()
        request.session.create()
        request.session.set_expiry(flow.expires_at)
        request.session["pwc_preauth_id"] = str(flow.pk)
        request.session.save()
        rotate_token(request)
        binding = request.session.session_key
    else:
        binding = control
    flow.client_digest = keyed("client", f"{flow.pk}:{binding}")
    flow.flow_control_digest = keyed("control", f"{flow.pk}:{control}")
    flow.proof_digest = password_binding(flow, user, factor)
    flow.save()
    event("auth.mfa_challenge_issued", user=user)
    return {
        "status": "mfa_required",
        "challenge_id": str(flow.pk),
        "preauth_control": control,
        "expires_in": 300,
    }


@sensitive_variables()
def password_binding(flow, user, factor):
    return keyed(
        "password",
        json.dumps(
            [
                str(flow.pk),
                str(user.pk),
                user.password,
                str(factor.pk),
                str(flow.target_contact_id),
                flow.target_contact.normalized_value,
                flow.auth_epoch,
                flow.factor_revision,
                flow.transport,
                flow.portal,
                flow.device_label,
                flow.client_digest,
                flow.flow_control_digest,
                flow.expires_at.isoformat(),
            ],
            separators=(",", ":"),
        ),
    )


@sensitive_variables()
def complete_login(request, data, transport, portal):
    from django.db import transaction

    configured()
    snapshot = AuthChallenge.objects.filter(
        pk=safe_uuid(data["challenge_id"]), purpose="preauth_mfa"
    ).first()
    if not snapshot or not snapshot.user_id:
        return problem()
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=snapshot.user_id).first()
        if not user:
            return problem()
        contact = sessions.current_contact(user, lock=True)
        factors = list(
            MfaFactor.objects.select_for_update().filter(user=user).order_by("id")
        )
        factor = next((f for f in factors if f.state == "active"), None)
        list(AuthSession.objects.select_for_update().filter(user=user).order_by("id"))
        flow = (
            AuthChallenge.objects.select_for_update()
            .filter(pk=snapshot.pk, user=user, purpose="preauth_mfa")
            .first()
        )
        now = timezone.now()
        if (
            not flow
            or not factor
            or not user.is_active
            or not contact
            or flow.consumed_at
            or flow.invalidated_at
            or flow.expires_at <= now
            or flow.created_at > now
            or flow.auth_epoch != user.auth_epoch
            or flow.factor_revision != factor.revision
            or flow.target_contact_id != contact.pk
            or flow.transport != transport
            or flow.portal != portal
        ):
            return problem()
        if transport == "web" and (
            request.session.get("pwc_preauth_id") != str(flow.pk)
            or request.session.get("_auth_user_id")
        ):
            return problem()
        binding = (
            request.session.session_key
            if transport == "web"
            else data["preauth_control"]
        )
        if (
            not constant_time_compare(
                flow.client_digest or "", keyed("client", f"{flow.pk}:{binding}")
            )
            or not constant_time_compare(
                flow.flow_control_digest,
                keyed("control", f'{flow.pk}:{data["preauth_control"]}'),
            )
            or not constant_time_compare(
                flow.proof_digest,
                password_binding(flow, user, factor),
            )
        ):
            return problem()
        if flow.failure_count >= 5:
            return problem()
        # Count all verification attempts within the five-minute challenge.
        flow.failure_count += 1
        flow.save(update_fields=["failure_count"])
        method = data["method"]
        if method == "totp":
            valid = verify_totp(factor, data["code"])
        elif method == "recovery_code":
            open_secret(factor)  # missing factor keys do not silently downgrade
            row = (
                MfaRecoveryCode.objects.select_for_update()
                .filter(
                    user=user,
                    factor=factor,
                    factor_revision=factor.revision,
                    consumed_at__isnull=True,
                    code_digest=keyed(
                        "recovery",
                        f'{user.pk}:{factor.pk}:{factor.revision}:{data["code"]}',
                    ),
                )
                .first()
            )
            valid = bool(row)
        else:
            valid = False
        if not valid:
            return problem()
        now = timezone.now()
        if now >= flow.expires_at:
            return problem()
        if method == "recovery_code":
            row.consumed_at = now
            row.save(update_fields=["consumed_at"])
        flow.consumed_at = now
        flow.save(update_fields=["consumed_at"])
        if method == "recovery_code":
            sessions.revoke_all_locked(user, "recovery_code")
            previous_hold = user.recovery_hold_state
            user.recovery_generation += 1
            user.recovery_hold_state = "review_required"
            user.hold_set_at = now
            user.hold_reason = "recovery_code"
            user.hold_factor = factor
            user.hold_factor_revision = factor.revision
            user.hold_cleared_event = None
            user.save(
                update_fields=[
                    "recovery_generation",
                    "recovery_hold_state",
                    "hold_set_at",
                    "hold_reason",
                    "hold_factor",
                    "hold_factor_revision",
                    "hold_cleared_event",
                ]
            )
            event(
                "auth.recovery_code_consumed",
                user=user,
                auth_epoch=user.auth_epoch,
                recovery_generation=user.recovery_generation,
                previous_hold_state=previous_hold,
                new_hold_state="review_required",
                actor=user,
                reason="recovery_code",
                factor_id_snapshot=factor.pk,
                factor_revision=factor.revision,
            )
        return sessions.issue_locked(
            request, user, flow.device_label, transport, portal, factor, method
        )


def safe_uuid(value):
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return None


def hold_denial(user, session, operation):
    event(
        "auth.recovery_hold_denied",
        "denied",
        user=user,
        actor=user,
        session=session,
        previous_hold_state=user.recovery_hold_state,
        new_hold_state=user.recovery_hold_state,
        auth_epoch=user.auth_epoch,
        recovery_generation=user.recovery_generation,
        reason=operation,
        factor_id_snapshot=user.hold_factor_id,
        factor_revision=user.hold_factor_revision,
    )
    return problem("RECOVERY_RESTRICTED", 403)


def scope(user, session, operation, context, command):
    if session.user_id != user.pk:
        return sessions.invalid()
    if operation not in OPERATIONS or context != {
        "kind": "personal",
        "id": str(user.pk),
    }:
        return problem("STEP_UP_REQUIRED", 403)
    expected = (
        {}
        if operation != "sessions.revoke"
        else {"session_id": command.get("session_id")}
    )
    if command != expected:
        return problem("VALIDATION_ERROR")
    if (
        operation == "sessions.revoke"
        and not AuthSession.objects.filter(
            pk=safe_uuid(command.get("session_id")), user=user
        ).exists()
    ):
        return problem("NOT_FOUND", 404)
    factor = active(user)
    if operation == "recovery_hold.clear":
        if (
            user.recovery_hold_state != "restricted"
            or not factor
            or user.hold_factor_id != factor.pk
            or user.hold_factor_revision != factor.revision
            or not factor.confirmed_at
            or factor.confirmed_at >= user.hold_set_at
        ):
            return hold_denial(user, session, operation)
    elif operation.startswith("mfa."):
        if user.recovery_hold_state != "clear":
            return hold_denial(user, session, operation)
        if operation != "mfa.enroll" and not factor:
            return problem("MFA_REQUIRED", 403)
    return None


@sensitive_variables()
def command_digest(user, session, operation, command):
    return keyed(
        "command",
        json.dumps(
            [str(user.pk), str(session.pk), operation, command],
            sort_keys=True,
            separators=(",", ":"),
        ),
    )


@sensitive_variables()
def intent_request(user, session, data):
    operation, context, command = data["operation"], data["context"], data["command"]
    if not isinstance(command, dict) or not isinstance(context, dict):
        return problem("VALIDATION_ERROR")
    denial = scope(user, session, operation, context, command)
    if denial:
        return denial
    target = (
        safe_uuid(command.get("session_id")) if operation == "sessions.revoke" else None
    )
    if target:
        command = {"session_id": str(target)}
    if "object_id" in data and (target is None or safe_uuid(data["object_id"]) is None):
        return problem("VALIDATION_ERROR")
    if (
        data.get("object_id") is not None
        and safe_uuid(data["object_id"]) != target
        or "version" in data
    ):
        return problem("VALIDATION_ERROR")
    now = timezone.now()
    row = AssuranceIntent.objects.create(
        user=user,
        session=session,
        auth_epoch=user.auth_epoch,
        recovery_generation=user.recovery_generation,
        operation=operation,
        context_kind="personal",
        context_id=user.pk,
        object_id=target,
        request_digest=command_digest(user, session, operation, command),
        created_at=now,
        expires_at=min(now + timedelta(minutes=5), sessions.idle_deadline(session)),
    )
    event(
        "auth.intent_issued", user=user, session=session, reason="intent:" + str(row.pk)
    )
    return {
        "intent_id": str(row.pk),
        "expires_at": row.expires_at.isoformat(),
        "required_methods": ["password", "totp"] if active(user) else ["password"],
    }


def intent_live(user, session, row):
    now = timezone.now()
    return bool(
        row
        and row.user_id == user.pk
        and row.session_id == session.pk
        and row.auth_epoch == user.auth_epoch
        and row.recovery_generation == user.recovery_generation
        and not row.consumed_at
        and not row.invalidated_at
        and row.created_at <= now < row.expires_at
        and row.context_kind == "personal"
        and row.context_id == user.pk
    )


def intent_command(row):
    return (
        {"session_id": str(row.object_id)} if row.operation == "sessions.revoke" else {}
    )


@sensitive_variables()
def step_up(user, session, data):
    row = (
        AssuranceIntent.objects.select_for_update()
        .filter(pk=safe_uuid(data["intent_id"]), user=user, session=session)
        .first()
    )
    if not intent_live(user, session, row) or row.proof_digest:
        return problem()
    command = intent_command(row)
    denial = scope(
        user,
        session,
        row.operation,
        {"kind": row.context_kind, "id": str(row.context_id)},
        command,
    )
    if denial:
        return denial
    if not constant_time_compare(
        row.request_digest, command_digest(user, session, row.operation, command)
    ):
        return problem()
    if not attempt(row.pk, row.created_at) or not check_password(
        data["password"], user.password
    ):
        return problem()
    factor = active(user)
    if factor:
        if data.get("totp_code"):
            if not verify_totp(factor, data["totp_code"]):
                return problem()
            observe(session, factor)
        elif not recent(session, factor):
            return problem("MFA_REQUIRED", 403)
    elif row.operation == "recovery_hold.clear":
        return problem("RECOVERY_RESTRICTED", 403)
    now = timezone.now()
    if now >= min(row.expires_at, sessions.idle_deadline(session)):
        return problem()
    session.last_interactive_at = max(session.last_interactive_at, now)
    session.save(update_fields=["last_interactive_at"])
    secret = new_secret()
    if factor:
        row.expires_at = min(row.expires_at, session.last_mfa_at + timedelta(minutes=5))
    row.methods = "password_totp" if factor else "password"
    row.factor_revision = factor.revision if factor else None
    row.proof_digest = proof_digest(user, session, row, secret)
    row.save(update_fields=["methods", "factor_revision", "proof_digest", "expires_at"])
    event(
        "auth.step_up_completed",
        user=user,
        session=session,
        reason="intent:" + str(row.pk),
    )
    return {
        "assurance_proof": row.pk.hex + "." + secret,
        "expires_at": row.expires_at.isoformat(),
    }


@sensitive_variables()
def proof_digest(user, session, row, secret):
    return keyed(
        "intent",
        json.dumps(
            [
                str(row.pk),
                str(user.pk),
                str(session.pk),
                row.operation,
                row.context_kind,
                str(row.context_id),
                str(row.object_id),
                row.object_version,
                row.request_digest,
                row.auth_epoch,
                row.recovery_generation,
                row.methods,
                row.factor_revision,
                row.expires_at.isoformat(),
                secret,
            ],
            separators=(",", ":"),
        ),
    )


@sensitive_variables()
def consume(user, session, operation, command, proof):
    parsed = sessions.parse_token(proof)
    if not parsed:
        return problem("STEP_UP_REQUIRED", 403)
    row = (
        AssuranceIntent.objects.select_for_update()
        .filter(pk=parsed[0], user=user, session=session)
        .first()
    )
    factor = active(user)
    denial = scope(
        user, session, operation, {"kind": "personal", "id": str(user.pk)}, command
    )
    if denial:
        return denial
    # Authenticate the exact owner/scope/proof before reporting owned replay.
    if (
        not row
        or row.operation != operation
        or not row.proof_digest
        or not constant_time_compare(
            row.request_digest, command_digest(user, session, operation, command)
        )
        or not constant_time_compare(
            row.proof_digest, proof_digest(user, session, row, parsed[1])
        )
    ):
        return problem("STEP_UP_REQUIRED", 403)
    if row.consumed_at:
        return problem("STATE_CONFLICT", 409)
    if (
        not intent_live(user, session, row)
        or (
            factor
            and (
                row.methods != "password_totp"
                or row.factor_revision != factor.revision
                or not recent(session, factor)
            )
        )
        or (not factor and row.methods != "password")
    ):
        return problem("STEP_UP_REQUIRED", 403)
    row.consumed_at = timezone.now()
    row.save(update_fields=["consumed_at"])
    event(
        "auth.intent_consumed",
        user=user,
        session=session,
        reason="intent:" + str(row.pk),
    )
    return None


@sensitive_variables()
def enrollment_request(user, session, proof):
    denial = consume(user, session, "mfa.enroll", {}, proof)
    if denial:
        return denial
    now = timezone.now()
    MfaFactor.objects.filter(user=user, state="pending").update(
        state="revoked", revoked_at=now
    )
    revision = max([f.revision for f in MfaFactor.objects.filter(user=user)] + [0]) + 1
    factor = MfaFactor(
        user=user,
        state="pending",
        enrollment_session=session,
        auth_epoch=user.auth_epoch,
        recovery_generation=user.recovery_generation,
        revision=revision,
        created_at=now,
        expires_at=min(now + timedelta(minutes=5), sessions.idle_deadline(session)),
        key_id=settings.PWC_AUTH_MFA_ACTIVE_KEY,
    )
    secret = pyotp.random_base32()
    factor.encrypted_secret = cipher(factor.key_id).encrypt(
        json.dumps(
            {
                "purpose": "totp-v1",
                "user": str(user.pk),
                "factor": str(factor.pk),
                "secret": secret,
            }
        ).encode()
    )
    factor.save()
    event("auth.mfa_enrollment_requested", user=user, session=session)
    return {
        "enrollment_id": str(factor.pk),
        "secret": secret,
        "otpauth_uri": pyotp.TOTP(secret).provisioning_uri(
            name=str(user.pk), issuer_name="PWC"
        ),
        "expires_at": factor.expires_at.isoformat(),
    }


@sensitive_variables()
def enrollment_confirm(user, session, data):
    if session.user_id != user.pk:
        return sessions.invalid()
    factor = MfaFactor.objects.filter(
        pk=safe_uuid(data["enrollment_id"]),
        user=user,
        state="pending",
        enrollment_session=session,
    ).first()
    now = timezone.now()
    if (
        not factor
        or user.recovery_hold_state != "clear"
        or factor.auth_epoch != user.auth_epoch
        or factor.recovery_generation != user.recovery_generation
        or factor.expires_at <= now
        or factor.created_at > now
    ):
        return problem()
    if not verify_totp(factor, data["code"]):
        return problem()
    if timezone.now() >= min(factor.expires_at, sessions.idle_deadline(session)):
        return problem()
    previous = active(user)
    if previous:
        previous.state, previous.revoked_at = "revoked", now
        previous.save(update_fields=["state", "revoked_at"])
    factor.state, factor.confirmed_at = "active", now
    factor.save(update_fields=["state", "confirmed_at"])
    sessions.revoke_all_locked(
        user, "factor_replaced" if previous else "factor_enrolled"
    )
    if not previous:
        session.revoked_at, session.revocation_reason = None, ""
        session.auth_epoch = user.auth_epoch
        session.save(update_fields=["revoked_at", "revocation_reason", "auth_epoch"])
        observe(session, factor)
    result = codes(user, factor)
    event(
        "auth.mfa_activated",
        user=user,
        session=session,
        factor_revision=factor.revision,
        factor_id_snapshot=factor.pk,
    )
    return {"status": "active", "recovery_codes": result}


@sensitive_variables()
def remove(user, session, proof):
    denial = consume(user, session, "mfa.remove", {}, proof)
    if denial:
        return denial
    factor = active(user)
    factor.state, factor.revoked_at = "revoked", timezone.now()
    factor.save(update_fields=["state", "revoked_at"])
    MfaFactor.objects.filter(user=user, state="pending").update(
        state="revoked", revoked_at=timezone.now()
    )
    MfaRecoveryCode.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=timezone.now()
    )
    sessions.revoke_all_locked(user, "factor_removed")
    event("auth.mfa_removed", user=user, session=session)
    return None


@sensitive_variables()
def clear_hold(user, session, data):
    row = AssuranceIntent.objects.filter(
        pk=safe_uuid(data["intent_id"]),
        user=user,
        session=session,
        operation="recovery_hold.clear",
    ).first()
    if not row:
        return problem("RECOVERY_RESTRICTED", 403)
    result = step_up(user, session, data)
    if isinstance(result, FlowProblem):
        return result
    denial = consume(
        user, session, "recovery_hold.clear", {}, result["assurance_proof"]
    )
    if denial:
        return denial
    previous = user.recovery_hold_state
    row.refresh_from_db()
    user.recovery_generation += 1
    AssuranceIntent.objects.filter(
        user=user, consumed_at__isnull=True, invalidated_at__isnull=True
    ).update(invalidated_at=timezone.now())
    clearance = SecurityEvent.objects.create(
        event="auth.recovery_hold_cleared",
        result="success",
        subject=user,
        actor=user,
        session=session,
        reason="intent:" + str(row.pk),
        previous_hold_state=previous,
        new_hold_state="clear",
        factor_revision=row.factor_revision,
        factor_id_snapshot=user.hold_factor_id,
        auth_epoch=user.auth_epoch,
        recovery_generation=user.recovery_generation,
    )
    user.recovery_hold_state = "clear"
    user.hold_set_at = None
    user.hold_reason = ""
    user.hold_cleared_event = clearance
    user.save(
        update_fields=[
            "recovery_hold_state",
            "hold_set_at",
            "hold_reason",
            "hold_cleared_event",
            "recovery_generation",
        ]
    )
    return None
