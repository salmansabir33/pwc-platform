# PWC-08C-A — public opportunities backend foundation

## Status and exact scope

Implemented Django/DRF + PostgreSQL foundation, **not approved live publishing**.
Based on merged PR49 (`f5fe44519d5d97e514f4415861832f0e8c2bba26`). Inspection
found no reusable opportunity model/endpoint in this baseline. Reuses Organization,
its existing four-field public serializer, workspace eligibility, normalization,
shared database-backed rate budgeting, error envelopes and contract tooling.

Requirements references: roadmap v2 §3 PWC-08C and §4/5; product strategic foundation
§volunteering; draft IA Discover; screen specifications PUB-05/PUB-06 and ORG-16;
backend draft volunteer-opportunity table and illustrative APIs. These drafts
recommend broader volunteering/projects; they do not authorize this task's
publishing workflow, grants or private project domain. ADR-0002, ADR-0004 and the
OPEN-DECISIONS publication/privacy gates remain unchanged. C1 acceptance is unrelated.

### Accepted boundaries versus proposed product choices

- Existing accepted invariants: NGO autonomy, explicit ownership, no inferred
  Board/Founder/staff/superuser/NGO-admin domain powers, no private member projection.
- The assignment authorizes implementation of independently safe foundations using
  its proposed three types, single-NGO ownership and forward lifecycle. Those
  product choices are **implemented as a candidate/test contract**, not recorded as
  separate accountable product/privacy/security acceptance.
- Existing verified-workspace visibility is only the same public eligibility
  **floor** used by the NGO directory, not consent to publish opportunity content.
- `PROJECT` is a discovery item, not a team, joint commitment, project workspace or
  replacement for the broader multi-owner project domain in the product drafts.

## Storage and lifecycle

`opportunities.Opportunity`: UUID PK; required protected Organization FK; `type`
JOB / INTERNSHIP / PROJECT; `state` DRAFT (default) / PUBLISHED / WITHDRAWN;
`title` (200), `summary` (1000, blank permitted), internal normalized `lookup_title`,
UTC `created_at`/`updated_at`, nullable `published_at`/`withdrawn_at`.

Database constraints enforce valid types, nonblank title, nonnull owner, exact state
and timestamp combinations; withdrawn time cannot precede publication. A PostgreSQL
trigger enforces immutable UUID/owner, DRAFT → PUBLISHED → WITHDRAWN updates, no
skipping/reopening, and an immutable publication timestamp after publication.
Partial `(type,id)` and `(organization_id,id)` indexes cover published filters;
UUID primary index supports keyset ordering. Search uses normalized title substring
and owning NGO normalized city; no unapproved contact, notes or roster search.

**No publish/withdraw service, admin registration, management command, role/grant,
background publisher, data migration or seed loader exists.** Tests construct
fictional state fixtures directly via ORM. Database access/model state transitions
are not an authorization mechanism or instructions for operators to publish live.
Any later writer must separately implement accepted authorization, locks,
revocation, revision/audit/idempotency and normalization contracts. `QuerySet.update`
and bulk writes do not maintain the model's normalized search field; no such public
writer is exposed here.

Migration `opportunities.0001_initial` is additive, depends on the existing
organization migration, creates only the new table/indexes/constraints/function/
trigger, and reverses cleanly. Reversal drops opportunity data; do not reverse a
populated installation without reviewed retention/backup decisions.

## Endpoints and explicit public candidate contract

Only `GET /api/v1/opportunities/` and `GET /api/v1/opportunities/{pk}/`.
POST/PUT/PATCH/DELETE/HEAD/OPTIONS return 405; no administrative writer path exists.
Anonymous only: authentication classes empty, AllowAny; no cookies, sessions,
Bearer credentials, grants or platform role are consulted to widen results.
Responses use JSON, `Cache-Control: no-store`, `Referrer-Policy: no-referrer` and
credential-partitioned Vary. Errors use the existing redacted `AuthError` envelope
shape with opportunity-specific availability code, not arbitrary backend text.

Candidate public fields (identical list/detail item):

