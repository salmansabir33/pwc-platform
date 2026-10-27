"""Actual disabled controlled onboarding adapters; no proposed privileged DTOs."""

from copy import deepcopy
from contracts.schema import operation, obj, enum, S, UUID
from .onboarding_policy import POLICY

ENTRIES = [
    ("controlledRequirements", "requirements/", "get"),
    ("controlledListUnavailable", "records/", "get"),
    ("controlledCreateUnavailable", "records/", "post"),
    ("controlledReadUnavailable", "records/{pk}/", "get"),
    ("controlledEditUnavailable", "records/{pk}/", "patch"),
    ("controlledAcceptUnavailable", "invitations/{pk}/accept/", "post"),
]
ENTRIES += [
    ("controlled" + c.title() + "Unavailable", "records/{pk}/" + c + "/", "post")
    for c in ("submit", "approve", "reject", "return", "withdraw", "invitation")
]


def definitions():
    return {
        "ControlledOnboardingRequirements": obj(
            {
                key: {"type": "boolean", "const": value}
                if type(value) is bool
                else {"type": "array", "items": S, "const": value}
                if isinstance(value, list)
                else enum(value)
                for key, value in POLICY.items()
            }
        )
    }


def paths():
    result = {}
    for identifier, suffix, method in ENTRIES:
        requirements = identifier == "controlledRequirements"
        op = operation(
            identifier,
            "personal",
            None,
            200 if requirements else 503,
            "ControlledOnboardingRequirements" if requirements else None,
            "registry",
        )
        op["description"] = (
            "Revised 04B offline initial rollout. Self-service unavailable. External examination, platform attestation, independent approval, recipient acceptance and later grant activation are separate. All controlled readers/commands and invitations unconditionally unavailable pending E04/GM contracts; no object lookup/body parsing or real authority. Requirements are generic policy, NOT caller capabilities."
        )
        op["parameters"] = (
            [{"in": "path", "name": "pk", "required": True, "schema": UUID}]
            if "{pk}" in suffix
            else []
        )
        op["x-pwc"]["unknown_query"] = "reject"
        if method != "get":
            op["security"][0]["csrfHeader"] = []
            op["responses"]["415"] = deepcopy(op["responses"]["400"])
        result.setdefault("/api/v1/controlled-onboarding/" + suffix, {})[method] = op
    return result
