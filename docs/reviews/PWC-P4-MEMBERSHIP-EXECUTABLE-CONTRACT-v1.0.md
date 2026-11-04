# PWC P4 membership — consolidated executable-contract acceptance package

**Review identity:** `P4-MEMBERSHIP-20261104.1`
**Date:** 4 November 2026, Asia/Karachi
**Status:** PROPOSED — all P4 decision rows below await accountable acceptance.
**Baseline:** main `6aea981b951afb4916397fc197efff0905f0ce9f` (merged PR38), plus
unmerged PR39 functional implementation `ec8573f743e1fca5c2a5237bb1f6a22887989054`
and read-only CI diagnostics `1d48be06a5ef8dc24b7d13d277629cc1a36f2d01`.

**Purpose:** one decision package for Phase A, not another authority grant or an
assertion that P4 is complete. No permission, real data collection, private reader,
writer, migration, proof, invitation or account link becomes executable by merging
this package. Phases B–E are conditional on the affected rows and their existing
security prerequisites receiving accountable acceptance. Technical implementation
approval, deployment, operational acceptance and M1 acceptance are different events.

## 1. Verified implementation and approval inventory

Inspected: product foundation §6; roadmap P4; identity foundation §5.2; schema
foundation §7.1; ORG-07–12 screens; ADR-0002/0003/0004; NGO administrator permission
matrix; operation-bound password/TOTP decision; 04C authorization package §12;
installed access registry, auth locking helpers, organization models and PR39 code.

| Source / existing decision | Preserved scope — not resubmitted | What it does NOT approve |
| --- | --- | --- |
| Adopted Django/PostgreSQL, React, Flutter and design-system foundations | Existing architecture, personal identity/MFA/sessions, English/Urdu and accessible presentation; reuse rather than rebuild | A private membership API, native credentialed membership operation or DB writer |
| ADR-0002 and installed `ngo_kernel_v1` | Deny-default isolation and exact frozen synthetic actions `ngo.context.enter`, `ngo.private_stub.read`, `ngo.kernel_settings.read` | Member/category/application/import/claim capability or retroactive expansion of issued grants |
| Approved administrator product matrix §§1–4 | Primary/ordinary administrators are distinct; membership is conditional on module approval and exact feature grants; no self-issuing primary root | Blanket membership rights from an administrator label, staff/superuser, Board title or personal login |
| Approved sensitive-platform assurance direction | Fresh password AND current eligible TOTP bound to exact sensitive platform operation; proof is not authorization | A finalized membership assurance protocol, proof TTL, key custody or ordinary-member operation classification |
| Existing independent appointment rules | No self-approval of admin appointment/promotion; independent verified mandate/issuer process remains necessary | A requirement that every ordinary membership edit use two humans, or an exemption allowing ordinary member approval to issue admin rights |
| Product foundation §6 [S]/[R] | Preserve Open/Approval/Invitation direction; configurable categories; unclaimed people without automatic accounts; separate membership/renewal/payment/roles; private ordinary rosters | A formally accepted universal category taxonomy, complete live transition table or identity proof contract; draft labels remain provisional |
| Public directory and four-field summary | Exact existing public allowlist only | Public member names, counts from private rosters, contacts, category lists or profiles |
| Locked `C04C-FIXTURE-20261103.1`, §12/F1–F9/E05 | Exact bytes and exclusions unchanged; its affected technical acceptances remain pending | P4 authority; even that fixture charter is PROPOSED, not accepted live onboarding/grant issuance |
| PR36–39 preparation | Pure CSV preview, category/admission evaluation, revision-bound hypothetical member/history projections; fixed redacted client specimens | Source authenticity, persistence, durable CAS, audit receipts, real identity claims or live workflow acceptance |

In particular, **no currently installed action authorizes even a private live
category/member list**. Do not install a reader first and rely on a hidden UI or
administrator label. A membership approval cannot substitute for the still-gated
04C/03B.3 issuer/root and actual feature-grant contract. Conversely, accepting those
specific prerequisites must not reopen the settled product boundaries above.

