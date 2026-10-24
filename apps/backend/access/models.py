"""Additive synthetic authority records. PostgreSQL guards live in migration 0002."""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models.functions import Now


class NGOKernelState(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField("organizations.Organization", on_delete=models.PROTECT)
    fixture_batch = models.UUIDField()
    evidence_ref = models.CharField(max_length=160)
    created_at = models.DateTimeField(db_default=Now())
    revision = models.PositiveBigIntegerField(default=1)
    mode = models.CharField(max_length=12, default="disabled")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(revision__gte=1), name="kernel_revision_positive"),
            models.CheckConstraint(condition=models.Q(mode__in=["disabled", "synthetic"]), name="kernel_mode_closed"),
            models.CheckConstraint(condition=~models.Q(evidence_ref=""), name="kernel_evidence_required"),
        ]


class SyntheticPrincipal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    fixture_batch = models.UUIDField()
    evidence_ref = models.CharField(max_length=160)
    created_at = models.DateTimeField(db_default=Now())

    class Meta:
        constraints = [models.CheckConstraint(condition=~models.Q(evidence_ref=""), name="synthetic_evidence_required")]


class NGOGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.PROTECT)
    subject = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="synthetic_ngo_grants")
    role_code = models.CharField(max_length=40)
    role_version = models.PositiveSmallIntegerField(default=1)
    scope_kind = models.CharField(max_length=20, default="organization")
    source_kind = models.CharField(max_length=24, default="synthetic_fixture")
    source_ref = models.CharField(max_length=160)
    fixture_batch = models.UUIDField()
    issuer_process = models.CharField(max_length=40, default="kernel_fixture_v1")
    issuing_actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="synthetic_issued_grants")
    verification_status = models.CharField(max_length=24, default="unverified")
    approval_evidence_ref = models.CharField(max_length=160)
    effective_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(db_default=Now())
    revision = models.PositiveBigIntegerField(default=1)
    revoked_at = models.DateTimeField(null=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name="synthetic_revoked_grants")
    revoked_by_process = models.CharField(max_length=40, blank=True, default="")
    revocation_reason = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("effective_at")) & models.Q(expires_at__lte=models.F("effective_at") + timedelta(hours=24)), name="grant_lifetime_bounded"),
            models.CheckConstraint(condition=models.Q(role_code__in=["ngo_kernel_reader", "ngo_kernel_admin_probe"], role_version=1), name="grant_bundle_closed"),
            models.CheckConstraint(condition=models.Q(scope_kind="organization", source_kind="synthetic_fixture", issuer_process="kernel_fixture_v1"), name="grant_scope_source_closed"),
            models.CheckConstraint(condition=models.Q(verification_status__in=["synthetic_verified", "unverified"]), name="grant_verification_closed"),
            models.CheckConstraint(condition=~models.Q(source_ref="") & ~models.Q(approval_evidence_ref=""), name="grant_evidence_required"),
            models.CheckConstraint(condition=models.Q(revision__gte=1), name="grant_revision_positive"),
            models.CheckConstraint(condition=(models.Q(revoked_at__isnull=True, revoked_by__isnull=True, revoked_by_process="", revocation_reason="") | (models.Q(revoked_at__isnull=False) & ~models.Q(revocation_reason="") & (models.Q(revoked_by__isnull=False) | ~models.Q(revoked_by_process="")))), name="grant_revocation_complete"),
            models.UniqueConstraint(fields=["organization", "subject", "role_code", "role_version"], condition=models.Q(revoked_at__isnull=True), name="grant_unrevoked_slot_unique"),
        ]
        indexes = [
            models.Index(fields=["organization", "subject", "revoked_at"], name="grant_tenant_subject_idx"),
            models.Index(fields=["organization", "expires_at"], name="grant_tenant_expiry_idx"),
        ]


class AuthorizationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", null=True, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    session = models.ForeignKey("accounts.AuthSession", null=True, on_delete=models.PROTECT)
    actor_process = models.CharField(max_length=40, blank=True, default="")
    action = models.CharField(max_length=64)
    result = models.CharField(max_length=16)
    reason_code = models.CharField(max_length=64)
    target_id = models.UUIDField(null=True)
    grant = models.ForeignKey(NGOGrant, null=True, on_delete=models.PROTECT)
    role_version = models.PositiveSmallIntegerField(null=True)
    old_context_revision = models.PositiveBigIntegerField(null=True)
    new_context_revision = models.PositiveBigIntegerField(null=True)
    old_grant_revision = models.PositiveBigIntegerField(null=True)
    new_grant_revision = models.PositiveBigIntegerField(null=True)
    fixture_batch = models.UUIDField(null=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    created_at = models.DateTimeField(db_default=Now())
    evidence_ref = models.CharField(max_length=160, blank=True, default="")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(result__in=["allow", "deny", "change"]), name="authz_result_closed"),
            models.CheckConstraint(condition=models.Q(organization__isnull=False) | models.Q(result="deny") | models.Q(action="discovery"), name="authz_context_required"),
        ]
        indexes = [models.Index(fields=["organization", "created_at"], name="authz_tenant_time_idx")]
