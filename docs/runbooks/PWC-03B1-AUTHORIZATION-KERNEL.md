# PWC-03B.1 — synthetic multi-NGO authorization kernel

**Date:** 24 October 2026
**Authority:** [ADR-0002](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), approved core architecture with documented gates.
**Starting checkpoint:** `e7b930fcf2403af09d92fb3f9ae18d8b8f922f41`.
**Scope:** internal synthetic read services and offline fixture lifecycle only. No NGO routes, real authority, grant-management APIs, frontend, finance, files or exports.

## 1. Preservation and scope

Preflight fetched the existing feature branch and `origin/main`, verified checkpoint ancestry, clean index/tree and approved ADR hashes. No reconciliation was necessary in this slice. User/Organization/Workspace/access scaffolding, authentication source and all accounts/organizations migrations are unchanged. The existing 247-test suite passed on PostgreSQL before editing.

The root AGENTS/roadmap's old branch/authentication status paragraphs are historical; this assignment uses `arena/d8a3e024-pwc-platform` and preserves the merged authentication implementation. No ADR amendment was necessary. This runbook does not authorize unresolved institutional or production policy.

## 2. Implemented schema

New Django application: `access`. Migration `0001_initial` depends on accounts `0006` and organizations `0002`; it creates no accounts, grants or default tenants.

| Record | Contract |
|---|---|
| `NGOKernelState` | UUID PK, protected one-to-one Organization, immutable fixture batch/evidence/creation metadata, positive revision, disabled-by-default mode (`disabled`/`synthetic`). Per-tenant serialization root. Synthetic → disabled is terminal. |
| `SyntheticPrincipal` | UUID PK, protected one-to-one existing User identity, immutable fixture batch, evidence and creation timestamp. No authority merely from this attestation. |
| `NGOGrant` | UUID, protected Organization/subject/optional issuer/revoker FKs, pinned role code/version, organization-only scope, synthetic source/process/batch/evidence, verification, effective/mandatory expiry timestamps, creation timestamp, positive revision and complete revocation metadata. |
| `AuthorizationEvent` | UUID, protected optional organization/actor/session/grant references, process, action/result/reason, target, role version, old/new tenant/grant revisions, batch, correlation UUID, database event timestamp and non-sensitive evidence reference. |

Database CHECKs enforce closed bundle pairs, source/scope/process/verification values, nonempty evidence, positive revisions, complete revocation fields, and `effective_at < expires_at <= effective_at + 24 hours`. The 24-hour limit is a synthetic fixture limit, not a real NGO policy. A partial unique index on organization/subject/role/version where unrevoked prevents competing slots; expired and unverified grants retain their slot until revoked. Tenant/subject/expiry and event/time indexes are additive.

`0002_postgresql_guards` adds PostgreSQL triggers, an explicitly permissioned lock function and PUBLIC privilege revocations:

- Principal attestations are immutable; state identity/batch/evidence are immutable. Only revision+1 and optional terminal disable are allowed on state updates.
- Grants may only transition once from unrevoked to revoked at revision+1; stale ORM save, un-revoke, in-place role/provenance/validity edits and deletes fail.
- Grant inserts start at revision 1, unrevoked. Cross-row triggers verify state/principal batch equality, synthetic tenant mode, and optional issuing/revoking actor batch ownership.
- Events are append-only. A referenced grant must have the same tenant/batch/role version; a referenced session must belong to the actor. Allow events identify context revision, batch, actor and session. Event time is overwritten with `clock_timestamp()`.
- Existing Workspace lifecycle updates/deletes are refused for a kernel tenant, rather than allowing an unaudited legacy writer. The supported .1 shutdown is terminal kernel-state disable. A later Workspace transition service needs its own reviewed revision/audit contract.
- Principal/state/grant/event deletes are refused. Parent foreign keys preserve history. An owner with TRUNCATE/DDL powers remains outside this guarantee.

Cross-row guarantees above are PostgreSQL triggers, not claims about `full_clean()` or single-row CHECKs. Expected-revision comparison and atomic event creation are performed by the fixture lifecycle service under locks; arbitrary privileged SQL is not an approved lifecycle writer. Constraints alone do not enforce a complete human authority policy.

## 3. Registry and contexts

`access.registry` exposes a read-only mapping and frozenset bundles:

| Pinned role | Exact actions |
|---|---|
| `ngo_kernel_reader / 1` | `ngo.context.enter`, `ngo.private_stub.read` |
| `ngo_kernel_admin_probe / 1` | Reader actions plus `ngo.kernel_settings.read` |