PR39 verification at inspection: OPEN, no GitHub reviews, web foundation fails at
`npm audit --audit-level=low`; other final checks pass. It cannot be merged under
this assignment's no-bypass policy. Its code is a dependent worktree baseline,
not claimed to be on main or independently reviewed/accepted.

## 2. One acceptance queue

Every row is **PENDING**. Owners are accountable functions to be assigned to actual
reviewers, not invented appointments. A product-owner decision covers its charter;
it does not imply independent security, privacy/legal, NGO-governance or DB approval.
Record accept/amend/reject for each affected row using §8, in one coordinated review.
Unrelated rows may stay pending while a fully accepted independent slice proceeds.

| ID | Concrete decision / proposal below | Required accountable charters | Unlocks only after dependencies |
| --- | --- | --- | --- |
| P4-01 | Category/policy identity, uniqueness, lifecycle and configuration (§3.1) | Product + NGO governance; DB/API for constraints; privacy for retained history | Category-only checkpoint C1 |
| P4-02 | Admission eligibility and member lifecycle, complete event matrix (§3.2) | Product + NGO governance; security and DB/API for subject/revision boundaries | Unclaimed admission/status C2 |
| P4-03 | Literal action/issuer/target matrix, assurance and independence (§4) | NGO governance + IAM/security/auth + DB/API; existing trusted issuer owner | Any private category/member operation |
| P4-04 | Exact private field/audience/minimization/retention schedule (§5) | Privacy specialist + legal adviser + NGO governance + product; DB/API | Personal intake, private member reads/history and storage |
| P4-05 | Provenance, source/conflict and authoritative revision rules (§3.3) | NGO governance + security + DB/API; privacy for source references | Source-backed admissions and later staging |
| P4-06 | Restricted writer, lock/fence/idempotency/audit protocol (§6) | DB/API + auth/security; privacy/legal for event/receipt fields and retention | Executable mutation; read authorization/revocation fence |
| P4-07 | Staging/batch review, duplicates, rollback and acceptance (§7.1) | Product + NGO governance + privacy/legal + security + DB/API | C3 bulk operations only |
| P4-08 | Claim/invitation identity, proof and recovery contracts (§7.2) | Identity/security + NGO governance + privacy/legal + product + DB/API | C4 invitation/claim/link only |
| P4-09 | Exact private API/client transport and acceptance fixtures (§7.3) | API/auth/security + web/mobile owners + privacy; operational evidence only where required by the existing transport contract | Actual permitted React/Flutter integration C5 |

No new production host, Contabo, Oracle, legal incorporation decision or generic
platform-readiness report is required to continue unrelated safe local development.
These rows concern actual P4 behavior and implementation-sensitive trust boundaries.

## 3. Product and source proposals — not accepted live policy

### 3.1 P4-01: categories and membership policy

Propose NGO-owned stable UUID categories with a separate immutable reference handle;
references unique within NGO including inactive history. Active labels are unique
within NGO after NFKC + whitespace collapse + casefold. Deactivation retains history,
never deletes or retroactively changes memberships or assessments. Cross-NGO handles
may repeat. No universal `ORDINARY` category is imposed; existing samples are fictional.

Category updates require expected category AND policy revision; mode changes must
not reinterpret pending applications or existing memberships. Proposed rule: pending
requests retain a policy-version snapshot; if its eligibility/source is superseded,
explicit re-review is required, not silent application of a new policy. Confirm the
exact deactivation effect on pending requests and existing active memberships.

**Owner must settle:** label/history uniqueness semantics; reference edit prohibition;
required category fields; whether multiple simultaneous categories/memberships for
one person are permitted; effective-time and pending-policy-change behavior. Define
fee/renewal *configuration* fields (currency/precision, periods, exemptions, prospective
history) or explicitly defer those fields for C1. No payment, waiver transaction,
assessment rewrite, automatic expiry or P6 operation is authorized by this choice.

### 3.2 P4-02: admission and status matrix to accept or amend

The following is a candidate complete *first-slice* matrix, not automatic promotion
of PR38/39 fixtures. Every event also needs P4-03 authorization and source checks:

