"""04A claimant-only service. Caller holds live User/session locks for its transaction.

No access/grant/mandate/reviewer models are written here. Public matching cannot
query hidden organizations or other applicants' drafts, even for collisions.
"""

import hashlib
import json
import uuid
from django.core import signing
from .models import (
    Organization,
    OrganizationWorkspace,
    OrganizationDraft,
    OrganizationClaim,
    RegistryEvent,
    RegistryReceipt,
)
from .registry_serializers import DraftOutput, ClaimOutput, normalize
from accounts.flow_security import FlowProblem

PAGE_SIZE = 20


def fail(code="STATE_CONFLICT", status=409):
    raise FlowProblem(code, status)


def digest(data):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def match_key(data):
    return digest({k: normalize(data[k]) for k in ("name", "city", "jurisdiction")})


def public():
    # Deliberately the EXISTING four-field verified-only public projection.
    return Organization.objects.filter(
        workspace__state=OrganizationWorkspace.State.VERIFIED
    )


def matches(query, city=""):
    values = public().filter(lookup_name__contains=normalize(query))
    if city:
        values = values.filter(lookup_city__contains=normalize(city))
    return values


def page(queryset, params, user, kind, output=None):
    cursor = params.get("cursor")
    if cursor:
        try:
            token = signing.loads(cursor, salt="pwc.registry.page.v1", max_age=3600)
            if token["owner"] != str(user.pk) or token["kind"] != kind:
                raise ValueError()
            queryset = queryset.filter(id__gt=uuid.UUID(token["after"]))
        except (signing.BadSignature, ValueError, KeyError, TypeError):
            fail("VALIDATION_ERROR", 400)
    values = list(queryset.order_by("id")[: PAGE_SIZE + 1])
    more = len(values) > PAGE_SIZE
    values = values[:PAGE_SIZE]
    cursor = (
        signing.dumps(
            {"owner": str(user.pk), "kind": kind, "after": str(values[-1].pk)},
            salt="pwc.registry.page.v1",
        )
        if more
        else None
    )
    output = output or (DraftOutput if kind == "draft" else ClaimOutput)
    return {"results": output(values, many=True).data, "next_cursor": cursor}


def own(model, user, pk):
    value = model.objects.select_for_update().filter(claimant=user, pk=pk).first()
    if not value:
        fail("NOT_FOUND", 404)
    return value


def audit(value, user, session, action):
    RegistryEvent.objects.create(
        actor=user,
        session=session,
        action=action,
        revision=value.revision,
        **(
            {"draft": value}
            if isinstance(value, OrganizationDraft)
            else {"claim": value}
        ),
    )


def create(kind, data, key, user, session):
    receipt = RegistryReceipt.objects.filter(claimant=user, key=key).first()
    fingerprint = digest(data)
    model, output = (
        (OrganizationDraft, DraftOutput)
        if kind == "draft"
        else (OrganizationClaim, ClaimOutput)
    )
    if receipt:
        if receipt.operation != kind or receipt.digest != fingerprint:
            fail()
        # Return CURRENT own state, never resurrect an old pending state on retry.
        return output(own(model, user, receipt.resource_id)).data
    if kind == "draft":
        identity = match_key(data)
        if model.objects.filter(
            claimant=user, match_key=identity, state__in=["draft", "submitted"]
        ).exists():
            fail()
        org = Organization.objects.create(
            name=data["name"], city=data["city"], classification=data["classification"]
        )
        OrganizationWorkspace.objects.create(organization=org)
        value = model.objects.create(
            organization=org, claimant=user, match_key=identity, **data
        )
    else:
        # Hidden, nonexistent, provisional and restricted targets are indistinguishable.
        org = public().filter(pk=data["organization_id"]).first()
        if org is None:
            fail("NOT_FOUND", 404)
        if model.objects.filter(
            claimant=user, organization=org, state__in=["pending", "needs_information"]
        ).exists():
            fail()
        value = model.objects.create(organization=org, claimant=user)
    audit(value, user, session, "created")
    RegistryReceipt.objects.create(
        claimant=user, key=key, operation=kind, digest=fingerprint, resource_id=value.pk
    )
    return output(value).data


def change(kind, pk, command, data, user, session):
    model, output = (
        (OrganizationDraft, DraftOutput)
        if kind == "draft"
        else (OrganizationClaim, ClaimOutput)
    )
    value = own(model, user, pk)
    if value.revision != data.pop("revision"):
        fail()
    if command == "edit" and kind == "draft" and value.state == "draft":
        identity = match_key(data)
        if (
            model.objects.filter(
                claimant=user, match_key=identity, state__in=["draft", "submitted"]
            )
            .exclude(pk=pk)
            .exists()
        ):
            fail()
        for field, item in data.items():
            setattr(value, field, item)
        value.match_key = identity
        # Only this application's private provisional identity may change.
        updated = Organization.objects.filter(
            pk=value.organization_id, workspace__state="provisional"
        ).update(
            name=value.name,
            city=value.city,
            classification=value.classification,
            lookup_name=normalize(value.name),
            lookup_city=normalize(value.city),
        )
        if updated != 1:
            fail()
    elif command == "submit" and kind == "draft" and value.state == "draft":
        value.state = "submitted"
    elif command == "withdraw" and value.state in (
        ["draft", "submitted"] if kind == "draft" else ["pending", "needs_information"]
    ):
        value.state = "withdrawn"
    else:
        fail()
    value.revision += 1
    value.save()
    audit(value, user, session, command)
    return output(value).data
