# P4 membership workbench — implementation checkpoint

Baseline: merged PR38, `6aea981b951afb4916397fc197efff0905f0ce9f`.
This builds on 05A/05B, not replacement authentication, authorization or clients.
Product Foundation §6 remains authoritative with its provisional [S]/[R] labels.
The precise live dependencies in [05A's report](PWC-05A-MEMBERSHIP-FOUNDATIONS.md#exact-contracts-still-required-before-live-implementation)
remain unresolved; this assignment permits independently safe non-authoritative
implementation, not inferred permission to install protected membership writers.

## Delivered business journeys

`organizations.membership_workbench` composes the existing admission evaluator,
CSV parser, category catalog, reference validation and redacted reports:

1. Hypothetical application → pending → proposed acceptance; a projected unclaimed
   member fixture appears only in an immutable returned object. Open and invitation
   fixture paths reuse the existing 05A evaluator. No User, grant or DB row appears.
2. Assign another active category; preserve original admission history. Unknown,
   inactive and unchanged categories reject. Ended fixtures cannot change category.
3. Active → suspended → active, active/suspended → ended. Ended is terminal in this
   synthetic matrix. No renewal, fee, finance, role or account state is inferred.
4. Keep per-record immutable history and separate record/global revisions. Reporting
   excludes subject handles, category handles, names, contacts, tenant UUIDs and source
   hashes. Internal `history_for` is a fixture filter, not a private-history API.
5. Bind every proposal to a source fingerprint covering the full policy, tenant,
   requests, members and history. Changed source rejects with a constant value-free
   `SOURCE_REVISION_CONFLICT`; source hashes never enter client bundles or telemetry.
6. Feed existing CSV validation into admission preparation: preserve column/record/
   related-record diagnostics, then check pending conflicts and policy. Candidates
   are not staged, imported or admitted. Repeated references/formula cells reject;
   malformed CSV still raises the original value-free fatal diagnostics.

**Important concurrency boundary:** pure projections do not claim a durable CAS
winner. Two concurrent proposals against one immutable source may both be valid;
using the old token against a projected successor rejects. The PostgreSQL test runs
parallel fixture evaluation inside actual independent transactions, asserts zero
queries during evaluation and unchanged organization/User/access counts. It does
not pretend to test an absent membership commit/locking implementation. Existing
kernel transaction/locking regressions remain in the complete suite.

All new states and transitions are internal synthetic proposals, not accepted live
membership policy. All projections report `non_authoritative=true` and
`commit_available=false`. Fixture containers are bounded (200 members/requests/
categories and 1,000 history events); these are not approved real NGO quotas.
There are **no new Django models, migrations, persistence services, permissions,
privileged endpoints, live roster reads or administrator shortcuts**.

## Integrated clients without live data or privilege

React: NGO portal `/foundation/membership`, linked from the existing overview.
Flutter: authenticated personal navigation → Membership demonstration →
`/membership-preparation`; existing session redirect remains unchanged.
Both use the existing design system and English/Urdu presentation. They show five
fixed redacted journeys: admission, category assignment, status/history, stale source
and CSV/admission preparation. Selection is local read-only specimen navigation,
not a workflow action. Category save, admission approval, status change, import and
claim/link controls remain disabled. No file selector, text intake, request gateway,
native operation allowlist, credential handling or browser/native networking is added.
The React route exposes fictional counts/codes only, never private member information.
It is not a live membership route or new public NGO-profile disclosure.

`scripts/membership_demonstrations.py` generates a fixed JSON fixture and embedded
Dart equivalent from backend evaluations. It accepts no arbitrary data/scenario/file
input. `--check` verifies exact parity; backend tests enforce it. This is **not**
OpenAPI registration or a new accepted wire API. No TypeScript/Dart HTTP model or
public directory field changes. Do not serialize domain fixtures with `asdict`:
only the explicit summaries are safe. Source hashing uses private values in memory,
not authorization, identity proof or report exports.

## Status by ticket — P4 is NOT complete

| Ticket | Status | Delivered / missing |
| --- | --- | --- |
| 05A | Partially implemented | Category/admission validation plus member/status/category/history fixture projections; live policy, schema and administrative commands lack accepted contracts. |
| 05B | Partially implemented | Bounded CSV template/parser/diagnostics and admission-preparation integration; XLSX, authorized staging, approval, atomic creation, retry/audit/undo absent. |
| 05C | Blocked by identified contracts | No claim/link service or proof intake. Client boundary remains disabled; verified identity/recipient proof, single-use expiry, conflict/recovery and authorization contracts required. |
| 05D | Partially implemented | Integrated English/Urdu, accessible read-only synthetic React/Flutter preparation screens; no live membership client transport, member data or operational workflows. |
| 05E | Partially implemented | Automated domain, PostgreSQL, parity and client regressions; not a live two-NGO M1 journey, manual accessibility/native acceptance or owner UAT. |

No ticket is marked fully implemented and accepted. Code/test success is not
operational approval or locked 04C accountable acceptance.

## Exact next functional milestone and contracts

The next live milestone is **one tenant-scoped, authorized admission command and
private member projection**, then versioned category/status operations and atomic
staging/import as separately authorized extensions. Its dependencies are:

- Accepted category identity/normalization/history, required personal fields,
  duplicate/multiple-category/reapplication scope, all mode-specific invitation
  semantics and complete member/application status and category-change tables.
- Exact issuer/action/target and trusted policy/roster provenance; assurance,
  recipient/reviewer binding, revocation, tenant ownership and read/export scopes.
  Existing context grants, staff/superuser, Board status or synthetic fixtures do
  not confer these capabilities. No generic new sign-off round is requested.
- Reviewed member/category/request schema constraints and restricted writer;
  source/request revision locking, atomic concurrent duplicate protection, audit
  history/readers, idempotency/replay/failure/transaction/outbox protocol.
- Privacy/intake/minimized fields, consent/legal basis, retention/deletion, notices;
  private API and separate approved React/native transport contracts before live UI.
- Independent 05C verified identity plus recipient-bound controlled single-use proof
  or approved NGO decision, expiry/collision/replay/mismatch/recovery and preserved
  membership history. Matching a name/contact never links a user.

Staging, import approval, atomic membership creation and verified claiming remain
separate. No finance or new grant activation. Locked 04C §12/F1–F9/E05 and AUTH/E/
GM/REAL gates, four-field public disclosure and prior audit evidence stay unchanged.
Contabo/Oracle and deployment are outside this checkpoint. Autonomous merge is
conditional on required checks and branch policy; the unresolved unsuppressed npm
audit failure is not waived by this assignment.
