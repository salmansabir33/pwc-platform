"""Personal session services. All authority transitions linearize on User.

Only established Django crypto/hash/session primitives. No JWT, local mutex or
OTP implementation. Failure outcomes return normally so revocation commits.
"""

import re
import uuid
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth import login as django_login
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.debug import sensitive_variables

from .backends import password_candidate
from .email_identity import normalize_email
from .flow_security import FlowProblem, abuse_digest, new_secret
from .models import (
    User,
    UserContact,
    MfaFactor,
    AuthSession,
    MobileCredential,
    AuthAbuseBucket,
    AuthChallenge,
    AssuranceIntent,
)
from .registration import event, flow_uuid, spend, cancel_deliveries

DURATIONS = {
    "mobile": (timedelta(days=7), timedelta(days=30)),
    "ngo_web": (timedelta(minutes=30), timedelta(hours=12)),
    "pwc_ops": (timedelta(minutes=15), timedelta(hours=8)),
}
TOKEN = re.compile(r"([0-9a-f]{32})\.([A-Za-z0-9_-]{43})\Z")
BACKEND = "accounts.backends.VerifiedEmailBackend"


def invalid():
    return FlowProblem("SESSION_INVALID", 401)


def configured():
    if (
        not settings.PWC_AUTH_SESSIONS_ENABLED
        or not isinstance(settings.PWC_AUTH_SESSION_KEY, str)
        or len(settings.PWC_AUTH_SESSION_KEY) < 43
        or not isinstance(settings.PWC_AUTH_ABUSE_KEY, str)
        or len(settings.PWC_AUTH_ABUSE_KEY) < 32
    ):
        raise FlowProblem("AUTH_UNAVAILABLE", 503)
    # No implicit proxy trust/deployment topology in this slice.
    if (
        settings.USE_X_FORWARDED_HOST
        or settings.USE_X_FORWARDED_PORT
        or settings.SECURE_PROXY_SSL_HEADER is not None
    ):
        raise FlowProblem("AUTH_UNAVAILABLE", 503)


def portal(request):
    configured()
    mapping = settings.PWC_AUTH_PORTALS
    if (
        not isinstance(mapping, dict)
        or not mapping
        or settings.SESSION_ENGINE != "django.contrib.sessions.backends.db"
        or not settings.SESSION_COOKIE_NAME.startswith("__Host-")
        or not settings.SESSION_COOKIE_SECURE
        or not settings.SESSION_COOKIE_HTTPONLY
        or settings.SESSION_COOKIE_DOMAIN is not None
        or settings.SESSION_COOKIE_PATH != "/"
        or settings.SESSION_COOKIE_SAMESITE not in ("Lax", "Strict")
        or not settings.CSRF_COOKIE_SECURE
    ):
        raise FlowProblem("AUTH_UNAVAILABLE", 503)
    if any(
        not isinstance(name, str) or name not in ("ngo_web", "pwc_ops")
        for name in mapping.values()
    ) or len(set(mapping.values())) != len(mapping):
        raise FlowProblem("AUTH_UNAVAILABLE", 503)
    for origin, name in mapping.items():
        if not isinstance(origin, str):
            raise FlowProblem("AUTH_UNAVAILABLE", 503)
        try:
            parsed = urlsplit(origin)
            parsed.port
            URLValidator(schemes=["https"])(origin)
        except (TypeError, ValueError, ValidationError):
            raise FlowProblem("AUTH_UNAVAILABLE", 503) from None
        if (
            not isinstance(origin, str)
            or parsed.scheme != "https"
            or not parsed.hostname
            or any(ord(c) <= 32 or ord(c) >= 127 for c in origin)
            or "\\" in origin
            or "*" in origin
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
            or name not in ("ngo_web", "pwc_ops")
        ):
            raise FlowProblem("AUTH_UNAVAILABLE", 503)
    origin = f"{request.scheme}://{request.get_host()}"
    if not request.is_secure() or origin not in mapping:
        raise FlowProblem("TRANSPORT_NOT_ALLOWED")
    return mapping[origin], origin


@sensitive_variables()
def keyed(purpose, value):
    return salted_hmac(
        "pwc.sessions." + purpose + ".v1",
        value,
        secret=settings.PWC_AUTH_SESSION_KEY,
        algorithm="sha256",
    ).hexdigest()


