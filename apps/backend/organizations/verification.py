"""04B synthetic case preparation. No evidence storage or reviewer authority writer."""

from . import registry
from .models import (
    OrganizationDraft,
    OrganizationClaim,
    VerificationCase,
    EvidencePreparation,
    VerificationEvent,
    VerificationReceipt,
)
from .verification_serializers import CaseOutput, PreparationOutput


def own(user, pk):
    return registry.own(VerificationCase, user, pk)


def source(case, user):
    model = OrganizationDraft if case.draft_id else OrganizationClaim
    record = registry.own(model, user, case.draft_id or case.claim_id)
    if record.organization_id != case.organization_id:
        registry.fail()
    return record


def live_source(case, user):
    record = source(case, user)
    if record.revision != case.source_revision or record.state not in (
        "draft",
        "submitted",
        "pending",
        "needs_information",
    ):
        registry.fail()
    return record


def event(case, user, session, reason, preparation=None):
    VerificationEvent.objects.create(
        case=case,
        actor=user,
        session=session,
        reason_code=reason,
        revision=case.revision,
        preparation=preparation,
        preparation_revision=preparation.revision if preparation else None,
        prepared_offline=preparation.prepared_offline if preparation else None,
    )


def receipt(user, key, operation, data):
    old = VerificationReceipt.objects.filter(claimant=user, key=key).first()
    if old and (old.operation != operation or old.digest != registry.digest(data)):
        registry.fail()
    return old


def create(user, session, data, key):
    old = receipt(user, key, "case", data)
    if old:
        return CaseOutput(own(user, old.case_id)).data
    model = OrganizationDraft if data["source_kind"] == "draft" else OrganizationClaim
    record = registry.own(model, user, data["source_id"])
    if record.revision != data["source_revision"] or record.state not in (
        "draft",
        "submitted",
        "pending",
        "needs_information",
    ):
        registry.fail()
    link = {data["source_kind"]: record}
    if VerificationCase.objects.filter(
        claimant=user, purpose=data["purpose"], state__in=["draft", "submitted"], **link
    ).exists():
        registry.fail()
    # Claim targets disclose only their already public category, not private notes.
    if isinstance(record, OrganizationDraft):
        category = record.classification
    else:
        target = registry.public().filter(pk=record.organization_id).first()
        if target is None:
            registry.fail()
        category = target.classification
    case = VerificationCase.objects.create(
        claimant=user,
        organization_id=record.organization_id,
        source_revision=record.revision,
        purpose=data["purpose"],
        track=category,
        **link,
    )
    event(case, user, session, "applicant_created")
    VerificationReceipt.objects.create(
        claimant=user,
        key=key,
        operation="case",
        digest=registry.digest(data),
        case=case,
    )
    return CaseOutput(case).data


def transition(user, session, pk, command, data):
    case = own(user, pk)
    if case.revision != data["revision"]:
        registry.fail()
    if command == "submit" and case.state == "draft":
        live_source(case, user)
        case.state = "submitted"
        reason = "preparation_submitted"
    elif command == "withdraw" and case.state in ("draft", "submitted"):
        # Withdrawal remains possible after the source changes or is withdrawn.
        case.state = "withdrawn"
        reason = "applicant_withdrawn"
    else:
        registry.fail()
    case.revision += 1
    case.save()
    event(case, user, session, reason)
    return CaseOutput(case).data


def prepare(user, session, pk, data, *, key=None, item_id=None, withdraw=False):
    case = own(user, pk)
    if key:
        old = receipt(user, key, "preparation", dict(data, case_id=str(pk)))
        if old:
            if old.case_id != case.pk:
                registry.fail()
            return PreparationOutput(
                EvidencePreparation.objects.get(pk=old.preparation_id, case=case)
            ).data
    if case.revision != data["case_revision"] or case.state != "draft":
        registry.fail()
    live_source(case, user)
    if item_id is not None:
        item = (
            EvidencePreparation.objects.select_for_update()
            .filter(case=case, pk=item_id)
            .first()
        )
        if item is None:
            registry.fail("NOT_FOUND", 404)
        if item.revision != data["revision"] or item.state != "planned":
            registry.fail()
        item.prepared_offline = data["prepared_offline"]
        item.state = "withdrawn" if withdraw else "planned"
        item.revision += 1
        item.save()
        reason = "preparation_withdrawn" if withdraw else "preparation_replaced"
    else:
        if EvidencePreparation.objects.filter(case=case, state="planned").exists():
            registry.fail()
        item = EvidencePreparation.objects.create(
            case=case, prepared_offline=data["prepared_offline"]
        )
        reason = "preparation_added"
    case.revision += 1
    case.save()
    event(case, user, session, reason, item)
    if key:
        VerificationReceipt.objects.create(
            claimant=user,
            key=key,
            operation="preparation",
            digest=registry.digest(dict(data, case_id=str(pk))),
            case=case,
            preparation=item,
        )
    return PreparationOutput(item).data


def requirements(case):
    return {
        "case_id": str(case.pk),
        "purpose": case.purpose,
        "track": case.track,
        "rubric_status": "unapproved",
        "accepted_evidence_classes": [],
        "file_intake_available": False,
        "review_available": False,
        "submission_effect": "preparation_record_only",
    }
