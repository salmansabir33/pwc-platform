# PWC-04C — Implementation Authorization and Independent Sign-off Package v1.0

**Prepared:** 27 October 2026 (Asia/Karachi)  
**Status:** REVIEW PACKAGE — NOT AUTHORIZED for real privileged-command implementation, sensitive data intake or activation  
**Roadmap:** P3 / PWC-04C; dependencies PWC-03B.3 and PWC-04B; retain P0–P8, M1–M3 and lettered tickets  
**Baseline:** main after merged PR #24 (`9d2f5072`)  
**Purpose:** Bring the eight critical implementation blockers in the PWC-04C readiness review to explicit accountable decisions in **one** package, without a string of separate product-choice PRs.

**Current closure delta:** [§11](#11-implementation-contract-closure-delta--2-november-2026) supplies exact proposed rules, acceptance ownership and the smallest coding checkpoint. Earlier pending rows remain pending; authoritative product constraints are carried forward without reopening them.

## 1. Evidence hierarchy and boundaries

The following **product decisions are already approved**: offline NGO/mandate examination; founding authority's separate signed initial platform appointments; manual restricted technical provisioning with independent confirmer; existing personal identity plus separate platform privilege; Super Admin submission distinct from Verification Officer approval; one-use exact-recipient invitation with at most 72-hour expiry and explicit acceptance; Primary versus scoped ordinary NGO Administrator nonfinance roles; fresh password **and** eligible current TOTP bound to sensitive command intent.

They are **not** independent security, NGO-governance, database/API, platform-operations or legal/privacy approvals. The original E01–E18 and GM01–GM12/REAL01–REAL04 registers and ADR-0002/0004 prevail where a proposed detail conflicts. Existing synthetic grants/24-hour cap remain unchanged. No file in this package issues roles or enables permissions.

### Status convention

- **Product accepted:** Product-level behavior/direction decided.
- **Proposed contract:** Implementable recommendation subject to specified independent approval.
- **Blocking I:** Do not implement the affected real command, writer or evidence intake when exact contract remains missing. Permitted read-only and separately approved deny-default preparation unaffected.
- **Blocking A/U/R:** No live real authority / real documents or personal-data intake / production release respectively.
- **Signed off:** Only after actual accountable people sign/date the specific version/environment with evidence and exclusions. **All independent sign-offs in this package initially remain PENDING.**

## 2. Decisions required — one approval register

| ID | Exact decision required | Recommended disposition for reviewer consideration | Accountable independent functions | Gate | Status |
| --- | --- | --- | --- | --- | --- |
| AUTH-01 | Founding authority, signed evidence and first-officer chain | Authenticate founding governance instrument; individually verify two distinct appointees; sealed two-person appointment/executor/confirmer chain | NGO governance, platform operations, security, privacy | I/A/U | **PENDING** |
| AUTH-02 | Real command charter and issuing matrix | Versioned allowlist and exact issuer → action → target → independent confirmer → exclusion matrix, with bootstrap distinct from ordinary NGO appointments | NGO governance, security, API, operations | I/A | **PENDING** |
| AUTH-03 | Exact nonfinance capabilities and initial bundles | Explicit v1 atom IDs and user-facing meanings, no wildcard/future permissions; finite source-bounded grants | Product, NGO governance, security, API | I/A | **PENDING** |
| AUTH-04 | Protected assurance and GM06 factor continuity | Fresh password and current eligible TOTP per command; recommend **suspend protected actions after factor removal/replacement until independent re-verification/re-enrollment**; do not auto-restore grants | Auth/security, operations, privacy | I/A | **PENDING — GM06 choice not yet adopted** |
| AUTH-05 | Provenance, restricted DB writer and concurrency | Separate real-source root/grant tables, least-privilege privileged writer, atomic transition/receipt/outbox, approved lock order | Database, security, API, operations | I/A/R | **PENDING** |
| AUTH-06 | Nominee invitation/consent and activation | Exact immutable recipient/account/NGO/mandate/role revision; hash-verifier one-use token; max 72h; acceptance distinct from source-approved grant activation | Security, API, NGO governance, operations, privacy | I/A/U/R | **PENDING** |
| AUTH-07 | Expiry, revocation, cascade, recovery | Explicit source cutoff hierarchy, immediate server revalidation, independent succession/recovery; compromise may leave zero admins | NGO governance, security, DB, operations | I/A/R | **PENDING** |
| AUTH-08 | Evidence reference privacy, notices, audit readers | Minimized external-case attestation references, classified audit read policies, distinct retention/holds/backups/deletion, safe notices and contested process | Privacy/legal, NGO governance, operations, security | I/U/R | **PENDING** |
| AUTH-09 | Deployment, actual operator staffing and release | Actual appointed humans and runbook, production TLS/cookie/CSRF/provider testing, restore rehearsal, mobile/web UAT | Operations, security, privacy/legal, product | A/U/R | **PENDING** |

No one may turn a PENDING cell into Approved simply by merging this document or asserting “product owner approved recommendations.” A reviewer may reject, amend or demand additional proof.

## 3. Proposed bounded command charter (AUTH-02/03)

Each operation must have a unique versioned command ID, exact actor/principal, source of authority, target type, target NGO, expected revision, independent confirmer (where required), assurance requirement, audit classification, idempotency scope and precise failure taxonomy.

| Protected command group | Initiator/source | Required independent review | Expected postcondition |
| --- | --- | --- | --- |
| `platform.appointment.bootstrap.v1` | Restricted offline operator; signed founding appointment for exact person | Distinct authorized confirmer and independently verified provenance | Bounded platform capability only; no NGO data access |
| `platform.appointment.rotate_revoke.v1` | Legitimate appointment issuer / independently designated compromise responder | Two-person regular change; scoped incident restriction path separately accepted | Old permissions fenced immediately |
| `ngo.onboard.submit.v1` | Currently appointed Super Admin | No self-approval | Immutable attested revision awaiting decision |
| `ngo.onboard.review.v1` | Independent appointed Verification Officer | Must differ from initiator/nominee and satisfy conflicts policy | Decision on exact revision; no grant |
| `ngo.nominee.invite.v1` | Appointed Super Admin acting on approved current mandate | Approval exists for exact nomination and recipient | Bounded pending invitation, no privilege |
| `ngo.nominee.accept.v1` | Exact verified personal identity and invitation recipient | Cannot be proxied by platform staff | Explicit version-bound acceptance, grant pending |
| `ngo.primary.issue.v1` | Narrow protected real writer backed by approved mandate, review and acceptance | Source-specific exact nonfinance approval | Independent bounded root provenance and nonfinance scope |
| `ngo.admin.request_approve.v1` | Primary requests; separately authorized nonconflicted approver decides | No requester/beneficiary self-approval; NGO-governance matrix controls | Scoped ordinary admin grant only |
| `ngo.primary.replace_recover.v1` | New authentic NGO governance nomination and fresh applicant evidence | Independent platform confirmation with new recipient acceptance | New approved grant; revoked prior power not resurrected |
| `ngo.dispute.restrict_review.v1` | Designated reviewer or restrict-only responder | Independently reviewed outcome, tightly bounded emergency exception | Restrict only; no broad data access or auto unfreeze |

**Reviewer must resolve** the precise identities eligible to execute each command (not just role labels), NGO governance quorum per appointment type, cross-review conflicts, exact scope/expiry and whether each protected command needs a separate confirm/approval distinct from existing offline evidence review. Treat these as **proposals**, not installed API routes or permission IDs.

## 4. Exact assurance-review worksheet (AUTH-04)

Product rule: verified personal identity + valid session + active appropriate source grant + **fresh password and eligible TOTP bound to the specific action** for sensitive platform commands.

Reviewers must accept a fully specified server challenge protocol covering: actor/session/NGO/target/revision/command/version binding; TTL and single-use nonce; canonical request serialization; password validation and current-factor continuity; anti-replay/TOTP timestep acceptance; challenge invalidation on session/contact/factor change; error taxonomy and rate limiting; intent-consumption transaction; lost-response status and evidence-retention limits. No web bearer-token workaround, password/TOTP plaintext persistence, token logs or personal recovery code privilege bypass.

**GM06 decision required:** Recommended rule is that factor removal/compromise/re-enrollment **immediately suspends protected command capability** until a separate independently authorized identity recovery and eligible factor re-enrollment process completes. The alternative (prohibit factor removal while duty active) has safety/usability downsides but must be expressly evaluated and either accepted or rejected by actual auth/security owner. Neither branch is accepted merely by this recommendation.

## 5. Exact state/lifetime worksheet (AUTH-06/07)

Product flow: offline NGO evidence → operator-submitted revision → distinct reviewer approval → exact nominee invitation → verified identity + explicit acceptance → separately authorized bounded nonfinance grant.

- Invitation: never longer than **72 hours after issuance**, no grace or implicit reissue.
- NGO eligibility: earlier of individually approved end date and proposed **12-month ceiling**; precise jurisdiction rubric and expiry clock need NGO-policy/security sign-off.
- Representative mandate: earlier of written governance nomination end, NGO eligibility end and proposed **12-month ceiling**.
- Real nonfinance grant: earlier of all source cutoffs and proposed **90-day maximum**; synthetic grant policy is untouched.
- Activation authorization: proposed ceiling **24 hours** after separately approved command authorization, never after source/reviewer revocation.
- Require reviewer agreement on UTC timestamps, inclusive/exclusive endpoints, timezone/calendar day arithmetic, transitions when evidence is corrected, revocation cascades and treatment of existing sessions. No grace. Previously accepted invitation cannot independently authorize a grant after source validity is lost.
- Distinguish statuses: `pending_review`, `approved`, `invitation_pending`, `invitation_expired`, `invitation_revoked`, `accepted_grant_pending`, `active`, `restricted`, `revoked` and `unavailable` in presentation and API. Exact backend enum names require API approval.

### Invitation and identity binding

Account/email collision, contact change/reuse, delivery failures, redelivery, aliasing, existing-account ownership and alternate-recipient challenges need explicit API/security/operations review. Tokens must be stored as cryptographic verifiers, be one-use and resist enumeration, and must not travel in persistent application telemetry, query strings or unaudited URL logs. Existing PWC personal confirmation uses a URL-fragment proof pattern; do not assume it can be reused for NGO invitation without explicit source/receiver/origin evaluation.

## 6. DB/API integrity and audit worksheet (AUTH-05/08)

Before implementation signoff, record the actual reviewed PostgreSQL writer ownership/GRANT/EXECUTE policy; trust anchor for offline appointment references; real-root vs synthetic grant provenance; append-only revision/event guarantees; unique constraints; explicit global lock ordering; transaction isolation and idempotent retry/receipt semantics; revocation fencing; source-cascade triggers; error codes and OpenAPI wire schema. Review concurrency with parallel approval/revoke/invite and delayed responses. No external network I/O while holding privileged transaction locks.

Specify exactly which appointed auditors may read **which metadata**, how notices to nominee/officer/NGO governance parties are redacted, what is not sent over email, and how recipients are determined. PWC Board and ordinary platform staff do not implicitly gain private audit reader authority.

Privacy/legal reviewers must define classification, controller/processor, lawful basis/notice, separate retention starts and periods for signed external appointment papers, evidence-reference metadata, attestation/event, outbox, backups and deletion holds; legal hold and restored-backup deletion propagation. No invented Pakistani statutory duration. Raw NGO verification documents remain outside the application for initial rollout. Legacy four-field public verified-NGO projection is **not** consent-aware: grant activation must never implicitly switch public profile visibility; publication needs independent accepted consent/policy (04D).

## 7. Minimum acceptance and adversarial test charter

Acceptance evidence must cover (at minimum):

1. Forged `is_staff`/`is_superuser`/Board role or fixture grant cannot provision or read NGO-private data.
2. Founder/executor/confirmer chain requires authentic signed source and distinct qualified humans; same person with two user IDs cannot self-approve.
3. NGO A/B tenant isolation in all read/list/write/export/audit/notice/receipt paths.
4. Concurrent approve-vs-reject, invite-vs-revoke, accept-vs-expire, grant-vs-nomination-revoke, recover-vs-compromise operations have a single authoritative atomic result.
5. Stale review revision, changed nominee or changed scope invalidates prior proofs and invitations.
6. Password-only, login MFA only, recovery code, new/replaced factor, expired/replayed TOTP, other command challenge and held account are denied for protected operations.
7. Invitation wrong recipient, duplicated/replayed invite, changed email and reissued token cannot activate improper authority.
8. Real/synthetic provenance never crosses; v1 fixture ceiling unchanged, app runtime DB user cannot issue real grants.
9. Planned last-admin transfer requires accepted replacement where feasible; compromise revocation never preserves attacker solely because last admin.
10. Audit/outbox/receipt preserve coherent atomicity and minimized content on transaction rollback and lost response.
11. NGO verification never causes automatic public profile publication or finance/signatory/alliance access.
12. React Operations and NGO web / Flutter distinguish gated previews, pending approval, rejected, invite accepted but grant pending and activated; tests verify design tokens, RTL and state/permission semantics.

Passing synthetic tests is **not** permission to run real writes. Require native/live staging/provider/HTTPS/restore and accessibility tests before activation/release.

## 8. Independent approval record template — one per owner or joint decision

> **Decision ID(s):** AUTH-__ / E__/GM__/REAL__  
> **Contract version + immutable Git commit:** ____  
> **Approved environment and scope:** ____  
> **Proposed option / alternative reviewed:** ____  
> **Decision:** APPROVE / APPROVE WITH CONDITIONS / REJECT / DEFER  
> **Exact changes required / exclusions:** ____  
> **Accountable human reviewer name + role + appointing authority:** ____  
> **Recorded date/time and approval evidence URI/reference:** ____  
> **Relevant test, threat model or operational evidence:** ____  
> **Expiry/re-review trigger:** ____  
> **Dependencies remaining open and designated owner:** ____

No placeholder is an approval. Do not prepopulate actual human names, signatures, legal conclusions or attestations. The product owner may accept product-specific scope but **cannot automatically replace** security, legal/privacy, operations or independent NGO-governance sign-off.

## 9. Next engineering gate and implementation handoff

Only after all **affected I gates** are independently signed off against an exact immutable contract version should Arena/Codex receive **one complete PWC-04C implementation assignment**. Its accepted scope must address models/migrations, narrow DB writer/provenance, platform IAM, distinct offline attestation review, intent-bound password+TOTP, invitation delivery/acceptance, nonfinance grant issuance, bounded administrator requests/approvals, revocation/recovery, Django/OpenAPI and the relevant React/Flutter UI, adverse PostgreSQL tests, local/CI validation and one consolidated PR.

Separate **A/U/R** acceptance still controls real user/evidence intake and deployment even after testable engineering implementation. Do not invent shortcut approvals or reopen public NGO self-registration. If a reviewer cannot approve a particular command, explicitly exclude it with an accurate roadmap/gate record rather than reporting PWC-04C complete.

## 10. Traceability

- [Roadmap v2.0 and reconciliation](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md)
- [ADR-0002 tenant authorization](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md)
- [ADR-0004 NGO verification and authority](../decisions/ADR-0004-ngo-verification-and-representative-authority.md)
- [E01–E18 authority register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md)
- [GM01–GM12/REAL01–REAL04 register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md)
- [PWC-04C consolidated proposed contract](PWC-04C-CONSOLIDATED-AUTHORIZATION-SECURITY-CONTRACT-v1.0.md)
- [PWC-04C readiness review](PWC-04C-IMPLEMENTATION-READINESS-REVIEW.md)
- [PWC Design System v1.0](../design/PWC_DESIGN_SYSTEM_v1.0.md)

**Release status:** No authorizations granted or real privileged code enabled by this document. The next step is real, independently evidenced review of AUTH-01–AUTH-09 and aligned E/GM/REAL gates.

## 11. Implementation contract closure delta — 2 November 2026

**Review version: `C04C-20261102.1`; status: PROPOSED where marked D below.**
This is the actionable delta to §§2–9 and the existing consolidated contract,
not a new readiness report or approval. Baseline: merged PR30, `64a51ea`;
PR27–29 already implement permitted browsing/history/preparation and browser
integration. Their code and tests must not be rebuilt. No signed technical
acceptance has been added by this assignment. The AUTH-01–09 PENDING entries
remain pending at their respective scopes; product choices below are not reopened.

### 11.1 Settled constraints — carry forward without redundant product approval

| Fixed rule | Authority and implemented reuse boundary |
| --- | --- |
| F1. Offline controlled onboarding only; organization eligibility and representative mandate are distinct findings. | ADR-0004 §7; `organizations/controlled_onboarding.py::preflight` and `controlled_preparation.py::prepare_submission`. These are nonwriting structural validators, not issuer authentication or decisions. |
| F2. Chairman/President is the founding appointing function; separate signed appointments for two distinct natural persons; technical executor and independent confirmer; existing personal accounts and separate platform authority. | [Role arrangements](PWC-04C-GOVERNANCE-AND-REVIEWER-ROLE-ARRANGEMENTS.md) §§1–4; [manual provisioning decision](PWC-04C-MANUAL-PLATFORM-OFFICER-PROVISIONING-DECISION.md). Actual identities/instruments and executable trust-anchor protocol are not supplied by this product rule. |
| F3. Sensitive platform actions need fresh password **and** eligible newly supplied TOTP bound to the exact action. No login-MFA/recovery-code/staff/superuser substitute. | [Password/TOTP decision](PWC-04C-OPERATION-BOUND-PASSWORD-AND-TOTP-DECISION.md); `accounts/mfa.py::verify_totp`, `sessions.py::authenticate_locked`. Personal `scope`, `step_up`, `consume` remain personal-only; do not add NGO operation strings to that allowlist. |
| F4. No self-approval, cross-NGO authority, legacy-role promotion, synthetic-to-real promotion, finance/signatory/alliance/support inheritance or future wildcard capabilities. | ADR-0002; GM/REAL register; [admin matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md). Keep `access/registry.py` v1 bundles and synthetic 24-hour ceiling unchanged. |
| F5. Exact nominee, explicit versioned consent, one-use invitation, at most 72 hours; acceptance is not grant activation. | [Invitation decision](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md). Token/protocol and account-resolution ordering still need D7–D9 acceptance. |
| F6. Current authorization/source checks, exact revision, immediate committed revocation fence and atomic audited outcomes; no positive cache/replica authority or network delivery under locks. | ADR-0002; `access/services.py`, `access/security.py`; existing controlled history constraints. These settle invariants, not the new writer/lock implementation. |
| F7. Primary may request—not self-approve—additional admins. Planned succession is distinct from compromise containment; the last compromised admin may be revoked without a successor. | Admin matrix §3; GM09. Exact quorum/cardinality/recovery decisions remain D11. |
| F8. No raw verification uploads initially; no automatic publication; preserve all transport/runtime gates. | ADR-0004 §7; AUTH-08; `config/environment.py`, `infra/web-auth/README.md`, `infra/staging/README.md`. A reviewer decision alone cannot change the legacy public projection or enable credentialed transport. |
| F9. E05 numeric **product upper bounds** are already adopted: eligibility 12 months, mandate at most evidenced term/12 months, real nonfinance grant 90 days/source cutoff, invitation 72h, activation authorization 24h; no grace or automatic renewal. | [E register §8](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md#8-consolidated-product-owner-approval--27-october-2026), E05 and conflict resolution. Older “proposed bounds” wording in §§5 and earlier drafts is historical; only exact clock/calendar/renewal mechanics remain for review. None extends personal proof/session deadlines or synthetic 24h grants. |

### 11.2 Decision register — exact questions and recommended dispositions

**D = proposed technical/product rule, affected implementation blocked until accepted.**
**O = actual operational evidence, blocking only the indicated activation/intake/release.**
A row's owner is an accountable function, not an invented appointed person. The
role arrangements document maps security to the designated Cybersecurity Specialist,
DB/API to the Senior Backend/Database Architect, and privacy to legal adviser **and**
data privacy specialist. Accept/reject/amend each D row using §8, on this version
and immutable commit; no request to reapprove F1–F9. “I” never means merely a flag.

| ID / unresolved question | Exact recommended rule and rationale | Existing source / code | Acceptance owner; gate |
| --- | --- | --- | --- |
| D1 / AUTH-02–03: Which commands/capabilities may each actor execute? | Adopt the closed matrix in §11.3, with one exact versioned atom per command/decision. No role-name fallback, implicit module rights or union of unrelated grants to manufacture issuer authority. Unknown command, bundle or version denies. This turns product functions into finite executable rights. | Package §3; consolidated contract §2; admin matrix §§2–4; GM01/02/04/09; `access/registry.py` is synthetic-only. | Product + NGO governance + security + DB/API + operations; **I**, then A. |
| D2 / AUTH-01/05: What authenticates the first provisioning operation without circular platform grants? | Restricted nonpublic CLI, never Django Admin/public signup. Require independently verified founding appointment reference, exact pre-existing verified User/contact and scoped executor authorization outside application-role issuance. Recommend two-person approval manifest: executor and independent confirmer authenticate separately; confirmer signs a server-canonical manifest binding source digest/version, beneficiary, exact atoms, validity, nonce and expected root revision. Verification keys/allowed issuer identities are deployment-controlled, not writable by runtime/fixture roles; nonce is consumed by the narrow writer with its receipt. Recommend platform-grant expiry min(issued_at + 90 days, signed appointment end); renewal requires a fresh independently confirmed manifest, never an implicit extension. Recommend Ed25519 signature over §11.4 canonical bytes; no keys generated here. No pre-existing platform grant is required for bootstrap, but the accepted external trust anchor is mandatory. This avoids a self-issued root or a reference-string-as-proof loophole. | F2; manual provisioning decision; readiness review §§4.1–4.3/6.1; `access/db_roles.sql` is NOT a bootstrap writer. | Founding governance + security + operations + DB/API + legal/privacy; **I** for protocol/custody model; actual instruments/keys/people are O1. |
| D3 / AUTH-04, GM06: What survives factor removal/replacement or account recovery? | Choose GM06 **B**: allow ordinary personal factor removal, but atomically fence protected eligibility/intents on removal/replacement, password/contact recovery or hold; no automatic reinstatement. A new factor becomes protected-eligible only through an independently approved re-verification tied to its ID/revision, not an arbitrary cooldown or recent-login flag. Initial eligible enrollment is independently recorded with the appointment. This preserves personal offboarding without restoring domain power through recovery. | Password/TOTP decision; readiness §5; `mfa.py::remove`, `clear_hold`, `sessions.py::revoke_all_locked`. | Security/auth primary + product + operations + privacy; **I**. Alternative A must be explicitly rejected or selected instead. |
| D4 / AUTH-04: What exact intent, proof, TOTP and failure rules apply? | Adopt §11.4: 180-second bounded challenge/proof, fresh password followed by newly supplied TOTP, strict generation/session/factor/source binding and no cached observation. Reuse the existing ±1 30-second-step, strictly increasing accepted-step fence; two commands cannot reuse a step. Propose 5 failed credential submissions per intent, consuming password/TOTP failures together, plus existing shared abuse ceilings; no global limit is raised. Five failures terminally invalidate that intent. This bounds proof lifetime and replay without modifying personal contracts. | Readiness §5; `mfa.py::verify_totp`, `command_digest`, `step_up`; `registration.py::spend`. | Security/auth + DB/API + operations; **I** including UX/DoS acceptance of limits and step contention. |
| D5 / AUTH-05: Which provenance and DB principals may mutate authority? | Separate real provenance/appointment/grant records from synthetic v1 and legacy `OrganizationAccess`; every edge binds tenant, subject, source kind, exact immutable revision and policy version. Runtime gets no authority-table DML, owner membership, schema CREATE, TRUNCATE or general writer. Fixed SECURITY DEFINER functions have nonlogin owners, explicit EXECUTE allowlists, trusted search_path, no dynamic SQL and no caller assertion of actor identity; functions derive actor/session/digest from an immutable verified-intent record plus its opaque proof, not a caller actor UUID. Only an isolated verifier principal may seal successful assurance records; ordinary runtime cannot insert/update/seal them or call an unverified sealing function. Actor/source checks must be repeated inside the transition function. Authentication of the verifier principal and separation from runtime/fixture role memberships are explicit DB/security acceptance obligations, not accomplished by function naming. Ordinary runtime must not be able to SET ROLE to the writer/verifier. Cross-row constraints/guarded functions—not cross-table CHECK fiction—enforce source/tenant/receipt consistency. | Readiness §6.1; GM03/05/11; `access/db_roles.sql`, existing migration guards; `controlled_preparation.py` only validates shape. | DB/API primary + security + operations; **I**. Deployed role inventory is O2. |
| D6 / AUTH-05: What serializes auth, source changes and duplicate requests? | Adopt §11.4 lock order/atomic unit, reviewed against actual auth helper calls before coding. READ COMMITTED, primary DB, DB wall clock after waits and final locked validity decision. Preserve existing 2s lock/5s statement bounds initially; they are not a workload SLA. One receipt per actor + command/decision + tenant/target + client key, UNIQUE in DB; same key/different digest conflicts. This serializes revocation and prevents duplicate outcomes without claiming physical commit-time deadline guarantees. | Readiness §§6.2–6.3; ADR-0002; `access/security.py`, `accounts/sessions.py`, `mfa.py`. | DB/API + auth/security; **I**. Real load acceptance is O2. |
| D7 / AUTH-06: May an invitation precede a resolved User/contact? | Require an independently resolved existing verified User and contact revision **before issuance**. A person may register first through already approved personal flows; no pre-account bearer invitation, email-only auto-link or first-login-wins. Contact/recipient changes revoke the offer and require fresh resolution/approval. This removes nullable-recipient ambiguity without removing personal signup. | Invitation decision; readiness §4.4; controlled snapshot nominee is currently nullable. | Product + NGO governance + security + API + privacy; **I** for issuance. |
| D8 / AUTH-06: Which token/delivery/reissue rules apply? | Recommend 256 random bits (43-character unpadded base64url), purpose-separated keyed verifier at rest and one active slot per approved nomination/role revision. Token-free same-origin landing page plus separately entered secret; no token in URL, logs, storage or receipt. Pin issuance and expiry once; resend the **same** issued secret only from separately approved encrypted delivery custody. Never reconstruct it from its verifier. Reissue revokes old verifier, requires fresh authorized issue and source checks; no silent retry or grace. Initial delivery adapter may be a test sink only, with the same expiry/dedup semantics. This makes delivery distinct from consent. | Package §5; readiness §4.4; personal fragment-link flow is not invitation approval. | Security + API + privacy + operations; **I** for token/channel/custody semantics; actual provider credentials/production delivery acceptance O2. |
| D9 / AUTH-06/07: When does acceptance expire and what does it authorize? | `expires_at = min(issued_at + 72 hours, all source deadlines)` using DB UTC instants; valid iff `effective_at <= now < expires_at`. Lock token/source/contact, require exact authenticated nominee and explicit offered version/scope/term consent. Recommend fresh password + newly supplied eligible TOTP on this consent intent using D4, without an officer capability; this is a proposed extra nominee safeguard, NOT an already accepted product requirement. Missing eligible enrollment blocks consent until the approved D3 eligibility procedure is satisfied. Consume once, append acceptance/receipt atomically. GET/preview never consumes. Acceptance records only `accepted_grant_pending`; no implicit role, profile publication or reuse after source change. Expired/revoked/declined offers cannot revive. | F5; invitation decision; readiness §§4.4/6.2. | NGO governance + security + API/DB + privacy; **I**. |
| D10 / AUTH-03/06/07: Who activates, when does the 24h clock start, and what does the grant contain? | Adopt the exact activation/bundle/clock proposal in §11.4: distinct post-acceptance authorization and issue, finite initial real bundles, accepted E05 upper bounds with explicit UTC origins/arithmetic. Acceptance alone never activates. This prevents a 72h invitation or 24h authorization from stretching a short proof, and prevents future module rights appearing in issued grants. | E register §8/E05; consolidated §§3/5; package §5; readiness §4.4; admin matrix §2. | Product/NGO governance + security + DB/API + operations; **I** for new authorize/issue phases, exact bundles, clocks and term arithmetic. No first coding-slice dependency. |
| D11 / AUTH-07: How do revocation, additional admins, last-admin and recovery work? | NGO eligibility/mandate/review-source invalidation fences dependent invitations, activation authorizations and grants immediately through root/source checks in the same lock protocol; asynchronous cleanup is not enforcement. Ordinary officer offboarding blocks that officer's future actions/unconsumed proofs and pending authorizations, not every already-issued NGO grant. Explicit invalidation of compromised/fraudulent review evidence instead fences its descendants; the incident approver must separately authorize that source invalidation. This avoids both stale authority and accidental platform-wide revocation on routine staff turnover. Replacements create new approved sources/grants, never mutate old grants back to active. Recommend at most one active Primary per NGO, no overlapping active Primaries; nominee can accept before predecessor departure, but successor activation/old grant termination are atomic. Additional-admin requester and beneficiary cannot approve; recommend one independently authorized NGO-governance confirmer distinct from both, but actual governance-form quorum must be accepted, not inferred from two platform officers. Compromise restriction can leave zero admins; recovery needs new independently corroborated nomination, approval and consent. | Admin matrix §3; GM07/09; REAL01/02; readiness §§4.3/6.2. | NGO governance + product + security + DB/API + operations; **I** for each affected branch, not unrelated local work. |
| D12 / AUTH-08: What may be stored/read/notified, and for how long? | Initial record allows opaque custody reference, issuer/rubric/version, result/reason code, examined/expiry times and qualified examiner reference; no raw documents, IDs, narratives or arbitrary URLs. Command audit adds actor/session/source/target IDs, versions, outcome and receipt correlation; no password/OTP/seed/token/verifier/full payload. Executor and independent reviewer see only assigned case metadata; nominee sees own offer/consent/status, not reviewer dossier; no Board/staff/global audit entitlement. Separate dedicated audit-reader atom must be approved before any broad audit endpoint. Notifications contain generic status/reference only and resolve recipient from approved server bindings. Recommend receipt dedup tombstones for the lifetime of the retained immutable source (never recycle a used key); actual periods, legal basis, holds and restored-backup deletion propagation must be supplied per data class by joint privacy reviewers. No invented statutory period or indefinite retention authorization. | Package §6; AUTH-08; readiness §§4.3/5/6.3; REAL04; existing append-only history. | Legal adviser **and** privacy specialist + governance/security/API/operations; **I** for data/read/notice/tombstone design; actual custody/retention operations O1/O2. |
| O1 / AUTH-01/09: Are actual appointments, identities and independent reviewers verified? | Obtain actual independently verified instruments, eligible persons, conflicts records and contract-specific signatures in access-controlled custody; publish only acceptance status/version/nonsecret reference. No names, keys or papers requested in Git/chat. These facts are necessary for real bootstrap, not for approved synthetic fixture tests. Abstract source/identity/conflict model D2/D12 must still be accepted first. | Role arrangements §§3–5; AUTH-01/09; REAL01. | Chairman/President + operations/confirmer + security + legal/privacy; **A/U** for actual bootstrap/intake, not a generic local-development blocker. |
| O2 / AUTH-09, REAL02/04: Is actual operation/transport accepted? | Independently accept actual host TLS/peer/Host/cookie/CSRF/source-IP behavior, restricted DB role inventory, appointed staff, delivery adapter, secret custody, backup/restore, incident/load/UAT and legacy cutover evidence before corresponding live use. Infrastructure merge and host acceptance cannot authorize runtime AUTH/E/GM/REAL gates. No Contabo change belongs to this package. | `infra/web-auth/README.md`; `infra/staging/README.md`; AUTH-09; REAL02/04. | Operations + security + privacy/legal + product; **A/U/R**. Any new provider or cutover **design** still requires its own affected I acceptance. |

### 11.3 Proposed finite issuer/action/target/confirmer matrix (D1)

Names below reuse §3's command families; finer decision atoms are **proposed**, not
installed permissions/routes. A platform capability permits only its listed case
operation, never a member roster, private NGO workspace or arbitrary audit query.
All actors must pass current identity/source/hold/conflict checks at execution.

| Action / exact atom proposal | Issuer/executor and target | Required independent authorization |
| --- | --- | --- |
| `platform.appointment.bootstrap.v1` | Restricted executor; exact personal beneficiary + founding source + finite platform bundle/term | D2 confirmer manifest; confirmer differs from executor/beneficiary; founder cannot approve own beneficial grant. Two initial officers are different independently vetted humans. |
| `platform.appointment.renew.v1`, `.revoke.v1` | Current designated appointment issuer/executor; exact appointment revision | Independent nonconflicted confirmer; no recipient/executor self-renewal. Urgent restrict-only authority needs its own explicit charter; no emergency issuer inferred. |
| `ngo.onboard.submit.v1` | Current Super Admin; exact controlled record/snapshot and two purpose-specific findings | Source comes from accepted offline rubric; no extra final confirmer on submit, but independent review is mandatory before any approval effect. |
| `ngo.onboard.review.approve.v1`, `.reject.v1`, `.return.v1` | Current Verification Officer; exact submitted revision | Reviewer differs from initiator and nominee as vetted natural persons and passes case-conflict policy. Recommend one such officer decision, not invented extra reviewer quorum. |
| `ngo.nominee.invite.v1`, `.revoke.v1` | Current Super Admin; exact independently approved nomination/User/contact/offer revision | Existing independent approval suffices only while all bindings remain unchanged; changed recipient/scope returns to approval, not operator discretion. |
| `ngo.nominee.accept.v1`, `.decline.v1` | Exact verified nominee; own immutable offer only | Explicit personal consent, never staff proxy. No officer capability required; D9 proposes fresh password/TOTP on the bound consent intent and must be accepted before this branch is coded. |
| `ngo.primary.authorize.v1` (new phase proposed), `ngo.primary.issue.v1` | Independent Verification Officer authorizes exact accepted source/offer; Super Admin separately executes exact grant | D10, no beneficiary self-approval; both current appointments and the prior independent approval must still be valid. No worker-issued ambient authority. |
| `ngo.admin.request.v1`, `.approve.v1`, `.revoke.v1` | Primary requests exact NGO/recipient/atoms/term; independently authorized NGO-governance approver decides | D11 quorum, requester/beneficiary exclusion and source constraints; no Primary self-issued bundle. |
| `ngo.primary.replace_recover.v1` | New legitimate NGO nomination plus independently appointed reviewer; exact old/new source revisions | Fresh verification/consent and D11 recovery policy; old admin consent is not a compromise veto. |
| `ngo.dispute.restrict.v1`, `.resolve.v1` | Specifically appointed restriction/review authority; exact source/root/restriction revision | Restricted emergency path only after explicit acceptance; resolution needs independent review, cannot create grants or private-read powers. |

Abbreviated `.verb.v1` cells expand under the immediately preceding full family
prefix, not a wildcard. Exact schema enum strings must be frozen before affected
code. For example review has three distinct atoms and proof digests, not an
unbounded caller-supplied decision. Matrix omissions mean denial. Later features
must introduce new reviewed bundle versions, never broaden issued v1 bundles.

### 11.4 Proposed shared protocol capsule (D4–D6)

This specifies the new domain substrate for acceptance; it does not repurpose
personal assurance or claim an existing secure writer exists.

- **Activation/bundle/clock proposal (D10; outside first checkpoint):** Recommend an
  explicit independent Verification Officer activation authorization **after
  acceptance**, binding unchanged approval/source/acceptance and exact grant
  bundle/term; authorized Super Admin executes a separate fresh intent-bound issue
  operation. Neither actor may be beneficiary; distinct-person checks remain.
  Authorization expires at min(authorized_at + 24h, source deadlines); it is not an
  assurance proof and never extends the 180s proof. Each execution revalidates current
  authority, mandate, acceptance, factor/contact/security generations and every
  revision. No unattended queued proof or automatic grant on acceptance. Propose
  separate real registry `ngo_authority_v1`: initial Primary bundle exactly
  `{ngo.context.enter.v1, ngo.authority.self.read.v1, ngo.admin.request.v1}`; ordinary
  Admin base exactly `{ngo.context.enter.v1, ngo.authority.self.read.v1}` plus only
  separately approved implemented-feature atoms in a new explicit bundle version. Self-
  read projects only the current actor's NGO grant/term/status, not roster, other admins
  or private case evidence. These new real-context/self-read consumers require their own
  accepted integration before issuance; they are not existing synthetic APIs. No
  profile/member/finance/future-module power is implied. Apply accepted E05 ceilings
  without reapproving their numbers: eligibility expiry min(approved end, eligibility
  examined_at + 12 calendar months); mandate expiry min(written end, mandate examined_at
  + 12 calendar months, eligibility expiry); grant expiry min(requested approved end,
  activated_at + 90 elapsed 24h days, source/mandate cutoffs). Twelve-month addition
  preserves UTC wall time and clamps Feb 29 to Feb 28 when necessary. `examined_at` must
  not be future; issue/activation timestamps come from DB clock, not a caller. No
  grace/auto-renewal; renewal needs new exact approval/acceptance. These clock
  origins/arithmetic, not E05 numbers, require acceptance.
- **Canonical intent:** strict per-command JSON schema, rejecting unknown/duplicate
  keys, floats and malformed UUIDs/times. UUIDs use lowercase hyphenated form;
  UTC timestamps use `YYYY-MM-DDTHH:mm:ss.ffffffZ`; strings are restricted by each
  field's schema (no free-form Unicode evidence). Construct a server-owned object
  containing contract/atom/version, actor/User, logical session **and current
  credential generation**, tenant/target, source/root/case/approval/recipient/contact/
  factor/grant revisions applicable to that command, exact bounded bundle/term,
  policy version, proposed transition and client idempotency key. Serialize UTF-8
  JSON with sorted keys, separators `(',', ':')`, no ASCII escaping and no NaN.
  Purpose-separated HMAC-SHA256 under versioned external command keys binds these
  bytes; clients never supply actor authority, canonical digest or secret payload.
- **Challenge/proof:** 256-bit random secret with keyed verifier at rest; bind all
  above fields plus auth epoch/recovery generation and approved factor ID/revision.
  Expires at min(DB issued_at + 180s, original session/access/idle/source/command
  deadlines); confirmation never restarts the clock. Validate fresh password then
  a new eligible TOTP under the existing monotonic step fence; no `recent()` reuse.
  Bad secret/credential consumes an attempt (D4); missing/wrong binding, changed
  generation/source, expiry or stale revision terminally invalidates the intent.
  Password/TOTP failure below the cap permits only a newly supplied credential on
  the same unchanged intent; any failed password still spends shared abuse budget.
  Propose fixed server route buckets `domain-intent` for issuance and
  `domain-assurance` for credential submission: 30/900s per observed REMOTE_ADDR
  and 30/900s per actor across all intents (use purpose-separated actor digest,
  not a caller route/flow label). TOTP retains `mfa:300`, at most 5 attempts per
  factor/5-minute bucket including other personal operations. Commit IP/actor
  budgets independently **before User locks**. Factor attempts and
  successful step updates commit in the verifier transaction, including normal
  credential denials; an exceptional verifier rollback still leaves IP/actor cost
  spent. Returned 429/Retry-After cannot be bypassed with a new intent.
  Do not trust forwarded IP
  or claim per-end-user budgets behind a proxy. Retain stricter existing limits.
- **No credentials in commands:** only the dedicated assurance request receives
  password/TOTP transiently. Domain mutation receives opaque intent/proof reference,
  not raw credentials. Proof never appears in URL, storage, logs, audit or receipts.
  A held/revoked/inactive actor cannot confirm, execute or read a private receipt.
- **Lock graph:** resolve candidate IDs without disclosing data, then lock all
  involved Users in ascending UUID order; contacts/factors, sessions, credentials/
  intents in reviewed auth-helper order; platform roots ordered by UUID before NGO
  roots ordered by UUID; appointments/grants; record/snapshot/approval; invitation/
  acceptance; receipt slot. Rows within each class use ascending UUID order. Acquire
  no late User/root locks. Every mutation/revocation helper must use this graph;
  inventory actual helper lock acquisitions and reject any reverse edge before
  acceptance. Initial proposal uses existing 2s/5s bounds and final DB wall clock
  check, not a physical-commit-before-expiry promise.
- **Code-backed helper inventory for D6 acceptance:**
  `sessions.authenticate_locked`: User → contact → session → mobile credential;
  `mfa_views.endpoint`: User → factor(s) → `authenticate_locked` → assurance intent;
  `mfa.verify_totp`: caller-held factor → abuse bucket → step update;
  `sessions.revoke_all_locked`: caller-held User → sessions in ID order → credential
  updates. The new coordinator must prelock **all** Users, then contacts and factors
  (contacts before factors for each class), before calling either auth helper;
  repeated already-held locks do not permit discovery of a new late User. Do not
  call `registration.spend`'s separate budget transaction while holding domain
  roots, or wrap the HTTP MFA adapter as a domain helper. Verifier commits proof/
  step state first; executor later locks intent and roots and rechecks versions.
  Factor removal must serialize through User/eligibility generation, so a proof
  minted before removal cannot execute afterward. New helper edges must be added
  to the reviewed inventory; existing personal flows are not silently reordered.
- **Atomic decision:** under those locks reauthenticate/revalidate current sources,
  proof, versions and deadlines; consume proof/token, transition + increment revision,
  insert immutable event and required notice intent/outbox + receipt in one durable
  transaction. No external delivery or lazy protected queryset escapes the boundary.
  Audit/outbox/receipt failure rolls back the domain outcome and provisional proof
  consumption; independent abuse/failure accounting must still commit. A successful
  TOTP step remains spent even if the later domain transaction rolls back: confirm
  assurance separately before execution, and do not roll back its anti-replay fence.
- **Receipt and retry:** key is 128 random client bits, scoped/unique as D6. Bind it
  to one canonical digest before execution; after concurrent creation reread the
  winner under locks. Fresh/current actor authorization and receipt-reader scope
  are required even for retries. Identical committed digest returns the existing
  minimized receipt, never reruns a write or rechecks a consumed proof as a new
  mutation. Different digest gets 409. Owned missing version gets 428; stale version
  412; invisible tenant/receipt 404; auth/CSRF denials retain existing semantics;
  dependency/deadlock/audit failure 503. Lock timeout permits only explicit same-key
  retry of an unchanged still-valid intent, never automatic resubmission/new key.
  Lost response means **unknown**; status lookup uses the original key. A missing
  receipt is not proof of noncommit or permission to manufacture another intent.
  New DTOs/errors need OpenAPI/fixture review; existing unavailable endpoints and
  personal error contracts remain unchanged until their own authorized integration.

### 11.5 Smallest proposed coding work package and acceptance

**One internal checkpoint of PWC-04C, not a new roadmap phase or completion of 04C:**
protected domain assurance + restricted, receipt-backed controlled submission and
independent decision in an **explicitly accepted synthetic-only exercise**.
Only these four domain atoms are in the initial command registry:
`ngo.onboard.submit.v1`, `ngo.onboard.review.approve.v1`,
`ngo.onboard.review.reject.v1`, `ngo.onboard.review.return.v1`.

**Admission to coding:** independent acceptance of D1 for these four atoms and the
synthetic actor/source/conflict fixture charter, D2's abstract authority/trust model
(not live bootstrap implementation), D3–D6 and the minimal D12 metadata/receipt/
notice-retention model. For this checkpoint only, retain fixture receipts/tombstones
  through all replay/restore tests and destroy them only with the disposable fixture
  database; do not require a production statutory-duration decision to execute
  accepted local synthetic tests. Real-data retention remains D12/O1/O2-gated.
  Record relevant AUTH/E/GM acceptance per branch; synthetic
fixtures alone do not waive the existing GM implementation gates. If any affected
I rule remains unsigned, that component stays contract-only. D7–D11 decisions are
prepared above but do not block this no-invitation/no-grant checkpoint. Actual
appointments, provider, Contabo and real-host evidence O1/O2 do not block the
accepted fixture-only test exercise. Synthetic source fixtures must be isolated
  and bounded to no more than 24h; this adds no extension to existing v1 grants.

**Code IN after admission:**

1. Reuse current personal authentication, TOTP cryptography/step fence, exact-revision
   structural preflight, controlled record/history and existing error conventions.
   Add a distinct domain-intent/verifier/receipt boundary; do not extend personal
   assurance operations or mutate synthetic authorization v1.
2. In an isolated PostgreSQL fixture-only environment, add only needed additive
   source/intent/receipt/event constraints and fixed least-privilege transition
   functions. Use dedicated test source/appointment fixtures from the explicitly
   approved charter, never public/client `actor_is_officer` inputs. No production
   fixture role credentials/membership in runtime. Existing production command
   availability remains false; fixture authorization is not a real-source fallback.
3. Expose only internal tested service/DB functions in this checkpoint, not new
   privileged HTTP endpoints, public readers, successful OpenAPI operations or
   shipped client adapters. Review DTO candidates/test vectors without claiming
   wire success. A later accepted integration checkpoint must add actual wire
   contracts and client behavior together, not silently enable old unavailable URLs.
4. Success creates only a controlled state revision, immutable decision event and
   receipt/notice intent. Even `approved` creates **zero** `NGOGrant`, real grants,
   `OrganizationAccess`, workspace verification/publication, invitation or platform
   appointment. Failed/stale/cross-tenant operations create no successful mutation.

**OUT:** executable officer provisioning, real data/authority sources, invitation/
acceptance/activation, additional-admin/Primary recovery writers, raw evidence,
public intake, 04D publication, private roster/audit/export APIs, finance/signatory/
alliance/support, provider integration, native allowlist or credentialed browser
transport changes, deployment or Contabo modifications. Complete 04C remains open.
No outbox worker, provider or generalized file service is justified by this slice.

**Required tests and acceptance criteria:**

- PostgreSQL actual restricted principals cannot forge sources, promote fixtures,
  DML authority/history tables, SET ROLE to owner, or invoke another command.
  Same person under two accounts, staff/superuser/Board/recovery/MFA alone, wrong
  actor/session/source kind and NGO A/B list/detail/status selectors all deny.
- Known canonical bytes/digest vectors; duplicate/unknown JSON fields, alternate
  representation, decision/recipient/tenant/bundle/version/key substitution deny.
  Fresh password AND new eligible TOTP required; cached login MFA, repeated step,
  old/new replacement factor, held account, fifth failure, boundary expiry,
  session rotation/revoke and reset/contact/security generation changes tested.
- Multi-connection barriers for approve-vs-reject, submit-vs-withdraw, duplicate key,
  same-key/different-body, source-revoke-vs-execute, factor-change-vs-confirm and
  timeout after lock wait. Exactly one valid revision/event/receipt per command;
  rollback/fault injection at proof/domain/event/notice/receipt stages leaves no
  partial domain result. Already spent TOTP cannot be reused after rollback.
- Lost response recovered only through owned receipt; replay/new key cannot create
  a second effect. Revoked actor cannot use retry/status as a private-data oracle.
  No secrets/payloads/raw evidence in rows, logs or test artifacts; delivery intent
  remains synthetic, deduplicated and has no network side effect.
- Run Django checks, migration plan/application/drift/check and restricted-role
  tests on PostgreSQL, full backend/contract regression, existing web checks and
  direct-TLS tests; run Flutter contracts/analyzer/tests when shared/mobile inputs
  change. Preserve all currently shipped unavailable behavior, personal auth,
  native/public allowlists, four-field public projection and synthetic ceiling.
- Done means accepted affected contracts referenced by immutable version/commit,
  coherent additive migrations and tested forward-fix/rollback rehearsal, negative
  and concurrency evidence, updated roadmap, clean scoped diff and one reviewed PR.
  It does **not** mean actual deployment, live authority or completion of P3/G1b.

**Next decision action:** accountable reviewers disposition D1–D12 (accept/amend/
reject/defer), stating per-command scope and residual exclusions. For the minimal
checkpoint, accept only its admission subset if appropriate; do not request a
production transport signature as a substitute. This assignment prepares those
exact contracts and test obligations; it records no new human acceptance.

### 11.9 Bounded implementation started — 3 November 2026

This addendum implements the subsequently requested **independently safe** work;
it does not amend §11.5's admission rule for executable protected components.
At that implementation checkpoint PR #31 was open; neither code nor PR
disposition signs D1–D12. It is now merged at `5118ad6`; see §11.10.
Latest merged `main` checked at `64a51ea` before implementation.

**Implemented without privileged transitions:**

- `organizations/controlled_command_shape.py`: closed **proposed** four-name
  vocabulary, immutable/redacted syntax objects, bounded strict UTF-8 JSON,
  duplicate/unknown-key rejection, canonical nonzero UUIDs, integer-only bounded
  source revisions and structural source/tenant matching. This is not canonical
  proof serialization, authenticated source binding, an authorization registry,
  assurance or an executable command. No route/adapter calls it; its success
  result confers no authority. Existing `command_available` remains false.
- `test_controlled_command_shape.py`: unsaved synthetic source builder and
  database-free negative tests, reusing existing `prepare_submission` and
  `preflight` rather than creating a second state machine or auth system.
- `test_controlled_boundary_harness.py`: actual PostgreSQL multi-connection
  NOWAIT contention, structural rollback fault and ephemeral nonlogin role
  read/lock/DML/DDL denials. Role creation is rolled back, requires the same
  isolated test-cluster role-administration privilege as existing kernel tests,
  and ships **no production principal, writer, migration or privileged service**.
  This no-table-privilege probe is not the future runtime/verifier/writer policy,
  nor evidence of its SET ROLE isolation or cross-NGO query enforcement.

**Exact remaining executable checkpoint blockers** (proposals remain unsigned):

The following is the **current fixture-checkpoint decision queue**, reconciled
against merged PR31 (`5118ad685740c06350c3d2e3f69336347d9a9950`). Each row is
**PENDING accountable acceptance**; accept/amend/reject the exact referenced
proposal using §8 (reviewer/role, immutable version/commit, date, fixture scope,
evidence, conditions and exclusions). F1–F9 and E05 limits are not resubmitted.

| Decision | Exact proposal to accept/amend for fixture submission/review | Accountable reviewers |
|---|---|---|
| D1 | §11.3/11.5: only `ngo.onboard.submit.v1` and `ngo.onboard.review.{approve,reject,return}.v1` (three literal review atoms, no wildcard); exact submitter/reviewer issuer→target/confirmer matrix and independently authenticated synthetic actor/source/conflict charter. No installed role-label fallback. | Product + NGO governance + security + DB/API + operations |
| D2 (unavoidable trust dependency only) | §11.2 D2/11.5: accept abstract external trust-anchor and independently confirmed exact actor/source binding, outside runtime/fixture write control, including how synthetic authority is authenticated and cannot promote itself. No live bootstrap CLI, named appointments, provisioning or key custody implementation in this checkpoint. | Founding governance + security + operations + DB/API + legal/privacy |
| D3 | GM06 **B**: ordinary factor removal remains possible, but removal/replacement, recovery or hold atomically fences protected eligibility/intents; no automatic restoration. Eligible initial factor and re-verification are independently recorded against exact factor ID/revision. Explicitly select B or amend/reject it. | Auth/security + product + operations + privacy |
| D4 | §11.4: separate domain intents; canonical server-owned command/version/actor/session/generation/tenant/target/source/revision/key bindings; purpose-separated HMAC; 256-bit proof verifier; original-deadline-bounded ≤180s; fresh password then new eligible monotonic TOTP. Five failed credential attempts terminally invalidate; actor/IP 30/900s and existing factor 5/300s fences; no personal recent-MFA reuse. Accept serialization, failure/invalidation and budget commit semantics together. | Auth/security + DB/API + operations |
| D5 | §11.2 D5/11.4: separate provenance plus restricted runtime/verifier/narrow writer; only isolated verifier seals proofs, actor derived from verified intent; runtime/fixtures cannot forge source/proof, DML protected tables or SET ROLE to owners. Accept principal authentication/membership, fixed-function privileges and trusted search_path model, not just function names. | DB/API + security + operations |
| D6 | §11.4: reviewed User→auth→root→source→record→receipt lock graph against existing auth helpers; READ COMMITTED, primary DB clock after waits, 2s/5s bounds; separately committed assurance/anti-replay fence; atomic transition+revision+proof consumption+event+notice intent+receipt. Unique actor/command/tenant/target/key receipt; identical digest returns owned receipt after current authorization, changed digest conflicts; rollback/lost-response semantics as specified. | DB/API + auth/security |
| D12 minimum | §11.2 D12/11.5: minimized external evidence references and event/receipt/notice fields; exact assigned-case/owned-receipt audiences, generic notices with server-resolved recipient, no broad audit reader or secrets/raw evidence. Keep fixture receipts/tombstones through replay/restore tests, destroy only with disposable DB. No production statutory-retention decision needed for this exercise. | Legal adviser **and** privacy specialist + NGO governance + security + DB/API + operations |

Aligned AUTH/E/GM gates remain. D7–D11 invitation/grant decisions do not block this
no-invite/no-grant work; neither O1/O2, Contabo nor live transport approval blocks
unrelated local code. Disposable fixture data is destroyed with its test database.

**Not built or claimed tested:** protected submission; independent exact-revision
approve/reject/return; domain password/TOTP verification or sealed proofs; real
source authorization; atomic audit/idempotent receipt; receipt replay/revocation,
NGO-isolated protected queries, full auth/source lock graph or decision races.
Those tests require the affected contracts and actual implementation, not fake
successful fixture authorities. No endpoint, client, native allowlist, deployment,
credentialed transport, invitation, grant, publication or finance changes.

**Validation for this bounded code:** PostgreSQL 16.2, Python 3.11; locked CI Python
requirements installed without changes. `manage.py test` for command-shape,
boundary-harness, controlled-onboarding and controlled-preparation modules: **32
passed**. Full `coverage run manage.py test --testrunner
contracts.testing.ContractRunner --noinput`: **488 passed**, **309** observed
route/method/status combinations. Initial full run caught the expected new-module
source-lock drift; standard `contracts.generate` added only its SHA-256 entry;
rerun passed. Frozen API compatibility, OpenAPI and generated clients unchanged.
Django check, migration drift/plan/application/check, pip check, focused Ruff and
contract generation/type checks passed. `npm run check`: **187 passed**, typecheck,
format/token checks and both builds passed. No browser/Flutter rerun or independent
host acceptance claimed. Existing PR31 head before this update had Django 3.11/3.12
and compose green, foundation red at `npm audit --audit-level=low`. Local audit
reproduced **3 moderate** package findings (`minimatch`, propagated through
`@redocly/openapi-core` and `openapi-typescript`; GHSA-g3hv-75wg-m249). Dependency
upgrade remains separate; audit gate is unchanged. New-head CI is separate from
these local results and must be checked after push. None of these tests supplies
the pending contract signatures or protected-workflow acceptance.


### 11.10 Small source-validation follow-up from merged PR31 — 3 November 2026

**Reconciliation/acceptance evidence:** PR31 merged at `5118ad6`; its GitHub review
and comment lists are empty when checked for this task. Package §2/§8/§11.2,
consolidated contract status, ADR-0002's approval scope/addendum and ADR-0004's
status record **no accountable acceptance of the affected D contracts**. Existing
core/synthetic technical approval is documented in ADR-0002 (24 October); product
policy approvals are recorded in ADR-0004/E register (27 October). Neither extends
to these new domain atoms, proofs, factor eligibility or provenance/writer/lock
contracts. The decision table above is the action queue, not a new approval.

**Working code delta:** `check_source_shape` now reuses `CommandShape` validation
for supplied source UUID/revision fields and converts missing attributes into its
existing redacted error. Equality-spoofing non-UUID objects no longer match. Three
new database-free tests cover malformed/missing sources and legitimate pre-NGO
(null organization) sources. A PostgreSQL test rechecks locked current metadata,
rejects stale candidates, stale immutable evidence even after changing the request
revision, and record/snapshot substitution. Test-owner revision edits exercise
structural validation only, never a protected submit/review operation. The checker
still trusts caller-supplied records, performs no lookup/locking/authorization and
returns no executable command; callers must not treat this fix as source trust.

**Evidence:** 36 targeted tests passed; full instrumented PostgreSQL 16.2/Python
3.11 regression **492 passed**, **309** route/method/status combinations. Only the
source-lock hash changes in API artifacts; no API operation/client/migration/model
or personal auth changes. No privileged transition or D-dependent service/writer
was added. D1–D6/minimum D12 remain blocked as listed; D7–D11, host acceptance,
Contabo and production retention are not prerequisites for these safe tests.
