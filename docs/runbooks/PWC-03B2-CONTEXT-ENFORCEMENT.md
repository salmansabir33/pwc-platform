# PWC-03B.2 — tenant HTTP enforcement and context contracts

**Date:** 24 October 2026

**Starting checkpoint:** `b42bd0ec791f766aaf83fb9c5102d9bb9376e9d0` on `arena/d8a3e024-pwc-platform`.

**Authority:** [ADR-0002](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md) §§3, 4.5, 5, 8, 11; [approved authentication ADR](../decisions/ADR-0001-authentication-and-recovery.md); [03B.1 runbook](PWC-03B1-AUTHORIZATION-KERNEL.md).

**Scope:** synthetic read APIs only. No real NGO authority, business workflows, grant mutation APIs, frontend or deployment. No approved ADR or existing migration was amended.

## 1. Preflight and preserved foundation

Fetched `origin/main` and the remote feature branch; both local and remote feature checkpoint contained `b42bd0ec`. Working tree/index were clean, so no restoration reconciliation was needed. The fresh pre-edit PostgreSQL baseline passed all **292 tests**. Existing accounts/organization source, approved ADR bytes and all migrations are preserved. Root AGENTS/roadmap historical branch/auth descriptions are not instructions to replace the merged foundation.

The only new HTTP activation setting is `PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED`, default **false**. The independent .1 synthetic environment/principal/grant controls remain mandatory. No fixtures, grants, roles or tenants are seeded at application startup or migration.

## 2. Implemented routes

All routes use `/api/v1/`; all successful bodies are JSON. GET and HEAD are supported. HEAD performs the same authorization and audit as GET, then Django suppresses the body. OPTIONS/POST/PUT/PATCH/DELETE are not implemented and return a minimized 405 while enabled, never metadata or mutation. When HTTP activation is off, registered routes/methods return a uniform 404 before touching credentials or authority data.

| Route | Server-owned action | Result |
|---|---|---|
| `GET /api/v1/me/ngo-contexts/` | Entry checked for every returned context | Current user's eligible synthetic contexts only; cursor scan, at most 50 results. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/capabilities/` | `ngo.context.enter` | Current effective actions, context revision and advisory expiry. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/private-probe/` | `ngo.private_stub.read` | Fixed synthetic private projection. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/kernel-settings/` | `ngo.kernel_settings.read` | Fixed synthetic settings projection; reader alone denies. |

These are the ADR names, not alternate workspace aliases. String path conversion deliberately sends malformed UUIDs to kernel validation, yielding 400 after authentication. UUIDs are normalized by the typed context resolver. There are no dynamic action/field/resource dispatch endpoints. Unregistered finance/grants/support/project/context-selection URLs retain ordinary Django 404; they do not inherit the new envelope or return private data.

## 3. Response contracts and checked fixtures

Discovery response keys:

```json
{
  "results": [
    {"kind": "ngo", "organization_id": "00000000-0000-4000-8000-000000000001", "context_revision": 2}
  ],
  "next_cursor": null
}
```

The example UUID is only a placeholder, not a seeded organization. No NGO names, counts, memberships, grant IDs, other users, evidence, finance or operational fields are exposed. Each item's revision is its current locked tenant revision.

Capability response keys:

- `context`: exactly `kind` and `organization_id`.
- `registry_version`: `ngo_kernel_v1`.
- `context_revision`: integer.
- `actions`: sorted current effective action identifiers, same NGO only.
- `earliest_grant_expires_at`: aware ISO-8601 UTC expiry of the earliest contributing current grant, **advisory only**. Revocation can invalidate the projection sooner.

Probe/settings response keys are exactly `organization_id`, `probe_code`, `label`, `context_revision`. Labels/codes are fixed synthetic constants. There is no arbitrary free text, model serialization, field selector, beneficiary/member data, account balance or document.

[`ngo-contexts-v1.fixtures.json`](../../packages/api-contracts/ngo-contexts-v1.fixtures.json) records route names, wire keys, registry, headers, errors and pagination semantics. A real HTTP/PostgreSQL test reads it and compares actual responses. It is not generated OpenAPI, a complete client SDK or production approval. Existing auth fixtures are unchanged.

