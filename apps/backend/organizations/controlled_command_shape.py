"""Non-authoritative command-shape preparation; never an executable contract.

The four names are PR31 review vocabulary, NOT installed permission atoms. No
actor, credential, proof, capability, expiry or idempotency policy is accepted
here. No database access, digest/signature, transition, dispatch or feature flag.
A structurally valid candidate confers no authority, including in fixture tests.
"""

from dataclasses import dataclass
import json
from types import MappingProxyType
from uuid import UUID

SHAPE_ACTIONS = MappingProxyType(
    {
        "ngo.onboard.submit.v1": "submit",
        "ngo.onboard.review.approve.v1": "approve",
        "ngo.onboard.review.reject.v1": "reject",
        "ngo.onboard.review.return.v1": "return",
    }
)
MAX_BYTES = 1024
# Leave room for the existing structural preflight's next revision in PostgreSQL.
MAX_SOURCE_REVISION = 2**63 - 2
FIELDS = frozenset(
    ("command", "record_id", "snapshot_id", "organization_id", "expected_revision")
)


class CommandShapeError(ValueError):
    """Value-free failure; never return request content in errors."""


def invalid(*_):
    raise CommandShapeError("Invalid controlled command shape") from None


def _uuid(value):
    if type(value) is not str:
        invalid()
    try:
        parsed = UUID(value)
    except ValueError:
        invalid()
    if parsed.int == 0 or str(parsed) != value:
        invalid()
    return parsed


@dataclass(frozen=True, slots=True, repr=False)
class CommandShape:
    command: str
    record_id: UUID
    snapshot_id: UUID
    organization_id: UUID | None
    expected_revision: int

    def __post_init__(self):
        if type(self.command) is not str or self.command not in SHAPE_ACTIONS:
            invalid()
        for value in (self.record_id, self.snapshot_id):
            if type(value) is not UUID or not value.int:
                invalid()
        if self.organization_id is not None and (
            type(self.organization_id) is not UUID or not self.organization_id.int
        ):
            invalid()
        if (
            type(self.expected_revision) is not int
            or not 1 <= self.expected_revision <= MAX_SOURCE_REVISION
        ):
            invalid()

    @property
    def executable(self):
        return False

    def __repr__(self):
        return "<CommandShape non-authoritative>"


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            invalid()
        result[key] = value
    return result


def parse_shape(raw):
    """Strict bounded syntax only. Do NOT attach this parser to a live endpoint."""
    if type(raw) is not bytes or len(raw) > MAX_BYTES:
        invalid()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique,
            parse_float=invalid,
            parse_constant=invalid,
        )
    except (ValueError, UnicodeError, RecursionError):
        invalid()
    if type(value) is not dict or set(value) != FIELDS:
        invalid()
    return CommandShape(
        command=value["command"],
        record_id=_uuid(value["record_id"]),
        snapshot_id=_uuid(value["snapshot_id"]),
        organization_id=(
            None
            if value["organization_id"] is None
            else _uuid(value["organization_id"])
        ),
        expected_revision=value["expected_revision"],
    )


def check_source_shape(candidate, *, record, snapshot):
    """Compare caller-supplied structural records, NOT authenticate their source.

    No lookup or mutation occurs. The caller's records may themselves be fake;
    success is deliberately None, not an authorization or a transition proposal.
    Missing/mismatched tenant/source/revision all share the same redacted failure.
    """
    if type(candidate) is not CommandShape:
        invalid()
    try:
        # Reuse the same UUID/revision validation for supplied source fields;
        # equality alone could accept a non-UUID object with permissive __eq__.
        source = CommandShape(
            command=candidate.command,
            record_id=record.pk,
            snapshot_id=snapshot.pk,
            organization_id=record.organization_id,
            expected_revision=record.revision,
        )
        snapshot_record_id = snapshot.record_id
        snapshot_revision = snapshot.revision
    except AttributeError:
        invalid()
    if (
        candidate != source
        or type(snapshot_record_id) is not UUID
        or snapshot_record_id != source.record_id
        or type(snapshot_revision) is not int
        or snapshot_revision != source.expected_revision
    ):
        invalid()
