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

    control_digest = models.CharField(max_length=64, blank=True)
    ceremony_key = models.CharField(max_length=100, blank=True)
    ceremony_payload = models.BinaryField(null=True)
    ceremony_expires_at = models.DateTimeField(null=True)
    consumed_at = models.DateTimeField(null=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name="personal_enrollment",
    )
    mail_generation = models.PositiveIntegerField(default=0)
    mail_state = models.CharField(max_length=12, default="empty")
    mail_attempts = models.PositiveSmallIntegerField(default=0)
    mail_next_at = models.DateTimeField(null=True)
    mail_lease_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(user__isnull=True, consumed_at__isnull=True)
                | Q(
                    user__isnull=False,
                    consumed_at__isnull=False,
                    consumed_at__lt=F("expires_at"),
                    consumed_at__gte=F("email_verified_at"),
                    email_verified_at__isnull=False,
                    cancelled_at__isnull=True,
                ),
                name="invitation_complete_before_expiry",
            ),
            models.CheckConstraint(
                condition=Q(
                    ceremony_payload__isnull=True,
                    ceremony_key="",
                    ceremony_expires_at__isnull=True,
                )
                | (
                    Q(
                        ceremony_payload__isnull=False,
                        ceremony_expires_at__lte=F("expires_at"),
                    )
                    & ~Q(ceremony_key="")
                    & Q(ceremony_expires_at__isnull=False)
                ),
                name="invitation_ceremony_pair",
            ),
            models.CheckConstraint(
                condition=Q(mail_attempts__lte=5), name="invitation_mail_attempts"
            ),
            models.CheckConstraint(
                condition=Q(
                    mail_state__in=[
                        "empty",
                        "pending",
                        "leased",
                        "sent",
                        "failed",
                        "expired",
                        "cancelled",
                    ]
                ),
                name="invitation_mail_states",
            ),
            models.CheckConstraint(
                condition=~Q(mail_state="leased") | Q(mail_lease_at__isnull=False),
                name="invitation_mail_lease",
            ),
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
                condition=Q(cancelled_at__isnull=True, consumed_at__isnull=True),
                name="personal_invitation_pending_recipient",
            ),
        ]