| Mode/path | From | Event / actor relationship | Proposed result |
| --- | --- | --- | --- |
| Open, self-application | new | Verified subject submits; exact eligibility checks pass | Accepted request; member creation only within the authorized atomic command |
| Approval, application | new | Authorized applicant/recording actor submits | Pending request only |
| Approval, application | pending | Authorized decision actor, independent under P4-03 | Accept → member; decline → terminal request; request information requires an explicitly accepted state before implementation |
| Invitation, ordinary membership | new | Authorized inviter creates recipient-bound offer | Pending invitation, no member/User/grant |
| Invitation | pending | Correct verified recipient accepts under current offer/policy revision | Accepted request; separately authorized member creation; not admin grant activation |
| Pending request/invitation | pending | Authorized subject cancels or authorized issuer withdraws | Terminal cancelled/withdrawn outcome; exact distinct statuses to be confirmed |
| Member | active | Authorized status actor suspends | Suspended member only |
| Member | suspended | Authorized status actor restores after current eligibility checks | Active member only |
| Member | active/suspended | Authorized ending decision | Ended member; no account deletion, grant revocation or financial posting implied |
| Member | active/suspended | Authorized category assignment to active same-NGO category | Category revision/history change; no role/dues rewrite |
| Terminal request/member | terminal | Replay, reapplication or reinstatement | Replay follows receipt rules; a new application/reinstatement requires a separately accepted rule, not resurrection by generic update |

**Owner must settle:** eligibility/required evidence by mode and category; self vs
admin-recorded subject binding; invitations under Open/Approval; reviewer/requester/
beneficiary conflicts; request-information and withdrawal states; duplicate scope;
ending/reapplication/reinstatement; suspension/restoration reasons and reviews;
category-change effective date. No list of allowed reason texts or eligibility
attributes is invented. Where unresolved, do not implement the corresponding event.

Recommended first live slice **C2**: approval-mode administrator-recorded **unclaimed**
person admission, followed by exact status/category commands. This avoids assuming
that self-application or invitation acceptance itself supplies a claim/link proof.
Open self-application and invitations can follow after their identity paths are
accepted. This is sequencing, not removal of the eventual P4 requirements.

### 3.3 P4-05: source and duplicate proposal

Propose a trusted, NGO-bound source identity/version for policy, person record and
application; origin and confirmation are server-validated, not caller attestation.
Category/request/member UUID ownership must be proven before private lookup/return.
A client revision counter or PR39 fixture digest alone is not trusted provenance.

Recommended initial duplicate rule: at most one current membership and one pending
admission per NGO/person record across categories. A membership number, if assigned,
is unique within NGO; references are not globally unique identity. Do not deduplicate
or link persons by matching name/contact. Existing records, alias corrections and
multi-category policy require explicit reviewed resolution, not automatic merging.

**Owner must supply:** authorized source types/issuers, independent confirmation
where needed, exact subject binding and source expiry/revocation/version fields;
who can resolve collisions, what evidence permits correction, and whether the
conservative duplicate rule is accepted or replaced. Changes during review must
invalidate stale approval/commit, without deleting original evidence/history.

## 4. P4-03: candidate actions and authority matrix

These are **proposed literal feature IDs**, not installed actions/bundles or grants:

