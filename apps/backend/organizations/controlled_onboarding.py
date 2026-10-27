"""Non-writing transition preflight, never permission or an executable command.

No issuer, appointment, token, invitation-delivery or grant writer is implemented.
Distinct accounts alone do not establish distinct independently vetted humans.
"""

from dataclasses import dataclass


class PreflightConflict(ValueError):
    pass


@dataclass(frozen=True)
class Proposal:
    next_state: str
    next_revision: int


def preflight(
    *,
    state,
    revision,
    expected_revision,
    command,
    initiator,
    actor,
    attestation_purposes=(),
):
    if (
        type(revision) is not int
        or type(expected_revision) is not int
        or revision < 1
        or expected_revision != revision
    ):
        raise PreflightConflict("Stale revision")
    transitions = {
        ("draft", "submit"): "submitted",
        ("returned", "submit"): "submitted",
        ("submitted", "approve"): "approved",
        ("submitted", "reject"): "rejected",
        ("submitted", "return"): "returned",
        ("draft", "withdraw"): "withdrawn",
        ("returned", "withdraw"): "withdrawn",
        ("submitted", "withdraw"): "withdrawn",
    }
    target = transitions.get((state, command))
    if target is None or initiator is None or actor is None:
        raise PreflightConflict("Invalid transition")
    if command in ("approve", "reject", "return"):
        if actor == initiator:
            raise PreflightConflict("Independent reviewer required")
    elif actor != initiator:
        raise PreflightConflict("Initiator required")
    if command in ("submit", "approve") and set(attestation_purposes) != {
        "organization_eligibility",
        "representative_mandate",
    }:
        raise PreflightConflict("Separate external attestations required")
    return Proposal(target, revision + 1)


def command_available(user, command):
    # This cannot be enabled with a setting, staff/Board flag or synthetic grant.
    # Exact E04 / GM01-12 provisioning and command assurance remain unapproved.
    return False