Registry identifier: `ngo_kernel_v1`. Version 1 must not be expanded in place. Unknown bundle/version inserts are rejected by the DB; evaluation independently denies unknown pairs. No wildcard, custom role, finance, signatory, delegation, real administration, audit-reader, file/export or governance action exists.

`resolve_context(kind, identifier, personal_user_id=...)` returns an immutable typed identifier for personal or NGO contexts. Personal context must match its authenticated owner. All other kinds reject. Resolution alone is not authorization. `evaluate` does not dispatch personal operations; existing accounts services remain authoritative for those.

Organization UUID is the external NGO identifier, not Workspace BigAutoField. A future HTTP adapter must take it from the canonical explicit path and reject conflicting context/body/header inputs. This slice accepts a server-supplied identifier/action and implements no HTTP context parser or remembered selection. No selection row, default tenant or global current organization exists.

## 4. Synthetic-only boundary and fixture writer

Evaluation and fixtures require all of:

- `PWC_SYNTHETIC_AUTHORIZATION_ENABLED=True` (environment default is false).
- `PWC_AUTHORIZATION_ENVIRONMENT` is `synthetic_test` or `synthetic_development` (default `disabled`).
- PostgreSQL, READ COMMITTED and no database routers. Database name starts with `test_` or `pwc_synthetic_`.
- An explicitly synthetic tenant state and principal with matching batch.
- A verified Workspace and a currently eligible grant from the same batch.

These settings are not production instructions. Keep production disabled regardless of database name. They are additional release/configuration safeguards, not cryptographic protection against an operator who controls settings and the database.

`access.testing.FixtureBatch` is an offline utility with a newly generated batch ID. `create_user()` creates a new unusable-password account, synthetic verified `.invalid` contact, immutable attestation and audit in one transaction. `create_tenant()` creates a new synthetic Organization, verified fixture Workspace, state and audit atomically. Neither method accepts an existing User/Organization to enroll. Test code may establish credentials/sessions through the existing accounts foundation.

`issue(organization_id, subject_id, expected_revision=..., ...)`, `revoke(..., expected_revision=..., expected_grant_revision=...)` and `disable(..., expected_revision=...)` operate only inside the utility's attested batch. Issue can deliberately seed expired, future or unverified negative fixtures; they never authorize access. No fixture utility is registered as a view, Django admin or general-purpose management command. It is not a human assurance or grant delegation API.

Membership/volunteer concepts, imported records, legacy `OrganizationAccess`, Board/Groups/staff/superuser flags and MFA do not participate in permission lookup. Membership/volunteering/Board domain models do not yet exist: .1 tests use the real legacy membership/admin scaffold and nonauthoritative Group labels, not invented business models.

## 5. Database roles and lock-only function

Do not run the application as the migration owner. Use separately provisioned, non-owner, non-superuser roles; runtime must not inherit fixture/migration roles or have CREATEROLE, schema CREATE, TRUNCATE or DDL privileges. No production credentials or cluster-wide roles are created by migrations.

[`access/db_roles.sql`](../../apps/backend/access/db_roles.sql) is a psql provisioning template, to run as the migration owner **after migrations**, only in an isolated synthetic environment:

```sh
psql "$SYNTHETIC_DATABASE_URL" -v runtime_role=your_runtime_role \
  -v fixture_role=your_offline_fixture_role -f apps/backend/access/db_roles.sql
```

The named roles must already exist. Existing accounts/organizations/session privileges needed by authentication are provisioned separately. Grant schema USAGE explicitly; do not use broad default privileges for future access tables. The template gives runtime access-table SELECT, event INSERT and lock-function EXECUTE, but no direct grant/state/attestation writes or event UPDATE/DELETE. The separate offline writer can create/revoke fixtures, but has no history DELETE permission. Do not provide its credentials or membership to application processes.

PostgreSQL `SELECT FOR UPDATE` requires UPDATE privilege, so runtime cannot lock the authority root directly. `public.pwc_kernel_lock(uuid)` is a narrowly scoped SECURITY DEFINER function that only selects/locks the specified state row. It has fixed `pg_catalog` search_path, fully qualified table access, no dynamic SQL or mutation and no PUBLIC execution. Runtime explicitly receives EXECUTE. Trigger functions use a fixed search path as well. Function ownership remains with the migration owner, never runtime.

