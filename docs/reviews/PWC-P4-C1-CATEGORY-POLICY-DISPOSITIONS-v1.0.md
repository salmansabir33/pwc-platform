# P4 C1 — exact category/policy dispositions v1.0

**Proposal identity:** `P4-C1-20261104.1`. **Every disposition remains PENDING.**
This is the C1 supplement to `P4-MEMBERSHIP-20261104.1`, not a replacement,
acceptance record or authorization to install capabilities. It resolves the open
choices in P4-01 into individually accept/amend/reject-ready proposals.

The immutable parent at `eed918459c08748cdccc2ae8c2d616c69f429f14` has SHA256
`70ddb87f09f075fe04b78970ddbff5b5ff89df785915b072c8f77e9e4356aa70` and remains unchanged.
No decision here waits on C3 import or C4 claiming.

## 1. Eight exact dispositions

| ID / P4-01 choice | Exact proposed disposition | Acceptance charters / status |
| --- | --- | --- |
| C1-R01 · NGO identity/reference | Category belongs to exactly one NGO. Server-generated nonzero UUID is immutable, distinct from its immutable NGO-local handle. Handle syntax is ASCII `[A-Z][A-Z0-9_-]{0,63}`; no automatic case conversion. Retain and reserve handles after deactivation; never reuse them for another category. Same handle in a different NGO is permitted. No universal default category or authority derives from a handle. | Product + NGO governance + DB/API; **PENDING** |
| C1-R02 · naming/uniqueness | Required display label: Unicode, 1–250 code points, nonblank, no Unicode C-category characters. Preserve supplied display spelling; compare active labels using NFKC, whitespace collapse, then casefold. Unique among active categories of the same NGO, not across NGOs. Inactive labels do not reserve active names; references and UUIDs still do. No translations, abbreviation, description, ordering or arbitrary metadata fields in C1. | Product + NGO governance + DB/API; **PENDING** |
| C1-R03 · lifecycle/required fields | Category fields: NGO UUID, category UUID, handle, label, active flag, positive category revision. Policy fields: NGO, positive policy revision, admission mode, effective timestamp. An empty catalog is permitted; no category is implicitly created. Create active at category revision 1. Edit only an active category's label. Deactivate is one-way in C1; no delete, reactivation, reference reassignment, tenant move or general PATCH. Every actual change advances policy revision; label/deactivation changes also advance category revision. Reject no-ops rather than invent audit revisions. Expected policy and affected category revisions are required. | Product + NGO governance + DB/API; **PENDING** |
| C1-R04 · multiple memberships/categories | For the first member slice, propose one current category per same-NGO membership and at most one active/suspended membership per same-NGO authoritative person identity. Different NGOs remain independent; category is not a role, permission or account link. C1 defines categories only: no member records, identity matching, reassignment or retroactive cleanup is authorized. The member writer/identity constraint belongs to affected P4-02/05 acceptance in C2, not a prerequisite for implementing accepted category definitions. | Product + NGO governance + privacy + DB/API; **PENDING** |
| C1-R05 · policy versions/pending applications | Modes are exactly `open`, `approval`, `invitation`. Each category creation/rename/deactivation or mode change publishes a new immutable aggregate policy version containing category UUIDs, handles, labels, active flags and category revisions. Pending applications retain their original policy/category version; no automatic reinterpretation, admission, rejection or cancellation. **Any new aggregate policy version requires explicit re-review of all older pending bindings, including unrelated-category additions and display-only renames.** This conservative UX cost is intentional and must be expressly accepted or amended. C1 observes stale counts only; it does not perform re-review or change request state. No new admission eligibility rules are authorized. | Product + NGO governance + DB/API; affected P4-02 for later request commands; **PENDING** |
| C1-R06 · deactivation effects | Hide inactive categories from new assignment/application choices; reject new use. Existing memberships remain in their current status and category; historical references remain resolvable. Pending applications stay pending and pinned, requiring explicit re-review under R05; deactivation alone never admits/rejects/cancels them. No automatic replacement/default category, membership ending, grant revocation or financial rewrite. | Product + NGO governance + DB/API + privacy; **PENDING** |
| C1-R07 · history/effective dates | No scheduled or caller-backdated changes. Live writer, once accepted, uses transaction-authoritative UTC effective time and revision ordering, never client timestamps. Preserve immutable before/after policy/category values and historical references; distinguish the effective time from request/audit timestamps. Equal effective times are ordered by revision. No hard-delete facility. Exact audit retention/access/minimization remains governed by the affected P4-06 and category-only disclosure acceptance, not indefinite personal-data retention inferred here. | Product + NGO governance + DB/API + privacy/security; **PENDING** |
| C1-R08 · fees/renewals | Explicitly defer ALL fee and renewal configuration fields from C1: no currency/amount/precision, period, exemption, waiver, assessment, automatic expiry or renewal calculation. Absence means **not configured/not supported**, not zero/free/permanent membership. Retain any pre-existing external obligations unchanged. Later configuration requires a versioned decision and separate implementation; no finance or P6 permissions follow from C1. | Product + NGO governance + DB/API; privacy/legal if later fields require it; **PENDING** |

