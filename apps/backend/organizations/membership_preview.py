"""05A internal, nonwriting membership preparation; NOT an authority service.

State/event vocabulary and conservative conflict rules are synthetic v1 proposals,
not approved live membership policy. No actors, grants, contacts, accounts, money,
DB access, executable commands or persistence adapters belong in this module.
"""

from dataclasses import dataclass
import unicodedata
from uuid import UUID
from types import MappingProxyType
from .member_import_preview import MAX_ROWS, PreviewCatalog, valid_reference

MODES = ("open", "approval", "invitation")
ROUTES = ("application", "invitation")
STATES = ("draft", "pending", "accepted", "declined", "cancelled")
EVENTS = ("apply", "invite", "approve", "accept", "decline", "cancel")
CODES = frozenset(
    {
        "INVALID_INPUT",
        "TENANT_MISMATCH",
        "DUPLICATE_CATEGORY_REFERENCE",
        "DUPLICATE_CATEGORY_LABEL",
        "DUPLICATE_REQUEST_REFERENCE",
        "DUPLICATE_REFERENCE",
        "UNKNOWN_CATEGORY",
        "INACTIVE_CATEGORY",
        "INACTIVE_POLICY",
        "UNSUPPORTED_EVENT",
        "MODE_ROUTE_CONFLICT",
        "INVALID_TRANSITION",
        "STALE_REQUEST",
        "UNKNOWN_REQUEST",
        "EXISTING_REFERENCE",
    }
)
# Deliberately incomplete outside these three synthetic paths. No rule is inferred
# for invitations under open/approval policy, renewal, expiry or reinstatement.
TRANSITIONS = MappingProxyType(
    {
        ("open", "application", "draft", "apply"): "accepted",
        ("approval", "application", "draft", "apply"): "pending",
        ("approval", "application", "pending", "approve"): "accepted",
        ("approval", "application", "pending", "decline"): "declined",
        ("approval", "application", "pending", "cancel"): "cancelled",
        ("invitation", "invitation", "draft", "invite"): "pending",
        ("invitation", "invitation", "pending", "accept"): "accepted",
        ("invitation", "invitation", "pending", "decline"): "declined",
        ("invitation", "invitation", "pending", "cancel"): "cancelled",
    }
)


class MembershipPreviewError(ValueError):
    def __init__(self, code="INVALID_INPUT"):
        if type(code) is not str or code not in CODES:
            raise ValueError("Unknown membership preview diagnostic")
        super().__init__("Invalid membership preview fixture")
        self.code = code

    def to_diagnostic(self):
        return {"code": self.code}


def _invalid(code="INVALID_INPUT"):
    raise MembershipPreviewError(code) from None


def _uuid(value):
    return type(value) is UUID and bool(value.int)


def _choice(value, choices):
    return type(value) is str and value in choices


@dataclass(frozen=True, slots=True, repr=False)
class CategoryFixture:
    organization_id: UUID
    reference: str
    label: str
    active: bool = True

    def __post_init__(self):
        if (
            not _uuid(self.organization_id)
            or not valid_reference(self.reference)
            or type(self.label) is not str
            or not self.label.strip()
            or len(self.label) > 250
            or any(unicodedata.category(c).startswith("C") for c in self.label)
            or type(self.active) is not bool
        ):
            _invalid()

    @property
    def normalized_label(self):
        return " ".join(unicodedata.normalize("NFKC", self.label).split()).casefold()


@dataclass(frozen=True, slots=True, repr=False)
class AdmissionRequestFixture:
    organization_id: UUID
    request_reference: str
    record_reference: str
    category_reference: str
    route: str
    state: str = "draft"

    def __post_init__(self):
        if (
            not _uuid(self.organization_id)
            or any(
                not valid_reference(v)
                for v in (
                    self.request_reference,
                    self.record_reference,
                    self.category_reference,
                )
            )
            or not _choice(self.route, ROUTES)
            or not _choice(self.state, STATES)
        ):
            _invalid()


