import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    preferred_language = models.CharField(max_length=8, default="en")
    auth_epoch = models.PositiveBigIntegerField(default=1)
    recovery_generation = models.PositiveBigIntegerField(default=0)
    recovery_hold_state = models.CharField(
        max_length=16,
        default="clear",
        choices=[
            ("clear", "Clear"),
            ("restricted", "Restricted"),
            ("review_required", "Review required"),
        ],
    )
    hold_set_at = models.DateTimeField(null=True, blank=True)
    hold_reason = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("", "None"),
            ("password_reset", "Password reset"),
            ("recovery_code", "Recovery code"),
            ("factor_loss", "Factor loss"),
            ("compromise", "Compromise"),
        ],
    )
    hold_factor = models.ForeignKey(
        "MfaFactor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="held_users",
    )
    hold_factor_revision = models.PositiveBigIntegerField(null=True, blank=True)
    hold_cleared_event = models.ForeignKey(
        "SecurityEvent",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cleared_holds",
    )

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(auth_epoch__gte=1), name="user_auth_epoch_positive"
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        recovery_hold_state="clear",
                        hold_set_at__isnull=True,
                        hold_reason="",
                    )
                    | (
                        models.Q(
                            recovery_hold_state__in=["restricted", "review_required"],
                            hold_set_at__isnull=False,
                            hold_reason__in=[
                                "password_reset",
                                "recovery_code",
                                "factor_loss",
                                "compromise",
                            ],
                        )
                    )
                ),
                name="user_hold_consistent",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    hold_factor__isnull=True, hold_factor_revision__isnull=True
                )
                | models.Q(
                    hold_factor__isnull=False,
                    hold_factor_revision__gte=1,
                    hold_factor_revision__isnull=False,
                ),
                name="user_hold_factor_pair",
            ),
        ]

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError

        if self.hold_factor_id and self.hold_factor.user_id != self.pk:
            raise ValidationError({"hold_factor": "Factor must belong to this user."})
        if self.hold_cleared_event_id and self.hold_cleared_event.subject_id != self.pk:
            raise ValidationError(
                {"hold_cleared_event": "Event must concern this user."}
            )


# Django discovers these inert models as part of the accounts application.
from .security_models import (  # noqa: E402,F401
    AssuranceIntent,
    AuthAbuseBucket,
    AuthChallenge,
    AuthSession,
    DeliveryIntent,
    MfaFactor,
    MfaRecoveryCode,
    MobileCredential,
    SecurityEvent,
    UserContact,
)