Restricted-role acceptance uses actual temporary NOLOGIN roles on separate SET ROLE boundaries, exercises the provisioning SQL, allows a successful read without state UPDATE, and rejects direct grant/state/attestation writes, event deletion and TRUNCATE. Tests clean those role grants up. CI/test ownership needs CREATEROLE for this acceptance, never production runtime. Provisioning/membership/default-privilege drift remains an operational review requirement.

## 6. Evaluation API

```python
from access.services import evaluate
from access.registry import READ

decision = evaluate(
    request, kind="ngo", identifier=organization_uuid, action=READ,
    object_organization_id=organization_uuid,  # optional direct-object probe
)
```

This is an internal service interface, not a route. The caller must map a server-owned operation to a constant; never forward a caller's desired permission or cached capabilities as authority.

`AuthorizationDecision` is frozen and contains allowed/code/status/correlation, and only on success context UUID/revision, sorted effective actions, registry version and a tuple of fixed scalar projection fields. No ORM objects/querysets, grant proofs, evidence documents or reusable capability tokens escape. All projections are materialized before commit. Entry returns context identity/revision only; probe/settings reads return fixed synthetic labels. There is no arbitrary callback, arbitrary-model query or streaming facility.

Evaluation opens a durable top-level transaction and reuses `PersonalAuthentication` **inside it**, retaining its locks through the read/audit. It preserves cookie/Bearer separation, TLS/CSRF checks, online contact/session/epoch/factor/credential checks and error statuses. It captures the original authentication deadline with existing accounts helpers. The caller's earlier `request.user` is never sufficient. No authentication code or MFA registry was changed.

After authenticating, the service resolves context, requires clear recovery hold, locks tenant state, checks attestation/workspace, then loads only the requesting subject's unrevoked grants from that tenant/batch. Grant actions union only within that tenant. One complete eligible grant supports the requested atom; scope/limits are never laundered between grants. The private lookup helper filters by tenant before object lookup/count; foreign and missing direct-object UUIDs yield the same absence. Final deadlines and grant eligibility are rechecked with DB wall-clock after audit insertion; expiry rolls the allow audit back and returns no protected projection.

Denials return no foreign identifiers/revisions/actions. A bounded redacted denial record is attempted in a new transaction after rollback. Audit/DB failure returns 503 without protected data; logging uses only fixed messages and correlation IDs, not exception payloads or credentials. Missing entry/ineligible tenant/foreign object is 404; entered tenant lacking action is 403; malformed supported context is 400; invalid auth is 401; holds are 403. Unsupported context denies. Personal action dispatch is deliberately unavailable here.

**Boundary restriction:** do not nest `evaluate` or fixture lifecycle calls inside another application transaction; durable atomic rejects that programmer error. A completed result must not precede its real commit. No positive authorization cache, session keepalive or idle-renewal write is performed.

## 7. Transactions, revocation, expiry and failures

Primary default connection, READ COMMITTED. Lock order: User(s) sorted → contact/factor as required by existing accounts helpers → AuthSession/credential → tenant state by Organization UUID → grant → domain row → audit. .1 handles one NGO at a time. Authentication adapter rechecks User/contact/session/credential before domain locking; no auth lock-acquiring helper runs after the root. Fixture issue/revoke locks the subject User before state; revoke locates the owner without changing data first. No external I/O under locks.

Both read authorization and fixture transitions use `lock_timeout=2s` and `statement_timeout=5s`, locally scoped to the transaction. DB clock uses `clock_timestamp()`, not transaction-start `now()`. Grant validity is effective-inclusive and expiry-exclusive. Expiry needs no scheduled job or revision flip.

Fixture creation/revocation serializes at the root and requires the caller's expected revision. Missing is 428, malformed is 400, stale is 412. Duplicate current slots/invalid lifecycle are 409. First revoke increments grant/root revisions and appends an event atomically; a repeated revoke with current revisions is an owned no-op. Revoked UUIDs are never reused or revived. Replacement is a distinct explicit grant at the current tenant revision. Disable is terminal and audited.

A read serialized before revoke may finish; once revocation commits, newly authorized reads deny, even using stale capability data or valid MFA. Already returned bytes cannot be recalled. Final authorization deadline is not a promise about network delivery time.

Audit insert failure rolls back changes/read authorization. Transient DB/lock/deadlock failures return 503, with no automatic retry on uncertain commit. Denial evidence is best-effort only when the authoritative DB itself is unavailable; correlation-only operational warnings do not claim durable audit. Successful transitions require durable DB events. No nonpersonal assurance intents or privileged command proof consumption exist in .1.

