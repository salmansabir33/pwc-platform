"""Security records; cryptography and workflows live in service modules.

Choices are database-enforced as well as form validated. full_clean() provides
cross-row validation but is not called by ORM saves/bulk writes. Transactional
services must lock and recheck ownership explicitly; a FK cannot enforce joins.
"""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

DIGEST_VALIDATOR = RegexValidator(
    r"\A[0-9a-f]{64}\Z", "Supply a digest, never a raw secret."
)


def digest(**kwargs):
    return models.CharField(max_length=64, validators=[DIGEST_VALIDATOR], **kwargs)


def user_fk(**kwargs):
    return models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, **kwargs
    )


def choice_check(field, values, name):
    return models.CheckConstraint(condition=Q(**{f"{field}__in": values}), name=name)


def expires_check(start, end, name):
    return models.CheckConstraint(condition=Q(**{f"{end}__gt": F(start)}), name=name)


def exclusive_end(name):
    return models.CheckConstraint(
        condition=Q(consumed_at__isnull=True) | Q(invalidated_at__isnull=True),
        name=name,
    )


class SecurityRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner_links = ()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        owner = getattr(self, "user_id", None)
        session = (
            getattr(self, "session", None)
            if hasattr(self, "session_id") and self.session_id
            else None
        )
        owner = owner or (session.user_id if session else None)
        for field in self.owner_links:
            if getattr(self, f"{field}_id", None):
                linked_owner = getattr(getattr(self, field), "user_id", None)
                if owner and linked_owner and owner != linked_owner:
                    raise ValidationError(
                        {field: "Security record must belong to the same user."}
                    )

    def __str__(self):
        # Never include contacts, digests, ciphertext or risk data in display.
        return f"{self._meta.object_name} {self.pk}"


class UserContact(SecurityRecord):
    user = user_fk(related_name="contacts")
    kind = models.CharField(
        max_length=16, choices=[("email", "Email")], default="email"
    )
    display_value = models.CharField(max_length=254)
    normalized_value = models.CharField(max_length=254, db_collation="C")
    created_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        constraints = [
            choice_check("kind", ["email"], "contact_kind_email"),
            models.CheckConstraint(
                condition=~Q(normalized_value="") & ~Q(display_value=""),
                name="contact_values_nonempty",
            ),
            models.UniqueConstraint(
                fields=["kind", "normalized_value"],
                condition=Q(verified_at__isnull=False, retired_at__isnull=True),
                name="contact_verified_owner_unique",
            ),
            models.UniqueConstraint(
                fields=["user", "kind"],
                condition=Q(is_primary=True, retired_at__isnull=True),
                name="contact_primary_unique",
            ),
            models.CheckConstraint(
                condition=Q(is_primary=False)
                | Q(verified_at__isnull=False, retired_at__isnull=True),
                name="contact_primary_verified_active",
            ),
        ]