| Literal candidate action | Canonical target | Candidate subject/actor boundary |
| --- | --- | --- |
| `ngo.membership.policy.read.v1` | NGO policy/version | Current exact read grant; no public exposure |
| `ngo.membership.policy.change.v1` | NGO policy/version | Exact policy-change grant and accepted review rule |
| `ngo.membership.category.create.v1` | NGO + server-owned create slot | Exact category-create grant |
| `ngo.membership.category.update.v1` | Same-NGO category/version | Exact category-update grant |
| `ngo.membership.category.deactivate.v1` | Same-NGO category/version | Exact deactivation grant; historical protection |
| `ngo.membership.application.submit.v1` | NGO + subject + source/version | Explicit accepted self/recording path; no arbitrary subject substitution |
| `ngo.membership.application.read.v1` | Assigned/owned request/version | Exact actor relationship and field scope |
| `ngo.membership.application.approve.v1` | Same-NGO request/version | Exact reviewer grant and independence rule |
| `ngo.membership.application.decline.v1` | Same-NGO request/version | Exact reviewer grant and independence rule |
| `ngo.membership.application.cancel.v1` | Same-NGO request/version | Exact subject/issuer cancellation scope |
| `ngo.membership.member.list.v1` | NGO + bounded query | Explicit field-scoped roster grant; no export implication |
| `ngo.membership.member.read.v1` | Same-NGO member/version | Exact private-profile field scope |
| `ngo.membership.member.suspend.v1` | Same-NGO member/version | Exact suspension grant/reason |
| `ngo.membership.member.restore.v1` | Same-NGO member/version | Exact restoration grant/review |
| `ngo.membership.member.end.v1` | Same-NGO member/version | Exact ending grant/review |
| `ngo.membership.member.assign_category.v1` | Member + category + policy versions | Exact category-assignment grant; same-NGO proof |
| `ngo.membership.history.read.v1` | Same-NGO subject + bounded history | Explicit history grant and minimized fields |
| `ngo.membership.import.stage.v1` | NGO + source + batch slot | Exact staging grant and intake/privacy acceptance |
| `ngo.membership.import.review.v1` | Frozen same-NGO batch/version/digest | Exact reviewer scope; no commit implied |
| `ngo.membership.import.commit.v1` | Accepted batch/version/digest | Exact commit grant and separation rule |
| `ngo.membership.invitation.issue.v1` | NGO + bound subject/offer/version | Ordinary membership invitation scope only |
| `ngo.membership.invitation.withdraw.v1` | Same-NGO offer/version | Exact issuer/withdrawal scope |
| `ngo.membership.claim.submit.v1` | Subject + same-NGO unclaimed record + proof | Verified claimant under P4-08; no contact matching |
| `ngo.membership.claim.decide.v1` | Frozen claim/record versions | Exact independent reviewer/proof contract |

The matrix must bind each accepted literal action to **actual accepted issuer/source,
role/bundle version, subject, tenant and resource bounds**, current revocation and
expiry. No wildcard, Django group, role-label inference or automatic expansion of
`ngo_kernel_v1`. The trusted grant issuer/root and GM/04C contracts are prerequisites;
this document does not instantiate them. Export, hard delete, merge, finance, grant
issue/revoke and platform/alliance authority are deliberately not in this matrix.

**Independence decision to accept/amend:** keep mandatory independent admin
appointment/promotion approval unchanged. For ordinary Approval-mode admission,
recommend final approver differ from submitting/recording human and beneficiary;
for bulk commit recommend accepted reviewer differ from stager. The exact handling
of claimed/unclaimed beneficiaries and natural-person equality must be defined.
For category policy changes, suspension, restoration and ending, owners must specify
single-actor vs independent review per action, conflict exclusions and compromise
containment. Do not silently impose or waive two-human review for all edits.

**Assurance decision:** classify every accepted action as read/ordinary mutation/
sensitive protected command and bind the exact approved assurance protocol. Existing
sensitive-platform password+TOTP direction stays fixed; its pending D3–D6 protocol
must not be copied as accepted membership machinery. Decide factor continuity,
operation intent target/source/revision bindings, deadlines, failure budgets and
single-use/revocation fences for affected P4 commands. Ordinary personal login/MFA
or `step_up=true` never substitutes for authorization or command-bound proof.

## 5. P4-04: proposed privacy field and audience schedule

Candidate minimum C2 person/member fields: server UUIDs/owning NGO, local reference,
display name, category, membership status, admission/effective date, source version
and revision. Contacts, national IDs, addresses, birth dates, attachments, free-text
case notes and linked-user identity are **excluded from the initial slice unless
separately enumerated and accepted**. Opaque UUIDs are not anonymous public data.

| Audience / surface | Candidate allowed fields | Required exclusions |
| --- | --- | --- |
| Category/policy reader | Accepted non-personal category/policy fields | No roster, member counts, personal source material or finance |
| Scoped roster reader | Member UUID, local number/reference, display name, category, status, revision | No contact, evidence, claim secrets, user identity, finance or broad exports |
| Scoped profile reader | Explicitly accepted minimum member/person fields above | No implicit inclusion of new model fields; stronger fields require a new field scope |
| Application reviewer | Assigned target, required eligibility outcome, exact revisions | No unrelated applications, other NGOs or raw evidence by default |
| History reader | Event type, revision/time and approved reason/actor representation | No credentials, proof material, raw CSV or automatic general audit access |
| Subject/self | Exact owned record after approved subject/link binding | Login alone does not reveal an unclaimed person record |
| Public directory/summary | Existing four-field public contract only | No membership projection at all |
| Logs, metrics, notices | Correlation ID + bounded code; generic notice to server-resolved recipient | No names/contacts, row cells, passwords/TOTP, proof tokens, source hashes or private bodies |