@dataclass(frozen=True, slots=True, repr=False)
class MembershipSnapshotFixture:
    organization_id: UUID
    mode: str
    categories: tuple[CategoryFixture, ...]
    requests: tuple[AdmissionRequestFixture, ...] = ()
    existing_references: frozenset[str] = frozenset()
    active: bool = True

    def __post_init__(self):
        if (
            not _uuid(self.organization_id)
            or not _choice(self.mode, MODES)
            or type(self.active) is not bool
            or type(self.categories) is not tuple
            or not 1 <= len(self.categories) <= MAX_ROWS
            or any(type(c) is not CategoryFixture for c in self.categories)
            or type(self.requests) is not tuple
            or len(self.requests) > MAX_ROWS
            or any(type(r) is not AdmissionRequestFixture for r in self.requests)
            or type(self.existing_references) is not frozenset
            or len(self.existing_references) > MAX_ROWS
            or any(not valid_reference(v) for v in self.existing_references)
        ):
            _invalid()
        # Ownership precedes conflict checks: never project foreign catalog data.
        if any(
            v.organization_id != self.organization_id
            for v in self.categories + self.requests
        ):
            _invalid("TENANT_MISMATCH")
        references = tuple(c.reference for c in self.categories)
        labels = tuple(c.normalized_label for c in self.categories if c.active)
        if len(set(references)) != len(references):
            _invalid("DUPLICATE_CATEGORY_REFERENCE")
        if len(set(labels)) != len(labels):
            _invalid("DUPLICATE_CATEGORY_LABEL")
        request_references = tuple(r.request_reference for r in self.requests)
        if len(set(request_references)) != len(request_references):
            _invalid("DUPLICATE_REQUEST_REFERENCE")
        if any(r.category_reference not in references for r in self.requests):
            _invalid("UNKNOWN_CATEGORY")
        current = tuple(
            r.record_reference
            for r in self.requests
            if r.state in ("pending", "accepted")
        )
        if len(set(current)) != len(current) or any(
            r.record_reference in self.existing_references
            for r in self.requests
            if r.state == "pending"
        ):
            _invalid("DUPLICATE_REFERENCE")

    def to_import_catalog(self):
        """05B shape adapter only. Caller fixtures are never a trusted live source.

        Pending requests are not members. The admission evaluator, not CSV
        structural acceptance, checks pending conflicts and admission mode.
        """
        return PreviewCatalog(
            self.organization_id,
            frozenset(c.reference for c in self.categories if self.active and c.active),
            self.existing_references
            | frozenset(
                r.record_reference for r in self.requests if r.state == "accepted"
            ),
        )


@dataclass(frozen=True, slots=True)
class AdmissionPreview:
    organization_id: UUID
    proposed_state: str | None
    errors: tuple[str, ...] = ()

    def __post_init__(self):
        if (
            not _uuid(self.organization_id)
            or type(self.errors) is not tuple
            or any(not _choice(c, CODES) for c in self.errors)
            or len(set(self.errors)) != len(self.errors)
            or bool(self.errors) != (self.proposed_state is None)
            or self.proposed_state is not None
            and not _choice(self.proposed_state, STATES[1:])
        ):
            _invalid()

    @property
    def transition_valid(self):
        return not self.errors

    def to_summary(self):
        return {
            "format": "pwc.membership-admission-preview.internal.v1",
            "organization_id": str(self.organization_id),
            "non_authoritative": True,
            "commit_available": False,
            "transition_valid": self.transition_valid,
            "proposed_state": self.proposed_state,
            "errors": list(self.errors),
        }


def evaluate_admission(snapshot, request, event):
    """Return only a hypothetical transition, never apply it or authorize an actor.

    Fail closed at the first deterministic conflict. Existing pending requests
    must exactly match the snapshot before a terminal decision can be proposed.
    Duplicate protection is conservatively per NGO/person-handle in this fixture,
    not a claim that live category/identity resolution policy has been accepted.
    """
    if (
        type(snapshot) is not MembershipSnapshotFixture
        or type(request) is not AdmissionRequestFixture
    ):
        _invalid()

    def reject(code):
        return AdmissionPreview(snapshot.organization_id, None, (code,))

    if snapshot.organization_id != request.organization_id:
        return reject("TENANT_MISMATCH")
    if not _choice(event, EVENTS):
        return reject("UNSUPPORTED_EVENT")
    if not snapshot.active:
        return reject("INACTIVE_POLICY")
    current = next(
        (
            r
            for r in snapshot.requests
            if r.request_reference == request.request_reference
        ),
        None,
    )
    if current is not None and current != request:
        return reject("STALE_REQUEST")
    if current is None and request.state != "draft":
        return reject("UNKNOWN_REQUEST")
    category = next(
        (c for c in snapshot.categories if c.reference == request.category_reference),
        None,
    )
    if category is None:
        return reject("UNKNOWN_CATEGORY")
    if not category.active:
        return reject("INACTIVE_CATEGORY")
    if (snapshot.mode, request.route) not in (
        ("open", "application"),
        ("approval", "application"),
        ("invitation", "invitation"),
    ):
        return reject("MODE_ROUTE_CONFLICT")
    target = TRANSITIONS.get((snapshot.mode, request.route, request.state, event))
    if target is None:
        return reject("INVALID_TRANSITION")
    if request.record_reference in snapshot.existing_references:
        return reject("EXISTING_REFERENCE")
    if any(
        r.request_reference != request.request_reference
        and r.record_reference == request.record_reference
        and r.state in ("pending", "accepted")
        for r in snapshot.requests
    ):
        return reject("DUPLICATE_REFERENCE")
    return AdmissionPreview(snapshot.organization_id, target)
