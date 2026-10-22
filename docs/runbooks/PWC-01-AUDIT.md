# PWC-01 — Repository audit and foundation validation

Date: 2026-10-22. Baseline: `7aceb7e` (`Initial PWC platform foundation`). Working branch: `arena/9192ec62-pwc-platform`, supplied from main by Arena. Initial working tree was clean. No branch switch, merge, push or M1 authentication implementation was performed. Planning documents were preserved unchanged.

## Audit summary
Reviewed repository structure, tracked code/configuration/tests, README, all eight product planning documents' scope/authority and relevant engineering/security sections, ADR-0001, open decisions, setup and placeholder READMEs. Product drafts are not implementation/production approval. Development Execution Plan §2 assigns source authority; IA and detailed screen specification control canonical screen IDs even where Flutter examples use alternate prefixes. Planning statements saying no repository exists describe their drafting context, not current code reality.

| Area | Implemented | Still planned / limitation |
|---|---|---|
| Identity | UUID `AbstractUser`, language preference, password validators, Django auth/session infrastructure | No registration, login/logout API, contact verification, provider, token lifecycle or recovery flow |
| Organizations | Organization, one-to-one workspace state, user/organization/role uniqueness with protected FKs | No claims, verification review/evidence, context authorization kernel or private NGO endpoints |
| Public API | `/api/v1/health/`, verified-only organization list/detail with four public fields | Health is liveness only; verification flag is not publication-consent policy or legal endorsement |
| Authorization | DRF authenticated default; explicit AllowAny for public directory; no Admin route | Minimal role strings are not granular permissions; no finance or private authorization enforcement can be claimed |
| Database | PostgreSQL backend, accounts/org initial migrations | No RLS, domain audits, backups, restore rehearsal or production least-privilege design |
| Clients | Reserved Flutter, NGO Web and PWC Operations paths | No generated apps, SDK pin, chosen web frameworks or frontend tests |
| Shared/infrastructure | Reserved contracts, tokens, E2E paths; local Docker/Compose; backend CI | No generated OpenAPI, worker/storage stack, production infrastructure or lint gate |

The structure supports all three client surfaces without selecting frameworks or rebuilding the application. NGO memberships, volunteer relationships, PWC institutional membership, finance, project commitments and imports remain unimplemented. No seeded authority or real personal data exists in the tracked scaffold.

## Verified errors and focused fixes
- **Migration drift:** Baseline `makemigrations --check --dry-run` exited 1. Handwritten initial migrations omitted inherited User Meta options/current `is_active` help text and generated BigAutoField metadata. Added `0002` migrations in accounts and organizations; did not rewrite `0001` or change business fields. Drift check now exits 0. Existing-initial-migration upgrade and fresh test DB initialization pass.
- **Environment instructions:** Native setup previously omitted loading `.env` and retained Compose-only hostname `db`. Documented explicit trusted-shell export and native `DB_HOST=127.0.0.1`; clarified test `CREATEDB`, migrations, logs, persistence and rebuild behavior.
- **Dependency repeatability:** Replaced broad ranges with the complete validated pinned dependency set; retained Django/DRF/PostgreSQL architecture. This is version pinning, not a cryptographic artifact lock or vulnerability audit.
- **Container context/ignore hygiene:** Added backend `.dockerignore`; extended Git ignore for frontend dependencies/build output, logs, coverage and private-key extensions. Existing `.env` exclusions remain intact.
- **Quality:** Preserved the original three tests and added five public-scaffold regression tests: liveness shape, public field allowlist, all nonverified states hidden, claimant grant not publishing provisional org, and write-method denial. Removed an unused view import. No private/business features added.
- **CI:** Added Python 3.11 alongside existing 3.12, pip consistency/cache, unapplied migration check, verbose tests and read-only repository token permissions. Existing PostgreSQL service/check/drift/migrate/test flow retained. Workflow execution on GitHub is not claimed.
- **Documentation:** Added root AGENTS guidance and corrected README's misleading suggestion that private reads already exist.

## Commands and execution evidence
Environment: Python 3.11.2, Django 5.2.18, DRF 3.18.3, psycopg/binary 3.3.6; actual PostgreSQL 16.2 (not SQLite). Docker, Compose, native PostgreSQL executables and Python 3.12 were not available on PATH. `pgserver==0.1.4` from PyPI supplied disposable PostgreSQL binaries for this audit only; it was not added to application dependencies. Temporary clusters were cleaned up automatically.

