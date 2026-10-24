"""Synthetic TTL disposal; never removes Users, sessions, grants or audit events."""

from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import AuthAbuseBucket, AuthChallenge, DeliveryIntent


def cleanup_flows(limit=100):
    now = timezone.now()
    flows = payloads = 0
    with transaction.atomic():
        challenges = list(
            AuthChallenge.objects.select_for_update(skip_locked=True)
            .filter(
                purpose__in=["registration", "reset"],
                expires_at__lte=now,
            )
            # Reserved reset notices already had their proof payload cancelled
            # atomically. Skip them until their own retention deadline so they
            # cannot occupy every batch slot and starve expired pending flows.
            .exclude(Q(purpose="reset", consumed_at__gt=now - timedelta(minutes=15)))
            .order_by("expires_at", "id")[:limit]
        )
        for challenge in challenges:
            intents = DeliveryIntent.objects.filter(challenge=challenge)
            payloads += intents.filter(encrypted_payload__isnull=False).count()
            intents.filter(state__in=["pending", "leased"]).update(
                state="expired",
                encrypted_payload=None,
                key_id="",
                secret_deleted_at=now,
                lease_expires_at=None,
            )
            intents.delete()
            challenge.delete()
            flows += 1
        buckets = list(
            AuthAbuseBucket.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now)
            .order_by("expires_at", "id")
            .values_list("id", flat=True)[:limit]
        )
        AuthAbuseBucket.objects.filter(pk__in=buckets).delete()
    return {"flows": flows, "payloads": payloads, "buckets": len(buckets)}
