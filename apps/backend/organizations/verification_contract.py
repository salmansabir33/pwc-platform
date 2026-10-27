"""Only implemented 04B preparation and unavailable adapters; no proposed approval API."""

from copy import deepcopy
from contracts.schema import obj, arr, ref, operation, S, UUID, DATE, enum


def definitions():
    rev = {"type": "integer", "minimum": 1, "maximum": 9223372036854775807}
    purpose = enum("organization_eligibility", "representative_mandate")
    track = enum("registered", "unregistered")
    common = {"id": UUID, "revision": rev, "created_at": DATE, "updated_at": DATE}
    result = {
        "VerificationCaseInput": obj(
            {
                "source_kind": enum("draft", "claim"),
                "source_id": UUID,
                "source_revision": rev,
                "purpose": purpose,
            }
        ),
        "VerificationCase": obj(
            dict(
                common,
                organization_id=UUID,
                source_kind=enum("draft", "claim"),
                source_id=UUID,
                source_revision=rev,
                purpose=purpose,
                track=track,
                state=enum("draft", "submitted", "withdrawn"),
            )
        ),
        "EvidencePreparationInput": obj(
            {"case_revision": rev, "prepared_offline": {"type": "boolean"}}
        ),
        "EvidencePreparationEdit": obj(
            {
                "case_revision": rev,
                "revision": rev,
                "prepared_offline": {"type": "boolean"},
            }
        ),
        "EvidencePreparation": obj(
            dict(
                common,
                case_id=UUID,
                prepared_offline={"type": "boolean"},
                state=enum("planned", "withdrawn"),
            )
        ),
        "VerificationHistory": obj(
            {
                "id": UUID,
                "revision": rev,
                "reason_code": enum(
                    "applicant_created",
                    "preparation_added",
                    "preparation_replaced",
                    "preparation_withdrawn",
                    "preparation_submitted",
                    "applicant_withdrawn",
                ),
                "preparation_id": {"anyOf": [UUID, {"type": "null"}]},
                "preparation_revision": {"anyOf": [rev, {"type": "null"}]},
                "prepared_offline": {"anyOf": [{"type": "boolean"}, {"type": "null"}]},
                "created_at": DATE,
            }
        ),
        "VerificationRequirements": obj(
            {
                "case_id": UUID,
                "purpose": purpose,
                "track": track,
                "rubric_status": enum("unapproved"),
                "accepted_evidence_classes": {
                    "type": "array",
                    "items": S,
                    "maxItems": 0,
                },
                "file_intake_available": {"type": "boolean", "const": False},
                "review_available": {"type": "boolean", "const": False},
                "submission_effect": enum("preparation_record_only"),
            }
        ),
    }
    for model in ("VerificationCase", "EvidencePreparation", "VerificationHistory"):
        result[model + "Page"] = obj(
            {
                "results": dict(arr(ref(model)), maxItems=20),
                "next_cursor": {"anyOf": [S, {"type": "null"}]},
            }
        )
    return result


ENTRIES = [
    ("verificationListCases", "cases/", "get", None, 200, "VerificationCasePage"),
    (
        "verificationCreateCase",
        "cases/",
        "post",
        "VerificationCaseInput",
        201,
        "VerificationCase",
    ),
    ("verificationGetCase", "cases/{pk}/", "get", None, 200, "VerificationCase"),
    (
        "verificationRequirements",
        "cases/{pk}/requirements/",
        "get",
        None,
        200,
        "VerificationRequirements",
    ),
    (
        "verificationHistory",
        "cases/{pk}/history/",
        "get",
        None,
        200,
        "VerificationHistoryPage",
    ),
    (
        "verificationSubmit",
        "cases/{pk}/submit/",
        "post",
        "RegistryRevision",
        200,
        "VerificationCase",
    ),
    (
        "verificationWithdraw",
        "cases/{pk}/withdraw/",
        "post",
        "RegistryRevision",
        200,
        "VerificationCase",
    ),
    (
        "verificationListPreparation",
        "cases/{pk}/preparation/",
        "get",
        None,
        200,
        "EvidencePreparationPage",
    ),
    (
        "verificationCreatePreparation",
        "cases/{pk}/preparation/",
        "post",
        "EvidencePreparationInput",
        201,
        "EvidencePreparation",
    ),
    (
        "verificationGetPreparation",
        "cases/{pk}/preparation/{item_id}/",
        "get",
        None,
        200,
        "EvidencePreparation",
    ),
    (
        "verificationReplacePreparation",
        "cases/{pk}/preparation/{item_id}/",
        "patch",
        "EvidencePreparationEdit",
        200,
        "EvidencePreparation",
    ),
    (
        "verificationWithdrawPreparation",
        "cases/{pk}/preparation/{item_id}/withdraw/",
        "post",
        "EvidencePreparationEdit",
        200,
        "EvidencePreparation",
    ),
    (
        "verificationEvidenceUnavailable",
        "cases/{pk}/evidence/",
        "post",
        None,
        None,
        None,
    ),
    (
        "verificationDownloadUnavailable",
        "cases/{pk}/evidence/{item_id}/download/",
        "get",
        None,
        None,
        None,
    ),
    ("verificationQueueUnavailable", "reviewer-queue/", "get", None, None, None),
]


def paths():
    result = {}
    for identifier, suffix, method, request, status, response in ENTRIES:
        op = operation(
            identifier, "personal", request, status or 503, response, "verification"
        )
        if status is None:
            op["responses"]["503"] = deepcopy(op["responses"]["400"])
        if method != "get":
            op["security"][0]["csrfHeader"] = []
            op["responses"]["415"] = deepcopy(op["responses"]["400"])
        op["description"] = (
            "04B personal synthetic preparation only; no admissible evidence or reviewer authorization. Distinct eligibility/mandate lanes. Submission never verifies an organization or issues authority. File/reviewer adapters ALWAYS unavailable; no body processing. Recovery holds deny reads/writes. Real intake and deployment gated."
        )
        params = [
            {"in": "path", "name": name, "required": True, "schema": UUID}
            for name in ("pk", "item_id")
            if "{" + name + "}" in suffix
        ]
        if method == "get" and (
            suffix == "cases/"
            or suffix.endswith("history/")
            or suffix.endswith("preparation/")
        ):
            params += [
                {"in": "query", "name": "cursor", "schema": dict(S, maxLength=1024)}
            ]
        if identifier in ("verificationCreateCase", "verificationCreatePreparation"):
            params += [
                {
                    "in": "header",
                    "name": "Idempotency-Key",
                    "required": True,
                    "schema": UUID,
                }
            ]
        op["parameters"] = params
        op["x-pwc"]["unknown_query"] = "reject"
        result.setdefault("/api/v1/verification/" + suffix, {})[method] = op
    return result