- `git status --short`, `git branch --show-current`, `git log --oneline --all -5`, `git ls-files`, structure listings and file reads: clean baseline, one initial commit, expected monorepo.
- `python3 -m venv .venv`; `.venv/bin/pip install -r apps/backend/requirements.txt pgserver`: succeeded.
- Baseline `python manage.py check`: pass; `makemigrations --check --dry-run`: **failed with drift**; `migrate --noinput`: pass; `test --verbosity 2`: **3/3 pass**.
- `DJANGO_SECRET_KEY=<audit-only-value> .venv/bin/python apps/backend/manage.py makemigrations accounts organizations`: generated additive metadata migrations. This standalone generation initially warned that no default localhost PostgreSQL was running; later checks against the disposable real database validated consistent history and no drift.
- Final `python manage.py check`: **0 issues**.
- Final `python manage.py makemigrations --check --dry-run`: **No changes detected**, exit 0.
- `migrate accounts 0001 --noinput`, `migrate organizations 0001 --noinput`, then `migrate --plan` and `migrate --noinput`: **pass**, exercising upgrade from original scaffold migrations.
- `migrate --check`, `showmigrations`: **pass**, all 19 migrations applied.
- `python manage.py test --verbosity 2`: **8/8 pass**, fresh PostgreSQL test DB migration/application and cleanup succeed.
- `.venv/bin/pip install -r apps/backend/requirements.txt` and `.venv/bin/pip check`: pinned set satisfied, **no broken requirements**.
- Fresh independent `/tmp/pwc-01-clean-venv`: installed only pinned application requirements; `pip check` and Django `check` both pass without the audit helper.
- `git diff --check`: pass.
- Ignore checks for `.env`, `.env.local`, venv, bytecode, node_modules and private-key samples: all ignored.
- `python manage.py check --deploy`: exit 0 with **5 warnings**: W004 HSTS unset, W008 HTTPS redirect unset, W009 deliberately short audit-only secret, W012 session cookie secure unset, W016 CSRF cookie secure unset. Production settings/reverse-proxy topology and real secret management require separate review; no insecure test value was installed as an application default.

### Reproducing the sandbox-only database validation
Normal developer setup uses the documented PostgreSQL 16/Compose workflow. Where Docker is unavailable, the audit used this optional harness from repository root after installing `pgserver==0.1.4` in the ignored venv:

```python
import os, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pgserver

python = str(Path('.venv/bin/python').resolve())
with tempfile.TemporaryDirectory() as data:
    server = pgserver.get_server(data, cleanup_mode='delete')
    uri = urlparse(server.get_uri())
    os.environ.update(
        DJANGO_SECRET_KEY='audit-only-not-production',
        DB_NAME='postgres', DB_USER=uri.username or 'user',
        DB_HOST=parse_qs(uri.query)['host'][0],
        DB_PORT=str(uri.port or 5432),
    )
    commands = [
        ('migrate', 'accounts', '0001', '--noinput'),
        ('migrate', 'organizations', '0001', '--noinput'),
        ('check',), ('makemigrations', '--check', '--dry-run'),
        ('migrate', '--plan'), ('migrate', '--noinput'),
        ('migrate', '--check'), ('showmigrations',),
        ('test', '--verbosity', '2'), ('check', '--deploy'),
    ]
    for args in commands:
        subprocess.run([python, 'manage.py', *args],
                       cwd='apps/backend', check=True)
```

This helper's local disposable cluster is not a recommended production database deployment. The audit-only key is intentionally nonsecret and unsuitable outside isolated tests.

## Security observations and unresolved limitations
- Manual tracked-file/configuration review plus patterns for private-key headers, GitHub tokens, AWS access keys and credential-bearing database URLs found **no apparent real committed credentials**. The one-commit baseline history was reviewed. `.env.example` contains placeholders; CI/test strings are explicitly disposable, not production secrets. This scoped review is not proof of absence of every secret or a dedicated historical secret-scanner/vulnerability audit.
- Django requires an environment secret and defaults debug off. DRF defaults to authenticated access; directory overrides intentionally expose only a public allowlist. CSRF middleware is retained. No admin endpoint is enabled.
- Existing `test_role_does_not_mean_finance_permission` asserts a role value only. It does **not** prove finance denial, multi-NGO private isolation or alliance-role authorization. Added tests likewise validate only existing public behavior. Full negative role/tenant matrices must arrive with their actual private APIs.
- No authentication/security/provider policy has been silently selected. Session authentication in settings is not approval of the future cross-client auth contract. User relationships permit multiple org grants structurally, but no relationship-management workflow exists.
- Compose is development-only: loopback ports, persistent named DB volume, dev server and development database superuser. Docker build/start/Compose validation and Python 3.12 execution remain **unverified locally**; CI matrix is configured but not run by this audit. No frontend SDK/tests/lint, production deployment or restore rehearsal was possible/claimed.
- Exact publication/consent policy, authentication/recovery channels, authorization contract, verification evidence, support access, legal/privacy retention and hosting remain open in the existing decision register. Pinning does not eliminate the need for periodic dependency security review.

## Changed files
- Created: `AGENTS.md`; `apps/backend/.dockerignore`; accounts and organizations `0002` migrations; this audit report.
- Modified: `README.md`, `docs/runbooks/LOCAL-SETUP.md`, `.env.example`, `.gitignore`, `.github/workflows/backend.yml`, `apps/backend/requirements.txt`, `apps/backend/organizations/tests.py`, `apps/backend/organizations/views.py`.
- Preserved: product planning drafts, decision documents, existing initial migrations, all frontend placeholders and all existing tests/business behavior.

## Readiness for PWC-02 authentication
**Development foundation ready; authentication implementation approval conditional.** Backend dependencies/setup are documented and repeatable; checks, migration upgrade/fresh initialization and existing-scope tests pass on real PostgreSQL. The task makes no claim of completed M1, production readiness or tested container execution.

Before coding PWC-02 authentication, approve an ADR covering login identifiers/channels, contact verification/provider, session/token lifecycle across mobile/web, logout/revocation, recovery and abuse controls. Agree the identity API/error contract and valid/invalid/expired/revoked acceptance tests. Keep one personal identity and independent NGO/PWC relationships, no implicit authority or finance grants. Obtain the required product/security decisions rather than inventing them. CI/container execution is the remaining environment confirmation step; no automatic merge into main is authorized.

Commit identifier is recorded in the task handoff (not embedded here to avoid self-referencing a commit).