class AuthSession(SecurityRecord):
    user = user_fk(related_name="security_sessions")
    transport = models.CharField(
        max_length=8, choices=[("web", "Web"), ("mobile", "Mobile")]
    )
    portal = models.CharField(
        max_length=16,
        choices=[
            ("ngo_web", "NGO Web"),
            ("pwc_ops", "PWC Operations"),
            ("mobile", "Mobile"),
        ],
    )
    web_key_digest = digest(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_interactive_at = models.DateTimeField(default=timezone.now)
    absolute_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=64, blank=True)
    auth_epoch = models.PositiveBigIntegerField()
    credential_generation = models.PositiveBigIntegerField(default=1)
    last_mfa_at = models.DateTimeField(null=True, blank=True)
    mfa_method = models.CharField(
        max_length=16,
        blank=True,
        choices=[("", "None"), ("totp", "TOTP"), ("recovery_code", "Recovery code")],
    )
    factor_revision = models.PositiveBigIntegerField(null=True, blank=True)
    device_label = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(revoked_at__isnull=True, revocation_reason="")
                | (Q(revoked_at__isnull=False) & ~Q(revocation_reason="")),
                name="session_revocation_consistent",
            ),
            models.CheckConstraint(
                condition=Q(
                    mfa_method="",
                    last_mfa_at__isnull=True,
                    factor_revision__isnull=True,
                )
                | Q(
                    mfa_method__in=["totp", "recovery_code"],
                    last_mfa_at__isnull=False,
                    factor_revision__isnull=False,
                    factor_revision__gte=1,
                ),
                name="session_assurance_consistent",
            ),
            models.CheckConstraint(
                condition=Q(web_key_digest__isnull=True)
                | Q(web_key_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="authsession_web_key_digest_shape",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        transport="web",
                        portal__in=["ngo_web", "pwc_ops"],
                        web_key_digest__isnull=False,
                    )
                    & ~Q(web_key_digest="")
                )
                | Q(transport="mobile", portal="mobile", web_key_digest__isnull=True),
                name="session_transport_binding",
            ),
            expires_check(
                "created_at", "absolute_expires_at", "session_positive_lifetime"
            ),
            models.CheckConstraint(
                condition=Q(
                    last_interactive_at__gte=F("created_at"),
                    last_interactive_at__lt=F("absolute_expires_at"),
                ),
                name="session_activity_in_lifetime",
            ),
            models.CheckConstraint(
                condition=Q(auth_epoch__gte=1, credential_generation__gte=1),
                name="session_positive_versions",
            ),
            choice_check(
                "mfa_method", ["", "totp", "recovery_code"], "session_mfa_method_valid"
            ),
        ]
        indexes = [models.Index(fields=["user", "revoked_at", "absolute_expires_at"])]


class AuthChallenge(SecurityRecord):
    PURPOSES = ["registration", "reset", "contact_change", "preauth_mfa"]
    user = user_fk(null=True, blank=True, related_name="auth_challenges")
    target_contact = models.ForeignKey(
        UserContact, on_delete=models.PROTECT, null=True, blank=True
    )
    purpose = models.CharField(max_length=20, choices=[(v, v) for v in PURPOSES])
    normalized_target = models.CharField(max_length=254, blank=True)
    flow_control_digest = digest()
    proof_selector = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    proof_digest = digest()
    generation = models.PositiveBigIntegerField(default=1)
    auth_epoch = models.PositiveBigIntegerField(null=True, blank=True)
    transport = models.CharField(
        max_length=8,
        blank=True,
        choices=[("", "None"), ("web", "Web"), ("mobile", "Mobile")],
    )
    portal = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    last_issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    failure_count = models.PositiveIntegerField(default=0)
    eligible = models.BooleanField(default=False)
    delivery_state = models.CharField(
        max_length=16,
        default="pending",
        choices=[(v, v) for v in ["pending", "sent", "failed", "expired", "cancelled"]],
    )
    client_digest = digest(null=True, blank=True)
    factor_revision = models.PositiveBigIntegerField(null=True, blank=True)
    device_label = models.CharField(max_length=100, blank=True)
    owner_links = ("target_contact",)

    class Meta:
        constraints = [
            choice_check(
                "transport", ["", "web", "mobile"], "challenge_transport_valid"
            ),
            models.CheckConstraint(
                condition=Q(eligible=False)
                | Q(purpose__in=["registration", "preauth_mfa"])
                | Q(target_contact__isnull=False),
                name="challenge_contact_required",
            ),
            models.CheckConstraint(
                condition=Q(flow_control_digest__isnull=True)
                | Q(flow_control_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="authchallenge_flow_control_digest_shape",
            ),
            models.CheckConstraint(
                condition=Q(proof_digest__isnull=True)
                | Q(proof_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="authchallenge_proof_digest_shape",
            ),
            choice_check(
                "purpose",
                ["registration", "reset", "contact_change", "preauth_mfa"],
                "challenge_purpose_valid",
            ),
            choice_check(
                "delivery_state",
                ["pending", "sent", "failed", "expired", "cancelled"],
                "challenge_delivery_valid",
            ),
            expires_check("created_at", "expires_at", "challenge_positive_lifetime"),
            exclusive_end("challenge_exclusive_terminal"),
            models.CheckConstraint(
                condition=Q(eligible=False)
                | Q(purpose="registration")
                | Q(user__isnull=False, auth_epoch__gte=1, auth_epoch__isnull=False),
                name="challenge_eligible_owner",
            ),
            models.CheckConstraint(
                condition=Q(generation__gte=1), name="challenge_positive_generation"
            ),
            models.CheckConstraint(
                condition=~Q(purpose="preauth_mfa")
                | Q(transport="web", portal__in=["ngo_web", "pwc_ops"])
                | Q(transport="mobile", portal="mobile"),
                name="challenge_preauth_binding",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "purpose", "expires_at"]),
            models.Index(fields=["purpose", "expires_at"]),
        ]


class MobileCredential(SecurityRecord):
    session = models.ForeignKey(
        AuthSession, on_delete=models.PROTECT, related_name="credentials"
    )
    kind = models.CharField(
        max_length=8, choices=[("access", "Access"), ("refresh", "Refresh")]
    )
    secret_digest = digest(unique=True)
    issued_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    generation = models.PositiveBigIntegerField(default=1)
    consumed_at = models.DateTimeField(null=True, blank=True)
    replaced_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        super().clean()
        if self.session_id and self.session.transport != "mobile":
            raise ValidationError(
                {"session": "Only mobile sessions may own bearer credentials."}
            )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(kind="access", consumed_at__isnull=True)
                | Q(kind="refresh", replaced_at__isnull=True),
                name="credential_terminal_kind",
            ),
            models.CheckConstraint(
                condition=Q(secret_digest__isnull=True)
                | Q(secret_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="mobilecredential_secret_digest_shape",
            ),
            choice_check("kind", ["access", "refresh"], "credential_kind_valid"),
            expires_check("issued_at", "expires_at", "credential_positive_lifetime"),
            models.CheckConstraint(
                condition=Q(generation__gte=1), name="credential_positive_generation"
            ),
            models.UniqueConstraint(
                fields=["session", "kind"],
                condition=Q(consumed_at__isnull=True, replaced_at__isnull=True),
                name="credential_one_current_kind",
            ),
        ]


