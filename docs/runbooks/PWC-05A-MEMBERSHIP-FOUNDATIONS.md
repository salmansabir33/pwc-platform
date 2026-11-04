# PWC-05A membership foundations — nonwriting domain preparation

## Requirements inspected and smallest safe capability

Baseline: merged PR37 / main `77e7bb29b56dc292954ee1685fb7cb7a55a5116e`.
The requirements authority is the [Product Foundation §6](../product/PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md#6-independent-ngo-membership-management):
NGO-configurable Open / Approval Required / Invitation Only, configurable categories,
no automatic account creation, private ordinary rosters. These are **[S] provisional
product selections**, not live command approval. §6.2 recommends separating member,
renewal/payment status and platform permissions. No fixed universal category list
or authoritative application-transition table was found.

Design references: [identity foundation §5.2](../product/PWC_Identity_Authorization_and_Multi_NGO_Data_Model_Foundation_v1.0_Draft.md#52-independent-ngo-members),
[schema inventory §7.1](../product/PWC_Django_Backend_and_PostgreSQL_Schema_Foundation_v1.0_Draft.md#71-ngo-membership),
ORG-07–09/12 in the detailed screen specification, M1-05 in the readiness backlog,
and [roadmap P4](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md#p4--ngo-membersimports-and-complete-m1-walkthrough).
They guide tenant-bound categories, normalized active-label conflicts and duplicate
admission protection; they do not independently approve writers or state rules.
The current authorization registry still contains only context/private-stub/settings
synthetic reads, not member/category/admission actions.

The independently implementable capability is now **category-snapshot validation
and hypothetical admission-transition evaluation**, beyond CSV structural preview.
`organizations.membership_preview` is pure Python with no database, actor, identity,
finance or transport dependency. Frozen fixtures and a bounded, redacted result
are useful for testing domain behavior, not an executable membership service.

## Implemented internal fixture contract

- `CategoryFixture`: owning NGO UUID, bounded reference, label and active flag.
  No fee, role, grant, contact or user field. References reuse 05B's
  `valid_reference` syntax unchanged. Active labels conflict after NFKC, whitespace
  collapse and case-folding; duplicate references conflict even if inactive.
  Inactive labels may overlap historical labels. These are synthetic v1 rules,
  not a new canonical category taxonomy or accepted live normalization policy.
- `AdmissionRequestFixture`: owning NGO UUID, request/person-record/category
  references, route and preparation state. Handles are not identity evidence.
- `MembershipSnapshotFixture`: NGO, mode, categories, requests, existing references
  and active flag. Nested values must be immutable and ownership-consistent.
  Duplicate request handles, multiple pending/accepted requests for the same record,
  pending-vs-existing member conflicts and missing historical categories reject.
  Accepted history can coexist with its existing member handle without double count.
  Terminal declined/cancelled history does not create a membership.
- Technical fixture bounds: up to 200 categories, requests and existing handles,
  at least one category, handle length at most 64 and label length at most 250.
  These bounds are not real NGO quotas or a roster storage design.

`evaluate_admission(snapshot, request, event)` returns an immutable `AdmissionPreview`
without applying it. The **synthetic v1** matrix is deliberately limited:

| Mode / route | Current preparation state | Hypothetical event | Proposed state |
| --- | --- | --- | --- |
| open / application | draft | apply | accepted |
| approval / application | draft | apply | pending |
| approval / application | pending | approve | accepted |
| approval / application | pending | decline / cancel | declined / cancelled |
| invitation / invitation | draft | invite | pending |
| invitation / invitation | pending | accept | accepted |
| invitation / invitation | pending | decline / cancel | declined / cancelled |

All other transitions fail closed. Invitations under open/approval modes are outside
this fixture's supported paths, **not an approved product prohibition**. This does
not implement renewal, expiry, suspension, category changes, reinstatement, reviewer
rights or invitation delivery/recipient binding. `accepted` is a proposed request
state, never an active membership, grant, payment result or persisted decision.

Checks fail at the first deterministic conflict: type/shape, tenant, event, policy
active state, exact stored-request equality, category, supported route/transition,
then existing/pending/accepted record conflicts. Pending decisions require an exact
stored request; a caller cannot invent a pending state or overwrite a request handle.
Terminal replay rejects; this is **not** a live revision, concurrency or idempotency
protocol. Duplicate scope is conservatively per NGO/person-handle across categories
in this fixture; live multiple-category and identity-resolution semantics remain open.
Even cancel/decline proposals require valid active policy/category and an unconflicted
snapshot; no live cancellation exception or recovery policy is inferred.

Stable errors: `INVALID_INPUT`, `TENANT_MISMATCH`, `DUPLICATE_CATEGORY_REFERENCE`,
`DUPLICATE_CATEGORY_LABEL`, `DUPLICATE_REQUEST_REFERENCE`, `DUPLICATE_REFERENCE`,
`UNKNOWN_CATEGORY`, `INACTIVE_CATEGORY`, `INACTIVE_POLICY`, `UNSUPPORTED_EVENT`,
`MODE_ROUTE_CONFLICT`, `INVALID_TRANSITION`, `STALE_REQUEST`, `UNKNOWN_REQUEST`,
`EXISTING_REFERENCE`. Malformed snapshots raise constant-message
`MembershipPreviewError` with a value-free code; evaluation conflicts return codes.

`to_summary()` yields `format: pwc.membership-admission-preview.internal.v1`, the
snapshot NGO UUID, `transition_valid`, `proposed_state`, code-only `errors`,
`non_authoritative: true` and `commit_available: false`. It never serializes labels,
request/member/category handles, names or contacts; reprs hide fixture values.
The fresh summary cannot mutate its immutable source. Never export fixture
`dataclasses.asdict()` values. This is an **internal contract, not a public API**.

## Working synthetic demonstration and 05B reuse

```sh
python apps/backend/manage.py preview_membership_fixture --scenario open
python apps/backend/manage.py preview_membership_fixture --scenario approval
python apps/backend/manage.py preview_membership_fixture --scenario invitation
python apps/backend/manage.py preview_membership_fixture --scenario conflict
```

Only these fixed fictional scenarios are accepted, including programmatic callers.
The first three emit redacted proposed steps and exit 0; conflict emits a duplicate
error and exits nonzero. Approval/invitation examples use independently fixed draft
and pending snapshots, not a writer applying a transition. No file/data input option
or endpoint exists. The CLI adds `synthetic_only: true`; arbitrary caller-supplied
fixtures are non-authoritative, not magically attested synthetic or authenticated.

`MembershipSnapshotFixture.to_import_catalog()` returns the existing immutable
05B `PreviewCatalog` of active categories and existing/accepted handles, bound to
the same NGO. The original parser/report/template remain the only CSV engine.
Pending requests are not members: a CSV row can be structurally accepted while
05A admission correctly rejects its pending conflict. Neither result bypasses
admission, privacy or authority. No new import path, commit, upload or wire adapter.

## Exact contracts still required before live implementation

1. **Category/policy semantics:** authoritative stable category identifiers, active
   label uniqueness/normalization/history, policy versions/effective changes,
   supported invitation routes under each mode, required fields, duplicate scope,
   reapplication/category changes and complete member/application transition tables.
   Fee/renewal configuration needs accepted currency/precision/effective/history
   rules separately; payment/ledger operations remain P6 and are not implemented.
2. **Authority and trusted source:** explicit member/category/policy/application/
   invite/admin actions; actor/issuer/target matrix, trusted policy/roster provenance,
   tenant ownership, current grant/revocation checks and read/export privacy scopes.
   Existing synthetic grants, staff/superuser, Board status and category labels supply
   none of these rights. Live administrative actions remain blocked, not just rollout.
3. **Persistence/commands:** reviewed schema/constraints for per-NGO references and
   category ownership, atomic duplicate/concurrent-admission protection, locked
   policy/request revisions, audit readers/history, idempotency/replay/error contracts,
   durable transaction/side-effect semantics and corresponding accepted transport.
4. **Intake/privacy/invitations:** approved minimum personal fields, consent/legal
   basis, collection/source, retention/deletion and disclosure; invitation sender,
   recipient verification/binding, expiry, cancellation, acceptance and review duties.
   No real intake, roster publication or privileged endpoint is installed here.
5. **Separate account linking (05C):** verified identity, controlled expiring single-use
   proof or approved NGO decision, collision/replay/mismatch/recovery and history
   preservation. A reference, matching label/contact or proposed acceptance is not
   proof and must not create a User or link an account.

These refine the already recorded 05A/05B dependencies; no redundant approval of
already accepted 04C rules is requested. Locked 04C §12/F1–F9/E05, AUTH/E/GM/REAL
acceptance, the four-field public projection, and separate NGO/platform/alliance
relationships remain unchanged. No Contabo/Oracle, infrastructure, finance, new
permission registry, schema/migration, frontend or privileged transport change.

## Validation evidence — 4 November 2026

- Real PostgreSQL 16.2 / Python 3.11: complete contract-instrumented Django suite
  **549 tests PASS**, **310 distinct route/method/status combinations**, exit 0.
- Focused 05A/05B suite: **50 tests PASS**, including 21 new DB-forbidden 05A
  tests (180 mode/route/state/event combinations plus conflict/negative subcases)
  and a new PostgreSQL zero-query evaluation/projection/catalog regression. User,
  organization and access counts remain unchanged by evaluation.
- Contracts/inventory/source provenance, TypeScript drift, migration checks,
  locked 04C bytes, 15 tooling tests, pip consistency, Python hash locks and Ruff
  checks/formatting passed. Tracked-file security scan includes all new code.
- Web tokens/types/formatting, **202 tests** and both builds passed. No shared
  wire, Dart or native interface changed; no local Flutter/browser rerun claimed.
- `npm audit --audit-level=low` remains exit 1 / **3 moderate findings** with
  unchanged package-lock and prior evidence. No suppression, threshold change,
  forced fix or override. Python advisory review remains exit 1 (`URLError`, OSV
  unreachable), not a zero-finding result. Remote CI is separate from local evidence;
  neither tests nor merge constitutes product/security acceptance or authority.
