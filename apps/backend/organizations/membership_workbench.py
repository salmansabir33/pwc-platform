"""P4 immutable hypothetical projections, never membership writers or authority.

Revision equality here detects stale fixture inputs only. It is NOT DB locking,
idempotency, audit evidence, a trusted source or an executable commit protocol.
"""

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from uuid import UUID
from .member_import_preview import (
    MAX_ROWS,
    ERROR_CODES,
    WARNING_CODES,
    PreviewDiagnostic,
    preview_csv,
    valid_reference,
)
from .membership_preview import (
    STATES,
    CODES,
    MembershipSnapshotFixture,
    AdmissionRequestFixture,
    evaluate_admission,
    MembershipPreviewError,
)

MEMBER_STATES = ("active", "suspended", "ended")
ERRORS = CODES | frozenset(
    {
        "SOURCE_REVISION_CONFLICT",
        "UNKNOWN_MEMBER",
        "INVALID_MEMBER_TRANSITION",
        "UNCHANGED_CATEGORY",
    }
)


def _deny(code="INVALID_INPUT"):
    raise MembershipWorkbenchError(code) from None


class MembershipWorkbenchError(ValueError):
    def __init__(self, code="INVALID_INPUT"):
        if type(code) is not str or code not in ERRORS:
            raise ValueError("Unknown membership preparation diagnostic")
        super().__init__("Invalid membership preparation")
        self.code = code

    def to_diagnostic(self):
        return {"code": self.code}


def _positive(value):
    return type(value) is int and value > 0


@dataclass(frozen=True, slots=True, repr=False)
class MemberFixture:
    organization_id: UUID
    reference: str
    category_reference: str
    state: str = "active"
    revision: int = 1

    def __post_init__(self):
        if (
            type(self.organization_id) is not UUID
            or not self.organization_id.int
            or not valid_reference(self.reference)
            or not valid_reference(self.category_reference)
            or type(self.state) is not str
            or self.state not in MEMBER_STATES
            or not _positive(self.revision)
        ):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class HistoryFixture:
    revision: int
    kind: str
    from_state: str
    to_state: str
    category_changed: bool = False
    subject_reference: str = ""

    def __post_init__(self):
        if (
            not _positive(self.revision)
            or not valid_reference(self.subject_reference)
            or type(self.kind) is not str
            or self.kind not in ("admission", "status", "category")
            or type(self.from_state) is not str
            or type(self.to_state) is not str
            or type(self.category_changed) is not bool
        ):
            _deny()
        choices = STATES if self.kind == "admission" else MEMBER_STATES
        if (
            self.from_state not in choices
            or self.to_state not in choices
            or self.category_changed != (self.kind == "category")
        ):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class SourceRevision:
    digest: str

    def __post_init__(self):
        if (
            type(self.digest) is not str
            or len(self.digest) != 64
            or any(c not in "0123456789abcdef" for c in self.digest)
        ):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class MembershipFixture:
    policy: MembershipSnapshotFixture
    members: tuple[MemberFixture, ...] = ()
    history: tuple[HistoryFixture, ...] = ()

    def __post_init__(self):
        if (
            type(self.policy) is not MembershipSnapshotFixture
            or type(self.members) is not tuple
            or len(self.members) > MAX_ROWS
            or any(type(m) is not MemberFixture for m in self.members)
            or type(self.history) is not tuple
            or len(self.history) > 1000
            or any(
                type(h) is not HistoryFixture or h.revision != i
                for i, h in enumerate(self.history, 1)
            )
        ):
            _deny()
        if any(m.organization_id != self.policy.organization_id for m in self.members):
            _deny("TENANT_MISMATCH")
        references = tuple(m.reference for m in self.members)
        if len(set(references)) != len(references):
            _deny("DUPLICATE_REFERENCE")
        categories = {c.reference for c in self.policy.categories}
        if any(m.category_reference not in categories for m in self.members):
            _deny("UNKNOWN_CATEGORY")
        if any(m.revision > self.revision + 1 for m in self.members):
            _deny()
        # Validate member-vs-pending conflicts through the existing 05A rules.
        self.admission_policy()

    def history_for(self, reference):
        if not valid_reference(reference):
            _deny()
        return tuple(h for h in self.history if h.subject_reference == reference)

    @property
    def revision(self):
        return len(self.history)

    def source_revision(self):
        # Hash private values only in memory; NEVER publish this digest as identity
        # evidence or telemetry. Bind policy/tenant/content, not just a counter.
        encoded = json.dumps(
            asdict(self),
            default=lambda v: sorted(v) if isinstance(v, frozenset) else str(v),
            sort_keys=True,
        )
        return SourceRevision(hashlib.sha256(encoded.encode()).hexdigest())

    def admission_policy(self):
        try:
            return replace(
                self.policy,
                existing_references=self.policy.existing_references
                | frozenset(m.reference for m in self.members),
            )
        except MembershipPreviewError as error:
            _deny(error.code)

    def to_summary(self):
        return {
            "format": "pwc.membership-preparation.internal.v1",
            "non_authoritative": True,
            "commit_available": False,
            "revision": self.revision,
            "member_count": len(self.members),
            "states": {
                s: sum(m.state == s for m in self.members) for s in MEMBER_STATES
            },
            "history": [
                {
                    "revision": h.revision,
                    "kind": h.kind,
                    "from_state": h.from_state,
                    "to_state": h.to_state,
                    "category_changed": h.category_changed,
                }
                for h in self.history
            ],
        }


