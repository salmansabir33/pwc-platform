"""Export ONLY these built-in redacted examples to client fixture bundles."""

from dataclasses import replace
from datetime import datetime, timezone
from uuid import UUID
from .category_policy_preview import (
    CategoryPolicyFixture,
    CategoryVersionFixture,
    PolicyVersionFixture,
    PendingPolicyFixture,
    preview_change_category,
    preview_change_mode,
)
from .member_import_fixtures import ORGANIZATION_ID
from .member_import_preview import TEMPLATE
from .membership_fixtures import CATEGORY, APPLICATION
from .membership_preview import MembershipSnapshotFixture
from .membership_workbench import (
    MembershipFixture,
    preview_admission,
    preview_member_change,
    prepare_import,
    MembershipWorkbenchError,
)


def demonstrations():
    source = MembershipFixture(
        MembershipSnapshotFixture(
            ORGANIZATION_ID,
            "approval",
            (
                CATEGORY,
                replace(CATEGORY, reference="ASSOCIATE", label="Synthetic Associate"),
            ),
        )
    )
    pending = preview_admission(
        source, source.source_revision(), APPLICATION, "apply"
    ).projected
    accepted = preview_admission(
        pending, pending.source_revision(), pending.policy.requests[0], "approve"
    ).projected
    assigned = preview_member_change(
        accepted, accepted.source_revision(), "MEMBER_A", category="ASSOCIATE"
    ).projected
    suspended = preview_member_change(
        assigned, assigned.source_revision(), "MEMBER_A", state="suspended"
    ).projected
    ended = preview_member_change(
        suspended, suspended.source_revision(), "MEMBER_A", state="ended"
    ).projected
    try:
        preview_member_change(
            assigned, accepted.source_revision(), "MEMBER_A", state="suspended"
        )
    except MembershipWorkbenchError as error:
        stale = error.to_diagnostic()
    else:
        raise AssertionError("Stale fixture unexpectedly accepted")
    category_id = UUID(int=9001)
    at = datetime(2026, 11, 4, tzinfo=timezone.utc)
    policy = CategoryPolicyFixture(
        (
            PolicyVersionFixture(
                ORGANIZATION_ID,
                1,
                "approval",
                (CategoryVersionFixture(category_id, CATEGORY),),
                at,
            ),
        ),
        (PendingPolicyFixture(category_id, 1),),
    )
    changed_policy = preview_change_mode(
        policy, policy.source_revision(), 1, "invitation", at=at
    )
    deactivated = preview_change_category(
        changed_policy,
        changed_policy.source_revision(),
        2,
        category_id,
        1,
        at=at,
        deactivate=True,
    )
    return {
        "version": "pwc.membership-demonstrations.internal.v1",
        "synthetic_only": True,
        "commit_available": False,
        "scenarios": [
            {"id": "admission", "steps": [pending.to_summary(), accepted.to_summary()]},
            {"id": "category", "steps": [assigned.to_summary()]},
            {"id": "status", "steps": [suspended.to_summary(), ended.to_summary()]},
            {"id": "stale", "steps": [stale]},
            {
                "id": "import",
                "steps": [
                    prepare_import(
                        accepted, accepted.source_revision(), TEMPLATE.sample_csv()
                    ).to_summary()
                ],
            },
            {
                "id": "category-policy",
                "steps": [policy.to_summary(), deactivated.to_summary()],
            },
        ],
    }
