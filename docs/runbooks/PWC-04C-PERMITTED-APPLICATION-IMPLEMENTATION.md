# PWC-04C — Permitted application implementation

**Date:** 27 October 2026 · **Baseline:** `444576d0e1848fc99ebfc92ae9bad150b2e0f8d6` (merged PR26).  
**Status:** Implemented bounded application features; **PWC-04C remains partial**. No real privileged workflow, new intake, deployment or next phase activated.

This is the operating/implementation record for code delivered in [PR27](https://github.com/salmansabir33/pwc-platform/pull/27), not another governance proposal. The [authorization package](../reviews/PWC-04C-IMPLEMENTATION-AUTHORIZATION-PACKAGE-v1.0.md) and [reviewer arrangements](../reviews/PWC-04C-GOVERNANCE-AND-REVIEWER-ROLE-ARRANGEMENTS.md) still record AUTH-01–09 as independently **PENDING**. Role-level arrangements are not technical signatures. Existing ADRs, E/GM/REAL registers, approved Design System and P0–P8 remain authoritative.

## 1. Actual delivered features and boundaries

| Surface            | Working implementation                                                                                                                                                                                                | Explicit limit                                                                                                                     |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Django/PostgreSQL  | Bounded normalized public registry; owner-isolated historical application workspace; latest two verification-purpose summaries, source-revision staleness; internal immutable submission packet validator             | No reviewer/nominee/NGO-private reader or privileged writer                                                                        |
| REST/OpenAPI       | Additive actual GET contracts, closed schemas, pagination/filtering, unavailable/auth/validation errors, TS/Dart generation and checked examples                                                                      | Historical v1 DTOs/operations remain frozen; no successful real command advertised                                                 |
| Both React portals | `/ngo-registry`: actual fixed public HTTP integration, classification/name/city filters, pagination, loading/empty/error, EN/UR and restricted-target exclusion                                                       | Four already-public fields only; not consent, legal verification or authority                                                      |
| NGO React          | `/application-history`: owner-history component and typed client, filtering, revision/stale-source states, confirmation/actual existing withdrawal followed by server reload, invalidation and late-response handling | Private transport remains default-disabled; component/gateway integration tested, **not live browser sign-in/admin functionality** |
| Operations React   | Same genuine public registry integration; existing controlled onboarding/review pages remain unavailable without fake queue rows/counts                                                                               | Officer registry, private review queue/details, nomination/invitation/audit readers remain gated                                   |
| Flutter            | Canonical DTOs and separate public-only HTTPS reader, registry screen with pagination, loading/empty/error/EN/UR; read-only historical workspace port/screen with scope purge and unavailable states                  | Public reader opt-in at build time; history not added to native personal transport. No mobile grant/admin/reviewer networking      |
| Tests/integration  | Actual React → restricted Vite proxy → Django → PostgreSQL browser test; owner-history/withdrawal wire tests; state/contract/client/widget negative tests                                                             | No mock result represented as proof of real privileged workflows, independent human vetting or production acceptance               |

No new model/table/migration is justified for these reads: existing 04A/04B persisted history and C3 snapshots are reused. All applied migrations and real/synthetic source restrictions are preserved. No speculative invitation, privileged permission bundle or real grant-source schema is installed before AUTH acceptance.

## 2. Public registry: exact networking exception

`GET /api/v1/directory/` returns **only** `id`, `name`, `city`, `classification`, the existing verified-workspace public projection. It does not widen publication fields or create a publication/consent approval. Provisional, pending, restricted and deactivated records are excluded **before** filtering/pagination. No total or private target metadata is returned.

- Optional `q`, `city`, `classification` (`registered`/`unregistered`), `cursor`; unknown/repeated parameters, GET bodies, controls and overlong inputs rejected.
- NFKC/casefold normalized search; page size at most 20; UUID keyset, signed filter-digest-bound cursor with one-hour maximum age. It is neither an authority token nor a snapshot guarantee. Restriction is re-evaluated each page.
- Persisted hashed-IP budget: 30 requests per 15 minutes for this route; bounded statement time, redacted 400/405/429/503 errors, `no-store`/`no-referrer`.
- Public authentication is deliberately absent: cookies, bearer strings, staff and held accounts do not expand the four-field projection.
- Browser adapter issues **only this exact relative GET**, `credentials: omit`, no bearer/CSRF, redirects rejected, no storage/cache/background refresh. It cannot send private paths, caller-defined endpoints or writes. Both apps load on explicit search, not automatically.
- Optional development proxy accepts **only** this exact path/query and a validated `http://127.0.0.1:<port>` backend target. It cannot forward `/auth`, controlled onboarding, registry history, descendant paths or arbitrary hosts.
- Original W1 **credentialed** `ApiClient`, factories and application config remain disabled. Frozen v1 global `web_network=disabled` records that original client; the **new operation's** explicit `client_network_exception` documents this bounded public-only reader. This assignment's permitted read integration is not W2/private networking approval.
- Native `PWC_PUBLIC_DIRECTORY_ORIGIN` is separate from `PWC_API_ORIGIN`, empty/default-off. The dedicated gateway accepts only an exact HTTPS origin and fixed public GET; rejects redirects/oversized/non-JSON/noncanonical payloads, carries no credentials and does not expand `PersonalApi`'s 22-operation allowlist. Invalid configuration fails closed. No actual device/provider acceptance is inferred from HTTP-fake/widget tests.

Existing public consent/publication operational/privacy gates still apply before real rollout. This is not permission to publish additional NGOs/data or seed real records.

## 3. Historical personal workspace and actual withdrawal

`GET /api/v1/registry/workspace/?kind=draft|claim&state=...&cursor=...` is an **owner-history** projection, not a private NGO workspace or membership discovery API.

- Existing `PWC_REGISTRY_ENABLED`, development/test profile, live personal session, direct HTTPS, transport separation, shared abuse budget and clear recovery hold are required. Default flags and staging/production denial remain unchanged.
- Reuses the existing transaction/User-first authentication boundary. Queries constrain `claimant` **before** pagination, cases or source references. Staff, legacy admin labels, synthetic grants and organization IDs cannot read another applicant's history.
- Default `kind=draft`; closed state filter; signed owner/kind/state-bound cursor, 20 applications per page, no total. Source history remains separate from legal NGO authority.
- Draft name/city/category are the owner's historical input, not an official public profile. **Claims always redact these three fields**; no join to the target organization's private/current profile, even if the target was previously public.
- Latest case per purpose, at most two/application, selected only from the same owner/source. Each has source revision and a computed `stale` flag; **not** a reviewer finding. `PWC_VERIFICATION_ENABLED=false` hides all case summaries and reports unavailability.
- `administration_available=false`, `intake_available=false` are fixed server values, not caller-selected capabilities. No roster, nomination, invitation token, private audit, finance or admin grant is returned.
- Owner can still call the **existing** `POST /registry/drafts/{id}/withdraw/` or `/claims/{id}/withdraw/` with the displayed revision. New self-service creation/edit/submission stays server-disabled. Current state/revision/owner are revalidated under locks; a duplicate/stale request returns 409 and creates no duplicate withdrawal event. Existing create receipts remain unchanged; no new receipt/idempotency policy is invented for withdrawal.
- React history gateway is explicit-injection-only, no ambient fetch/default enablement. It requires current scope, masks errors, checks DTOs, requires CSRF for unsafe cookie requests and purges on 401/403/409 or scope invalidation. No unsafe retry/optimistic success. After an uncertain withdrawal outcome, explicitly reload current history before taking another action. Browser confirmation does not confer authority.
- Flutter history is read-only and port-based; personal session/hold scope changes discard rows and late results. Actual native domain/history transport is deliberately unsupported. Both history screens explain missing administration/invitations rather than display fake memberships or approval success.

### Working backend workflow

With existing **synthetic test-only historical fixtures**, restore rollout policy (`PWC_LEGACY_ONBOARDING_TEST_EXERCISE=false`), authenticate the owner, fetch workspace → inspect submitted case/source revision → withdraw displayed historical draft revision → fetch workspace again. State is withdrawn, revision increments, case is stale, one withdrawal audit event exists and no NGO access/grant appears. Replaying old revision fails; a rival/staff principal cannot read or withdraw it. This works over actual Django HTTP/PostgreSQL, **not** a mocked persistence layer. It does not reopen applicant intake in development or production.

## 4. Nonwriting controlled submission preparation

`organizations.controlled_preparation.prepare_submission` accepts existing record/snapshot/attestation objects and expected revision; returns an immutable minimized packet containing only IDs/revisions, recipient-resolution flag and fixed `command_available=false`.

It validates initiator/recorder coherence, current exact snapshot/revision, permitted preflight state, exactly two unique eligibility/mandate attestation lanes, same-snapshot/attestor references, bounded opaque handles, aware/nonfuture examination timestamps and structural organization fields. It performs **no queries/writes**, does not accept uploads or personal documents and does not declare evidence authentic, humans independent or nominees verified. A nullable nominee is marked unresolved; the pending invitation/account-order decision is not silently selected. This helper is not wired to the unavailable controlled command adapter and cannot authorize submit/review/invite/grant.

## 5. Local execution and browser integration

Use the existing local setup runbook and PostgreSQL; no SQLite substitution. Use only a disposable database named `pwc_synthetic_*` and `PWC_ENVIRONMENT=test` for the public E2E seed. The guarded seed creates 23 explicitly named **Synthetic Directory NGO** public projection rows and two restricted rows; **no users, officers, invitations, claims or grants**. Never run it on a real dataset.

```bash
# Existing trusted local environment: DB settings, PWC_ENVIRONMENT=test,
# DJANGO_SECRET_KEY supplied outside source control.
export PYTHONPATH="$PWD/apps/backend"
.venv/bin/python apps/backend/manage.py migrate --noinput
.venv/bin/python tests/end-to-end/seed_public_directory.py
npm ci --ignore-scripts
npm run check

# Starts only public fixture API + both production-built portal previews;
# Playwright owns and tears down these child servers.
PWC_PUBLIC_API_TARGET=http://127.0.0.1:8000 \
PWC_E2E_PYTHON=.venv/bin/python npm run test:browser
```

For interactive public-only development: run Django on loopback port 8000; run `PWC_PUBLIC_API_TARGET=http://127.0.0.1:8000 npm run dev:ngo` (or `dev:ops`) and open `/ngo-registry`. Remote preview uses an exact `PWC_PREVIEW_HOST`; browser requests stay relative, never browser localhost. Omit the proxy setting without a backend and the screen reports unavailable—no fallback/mock data.

Flutter public integration, only with an independently acceptable **public API origin**, is opt-in via `--dart-define=PWC_PUBLIC_DIRECTORY_ORIGIN=https://...`. This does not enable native personal/history/domain transports. Without it, the public screen explicitly reports unavailable. Native history transport has no enable switch in this change.

## 6. Validation ledger

Local: Python 3.11.2, actual PostgreSQL 16.2, Node 22.22.3/npm10.9.8 and Chromium153. Disposable tools/libraries are excluded from source and shipped dependencies.

| Exact command / working directory                                                                                                                                                        | Observed result                                                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `.venv/bin/pip install --require-hashes -r requirements-ci.lock`; `.venv/bin/pip check` (root)                                                                                           | Pinned install; no broken requirements                                                                                                       |
| `.venv/bin/python -m scripts.python_lock --check`                                                                                                                                        | 12 runtime / 33 CI pinned hash locks passed                                                                                                  |
| `.venv/bin/python apps/backend/manage.py check`                                                                                                                                          | No issues                                                                                                                                    |
| Same prefix `makemigrations --check --dry-run`, `migrate --plan`, `migrate --noinput`, `migrate --check`                                                                                 | No drift; fresh PostgreSQL application succeeded; no pending migrations                                                                      |
| `.venv/bin/python -m contracts.check --check` (root with backend PYTHONPATH)                                                                                                             | Inventory/source/frozen compatibility/OpenAPI3.1/security/checked examples passed                                                            |
| `../../.venv/bin/python manage.py test --testrunner contracts.testing.ContractRunner --verbosity 1` (`apps/backend`)                                                                     | **471 tests passed /508.222s /300 observed route-method-status combinations** (earlier checkpoint468/515.921s/299 also passed)               |
| Same test command, explicit `organizations.test_workspace organizations.test_directory organizations.test_controlled_preparation` labels                                                 | Final targeted **21 tests passed** /15.481s /19 observed combinations                                                                        |
| `.venv/bin/python -m unittest discover -s tests/tooling -v`                                                                                                                              | 6 passed                                                                                                                                     |
| `.venv/bin/ruff check apps/backend scripts tests/tooling`; scoped existing `ruff format --check`                                                                                         | Passed; six scoped files formatted                                                                                                           |
| `.venv/bin/python scripts/security_checks.py`; `git diff --check`                                                                                                                        | 0 tracked-file findings; no whitespace errors                                                                                                |
| `npm run check`                                                                                                                                                                          | Token/font parity, TypeScript, formatting, **158 tests**, both portal builds passed                                                          |
| `npm run contracts:types:check`; `npm audit --audit-level=low`                                                                                                                           | Types in sync; 0 NPM vulnerabilities                                                                                                         |
| `LD_LIBRARY_PATH="$PWD/.cache/al2023/lib" PLAYWRIGHT_CHROMIUM_EXECUTABLE=/tmp/chromium PWC_PUBLIC_API_TARGET=http://127.0.0.1:8000 PWC_E2E_PYTHON=.venv/bin/python npm run test:browser` | **24 passed /37.7s**; two actual PostgreSQL-backed registry journeys; private history stays gated; EN/UR/axe/reflow/keyboard suite preserved |
| Local Dart WASM `dart_style` formatting at language3.9.0                                                                                                                                 | Existing pinned formatted source matched; changed source formatted. **Not** a local Flutter compile/widget/device pass                       |

Local Flutter/Dart SDK, Android/iOS SDK and Docker are absent. Hosted existing pinned Flutter3.35.7/Dart3.9.2 performs authoritative generation/format/analyze/widget and Android debug checks; final immutable SHA, commands, counts and CI links are recorded in PR evidence. No physical-device, TalkBack/VoiceOver/manual Urdu, production TLS/provider/operational sign-off claimed.

Initial local fixture tests exposed invalid test hold metadata/OneToOne reuse and were corrected, not bypassed. Initial Chromium launch lacked shared libraries; excluded local runtime setup repaired and all24 passed. Initial hosted mobile compilation/analyzer caught shared `PwcBadge` call shape and analyzer/style issues; corrected in code and the next pinned analysis/widget run passed. Final-head results, not superseded failed runs, govern handoff.

## 7. Still-gated operations and blocking acceptance

| Unavailable functionality                                                                             | Blocking contracts / accountable technical functions                                                                                              |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Officer provisioning, founding issuer/executor/confirmer, platform privilege                          | AUTH-01/02/05; designated operations, security specialist, backend/database architect; valid appointment source and independence                  |
| Real onboarding submit/review/approve/reject/return, private review queue/case/nomination read        | AUTH-02/04/05/08; exact command/reader matrix, assurance, restricted writer, privacy and evidence contract                                        |
| Sensitive invitation issue/reissue/acceptance and durable consent                                     | AUTH-04/06/07/08; precise recipient/account order, proof/token/receipt/clock/privacy acceptance                                                   |
| Primary/ordinary admin permissions, grant issue/revoke/replace/recovery, private member/admin listing | AUTH-02/03/04/05/07/08; exact capabilities, GM06, issuer/quorum, real provenance, lock graph and reader scope                                     |
| NGO-private audit, notices, real evidence/reference intake/publication changes                        | AUTH-08 and affected source/reader contracts; joint legal/privacy with security/operations                                                        |
| Credentialed browser and native domain/history networking and real release                            | Existing W2/W3/native integration gates plus AUTH-09/A/U/R; exact origins/CSRF, provider/device/manual accessibility, operations/security/privacy |

Merging this implementation is not signing any pending AUTH/E/GM/REAL contract. Do not label all04C complete or infer actual privileged-command tests from public/owner-history tests. Next work stays within04C: obtain acceptance of a precise excluded command/reader contract before implementing that affected slice; meanwhile retain existing default-deny behavior. Do not begin04D/P5–P8.

## 8. Android advisory remediation found during acceptance

The first complete hosted Android job at `0543d91` **compiled both debug variants**
but correctly failed the resolved-runtime audit: existing Guava33.4.8-android
matched newly published [GHSA-xxph-c9ww-hj94](https://github.com/advisories/GHSA-xxph-c9ww-hj94)
(native Java deserialization memory exhaustion). Upstream identifies33.7.2 as
fixed and [explicitly publishes33.7.2-android](https://github.com/google/guava/releases/tag/v33.7.2).
The existing application runtime constraint is minimally raised to33.7.2-android,
with the advisory documented in Gradle. This changes no Flutter dependency,
network permission, signing or API authority. No suppression, allowlist or audit
weakening is introduced. Final Android compilation and actual selected-coordinate
OSV evidence must pass on the patched immutable PR head. Local Android SDK remains
absent; no local native build is claimed.

## 10. Authenticated workspace follow-on — 28 October 2026

Baseline: merged PR27 / `5bee4d8133c9bb75eb768603e3d63eeb6a6424a0`.
This is additive implementation, not authority to reopen intake or activate W2.

### Delivery matrix

| Area | Classification | Implemented behavior / precise boundary |
| --- | --- | --- |
| Public NGO registry, both React portals | Fully functional within existing public-read exception | Existing fixed public reader, filters, signed pagination, errors, EN/UR; exercised against actual PostgreSQL again. No publication/consent expansion. |
| Owner point reconciliation | Backend functional; shipped browser integration gated | New GET `/api/v1/registry/workspace/drafts/{pk}/` and `/claims/{pk}/`. Exact owner-filtered lookup, same locked session/user, recovery/config/transport gates, no query/body, no-store, bounded minimized current projection. Missing/foreign IDs indistinguishable. Claims never join private target names. |
| Personal session composition | Backend functional; shipped browser integration gated | Explicit injected-only `PersonalWorkspaceSession`: real `me`, fresh CSRF bootstrap after personal scope selection, memory-only CSRF, verified-contact/hold restriction, scope purge and logout. No ambient fetch, environment enable switch, login/MFA bypass or NGO context inferred. Default application route has no adapter. |
| Owner history/withdrawal React | Backend functional; shipped browser integration gated | Shared accessible confirmation dialog, revision-bound original withdrawal, no optimistic success, no automatic replay, exact-record reconciliation independent of filters/page, source and verification revisions. Scope/locale/unmount discard late data. Unknown result remains unresolved after an unchanged read; filter changes do not discard uncertainty. |
| Operations rollout policy | Backend functional; shipped browser integration gated | Fixed authenticated GET of existing generic `controlledRequirements`; strict closed constant validation. Displays actual policy version, server source and blockers when injected; default unavailable. This is NOT a capability response, private verification summary, queue, audit reader or reviewer authorization. No invented counts or decisions. |
| NGO information/admin/representatives/nonfinance permissions/invitations/appointments | UI-state preparation | `/administration`: EN/UR unavailable/no-context/restricted/expired boundaries, no private profile/roster/grant/token payload or mutation buttons. Public organization information remains in separate approved registry. Invitation acceptance is explicitly distinct from grant activation; 72-hour maximum remains. |
| Flutter history/admin | UI-state preparation for private domains | History state filter forwarded to optional read-only port, case/source revision display; new EN/UR administration boundary states/route/tests. No new native networking or personal allowlist operation. Generated detail DTOs do not authorize native transport. Existing public fixed HTTPS reader unchanged. |
| Privileged writers and readers | Privileged unavailable | Officer provisioning, appointment/grant activation, review queues/decisions, recipient-bound invitation acceptance, private administration, finance/signatory/support/alliance powers remain deny-default. No new table or migration. |

### Lost-response semantics

The point read returns `WorkspaceDetail.application` plus the existing false administration/intake flags and verification availability. It is **not** a withdrawal command receipt, an idempotency result, proof of who caused a state change, or proof that an in-flight command will not commit. An unchanged old revision keeps the UI outcome unresolved and does not offer automatic resend. A withdrawn state or later revision can resolve the stale snapshot. Normal CAS/state checks still prevent duplicate withdrawal events. The original withdrawal schemas and audit behavior are unchanged.

### Genuine executable synthetic integration

`tests/end-to-end/auth-harness/` is a separate, nonshipped Vite entry; neither app imports it. `authenticated-workspace.py` requires explicit test environment, PostgreSQL and a `pwc_synthetic_*` disposable database. It creates/drops a separate test database, constructs historical fixtures using preserved tests, then closes intake during browser execution. Browser cookies originate from actual Django web-login fixtures. No fixture HTTP endpoint, bearer bridge, development proxy trust rule or production credential toggle is added.

A temporary TLS certificate covers **synthetic** `.invalid` portal aliases. The WSGI server recognizes HTTPS only on actual TLS sockets, with exact port-qualified portal origins. Playwright trusts the self-signed certificate only in these test contexts. The test performs real React → direct TLS → Django → PostgreSQL requests for both public portals, authenticated policy, owner history, cross-owner denial, CSRF failure/purge/explicit session recheck (no mutation retry), deliberate loss of an actual successful withdrawal response, exact-record reconciliation despite an excluding filter, stale source revision, duplicate conflict, wrong-portal cookie denial and logout/session invalidation. Final database checks require exactly one withdrawal event and no authority grants. Nothing here proves production certificate/provider/ingress acceptance.

Reproduce after installing locked dependencies and setting the existing test database environment:

```sh
npx vite build --config tests/end-to-end/auth-harness/vite.config.ts
python tests/end-to-end/authenticated-workspace.py
# Normal regression (run from backend directory, or name all four apps):
python apps/backend/manage.py test accounts access organizations contracts --testrunner contracts.testing.ContractRunner --noinput
npm run check
npm run contracts:types:check
npm run test:browser # with existing PWC_PUBLIC_API_TARGET and synthetic public seed
```

The frontend CI job runs the direct-TLS integration as well as normal browser regression; it uses no new dependency or workflow permission. Browser tests and synthetic component/widget tests remain separate evidence categories.

### Exact remaining gate / evidence discipline

ADR-0003 §4 still requires independently accepted evidence for **both exact live portal hosts**: TLS/certificates, Host/portal and cookie/session/MFA/CSRF binding, proxy/IP/NAT/provider configuration and ingress behavior. HTTP Compose or Arena's TLS-terminating preview is expressly not the accepted live authenticated ingress. AUTH-01–09 remain pending; E/GM/REAL approvals are not inferred. Therefore credentialed shipped web transport remains disabled, as does private native-domain networking. No live reviewer/admin success, physical device/native Urdu rendering, manual accessibility, production deployment or completion of 04C is claimed.

### Follow-on validation at implementation head

Local actual PostgreSQL full regression: **474 tests passed**, **310 distinct route/method/status wire combinations** (496.850 seconds). The new workspace/contracts subset also passed 28 tests / 84 wire combinations. An earlier full run correctly caught the two missing new success examples; examples were added and both the targeted and complete suites rerun successfully (no suppression).

`npm run check` passed: tokens, TypeScript, formatting, **172 unit/component tests**, both production builds. Canonical OpenAPI/security/example/source checks and TypeScript generation drift check passed. Production-bundle browser regression: **26 passed**, no failures/skips, including the two new unavailable-state routes at 320px with EN/UR RTL and automated axe checks. The separate genuine direct-TLS authenticated synthetic workflow passed again; its assertions are not counted as the 26 production-bundle tests. npm audit reported zero vulnerabilities. Python dependency consistency, Django system/migration drift/application checks passed; no model migration was introduced.

Local Flutter/Android SDKs are absent; WASM Dart formatting is only preparation, not Flutter analyzer/build/device proof. Hosted checks on this new branch must supply the authoritative pinned Flutter/Android results. Prior PR27's results are not attributed to this implementation. Human Urdu, physical-device/native rendering, manual accessibility and live ingress/provider approvals remain outstanding regardless of automated results.
