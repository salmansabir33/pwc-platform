# PWC-03B — authorization foundation integration review

**Date:** 24 October 2026

**Verdict: READY FOR A BOUNDED, HUMAN-REVIEWED FOUNDATION PR; NOT PRODUCTION OR PWC-03B.3 APPROVAL.**

**Reviewed implementation:** PWC-03B.2 `c443b60aa12eb7a5d63f6d2d2f4448eaf29815e6`, including PWC-03B.1 `b42bd0ec791f766aaf83fb9c5102d9bb9376e9d0` and approved architecture checkpoint `e7b930fcf2403af09d92fb3f9ae18d8b8f922f41`.

**Branch:** `arena/d8a3e024-pwc-platform`. This review does not create or merge a PR.

## 1. Repository verification and review method

The initial index/working tree were clean. Fetches of `origin/main` and the remote feature branch confirmed local HEAD and the remote feature checkpoint both equal the full 03B.2 SHA above. No older-checkout restoration or reconciliation was needed. Commit ancestry retains 03B.1 and the approved ADR. The reviewed feature branch is an explicit dependent branch containing both slices; they have not been assumed to be separately merged into main.

Inspected root [AGENTS](../../AGENTS.md), [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), [ADR-0002](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), [ADR-0001](../decisions/ADR-0001-authentication-and-recovery.md), identity/data-model references, both implementation runbooks, the actual models/migrations/SQL privilege template, central services, authentication call graph, URL/views/input grammar, checked JSON fixture and security/concurrency tests. Historical root/roadmap branch/auth status prose was not used to replace the actual merged authentication implementation.

This is a source/test/contract review, not independent penetration certification. Existing 03B.1/03B.2 behavior was tested afresh; historical reported test counts were not accepted as current evidence. No confirmed defect requiring an in-scope implementation change was found. Accordingly this review changes documentation only: no speculative refactoring, new feature, migration, model, permission or authentication alteration. No new regression test is claimed for a nonexistent code fix; the existing negative/regression suites were executed.

Approved ADR hashes remain:

- ADR-0001 authentication: `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
- ADR-0002 authorization: `93d30e1169c2ac0654803348ae4a01450b2fa4902b414a517b050692376a834f`.

## 2. Scope and architecture alignment

| Reference / approved boundary | Implementation assessment |
|---|---|
| ADR-0002 D01: explicit personal/NGO context, all other kinds denied | Typed identifier resolution, Organization UUID path authority; no generic nullable tenant, remembered selection or default tenant. Personal action dispatch remains owned by accounts. |
| D02: closed minimal bundles and current DB authority | Exactly three read atoms and two pinned immutable v1 synthetic bundles; DB constraints reject other bundle pairs. Same-tenant union only, no delegation, wildcard, custom role or business-admin inheritance. |
| D03/D14: provenance and no legacy promotion | New synthetic accounts/organizations are created by the offline factory; batch/evidence/source recorded. No grant backfill from legacy access/membership/admin/Board/contact/import labels. Real verification/regrant decisions remain blocked. |
| D05 / ADR-0001: auth is not NGO authority | PersonalAuthentication is invoked inside the durable domain read transaction, not trusted from an earlier view check. Current session/epoch/factor/credential deadlines and clear hold remain necessary. No NGO proof operation or privileged command exists. |
| D09: only fixed synthetic private category | Probe/settings contain only organization UUID, fixed code/label and revision. No beneficiary, people, finance, file or evidence payloads. |
| D11: scoped discovery/capabilities/errors and no authority from selection | Exact approved routes, closed request grammar, minimized JSON, current capability projections, signed keyset pagination and no-store headers. No select route or persistence. |
| D13: PostgreSQL primary, locks/revisions/audit/fail-closed | READ COMMITTED/default primary only, no routers/positive cache, shared lock roots, DB wall-clock expiry, atomic lifecycle/audit, terminal revocation and explicit denial/unavailability behavior. |
| Roadmap P2 / P3 separation | P2 synthetic kernel/HTTP foundation exists. Real representative verification, bootstrap, invitations/team grants and transfer/recovery remain later P3 policy/work. Finance P6 and alliance/legal commitments P7 are not implemented. |
| Roadmap 03C/03D | Checked narrow wire fixtures exist; no generated OpenAPI/client SDK, private-file release, Flutter/Web screens or real-client cache-switch acceptance is claimed. |

Core architecture approval is not approval of all ADR future-model catalogs or institutional policies. The existing read-only synthetic scope can integrate without resolving privileged command policy first.

## 3. Security findings and evidence

### F01 — Tenant and object isolation: satisfactory within implemented singleton surface

The HTTP view maps each route to a server constant; it does not accept a client action. `evaluate` validates the path context, locks its state, checks principal/state batch and workspace eligibility, and fetches only that subject's unrevoked grants in that organization/batch. Direct-object probes query the tenant-prefiltered state before matching the target. The same person can have admin-probe in A and reader in B without carrying settings permission across tenants.

Unknown/foreign/absent/ungranted/ineligible NGO/object responses share the redacted 404 contract. Missing action becomes 403 only inside an entered NGO. Malformed inputs become 400 after authentication; invalid auth remains 401. No grant/NGO UUID or revision is included in error bodies. Default-off registered endpoints return no-store 404 before authority evaluation. Unregistered URLs retain ordinary Django 404, not a falsely claimed universal JSON error contract.

**Evidence:** K01–K05 tests, real HTTP A/B/unknown tests, strict query/body/header negatives and response-key fixture checks. This proves the singleton synthetic state/probe surface, not arbitrary future related-object joins, member lists, business writes or files.

### F02 — Current grants, revocation and holds: satisfactory within scope

No legacy `OrganizationAccess`, Group, staff/superuser, Board/membership/volunteer label or MFA observation is consulted for an allow. Allowlists use only known live grants with matching synthetic provenance/verification and expiry. A valid accepted TOTP observation without an NGO grant still denies, and admin-probe cannot obtain finance powers. Role v1 cannot silently expand; grant scope/source/role/provenance/validity are immutable.

Revocation takes effect on newly authorized operations after its commit. A read serialized first can finish; the review does not promise recall of already returned bytes. Expiry is rechecked with `clock_timestamp()` after lock waits and before the final decision, independently of revision changes. Session original credential/idle/absolute cutoffs are captured without extending them. Held/recovery-code sessions cannot use private NGO contexts; fresh MFA does not clear hold or replace permission.

**Evidence:** K03/K04/K06/K07/K09/K14; HTTP immediate revocation/stale capabilities/session/hold/expiry cases; accepted-TOTP negative; two-connection grant/auth transitions.

### F03 — Transaction and helper lock integration: satisfactory for these commands

The adapter's nested `atomic` remains inside the kernel's durable top-level transaction, retaining locks through projection and audit. Current read lock order is User → active contact → AuthSession/access credential → tenant state; factors are checked under the User serialization lock, not falsely claimed as independently locked on every read. Existing factor/reset/hold lifecycle writers use the User prefix. No auth lock-acquiring helper is called after a tenant root. Fixture issue/revoke locks its subject User before state/grant; disable needs only its root and takes no later User lock. Discovery acquires at most 50 roots in sorted Organization UUID order.

Runtime uses an explicitly permissioned fixed-search-path SECURITY DEFINER function to lock state without direct table UPDATE privilege. It only selects/locks a typed tenant row, uses a fully qualified table and has no PUBLIC execution. Trigger functions also fix their search path. New human actor+recipient commands cannot simply reuse the single-subject fixture lock path; all involved Users and proof/source locks must be designed first.

**Evidence:** separate PostgreSQL connections with Barriers/Events and observed `pg_blocking_pids`; both read/revoke orders, competing creation/revocation, expiry during root wait, auth epoch/logout/hold/refresh races, timeout tests and actual restricted-role reads. PostgreSQL locks, not mocked mutexes, arbitrate the races.

### F04 — Audit rollback, durable evidence and error minimization: satisfactory with stated outage limits

Successful read/transition evidence is inserted in the same transaction. Audit insertion failure prevents a protected result and rolls back a lifecycle mutation. A final deadline failure rolls back provisional allow evidence. Discovery returns redacted 409 if an already evaluated supporting grant expires before final release; no partial page is returned. An empty discovery page records a denial of NGO authority (`no_eligible_contexts`) while returning HTTP 200 enumeration success, rather than fabricating a null-context grant-backed allow.

SQL constraints/triggers protect immutable attestations/grants/events, tenant/batch/role audit linkage, session actor ownership and terminal revocation. Used access history blocks destructive reversal. Expected revision checks and transition-plus-audit semantics are service guarantees under locks, not claims that arbitrary fixture-writer SQL must produce a complete business audit.

Denial audit is separately attempted after rollback. If DB/audit availability itself fails, 503 and correlation-only telemetry are fail-closed output, not proof that a durable denial event exists. No secret, raw private body or foreign object is echoed. There is no exactly-once HTTP response/commit guarantee.

**Evidence:** K10/K12/K13 and HTTP audit/DB failure, final deadline, 409 rollback, restricted roles and migration preservation cases.

### F05 — Synthetic boundary and absence of HTTP grant authority: satisfactory with operator trust

Two independent default-off switches plus isolated environment/database-name checks do not replace attestation/grants. The factory creates new synthetic identities/tenants; its verified contacts are explicitly synthetic `.invalid` fixtures, not real verification. Runtime cannot insert/update grants/state/attestations through the provided DB role template. No public admin site, management command or route exposes the fixture writer. All registered context routes allow only GET/HEAD, and no closed role contains a grant-management action.

Inspected the actual route map and write-method rejection tests: HTTP clients cannot issue, replace, revoke or delegate NGO grants. A new `AuthorizationEvent` read audit is not a grant mutation. Existing migrations preserve old users, workspace IDs, passwords/FKs and legacy rows without granting them authority.

**Evidence:** K11–K13, default-off tests, real/unattested record negatives, absent grant/finance/support routes and actual runtime role SQL/HTTP tests. This is an application/release boundary, not protection against an operator who controls configuration, privileged fixture credentials or the DB owner.

### F06 — Discovery, capability and input contracts: satisfactory within synthetic disclosure policy

Discovery considers only the caller's current eligible grant candidates, not another user's grants or all organizations. It scans at most 51 candidate UUIDs, locks/evaluates at most 50 roots and returns no names, total counts, people or grant IDs. Every page reauthenticates/rechecks; cursor/revision/capability data is never a bearer permission. A one-hour cursor is signed and bound to User/logical session, with tamper/expiry/session-substitution rejection. Changing grants between pages is allowed; this is not snapshot pagination.

Input grammar rejects GET bodies, conflicting or matching redundant tenant identifiers, role/action/capability header families, field wildcards and unknown/duplicate query fields. Only discovery accepts cursor. If-Match/If-None-Match on reads cannot authorize or cause cached 304. Output is fixed JSON, no-store, no-referrer and varied on credentials; no debug/browsable serializer or arbitrary field selection.

**Disclosure qualification:** signatures provide integrity, not confidentiality. Cursor payloads can be decoded to the caller's User/session IDs and last scanned Organization UUID. A scan position may refer to an own-grant candidate omitted by the final eligibility check, as documented for empty/short pages. No other principal's candidate set is queried, but this must not be promoted to a claim of encrypted metadata or real-data non-disclosure after every expiry. See R03 below.

**Evidence:** 51-candidate pagination, current continuation after revocation, malformed/tampered/expired/copied cursor tests, exact wire-key fixture and bounded/sorted root test.

## 4. Remaining risks and release gates

None below is a confirmed blocker for merging the **default-off, synthetic-only** foundation. They remain concrete limits, not waived production requirements.

| ID | Risk / limitation | Required handling |
|---|---|---|
| R01 — database and configuration trust | Shared-schema application isolation is not RLS or defense against a compromised runtime SQL connection, owner, migration operator or fixture writer. The role template is not automatically provisioned deployment infrastructure. | Before activation, review actual credentials, membership/default privileges, function ownership/EXECUTE/search path, schema/DDL/TRUNCATE powers and isolated environments. Never give HTTP workers owner/fixture credentials. |
| R02 — lock/load availability | User/exclusive tenant locks serialize reads and revocation. A page can involve 50 roots and multiple SQL statements per entry. The 2s lock/5s statement timeouts apply per statement, not a 5s total HTTP transaction deadline. Small deterministic races are not throughput/load certification. | Establish load/latency/total budget targets, measure contention and audit costs before broader activation. Do not optimize away root/deadline checks without equivalence tests. |
| R03 — pagination metadata | Signed cursors are readable and may preserve an omitted own-candidate scan UUID; they are pagination hints, not confidential storage or authority. Client URLs/analytics can retain them. | Do not log cursors as credentials or rely on their secrecy. Approve real-data metadata/retention policy (D09), and redesign opaque/encrypted position semantics if that policy requires it, before real-data use. |
| R04 — audit availability/growth | Authenticated reads and denial attempts append events; no new read-endpoint throttling, production retention/purge, monitoring or external tamper-evident store is supplied. Enabling public synthetic endpoints can still consume DB/audit capacity. DB outage cannot persist every denial. | Keep endpoints default-off/isolated. Define abuse/rate budgets, alerting, retention/legal holds, DB capacity and infrastructure audit controls before public/real activation. No unapproved purge/ratelimit numbers were invented in this review. |
| R05 — unsupported domain coverage | Probes are singleton fixed synthetic resources, not memberships, private joins, finance, sharing, files, reports, exports or workload execution. No client implementation proves cache switching. | Add scoped field/object/parent ownership tests with each actual feature; retain future AZ cases as pending rather than certify absent features. |
| R06 — operational schema lifecycle | Kernel workspace state is intentionally frozen against legacy writers; terminal kernel disable is the supported shutdown. Used-history reversal refuses rollback. | Any new lifecycle writer needs root revision/audit/locking review. Disable/drain and use reviewed forward fixes/restore rather than delete evidence or revive legacy authority. |
| R07 — future command authority | No issuer command atoms, real mandates, human grant provenance or nonpersonal intent integration exist. Current source fields/process and fixture privileges are deliberately synthetic. | Resolve the separate GM register before commands. No runtime role broadening, v1 mutation, admin-probe promotion or personal MFA registry shortcut. |

No real verification, finance, signatory, governance, support, sharing, export or workload feature is certified by this review. Core approval and passing tests do not close D03–D10/D12–D14's remaining institutional/operational scopes.

## 5. Fresh validation evidence

Local environment: Python **3.11.2**, Django **5.2.18**, PostgreSQL **16.2**, primary READ COMMITTED. Existing pinned dependency set unchanged. Sandbox PostgreSQL is supplied by an external development-only pgserver installation, not a new application dependency. Django test databases contain synthetic data and are created/dropped by the suite; tests include actual restricted SET ROLE credentials, not only superuser behavior.

Executed from `apps/backend` with environment-supplied settings:

```sh
python manage.py test --verbosity 1
python manage.py test access --verbosity 1
# Repeated three times:
python manage.py test access.test_http.ContextHTTPRaceTests access.tests.KernelRaceTests --verbosity 1
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python -m pip check
```

| Check | Fresh result |
|---|---|
| Full PostgreSQL backend | **336 PASS**, 257.620s: 247 existing auth/public + 45 kernel + 44 HTTP tests. No failures or skips. |
| Focused access security/integration | **89 PASS**, 28.657s. Includes actual HTTP, constraints, migration/reversal and restricted role cases. |
| Focused race/lock-order subset | **16 PASS in each of 3 additional runs** (48 repeated executions), 7.245s / 7.182s / 7.354s. Includes six HTTP/routing-lock cases and ten kernel/auth race cases. |
| System checks | No issues. |
| Migration drift | No changes detected. |
| Migration plan/application/pending check | No planned or unapplied operations. Fresh suite DBs also apply the unchanged access migrations. |
| Dependencies | No broken requirements. |
| Documentation/source preservation | Approved ADRs and every tracked runtime/fixture/migration source at the reviewed checkpoint remain unchanged in this review; document links/whitespace checked at handoff. |

GitHub independently reports implementation checkpoint CI **success**, run [40096979501](https://github.com/salmansabir33/pwc-platform/actions/runs/40096979501), with both `django (3.11)` and `django (3.12)` completed successfully. That is remote implementation evidence, not a claim that Python 3.12/Docker ran in this sandbox. The later documentation-review commit must receive its own normal CI checks before merge; do not infer them from the older run.

No real browser/mobile secure-storage/session-navigation, SMTP delivery, production deployment, load/chaos, timing-side-channel or external penetration test was performed. Controlled fault injection and deterministic locks are not those certifications.

## 6. Acceptance coverage and gaps

K01–K15 are covered for the synthetic service/HTTP slice by the combined tests: A/B query and singleton direct-object isolation, same-user independent grants, non-inheritance, live auth/hold/expiry, preconditions/revocation, immutable DB history and actual privileges, atomic audit/fail-closed output, signed pagination, sorted locks and fresh auth regressions.

This is partial realization of AZ-01/02/03/04/05/08/10/11/12/13/14/18/19/26/28/29/30 as applicable to the implemented read surface. For example no finance allow-path, member import, parent delegation chain, commitment, file/export or durable workload case was executed because those features do not exist. Existing legacy/Group labels stand in for absent membership/volunteering/Board domain models; that is not live institutional acceptance. Full G1a still includes client context-switch/cache behavior; G1/M1 additionally requires later trust/onboarding/membership workflows. Neither milestone is declared complete here.

## 7. Merge and next-slice recommendation

**Independently merge-ready:** yes, for the bounded default-off synthetic foundation, subject to human code/migration/privilege review and green checks on the actual final PR head. No unresolved GM approval is a prerequisite to merging code that cannot execute those commands.

Recommend a PR from this existing branch into main titled along the lines of **“PWC-03B: integrate default-off synthetic authorization foundation.”** Include approved ADR-0002/history, 03B.1/03B.2 implementation, tests, runbooks, checked fixture and these two review documents. Exclude any activation flags, real data, new roles, nonpersonal proof registration, command endpoints or production claims. Review the security-definer function, triggers, migration reverse guard, runtime role template and centralized transaction boundary explicitly. No PR or merge is performed by this assignment.

**PWC-03B.3 is not implementation-ready.** Use the separately maintained [privileged grant decision register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md) for the precise product/security approvals. The next policy assignment should be a design-only, explicitly scoped command approval pack. If/when approved and assigned, privileged commands belong in a separate later PR, with new reviewed actions/versions/provenance/assurance/privilege contracts and their own negative PostgreSQL race tests. Do not turn an offline fixture method into an HTTP command.

This verdict is a review recommendation, not owner approval of institutional policy, production activation or privileged workflows. Review deliverables are documentation-only and are committed/pushed on the existing feature branch; the final handoff reports that new GitHub checkpoint separately from the pinned implementation reviewed above.