@dataclass(frozen=True, slots=True, repr=False)
class Projection:
    projected: MembershipFixture

    # This is an in-memory hypothetical fixture, NOT an action receipt.
    def __post_init__(self):
        if type(self.projected) is not MembershipFixture:
            _deny()

    def to_summary(self):
        return self.projected.to_summary()


def _source(source, expected):
    if type(source) is not MembershipFixture or type(expected) is not SourceRevision:
        _deny()
    if source.source_revision() != expected:
        _deny("SOURCE_REVISION_CONFLICT")
    if not source.policy.active:
        _deny("INACTIVE_POLICY")


def _project(source, *, policy=None, members=None, kind, before, after, reference):
    return Projection(
        MembershipFixture(
            source.policy if policy is None else policy,
            source.members if members is None else members,
            source.history
            + (
                HistoryFixture(
                    source.revision + 1,
                    kind,
                    before,
                    after,
                    kind == "category",
                    reference,
                ),
            ),
        )
    )


def preview_admission(source, expected, request, event):
    _source(source, expected)
    try:
        result = evaluate_admission(source.admission_policy(), request, event)
    except MembershipPreviewError as error:
        _deny(error.code)
    if not result.transition_valid:
        _deny(result.errors[0])
    if len(source.policy.requests) == MAX_ROWS and not any(
        r.request_reference == request.request_reference for r in source.policy.requests
    ):
        _deny()
    proposed = replace(request, state=result.proposed_state)
    requests = tuple(
        r
        for r in source.policy.requests
        if r.request_reference != request.request_reference
    ) + (proposed,)
    members = source.members
    if proposed.state == "accepted":
        members += (
            MemberFixture(
                source.policy.organization_id,
                proposed.record_reference,
                proposed.category_reference,
            ),
        )
    return _project(
        source,
        policy=replace(source.policy, requests=requests),
        members=members,
        kind="admission",
        before=request.state,
        after=proposed.state,
        reference=request.record_reference,
    )


def preview_member_change(source, expected, reference, *, state=None, category=None):
    _source(source, expected)
    if not valid_reference(reference) or (state is None) == (category is None):
        _deny()
    member = next((m for m in source.members if m.reference == reference), None)
    if member is None:
        _deny("UNKNOWN_MEMBER")
    if state is not None:
        if type(state) is not str or (member.state, state) not in (
            ("active", "suspended"),
            ("suspended", "active"),
            ("active", "ended"),
            ("suspended", "ended"),
        ):
            _deny("INVALID_MEMBER_TRANSITION")
        changed = replace(member, state=state, revision=member.revision + 1)
    else:
        if member.state == "ended":
            _deny("INVALID_MEMBER_TRANSITION")
        if not valid_reference(category):
            _deny()
        target = next(
            (c for c in source.policy.categories if c.reference == category), None
        )
        if target is None:
            _deny("UNKNOWN_CATEGORY")
        if not target.active:
            _deny("INACTIVE_CATEGORY")
        if category == member.category_reference:
            _deny("UNCHANGED_CATEGORY")
        changed = replace(
            member, category_reference=category, revision=member.revision + 1
        )
    return _project(
        source,
        members=tuple(changed if m == member else m for m in source.members),
        kind="status" if state is not None else "category",
        before=member.state,
        after=changed.state,
        reference=reference,
    )


@dataclass(frozen=True, slots=True)
class ImportPreparation:
    # Only codes, positions and counts: never CSV values or person references.
    rows: tuple[tuple[int, tuple[str, ...], tuple[str, ...]], ...]
    diagnostics: tuple[tuple[PreviewDiagnostic, ...], ...]

    def __post_init__(self):
        if type(self.rows) is not tuple or not 1 <= len(self.rows) <= MAX_ROWS:
            _deny()
        if (
            type(self.diagnostics) is not tuple
            or len(self.diagnostics) != len(self.rows)
            or any(
                type(ds) is not tuple
                or any(
                    type(d) is not PreviewDiagnostic or d.record != number for d in ds
                )
                for number, ds in enumerate(self.diagnostics, 2)
            )
        ):
            _deny()
        for number, row in enumerate(self.rows, 2):
            if (
                type(row) is not tuple
                or len(row) != 3
                or type(row[0]) is not int
                or row[0] != number
                or type(row[1]) is not tuple
                or type(row[2]) is not tuple
                or any(
                    type(c) is not str or c not in ERRORS | frozenset(ERROR_CODES)
                    for c in row[1]
                )
                or any(type(c) is not str or c not in WARNING_CODES for c in row[2])
            ):
                _deny()

    def to_summary(self):
        return {
            "non_authoritative": True,
            "commit_available": False,
            "row_count": len(self.rows),
            "candidate_count": sum(not errors for _, errors, _ in self.rows),
            "rows": [
                {
                    "record": n,
                    "errors": list(e),
                    "warnings": list(w),
                    "csv_diagnostics": [d.to_summary() for d in ds],
                }
                for (n, e, w), ds in zip(self.rows, self.diagnostics)
            ],
        }


def prepare_import(source, expected, raw):
    _source(source, expected)
    policy = source.admission_policy()
    report = preview_csv(
        raw, organization_id=policy.organization_id, catalog=policy.to_import_catalog()
    )
    rows = []
    for row in report.rows:
        errors = row.errors
        if not errors:
            reference, _, category = row.values
            request = AdmissionRequestFixture(
                policy.organization_id,
                f"IMPORT_R{row.number}",
                reference,
                category,
                "application",
            )
            result = evaluate_admission(policy, request, "apply")
            errors = result.errors
        rows.append((row.number, errors, row.warnings))
    return ImportPreparation(tuple(rows), tuple(row.diagnostics for row in report.rows))
