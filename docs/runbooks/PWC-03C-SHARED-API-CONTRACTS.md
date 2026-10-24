# PWC-03C — Shared API Contracts & Cross-Platform Integration Foundation

Date: 24 October 2026. Scope: the bounded API-contract slice of PWC-03C, not completion of every PWC-03C roadmap item or approval of live integration.

## Starting state and existing assessment

Active writable branch: `arena/44f76f8d-pwc-platform`, initially clean at `cf82dec7adfc6f57e1152cabc6d1f0491d09a5b7`, equal to freshly fetched `origin/main`. The checkout was shallow; fetching existing history (not changing branches or rewriting history) allowed ancestry verification of merged PRs #3 (`889fc2f`), #4 (`cb4ae6c`) and #5 (`cf82dec`). Historical branch/scaffold statements in AGENTS/roadmap are not the current task status.

Read AGENTS, Roadmap v2.0, approved ADR-0001/0002/0003, actual URL configurations, registration/session/MFA and synthetic-context adapters/services, public serializer/settings, existing tests/CI, W1 API runtime and Flutter architecture/reserved directory. Approved ADRs, application security behavior, migrations and product requirements remain unchanged.

Existing contracts were three useful checked JSON wire-key/transport fixture sets, not OpenAPI or generated clients. Registration/reset had no equivalent checked JSON examples. Most auth routes are ordinary Django closures, not DRF serializers; automatic DRF schema discovery alone would silently omit them. Session fixtures describe the historical MFA-disabled profile; the MFA fixture/current implementation supersedes its deferred-denial notes when MFA is enabled. No fixture was discarded or rewritten.

## Canonical source and organization

**Implemented Django behavior remains the authority.** The single interchange artifact is `packages/api-contracts/openapi-v1.json`: OpenAPI **3.1.0**, contract release **1.0.0**, relative server `/`, only currently registered `/api/v1/` routes.

| File                                                                         | Role                                                                                                                                                                                                        |
| ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/backend/contracts/schema.py`                                           | Narrow annotations for plain Django function views, security/error/availability metadata and response shapes; public organization properties derive from the actual DRF serializer, not a second field list |
| `apps/backend/contracts/generate.py`                                         | Deterministic offline generation; exact recursive Django route inventory, source fingerprint and frozen compatibility checks                                                                                |
| `packages/api-contracts/openapi-v1.json`                                     | Checked canonical artifact: 32 paths, 47 operations including actual HEAD/OPTIONS and method-agnostic health behavior, 39 schemas                                                                           |
| `packages/api-contracts/source-lock.json`                                    | SHA256 fingerprints of relevant existing adapters, services, registry, models and settings; any backend source change requires deliberate contract review/regeneration                                      |
| `packages/api-contracts/compatibility-v1.json`                               | Frozen initial-release operation/schema/security fingerprints, not a second editable specification                                                                                                          |
| `packages/api-contracts/examples-v1.json`                                    | 70 checked synthetic structural request/success/error cases, including registration/reset and enabled-MFA preauth; not issued credentials or an oracle proving backend behavior                             |
| Existing `*.fixtures.json`                                                   | Retained historical checked behavioral/wire-key fixtures; key/transport overlap is checked against the canonical schemas                                                                                    |
| `packages/api-contracts/generated/schema.ts`                                 | Type-only output of pinned `openapi-typescript` 7.13.0; no fetch client, secret store or runtime SDK                                                                                                        |
| `packages/api-contracts/generated/browser-operations.ts`                     | Generated version/transport metadata for exactly W1's existing six browser-safe operations                                                                                                                  |
| `apps/backend/contracts/check.py`, `validation.py`, `tests.py`, `testing.py` | OpenAPI/schema/example/security/compatibility tests and an opt-in actual-HTTP regression validator                                                                                                          |
| `packages/api-contracts/requirements.txt`                                    | Pinned optional Python build/test tools and transitives, separate from production backend requirements                                                                                                      |

Nothing serves a new schema endpoint or imports this tooling into production authentication. No DRF/auth framework replacement, schema SaaS, middleware bypass or new runtime dependency was added. Tooling choice: maintained `openapi-spec-validator` 0.9.0 and `jsonschema` 4.26.0, with pinned dependencies, plus build-only TypeScript generation. Apache-2.0/MIT primary tool licensing is not a formal legal approval. The generator is intentionally small because existing function views require annotations regardless of discovery framework.

## Generate and check

From repository root, use Python 3.11 or 3.12 and the existing PostgreSQL 16 setup in [LOCAL-SETUP](LOCAL-SETUP.md). Supply a development/test-only `DJANGO_SECRET_KEY`; do not put operational credentials in commands, examples or Git.

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r apps/backend/requirements.txt -r packages/api-contracts/requirements.txt
pip check
npm ci --ignore-scripts

cd apps/backend
python -m contracts.generate
python -m contracts.check --check
cd ../..
npm run contracts:types
npm run contracts:types:check
npm run check
```

