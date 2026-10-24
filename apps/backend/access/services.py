"""Synthetic read boundary. Never return lazy querysets or reusable authority tokens."""
import uuid
import logging
from dataclasses import dataclass
from types import SimpleNamespace

from django.db import DatabaseError, transaction
from rest_framework.exceptions import APIException

from accounts import sessions
from accounts.session_authentication import PersonalAuthentication
from accounts.flow_security import FlowProblem
from organizations.models import OrganizationWorkspace
from .context import resolve_context
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


def evaluate(request, *, kind, identifier, action, object_organization_id=None):
    """Reauthenticate raw/DRF request inside the same transaction as scoped read/audit.

    Caller must choose a server-owned action, never copy client capabilities. Personal
    context resolution exists, but personal operation dispatch stays in accounts.
    This is not a generic callback or arbitrary-model query authorization API.
    """
    correlation = uuid.uuid4()
    actor_id = session_id = None
    try:
        # A successful result may leave this boundary only after the real commit.
        # Durable blocks reject nesting in another transaction with an uncertain commit.
        with transaction.atomic(durable=True):
            transaction_limits()
            require_synthetic_environment()
            # Adapter retains transport/CSRF/session behavior; outer atomic retains locks.
            raw = getattr(request, "_request", request)
            result = PersonalAuthentication().authenticate(SimpleNamespace(_request=raw))
            if not result:
                raise KernelProblem("authentication_required", 401)
            user, session = result
            actor_id, session_id = user.pk, session.pk
            snapshot = sessions.locate(raw)
            deadline = sessions.authorization_deadline(session, snapshot) if snapshot else None
            try:
                context = resolve_context(kind, identifier, personal_user_id=user.pk)
            except (TypeError, ValueError, AttributeError):
                raise KernelProblem("invalid_context" if kind in ("personal", "ngo") else "not_found", 400 if kind in ("personal", "ngo") else 404) from None
            if user.recovery_hold_state != "clear":
                raise KernelProblem("recovery_hold", 403)
            if context.kind != "ngo":
                # No personal-to-NGO dispatch; existing personal services remain owner.
                raise KernelProblem("permission_denied", 403)
            rows = list(NGOKernelState.objects.raw(
                "SELECT * FROM public.pwc_kernel_lock(%s)", [context.subject_uuid]))
            state = rows[0] if rows else None
            principal = SyntheticPrincipal.objects.filter(user=user).first()
            if not (state and state.mode == "synthetic" and principal
                    and principal.fixture_batch == state.fixture_batch
                    and OrganizationWorkspace.objects.filter(organization_id=context.subject_uuid, state="verified").exists()):
                raise KernelProblem("not_found", 404)
            grants = list(NGOGrant.objects.filter(
                organization_id=context.subject_uuid, subject=user,
                fixture_batch=state.fixture_batch, revoked_at__isnull=True,
            ).order_by("id"))
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
                # Direct object lookup remains tenant filtered; never query the foreign ID.
                if not _state_queryset(context.subject_uuid).filter(organization_id=object_id).exists():
                    raise KernelProblem("not_found", 404)
            projection = (("organization_id", str(context.subject_uuid)),
                          ("probe_code", "kernel_settings_v1" if action == SETTINGS else "private_probe_v1"),
                          ("label", "Synthetic kernel settings" if action == SETTINGS else "Synthetic private probe"),
                          ("context_revision", str(state.revision)))
            if action == ENTER:
                projection = (("organization_id", str(context.subject_uuid)),
                              ("context_revision", str(state.revision)))
            # One complete eligible grant supports this atom; never compose bounds.
            supporting = max((g for g in eligible if action in BUNDLES[(g.role_code, g.role_version)]),
                             key=lambda g: g.expires_at)
            # Audit first, then final wall-clock check: rollback audit if deadlines pass.
            _audit(organization_id=context.subject_uuid, actor=user, session=session,
                   action=action, result="allow", reason_code="authorized",
                   target_id=context.subject_uuid, fixture_batch=state.fixture_batch,
                   grant=supporting, role_version=supporting.role_version,
                   new_grant_revision=supporting.revision,
                   new_context_revision=state.revision, correlation_id=correlation)
            now = db_clock()
            final_actions, _ = _eligible_actions(grants, now)
            if deadline is None or now >= deadline:
                raise KernelProblem("authentication_required", 401)
            if ENTER not in final_actions or action not in final_actions or now >= supporting.expires_at:
                raise KernelProblem("not_found", 404)
            decision = AuthorizationDecision(True, "authorized", 200, correlation,
                                             context.subject_uuid, state.revision,
                                             tuple(sorted(final_actions)), projection)
        return decision
    except KernelProblem as exc:
        problem = exc
    except APIException as exc:
        # No normalization of auth success; retain transport status, redact nested details.
        problem = KernelProblem("authentication_required" if exc.status_code == 401 else "authentication_rejected", exc.status_code)
    except FlowProblem as exc:
        problem = KernelProblem("authentication_required" if exc.status == 401 else "authorization_unavailable", exc.status)
    except DatabaseError:
        logger.warning("Kernel dependency unavailable; correlation=%s", correlation)
        return AuthorizationDecision(False, "authorization_unavailable", 503, correlation)
    # No context/target existence or secret-bearing action strings in denial events.
    try:
        with transaction.atomic(durable=True):
            transaction_limits()
            _audit(actor_id=actor_id, session_id=session_id, action="context_request",
                   result="deny", reason_code=problem.code, correlation_id=correlation)
    except (DatabaseError, KernelProblem):
        logger.warning("Kernel dependency unavailable; correlation=%s", correlation)
        return AuthorizationDecision(False, "authorization_unavailable", 503, correlation)
    return AuthorizationDecision(False, problem.code, problem.status, correlation)
