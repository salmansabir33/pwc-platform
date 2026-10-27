# PWC-04B verification integration review

Status: bounded preparation implementation; no independent approval, production
activation or complete policy-dependent 04B roadmap sign-off. Baseline main c8a1637 (merged PR11).
Assigned branch: arena/1778b1f4-pwc-platform; consolidated PR #12, no auto-merge.

## Delivered safe slice

Four additive models: revision-bound personal VerificationCase with mutually
exclusive 04A draft/claim source; EvidencePreparation non-file boolean marker;
immutable VerificationEvent and VerificationReceipt. Separate eligibility and
representative-mandate purposes and registered/unregistered category snapshots.
Draft/submitted/withdrawn only. No accepted document metadata, reviewer IAM,
review decision, government attestation, public-state or grant writer. See the
[runbook](../runbooks/PWC-04B-NGO-VERIFICATION-AND-EVIDENCE.md) for exact states,
API, minimization and migration/incident boundaries.

## Authority, privacy and dependency review

Case ownership is personal, not NGO membership/administration. Authentication,
current account/session/hold checks, source ownership and revision checks occur
inside the durable transaction with the existing User-first prefix. Atomic
history/receipts have PostgreSQL update/delete guards. Source withdrawal blocks
submission/marker mutations, not applicant withdrawal. Same-key replay returns
current state; no resurrection. One active case per own source/purpose and one
active marker/case are database constrained. Application validation establishes
source/claimant/organization consistency; this is not a restricted DB-writer
architecture or defense against DB owners.

Staff/superuser/legacy NGO admin/Board confer no case-review entitlement. No
reviewer model, provisioning flag, assignment, assessment or approval exists.
Queue adapter always 503 without enumeration. Self/conflict/independence and
reviewer-revocation races cannot be claimed tested for a nonexistent decision
writer; forbidden routes/unavailable adapters are tested instead.

No file bytes are parsed or stored. Filename, URL, hash, notes, reviewer and
asserted approval inputs are rejected. Disabled own upload/download adapters
have no success response, and foreign/missing case/marker stays 404. No media,
public URL, scanner, retention schedule or authenticity automation is supplied.
Synthetic boolean preparation has no evidentiary weight.

All thirty E/GM dispositions remain scoped. E01–E04 rubric/namespace/governance/
reviewer IAM; E06/E07 privacy/storage/retention/scanning; E10 assurance;
E12–E14 disputes/exception/command protocols and E17/E18 reader/activation
contracts still gate their affected implementations. E05 bounds are not new
settings. E08 public consent remains separate. E09/E11 and GM01–GM12 do not
permit grant commands or synthetic-to-real migration. E15/E16 delegation,
finance/alliance and support remain excluded. OPEN-DECISIONS is unchanged: no
new product choice or independent sign-off is fabricated.

## API and clients

15 implemented operations, 12 success contracts plus permanently unavailable
file/reviewer adapters. Frozen 03C/04A contracts unchanged; source hashes, checked
synthetic examples, TS types and Dart DTOs/verification-only manifest refreshed.
Personal native 22-operation allowlist unchanged. No endpoint proposal for
approval is advertised.

React ORG-03 source-bound initiation, own list/status, requirements/history,
preparation add/replace/withdraw, revision-bound submit/withdraw and safe errors;
PWC-01 unavailable view. Flutter parallel preparation/status components and
unavailable review. Both are synthetic-DI tests, not client/server integration.
Mounted W1 networking remains blocked; native credential transport/storage is
unchanged. Private state clears on context/gateway/language changes and ignores
late responses. History/marker views are bounded first pages, not complete
exports; web additionally continues case lists. Unavailable future
needs-information/appeal/decision workflows are explicit rather than mocked
verified success.

## Findings and limits

- Native DTO validation initially did not enforce JSON Schema const/maxItems/
  maximum: corrected with closed unavailable-requirements regression tests.
- Old web route tests expected /verification to be absent: updated only that
  expectation now an explicit unavailable canonical view is mounted; other
  unfinished routes remain absent.
