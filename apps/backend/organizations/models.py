import uuid
from django.conf import settings
from django.db import models


class Organization(models.Model):
    class Classification(models.TextChoices):
        REGISTERED = "registered", "Registered"
        UNREGISTERED = "unregistered", "Eligible unregistered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=250)
    city = models.CharField(max_length=100, blank=True)
    classification = models.CharField(max_length=16, choices=Classification.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    lookup_name = models.TextField(blank=True)
    lookup_city = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        import unicodedata

        self.lookup_name = " ".join(
            unicodedata.normalize("NFKC", self.name).split()
        ).casefold()
        self.lookup_city = " ".join(
            unicodedata.normalize("NFKC", self.city).split()
        ).casefold()
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {
                "lookup_name",
                "lookup_city",
            }
        super().save(*args, **kwargs)


class OrganizationWorkspace(models.Model):
    class State(models.TextChoices):
        PROVISIONAL = "provisional", "Provisional"
        PENDING = "pending", "Verification pending"
        VERIFIED = "verified", "Verified"
        RESTRICTED = "restricted", "Restricted"
        DEACTIVATED = "deactivated", "Deactivated"

    organization = models.OneToOneField(
        Organization, on_delete=models.PROTECT, related_name="workspace"
    )
    state = models.CharField(
        max_length=16, choices=State.choices, default=State.PROVISIONAL
    )


class OrganizationAccess(models.Model):
    class Role(models.TextChoices):
        CLAIMANT = "claimant", "Claimant"
        ADMIN = "admin", "Verified administrator"
        MEMBER_MANAGER = "members", "Member manager"

    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    role = models.CharField(max_length=16, choices=Role.choices)
    active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user", "role"], name="unique_org_user_role"
            )
        ]


class OrganizationDraft(models.Model):
    """Private application, not ownership, verification or a workspace grant."""

    class State(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted (review unavailable)"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(Organization, on_delete=models.PROTECT)
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    name = models.CharField(max_length=250)
    legal_name = models.CharField(max_length=250, blank=True)
    aliases = models.JSONField(default=list)
    city = models.CharField(max_length=100, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True)
    classification = models.CharField(
        max_length=16, choices=Organization.Classification.choices
    )
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    match_key = models.CharField(max_length=64)
    state = models.CharField(max_length=16, choices=State.choices, default=State.DRAFT)
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claimant", "match_key"],
                condition=models.Q(state__in=["draft", "submitted"]),
                name="one_own_open_draft",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["draft", "submitted", "withdrawn"]),
                name="draft_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="draft_revision_positive"
            ),
        ]
        indexes = [models.Index(fields=["claimant", "id"], name="draft_owner_page")]


class OrganizationClaim(models.Model):
    class State(models.TextChoices):
        PENDING = "pending", "Pending (review unavailable)"
        NEEDS_INFORMATION = "needs_information", "Needs information"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    state = models.CharField(
        max_length=24, choices=State.choices, default=State.PENDING
    )
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claimant", "organization"],
                condition=models.Q(state__in=["pending", "needs_information"]),
                name="one_own_open_claim",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    state__in=["pending", "needs_information", "rejected", "withdrawn"]
                ),
                name="claim_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="claim_revision_positive"
            ),
        ]
        indexes = [models.Index(fields=["claimant", "id"], name="claim_owner_page")]


class RegistryReceipt(models.Model):
    """Owner-scoped create retries, no credentials or request payload retained."""

    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    operation = models.CharField(
        max_length=16, choices=[("draft", "Draft"), ("claim", "Claim")]
    )
    digest = models.CharField(max_length=64)
    resource_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claimant", "key"], name="registry_owner_retry_key"
            )
        ]