Generation needs Django configuration, but does not connect to PostgreSQL or activate authentication. `--check` compares exact bytes and never overwrites generated outputs. The TypeScript check generates into a temporary directory and compares bytes before cleanup. The generated files intentionally retain their generators' formatting; do not manually edit/reformat them.

For actual regression evidence, provision a disposable PostgreSQL database/test role with the existing instructions, export DB configuration, and run:

```bash
cd apps/backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --testrunner contracts.testing.ContractRunner --verbosity 2
```

The opt-in runner instruments Django test-client responses across the **existing full suite**, validating JSON status/body shape, security headers and empty HEAD/204 semantics against the canonical document. It does not mock services or print payloads/credentials. Existing tests still determine authorization and business outcomes. Only combinations actually exercised are checked; a schema or coverage count is not proof of every possible endpoint/state/transport combination. Framework/proxy non-JSON error responses remain a documented fallback and are not misclassified as successful API JSON.

To recheck the focused negative guard suite without a database:

```bash
cd apps/backend
python manage.py test contracts --verbosity 2
```

## Availability and implemented methods

`x-pwc.availability`, `gates`, `transport`, `csrf`, `disabled`, `direct_https` and `authorization` are machine-readable operation metadata, not permissions. Error statuses in shared families are conservative possible envelopes, not promises that every status can arise at every operation. Parsing/transport/method guards can take precedence over the nominal disabled response.

- **Public implemented:** health liveness, CSRF bootstrap and read-only verified-workspace organization projections. Public does not mean production approved. The directory is not a full search/publishing product and exposes only `id`, `name`, `city`, `classification`. Health is method-agnostic in the actual Django function; unsafe verbs can still be rejected by Django CSRF middleware. Consumers should use GET. DRF organization GET/HEAD/OPTIONS are documented, including framework metadata, not NGO capabilities.
- **Implemented, default-disabled:** registration/verification, password reset, web/mobile issuance, mobile refresh, personal `me`, logout, device sessions/revoke/logout-all, MFA enrollment/confirmation/removal/recovery-code rotation, personal assurance intents/step-up/hold clearance. The schema does not enable them. Registration/reset delivery is additionally **synthetic-only**, not an approved live email provider. Primary disabled/misconfigured auth responses use `503 AUTH_UNAVAILABLE`; malformed transport/method/body can fail earlier.
- **Synthetic-only, independently gated:** discovery and three context-addressed GET/HEAD endpoints. With `PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED=false`, even unsupported methods are hidden by `404 not_found`. The HTTP gate alone is insufficient: disabled kernel/non-isolated or unavailable dependencies can produce `503 authorization_unavailable`; current principal/session/hold/batch/tenant/grant checks still apply. Nominal `disabled` metadata describes the outer HTTP gate, not every combination of internal failure.
- **Planned/unregistered:** password/contact change, real workspace discovery, onboarding, grants, membership, finance, governance, files/exports and other business routes. These are deliberately absent from `paths`; ADR target catalogs are not implemented endpoints. No new route is added by PWC-03C.

## Errors, pagination and wire conventions

- Auth JSON error: `{error: {code, message, field_errors, request_id}}`; `field_errors` maps to arrays of strings. Synthetic-context JSON error: `{error: {code, correlation_id}}`. Public DRF errors may use `{detail}`; global Django/ingress failures may be HTML/non-JSON. Error-code/status families are listed in `x-pwc-security.error_codes`.
- Never render raw server errors, field values or HTML, or log request bodies/proofs/passwords/tokens. Use safe internal categories and bounded support references. W1 normalization already handles nested auth/context envelopes and non-JSON failure safely.
- `401` requires authoritative session invalidation; `403` denies current access, `404` can hide resources/features, `409` means state conflict, `429` may provide numeric Retry-After, `503` means unavailable (not necessarily disabled). Do not turn failures into fabricated empty workspaces or retry unsafe requests automatically.
- Auth/synthetic adapter responses require `Cache-Control: no-store` and `Referrer-Policy: no-referrer`; synthetic responses also vary on Cookie/Authorization. These are not promises about global middleware/proxy-generated errors. Secrets must not enter CDN/offline/query persistence.
- UUIDs serialize as UUID strings; dates are timezone-aware ISO-8601; hold states stay `clear`, `restricted`, `review_required`. Public organization detail uses Django's UUID path converter. Synthetic context uses a string converter so malformed UUIDs reach the kernel's deliberate error handling; accepted clients send canonical explicit Organization UUIDs.
- Public organizations are currently an **unpaginated array**. Session inventory is `{results}` without cursors. Synthetic discovery is `{results, next_cursor}` with at most 50 rows and a signed, principal/logical-session-bound scan cursor (max age 3600 seconds), not encrypted or a stable snapshot. Unknown discovery/context query fields and GET bodies are rejected. Do not invent generic page/limit or alternate context selection headers.
- Request schemas express successful wire shapes, not every invalid value deliberately exercised by negative tests. Backend email canonicalization (case-insensitive, dots/plus preserved, reviewed IDNA profile), password policy (15–128 characters), field validation, ownership, time/deadline and assurance requirements remain authoritative; structural JSON validity never proves semantic acceptance.

