"""Nonwriting 08C-B proposals; NEVER authorization, approval or persistence.

Tenant IDs constrain the snapshot query, not the caller's authority. There is no
HTTP adapter, grant evaluator, writer/apply method, public preview or activation
flag. Proposals are untrusted simulations and must not become future receipts.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from django.core.exceptions import ValidationError
from django.utils.timezone import is_aware
from rest_framework import serializers
from organizations.registry_serializers import ClosedSerializer, Text, normalize
from .models import Opportunity


class PreparationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__("Opportunity preparation rejected")


def _deny(code):
    raise PreparationError(code) from None


def _identifier(value):
    if type(value) is not UUID or not value.int:
        _deny("INVALID_IDENTIFIER")
    return value


class _DraftFields(ClosedSerializer):
    # Reuse model choices/limits and the existing bounded, strict text normalizer.
    type = serializers.ChoiceField(choices=Opportunity.Type.choices)
    title = Text(max_length=Opportunity._meta.get_field("title").max_length)
    summary = Text(
        max_length=Opportunity._meta.get_field("summary").max_length,
        allow_blank=True,
        default="",
    )


@dataclass(frozen=True, slots=True, repr=False)
class OpportunityProposal:
    operation: str
    organization_id: UUID
    opportunity_id: UUID | None
    source_state: str | None
    proposed_state: str
    type: str
    title: str
    summary: str
    lookup_title: str
    published_at: datetime | None
    withdrawn_at: datetime | None

    @property
    def live_execution_available(self):
        return False

    def __repr__(self):
        return "OpportunityProposal(<nonwriting; content redacted>)"


def _source(organization_id, opportunity_id):
    _identifier(opportunity_id)
    # Ownership is checked in SQL before inspecting content or lifecycle state.
    row = Opportunity.objects.filter(
        organization_id=organization_id, pk=opportunity_id
    ).first()
    if row is None:
        _deny("SOURCE_UNAVAILABLE")
    return row


def _lookup(title):
    try:
        return normalize(title)
    except serializers.ValidationError:
        _deny("INVALID_FIELDS")


def _validate(candidate):
    try:
        fields = _DraftFields(
            data={key: getattr(candidate, key) for key in ("type", "title", "summary")}
        )
        fields.is_valid(raise_exception=True)
        # Reuse field limits, choices, FK existence and lifecycle/date constraints.
        # No save/full_clean on the caller's object, and no speculative DB writes.
        candidate.full_clean(
            exclude=("created_at", "updated_at"), validate_unique=False
        )
    except (ValidationError, serializers.ValidationError, ValueError):
        _deny("INVALID_FIELDS")


def _proposal(operation, source, candidate):
    return OpportunityProposal(
        operation=operation,
        organization_id=candidate.organization_id,
        opportunity_id=source.pk if source else None,
        source_state=source.state if source else None,
        proposed_state=candidate.state,
        type=candidate.type,
        title=candidate.title,
        summary=candidate.summary,
        lookup_title=candidate.lookup_title,
        published_at=candidate.published_at,
        withdrawn_at=candidate.withdrawn_at,
    )


def prepare_draft(organization_id, payload, *, opportunity_id=None):
    """Validate a new or partial existing draft; return data, never a saved model."""
    _identifier(organization_id)
    source = (
        _source(organization_id, opportunity_id) if opportunity_id is not None else None
    )
    if source is not None and source.state != Opportunity.State.DRAFT:
        _deny("INVALID_TRANSITION")
    if (
        type(payload) is not dict
        or not payload
        or len(payload) > len(_DraftFields().fields)
    ):
        _deny("INVALID_FIELDS")
    fields = _DraftFields(data=payload, partial=source is not None)
    try:
        fields.is_valid(raise_exception=True)
    except (serializers.ValidationError, ValueError):
        _deny("INVALID_FIELDS")
    values = (
        {key: getattr(source, key) for key in ("type", "title", "summary")}
        if source
        else {}
    )
    values.update(fields.validated_data)
    candidate = Opportunity(organization_id=organization_id, **values)
    candidate.lookup_title = _lookup(candidate.title)
    _validate(candidate)
    return _proposal("prepare_draft", source, candidate)


def propose_transition(organization_id, opportunity_id, operation, *, effective_at):
    """Propose a request-publication/withdrawal outcome, not execute either.

    A publication request is NOT approval. Its desired PUBLISHED state and supplied
    timestamp are simulation data only. Published-content edits are unsupported.
    """
    _identifier(organization_id)
    if type(operation) is not str or operation not in {
        "request_publication",
        "withdraw",
    }:
        _deny("INVALID_OPERATION")
    source = _source(organization_id, opportunity_id)
    transitions = {
        "request_publication": (Opportunity.State.DRAFT, Opportunity.State.PUBLISHED),
        "withdraw": (Opportunity.State.PUBLISHED, Opportunity.State.WITHDRAWN),
    }
    before, after = transitions[operation]
    if source.state != before:
        _deny("INVALID_TRANSITION")
    if type(effective_at) is not datetime or not is_aware(effective_at):
        _deny("INVALID_EFFECTIVE_TIME")
    _validate(source)
    candidate = Opportunity(
        organization_id=source.organization_id,
        type=source.type,
        title=source.title,
        summary=source.summary,
        lookup_title=_lookup(source.title),
        state=after,
        published_at=effective_at.astimezone(timezone.utc)
        if operation == "request_publication"
        else source.published_at,
        withdrawn_at=effective_at.astimezone(timezone.utc)
        if operation == "withdraw"
        else None,
    )
    _validate(candidate)
    return _proposal(operation, source, candidate)
