# PWC Platform — Initial M1 Repository

Independent repository for the Pakistan Welfare Club digital ecosystem (Faisalabad pilot).

**Status:** Initial engineering scaffold; not a completed application. PWC planning choices remain provisional. No production deployment is configured.

## Modules

- `apps/backend`: Django REST API, shared identity, tenant-owned organization models, public projection tests.
- `apps/mobile`: Flutter 3.35.7 / Dart 3.9.2 personal identity and security foundation; actual-project CI and Android debug builds, with separate native-device acceptance gates.
- `apps/ngo-web`: independent React/TypeScript/Vite W1 foundation; no live authentication or NGO workflows.
- `apps/pwc-ops`: separately built W1 operations shell; no operational authority or business tools enabled.
- `docs/product`: reference planning documents.
- `docs/decisions`: architectural decisions and outstanding sign-offs.
- `infra`: local PostgreSQL and backend dev Docker configuration.

## NGO registry and claims (PWC-04A)

The [04A runbook](docs/runbooks/PWC-04A-NGO-REGISTRY-AND-CLAIMS.md) describes default-off claimant-only draft/claim APIs, private provisional permissions, public-only matching and ORG-01/02 contract-tested web/mobile components. Real intake, reviewer decisions, NGO authority and live registry clients remain disabled. See [the integration review](docs/reviews/PWC-04A-NGO-REGISTRY-INTEGRATION-REVIEW.md) for tests and remaining gates.

## Web foundation (W1)

The two portals use a shared npm workspace, design primitives and network-disabled API infrastructure. See [the web foundation runbook](docs/runbooks/PWC-W1-WEB-FOUNDATION.md) for Node installation, independent dev/build commands, tests and W2/W3 security gates. No production deployment or live login is enabled.

## Environment and security tooling

See [PWC-02F environment/tooling](docs/runbooks/PWC-02F-ENVIRONMENT-AND-SECURITY-TOOLING.md) for strict configuration profiles, Python hash locks, CI/security/quality commands and deployment gates. Staging/production readiness profiles keep synthetic/auth features disabled; configuration validation is not rollout approval.

## Development setup

Prerequisites: Python 3.11/3.12 and PostgreSQL 16, or Docker Engine with Compose v2. See [the full local setup runbook](docs/runbooks/LOCAL-SETUP.md) for environment loading, tests, troubleshooting and remote previews. Dependencies are pinned in `apps/backend/requirements.txt`.

### Docker

```bash
cp .env.example .env
# Replace placeholder secrets in .env with strong development-only values.
docker compose up --build -d db
docker compose up --build -d backend
docker compose logs -f backend
```

Compose applies migrations before startup. Open `http://localhost:8000/api/v1/health/` (liveness only). The database starts empty; no accounts or NGO authority are assigned automatically. Rebuild after host code changes; there is no source bind mount.

### Native Python (with a local PostgreSQL database)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements-ci.lock
python -m pip check
cp .env.example .env
# Edit development secrets; Django does not load .env automatically.
set -a
. ./.env
set +a
export DB_HOST=127.0.0.1
# Start local PostgreSQL or: docker compose up -d db
cd apps/backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --verbosity 2
python manage.py runserver 127.0.0.1:8000
```

The development database role needs `CREATEDB` for Django tests; production application roles should not have it. The runbook includes equivalent `docker compose exec backend` commands. Do not delete persistent database volumes casually.

## Flutter mobile foundation

The committed project is at `apps/mobile`. Do not run `flutter create` over its source. See [the mobile runbook](docs/runbooks/PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and [integration/security review](docs/reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md) for the pinned toolchain, real CI evidence, secure-session lifecycle and native-device/deployment gates. Networking is disabled unless an approved bare HTTPS API origin is explicitly supplied at build time. No live delivery or production NGO-private workspace is enabled.

## Initial tests

`cd apps/backend && python manage.py test`; CI runs PostgreSQL-backed tests, Django system checks and migration drift check. See `docs/decisions/ADR-0001-repository.md`.

## Non-negotiable boundary

PWC's alliance roles do not inherit NGO-private access. The initial organization endpoints are public read-only projections of verified workspaces; private reads are not implemented. Do **not** expose unrestricted Django Admin to alliance personnel. Finance, imports and binding commitments are not implemented here.

## Agent workflow and validation evidence

Read [AGENTS.md](AGENTS.md) before development. Planning drafts and unresolved decisions are preserved under `docs/`; the guide explains their authority and provisional status. See [PWC-01 audit](docs/runbooks/PWC-01-AUDIT.md) for implemented versus planned functionality, validation evidence and next-task blockers.

## Known limitations

Registration, email verification and password recovery are implemented as disabled-by-default, synthetic-only backend flows; see [the recovery/security review](docs/runbooks/PWC-03A2-RECOVERY-REVIEW.md) and [registration runbook](docs/runbooks/PWC-03A2-REGISTRATION.md). Browser/mobile login and session lifecycle are also implemented behind a separate disabled flag; see [the sessions contract and validation](docs/runbooks/PWC-03A3-SESSIONS.md). MFA/TOTP, recovery codes and personal operation-bound assurance are implemented under another default-off flag; see [the MFA/assurance policy and evidence](docs/runbooks/PWC-03A4-MFA-ASSURANCE.md). Private tenant APIs, granular permissions, memberships/import/claim, finance and alliance workflows remain unimplemented. Authentication security events/outbox are scoped evidence, not a general audit platform. The configured session authentication and minimal access labels are not a finished authentication/authorization system. The existing finance-named test only checks a scaffold role value, not finance enforcement. The current Flutter and W1 web foundation runbooks supersede historical placeholder descriptions; neither is production deployment or complete NGO business functionality. No RLS, production hosting or operational backup/restore acceptance is configured. Frontend and scoped quality/security CI gates exist; see the current runbooks. Local debug/server/database settings must not be used in production. PWC-02 identity work requires an approved authentication/recovery ADR; passing scaffold checks does not resolve that decision.

## PWC-04C permitted application features

Both web portals now provide `/ngo-registry`, a bounded read-only HTTP client for
only the existing four-field public verified-workspace projection. The optional
local proxy forwards that exact public endpoint only—no authentication/private
paths, cookies or writes. Owner-only historical application/verification summaries
and existing revision-checked withdrawal are implemented/tested on PostgreSQL;
credentialed browser/native history transport remains gated. Flutter adds a
separate opt-in exact HTTPS public reader and permission-aware history screen.
No officer provisioning, real review/invitation/admin grant or new intake is enabled.
See [setup, working workflows, exact validation and remaining gates](docs/runbooks/PWC-04C-PERMITTED-APPLICATION-IMPLEMENTATION.md).