## Versioning and compatibility

`/api/v1/` is the API major; `info.version`/generated `contractVersion` is the checked contract release. No HTTP contract-version header, server negotiation endpoint or SDK release has been invented. Clients must pin the canonical artifact/release and generated types together. `assertContractVersion` fails mismatched local artifacts closed; it cannot prove a running backend's version.

The initial compatibility baseline freezes operation, schema and security fingerprints. Removal/rename, body/response shape, transport or security metadata changes fail until explicitly reviewed. Additive new operations/schemas can preserve existing fingerprints; the source inventory still requires conscious annotation review. This is intentionally stricter than a general semantic compatibility engine: even a harmless metadata correction can trigger it, and it does not prove behavioral equivalence. Never update the frozen baseline just to make CI green. A necessary existing-v1 change requires a documented owner-reviewed compatibility/version decision; breaking live consumers normally need a new API major/migration plan. This task establishes the first baseline; it does not approve future changes.

## TypeScript consumption and W1 safeguards

W1 imports only generated six-operation metadata and type-only request definitions from the canonical document. Its redacted `SessionView`/login classifiers and safe error parser remain deliberate projections rather than copies of all wire data. Hold-clear requires a factor code while ordinary step-up's factor is conditionally optional. Generated types do not replace runtime response validation.

No native bearer issuance/refresh operation or synthetic context probe was added to W1's runtime allowlist. Both app factories still instantiate a disabled transport, no live environment switch or fetch fallback. Cookie/CSRF remains same-origin, no-store, redirect-rejecting and memory-only; no browser bearer/refresh storage. Registry/revision/context IDs are partition hints, not grants. The shared package does not combine app session objects or NGO/Operations authority.

## Flutter integration preparation — no application implementation

`apps/mobile` remains reserved; no Flutter SDK, project, screen, shell, Dart package or generated runtime client is added. Keep that repository path rather than copying illustrative draft directories.