- Pinned Flutter formatting passed at the initial c3747aa checkpoint; four
  analyzer control-flow infos were corrected in fb28553. Final analysis/tests
  and Android builds require exact-head CI confirmation. Local WASM dart_style
  formatting matches existing pinned-formatted source but is not Flutter SDK
  execution.
- CI also exposed stale browser unfinished-route expectations and native
  widget selectors matching purpose buttons as well as case status. The browser
  expectation was corrected to the actual unavailable route; native selectors
  now target case-specific status (without assuming the generated fixture track)
  and scroll before off-screen actions. CI bounded diagnostics now retain failure
  context rather than losing early failures in parallel progress output.
  These corrections require a fresh final-head rerun, not reuse of failed runs.
- No known unresolved Critical/High finding in this bounded slice from the
  agent's review; independent security/privacy/database review is outstanding.
- No physical device/emulator test, real document/NGO authenticity check,
  production load/restore/retention/operational acceptance or external audit is
  implied by synthetic tests or Android compile jobs.

## Executed validation

Local executed evidence (not substitutes for final-head CI):

- PostgreSQL 16.2 additive migration application passed; Django `check`,
  `makemigrations --check --dry-run`, `migrate --plan` (none outstanding),
  `migrate --check` passed.
- Full contract-instrumented regression re-executed at 0894175: **433 tests
  passed**, **266 distinct route/method/status combinations**, 350.854 seconds.
  Earlier run: 429 tests / 258 combinations. Subsequent corrections affected
  client test expectations, not backend runtime/tests.
- Final focused verification suite at c3747aa: **34 tests passed**, 53 wire
  combinations, 43.727 seconds. Includes duplicate creation/retry/submission,
  replacement and submit/withdraw/source-withdrawal races; holds, cross-owner/
  case/download isolation, strict scalar/closed inputs, parser bounds, signed
  context-bound pagination, history/receipt immutability and audit rollback.
- `contracts.check --check`: generation/inventory/source/frozen compatibility,
  OpenAPI 3.1/security/historical keys and request/success examples passed.
- Local `npm run check`: typecheck, Prettier, **121 Vitest tests**, both Vite
  production builds passed. Two new browser scenarios await CI execution.
- Ruff repository check passed. `pip check`, hash-lock checks (12 runtime and
  33 CI pins), six tooling tests, tracked-file security scan (0 findings), and
  npm audits (runtime and full development tree: 0 vulnerabilities) passed.
- Local Flutter SDK/Android tooling/browser runtime are unavailable. Temporary
  npm WASM formatter was used only in ignored scratch storage; no dependency
  manifests/locks were changed. Official pinned Dart format/generation,
  Flutter analysis/tests, Android app/harness builds, browser tests, Python
  3.11/3.12 regression and network-dependent advisory reviews are delegated to
  the existing CI gates, **not asserted passed here before completion**.

