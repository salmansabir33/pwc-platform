# PWC Platform — Initial M1 Repository

Independent repository for the Pakistan Welfare Club digital ecosystem (Faisalabad pilot).

**Status:** Initial engineering scaffold; not a completed application. PWC planning choices remain provisional. No production deployment is configured.

## Modules
- `apps/backend`: Django REST API, shared identity, tenant-owned organization models, basic tenant-isolation tests.
- `apps/mobile`: Flutter placeholder; generate SDK-native project using installed Flutter CLI before developing UI.
- `apps/ngo-web`: reserved for NGO web administration (framework pending).
- `apps/pwc-ops`: reserved for separately authorized platform/alliance operations (framework pending).
- `docs/product`: reference planning documents.
- `docs/decisions`: architectural decisions and outstanding sign-offs.
- `infra`: local PostgreSQL and backend dev Docker configuration.

## Local setup (Docker required)
```bash
cp .env.example .env
# Set strong local values in .env before starting services
docker compose up --build -d db
# Backend runs migrations and server with:
docker compose up --build backend
```
Open `http://localhost:8000/api/v1/health/`. The database starts empty. No sample NGO authority is assigned automatically.

## Local setup (without Docker)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/backend/requirements.txt
# Provide PostgreSQL and set required DB_* and DJANGO_SECRET_KEY env vars
cd apps/backend
python manage.py migrate
python manage.py test
python manage.py runserver
```

## Flutter preparation
Install Flutter stable separately, then run `flutter create --project-name pwc_mobile apps/mobile` from the repository root and implement the M1 shell using the screen spec. Flutter SDK is not available in this build environment, so no generated Flutter app is represented as complete.

## Initial tests
`cd apps/backend && python manage.py test`; CI runs PostgreSQL-backed tests, Django system checks and migration drift check. See `docs/decisions/ADR-0001-repository.md`.

## Non-negotiable boundary
PWC's alliance roles do not inherit NGO-private access. The initial organization endpoints deliberately remain narrow and require verified authority for private reads. Do **not** expose unrestricted Django Admin to alliance personnel. Finance, imports and binding commitments are not implemented here.