**Privacy/legal owners must return exact values**, not simply approve “GDPR/privacy”:
legal basis and purpose per field; consent/notice audience; collection/source;
who may see full vs masked values; encryption/key-custody where needed; retention,
erasure/anonymization and legal-hold schedule for person records, rejected requests,
staging rows/files, claim proofs, history, receipts and notices. Define durations and
start/stop events, deletion authority and retained replay tombstones. No invented
retention period, public consent or universal roster-reader permission is supplied.

## 6. P4-06: proposed executable database/command contract

Reuse existing PostgreSQL and auth primitives; no SQLite, service replacement or
parallel identity store. Candidate additive tables: NGO policy/category, private
person record, application, membership, history/event and idempotent receipt;
staging/batch/claim tables only in later accepted checkpoints.

Required schema invariants: composite tenant ownership of person/category/request/
member FKs; per-NGO reference and active-duplicate constraints under P4-01/02/05;
monotonic revisions; append-only event/history and receipt protection; no cascade
removal of history; no raw proof or plaintext credential storage. Schema acceptance
must include migrations, runtime grants and direct-SQL denial, not ORM validation only.

Candidate command protocol, subject to actual lock-graph/security acceptance:

1. Server derives authenticated actor/session and current context; allowlisted literal
   action + tenant + target + expected policy/source/record revisions + canonical
   accepted payload + idempotency key. Client cannot supply its own issuer/assurance.
2. Lock/fence shared actor User first, then required auth/factor/session/proof rows
   under a reviewed common order; then trusted authority roots/grants/source, NGO
   policy, sorted category/person/application/member targets, batch/claim if relevant,
   and receipt slot. Recheck actual helper orders in `accounts/sessions.py`, `mfa.py`
   and `access/services.py`; no membership-first → User reverse path. Multiple actor
   or target locks use sorted stable IDs. **This outline is not an accepted full graph.**
3. After lock waits, use primary DB time and recheck actor eligibility, current grant/
   source/policy/target revision, human independence, holds/revocation and proof
   deadline. Stale or mismatched revisions reject without business mutation.
4. Runtime principal has no direct membership/history/receipt DML or owner/SET ROLE
   escape. Narrow reviewed writer and separately trusted assurance verifier, fixed
   search path and restricted function privileges; no fixture attestation or Django
   staff override. Approve exact principals, function signatures and trusted source
   authentication before installing executable functions or grants.
5. In one accepted transaction: business transition + revision + relevant single-use
   proof consumption + minimized append-only event + generic notice/outbox intent +
   receipt. Failure rolls back all business effects. Credential-abuse and replay-fence
   persistence must follow the accepted separately committed auth design, not be
   accidentally undone with business rollback. No network send while holding locks.
6. Receipt scope: actor + tenant + literal command + canonical target/create slot +
   key. Same key/same canonical payload returns the owned minimal receipt **after
   current authorization**, not disclosure after revocation; changed payload conflicts.
   Database uniqueness prevents two durable winners; a memory dictionary is not a
   receipt store. Unknown/lost-response outcomes use authorized receipt lookup, not
   blind retries with a new key. Invalid/stale retry semantics and receipt/tombstone
   retention must be accepted together.

**DB/auth/security must settle:** full order against each invoked helper, isolation,
lock/statement deadlines and DB-clock rules; revocation linearization point; intent/
proof verifier boundaries, principal/key custody; canonical payload/digest privacy;
create-slot reservation; timeout/rollback/unknown-outcome errors; audit/receipt readers
and exact field/retention rules. Existing pending 04C D4–D6 figures are not treated
as P4-approved constants. Routine index/code layout choices need no separate approval
once the actual invariants and security contract are accepted.

## 7. Imports, identity and clients

