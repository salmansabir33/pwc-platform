"""C1-R01–R08 proposed rules, immutable fixtures ONLY; no authority or persistence.

The effective time is a supplied simulation clock, never evidence of DB time.
Source hashes detect stale fixture inputs, not authorization, locks or receipts.
"""

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from uuid import UUID
from .member_import_preview import MAX_ROWS
from .membership_preview import (
    CategoryFixture,
    MembershipSnapshotFixture,
    MembershipPreviewError,
    MODES,
    CODES,
)
from .membership_workbench import SourceRevision

ERRORS = CODES | frozenset(
    {
        "SOURCE_REVISION_CONFLICT",
        "POLICY_REVISION_CONFLICT",
        "CATEGORY_REVISION_CONFLICT",
        "DUPLICATE_CATEGORY_ID",
        "UNCHANGED_CATEGORY",
        "UNCHANGED_POLICY",
        "INVALID_EFFECTIVE_TIME",
    }
)


class CategoryPolicyPreviewError(ValueError):
    def __init__(self, code="INVALID_INPUT"):
        if type(code) is not str or code not in ERRORS:
            raise ValueError("Unknown category preparation diagnostic")
        super().__init__("Invalid category/policy preparation")
        self.code = code

    def to_diagnostic(self):
        return {"code": self.code}


def _deny(code="INVALID_INPUT"):
    raise CategoryPolicyPreviewError(code) from None


def _uuid(value):
    return type(value) is UUID and bool(value.int)


def _revision(value):
    return type(value) is int and value > 0


def _clock(value):
    return type(value) is datetime and value.tzinfo is timezone.utc


@dataclass(frozen=True, slots=True, repr=False)
class CategoryVersionFixture:
    id: UUID
    definition: CategoryFixture
    revision: int = 1

    def __post_init__(self):
        if (
            not _uuid(self.id)
            or type(self.definition) is not CategoryFixture
            or not _revision(self.revision)
        ):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class PolicyVersionFixture:
    organization_id: UUID
    revision: int
    mode: str
    categories: tuple[CategoryVersionFixture, ...]
    effective_at: datetime
    operation: str = "initial"

    def __post_init__(self):
        if (
            not _uuid(self.organization_id)
            or not _revision(self.revision)
            or type(self.mode) is not str
            or self.mode not in MODES
            or type(self.categories) is not tuple
            or len(self.categories) > MAX_ROWS
            or any(type(c) is not CategoryVersionFixture for c in self.categories)
            or not _clock(self.effective_at)
            or type(self.operation) is not str
            or self.operation
            not in (
                "initial",
                "category_created",
                "category_updated",
                "category_deactivated",
                "mode_changed",
            )
        ):
            _deny()
        if len({c.id for c in self.categories}) != len(self.categories):
            _deny("DUPLICATE_CATEGORY_ID")
        if self.categories:
            try:
                # Reuse 05A tenant, reference and normalized active-label validation.
                MembershipSnapshotFixture(
                    self.organization_id,
                    self.mode,
                    tuple(c.definition for c in self.categories),
                )
            except MembershipPreviewError as error:
                _deny(error.code)


@dataclass(frozen=True, slots=True, repr=False)
class PendingPolicyFixture:
    # No subject identity/contact needed to demonstrate version pinning.
    category_id: UUID
    policy_revision: int

    def __post_init__(self):
        if not _uuid(self.category_id) or not _revision(self.policy_revision):
            _deny()


