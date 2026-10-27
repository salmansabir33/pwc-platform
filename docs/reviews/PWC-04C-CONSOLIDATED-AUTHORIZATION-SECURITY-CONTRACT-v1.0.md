# PWC-04C — Consolidated Authority, Security and Activation Contract v1.0

**Date:** 27 October 2026 (Asia/Karachi)  
**Status:** PROPOSED TECHNICAL CONTRACT — product decisions adopted; accountable independent security, NGO-policy, platform-operations, database/API and privacy/legal approvals **not yet evidenced**  
**Roadmap:** P3 / PWC-04C, with PWC-03B.3 dependencies; no new phase or scope reduction

## 1. Governing decisions and strict separation

Product owner has approved: (a) founding platform authority signs separate offline appointments for first Super Admin and independent Verification Officer; (b) officers use existing PWC personal identities, not privileged login accounts; (c) initial grants are manually provisioned by restricted technical operator with independently authorized confirmer; (d) externally verified NGO nominates representative in official record; (e) PWC operator submits exact NGO/mandate revision and separate officer approves; (f) exact recipient receives one-use invitation with **maximum 72-hour expiry** and signs in/verifies email/accepts specific **nonfinance** role; (g) Primary NGO Administrator versus scoped ordinary administrators, with additional-admin appointment by independently approved process; (h) sensitive platform commands require **fresh password plus TOTP bound to the exact action**.

Separate legal NGO existence, organization eligibility, representative mandate, technical authority, published profile consent and PWC alliance membership. A Board title, Django staff/superuser flag, login/MFA/recovery status, applicant claim or synthetic grant must **never** yield platform or NGO-private access. No automatic finance/signatory/alliance/collaboration/support powers.

## 2. Command families and issuance matrix — PROPOSED, not approved

| Command family | Initiator / required source | Independent authority / beneficiary restriction | Effects and prohibition |
| --- | --- | --- | --- |
| `PLATFORM_OFFICER_BOOTSTRAP` | Restricted technical executor; signed founding appointment and verified exact personal identity | Separate named confirming authority, independent of executor/beneficiary and appointment recipient | Time/scope bounded platform grant **only after** separate contract sign-off; no general Django or raw ORM grant writer. |
| `PLATFORM_OFFICER_RENEW/REVOKE` | Currently authorized platform appointment issuer or restricted incident authority | Separate nonconflicted approver under explicit issuer matrix; revoke may use independently approved urgent containment | Immediate server-side authorization fence; no insecure last-admin immunity. |
| `NGO_ONBOARD_SUBMIT` | Currently authorized PWC Super Admin | No final approval by initiating/benefiting principal | Exact offline-reviewed organization + nominee/mandate attestation revision; no upload requirement. |
| `NGO_ONBOARD_APPROVE/REJECT/RETURN` | Appointed independent Verification Officer | Cannot be initiating Super Admin, nominee, conflicted reviewer or self-approver; explicit two-distinct-human confirmation policy | Revision-bound independently reviewed status; no automatic NGO grant. |
| `NOMINEE_INVITE_ISSUE/REVOKE` | Authorized Super Admin on independently approved nomination revision | Preapproved exact recipient, registered source validity and appointment assurance; never arbitrary target | Single-use, recipient-bound, max 72-hour invite; no power before acceptance. |
| `NOMINEE_INVITE_ACCEPT/DECLINE` | Exact nominated, authenticated, verified personal identity | No acceptance by staff, agent, applicant impersonator or different account | Explicit role/scope/version consent; acceptance alone is **not** synthetic or real NGO grant. |
| `NGO_INITIAL_NONFINANCE_GRANT` | Protected writer with independently evidenced nomination + authorized invite acceptance | Issuer matrix, bounded grant, nonconflicted approval and proof; no root auto-elevation | Precisely defined Primary nonfinance capabilities only after independently accepted PWC-03B.3 contract. |
| `NGO_ADMIN_APPOINT/CHANGE/REVOKE` | Primary NGO Administrator **requests** exact bounded action | Independent authorized approval per NGO governance; no self-grant/self-approval or cross-NGO effect | Ordinary NGO Admin receives only requested functional sub-capabilities; root transfer requires new official nomination. |
| `NGO_PRIMARY_REPLACE/RECOVER` | Fresh NGO governance-valid nomination and verified identity | Fresh external corroboration + independent platform approval; separate recipient acceptance | Never implicit successor, account reset, existing admin veto or expired-grant resurrection. |
| `DISPUTE_RESTRICT/REVIEW/RESOLVE` | Specifically appointed safeguarding/incident authority on credible evidence | Independently reviewed action; no broad private-read privilege | Restriction-only urgent containment if separately authorized, no automatic unfreeze or silent grant. |

