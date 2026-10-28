"""Non-writing, non-authorizing exact-revision review-packet preparation.

No public adapter, evidence intake, reviewer appointment, invitation, token or
permission is created. A valid packet is NOT approval or an executable command.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID
from django.utils import timezone
from .controlled_onboarding import preflight, PreflightConflict


@dataclass(frozen=True)
class PreparedSubmission:
    record_id: UUID
    snapshot_id: UUID
    source_revision: int
    proposed_revision: int
    attestation_ids: tuple[UUID, UUID]
    recipient_resolved: bool
    # No available command or invitation token can be inferred from this result.
    command_available: bool = field(default=False, init=False)


def prepare_submission(
    *, record, snapshot, attestations, actor_id, expected_revision, now: datetime
):
    """Validate structural coherence only; never authenticate external findings."""
    rows = tuple(attestations)
    if (
        timezone.is_naive(now)
        or snapshot.record_id != record.pk
        or snapshot.revision != record.revision
        or snapshot.recorded_by_id != record.initiator_id
        or len(rows) != 2
        or len({a.pk for a in rows}) != 2
        or {a.purpose for a in rows}
        != {"organization_eligibility", "representative_mandate"}
        or snapshot.classification not in ("registered", "unregistered")
        or not snapshot.organization_name.strip()
        or not snapshot.city.strip()
    ):
        raise PreflightConflict("Invalid preparation")
    handles = [snapshot.nomination_reference, snapshot.nominee_reference]
    for a in rows:
        if (
            a.snapshot_id != snapshot.pk
            or a.attestor_id != record.initiator_id
            or timezone.is_naive(a.examined_at)
            or a.examined_at > now
        ):
            raise PreflightConflict("Invalid preparation")
        handles.extend([a.evidence_reference, a.method_reference])
    if any(
        not isinstance(v, str)
        or re.fullmatch(r"[A-Z][A-Z0-9_-]{0,63}", v, re.ASCII) is None
        for v in handles
    ):
        raise PreflightConflict("Invalid preparation")
    proposal = preflight(
        state=record.state,
        revision=record.revision,
        expected_revision=expected_revision,
        command="submit",
        initiator=record.initiator_id,
        actor=actor_id,
        attestation_purposes=tuple(a.purpose for a in rows),
    )
    return PreparedSubmission(
        record.pk,
        snapshot.pk,
        record.revision,
        proposal.next_revision,
        tuple(a.pk for a in sorted(rows, key=lambda a: a.purpose)),
        snapshot.nominee_id is not None,
    )