@sensitive_variables()
def web_digest(key):
    return keyed("web", key)


@sensitive_variables()
def credential_digest(kind, selector, secret, user, session):
    return keyed(kind, f"{session.pk}:{user.pk}:{selector}:{secret}:{user.password}")


@sensitive_variables()
def parse_token(token):
    if not isinstance(token, str) or len(token) != 76:
        return None
    match = TOKEN.fullmatch(token)
    return (uuid.UUID(hex=match[1]), match[2]) if match else None


def idle_deadline(session):
    return min(
        session.absolute_expires_at,
        session.last_interactive_at + DURATIONS[session.portal][0],
    )


def live(user, contact, session, now):
    return bool(
        user.is_active
        and contact
        and contact.user_id == user.pk
        and contact.kind == "email"
        and contact.is_primary
        and contact.verified_at
        and not contact.retired_at
        and session.user_id == user.pk
        and not session.revoked_at
        and session.auth_epoch == user.auth_epoch
        and session.portal in DURATIONS
        and session.created_at <= now
        and now < idle_deadline(session)
        and not MfaFactor.objects.filter(user=user, state="active").exists()
    )


def current_contact(user, lock=False):
    query = UserContact.objects.select_for_update() if lock else UserContact.objects
    return query.filter(
        user=user,
        kind="email",
        is_primary=True,
        verified_at__isnull=False,
        retired_at__isnull=True,
    ).first()


def envelope(user, session):
    return {
        "user": {"id": str(user.pk), "preferred_language": user.preferred_language},
        "session": {
            "id": str(session.pk),
            "absolute_expires_at": session.absolute_expires_at.isoformat(),
            "idle_expires_at": idle_deadline(session).isoformat(),
            "assurance": {"method": "password", "last_mfa_at": None},
        },
        "recovery_hold_state": user.recovery_hold_state,
    }


@sensitive_variables()
def issue_pair(user, session, now):
    result = {}
    for kind, seconds in (("access", 300), ("refresh", None)):
        selector, secret = uuid.uuid4(), new_secret()
        expires = (
            min(now + timedelta(seconds=seconds), session.absolute_expires_at)
            if seconds
            else session.absolute_expires_at
        )
        MobileCredential.objects.create(
            id=selector,
            session=session,
            kind=kind,
            secret_digest=credential_digest(kind, selector, secret, user, session),
            generation=session.credential_generation,
            issued_at=now,
            expires_at=expires,
        )
        result["access_token" if kind == "access" else "refresh_token"] = (
            f"{selector.hex}.{secret}"
        )
        if kind == "access":
            result["expires_in"] = int((expires - now).total_seconds())
        else:
            result["refresh_expires_at"] = expires.isoformat()
    result["token_type"] = "Bearer"
    return result


