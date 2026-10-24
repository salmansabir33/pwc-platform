"""Synthetic read boundary. Never return lazy querysets or reusable authority tokens."""
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from types import SimpleNamespace

from django.core import signing
from django.db import DatabaseError, transaction
from rest_framework.exceptions import APIException

from accounts import sessions
from accounts.session_authentication import PersonalAuthentication
from accounts.flow_security import FlowProblem
from organizations.models import OrganizationWorkspace
from .context import resolve_context
from .http_contract import validate_input
from .models import AuthorizationEvent, NGOKernelState, NGOGrant, SyntheticPrincipal
from .registry import ACTIONS, BUNDLES, ENTER, READ, SETTINGS, REGISTRY_VERSION
from .security import KernelProblem, db_clock, require_synthetic_environment, transaction_limits

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    code: str
    status: int
    correlation_id: uuid.UUID
    context_id: uuid.UUID | None = None
    context_revision: int | None = None
    actions: tuple[str, ...] = ()
    # Only fixed synthetic scalar fields, never model instances or arbitrary payloads.
    projection: tuple[tuple[str, str], ...] = ()
    registry_version: str = REGISTRY_VERSION
    earliest_grant_expires_at: datetime | None = None


def _state_queryset(organization_id):
    """Always scope before object lookup/count; internal to the locked boundary."""
    return NGOKernelState.objects.filter(organization_id=organization_id)


def _eligible_actions(grants, now):
    actions = set()
    eligible = []
    for grant in grants:
        bundle = BUNDLES.get((grant.role_code, grant.role_version))
        if (bundle and grant.scope_kind == "organization"
                and grant.source_kind == "synthetic_fixture"
                and grant.issuer_process == "kernel_fixture_v1"
                and grant.source_ref and grant.approval_evidence_ref
                and grant.verification_status == "synthetic_verified"
                and grant.revoked_at is None
                and grant.effective_at <= now < grant.expires_at):
            actions.update(bundle)
            eligible.append(grant)
    return actions, eligible


def _audit(**values):
    return AuthorizationEvent.objects.create(**values)


@dataclass(frozen=True)
class ContextProjection:
    organization_id: uuid.UUID
    context_revision: int


@dataclass(frozen=True)
class DiscoveryDecision:
    allowed: bool
    code: str
    status: int
    correlation_id: uuid.UUID
    contexts: tuple[ContextProjection, ...]
    next_cursor: str | None


@dataclass
class _Evidence:
    correlation: uuid.UUID
    actor_id: uuid.UUID | None = None
    session_id: uuid.UUID | None = None


def _boundary(function):
    """The actual commit precedes every allowed service result; failures redact data."""
    @wraps(function)
    def wrapped(request, *args, **kwargs):
        evidence = _Evidence(uuid.uuid4())
        try:
            with transaction.atomic(durable=True):
                transaction_limits()
                require_synthetic_environment()
                decision = function(request, *args, _evidence=evidence, **kwargs)
            return decision
        except KernelProblem as exc:
            problem = exc
        except APIException as exc:
            if exc.status_code == 401:
                code = "authentication_required"
            elif exc.status_code >= 500:
                code = "authorization_unavailable"
            else:
                # Retain auth-owned transport/CSRF error semantics, not a domain allow.
                code = str(exc.detail["error"]["code"])
            problem = KernelProblem(code, exc.status_code)
        except FlowProblem as exc:
            problem = KernelProblem("authentication_required" if exc.status == 401 else "authorization_unavailable", exc.status)
        except DatabaseError:
            logger.warning("Kernel dependency unavailable; correlation=%s", evidence.correlation)
            return AuthorizationDecision(False, "authorization_unavailable", 503, evidence.correlation)
        # No context/target existence or secret-bearing action strings in denial events.
        try:
            with transaction.atomic(durable=True):
                transaction_limits()
                _audit(actor_id=evidence.actor_id, session_id=evidence.session_id,
                       action="context_request", result="deny", reason_code=problem.code,
                       correlation_id=evidence.correlation)
        except (DatabaseError, KernelProblem):
            logger.warning("Kernel dependency unavailable; correlation=%s", evidence.correlation)
            return AuthorizationDecision(False, "authorization_unavailable", 503, evidence.correlation)
        return AuthorizationDecision(False, problem.code, problem.status, evidence.correlation)
    return wrapped


