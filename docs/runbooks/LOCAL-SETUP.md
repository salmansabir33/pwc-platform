# Local developer setup

Current cross-surface configuration, hash locks, quality/security CI and deployment boundaries are in [PWC-02F](PWC-02F-ENVIRONMENT-AND-SECURITY-TOOLING.md). Use that runbook for the current toolchain/validation contract; historical evidence below is not a claim about the present checkout.

## Prerequisites

- Python 3.11 or 3.12 (Docker and original CI use 3.12).
- PostgreSQL 16, either installed locally or via Docker Engine + Compose v2.
- Use synthetic data only. No accounts or NGO authority are seeded automatically.

Backend dependencies, including transitive packages, are pinned in `apps/backend/requirements.txt`. Upgrade them deliberately with PostgreSQL-backed validation. Do not replace PostgreSQL with SQLite to make tests pass.

## Environment

From repository root:

```bash
cp .env.example .env
# Edit .env: replace both placeholder secrets with strong development-only values.
```

`.env` is ignored by Git. Django does **not** automatically load it. Compose injects it; native shells must export it explicitly. Do not use production credentials. The example defaults to `DB_HOST=db` for Compose; native Python needs `127.0.0.1` when using a local/published database.

## Docker workflow

```bash
docker compose up --build -d db
docker compose up --build -d backend
docker compose logs -f backend
```

The backend waits for database health, applies migrations and runs Django's **development** server. Endpoints are available locally at `http://localhost:8000/api/v1/health/` and `/api/v1/organizations/`. The latter is a public projection of verified workspaces, not a private tenant API. Health is process liveness only, not a database readiness probe.

```bash
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py migrate --plan
docker compose exec backend python manage.py migrate --noinput
docker compose exec backend python manage.py migrate --check
docker compose exec backend python manage.py test --verbosity 2
docker compose down
```

Database data survives in `pwc_pgdata`. **Do not use `down -v` unless deliberately destroying disposable development data.** Changing `.env` database credentials does not reset credentials in an existing volume. After code/dependency changes, rebuild the backend; no source bind mount or automatic host-source reload is configured.

Compose interpolates DB variables from the root `.env`; exported shell variables take precedence. Avoid stale shell overrides when troubleshooting. Both published ports bind loopback only by design.

## Native Python + PostgreSQL

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r apps/backend/requirements.txt
python -m pip check
# Load only your own trusted local file (shell syntax; quote values as needed).
set -a
. ./.env
set +a
export DB_HOST=127.0.0.1
```

Start the Compose database with `docker compose up -d db`, or provision a local PostgreSQL 16 database matching `DB_NAME`, `DB_USER`, `DB_PASSWORD` and `DB_PORT`. The development test role needs `CREATEDB` to create/drop Django's separate test database. Do not give production application roles this privilege. The Compose initialization role is a local development superuser, not a production role design.

```bash
cd apps/backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py showmigrations
python manage.py test --verbosity 2
python manage.py runserver 127.0.0.1:8000
```

To create a reviewed model migration, use `python manage.py makemigrations <app>` and commit the generated migration with the model change. Do not modify historical migrations. Test both upgrades and fresh database initialization when changing the foundation.

### Remote sandbox preview

For native preview only, set `DJANGO_ALLOWED_HOSTS` to the exact preview hostname plus necessary local hosts, then run `python manage.py runserver 0.0.0.0:8000`. Do not use wildcard hosts or globally disable CSRF/embedding protections. Browser clients must use a relative API URL and a server-side proxy, never a browser `localhost` backend URL. Compose's loopback publishing is intended for local development, not automatically configured remote previews.

## Troubleshooting and limitations

- Missing `DJANGO_SECRET_KEY`: export the environment before running Django; missing keys intentionally fail closed.
- Connection refused / host `db` cannot resolve: start PostgreSQL, check credentials/port, and use `DB_HOST=127.0.0.1` for native Python. `db` resolves only in the Compose network.
- Test database permission denied: use a disposable development role with `CREATEDB` and no real data.
- Migration drift: inspect the model and add a migration; do not hide it by regenerating initial history.
- Python 3.11 and PostgreSQL 16.2 were exercised in the PWC-01 sandbox. Docker/Compose and Python 3.12 were not available there; CI defines 3.11/3.12 with PostgreSQL 16. See the audit report for execution evidence.
- No production deployment, live delivery provider, real NGO authority, RLS, production private evidence/import/claim or finance is implemented. Personal auth, synthetic authorization, OpenAPI, Flutter/web foundations and quality gates now exist; see their current runbooks and the PWC-02F review. Synthetic tests do not approve real activation.
- Before production, review `check --deploy` against actual production settings, configure HTTPS/secure cookies/HSTS appropriately, managed secrets, least-privilege roles, backups/restore, private storage and logging. Local settings are not production-ready.
