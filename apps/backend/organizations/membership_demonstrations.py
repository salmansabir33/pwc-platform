"""Export ONLY these built-in redacted examples to client fixture bundles."""

from dataclasses import replace
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
        ],
    }
