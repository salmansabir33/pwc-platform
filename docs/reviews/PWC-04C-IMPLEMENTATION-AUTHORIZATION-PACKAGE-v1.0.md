# PWC-04C — Implementation Authorization and Independent Sign-off Package v1.0

**Prepared:** 27 October 2026 (Asia/Karachi)  
**Status:** REVIEW PACKAGE — NOT AUTHORIZED for real privileged-command implementation, sensitive data intake or activation  
**Roadmap:** P3 / PWC-04C; dependencies PWC-03B.3 and PWC-04B; retain P0–P8, M1–M3 and lettered tickets  
**Baseline:** main after merged PR #24 (`9d2f5072`)  
**Purpose:** Bring the eight critical implementation blockers in the PWC-04C readiness review to explicit accountable decisions in **one** package, without a string of separate product-choice PRs.

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