class RegistryEvent(models.Model):
    """Append-only metadata history; never store contacts, names or evidence."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session = models.ForeignKey("accounts.AuthSession", on_delete=models.PROTECT)
    draft = models.ForeignKey(OrganizationDraft, null=True, on_delete=models.PROTECT)
    claim = models.ForeignKey(OrganizationClaim, null=True, on_delete=models.PROTECT)
    action = models.CharField(max_length=24)
    revision = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(draft__isnull=False, claim__isnull=True)
                    | models.Q(draft__isnull=True, claim__isnull=False)
                ),
                name="registry_event_one_source",
            ),
            models.UniqueConstraint(
                fields=["draft", "revision"], name="draft_event_revision"
            ),
            models.UniqueConstraint(
                fields=["claim", "revision"], name="claim_event_revision"
            ),
        ]


class VerificationCase(models.Model):
    """Personal application preparation, NEVER an authority or verification result."""

    class Purpose(models.TextChoices):
        ELIGIBILITY = "organization_eligibility", "Organization eligibility"
        MANDATE = "representative_mandate", "Representative mandate"

    class State(models.TextChoices):
        DRAFT = "draft", "Preparation draft"
        SUBMITTED = "submitted", "Preparation submitted; review unavailable"
        WITHDRAWN = "withdrawn", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT)
    draft = models.ForeignKey(OrganizationDraft, null=True, on_delete=models.PROTECT)
    claim = models.ForeignKey(OrganizationClaim, null=True, on_delete=models.PROTECT)
    source_revision = models.PositiveBigIntegerField()
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    track = models.CharField(max_length=16, choices=Organization.Classification.choices)
    state = models.CharField(max_length=16, choices=State.choices, default=State.DRAFT)
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["claimant", "id"], name="verification_owner_page")
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(draft__isnull=False, claim__isnull=True)
                    | models.Q(draft__isnull=True, claim__isnull=False)
                ),
                name="verification_one_source",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["draft", "submitted", "withdrawn"]),
                name="verification_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    purpose__in=["organization_eligibility", "representative_mandate"]
                ),
                name="verification_purpose_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(track__in=["registered", "unregistered"]),
                name="verification_track_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1, source_revision__gte=1),
                name="verification_revisions_positive",
            ),
            models.UniqueConstraint(
                fields=["claimant", "draft", "purpose"],
                condition=models.Q(state__in=["draft", "submitted"]),
                name="one_open_draft_verification",
            ),
            models.UniqueConstraint(
                fields=["claimant", "claim", "purpose"],
                condition=models.Q(state__in=["draft", "submitted"]),
                name="one_open_claim_verification",
            ),
        ]


class EvidencePreparation(models.Model):
    """Synthetic checklist marker, NOT an evidence object, file or assertion of validity."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(VerificationCase, on_delete=models.PROTECT)
    prepared_offline = models.BooleanField(default=False)
    state = models.CharField(
        max_length=16,
        choices=[("planned", "Planned"), ("withdrawn", "Withdrawn")],
        default="planned",
    )
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case"],
                condition=models.Q(state="planned"),
                name="one_active_preparation_marker",
            ),
            models.CheckConstraint(
                condition=models.Q(state__in=["planned", "withdrawn"]),
                name="preparation_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1),
                name="preparation_revision_positive",
            ),
        ]


class VerificationEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey(VerificationCase, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session = models.ForeignKey("accounts.AuthSession", on_delete=models.PROTECT)
    reason_code = models.CharField(
        max_length=32,
        choices=[
            (v, v)
            for v in [
                "applicant_created",
                "preparation_added",
                "preparation_replaced",
                "preparation_withdrawn",
                "preparation_submitted",
                "applicant_withdrawn",
            ]
        ],
    )
    revision = models.PositiveBigIntegerField()
    preparation = models.ForeignKey(
        EvidencePreparation, null=True, on_delete=models.PROTECT
    )
    preparation_revision = models.PositiveBigIntegerField(null=True)
    prepared_offline = models.BooleanField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["case", "revision"], name="verification_event_revision"
            )
        ]


class VerificationReceipt(models.Model):
    claimant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    key = models.UUIDField()
    operation = models.CharField(max_length=24)
    digest = models.CharField(max_length=64)
    case = models.ForeignKey(VerificationCase, on_delete=models.PROTECT)
    preparation = models.ForeignKey(
        EvidencePreparation, null=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claimant", "key"], name="verification_retry_key"
            )
        ]