def _authenticate(request, evidence):
    raw = getattr(request, "_request", request)
    result = PersonalAuthentication().authenticate(SimpleNamespace(_request=raw))
    if not result:
        raise KernelProblem("authentication_required", 401)
    user, session = result
    evidence.actor_id, evidence.session_id = user.pk, session.pk
    snapshot = sessions.locate(raw)
    deadline = sessions.authorization_deadline(session, snapshot) if snapshot else None
    return raw, user, session, deadline


def _locked_state(organization_id):
    rows = list(NGOKernelState.objects.raw(
        "SELECT * FROM public.pwc_kernel_lock(%s)", [organization_id]))
    return rows[0] if rows else None


def _principal(user):
    return SyntheticPrincipal.objects.filter(user=user).first()


def _eligible_state(state, principal):
    return bool(state and state.mode == "synthetic" and principal
                and principal.fixture_batch == state.fixture_batch
                and OrganizationWorkspace.objects.filter(
                    organization_id=state.organization_id, state="verified").exists())


def _tenant_grants(state, user):
    return list(NGOGrant.objects.filter(
        organization_id=state.organization_id, subject=user,
        fixture_batch=state.fixture_batch, revoked_at__isnull=True,
    ).order_by("id"))


def _allow_audit(state, user, session, grant, action, correlation):
    _audit(organization_id=state.organization_id, actor=user, session=session,
           action=action, result="allow", reason_code="authorized",
           target_id=state.organization_id, fixture_batch=state.fixture_batch,
           grant=grant, role_version=grant.role_version,
           new_grant_revision=grant.revision, new_context_revision=state.revision,
           correlation_id=correlation)


@_boundary
def evaluate(request, *, kind, identifier, action, object_organization_id=None,
             http_contract=False, _evidence):
    """Reauthenticate and materialize an exact synthetic projection under shared locks.

    Actions are server-owned constants. No arbitrary-model queryset/callback interface.
    Personal operation dispatch remains in accounts. HTTP parsing is fixed, not policy.
    """
    raw, user, session, deadline = _authenticate(request, _evidence)
    if http_contract:
        validate_input(raw, discovery=False)
    try:
        context = resolve_context(kind, identifier, personal_user_id=user.pk)
    except (TypeError, ValueError, AttributeError):
        raise KernelProblem("invalid_context" if kind in ("personal", "ngo") else "not_found", 400 if kind in ("personal", "ngo") else 404) from None
    if user.recovery_hold_state != "clear":
        raise KernelProblem("recovery_hold", 403)
    if context.kind != "ngo":
        raise KernelProblem("permission_denied", 403)
    state, principal = _locked_state(context.subject_uuid), _principal(user)
    if not _eligible_state(state, principal):
        raise KernelProblem("not_found", 404)
    grants = _tenant_grants(state, user)
    actions, eligible = _eligible_actions(grants, db_clock())
    if ENTER not in actions:
        raise KernelProblem("not_found", 404)
    if not isinstance(action, str) or action not in ACTIONS or action not in actions:
        raise KernelProblem("permission_denied", 403)
    if object_organization_id is not None:
        try:
            object_id = uuid.UUID(str(object_organization_id))
        except (TypeError, ValueError, AttributeError):
            raise KernelProblem("not_found", 404) from None
        if not _state_queryset(context.subject_uuid).filter(organization_id=object_id).exists():
            raise KernelProblem("not_found", 404)
    projection = (("organization_id", str(context.subject_uuid)),
                  ("probe_code", "kernel_settings_v1" if action == SETTINGS else "private_probe_v1"),
                  ("label", "Synthetic kernel settings" if action == SETTINGS else "Synthetic private probe"),
                  ("context_revision", str(state.revision)))
    if action == ENTER:
        projection = (("organization_id", str(context.subject_uuid)),
                      ("context_revision", str(state.revision)))
    supporting = max((g for g in eligible if action in BUNDLES[(g.role_code, g.role_version)]),
                     key=lambda g: g.expires_at)
    _allow_audit(state, user, session, supporting, action, _evidence.correlation)
    now = db_clock()
    final_actions, final_grants = _eligible_actions(grants, now)
    if deadline is None or now >= deadline:
        raise KernelProblem("authentication_required", 401)
    if ENTER not in final_actions or action not in final_actions or now >= supporting.expires_at:
        raise KernelProblem("not_found", 404)
    return AuthorizationDecision(True, "authorized", 200, _evidence.correlation,
                                 context.subject_uuid, state.revision,
                                 tuple(sorted(final_actions)), projection,
                                 earliest_grant_expires_at=min(g.expires_at for g in final_grants))


