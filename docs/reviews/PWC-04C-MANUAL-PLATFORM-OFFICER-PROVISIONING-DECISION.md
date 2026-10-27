# PWC-04C — Initial Platform Officer Manual Provisioning Decision

**Date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product-level deployment/provisioning direction, not a security or activation approval  
**Decision source:** Product owner explicitly approved manual provisioning by an authorized technical operator via a secure, independent-authorized procedure rather than a public appointment screen.

## Approved initial-rollout direction

1. **Manual, restricted bootstrap:** The initial PWC Super Admin and independent PWC Verification Officer platform privileges are provisioned **manually through a narrowly authorized, auditable technical procedure**, not through public officer signup, a public appointment endpoint, or an unrestricted Django Admin shortcut.
2. **Appointment precedes provisioning:** The formally designated founding platform authority issues two **separate signed offline appointments**, tied to two distinct, independently vetted people and their exact pre-existing/verified PWC personal identities. Written appointment alone does not confer application permission.
3. **Distinct responsible functions:** A specifically authorized technical operator executes the bounded provisioning operation only after checking appointment provenance and recipient identity. An **independent authorizer/confirmer** must approve the proposed target, scope and version before the privileges become effective. The technical executor cannot independently issue or approve their own authority; the exact human-function separation and bootstrap issuer matrix require security/operations sign-off.
4. **Separate privileges:** PWC platform permissions use separate bounded, revocable grants linked to the personal account and appointment, not `is_superuser`, `is_staff`, Board membership, MFA, recovery status or synthetic NGO grants. No platform privilege creates NGO-private finance/member/records access.
5. **Controlled scope and lifecycle:** Provision only precisely approved platform actions and initial validity; independently reviewed expiry, renewal, suspension, revocation, compromise containment and replacement remain necessary. No general-purpose raw ORM grant writer or production fixture promotion.
6. **Evidence and accountability:** Preserve minimized references to the signed appointment and distinct authorization, exact recipient, issuer, executor, confirmer, command version, outcome and immutable audit history. Handle offline appointment documents under separately approved privacy/retention/custody rules; do not upload raw files by default.
7. **Fail closed:** If verified identities, signatures, independent confirmation, assurance, restricted writer or command audit cannot be established, the real privilege remains unavailable. Manual provisioning never bypasses approved personal MFA or operational proof requirements.

## Outstanding contracts before any real provisioning command

This is **product-owner agreement to the procedure type**, not approval of its implementation or use. The exact following still require independently accountable **security, platform operations, NGO governance and privacy/legal** acceptance:

- The named founding appointing authority's valid designating instrument, offline appointment evidence/custody and identity proofing of both officers.
- Explicit **initial issuer → technical executor → independent confirmer → recipient** authority matrix, duties, human independence, conflicts, separation or emergency replacement and revocation.
- A protected provisioning instrument (e.g. narrowly scoped offline CLI/service) with dedicated database ownership/EXECUTE restrictions, trust anchoring, least privilege, replay/idempotency and audited atomic grants; no general-purpose role toggle.
- Exact platform capability codes and scopes, grant version, maximum validity/renewal, active eligibility and immediate revocation, including handling compromised last operator and recovery.
- Password/TOTP/operation-bound step-up proof, intent normalization, proof lifetime, factor continuity/recovery limitations (including unresolved GM06), session/hold semantics and device assurance.
- Secret handling, secured execution environment, peer witness/approval evidence, logs without secrets, alert/notice delivery, incident drills, rollback and restore.
- Deployment controls and tests (real source-of-truth identity mapping, concurrency, self-issue/forgery, cross-NGO data reads, session invalidation, compromised/grant expiry).

**Implementation/activation status:** E04/E09/E10/E11/E14/E17, applicable GM01–GM12 and REAL01–REAL04 gates remain open; do not implement or activate real platform appointment command paths beyond expressly permitted deny-default preparation until affected contracts are approved.

## Traceability

- [Roadmap v2.0 and execution reconciliation](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md): P3/PWC-04C; preserve P0–P8.
- [ADR-0004 — NGO verification and authority](../decisions/ADR-0004-ngo-verification-and-representative-authority.md).
- [Founding appointing authority decision](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md).
- [Existing personal identity and separate officer privileges](PWC-04C-PLATFORM-OFFICER-IDENTITY-AND-PRIVILEGE-SEPARATION-DECISION.md).
- [Representative invitation/activation policy](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md).
- [NGO Administrator permission matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md).
- [E decision register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md) and [GM/REAL privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).

Documentation-only approval record. No provisioning commands, roles, migrations or authority activation are implemented by this PR.