class ControlledOnboardingRecord(models.Model):
    """Structural preparation only. No HTTP writer/provisioning/authority activation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, null=True, on_delete=models.PROTECT)
    initiator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="initiated_onboarding_records",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.PROTECT,
        related_name="reviewed_onboarding_records",
    )
    state = models.CharField(
        max_length=16,
        default="draft",
        choices=[
            (v, v)
            for v in (
                "draft",
                "submitted",
                "returned",
                "approved",
                "rejected",
                "withdrawn",
            )
        ],
    )
    revision = models.PositiveBigIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    state__in=[
                        "draft",
                        "submitted",
                        "returned",
                        "approved",
                        "rejected",
                        "withdrawn",
                    ]
                ),
                name="controlled_state_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="controlled_revision_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(reviewer__isnull=True)
                | ~models.Q(reviewer=models.F("initiator")),
                name="controlled_no_self_review",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        state__in=["returned", "approved", "rejected"],
                        reviewer__isnull=False,
                    )
                    | models.Q(
                        state__in=["draft", "submitted", "withdrawn"],
                        reviewer__isnull=True,
                    )
                ),
                name="controlled_review_provenance",
            ),
        ]


class ControlledOnboardingRevision(models.Model):
    """Immutable minimized snapshot, not an authoritative evidence finding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(ControlledOnboardingRecord, on_delete=models.PROTECT)
    revision = models.PositiveBigIntegerField()
    organization_name = models.CharField(max_length=250)
    city = models.CharField(max_length=100)
    classification = models.CharField(
        max_length=16, choices=Organization.Classification.choices
    )
    nominee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT
    )
    # Opaque external custody handles, NOT document/person numbers, URLs or notes.
    nomination_reference = models.CharField(max_length=64)
    nominee_reference = models.CharField(max_length=64)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="onboarding_snapshots",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["record", "revision"], name="controlled_snapshot_revision"
            ),
            models.CheckConstraint(
                condition=models.Q(revision__gte=1), name="controlled_snapshot_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(classification__in=["registered", "unregistered"]),
                name="controlled_classification_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    nomination_reference__regex=r"^[A-Z][A-Z0-9_-]{0,63}$",
                    nominee_reference__regex=r"^[A-Z][A-Z0-9_-]{0,63}$",
                ),
                name="controlled_nomination_handles",
            ),
        ]


class OfflineVerificationAttestation(models.Model):
    """External examination recorded separately for eligibility and mandate."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ControlledOnboardingRevision, on_delete=models.PROTECT)
    purpose = models.CharField(max_length=32, choices=VerificationCase.Purpose.choices)
    evidence_reference = models.CharField(max_length=64)
    method_reference = models.CharField(max_length=64)
    examined_at = models.DateTimeField()
    attestor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "purpose"], name="offline_attestation_lane"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    purpose__in=["organization_eligibility", "representative_mandate"]
                ),
                name="offline_attestation_purpose",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    evidence_reference__regex=r"^[A-Z][A-Z0-9_-]{0,63}$",
                    method_reference__regex=r"^[A-Z][A-Z0-9_-]{0,63}$",
                ),
                name="offline_attestation_handles",
            ),
        ]


class ControlledOnboardingEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ControlledOnboardingRevision, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session = models.ForeignKey("accounts.AuthSession", on_delete=models.PROTECT)
    action = models.CharField(
        max_length=24,
        choices=[
            (v, v)
            for v in (
                "recorded",
                "submitted",
                "returned",
                "approved",
                "rejected",
                "withdrawn",
            )
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot", "action"], name="controlled_event_once"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    action__in=[
                        "recorded",
                        "submitted",
                        "returned",
                        "approved",
                        "rejected",
                        "withdrawn",
                    ]
                ),
                name="controlled_event_action",
            ),
        ]
