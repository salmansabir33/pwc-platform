"""04A additive offline annotations; implemented routes only, no review authority."""

from copy import deepcopy
from contracts.schema import obj, arr, ref, operation, S, UUID, DATE, enum


def definitions():
    fields = {
        "name": {"type": "string", "minLength": 1, "maxLength": 250},
        "legal_name": dict(S, maxLength=250),
        "aliases": {
            "type": "array",
            "maxItems": 5,
            "items": dict(S, minLength=1, maxLength=250),
        },
        "city": dict(S, maxLength=100),
        "jurisdiction": dict(S, maxLength=100),
        "classification": enum("registered", "unregistered"),
        "contact_email": dict(S, maxLength=254),
        "contact_phone": dict(S, maxLength=40),
    }
    revision = {"type": "integer", "minimum": 1, "maximum": 9223372036854775807}
    common = {
        "id": UUID,
        "organization_id": UUID,
        "revision": revision,
        "created_at": DATE,
        "updated_at": DATE,
    }
    result = {
        "RegistryDraftInput": obj(
            fields,
            optional=(
                "legal_name",
                "aliases",
                "city",
                "jurisdiction",
                "contact_email",
                "contact_phone",
            ),
        ),
        "RegistryDraftEdit": obj(
            dict(fields, revision=revision),
            optional=(
                "legal_name",
                "aliases",
                "city",
                "jurisdiction",
                "contact_email",
                "contact_phone",
            ),
        ),
        "RegistryRevision": obj({"revision": revision}),
        "RegistryClaimInput": obj({"organization_id": UUID}),
        "RegistryDraft": obj(
            dict(fields, **common, state=enum("draft", "submitted", "withdrawn"))
        ),
        "RegistryClaim": obj(
            dict(
                common,
                state=enum("pending", "needs_information", "rejected", "withdrawn"),
            )
        ),
        "RegistryEvent": obj(
            {
                "id": UUID,
                "action": enum("created", "edit", "submit", "withdraw"),
                "revision": revision,
                "created_at": DATE,
            }
        ),
    }
    for name, item in (
        ("RegistryDraftPage", "RegistryDraft"),
        ("RegistryClaimPage", "RegistryClaim"),
        ("RegistryEventPage", "RegistryEvent"),
        ("RegistrySearchPage", "PublicOrganization"),
    ):
        result[name] = obj(
            {
                "results": dict(arr(ref(item)), maxItems=20),
                "next_cursor": {"anyOf": [S, {"type": "null"}]},
            }
        )
    return result


def paths():
    entries = [("registrySearch", "search/", "get", None, 200, "RegistrySearchPage")]
    for plural, kind in (("drafts", "Draft"), ("claims", "Claim")):
        entries += [
            (
                "registryList" + kind + "s",
                plural + "/",
                "get",
                None,
                200,
                "Registry" + kind + "Page",
            ),
            (
                "registryCreate" + kind,
                plural + "/",
                "post",
                "Registry" + kind + "Input",
                201,
                "Registry" + kind,
            ),
            (
                "registryGet" + kind,
                plural + "/{pk}/",
                "get",
                None,
                200,
                "Registry" + kind,
            ),
            (
                "registryWithdraw" + kind,
                plural + "/{pk}/withdraw/",
                "post",
                "RegistryRevision",
                200,
                "Registry" + kind,
            ),
            (
                "registryHistory" + kind,
                plural + "/{pk}/history/",
                "get",
                None,
                200,
                "RegistryEventPage",
            ),
        ]
    entries += [
        (
            "registryEditDraft",
            "drafts/{pk}/",
            "patch",
            "RegistryDraftEdit",
            200,
            "RegistryDraft",
        ),
        (
            "registrySubmitDraft",
            "drafts/{pk}/submit/",
            "post",
            "RegistryRevision",
            200,
            "RegistryDraft",
        ),
    ]
    result = {}
    for identifier, suffix, method, request, status, response in entries:
        op = operation(identifier, "personal", request, status, response, "registry")
        if method != "get":
            op["security"][0]["csrfHeader"] = []
            op["responses"]["415"] = deepcopy(op["responses"]["400"])
        op["description"] = (
            "Claimant-only 04A. Default-off synthetic development/test exercise; no real intake/NGO authority/reviewer/publication/grant operations. Holds deny both reads and writes. UUID keyset pages, not snapshots; only existing four-field public projection is searchable. No auto-merge or private collision oracle."
        )
        params = []
        if "{pk}" in suffix:
            params.append(
                {"in": "path", "name": "pk", "required": True, "schema": UUID}
            )
        if method == "get" and ("{pk}" not in suffix or "history" in suffix):
            params.append(
                {"in": "query", "name": "cursor", "schema": dict(S, maxLength=1024)}
            )
        if suffix == "search/":
            params.extend(
                [
                    {
                        "in": "query",
                        "name": "q",
                        "required": True,
                        "schema": dict(S, minLength=2, maxLength=250),
                    },
                    {"in": "query", "name": "city", "schema": dict(S, maxLength=250)},
                ]
            )
        if method == "post" and "{pk}" not in suffix:
            params.append(
                {
                    "in": "header",
                    "name": "Idempotency-Key",
                    "required": True,
                    "schema": UUID,
                    "description": "Owner-scoped stable retry UUID; changed normalized payload/operation conflicts. Replays return CURRENT resource state; never automatically replay after uncertain response.",
                }
            )
        op["parameters"] = params
        op["x-pwc"]["unknown_query"] = "reject"
        result.setdefault("/api/v1/registry/" + suffix, {})[method] = op
    return result