Every new route's success/error response has `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, and Vary includes Cookie and Authorization. Responses are always JSON, even if Accept asks for HTML; there is no browsable/debug renderer or format-query override. No ETag is emitted. If-Match/If-None-Match do not skip authorization, return 304, or impose a write precondition on these reads.

## 4. Authentication and centralized enforcement

`access.views` contains only static action mappings, gate/method handling and response shaping. It deliberately does not let DRF's default authentication/permission phase make an earlier business decision: `services.evaluate` and `services.discover` reuse `PersonalAuthentication` **inside the same durable transaction as scoped projection and audit**. No view trusts an earlier `request.user`, claims or a client-selected action.

The common service boundary retains the .1 lock protocol, primary READ COMMITTED connection, transaction timeouts, current session/contact/epoch/factor/credential checks, clear recovery hold, matching synthetic attestations, verified workspace, closed registry, current grants and database wall-clock checks. Private probes additionally exercise the tenant-prefiltered direct-object lookup. No lazy ORM objects/querysets escape to serialization.

Authentication behavior is unchanged: registered web cookies or opaque mobile Bearer credentials, never both; direct HTTPS; exact configured portal binding for cookies; invalid/revoked/expired/epoch-stale sessions deny. Safe reads need no new CSRF challenge. Unsafe context methods do not exist; existing authentication mutations retain their exact Origin/CSRF requirements, covered by regression tests. Reads/discovery/HEAD do not renew idle lifetime or rotate credentials.

A refactor extracted the shared transaction/authentication/eligibility/audit helpers from .1 so discovery and direct reads use one permission evaluator. No alternate permission engine, Django staff/superuser shortcut, new role, wildcard or nonpersonal assurance operation was introduced.

## 5. Explicit tenant inputs

For private reads, only the path Organization UUID addresses the tenant. There is no remembered server selection, selection row, User.current_organization or default tenant. Personal auth remains shared across NGOs, not duplicated identities.

The input grammar is closed and runs after live authentication, before domain lookup:

- All GET bodies, including `{}`, are rejected. They cannot supply ownership or authority.
- Private reads accept **no query parameters**. Discovery accepts only one nonempty `cursor` value of at most 512 characters.
- Tenant/context/selection/role/permission/capability/action header families are rejected, including X-prefixed variants. Matching values are rejected too, rather than becoming competing sources of truth.
- Unknown or duplicate query fields, `fields=*`, `format`, action/role claims, organization IDs and page-size overrides reject with 400.
- Unrecognized ordinary headers cannot grant anything: views never consume them as authority. For example an MFA assertion header cannot override missing grants.

No client-supplied parameter changes the server's mapped action. A reader's kernel-settings request remains denied even when it supplies an admin-probe label, old capability list or MFA assertion.

## 6. Discovery pagination, locks and audit

Discovery first authenticates the User/session under existing auth locks. Candidate querying is filtered to that User and attested batch, verified/unrevoked/current grant and eligible synthetic workspace. It selects **Organization UUIDs only**, not an organization registry dump or another user's grants.

A keyset scan takes at most 51 distinct candidate IDs in Organization UUID order; at most 50 roots are locked, in that same stable order, through the existing permissioned lock-only PostgreSQL function. Every locked state, batch, workspace and current tenant grant is rechecked using the shared helpers. At most 50 scalar entries are materialized. A later wall-clock check occurs after access-audit insertion and before release.

The opaque cursor is Django-signed, v1, bound to User and logical AuthSession, with a one-hour maximum age. It stores only a scan position, not grants/capabilities or selection authority. Secret rotation, expiry, tampering, another User or a different session invalidate it with 400. Refresh that preserves the same logical session does not itself turn it into authority; every continuation reauthenticates and requeries grants.

Pages are not a stable snapshot. New grants/revocations/expiry may alter later pages. The next cursor follows the last **scanned** candidate, not the last returned item; candidates that become ineligible before root validation are omitted. An empty/short page with a cursor is possible. Follow the cursor rather than assuming a short page means completion; only null means this scan has no further known candidates. No total count or foreign existence signal is returned.