class MfaFactor(SecurityRecord):
    user = user_fk(related_name="mfa_factors")
    kind = models.CharField(max_length=8, default="totp", choices=[("totp", "TOTP")])
    state = models.CharField(
        max_length=8, choices=[(v, v) for v in ["pending", "active", "revoked"]]
    )
    encrypted_secret = models.BinaryField(editable=False)
    key_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revision = models.PositiveBigIntegerField(default=1)
    last_accepted_timestep = models.PositiveBigIntegerField(null=True, blank=True)
    enrollment_session = models.ForeignKey(AuthSession, on_delete=models.PROTECT)
    auth_epoch = models.PositiveBigIntegerField()
    recovery_generation = models.PositiveBigIntegerField()
    expires_at = models.DateTimeField()
    owner_links = ("enrollment_session",)

    class Meta:
        constraints = [
            choice_check("kind", ["totp"], "factor_kind_totp"),
            models.CheckConstraint(
                condition=Q(
                    state="pending", confirmed_at__isnull=True, revoked_at__isnull=True
                )
                | Q(state="active", confirmed_at__isnull=False, revoked_at__isnull=True)
                | Q(state="revoked", revoked_at__isnull=False),
                name="factor_state_timestamps",
            ),
            models.UniqueConstraint(
                fields=["user"], condition=Q(state="active"), name="factor_one_active"
            ),
            models.UniqueConstraint(
                fields=["user"], condition=Q(state="pending"), name="factor_one_pending"
            ),
            expires_check("created_at", "expires_at", "factor_positive_lifetime"),
            models.CheckConstraint(
                condition=Q(revision__gte=1, auth_epoch__gte=1)
                & ~Q(key_id="")
                & ~Q(encrypted_secret=b""),
                name="factor_secret_metadata",
            ),
        ]


class MfaRecoveryCode(SecurityRecord):
    user = user_fk()
    factor = models.ForeignKey(MfaFactor, on_delete=models.PROTECT)
    factor_revision = models.PositiveBigIntegerField()
    set_id = models.UUIDField()
    code_digest = digest(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    consumed_at = models.DateTimeField(null=True, blank=True)
    owner_links = ("factor",)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(code_digest__isnull=True)
                | Q(code_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="mfarecoverycode_code_digest_shape",
            ),
            models.CheckConstraint(
                condition=Q(factor_revision__gte=1),
                name="recovery_code_revision_positive",
            ),
        ]