CURSOR_SALT = "pwc.synthetic-contexts.scan.v1"
PAGE_SIZE = 50


def _cursor(after, user, session):
    return signing.dumps({"v": 1, "after": str(after), "user": str(user.pk),
                          "session": str(session.pk)}, salt=CURSOR_SALT)


def _decode_cursor(value, user, session):
    if value is None:
        return None
    try:
        if not isinstance(value, str) or not value or len(value) > 512:
            raise ValueError()
        data = signing.loads(value, salt=CURSOR_SALT, max_age=3600)
        if (set(data) != {"v", "after", "user", "session"} or data["v"] != 1
                or data["user"] != str(user.pk) or data["session"] != str(session.pk)):
            raise ValueError()
        return uuid.UUID(data["after"])
    except (signing.BadSignature, TypeError, ValueError, KeyError, AttributeError):
        raise KernelProblem("invalid_context", 400) from None


@_boundary
def discover(request, *, _evidence):
    """Scan <=50 own candidate tenants; lock in UUID order and recheck every page.

    Cursors are signed display pagination, never authority or a stable snapshot.
    Empty pages may occur if candidates lose eligibility before roots are locked.
    """
    raw, user, session, deadline = _authenticate(request, _evidence)
    cursor = validate_input(raw, discovery=True)
    if user.recovery_hold_state != "clear":
        raise KernelProblem("recovery_hold", 403)
    after = _decode_cursor(cursor, user, session)
    principal = _principal(user)
    now = db_clock()
    candidates = NGOGrant.objects.none()
    if principal:
        candidates = NGOGrant.objects.filter(
            subject=user, fixture_batch=principal.fixture_batch, revoked_at__isnull=True,
            effective_at__lte=now, expires_at__gt=now, verification_status="synthetic_verified",
            scope_kind="organization", source_kind="synthetic_fixture", issuer_process="kernel_fixture_v1",
            role_code__in=[code for code, version in BUNDLES], role_version=1,
            organization__ngokernelstate__mode="synthetic",
            organization__ngokernelstate__fixture_batch=principal.fixture_batch,
            organization__workspace__state="verified",
        )
    if after:
        candidates = candidates.filter(organization_id__gt=after)
    ids = list(candidates.order_by("organization_id").values_list("organization_id", flat=True).distinct()[:PAGE_SIZE + 1])
    scanned = ids[:PAGE_SIZE]
    # Acquire the entire sorted root set before evaluating any page projections.
    states = [_locked_state(identifier) for identifier in scanned]
    contexts, checked = [], []
    for state in states:
        if not _eligible_state(state, principal):
            continue
        grants = _tenant_grants(state, user)
        actions, eligible = _eligible_actions(grants, db_clock())
        if ENTER not in actions:
            continue
        supporting = max((g for g in eligible if ENTER in BUNDLES[(g.role_code, g.role_version)]),
                         key=lambda g: g.expires_at)
        _allow_audit(state, user, session, supporting, ENTER, _evidence.correlation)
        contexts.append(ContextProjection(state.organization_id, state.revision))
        checked.append(supporting)
    if not contexts:
        # No domain allow occurred. Existing immutable schema permits a null-context
        # denial of authority, not a fabricated allow without a grant/root.
        _audit(actor=user, session=session, action="discovery", result="deny",
               reason_code="no_eligible_contexts", correlation_id=_evidence.correlation)
    final_now = db_clock()
    if deadline is None or final_now >= deadline:
        raise KernelProblem("authentication_required", 401)
    if any(final_now >= grant.expires_at for grant in checked):
        # Roll back the entire page's allow evidence, and release no stale entry.
        raise KernelProblem("state_conflict", 409)
    next_cursor = _cursor(scanned[-1], user, session) if len(ids) > PAGE_SIZE else None
    return DiscoveryDecision(True, "authorized", 200, _evidence.correlation,
                             tuple(contexts), next_cursor)