### 7.1 P4-07: staging and atomic import proposal

CSV preview remains pure, bounded and non-authoritative. Propose first intake as the
existing exact UTF-8 CSV template with explicit accepted size/row limits; current
65,536-byte/200-row values are preview limits, **not automatic live intake consent**.
XLSX and file mapping need a separately accepted parser/intake contract.

Candidate batch lifecycle: staged → reviewed/accepted → committed, with rejected/
expired/cancelled terminal outcomes. Freeze owning NGO, source/policy/category
versions, validated row digest, reviewer, accepted subset and batch revision.
Candidate policy: unresolved duplicate/error rows prevent acceptance; any explicitly
accepted skip/correction makes a new reviewed batch version. Never silently merge,
change another member or create/login/link a User. Revalidate all references and
current authority after deterministic locks; commit all accepted rows + event/
receipt/notice intents atomically or none. Concurrent claims/admissions/imports
share the accepted person/duplicate fence. No partial commit called success.

**Owners must settle:** intake source and field mapping, encrypted staging/storage,
limits, retention/deletion, collision-resolution authority/evidence; accepted skip
semantics, stager/reviewer/committer independence; policy/category changes during
review; expiry/cancel/retry/unknown outcome; import summary/error audiences and
whether undo exists (otherwise no undo endpoint). Preview, staging, acceptance,
commit and identity claims remain five separate operations.

### 7.2 P4-08: ordinary invitations, verified claims and linking

Propose server-owned pending claim bound to verified claimant, exact NGO/person/
membership revisions, approved verified-contact or NGO-review evidence and intended
link. No candidate search or link from a name/contact match; matching records across
NGOs never merge automatically. Invite acceptance does not grant administrator rights.

**Identity/security/privacy/NGO owners must settle:** required identity strength and
subject/recipient proof; sender and reviewer authority; distinct-human conflicts;
proof generation, hash/verifier storage and single-use binding; exact expiry,
attempt/rate limits and resend/invalidation; factor/contact/recovery continuity;
proof consumption and link uniqueness under locks; simultaneous claims, already-
linked records, contact reassignment, collision, dispute and recovery/unlink rules.
Approved representative-invitation maximum 72h is **not automatically an ordinary
membership invitation or claim-token lifetime**. No numeric proof lifetime is inferred.

### 7.3 P4-09: web/mobile and API acceptance

Reuse established error envelopes, server authorization, tenant-filtered querysets,
pagination and exact field allowlists. Specify every permitted path/method/field/
error/receipt/revision and revocation/late-response scenario before publishing a
versioned OpenAPI/TypeScript/Dart contract. The literal action matrix is not an API. Route spelling, component layout, index
names and generator internals are routine engineering choices once the affected
operation/privacy/transport contracts are accepted; they are not extra product
approval rounds. Review the actual permission and credential boundary, not cosmetic
URL or implementation choices.

Browser: preserve genuine direct TLS, same-origin cookies/CSRF and exact configurable
portal origins; no forwarded-header shortcut or cross-portal grant inference.
Flutter: extend native operation allowlists only under the applicable accepted
identity/credentialed-transport contract; do not turn personal API transport into a
private membership client by changing a URL. No host deployment is silently required
for a safe local adapter test, and no local test grants credentialed rollout approval.

Actual permitted UI must show server truth; explicit loading/empty/error/stale/revoked/
unknown-outcome states; English/Urdu, keyboard/RTL/scaling and responsive acceptance;
clear private state on logout/context/factor/revocation invalidation. No optimistic
admission/import success or cached cross-NGO roster. Unaccepted actions stay disabled.

## 8. Accountable response worksheet — one coordinated review

For **each affected P4-ID**, return the following, referencing this document's exact
Git commit and whole-file SHA-256 (computed after publishing; not a self-hash):

```text
Contract: P4-MEMBERSHIP-20261104.1
Immutable Git commit + document SHA-256:
P4-ID(s) and exact sections/action/field/state rows covered:
Disposition: accept as written | amend (exact replacement attached) | reject
Accepted checkpoint(s), exclusions and unmet dependencies:
Reviewer identity and accountable charter (not merely staff/job title):
Independence/conflict declaration, where required:
Decision date, authenticated acceptance evidence reference:
Required evidence/tests and acceptance conditions:
Outstanding exact parameters (none may be implied or left blank for execution):
```