**Not executable policy:** Exact issuer identities, legal authority, human quorum, capability IDs, action schemas, time bounds, assurance proof and writer implementation remain unresolved; this matrix is a review draft only.

## 3. Proposed lifetime and source constraints

- NGO platform eligibility: **12-month maximum** subject to accepted NGO-policy rubric and status changes.
- Representative mandate: earlier of written mandate end and **12 months maximum**.
- Real nonfinance authority grant: earlier of source/mandate expiration and **90 days maximum**, with fresh grant/acceptance on renewal as approved.
- Nominee invitation: earlier of source validity and **72 hours maximum**, consumed once.
- Activation command authorization: at most **24 hours** from independently authorized decision, bounded by source and command assurance.
- No automatic renewal, post-expiry grace, inherited finance grants or extension due to appeal/recovery.
- These were earlier **product upper-bound recommendations**; the precise limits/clock origins and renewal rules remain independently gated. Existing synthetic-grant 24-hour constraints remain unchanged.

## 4. Proposed operation-bound assurance contract

Every protected command requires an active verified personal identity and session, active scoped platform/NGO authority, no disqualifying hold or restriction, and **fresh password plus current TOTP** for sensitive platform actions. The backend should generate a single-use challenge with an unguessable identifier, canonical command family/target/principal/NGO/case revision/scope and short configurable expiry. Any mutation must atomically consume approved intent after fresh password/TOTP verification, re-check current grants/holds/source/revisions and persist result/audit/idempotency receipt in one transaction. Reject replay, alternate target, rotated context, stale revision, previous factor or permission revocation.

**Do not implement based solely on this sketch.** Security/auth reviewers must specify exact canonicalization, challenge TTL, factor window/reuse/re-enrollment eligibility, proof storage, failure/lockout, lost response recovery, and protected command taxonomy. Explicitly decide **GM06**: whether factor removal is prohibited during outstanding protected duties or protected actions are suspended after factor removal/re-enrollment; no recovery code/new TOTP seed or personal account recovery may bypass sensitive command assurance. No generic recent-MFA boolean qualifies.

## 5. Invitation and acceptance contract to approve

Proposed lifecycle: `draft_authorized → issued → delivered/pending → accepted → grant_pending → activated`, with `declined`, `expired`, `revoked`, `delivery_failed`, and `blocked` terminal/handled exceptions. **Never equate `accepted` with an active role.** A nonce/token must be opaque, one-use, securely stored as a verifier (not plaintext), scoped to exact personal identity and approved NGO/mandate/role version. Never expose persistent secrets in URLs, browser storage, analytics or audit. Bind recipient identity with independently verified account/email contact, and protect against reused/changed email and account collision. Failed/bounced delivery and retries do not extend expiry or issue an unintended second token.

Security/API/operations must define token entropy, exact delivery flow and URI fragment handling, password/TOTP ceremony, permitted resend/reissue/revoke actions, idempotency and atomic transition semantics, notice and privacy before any live issuance.

## 6. Database, audit, notices and isolation contract to approve