@sensitive_variables()
def login(request, email, password, device_label, transport, portal_name):
    configured()
    try:
        target = normalize_email(email)
    except ValidationError:
        target = "invalid-email"
    problem = spend(request.META.get("REMOTE_ADDR", "unknown"), "login")
    if problem:
        return problem
    # Serialize the bounded password check against a shared failure bucket.
    # Release that lock BEFORE acquiring User/domain locks; successes do not
    # spend or reset the target failure budget.
    now = timezone.now()
    start = now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)
    with transaction.atomic():
        bucket, _ = AuthAbuseBucket.objects.select_for_update().get_or_create(
            dimension="target",
            key_digest=abuse_digest(target),
            route="login:900",
            window_start=start,
            defaults={"expires_at": start + timedelta(minutes=15)},
        )
        if bucket.count >= 5:
            return FlowProblem(
                "RATE_LIMITED",
                429,
                retry_after=max(
                    1, int((start + timedelta(minutes=15) - now).total_seconds()) + 1
                ),
            )
        candidate = password_candidate(email, password)
        if not candidate:
            bucket.count += 1
            bucket.save(update_fields=["count"])
            event("auth.login_denied", "denied")
            if bucket.count == 5:
                event("auth.login_target_limited", "denied")
            return FlowProblem("INVALID_CREDENTIALS", 401)
    snapshot, contact_snapshot, canonical = candidate
    with transaction.atomic():
        user = User.objects.select_for_update().filter(pk=snapshot.pk).first()
        if user is None:
            return FlowProblem("INVALID_CREDENTIALS", 401)
        contact = (
            UserContact.objects.select_for_update()
            .filter(pk=contact_snapshot.pk)
            .first()
        )
        factor = (
            MfaFactor.objects.select_for_update()
            .filter(user=user, state="active")
            .first()
        )
        if not (
            user.is_active
            and user.password == snapshot.password
            and user.auth_epoch == snapshot.auth_epoch
            and contact
            and contact.user_id == user.pk
            and contact.normalized_value == canonical
            and contact.verified_at
            and not contact.retired_at
            and contact.is_primary
        ):
            return FlowProblem("INVALID_CREDENTIALS", 401)
        if factor:
            return FlowProblem("MFA_REQUIRED", 403)
        now = timezone.now()
        duration = DURATIONS[portal_name][1]
        if transport == "web":
            # Django rotates key and CSRF, preserving neither an attacker-chosen
            # session key nor an unrelated authenticated principal.
            previous_key = request.session.session_key
            if previous_key:
                previous = (
                    AuthSession.objects.select_for_update()
                    .filter(
                        user=user,
                        transport="web",
                        web_key_digest=web_digest(previous_key),
                        revoked_at__isnull=True,
                    )
                    .first()
                )
                if previous:
                    previous.revoked_at, previous.revocation_reason = (
                        now,
                        "reauthentication",
                    )
                    previous.save(update_fields=["revoked_at", "revocation_reason"])
            django_login(request, user, backend=BACKEND)
            request.session.cycle_key()  # rotate even same-user reauthentication
            request.session.set_expiry(now + duration)
            request.session.save()
            key_digest = web_digest(request.session.session_key)
        else:
            key_digest = None
        session = AuthSession.objects.create(
            user=user,
            transport=transport,
            portal=portal_name,
            auth_epoch=user.auth_epoch,
            web_key_digest=key_digest,
            device_label=device_label,
            created_at=now,
            last_interactive_at=now,
            absolute_expires_at=now + duration,
        )
        if transport == "web":
            request.session["pwc_session_id"] = str(session.pk)
            request.session.save()
        result = envelope(user, session)
        if transport == "mobile":
            result.update(issue_pair(user, session, now))
        event(
            "auth.login_completed",
            user=user,
            session=session,
            auth_epoch=user.auth_epoch,
        )
    return result


@sensitive_variables()
def locate(request):
    """Untrusted selector only. Caller must lock/re-read all authority."""
    if settings.SESSION_COOKIE_NAME in request.COOKIES:
        name, _ = portal(request)
        key = request.session.session_key
        if not key:
            return None
        session = AuthSession.objects.filter(
            web_key_digest=web_digest(key), transport="web", portal=name
        ).first()
        return (session, None, None) if session else None
    header = request.META.get("HTTP_AUTHORIZATION", "")
    if not header.startswith("Bearer "):
        return None
    parsed = parse_token(header[7:])
    if not parsed:
        return None
    credential = (
        MobileCredential.objects.select_related("session")
        .filter(pk=parsed[0], kind="access")
        .first()
    )
    return (credential.session, credential.pk, parsed[1]) if credential else None


@sensitive_variables()
def authenticate_locked(request, snapshot):
    """User -> contact -> session -> credential; stays in caller transaction."""
    session_snapshot, credential_id, secret = snapshot
    user = User.objects.select_for_update().filter(pk=session_snapshot.user_id).first()
    if not user:
        return None
    contact = current_contact(user, lock=True)
    session = (
        AuthSession.objects.select_for_update().filter(pk=session_snapshot.pk).first()
    )
    now = timezone.now()
    if not session or not live(user, contact, session, now):
        return None
    if credential_id:
        credential = (
            MobileCredential.objects.select_for_update()
            .filter(pk=credential_id, session=session, kind="access")
            .first()
        )
        if not (
            session.transport == "mobile"
            and session.portal == "mobile"
            and credential
            and credential.generation == session.credential_generation
            and credential.expires_at > now
            and not credential.replaced_at
            and not credential.consumed_at
            and constant_time_compare(
                credential.secret_digest,
                credential_digest("access", credential.pk, secret, user, session),
            )
        ):
            return None
    else:
        if not (
            session.transport == "web"
            and session.web_key_digest == web_digest(request.session.session_key or "")
            and request.session.get("pwc_session_id") == str(session.pk)
            and request.session.get("_auth_user_id") == str(user.pk)
            and request.session.get("_auth_user_backend") == BACKEND
            and constant_time_compare(
                request.session.get("_auth_user_hash", ""), user.get_session_auth_hash()
            )
        ):
            return None
    return user, session


