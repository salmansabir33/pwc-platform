# PWC-02F — Environment, API and security tooling

Date: 26 October 2026. Scope: Roadmap v2.0 PWC-02F development environment contract (Django/Python/PostgreSQL matrix, migrations/CI, formatter/linter policy, synthetic fixtures), plus the assigned API/security reproducibility checks. Not staging deployment (PWC-09B), real-user activation or authority development.

## 1. Existing foundations and preservation

Read [AGENTS](../../AGENTS.md), [roadmap](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), [authentication ADR](../decisions/ADR-0001-authentication-and-recovery.md), [authorization ADR](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), [web ADR](../decisions/ADR-0003-web-frontend-architecture.md) and [proposed ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md). Historical scaffold/session-branch descriptions do not supersede merged implementation or the assigned Arena branch. ADR-0004 stays PROPOSED; GM01–GM12 and REAL01–REAL04 are not closed.

Reuse, do not replace: the [local setup](LOCAL-SETUP.md), [03C canonical API](PWC-03C-SHARED-API-CONTRACTS.md), [03B synthetic context](PWC-03B2-CONTEXT-ENFORCEMENT.md), [W1 web](PWC-W1-WEB-FOUNDATION.md), [03D Flutter](PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and native/security runbooks. Auth contracts, registered operations, grant bundles, migrations, database guards, public projection fields, UI networking and application dependencies are unchanged. Settings/source fingerprints intentionally change for configuration parsing; canonical OpenAPI wire schemas/compatibility/generated clients do not.

## 2. Supported tools and reproducibility boundary

| Surface              | Contract                                                                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend              | Python 3.11 and 3.12; Django 5.2.18, DRF 3.18.3, psycopg 3.3.6; PostgreSQL 16; UTC; primary READ COMMITTED for synthetic authority                                                                                                     |
| Python quality tools | Build/test-only Ruff 0.17.2, coverage.py 7.17.0 in `requirements-tooling.txt`; not added to runtime image                                                                                                                              |
| Web                  | Node 22.22.3 (`.nvmrc`), npm 10.9.8 (`packageManager` and CI bootstrap); existing exact workspace pins and `package-lock.json`; React 19 / TypeScript 5.9.3 / Vite 8.3.5                                                               |
| Mobile               | Flutter 3.35.7 / Dart 3.9.2, exact upstream revision `adc901062556672b4138e18a4dc62a4be8f4b3c2`; committed resolver-produced Pub lock and enforced hashes; JDK 17, Android compile/target 36, build-tools 35.0.0 and NDK 27.0.12077973 |
| CI                   | Ubuntu 24.04 runner label; immutable action commit refs, contents-read permissions, checkout without persisted Git credentials; bounded jobs and cancellation of superseded same-ref runs                                              |

Python source requirements remain exact pins in backend, contract and tooling files. `python -m scripts.python_lock` retrieves **actual non-yanked release SHA256 hashes from PyPI HTTPS metadata**, writing runtime `apps/backend/requirements.lock` and combined `requirements-ci.lock`. No guessed checksums. Runtime Docker uses only its runtime lock; developer/CI install uses the combined lock. `--check` is offline source/specification/hash-format drift validation; pip `--require-hashes` checks downloaded bytes. Regenerate deliberately, review source+hash diff, install on both supported Python versions and rerun advisory/tests. Do not edit generated hashes or replace them with one machine's installed-package list.

`npm ci --ignore-scripts` enforces the checked lock/integrity; do not run audit fix blindly. Flutter uses existing `pub get --enforce-lockfile`; no second resolver/client/schema system. Android app and harness APK SHA256 values are printed immediately after each successful build, before the harness overwrites the same output path. These are separate builds; the harness is not a device test or signed production artifact.

Limits: image tags `postgres:16`, local `postgres:16-alpine`, Python development Docker base and Ubuntu runner images receive upstream patch updates; Python patch versions/Android platform-tools are not bit-for-bit hermetic. SDK archive SHA256 verification remains the documented Flutter limitation; the action uses official HTTPS and checks the installed revision. PyPI metadata hashes and action SHAs do not constitute independent publisher identity/signature attestation. No production container/ingress/OS/CocoaPods certification is implied.

## 3. Configuration contract

`apps/backend/config/environment.py` validates before settings are applied. Exceptions name the invalid variable only: never JSON contents, passwords, origins with credentials or key material. Syntax errors fail startup, not silent boolean coercion. `override_settings` in synthetic tests still exercises request-time auth/authorization failures; environment validation does not replace those guards.

| Variable/group                                                                | Development / test                                                                                                                          | Staging / production readiness profiles                                                                                                                     |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PWC_ENVIRONMENT`                                                             | Exact `development` (default) or `test`                                                                                                     | Exact `staging` or `production`; label is not approval                                                                                                      |
| `DJANGO_SECRET_KEY`                                                           | Required by settings; environment supplied                                                                                                  | At least 50 characters and not known placeholder/test-only/example markers. This is a minimum check, not entropy certification; use managed random secrets. |
| `DJANGO_DEBUG`                                                                | Exact 0/1; default 0; example explicitly uses 1 locally                                                                                     | Must be 0                                                                                                                                                   |
| `DJANGO_ALLOWED_HOSTS`                                                        | Nonempty explicit hostname/IP list, default localhost/127.0.0.1; no wildcard, suffix, URL, path or port                                     | Explicit non-placeholder/nonloopback hosts required; actual canonical DNS/certificates need independent acceptance                                          |
| `DB_NAME/USER/PASSWORD/HOST/PORT`                                             | Existing pwc/pwc/empty/localhost/5432 defaults; example instructs password replacement                                                      | Explicit name/user/host, password at least 16 characters, no known placeholders; port 1–65535                                                               |
| `DB_SSLMODE`, `DB_SSLROOTCERT`                                                | Closed libpq mode, default `prefer`; optional CA path. Local CI may use non-TLS disposable PostgreSQL.                                      | `verify-full` plus nonempty CA certificate path; connectivity/certificate readability/name validation require actual DB tests, not just this parser         |
| `PWC_AUTH_FLOWS_ENABLED`, `PWC_AUTH_SESSIONS_ENABLED`, `PWC_AUTH_MFA_ENABLED` | Exact 0/1, separately default off; isolated synthetic tests only under existing contracts                                                   | All must remain 0; no real-user activation switch authorized                                                                                                |
| `PWC_SYNTHETIC_AUTHORIZATION_ENABLED`, `PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED`   | Separate default-off flags; existing attested principal/tenant/batch, database name and grant/expiry restrictions remain                    | Both must remain 0                                                                                                                                          |
| `PWC_AUTHORIZATION_ENVIRONMENT`                                               | `disabled` default, or existing `synthetic_test`/`synthetic_development`; runtime additionally checks DB name and attestations              | Must be `disabled`; no real mode exists                                                                                                                     |
| Delivery                                                                      | Synthetic hard-coded runtime mode; any supplied `PWC_AUTH_DELIVERY_MODE` must say synthetic                                                 | No SMTP/provider activation; environment cannot opt into live delivery                                                                                      |
| `PWC_AUTH_PORTALS`                                                            | JSON object: exact HTTPS origins → distinct `ngo_web`/`pwc_ops`; no path/trailing slash/query/fragment/userinfo/wildcard/control characters | Still inactive because sessions must be off; production host/origin ownership not approved by parsing                                                       |
| `PWC_AUTH_LINK_ORIGIN`                                                        | Bare exact HTTPS origin; default `https://pwc.invalid`                                                                                      | Inactive synthetic setting, not evidence of real mail/app-link ownership                                                                                    |
| Delivery/MFA key rings                                                        | JSON objects of nonempty string values; reject duplicate keys, arrays/null and malformed JSON                                               | Managed injection only if later separately approved; no keys enabled here                                                                                   |
| `PWC_AUTH_ABUSE_KEY/SESSION_KEY/MFA_PROOF_KEY`, active-key IDs                | Existing request-time cryptographic length/key-ring/independence checks still apply when synthetic features run; empty while off            | No plaintext defaults or fallback to Django secret; flags remain off                                                                                        |

No environment-controlled trusted-proxy/forwarded-host/scheme settings are added. `SECURE_PROXY_SSL_HEADER` remains None, forwarded host/port remain false. Staging/production profiles redirect HTTP at the Django boundary; secure host-only session/CSRF cookies remain enabled in all profiles. No-referrer, nosniff and DENY framing defaults are explicit. HSTS policy is **not** self-approved: `check --deploy` warnings and rollout/preload decisions remain a release gate.

Profile tests use fabricated values and no database connection. Do not copy their fake password/domain into a deployment. Configuration passing is not a credential-strength audit, direct HTTPS proof, production database-role audit or rollout authorization. Mislabeling a production process as development is an operator trust risk; deployment must explicitly select/verify the intended profile.

### Secrets and logging conventions

Copy `.env.example` only for local development; `.env` is ignored, Django does not automatically load it, and the source-control check rejects tracked `.env`/`.env.*` except `.env.example`. No real credentials/data in fixtures, reports, GitHub output, screenshots or PR text. Generate independent synthetic keys by the existing auth runbooks, inject via trusted shell/secret manager, never reuse CI example strings in a deployed service. Production migration/DB owner/fixture credentials must not be issued to HTTP workers; restricted-role acceptance and restore/rotation remain operational gates.

Do not dump `env`, Django settings, HTTP bodies, credential/key JSON, private documents or raw exception objects into diagnostics. Tracked-file checks report paths and pattern labels only. Coverage/JUnit reports contain synthetic code/test evidence, not request/response captures. Seven-day CI report artifacts are not a legally approved business-data retention policy. The scanner is deliberately limited to known GitHub/AWS/private-key markers, env files and machine caches; it is not a high-entropy/history/incident scanner or assurance that no credential ever leaked. A genuine finding requires independent revocation/rotation and history review, not just deleting a file.

## 4. Setup and local validation

Use only synthetic accounts and disposable PostgreSQL. Do not substitute SQLite. From root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --require-hashes -r requirements-ci.lock
python -m pip check
python -m scripts.python_lock --check
python scripts/security_checks.py
python -m unittest discover -s tests/tooling -v
ruff check apps/backend scripts tests/tooling
ruff check --select E4,E7,E9,F apps/backend/config/environment.py apps/backend/accounts/test_environment.py scripts/security_checks.py scripts/python_dependency_review.py scripts/python_lock.py tests/tooling
ruff format --check apps/backend/config/environment.py apps/backend/accounts/test_environment.py scripts/security_checks.py scripts/python_dependency_review.py scripts/python_lock.py tests/tooling
```

Existing Python receives a correctness lint baseline (E9/F63/F7/F82), not an unrelated mass reformat. New PWC-02F Python receives E4/E7/E9/F plus Ruff formatting. This is an explicit incremental policy; no broad legacy-style or mypy pass is claimed. Backend type safety remains Django/runtime/contract tests, not a fictitious global static-type gate. Web keeps existing strict TypeScript/Prettier; Flutter keeps analyzer/Dart format. No arbitrary coverage threshold is invented as a product/security approval.

Load only your own trusted `.env` as in LOCAL-SETUP, choose `PWC_ENVIRONMENT=test` for tests, start PostgreSQL 16, then:

```sh
cd apps/backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python -m contracts.check --check
coverage run --source=accounts,access,organizations,config,contracts manage.py test --testrunner contracts.testing.ContractRunner --verbosity 2
coverage xml -o coverage.xml
coverage report
cd ../..
python scripts/python_dependency_review.py
```

The advisory script queries all 33 exact runtime/contract/tool versions through OSV HTTPS. Any finding, malformed/incomplete/error result or network failure fails the check; no allowlist or automatic suppression. A result means no currently returned findings for those exact versions, not absence of vulnerabilities. In restricted sandboxes run it in GitHub Actions, never bypass TLS or fabricate zero results.

For changes to settings/configuration/contracts, use existing `python -m contracts.generate` from backend, review `source-lock.json` and rerun `contracts.check --check`. The new environment module is included in canonical source fingerprinting. Frozen wire/security/version fingerprints must not be reset to accommodate drift. No second API schema system or proposed ADR-0004 endpoints enter OpenAPI.

Web:

```sh
npm install --global --ignore-scripts npm@10.9.8
npm ci --ignore-scripts
npm audit --audit-level=low
npm run contracts:types:check
npm run check
npx playwright install --with-deps chromium
npm run test:browser
```

113 existing unit/contract/config/UI tests and the real browser suite cover disabled networking, no browser bearer transport, separate portals, context fences, origin/preview-host restrictions and responsive RTL/accessibility specimens. Vitest writes `coverage/web-junit.xml`; Playwright writes `coverage/browser-junit.xml`, outside its cleared output directory. These are **test results, not web line-coverage reports**. Backend XML and Flutter lcov measure lines, not sufficient security/path coverage. Record failed/skipped/unavailable checks separately; neither coverage percentage nor mocks prove isolation.

Mobile: keep the [03D pinned commands and native gates](PWC-03D-FLUTTER-MOBILE-FOUNDATION.md). CI runs locked Pub resolution, strict format, canonical mobile generation, analyzer, `flutter test --no-pub --coverage`, hosted-package license/OSV review, actual Android app/harness builds and selected-runtime Maven advisory review. No mobile source/regeneration is necessary here. `PWC_API_ORIGIN` defaults empty (network disabled); only an explicitly approved bare HTTPS origin enables existing personal API calls. Native secure-storage, refresh rotation, lifecycle/late-response protections and English/Urdu tests remain unchanged. Real NGO contexts remain unavailable.

## 5. CI map and reports

| Workflow | Gates / report                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Backend  | Python 3.11/3.12 + PostgreSQL 16, hash-locked install, pip consistency, canonical OpenAPI/source/frozen compatibility/example checks, Django checks, migration plan/drift/apply/check, complete contract-instrumented regression suite and XML line coverage. Once on 3.12: lock drift, tooling negatives, tracked-file/action checks, lint/format, Python OSV review. No duplicate advisory/lint job per Python version. |
| Web      | Exact Node/npm, locked no-script install, npm audit including dev tools, generated TypeScript byte check, strict quality/unit/production builds, managed Chromium actual browser tests, JUnit reports.                                                                                                                                                                                                                    |
| Flutter  | Existing source/Android jobs; push trigger now supports all Arena feature branches rather than a stale single task branch. Path filters remain; source and APK revision checks, coverage and per-build SHA256 evidence added.                                                                                                                                                                                             |

Workflows use push/PR triggers for checkpoint and integration evidence; superseded same-ref runs cancel. Push and PR events can both run at PR opening; they are independent checkpoint/merge-context evidence, not an added competing test pipeline. Contents permission is read-only, no deployment environment/secrets or `pull_request_target`, action references immutable, credentials not persisted. Artifacts use fixed scoped report paths and seven-day retention; no entire workspace/cache/vault/trace dumps. Public dependency metadata is not a secret.

No CI deploy, database seeding with real NGOs, granting authority, email provider integration or live W2 networking. CI image/action/registry/platform drift and endpoint availability can fail jobs; investigate rather than removing the gate. Updating a pin requires a real resolver/hash/regression pass. No automatic merge or privileged bot writer.

## 6. HTTPS and deployment-readiness gate

ADR-0003 requires canonical exact portal hosts, same-origin browser `/api/` routing, backend-observed correct canonical Host/scheme/origin, verified TLS upstream to restricted backend ingress, and safe source-IP/abuse controls. Browser code must not call sandbox localhost for another service. Local Compose/runserver/static previews do not prove that topology; auth uses direct HTTPS and refuses trusted-proxy flags. No proxy settings, CORS bypass or CSRF trust wildcard are activated here.

Before any approved live integration: demonstrate both exact portal hosts' TLS certificates/upstream hostname verification, peer-restricted ingress, spoofed forwarded headers/direct-backend rejection, cookie/CSRF/Origin/session/hold/refresh behavior, no API caching/SPA fallback, correct client-IP trust and shared-NAT abuse tests. If the actual ingress requires trusted termination, obtain the separate reviewed extension; do not work around rejection by weakening direct HTTPS. Include `manage.py check --deploy` against real intended settings, HSTS rollout, restricted database roles/TLS/restore, secret rotation, private storage, actual provider and operational/privacy approvals. Parsing a production profile or a successful debug APK is not this acceptance.

See [integration review](../reviews/PWC-02F-ENVIRONMENT-TOOLING-INTEGRATION-REVIEW.md) for executed results and unresolved limitations. Stop after PWC-02F; no privileged commands, onboarding, finance or production module is started.