- Source-of-truth PostgreSQL invariants: same-tenant ownership, exact grant provenance (never synthetic), signed/validated issuer/approver identities, independent reviewer, immutable case revisions, grant/source expiry and suspension fences.
- Protected writes by narrow designated DB authority with least-privilege runtime user; prohibit unrestricted ORM privilege changes, source forgery and synthetic-to-real promotion.
- Defined global lock order across user/appointment/NGO/case/grant/invitation/idempotency; single transaction for authorization recheck + proof consumption + transition + immutable event/outbox + receipt. No external delivery within held locks.
- Receipts support same-principal exact-intent idempotent retry and separately authorized status fetch after lost response. No blind automatic retry with new key for sensitive operations.
- Audit must preserve minimal action/status/source/target/version, subject to privacy/retention controls; no raw nomination documents, passwords, TOTP seeds, tokens, NGO-private rosters or finance values in broad logs.
- Notices to nominee/officers and operations must use documented recipient/channel, content redaction, safe delay/exception, deduplication and delivery failure handling.
- No platform title, applicant status or web UI route bypasses tenant-scoped Django authorization. Require adversarial tests for NGO A/B, initiator=approver, duplicated invitation, stale revisions, revocation races and compromise recovery.

## 7. Recovery and revocation principles

Normal departures: new approved nominee/appointment and recipient acceptance precede planned surrender where possible. Compromise: revoke/suspend immediately even for last active authority; restore only through independently verified new nomination/appointment. Personal password reset/MFA recovery never reinstates roles. Do not auto-freeze on uncorroborated third-party allegations; require specific credible-risk threshold and independent dispute triage. Emergency restriction is **restrict-only** until independently approved responder matrix, review deadline and incident procedure; never emergency data disclosure/grant.

Any temporary delegation remains disabled in initial rollout. Later delegation/finance/signatory/alliances require their own separate approvals.

## 8. Acceptance and review gate checklist

| Owner / reviewer function | Must accept before protected implementation |
| --- | --- |
| NGO governance / founding appointing authority | Exact signed designation, nomination evidentiary rubric, issuer/quorum matrix, appointment/mandate validity, contested replacement |
| Security / authentication | MFA proof protocol, GM06 branch, factor continuity, lockout, challenge replay, account recovery, privileged root |
| Database / API | Real-grant schema/DB writer, transactional lock order, version/error/idempotency/receipts, OpenAPI command contracts |
| Platform operations | Named actual provisioning operators/confirmers, custody and execution runbook, emergency revocation, credential management, alerts |
| Privacy / legal | External evidence custody, minimal attestation reference fields, lawful basis, notices, retention, appeals, recipient data and backups |
| Product owner | Exact initial Primary/ordinary role permission codes, screen/action copy, launch scope and capability exclusions |
| Release reviewers | Real HTTPS/cookie/CSRF, provider and mail delivery, monitoring/restore, mobile/web integration, accessibility/Urdu, pilot evidence |

Approval requires a dated record naming **actual accountable humans**, accepted contract version, environment, supporting tests and remaining exclusions. The product owner approving high-level preferences is not approval on behalf of security/legal/operations. Existing E01–E18, GM01–GM12 and REAL01–REAL04 registers remain authoritative on the exact gates. Until reviews close the affected **I** gates, leave real writes, reviewer-reader grants, invitations and NGO permissions unavailable. No implementation task may silently relabel I to A/R.

## 9. Roadmap and client implementation handoff

PWC-04C includes scoped nonfinance admin roles/grants, secure invite/acceptance and governed replacement/revocation, plus React/Flutter interactions as required by canonical screen specifications. Use `docs/design/PWC_DESIGN_SYSTEM_v1.0.md`; source screens and accepted APIs determine actual UI. PWC-03B.3 remains its privileged grant-command dependency; 04D publication/profile and P4–P8 remain separate. No new lettered roadmap phase.

One comprehensive Codex prompt per PWC-04C subphase may include contract implementation **only after** the affected independent approvals are recorded. Until then, implement only specifically allowed default-off preparations and document blockers; do not misrepresent synthetic UI or successful unit tests as live onboarding.

## 10. Source documents

- [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), especially dated reconciliation §11.
- [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md).
- [Founding authority](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md); [manual officer provisioning](PWC-04C-MANUAL-PLATFORM-OFFICER-PROVISIONING-DECISION.md); [identity/grant separation](PWC-04C-PLATFORM-OFFICER-IDENTITY-AND-PRIVILEGE-SEPARATION-DECISION.md).
- [Representative invitation](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md); [NGO admin matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md); [password/TOTP decision](PWC-04C-OPERATION-BOUND-PASSWORD-AND-TOTP-DECISION.md).
- [E decision register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md); [GM/REAL register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).
