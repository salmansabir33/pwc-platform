"""Bounded ordinary-account invitation storage; not a live issuer root."""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import F, Q


class PersonalInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issuer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    source_digest = models.CharField(max_length=64)
    recipient = models.EmailField(max_length=254)
    token_digest = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True)
    email_verified_at = models.DateTimeField(null=True)
    proof_digest = models.CharField(max_length=64, blank=True)
    proof_expires_at = models.DateTimeField(null=True)
    failures = models.PositiveSmallIntegerField(default=0)
    # Encrypted pending message only. No dispatcher/SMTP activation is installed.
    mail_key = models.CharField(max_length=100, blank=True)
    mail_payload = models.BinaryField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(expires_at=F("created_at") + timedelta(hours=24)),
                name="personal_invitation_24h",
            ),
            models.CheckConstraint(
                condition=Q(
                    token_digest__regex=r"^[0-9a-f]{64}$",
                    source_digest__regex=r"^[0-9a-f]{64}$",
                ),
                name="personal_invitation_digests",
            ),
            models.CheckConstraint(
                condition=Q(failures__lte=5), name="personal_invitation_failures"
            ),
            models.CheckConstraint(
                condition=Q(email_verified_at__isnull=True)
                | Q(
                    email_verified_at__lt=F("expires_at"),
                    email_verified_at__gte=F("created_at"),
                ),
                name="personal_invitation_email_time",
            ),
            models.UniqueConstraint(
                fields=["recipient"],
                condition=Q(cancelled_at__isnull=True),
                name="personal_invitation_pending_recipient",
            ),
        ]
