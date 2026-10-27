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