@sensitive_variables()
def refresh(token, ip):
    configured()
    problem = spend(ip, "refresh")
    if problem:
        return problem
    parsed = parse_token(token)
    if not parsed:
        return invalid()
    snapshot = (
        MobileCredential.objects.select_related("session")
        .filter(pk=parsed[0], kind="refresh")
        .first()
    )
    if not snapshot:
        return invalid()
    with transaction.atomic():
        user = (
            User.objects.select_for_update().filter(pk=snapshot.session.user_id).first()
        )
        if not user:
            return invalid()
        contact = current_contact(user, lock=True)
        session = (
            AuthSession.objects.select_for_update()
            .filter(pk=snapshot.session_id, user=user)
            .first()
        )
        credential = (
            MobileCredential.objects.select_for_update()
            .filter(pk=snapshot.pk, session=session, kind="refresh")
            .first()
        )
        if session is None or credential is None:
            return invalid()
        now = timezone.now()
        if not (
            session.transport == "mobile"
            and session.portal == "mobile"
            and live(user, contact, session, now)
            and constant_time_compare(
                credential.secret_digest,
                credential_digest("refresh", credential.pk, parsed[1], user, session),
            )
        ):
            return invalid()
        if credential.expires_at <= now:
            return invalid()
        if credential.consumed_at is not None:
            session.revoked_at, session.revocation_reason = now, "refresh_replay"
            session.save(update_fields=["revoked_at", "revocation_reason"])
            event("auth.refresh_replay", "denied", user=user, session=session)
            return invalid()
        if credential.generation != session.credential_generation:
            return invalid()
        start = now.replace(second=0, microsecond=0)
        bucket, _ = AuthAbuseBucket.objects.select_for_update().get_or_create(
            dimension="session",
            key_digest=abuse_digest(str(session.pk)),
            route="refresh:60",
            window_start=start,
            defaults={"expires_at": start + timedelta(minutes=1)},
        )
        bucket.count = min(bucket.count + 1, 31)
        bucket.save(update_fields=["count"])
        if bucket.count > 30:
            return FlowProblem("RATE_LIMITED", 429, retry_after=60)
        # A blocking budget/DB operation must not turn a previously live
        # session into issuance after its idle/absolute/credential deadline.
        now = timezone.now()
        if not live(user, contact, session, now) or credential.expires_at <= now:
            return invalid()
        credential.consumed_at = now
        credential.save(update_fields=["consumed_at"])
        MobileCredential.objects.filter(
            session=session, kind="access", replaced_at__isnull=True
        ).update(replaced_at=now)
        session.credential_generation += 1
        session.save(update_fields=["credential_generation"])
        result = envelope(user, session)
        result.update(issue_pair(user, session, now))
        event("auth.refresh_completed", user=user, session=session)
    return result


def revoke_all_locked(user, reason):
    """Internal lifecycle primitive: caller holds User lock and authorizes action.

    Not an assurance bypass API; public logout-all denies until 03A.4.
    """
    list(AuthSession.objects.select_for_update().filter(user=user).order_by("id"))
    now = timezone.now()
    user.auth_epoch += 1
    user.save(update_fields=["auth_epoch"])
    AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
        revoked_at=now, revocation_reason=reason
    )
    challenges = AuthChallenge.objects.filter(
        user=user, consumed_at__isnull=True, invalidated_at__isnull=True
    )
    ids = list(challenges.values_list("pk", flat=True))
    challenges.update(invalidated_at=now)
    cancel_deliveries(ids, now)
    AssuranceIntent.objects.filter(
        user=user, consumed_at__isnull=True, invalidated_at__isnull=True
    ).update(invalidated_at=now)
    event(
        "auth.all_sessions_revoked",
        user=user,
        reason=reason,
        auth_epoch=user.auth_epoch,
    )


def suspend_account(user_id):
    """Trusted internal suspension hook, not an operator/NGO authorization API."""
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user_id)
        user.is_active = False
        user.save(update_fields=["is_active"])
        # Helper locks registry rows before challenge rows, as reset/refresh do.
        revoke_all_locked(user, "suspension")
