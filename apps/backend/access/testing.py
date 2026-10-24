"""Isolated fixture writer, NOT a runtime grant-management API.

Use only a separate test/development writer connection. Never expose from views,
admin or a management command. It creates new identities, never enrolls existing ones.
"""
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from functools import wraps

from django.db import DatabaseError, IntegrityError, transaction

from accounts.models import User, UserContact
from organizations.models import Organization, OrganizationWorkspace
from .models import AuthorizationEvent, NGOKernelState, NGOGrant, SyntheticPrincipal
from .registry import BUNDLES
from .security import KernelProblem, db_clock, require_revision, require_synthetic_environment, transaction_limits

PROCESS = "kernel_fixture_v1"
EVIDENCE = "synthetic-fixture-only:no-real-authority"


def lifecycle(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            with transaction.atomic(durable=True):
                transaction_limits()
                require_synthetic_environment()
                return function(*args, **kwargs)
        except IntegrityError:
            problem = KernelProblem("state_conflict", 409)
        except KernelProblem as exc:
            problem = exc
        except DatabaseError:
            raise KernelProblem("authorization_unavailable", 503) from None
        try:
            with transaction.atomic(durable=True):
                transaction_limits()
                AuthorizationEvent.objects.create(
                    actor_process=PROCESS, action="fixture_transition", result="deny",
                    reason_code=problem.code,
                )
        except (DatabaseError, KernelProblem):
            raise KernelProblem("authorization_unavailable", 503) from None
        raise problem
    return wrapped


@dataclass(frozen=True)
class FixtureBatch:
    id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)

    @lifecycle
    def create_user(self):
        key = uuid.uuid4().hex
        user = User(username="synthetic-" + key, email=key + "@pwc.invalid")
        user.set_unusable_password()
        user.save(force_insert=True)
        UserContact.objects.create(user=user, kind="email", normalized_value=user.email, display_value=user.email,
                                   is_primary=True, verified_at=db_clock())
        SyntheticPrincipal.objects.create(user=user, fixture_batch=self.id, evidence_ref=EVIDENCE)
        AuthorizationEvent.objects.create(actor=user, actor_process=PROCESS,
            action="fixture_principal_create", result="deny", reason_code="no_ngo_authority",
            fixture_batch=self.id, evidence_ref=EVIDENCE, target_id=user.pk)
        return user.pk

    @lifecycle
    def create_tenant(self):
        organization = Organization.objects.create(
            name="Synthetic kernel fixture", classification="unregistered")
        OrganizationWorkspace.objects.create(organization=organization, state="verified")
        state = NGOKernelState.objects.create(organization=organization, fixture_batch=self.id,
                                              evidence_ref=EVIDENCE, mode="synthetic")
        AuthorizationEvent.objects.create(organization=organization, actor_process=PROCESS,
            action="fixture_tenant_create", result="change", reason_code="synthetic_only",
            fixture_batch=self.id, evidence_ref=EVIDENCE, target_id=organization.pk, new_context_revision=state.revision)
        return organization.pk

    def _state(self, organization_id):
        state = NGOKernelState.objects.select_for_update().filter(
            organization_id=organization_id, fixture_batch=self.id, mode="synthetic").first()
        if not state:
            raise KernelProblem("not_found", 404)
        return state

    @lifecycle
    def issue(self, organization_id, subject_id, *, expected_revision,
              role_code="ngo_kernel_reader", role_version=1,
              effective_at=None, expires_at=None, verified=True):
        if (role_code, role_version) not in BUNDLES:
            raise KernelProblem("permission_denied", 403)
        # Subject User before context root, also prevents attestation/auth races.
        user = User.objects.select_for_update().filter(pk=subject_id).first()
        if not user or not SyntheticPrincipal.objects.filter(user=user, fixture_batch=self.id).exists():
            raise KernelProblem("not_found", 404)
        state = self._state(organization_id)
        require_revision(state.revision, expected_revision)
        now = db_clock()
        effective_at = effective_at or now
        expires_at = expires_at or (effective_at + timedelta(hours=1))
        if not effective_at < expires_at <= effective_at + timedelta(hours=24):
            raise KernelProblem("state_conflict", 409)
        grant = NGOGrant.objects.create(
            organization_id=organization_id, subject=user,
            role_code=role_code, role_version=role_version, source_ref=str(self.id),
            fixture_batch=self.id, issuer_process=PROCESS, approval_evidence_ref=EVIDENCE,
            verification_status="synthetic_verified" if verified else "unverified",
            effective_at=effective_at, expires_at=expires_at,
        )
        state.revision += 1
        state.save(update_fields=["revision"])
        AuthorizationEvent.objects.create(organization_id=organization_id,
            actor_process=PROCESS, action="fixture_grant_create", result="change",
            reason_code="synthetic_only", grant=grant, target_id=grant.pk, role_version=role_version,
            fixture_batch=self.id, evidence_ref=EVIDENCE,
            old_context_revision=state.revision - 1, new_context_revision=state.revision,
            new_grant_revision=1)
        return grant.pk

    @lifecycle
    def revoke(self, organization_id, grant_id, *, expected_revision, expected_grant_revision):
        # Locate owner without exposing any data, then acquire canonical lock order.
        subject_id = NGOGrant.objects.filter(pk=grant_id, organization_id=organization_id,
                                             fixture_batch=self.id).values_list("subject_id", flat=True).first()
        if subject_id is None:
            raise KernelProblem("not_found", 404)
        User.objects.select_for_update().get(pk=subject_id)
        state = self._state(organization_id)
        require_revision(state.revision, expected_revision)
        grant = NGOGrant.objects.select_for_update().get(pk=grant_id, organization_id=organization_id)
        require_revision(grant.revision, expected_grant_revision)
        if grant.revoked_at is not None:
            return grant.pk  # current-revision owned no-op; never a second mutation/event
        grant.revoked_at = db_clock()
        grant.revoked_by_process = PROCESS
        grant.revocation_reason = "synthetic_fixture_revocation"
        grant.revision += 1
        grant.save(update_fields=["revoked_at", "revoked_by_process", "revocation_reason", "revision"])
        state.revision += 1
        state.save(update_fields=["revision"])
        AuthorizationEvent.objects.create(organization_id=organization_id, actor_process=PROCESS,
            action="fixture_grant_revoke", result="change", reason_code="synthetic_only",
            grant=grant, target_id=grant.pk, role_version=grant.role_version, fixture_batch=self.id,
            evidence_ref=EVIDENCE, old_context_revision=state.revision - 1,
            new_context_revision=state.revision, old_grant_revision=grant.revision - 1,
            new_grant_revision=grant.revision)
        return grant.pk

    @lifecycle
    def disable(self, organization_id, *, expected_revision):
        state = self._state(organization_id)
        require_revision(state.revision, expected_revision)
        state.mode = "disabled"
        state.revision += 1
        state.save(update_fields=["mode", "revision"])
        AuthorizationEvent.objects.create(organization_id=organization_id, actor_process=PROCESS,
            action="fixture_tenant_disable", result="change", reason_code="synthetic_only", target_id=organization_id,
            fixture_batch=self.id, evidence_ref=EVIDENCE,
            old_context_revision=state.revision - 1, new_context_revision=state.revision)