## 2. Acceptance record: concrete scope, not a generic readiness gate

Each accountable reviewer records: actual identity, charter, date, proposal identity,
R01–R08 accept/amend/reject (exact replacement text for amendments), and immutable
review evidence link. There are no prefilled approvals. Changes require a new
proposal version and re-review of affected dispositions/tests.

C1 live implementation needs accepted P4-01 dispositions relevant to the category
slice, the affected **P4-03 literal action/issuer/target and trusted-root authority**,
and **P4-06 restricted writer, locking/revocation fence, audit and receipt** terms.
Private category reads need accepted category-only audience/field disclosure;
HTTP/React and native networking additionally require the affected P4-09 contract.
These dependencies do not require accepting unrelated person intake, imports or
claiming. Current frozen registry has no membership actions. This supplement does
not install, grant, approve or silently map existing roles to any action.

## 3. Executable proposal coverage — explicitly not live capability

`organizations/category_policy_preview.py` implements immutable in-memory values
and deterministic proposal functions for R01–R03/R05–R07. It reuses existing
`CategoryFixture`, `MembershipSnapshotFixture` tenant/reference/label validation
and `SourceRevision`; no parallel authority service or database adapter is added.

- Complete policy versions retain old definitions. Creation, rename, deactivation
  and mode changes validate identity, revisions, uniqueness and history continuity.
- Source fingerprints include complete fixture history and pending bindings;
  changing the input invalidates the expected fingerprint. Fingerprints are NOT
  provenance, authenticated revisions, CAS, authorization or idempotency receipts.
- Pending fixture observations contain only category UUID and original policy
  revision, not member identity/contact. Only bindings to an active category in
  the bound version are allowed. Older bindings remain untouched and need review.
- The supplied `at` is a **simulation clock**, accepting monotonic UTC instants;
  it cannot verify actual DB time or enforce the no-future-date live rule.
- Internal fixture bounds: 200 policy versions; existing `MAX_ROWS` category and
  pending-observation bounds. These are computation limits, not accepted product
  quotas, retention schedules or a limit to impose on a future live database.
- Redacted summaries contain counts, modes and operation/revision history, not
  category UUIDs, labels, handles, NGO identifiers, timestamps or person fields.
  No summary serializer is permission to expose private real metadata.
- R04 member uniqueness and R08 finance deferral introduce no member/finance model
  or writer. Unclaimed memberships and account linking remain separate.

The fixed `category-policy` example is generated by the same backend fixture
builder for React and Flutter: initial version → mode change → deactivation.
Clients render only built-in fictional counts/history in EN/UR. No network calls,
private projections, editable category forms or new enabled actions are introduced.
The example is a proposal demonstration, not the accepted C1 management journey.

## 4. Verification boundary

Database-forbidden tests exercise A/B fixture isolation, duplicate labels/handles/
UUIDs, stale expected source/policy/category revisions, pending version retention,
deactivation, immutable history and minimal diagnostic/summary fields. Competing
proposals from the same source both remain proposals: this is **not** a one-winner
PostgreSQL concurrency test, replay receipt test or database rollback proof.

No new tests claim unauthorized live reads/writes, session revocation, transactional
locking, restricted database roles, audit durability or authoritative idempotency.
Those acceptance tests must accompany the accepted live writer/read implementation.
Existing authenticated routes, PostgreSQL regressions and locked 04C contracts must
continue passing; no permission registry or migration history is changed here.
Flutter checks require the repository's pinned SDK CI; local absence is not a pass.
