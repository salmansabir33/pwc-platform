# PWC Platform — Initial M1 Repository

Independent repository for the Pakistan Welfare Club digital ecosystem (Faisalabad pilot).

**Status:** Initial engineering scaffold; not a completed application. PWC planning choices remain provisional. No production deployment is configured.

## Modules
- `apps/backend`: Django REST API, shared identity, tenant-owned organization models, public projection tests.
- `apps/mobile`: Flutter placeholder; generate SDK-native project using installed Flutter CLI before developing UI.
- `apps/ngo-web`: reserved for NGO web administration (framework pending).
- `apps/pwc-ops`: reserved for separately authorized platform/alliance operations (framework pending).
- `docs/product`: reference planning documents.
- `docs/decisions`: architectural decisions and outstanding sign-offs.
- `infra`: local PostgreSQL and backend dev Docker configuration.

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
python -m pip install -r apps/backend/requirements.txt
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

## Flutter preparation
Install Flutter stable separately, then run `flutter create --project-name pwc_mobile apps/mobile` from the repository root and implement the M1 shell using the screen spec. Flutter SDK is not available in this build environment, so no generated Flutter app is represented as complete.

## Initial tests
`cd apps/backend && python manage.py test`; CI runs PostgreSQL-backed tests, Django system checks and migration drift check. See `docs/decisions/ADR-0001-repository.md`.

## Non-negotiable boundary
PWC's alliance roles do not inherit NGO-private access. The initial organization endpoints are public read-only projections of verified workspaces; private reads are not implemented. Do **not** expose unrestricted Django Admin to alliance personnel. Finance, imports and binding commitments are not implemented here.

## Agent workflow and validation evidence
Read [AGENTS.md](AGENTS.md) before development. Planning drafts and unresolved decisions are preserved under `docs/`; the guide explains their authority and provisional status. See [PWC-01 audit](docs/runbooks/PWC-01-AUDIT.md) for implemented versus planned functionality, validation evidence and next-task blockers.

## Known limitations
Registration, email verification and password recovery are implemented as disabled-by-default, synthetic-only backend flows; see [the recovery/security review](docs/runbooks/PWC-03A2-RECOVERY-REVIEW.md) and [registration runbook](docs/runbooks/PWC-03A2-REGISTRATION.md). Browser/mobile login and session lifecycle are also implemented behind a separate disabled flag; see [the sessions contract and validation](docs/runbooks/PWC-03A3-SESSIONS.md). MFA operations and assurance-gated session management, private tenant APIs, granular permissions, memberships/import/claim, finance and alliance workflows remain unimplemented. Authentication security events/outbox are scoped evidence, not a general audit platform. The configured session authentication and minimal access labels are not a finished authentication/authorization system. The existing finance-named test only checks a scaffold role value, not finance enforcement. Flutter and both web surfaces remain placeholders; frameworks/SDK decisions are open. No RLS, production hosting, backup/restore, frontend or lint gates are configured. Local debug/server/database settings must not be used in production. PWC-02 identity work requires an approved authentication/recovery ADR; passing scaffold checks does not resolve that decision.