At the separately approved Flutter foundation, pin and test Flutter/Dart and a maintained generator (candidate: OpenAPI Generator's `dart-dio` profile) against this **same** versioned document. First generate only models for actually consumed schemas into a temporary output, review nullability/unions/date handling and error decoding, then check a reproducible bounded model subset into the mobile package if justified. Do not blindly register all operations, especially synthetic ones, or maintain parallel handwritten API definitions. Standard generators do not enforce custom `x-pwc` security metadata; the native adapter and negative tests must.

Native adapter acceptance:

1. Login/MFA completion has no session cookie, Authorization or browser provenance; credentials/preauth controls are explicit body proofs. A 202 MFA response is **not** an authenticated principal.
2. Later personal calls use exactly one revocable opaque Bearer credential, never cookie-plus-Bearer. Credentials are not JWTs and convey no NGO authority. Access lifetime is 300 seconds; refresh is a body-only credential, without access Authorization/cookie/browser provenance.
3. Use reviewed OS secure storage for refresh secrets, bounded in-memory access credentials, serialized single-use refresh and atomic replacement fenced by session/generation. Never persist secrets in preferences, ordinary cache, diagnostics or crash reports. On uncertain consumed refresh response, clear secrets and require re-login; no automatic refresh replay/grace.
4. Observe mobile 7-day idle/30-day absolute expiry. GET/status/list/refresh does not extend idle time; no keepalive heartbeat. Distinguish revocation/expiry, recovery holds, preauth, assurance and authorization.
5. Parse both error envelopes and non-JSON failure into the same safe taxonomy as web. Treat feature-disabled responses as unavailable/hidden, not successful integration. Reject mismatched checked contract artifacts; real server compatibility needs deployment/release acceptance.
6. Partition data by principal/logical session/explicit NGO/registry/revision/generation. On logout, context switch, revocation, hold/revision change: suspend private views, abort work, purge caches/drafts/proofs, and reject late responses. Revalidate grants backend-side, including focus/online transitions. No persisted capabilities or first-NGO fallback.
7. Use the checked examples and historical fixture profiles for future Dart decoding/negative tests. Placeholder secrets intentionally cannot authenticate; do not attempt OTP, issuance or refresh with them. Real secure-store/deep-link/TLS and Android/iOS lifecycle acceptance is still unperformed.

## Security and tenancy invariants

One personal identity, independent NGO relationships. Only backend-verified UUID context and current action-specific grants authorize access. Primary NGO administration never implies finance; Board/platform/staff never shortcuts into NGO-private data. Personal MFA/operation-bound assurance cannot escalate domain authority. Synthetic grants, probes and kernel-settings are not real workspaces, rosters, grant commands, finance or ORG-25. No identity/NGO authority is seeded by schemas/examples. Every example is synthetic, with inert secrets and reserved identifiers/domains; no operational credential is checked in.

Existing direct-HTTPS/cookie/origin/proxy-trust guards are unchanged. Live email, exact ingress/Host/Origin/CSRF acceptance, source-IP trust/abuse controls, recovery/rotation/lost-response ceremonies and deployment remain blockers, not problems to bypass for schema generation.

## CI and validation evidence

Backend CI retains Python 3.11/3.12 and PostgreSQL 16, dependency checks, Django/migration gates and the complete existing suite. It additionally installs optional contract tools, checks generated schemas/source/compatibility/examples, and selects the contract-instrumented test runner. Frontend CI additionally regenerates/checks TypeScript bytes before its existing strict checks/builds/production browsers. Nothing deploys or enables backend flags.

Local evidence on Python 3.11, PostgreSQL 16.2, Node 22.22.3/npm 10.9.8:

- OpenAPI 3.1 validation, deterministic generation/source inventory, frozen compatibility, all 70 checked examples and legacy key overlap: passed.
- Focused negative contract guards: passed (7 tests), including breaking removal/transport changes, malformed UUIDs, fabricated domain assurance and disabled endpoints.
- First instrumented full run exposed tooling assumptions about synthetic disabled-method precedence and valid registration payload prerequisites; corrected annotations/validators/tests, with **no runtime security change**. **Full rerun: 343/343 tests passed on actual PostgreSQL 16.2; 168 distinct route/method/status combinations checked by the wire validator.**
- Fresh npm locked install, generated type byte comparison, strict TypeScript/scoped formatting, **113 web tests**, both production builds: passed.
- Fresh production Chromium **11/11**: passed, including zero API calls, portal independence, RTL/320px/keyboard/axe checks. Sandbox used external Chromium 153 and its libraries; CI uses Playwright-managed Chromium. Browser binaries, PostgreSQL data, dependency environments, builds and logs are outside Git.
- npm audit: **0 reported vulnerabilities** at validation time, not a security certification. Backend dependency consistency, Django checks, no migration drift, migration application/check and the complete PostgreSQL regression run passed. Python 3.12 and managed-browser acceptance depend on actual GitHub runs, not this local Python 3.11 run.

## Follow-on scope and remaining blockers

This is **PWC-03C contract foundation**, not closure of every broader roadmap requirement. Shared cross-domain audit/event infrastructure, approved retention/privacy and immutable evidence conventions need their own bounded design/implementation task; existing auth/security/authorization events are preserved, not replaced. Private file authorization/storage/delivery/export primitives require approved ownership, scanning, expiration, download audit and storage contracts, and remain completely unimplemented here.

W2 live personal-auth integration, real email delivery, trusted HTTPS ingress and backend/frontend storage/rotation acceptance need separate approval. W3 needs real NGO eligibility/representative verification, REAL01–REAL04 authority activation and actual workspace/capability contracts. Flutter needs its own pinned foundation and native acceptance. No PR, production deployment, business API, privileged command or live authentication is authorized by completing this task.

## Integration-review checkpoint

See [PWC-03C integration review](../reviews/PWC-03C-API-CONTRACT-INTEGRATION-REVIEW.md) for corrections and current validation; the counts above record the original implementation checkpoint. Review adds global-security/protocol compatibility fingerprints without changing any existing operation/schema/security fingerprint or the canonical API. Generation now rejects compatibility failures before writing files. Example coverage requires each JSON success status and each request body; the wire validator rejects undocumented empty successes, matches JSON media types exactly, and enforces synthetic Cookie/Authorization Vary tokens.

Native integration clarification: clear all local credentials, private caches and pending proofs on logout even if the outgoing request fails, but never claim successful backend revocation without acknowledgement. Cancellation of an unsafe request or loss of its response does not prove that the server rolled back. Fence all late completions, do not replay consumed refresh/assurance/enrollment commands automatically, and use the separately accepted re-login/new-ceremony recovery path. HTTP GET retries, if later introduced, must be bounded and retain current-principal/context/contract checks; no retry may turn an unavailable/hidden endpoint into a fabricated successful workspace.