## 8. Migrations and rollback

MigrationExecutor acceptance runs an actual down-to-pre-access/up-to-current migration on an unused access schema, preserving User UUID/password, Organization UUID, Workspace PK, legacy access row and accounts migration history. No access state/grants are backfilled. Fresh test databases apply both migrations.

`0002` checks for any used state/principal/grant/event rows before reversal, refusing destructive rollback. Disable/drain affected services and use reviewed forward fixes/restore instead. Existing identity/membership/role history must never be deleted or reinterpreted. The empty local acceptance database exercised an unused guard down/up cycle; no production rollback was attempted. No real legacy regrant/reconciliation approvers are implemented.

## 9. Acceptance evidence

Environment: Python 3.11.2, Django 5.2.18, PostgreSQL **16.2**, READ COMMITTED. Dependencies are the existing pinned requirements. Sandbox PostgreSQL was provided by an external development-only `pgserver` installation, not added as an application dependency. Python 3.12/Docker and production deployment were not exercised locally.

Commands (with the normal environment-supplied Django/DB settings):

```sh
python -m pip check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test access --verbosity 1
python manage.py test access.tests.KernelRaceTests --verbosity 1
python manage.py test --verbosity 1
```

- Pre-edit baseline: **247 tests PASS**.
- Final access suite: **45 tests PASS**.
- Concurrency subset: **10 tests PASS in each of three additional repetitions** (30 repeated executions).
- Full final suite: **292 tests PASS** (247 existing + 45 new), 167.276 seconds.
- Dependency consistency, system check, no migration drift, migration plan/application/no-pending checks and whitespace validation pass.

| ADR gate | .1 evidence |
|---|---|
| K01–K02 | Tenant-filtered queryset/count/direct probe; A/B grants and per-tenant union; foreign/absent equivalence. |
| K03 | Real legacy roles and Group/staff/superuser labels ignored; admin-probe excluded from unsupported domains; accepted live TOTP observation still cannot create NGO/finance authority. |
| K04–K06 | Expired/future/unverified/unknown/legacy/unattested/disabled grants/contexts, epochs/sessions/holds; revocation after commit on a new connection; once-only revisions/events. |
| K07–K09 | Separate connections with Barriers/Events and observed `pg_blocking_pids`; both read/revoke orderings, DB expiry during root wait, competing create, revoke/create and stale revisions. Final DB rows/events are asserted. |
| K10 | Insert/read/revoke audit failures, final-deadline failure, database fault injection and actual lock timeout; no protected response or partial change. |
| K11–K12 | Default/config/DB-name/router/isolation gates; no enrollment of existing records; batch ownership; DB CHECK names tested independently of duplicate-slot failure; actual restricted runtime/fixture roles, immutable history, parent FKs and append-only audit. |
| K13 | Actual additive migration preservation and used-history reversal refusal. |
| K14 | Observed User/root lock waits; committed epoch/logout/hold/refresh transitions versus reads; no idle renewal; no lazy data escapes. Full factor lifecycle race matrix remains in existing auth regressions; no new factor mutation exists here. |
| K15 | Fresh whole-backend regression; no new HTTP routes registered. |

## 10. Deferred work and PWC-03B.2 readiness

The internal boundary and fixture/DB acceptance are ready for review before a separate .2 assignment. Remaining .2 work: synthetic-only HTTP discovery/capability/read adapters, canonical path/body/header conflict enforcement, consistent error envelopes/no-store, bounded 50-item discovery locking/materialization, cookie/Bearer/CSRF endpoint regression and schema integration. Those endpoint/client tests are **pending**, not passed here. The service currently has no discovery paginator, context-switch UI or generated API contract.

Real NGO eligibility/representative evidence, initial independent bootstrap, disputed/last-admin recovery, real regrant approvers and all privileged grant commands remain blocked by ADR D03/D05/D14. Finance, signatory, governance, exceptional support, sharing, sensitive records/files/exports and durable workloads retain their separate gates. There are no membership, volunteer, beneficiary or finance domain models in this slice.

Before any deployment, review least-privilege role provisioning/function ownership, migration credentials, logs/audit-read policy, retention/legal holds, monitoring, incident response, bounded load/lock contention and release flags. No RLS, immutable external audit, support impersonation, production access, legal authorization or G1a/M1 completion is claimed. Database/migration owners and compromised infrastructure remain explicit trust boundaries.