The responsible owner must supply real reviewer assignments/charters and evidence;
none are fabricated here. A reply from a product owner can record product choices,
not unclaimed independent technical/privacy/legal acceptance. An amended artifact
gets a new immutable review version; earlier signatures do not float to changed text.
Accepting a core subset is valid; unsupported rows remain unavailable. Approval of
one row does not accept all rows or satisfy an underlying 04C/GM issuer contract.
No boolean, hash match, GitHub merge, test pass or machine checker is an enable switch.

## 9. Implementation checkpoints after affected acceptance

| Checkpoint | Exact dependencies | Concrete coding/test delivery |
| --- | --- | --- |
| C1: private category/policy module | P4-01/03/06; accepted feature issuer/root, read/write field scopes, and P4-09 for HTTP/client integration | Additive category/policy constraints, scoped services, restricted writer, source revisions/receipts and tenant-filtered category projection; direct-SQL/foreign-NGO/revocation/stale/replay tests |
| C2: unclaimed approval admission/member history | C1 + P4-02/04/05 + affected P4-03/06/09 rows | Private person/request/member models; independent approval where selected; status/category/history commands and projections; same-person race, self-approval, revocation and rollback tests |
| C3: CSV staging/review/atomic import | C2 + P4-07 and its field/authority/proof/retention rules | Scoped staged batches and error reports, reviewed exact revisions, atomic all-or-none creation; concurrency/duplicate/crash/receipt/partial-failure tests |
| C4: invitations/self-service/claim-link | Affected C2 + P4-08, applicable P4-03/04/06/09 rows | Bound identity proofs, recipient acceptance/link, single-use and race/recovery tests; no matching-based links |
| C5: actual React/Flutter journeys and M1 acceptance | Each actual backend command/read accepted + P4-09 and applicable transport/operational evidence | Shared generated contracts, bilingual real workflows, accessibility, invalidation, direct API/cross-NGO adversarial tests and accountable UAT |

Do not force C1 to await unrelated C3/C4 decisions; equally, C1 cannot proceed before
its actual private capability/root, privacy scope and writer prerequisites. No code
is authorized solely by this proposed sequencing. Protected-component migrations
and functions must not be installed first behind an arbitrary feature flag.

## 10. Current delivery/acceptance status and independent security issue

| Ticket | Status now | Real user journey / restriction |
| --- | --- | --- |
| 05A | Partially implemented | Synthetic category/admission/member/history foundations only; no live admission, private roster or status service |
| 05B | Partially implemented | CSV preview/admission preparation only; no authorized staging or atomic member creation |
| 05C | Blocked by identified contracts | No verified identity claim/link service |
| 05D | Partially implemented | Integrated redacted bilingual workbench; protected React/Flutter workflows remain disabled |
| 05E | Partially implemented | Automated regressions, not a real two-NGO membership journey or accountable UAT |

**No new real membership journey is completed by this Phase A package.** Existing
personal identity/public-directory journeys are preserved, not re-counted as P4.
There are no new models/migrations, networked clients, permission atoms or writers.
P4 and M1 are not complete; live implementation is blocked by the affected rows and
underlying still-unaccepted privileged issuer/security contracts, not by Contabo.

PR39's existing evidence: local 563 PostgreSQL tests / 310 HTTP combinations; 64
focused membership/import tests; 206 web tests and both builds; pinned Flutter 164
tests, analysis/format, Android and final Django 3.11/3.12/staging CI passed. These
are prior functional-head results, not fresh tests of a live module. One earlier
Python 3.11 PR failure was not reproduced and is not claimed as a diagnosed fix.

Track the unresolved npm issue **separately from authority acceptance**: unchanged
three moderate findings through openapi-typescript → Redocly → minimatch; existing
review/evidence and audit threshold unchanged. No unsafe override, suppression,
forced fix, branch-protection waiver or repeated dependency investigation. PR39
remains unmerged while its audit gate fails; new Phase A text does not waive it.
Infrastructure, production activation, Contabo and Oracle remain outside scope.