class AssuranceIntent(SecurityRecord):
    CONTEXTS = ["personal", "ngo", "platform", "pwc_alliance", "committee", "project"]
    user = user_fk()
    session = models.ForeignKey(AuthSession, on_delete=models.PROTECT)
    auth_epoch = models.PositiveBigIntegerField()
    recovery_generation = models.PositiveBigIntegerField()
    operation = models.CharField(max_length=80)
    context_kind = models.CharField(max_length=16, choices=[(v, v) for v in CONTEXTS])
    context_id = models.UUIDField()
    object_id = models.UUIDField(null=True, blank=True)
    object_version = models.PositiveBigIntegerField(null=True, blank=True)
    request_digest = digest()
    proof_digest = digest(null=True, blank=True, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)
    methods = models.CharField(
        max_length=24,
        blank=True,
        choices=[
            ("", "Pending"),
            ("password", "Password"),
            ("password_totp", "Password and TOTP"),
        ],
    )
    factor_revision = models.PositiveBigIntegerField(null=True, blank=True)
    owner_links = ("session",)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(
                    methods="", proof_digest__isnull=True, factor_revision__isnull=True
                )
                | Q(
                    methods="password",
                    proof_digest__isnull=False,
                    factor_revision__isnull=True,
                )
                | Q(
                    methods="password_totp",
                    proof_digest__isnull=False,
                    factor_revision__isnull=False,
                    factor_revision__gte=1,
                ),
                name="assurance_proof_methods_match",
            ),
            models.CheckConstraint(
                condition=Q(consumed_at__isnull=True) | Q(proof_digest__isnull=False),
                name="assurance_consumed_has_proof",
            ),
            models.CheckConstraint(
                condition=Q(request_digest__isnull=True)
                | Q(request_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="assuranceintent_request_digest_shape",
            ),
            models.CheckConstraint(
                condition=Q(proof_digest__isnull=True)
                | Q(proof_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="assuranceintent_proof_digest_shape",
            ),
            choice_check(
                "context_kind",
                ["personal", "ngo", "platform", "pwc_alliance", "committee", "project"],
                "assurance_context_valid",
            ),
            choice_check(
                "methods", ["", "password", "password_totp"], "assurance_methods_valid"
            ),
            expires_check("created_at", "expires_at", "assurance_positive_lifetime"),
            exclusive_end("assurance_exclusive_terminal"),
            models.CheckConstraint(
                condition=Q(auth_epoch__gte=1) & ~Q(operation=""),
                name="assurance_operation_required",
            ),
        ]


class DeliveryIntent(SecurityRecord):
    STATES = ["pending", "leased", "sent", "failed", "expired", "cancelled"]
    challenge = models.ForeignKey(AuthChallenge, on_delete=models.PROTECT)
    generation = models.PositiveBigIntegerField()
    template = models.CharField(
        max_length=24,
        choices=[
            (v, v) for v in ["registration", "reset", "contact_change", "placeholder"]
        ],
    )
    encrypted_payload = models.BinaryField(null=True, editable=False)
    key_id = models.CharField(max_length=100, blank=True)
    state = models.CharField(
        max_length=10, choices=[(v, v) for v in STATES], default="pending"
    )
    attempts = models.PositiveIntegerField(default=0)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    lease_expires_at = models.DateTimeField(null=True, blank=True)
    secret_deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~Q(state__in=["sent", "failed", "expired", "cancelled"])
                | Q(encrypted_payload__isnull=True),
                name="delivery_terminal_payload_empty",
            ),
            models.UniqueConstraint(
                fields=["challenge", "generation"], name="delivery_generation_unique"
            ),
            choice_check(
                "state",
                ["pending", "leased", "sent", "failed", "expired", "cancelled"],
                "delivery_state_valid",
            ),
            choice_check(
                "template",
                ["registration", "reset", "contact_change", "placeholder"],
                "delivery_template_valid",
            ),
            models.CheckConstraint(
                condition=Q(generation__gte=1), name="delivery_generation_positive"
            ),
            models.CheckConstraint(
                condition=Q(encrypted_payload__isnull=True, key_id="")
                | (
                    Q(encrypted_payload__isnull=False)
                    & ~Q(key_id="")
                    & ~Q(encrypted_payload=b"")
                ),
                name="delivery_payload_key_pair",
            ),
            models.CheckConstraint(
                condition=Q(secret_deleted_at__isnull=True)
                | Q(encrypted_payload__isnull=True),
                name="delivery_deleted_secret_empty",
            ),
            models.CheckConstraint(
                condition=~Q(state="leased") | Q(lease_expires_at__isnull=False),
                name="delivery_lease_required",
            ),
        ]
        indexes = [models.Index(fields=["state", "next_attempt_at"])]


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Security events are append-only.")

    def delete(self):
        raise ValidationError("Security events require a reviewed retention procedure.")

    def bulk_create(self, objs, **kwargs):
        if kwargs.get("update_conflicts"):
            raise ValidationError("Security events are append-only.")
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        raise ValidationError("Security events are append-only.")