- `id` (opportunity UUID)
- `organization`: exactly existing `id`, `name`, `city`, `classification`
- `type`: JOB / INTERNSHIP / PROJECT
- `title`, `summary`: bounded plain-text content, not trusted HTML
- `published_at`: UTC timestamp

No state, draft/withdrawal/internal timestamps, lookup fields, applications,
private contacts, evidence, authorization metadata, membership or finance fields.
No private fields are even defined on this first opportunity model.

List parameters: `q` (title only), `city` (owning NGO), exact `type`,
`organization_id` (filter, **not authority**), opaque `cursor`. Unknown/repeated,
control-character/overlong inputs and GET bodies are rejected. q/city are NFKC,
whitespace-normalized, casefolded. q/city <=250 raw characters, cursor <=1024.
Detail rejects queries/GET bodies; missing/draft/withdrawn/ineligible-owner/invalid
IDs all deny without returning the object. Public visibility always requires
PUBLISHED **and** currently verified owning workspace; missing workspaces deny.

Pages: at most 20, ascending UUID, `results` + nullable `next_cursor`; no count.
Signed one-hour cursor binds normalized filters and last UUID. Changed filters,
tampering and expiry reject. Visibility is rechecked on every page/detail; no
cross-request snapshot or guarantee against insertions before the last UUID.
Query execution has a PostgreSQL five-second statement deadline. List/detail
share a 30-request/15-minute IP-derived budget through existing hashed rate limits.

## Live acceptance gate — deliberately unavailable

All reads return **503 OPPORTUNITIES_UNAVAILABLE** outside an explicit isolated
exercise (`PWC_ENVIRONMENT == test` and Django setting
`PWC_OPPORTUNITIES_TEST_EXERCISE is True`). This setting is **not environment-parsed**;
there is no development/staging/production enable switch. Even injected True in
those profiles fails closed before database lookup. Normal test-profile operation
also stays unavailable unless a test explicitly overrides the exercise setting.
This does not change personal/authentication or directory feature flags.

Exact separate acceptance needed before removing this gate:

1. Product owner: type/ownership/lifecycle candidate, PROJECT's limited discovery
   meaning and reopen/edit semantics; no assumption that this covers project teams.
2. NGO governance + trusted issuer/IAM/security: explicit publishing/edit/withdraw
   actions, actor/subject/tenant/source/expiry/revocation matrix and actual accepted
   issuer authority. No title, staff, superuser or NGO role shortcut.
3. NGO/privacy/legal + product: title/summary/timestamp and nested NGO public-field
   allowlist, publication consent/legal basis, responsible content review,
   withdrawal/retention/abuse and owner-visibility integration. Verified != consent.
4. DB/API + security: authenticated writer contracts including assurance, lock order,
   audit, revisions, idempotency/replay and revocation linearization, plus explicit
   acceptance of any live transport/activation change. No writer is proposed here.

This is a bounded acceptance queue for future live publication, not a new general
product/governance cycle. No existing settled C1 decision is reopened.

## Contracts and exclusions

OpenAPI v1 changes are additive; existing frozen operation/schema fingerprints
remain unchanged and new ones are added to the compatibility baseline. Checked
success examples are **test-only**, never response stubs. Source provenance now
covers the new app. TypeScript contracts regenerated; browser network allowlist
unchanged. No Flutter feature, transport, screen or model work: only the existing
generated Dart contract's global SHA changes as mandatory shared-contract
provenance (the deterministic generator binds the complete OpenAPI document).

No applications/saved items/project teams/dashboard/private workspace/publishing
privileges/finance/membership changes, no staging or production deployment.

## Reproducible validation

Use Python 3.11/3.12, hash-locked `requirements-ci.lock` and real PostgreSQL 16.
Do not substitute SQLite. Supply only local fictional secrets and disposable DB.

```sh
python -m pip check
cd apps/backend
python -m contracts.check --check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test opportunities organizations.test_directory organizations.tests organizations.test_public_summary --testrunner contracts.testing.ContractRunner
python manage.py test --testrunner contracts.testing.ContractRunner
# Repository root
ruff check apps/backend scripts tests/tooling
ruff check --select E4,E7,E9,F apps/backend/opportunities
npm run contracts:types:check
```

