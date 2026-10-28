"""Additive actual read contracts; no permission, reviewer or command promises."""

from contracts.schema import obj, arr, ref, enum, operation, response, S, UUID


def definitions():
    revision = {"type": "integer", "minimum": 1, "maximum": 9223372036854775807}
    nullable = lambda schema: {"anyOf": [schema, {"type": "null"}]}
    return {
        "WorkspaceVerification": obj(
            {
                "id": UUID,
                "purpose": enum("organization_eligibility", "representative_mandate"),
                "state": enum("draft", "submitted", "withdrawn"),
                "revision": revision,
                "source_revision": revision,
                "stale": {"type": "boolean"},
            }
        ),
        "WorkspaceApplication": obj(
            {
                "id": UUID,
                "kind": enum("draft", "claim"),
                "organization_id": UUID,
                "revision": revision,
                "state": enum(
                    "draft",
                    "submitted",
                    "pending",
                    "needs_information",
                    "rejected",
                    "withdrawn",
                ),
                "name": nullable(dict(S, maxLength=250)),
                "city": nullable(dict(S, maxLength=100)),
                "classification": nullable(enum("registered", "unregistered")),
                "can_withdraw": {"type": "boolean"},
                "verification": dict(arr(ref("WorkspaceVerification")), maxItems=2),
            }
        ),
        "WorkspacePage": obj(
            {
                "results": dict(arr(ref("WorkspaceApplication")), maxItems=20),
                "next_cursor": nullable(S),
                "administration_available": {"type": "boolean", "const": False},
                "intake_available": {"type": "boolean", "const": False},
                "verification_available": {"type": "boolean"},
            }
        ),
    }


def paths():
    workspace = operation(
        "registryWorkspace", "personal", None, 200, "WorkspacePage", "registry"
    )
    workspace["description"] = (
        "Owner-only historical applications and latest-per-purpose exact-source-revision verification summaries (at most two per application), hidden when verification feature is disabled. Not NGO membership/administration. No new intake, reviewer, evidence or private target-organization reader. Claim labels are redacted. Withdrawal uses existing revision-checked endpoint; reads never mutate or issue authority."
    )
    workspace["parameters"] = [
        {"in": "query", "name": "kind", "schema": enum("draft", "claim")},
        {
            "in": "query",
            "name": "state",
            "schema": enum(
                "",
                "draft",
                "submitted",
                "pending",
                "needs_information",
                "rejected",
                "withdrawn",
            ),
        },
        {"in": "query", "name": "cursor", "schema": dict(S, maxLength=1024)},
    ]
    workspace["x-pwc"]["unknown_query"] = "reject"
    directory = operation(
        "publicDirectory", "public-drf", None, 200, "RegistrySearchPage"
    )
    directory["description"] = (
        "Bounded keyset search over existing verified four-field public projection only. No additional publication, consent approval, private fields or authority. Cursor signed, filter-bound, max age 3600s; page <=20, no total count, no snapshot guarantee. Public caller credentials are ignored. No real onboarding or private browser/mobile integration enabled."
    )
    directory["parameters"] = [
        {"in": "query", "name": key, "schema": dict(S, maxLength=250)}
        for key in ("q", "city")
    ] + [
        {
            "in": "query",
            "name": "classification",
            "schema": enum("", "registered", "unregistered"),
        },
        {"in": "query", "name": "cursor", "schema": dict(S, maxLength=1024)},
    ]
    directory["x-pwc"]["unknown_query"] = "reject"
    directory["x-pwc"]["client_network_exception"] = "Explicit public-only reader: exact directory GET, credentials omitted, no private/auth operations. Frozen W1 web_network=disabled continues to govern original authenticated client."
    for code in ("400", "429", "503"):
        directory["responses"][code] = response("AuthError")
    for code in ("403", "404", "405"):
        directory["responses"][code] = response("AuthError")
    directory["responses"]["200"] = response("RegistrySearchPage")
    directory["responses"]["429"]["headers"]["Retry-After"] = {
        "schema": {"type": "string"}
    }
    return {
        "/api/v1/directory/": {"get": directory},
        "/api/v1/registry/workspace/": {"get": workspace},
    }
