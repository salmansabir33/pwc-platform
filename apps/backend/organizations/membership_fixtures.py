"""Fixed fictional 05A scenarios, not intake, identity evidence or authority."""

from dataclasses import replace
from .member_import_fixtures import ORGANIZATION_ID
from .membership_preview import (
    AdmissionRequestFixture,
    CategoryFixture,
    MembershipSnapshotFixture,
    evaluate_admission,
)

SCENARIOS = ("open", "approval", "invitation", "conflict")
CATEGORY = CategoryFixture(ORGANIZATION_ID, "ORDINARY", "Synthetic Ordinary")
APPLICATION = AdmissionRequestFixture(
    ORGANIZATION_ID, "REQUEST_A", "MEMBER_A", "ORDINARY", "application"
)
INVITATION = replace(APPLICATION, route="invitation")


class UnknownMembershipScenario(ValueError):
    pass


def preview_membership_fixture(scenario):
    if type(scenario) is not str or scenario not in SCENARIOS:
        raise UnknownMembershipScenario("Unknown synthetic membership scenario")
    if scenario == "open":
        return (
            evaluate_admission(
                MembershipSnapshotFixture(ORGANIZATION_ID, "open", (CATEGORY,)),
                APPLICATION,
                "apply",
            ),
        )
    if scenario == "conflict":
        other = replace(APPLICATION, request_reference="REQUEST_B", state="pending")
        return (
            evaluate_admission(
                MembershipSnapshotFixture(
                    ORGANIZATION_ID, "approval", (CATEGORY,), (other,)
                ),
                APPLICATION,
                "apply",
            ),
        )
    request = INVITATION if scenario == "invitation" else APPLICATION
    initial = MembershipSnapshotFixture(ORGANIZATION_ID, scenario, (CATEGORY,))
    # Independent fixed snapshots demonstrate both steps; no transition is applied.
    pending = replace(request, state="pending")
    following = replace(initial, requests=(pending,))
    return (
        evaluate_admission(
            initial, request, "invite" if scenario == "invitation" else "apply"
        ),
        evaluate_admission(
            following, pending, "accept" if scenario == "invitation" else "approve"
        ),
    )
