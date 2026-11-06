"""Additive v1 read contract; success cases describe test-only exercise, not rollout."""


def definitions():
    from contracts.schema import obj, ref, arr, UUID, DATE, enum
    from .models import Opportunity

    return {
        "PublicOpportunity": obj(
            {
                "id": UUID,
                "organization": ref("PublicOrganization"),
                "type": enum(*Opportunity.Type.values),
                "title": {"type": "string", "maxLength": 200},
                "summary": {"type": "string", "maxLength": 1000},
                "published_at": DATE,
            }
        ),
        "PublicOpportunityPage": obj(
            {
                "results": dict(arr(ref("PublicOpportunity")), maxItems=20),
                "next_cursor": {"type": ["string", "null"], "maxLength": 1024},
            }
        ),
    }


def paths():
    from contracts.schema import operation, response, UUID, enum
    from .models import Opportunity

    result = {}
    for suffix, identifier, schema in [
        ("", "publicOpportunities", "PublicOpportunityPage"),
        ("{pk}/", "publicOpportunity", "PublicOpportunity"),
    ]:
        op = operation(identifier, "public-drf", None, 200, schema)
        op["description"] = (
            "08C-A independent read foundation. Live reads/publication unavailable pending exact authority and privacy acceptance. "
            "Success is test-profile exercise only. Published records AND currently verified owning NGO only; "
            "verified is an eligibility floor, not approved publication consent. No credentials consulted or writers. "
            "Title-only normalized substring search, owning NGO city, exact type/NGO filters. "
            "UUID ascending keyset, <=20 records; filter-bound signed cursor, max age 3600 seconds; "
            "no total counts or snapshot guarantee, current eligibility rechecked each request. "
            "No applications, saved items, private project workspace or permission metadata."
        )
        op["x-pwc"].update(
            {
                "availability": "default-disabled",
                "gates": [
                    "test-profile-only",
                    "PWC_OPPORTUNITIES_TEST_EXERCISE (not environment-configurable)",
                    "publication-authority-and-privacy-acceptance-required-for-live",
                ],
                "disabled": {"status": 503, "code": "OPPORTUNITIES_UNAVAILABLE"},
                "unknown_query": "reject",
            }
        )
        op["responses"] = {
            "200": response(schema),
            **{
                str(code): response("AuthError")
                for code in (400, 403, 404, 405, 429, 503)
            },
            "default": op["responses"]["default"],
        }
        op["responses"]["429"]["headers"]["Retry-After"] = {
            "schema": {"type": "string"}
        }
        op["parameters"] = (
            [{"in": "path", "name": "pk", "required": True, "schema": UUID}]
            if suffix
            else [
                {
                    "in": "query",
                    "name": key,
                    "schema": {"type": "string", "maxLength": 250},
                }
                for key in ("q", "city")
            ]
            + [
                {
                    "in": "query",
                    "name": "type",
                    "schema": enum("", *Opportunity.Type.values),
                },
                {"in": "query", "name": "organization_id", "schema": UUID},
                {
                    "in": "query",
                    "name": "cursor",
                    "schema": {"type": "string", "maxLength": 1024},
                },
            ]
        )
        result["/api/v1/opportunities/" + suffix] = {"get": op}
    return result
