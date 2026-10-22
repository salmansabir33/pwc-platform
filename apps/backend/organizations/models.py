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

class OrganizationWorkspace(models.Model):
    class State(models.TextChoices):
        PROVISIONAL = "provisional", "Provisional"
        PENDING = "pending", "Verification pending"
        VERIFIED = "verified", "Verified"
        RESTRICTED = "restricted", "Restricted"
        DEACTIVATED = "deactivated", "Deactivated"
    organization = models.OneToOneField(Organization, on_delete=models.PROTECT, related_name="workspace")
    state = models.CharField(max_length=16, choices=State.choices, default=State.PROVISIONAL)

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
        constraints = [models.UniqueConstraint(fields=["organization", "user", "role"], name="unique_org_user_role")]