class SecurityEvent(SecurityRecord):
    subject = user_fk(null=True, blank=True, related_name="subject_security_events")
    actor = user_fk(null=True, blank=True, related_name="actor_security_events")
    session = models.ForeignKey(
        AuthSession, on_delete=models.PROTECT, null=True, blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    event = models.CharField(max_length=80)
    result = models.CharField(
        max_length=16,
        choices=[("success", "Success"), ("denied", "Denied"), ("failure", "Failure")],
    )
    reason = models.CharField(max_length=80, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)
    # Typed recovery-transition evidence, never arbitrary request bodies/secrets.
    auth_epoch = models.PositiveBigIntegerField(null=True, blank=True)
    recovery_generation = models.PositiveBigIntegerField(null=True, blank=True)
    previous_hold_state = models.CharField(max_length=16, blank=True)
    new_hold_state = models.CharField(max_length=16, blank=True)
    factor_id_snapshot = models.UUIDField(null=True, blank=True)
    factor_revision = models.PositiveBigIntegerField(null=True, blank=True)
    # Deliberately no arbitrary JSON/body metadata field: future risk data needs review.
    objects = AppendOnlyQuerySet.as_manager()

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Security events are append-only.")
        kwargs["force_insert"] = True
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Security events require a reviewed retention procedure.")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=~Q(event=""), name="event_code_required"),
            choice_check(
                "previous_hold_state",
                ["", "clear", "restricted", "review_required"],
                "event_previous_hold_valid",
            ),
            choice_check(
                "new_hold_state",
                ["", "clear", "restricted", "review_required"],
                "event_new_hold_valid",
            ),
            models.CheckConstraint(
                condition=Q(auth_epoch__isnull=True) | Q(auth_epoch__gte=1),
                name="event_epoch_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    factor_id_snapshot__isnull=True, factor_revision__isnull=True
                )
                | Q(
                    factor_id_snapshot__isnull=False,
                    factor_revision__isnull=False,
                    factor_revision__gte=1,
                ),
                name="event_factor_pair",
            ),
            choice_check(
                "result", ["success", "denied", "failure"], "event_result_valid"
            ),
        ]
        indexes = [models.Index(fields=["subject", "created_at"])]


class AuthAbuseBucket(SecurityRecord):
    dimension = models.CharField(
        max_length=16,
        choices=[(v, v) for v in ["target", "ip", "session", "flow", "global"]],
    )
    key_digest = digest()
    route = models.CharField(max_length=80)
    window_start = models.DateTimeField()
    count = models.PositiveBigIntegerField(default=0)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(key_digest__isnull=True)
                | Q(key_digest__regex=r"\A[0-9a-f]{64}\Z"),
                name="authabusebucket_key_digest_shape",
            ),
            models.UniqueConstraint(
                fields=["dimension", "key_digest", "route", "window_start"],
                name="abuse_window_unique",
            ),
            choice_check(
                "dimension",
                ["target", "ip", "session", "flow", "global"],
                "abuse_dimension_valid",
            ),
            expires_check("window_start", "expires_at", "abuse_positive_window"),
        ]
