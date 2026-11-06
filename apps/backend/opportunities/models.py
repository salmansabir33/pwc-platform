"""08C-A storage foundation, not an authorized publishing service."""

import uuid
from django.db import models
from django.db.models import Q
from organizations.registry_serializers import normalize


class Opportunity(models.Model):
    class Type(models.TextChoices):
        JOB = "JOB", "Job"
        INTERNSHIP = "INTERNSHIP", "Internship"
        PROJECT = "PROJECT", "Project discovery item"

    class State(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="opportunities",
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    state = models.CharField(max_length=9, choices=State.choices, default=State.DRAFT)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=1000, blank=True)
    lookup_title = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(type__in=["JOB", "INTERNSHIP", "PROJECT"]),
                name="opportunity_valid_type",
            ),
            models.CheckConstraint(
                condition=Q(title__regex=r"\S"), name="opportunity_nonblank_title"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        state="DRAFT",
                        published_at__isnull=True,
                        withdrawn_at__isnull=True,
                    )
                    | Q(
                        state="PUBLISHED",
                        published_at__isnull=False,
                        withdrawn_at__isnull=True,
                    )
                    | Q(
                        state="WITHDRAWN",
                        published_at__isnull=False,
                        withdrawn_at__isnull=False,
                        withdrawn_at__gte=models.F("published_at"),
                    )
                ),
                name="opportunity_lifecycle_dates",
            ),
        ]
        indexes = [
            models.Index(
                fields=["type", "id"],
                condition=Q(state="PUBLISHED"),
                name="opportunity_public_type_id",
            ),
            models.Index(
                fields=["organization", "id"],
                condition=Q(state="PUBLISHED"),
                name="opportunity_public_org_id",
            ),
        ]

    def save(self, *args, **kwargs):
        self.lookup_title = normalize(self.title)
        if kwargs.get("update_fields") is not None:
            kwargs["update_fields"] = set(kwargs["update_fields"]) | {"lookup_title"}
        super().save(*args, **kwargs)