Each returned context requires its own durable `ngo.context.enter` allow event. An empty page records `discovery` / `deny` / `no_eligible_contexts`: HTTP enumeration succeeded, but no NGO authority was exercised. This uses the existing immutable event schema honestly instead of fabricating a null-context grant-backed allow; no migration amendment was needed.

If a selected supporting grant expires after page evaluation/audit but before the final check, the entire page's allow evidence rolls back and HTTP returns a redacted **409 state_conflict**, with no entries. A final session deadline failure similarly rolls back and returns 401. Clients may start a fresh discovery after 409; this is not an authority mutation or replay guarantee.

Revocation and reads serialize on the same User/root protocol. A read that acquired authority first may finish before revocation. After revocation commits, new HTTP reads/capabilities/discovery deny or omit that context. Already returned bytes cannot be recalled. There is no positive cache and no promise to cancel a previously serialized response.

## 7. Error taxonomy

Registered routes use exactly `{"error":{"code":"...","correlation_id":"..."}}`. Errors contain no NGO/object/grant IDs, current revisions, field payloads or existence details.

| Status | Code / meaning |
|---|---|
| 400 | `invalid_context`: malformed UUID, forbidden/conflicting inputs or invalid cursor. Auth-owned `AMBIGUOUS_CREDENTIALS` and `TRANSPORT_NOT_ALLOWED` retain their existing status semantics. |
| 401 | `authentication_required`: absent, invalid, expired, revoked, suspended or otherwise ineligible personal session. Includes `WWW-Authenticate: Bearer`. |
| 403 | `recovery_hold`; or `permission_denied` only after entry to that NGO is authorized. Existing auth-owned CSRF failures remain 403. |
| 404 | `not_found`: unknown NGO, missing entry grant, synthetic-ineligible tenant/principal, foreign/absent object, revoked/expired grant; or registered HTTP route disabled. Foreign and absent cases share an envelope. |
| 405 | `method_not_allowed`: enabled registered routes have no unsafe-method/OPTIONS implementation. No mutation or private metadata is released. |
| 409 | `state_conflict`: discovery's selected authority expires before final release; no partial page or allow audits commit. |
| 503 | `authorization_unavailable`: required configuration, auth dependency, DB, lock or audit failure. Never an anonymous/legacy fallback. |

Reads require no 428/412 revision preconditions. Those and mutation-specific 409 transitions remain in the existing fixture lifecycle service or future separately approved commands, not invented HTTP write APIs. Malformed requests do not disclose revisions before entry permission.

Successful projection/audit commits atomically. Audit failure releases no private response. Dependency failures log fixed text/correlation only; no exception payload, credentials, raw body or foreign records are logged by the adapter. Redacted denial events are attempted separately after rollback where possible. A database outage cannot guarantee durable denial audit; telemetry is not claimed as DB evidence.

## 8. Synthetic configuration and database privileges

The HTTP switch alone cannot grant eligibility. The .1 switch, isolated environment and database-name checks, READ COMMITTED/no-router requirement, existing auth configuration, synthetic principal/tenant/batch, verified workspace and live grant all still apply. Production stays disabled. The factory only creates new synthetic entities, not real enrollments. Legacy rows remain historical/non-authoritative.

Use the separately provisioned restricted runtime role and offline fixture writer described in the .1 runbook and `access/db_roles.sql`. Runtime must not own tables/functions or inherit fixture/migration/DDL privileges. This slice adds no DB objects/privileges. New HTTP tests exercise discovery, capabilities and reads under an actual restricted role without direct state UPDATE permission. Operators controlling settings, migration-owner credentials or raw SQL remain explicit trust boundaries, not protections supplied by JSON APIs.

## 9. PostgreSQL acceptance evidence

Environment: Python **3.11.2**, Django **5.2.18**, PostgreSQL **16.2**, READ COMMITTED. Existing pinned requirements retained. The sandbox's external development-only pgserver supplies PostgreSQL; it is not an application dependency. No local Python 3.12, Docker, real browser/native storage or production deployment acceptance is claimed.

