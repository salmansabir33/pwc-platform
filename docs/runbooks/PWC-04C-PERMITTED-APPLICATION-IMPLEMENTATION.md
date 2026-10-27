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