Final exact-head check URLs, SHA, counts, any corrected failures and the human
merge verdict are recorded in the [PR #12 evidence thread](https://github.com/salmansabir33/pwc-platform/pull/12).
Treat a pending/cancelled run or an earlier-head green run as no final-head pass.
The review checkpoint is deliberately separated from that final evidence to
avoid circularly claiming CI on a documentation commit it has not tested.

## Readiness and human handoff

Reviewable only as the bounded preparation foundation after exact-head gates
pass. Not complete policy-dependent verification or production readiness.
Independent policy/IAM/privacy/legal/security/operations gates and REAL01–04
remain. Stop before 04C/04D, privileged grants, finance or deployment. Human PR
review and explicit merge decision required; do not auto-merge.

## Revised assignment checkpoint — offline initial rollout, 27 October 2026

The later explicit product-owner instruction supersedes the applicant-driven
initial-rollout expectation above. Base `06f5c74` includes merged PR12; assigned
branch `arena/305ca95a-pwc-platform`. This is one comprehensive revised 04B
assignment, not new user-facing subphases. Historical sections/evidence remain
for provenance and are not a live rollout authorization.

### Scope and implementation review

ADR-0004 §7, PWC-02E §9, OPEN and the existing roadmap record the revised offline
policy. Four additive models/migrations 0007/0008 prepare controlled records,
immutable revisions, purpose-separated external attestations and immutable
actor/session events. Different reviewer account/provenance constraints and an
immutable initiator guard prevent structural self-review bypass. Unique revision
constraints and transaction rollback are tested on actual PostgreSQL.

No live privileged writer, private queue/reader, reviewer provisioning,
invitation delivery/acceptance or grant activation exists. Missing E04/GM
contracts make these adapters unconditionally unavailable, not optionally enabled
by a broad flag. This uses the assignment's explicit disabled-adapter alternative.
The non-writing preflight is not a permission service or evidence rubric.
Two account IDs cannot establish independently vetted distinct individuals.

Default server denial now shuts down applicant creation/edit/submission even
with both old API gates enabled; existing own reads/withdrawal and audit data
remain. Historical success-wire tests explicitly opt into an isolated test-only
exercise; default-rollout tests explicitly turn it off. No environment, browser
or staff/operator bypass is added. OpenAPI preserves historical success DTOs and
adds explicit rollout-policy metadata; old success fixtures do not claim live
availability. New schemas describe only actual requirements/unavailable routes.

OPS PWC-01 has a disabled controlled-onboarding interface and synthetic-only
local preview; no browser networking, document chooser, persistence, real role
or approval success. Native personal operation allowlists remain unchanged;
legacy client components show the initial-rollout policy. The existing W1 and
native-credential boundaries are retained.

### Findings, tests and remaining approvals

Initial focused tests exposed test expectations for GET query/body encoding,
PostgreSQL deferred FK checking and varchar error classification; corrected
without loosening production constraints. Focused controlled suite: **17 tests,
34 observed HTTP combinations passed** on actual PostgreSQL 16.2. The duplicate
snapshot revision race allows exactly one insert; immutable history/initiator,
self-review constraints, reference bounds, atomic rollback, auth/hold/transport/
CSRF and all unavailable operations are covered. This is **not** execution of
unimplemented approval/issuer-revoke/token/grant races or real authenticity.

Full backend/frontend/browser/mobile/Android and final-head CI results are
recorded in the consolidated PR evidence thread after execution. Pending,
cancelled or older-head checks do not constitute exact-head acceptance. No
physical-device, independent privacy/security/legal/IAM/operations review or
production acceptance is inferred. All GM01–GM12 gates and applicable E/REAL
residual gates remain; no new self-approved command matrix, retention schedule,
reviewer appointment or activation path is introduced.

**Readiness:** revised policy and safe domain/API/UI preparation are reviewable
only after validation. Actual controlled onboarding remains blocked on the exact
contracts listed in the revised runbook. Stop before 04C/04D, real grants,
finance, production deployment or any automatic merge.

### Revised validation checkpoint and internal review

Local full contract-instrumented PostgreSQL 16.2 regression: **450 tests passed**,
**288 observed route/method/status combinations**, 463.879 seconds. This began
before the final non-writing draft/returned edit-preflight assertion and preview
bound correction; final exact-head CI must revalidate those changes. Local
focused suite was re-run afterward: **17 tests passed / 34 wire combinations**.
Local web check passed **125 unit tests**, typecheck, Prettier and both production
bundles. Django system checks, additive migrations/application/drift, canonical
contract/source/inventory/frozen compatibility, hash locks (12 runtime / 33 CI
pins), pip consistency, six tooling tests, Ruff, tracked-file security scan (0
findings) and npm advisory audit (0 vulnerabilities) passed.

The HTML Unicode-sets pattern initially failed to enforce the intended opaque
handle bounds because a hyphen needed escaping; fixed and covered by invalid
URL/numeric-only-string tests. This is a syntax bound, not document-number or
PII detection. Local preview history now bounds inside the state updater as
well as the button guard. Independent approve/reject/return adapters remain
unavailable even if the generic availability hook is accidentally made true
or the historical test-exercise setting is injected.

Agent internal review found no known unresolved Critical/High issue in this
bounded revised slice. It is not an independent security/database/privacy/legal
or reviewer-IAM review. Final exact-head GitHub evidence, immutable head SHA,
check URLs/counts and the human-review verdict are recorded in the consolidated
PR #13 thread. Merging policy/preparation never activates real onboarding,
reviewer appointments, invitations, NGO grants or production services.