@dataclass(frozen=True, slots=True, repr=False)
class CategoryPolicyFixture:
    versions: tuple[PolicyVersionFixture, ...]
    pending: tuple[PendingPolicyFixture, ...] = ()

    def __post_init__(self):
        if (
            type(self.versions) is not tuple
            or not 1 <= len(self.versions) <= 200
            or any(
                type(v) is not PolicyVersionFixture or v.revision != i
                for i, v in enumerate(self.versions, 1)
            )
            or type(self.pending) is not tuple
            or len(self.pending) > MAX_ROWS
            or any(type(p) is not PendingPolicyFixture for p in self.pending)
        ):
            _deny()
        first = self.versions[0]
        if first.operation != "initial" or any(
            c.revision != 1 for c in first.categories
        ):
            _deny()
        for before, after in zip(self.versions, self.versions[1:]):
            if before.organization_id != after.organization_id:
                _deny("TENANT_MISMATCH")
            if after.effective_at < before.effective_at:
                _deny("INVALID_EFFECTIVE_TIME")
            old = {c.id: c for c in before.categories}
            new = {c.id: c for c in after.categories}
            if not old.keys() <= new.keys():
                _deny()  # No deletion, reference reuse or category UUID substitution.
            for id, c in new.items():
                previous = old.get(id)
                if previous is None:
                    if c.revision != 1:
                        _deny()
                elif (
                    previous.definition.reference != c.definition.reference
                    or (c != previous and c.revision != previous.revision + 1)
                    or c != previous
                    and not previous.definition.active
                ):
                    _deny()
            changed = [id for id in old if old[id] != new[id]]
            added = new.keys() - old.keys()
            if after.operation == "mode_changed":
                if changed or added or before.mode == after.mode:
                    _deny()
            elif before.mode != after.mode:
                _deny()
            elif after.operation == "category_created":
                if (
                    changed
                    or len(added) != 1
                    or not new[next(iter(added))].definition.active
                ):
                    _deny()
            elif after.operation in ("category_updated", "category_deactivated"):
                if added or len(changed) != 1:
                    _deny()
                old_c, new_c = old[changed[0]], new[changed[0]]
                if after.operation == "category_updated":
                    if (
                        old_c.definition.label == new_c.definition.label
                        or not new_c.definition.active
                    ):
                        _deny()
                elif (
                    new_c.definition.active
                    or old_c.definition.label != new_c.definition.label
                ):
                    _deny()
            else:
                _deny()
        for p in self.pending:
            if p.policy_revision > self.current.revision or p.category_id not in {
                c.id
                for c in self.versions[p.policy_revision - 1].categories
                if c.definition.active
            }:
                _deny()

    @property
    def current(self):
        return self.versions[-1]

    def source_revision(self):
        raw = json.dumps(asdict(self), sort_keys=True, default=str)
        return SourceRevision(hashlib.sha256(raw.encode()).hexdigest())

    def to_summary(self):
        return {
            "format": "pwc.category-policy-preview.internal.v1",
            "non_authoritative": True,
            "commit_available": False,
            "policy_revision": self.current.revision,
            "category_count": len(self.current.categories),
            "active_category_count": sum(
                c.definition.active for c in self.current.categories
            ),
            "pending_review_count": sum(
                p.policy_revision != self.current.revision for p in self.pending
            ),
            "policy_history": [
                {
                    "revision": v.revision,
                    "operation": v.operation,
                    "mode": v.mode,
                    "active_category_count": sum(
                        c.definition.active for c in v.categories
                    ),
                }
                for v in self.versions
            ],
        }


def _source(source, expected, revision, at):
    if (
        type(source) is not CategoryPolicyFixture
        or type(expected) is not SourceRevision
    ):
        _deny()
    if source.source_revision() != expected:
        _deny("SOURCE_REVISION_CONFLICT")
    if not _revision(revision) or revision != source.current.revision:
        _deny("POLICY_REVISION_CONFLICT")
    if not _clock(at) or at < source.current.effective_at:
        _deny("INVALID_EFFECTIVE_TIME")


def _propose(source, at, operation, *, categories=None, mode=None):
    version = PolicyVersionFixture(
        source.current.organization_id,
        source.current.revision + 1,
        source.current.mode if mode is None else mode,
        source.current.categories if categories is None else categories,
        at,
        operation,
    )
    return CategoryPolicyFixture(source.versions + (version,), source.pending)


def preview_create_category(source, expected, policy_revision, definition, id, *, at):
    _source(source, expected, policy_revision, at)
    if type(definition) is not CategoryFixture or not _uuid(id):
        _deny()
    if definition.organization_id != source.current.organization_id:
        _deny("TENANT_MISMATCH")
    if any(c.id == id for c in source.current.categories):
        _deny("DUPLICATE_CATEGORY_ID")
    if not definition.active:
        _deny("INACTIVE_CATEGORY")
    return _propose(
        source,
        at,
        "category_created",
        categories=source.current.categories
        + (CategoryVersionFixture(id, definition),),
    )


def preview_change_category(
    source,
    expected,
    policy_revision,
    id,
    category_revision,
    *,
    at,
    label=None,
    deactivate=False,
):
    _source(source, expected, policy_revision, at)
    if not _uuid(id) or type(deactivate) is not bool or (label is None) != deactivate:
        _deny()
    category = next((c for c in source.current.categories if c.id == id), None)
    if category is None:
        _deny("UNKNOWN_CATEGORY")
    if not _revision(category_revision) or category_revision != category.revision:
        _deny("CATEGORY_REVISION_CONFLICT")
    if not category.definition.active:
        _deny("INACTIVE_CATEGORY")
    try:
        definition = (
            replace(category.definition, active=False)
            if deactivate
            else replace(category.definition, label=label)
        )
    except MembershipPreviewError as error:
        _deny(error.code)
    if definition == category.definition:
        _deny("UNCHANGED_CATEGORY")
    changed = replace(category, definition=definition, revision=category.revision + 1)
    return _propose(
        source,
        at,
        "category_deactivated" if deactivate else "category_updated",
        categories=tuple(
            changed if c.id == id else c for c in source.current.categories
        ),
    )


def preview_change_mode(source, expected, policy_revision, mode, *, at):
    _source(source, expected, policy_revision, at)
    if type(mode) is not str or mode not in MODES:
        _deny()
    if mode == source.current.mode:
        _deny("UNCHANGED_POLICY")
    return _propose(source, at, "mode_changed", mode=mode)