Executed from `apps/backend` with environment-supplied secrets/database configuration:

```sh
python manage.py test --verbosity 1
python manage.py test access.test_http --verbosity 1
python manage.py test access.test_http.ContextHTTPRaceTests access.tests.KernelRaceTests --verbosity 1
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python -m pip check
```

Results:

- Fresh pre-edit baseline: **292 passed**, 251.328 seconds.
- New HTTP/fixture/privilege/discovery suite: **44 passed**, 14.054 seconds.
- Full final suite: **336 passed** (292 prior + 44 new), 258.966 seconds; no failures or skips.
- Concurrency subset: **16 passed in each of three additional runs** (48 repeated executions). Six HTTP cases plus ten existing kernel cases.
- Django checks, dependency checks and migration drift/application/pending checks passed. No migration operations were added; fresh test databases still exercise all existing migrations.
- Python compilation, scoped source/fixture/whitespace checks and approved ADR/migration/auth-source preservation are checked at handoff. No configured formatter/linter gate is claimed.

The prior .1 test asserting HTTP route absence now asserts that the implemented routes remain unavailable by default, with minimized/no-store 404 responses. It is a scoped acceptance update, not removal of the default-off safeguard.

| ADR coverage | Evidence / boundary |
|---|---|
| K01–K02; AZ-01/02 | Real HTTP lists and singleton probes scope by User/tenant; A/B direct access denied; one User with different NGO roles. No business writes exist to certify. |
| K03–K06; AZ-03/04/05/08/10/13/18 | Legacy/member/admin/Board/staff/Group labels ignored; reader/admin-probe separation; live auth/hold/expiry/revocation/unknown-action negatives. Prior accepted-TOTP kernel negative retained. No real finance/support/signatory acceptance implied. |
| K07–K10; AZ-11/19/28 | Separate connections, Events and observed `pg_blocking_pids`: read-first and revoke-first for both HTTP probe/discovery; actual DB expiry during root wait; final deadlines, audit rollback, redacted 409/503. Existing create/revoke/timeout races retained. |
| K11–K13; AZ-29 | Independent default-off HTTP/environment gates, unattested real-record denial, restricted runtime SQL role; unchanged migrations and existing preservation/irreversibility tests. |
| K14–K15; AZ-12/26/30 | Sorted/bounded discovery roots and 51-candidate pagination; session-bound/tampered/expired cursor tests; no idle renewal/cache bypass; cookie/Bearer/TLS/CSRF regression; checked minimized JSON keys. Client cache-switch rendering remains unimplemented. |

No representative bootstrap, beneficiary data, finance/maker-checker, commitments, sharing, file/export, durable-workload or support-access positive paths were implemented or certified (remaining AZ domain cases). Security coverage is for this synthetic read slice, not full G1a/M1 or production sign-off.

## 10. Flutter/web integration and next gate

Capture the explicit Organization UUID with each request. A frontend may remember a display choice, but cannot send selection headers or tenant body overrides. Partition private state by personal identity/context; cancel/tag old requests, discard late responses after switches and clear private state on logout/revocation/hold. A capability projection is presentation data, never authorization. Refresh it on context/revision changes, but still expect each subsequent request to deny.

On 401 use existing personal session recovery/re-login rules. On hold/403 clear the inaccessible screen rather than inventing an MFA override. Treat 404 as absence/unavailable authority without distinguishing foreign/unknown tenants. On discovery 409 restart the scan; on 503 release no optimistic private result. Cursors bind to a logical session, so a new login restarts discovery. No client SDK/schema/screens were generated.

**Recommendation:** proceed to authorization integration review before any PWC-03B.3 assignment. Privileged grant issue/revoke/delegate/admin-transfer commands remain disabled pending complete D03/D05/D14 permission, provenance, assurance, canonicalization and recovery contracts. No nonpersonal proof registry extension was made. Real onboarding/verification, finance, governance, legal commitments, sharing, support, files/exports and workload authority retain their own ADR/operational gates. Production privilege provisioning, retention/monitoring/incident rules, load testing and client runtime acceptance remain unresolved release work.
