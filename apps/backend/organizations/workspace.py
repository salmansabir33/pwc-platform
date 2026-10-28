"""Minimized historical personal workspace, NOT NGO administration authority.

Caller holds the live User/session locks. Every row and joined case is owner scoped.
No controlled onboarding, invitation, roster, grant or private audit reader exists.
"""

import uuid
from django.core import signing
from django.conf import settings
from . import registry
from .models import OrganizationDraft, OrganizationClaim, VerificationCase

STATES = ("draft", "submitted", "pending", "needs_information", "rejected", "withdrawn")


def history(user, params):
    kind = params.get("kind", "draft")
    state = params.get("state", "")
    if kind not in ("draft", "claim") or state and state not in STATES:
        registry.fail("VALIDATION_ERROR", 400)
    model = OrganizationDraft if kind == "draft" else OrganizationClaim
    query = model.objects.filter(claimant=user)
    if state:
        query = query.filter(state=state)
    cursor = params.get("cursor")
    binding = {"owner": str(user.pk), "kind": kind, "state": state}
    if cursor:
        try:
            payload = signing.loads(cursor, salt="pwc.workspace.v1", max_age=3600)
            if any(payload[k] != value for k, value in binding.items()):
                raise ValueError()
            query = query.filter(id__gt=uuid.UUID(payload["after"]))
        except (signing.BadSignature, KeyError, ValueError, TypeError):
            registry.fail("VALIDATION_ERROR", 400)
    values = list(query.order_by("id")[:21])
    more = len(values) > 20
    values = values[:20]
    results = project(user, kind, values)
    return {
        "results": results,
        "next_cursor": signing.dumps(
            dict(binding, after=str(values[-1].pk)), salt="pwc.workspace.v1"
        )
        if more
        else None,
        "administration_available": False,
        "intake_available": False,
        "verification_available": settings.PWC_VERIFICATION_ENABLED,
    }


def project(user, kind, values):
    """Same minimized projection for pages and owner-only point reconciliation."""
    ids = [v.pk for v in values]
    cases = VerificationCase.objects.filter(claimant=user, **{kind + "_id__in": ids})
    if not settings.PWC_VERIFICATION_ENABLED:
        cases = cases.none()
    # Do not join private organization data for claims. Historical IDs and state
    # are already owned; a claim does NOT confer access to the target's profile.
    by_source = {}
    for case in cases.order_by(kind + "_id", "purpose", "-created_at", "-id").distinct(
        kind + "_id", "purpose"
    ):
        by_source.setdefault(getattr(case, kind + "_id"), []).append(case)
    results = []
    for value in values:
        results.append(
            {
                "id": str(value.pk),
                "kind": kind,
                "organization_id": str(value.organization_id),
                "revision": value.revision,
                "state": value.state,
                "name": value.name if kind == "draft" else None,
                "city": value.city if kind == "draft" else None,
                "classification": value.classification if kind == "draft" else None,
                "can_withdraw": value.state
                in ("draft", "submitted", "pending", "needs_information"),
                "verification": [
                    {
                        "id": str(c.pk),
                        "purpose": c.purpose,
                        "state": c.state,
                        "revision": c.revision,
                        "source_revision": c.source_revision,
                        "stale": c.source_revision != value.revision,
                    }
                    for c in by_source.get(value.pk, [])
                ],
            }
        )
    return results


def detail(user, kind, pk):
    if kind not in ("draft", "claim"):
        registry.fail("VALIDATION_ERROR", 400)
    model = OrganizationDraft if kind == "draft" else OrganizationClaim
    # User/session locked by adapter, then exact owner lookup; foreign and missing
    # are indistinguishable. No target organization/profile/receipt lookup.
    value = registry.own(model, user, pk)
    return {
        "application": project(user, kind, [value])[0],
        "administration_available": False,
        "intake_available": False,
        "verification_available": settings.PWC_VERIFICATION_ENABLED,
    }