Coverage includes published list/detail, drafts/withdrawal, every nonpublic NGO
state and missing workspace, A/B filters and credentials/role non-escalation,
Unicode search/types, stable bounded pages, mid-pagination withdrawal, cursor
binding/tamper/expiry, malformed query/body/IDs, redaction, rate limits, write denial,
DB constraints/trigger under ORM bypass, protected owner deletion and actual
migration reversal/reapplication. CI Python 3.11/3.12 executes the full instrumented
suite; mobile CI verifies shared generated-provenance drift. Execution counts,
CI links and limitations are reported in the PR, not guessed here.

## 08C-B continuation — nonwriting publishing preparation

[Issue #51](https://github.com/salmansabir33/pwc-platform/issues/51) records the
Founder's “ok” to seven product rules on 6 November 2026. This supersedes the
08C-A *pending product* disposition above only: single NGO ownership; three types
with PROJECT limited to discovery; explicitly authorized officer draft/request
preparation (not creation of that authority); published-only/NGO-eligible discovery;
withdrawal removes discovery/detail; no reopening or republishing withdrawn v1
records; and the existing candidate public projection. Exact published-content
editing/version semantics remain open. No independent privacy/legal/IAM/DB security
or live-activation acceptance is inferred; no signer/evidence is invented here.

`opportunities.preparation` now provides two **internal, nonwriting** functions:

- `prepare_draft(organization_id, payload, opportunity_id=None)` validates a new
  draft or a nonempty partial edit to an existing DRAFT. Only type/title/summary
  are accepted. It reuses existing bounded text normalization and model-derived
  limits/choices; title lookup uses the same normalization as `Opportunity.save`.
- `propose_transition(organization_id, opportunity_id, operation, effective_at=...)`
  accepts only `request_publication` from DRAFT or `withdraw` from PUBLISHED.
  Returned PUBLISHED/WITHDRAWN states are **desired simulation outcomes**, not
  approval or state changes. `publish`, `approve`, reopening, republishing and
  published-content edits are rejected. The supplied aware clock is converted to
  UTC, never represented as authoritative transaction time.

Existing snapshots are freshly queried with **both NGO and opportunity IDs** before
content/state checks; a missing/wrong-NGO source gives the same redacted diagnostic.
IDs constrain data selection; **they are not permission**. The module is not routed,
exported through an API, installed as a writer, or usable as an authorization proof.
It has no actor/grant/issuer/staff override. Frozen, redacted-repr proposal values
have no save/apply/public-preview methods and `live_execution_available` is always
False. Do not log or publicly serialize their draft content.

Field/FK and lifecycle/date constraints are evaluated with the existing model's
`full_clean`, rather than introducing a second schema or relaxing PostgreSQL.
Source-to-target checks are necessary for a nonwriting proposal: the existing
forward-transition trigger cannot be invoked without writing. That trigger remains
unchanged and is exercised separately in fictional-fixture database tests. Model
validation may use SELECTs and savepoint bookkeeping, never speculative writes.

No model/migration/HTTP contract/serializer/public gate/client changes. Only source
provenance is regenerated for the new Python module; the OpenAPI contract itself
is unchanged. `python manage.py test opportunities` covers normalization, partial
preparation, malformed/unknown fields, immutable ownership/tenant lookup, lifecycle
matrix, aware clocks, redacted immutable results, SELECT/savepoint-only validation,
fresh snapshots, agreement with existing DB guards, unchanged public projections
and the existing live-read 503 gate.

**Remaining precise approvals, not product reapproval:** accountable NGO governance
and trusted IAM/security must accept exact create/edit/request/publish/withdraw
actor/issuer/source/tenant/expiry/revocation rules and the approval path; privacy/
legal + product must accept actual field disclosure, consent/content safeguarding,
audiences, retention/incident/withdrawal policy and NGO visibility integration;
DB/API security must accept restricted writers, locks/revocation fence, revision/
audit/receipt/idempotency/authorization contracts and live-read activation criteria.
Published-content edits/versioning remain unimplemented pending exact acceptance.
A future writer must re-read/revalidate under those accepted contracts: proposals
can become stale and are neither locked state nor signed receipts. Browser/native
integration awaits accepted live endpoints/source. C1/04C/GM remain untouched.
