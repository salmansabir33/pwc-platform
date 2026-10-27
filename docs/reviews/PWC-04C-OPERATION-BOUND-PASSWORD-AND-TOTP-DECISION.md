# PWC-04C — Sensitive Platform Operations: Password and TOTP Product Decision

**Decision date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product-level assurance direction; technical/security acceptance and real command activation remain blocked  
**Source:** Product owner explicitly approved fresh password confirmation **and** current TOTP for sensitive PWC Super Admin and Verification Officer operations, bound to the exact intended action.

## Approved policy

1. A platform officer must have a **verified personal identity**, a currently valid authenticated session, and current separately provisioned and independently approved platform authority. Neither login/MFA nor platform job title alone confers the relevant operation capability.
2. Before a **sensitive platform command**, require **both** a fresh password verification and a fresh current TOTP factor, cryptographically or server-transactionally bound to that specific command intent and its canonical target, action, authorized scope and relevant revision. Ordinary login MFA or a generic recently authenticated flag is insufficient.
3. Require exact, up-to-date backend authorization, including active appointment/issuer scope, separation-of-duties checks, no self-approval, current NGO/case revision, and absence of any disqualifying account recovery, dispute, hold, suspension, expiry or revocation state. A proof never overrides insufficient permissions.
4. Reject stale or replayed intent proofs, TOTP reuse outside the accepted anti-replay window, switched identity/NGO context, mismatched command, expired approval and authorization changes during a pending action. No optimistic UI success, unsafe blind retries or fallback to personal recovery.
5. **Recovery codes, password-reset links, newly enrolled or replacement factors, personal account recovery status and emergency support workflows are not substitutes** for operation-specific password-plus-TOTP approval. Held or review-required personal identities cannot perform protected actions; a separately approved recovery/re-provisioning pathway is needed.
6. Apply these requirements at least to initial/renewed/revoked platform operator and reviewer authority, independent NGO onboarding approval, sensitive nominee invitation issuance/revocation and administrator/grant transitions, as permitted by subsequently approved exact command contracts. Ordinary read-only or personal account features keep their existing approved contracts unless explicitly changed.
7. Do not collect or preserve plaintext passwords, TOTP seeds or OTP values in general audit logs, analytics, browser persistence or user-visible receipts. Only appropriately minimized and signed/sealed outcome evidence may be retained under an approved security/privacy design.
8. Server enforcement is authoritative in Django. React and Flutter use the approved PWC Design System v1.0 to present clear operation summaries, factor prompts, errors and status, without client-computed authorization.

## Still-open technical and independent review decisions

This is the *product owner's assurance preference*, not an implementation-ready cryptographic protocol. The designated security/auth, database, platform operations, NGO-governance and relevant privacy/legal reviewers must separately approve:

- **Exact protected command list and issuer → action → target authorization matrix**, including which operations require dual independent human approval.
- Canonical intent serialization and target/revision binding, proof identifier and nonce policy, server-generated challenge design, TTL, storage and replay prevention, password/TOTP verification order, and one-time consumption semantics.
- Factor continuity, recent enrollment/rotation restrictions, recovery and compromise handling; **GM06's unresolved choice** between factor-removal prohibition and protected-action unavailability must be decided explicitly, not bypassed.
- Atomic grant/decision mutation, transaction lock ordering, DB writer/EXECUTE restrictions, idempotent retries and immutable audit/notice/receipt treatment, including known/unknown mutation results.
- TOTP time skew, anti-replay within accepted steps, rate limits, abuse/lockout/DoS considerations, operational review and incident containment.
- Browser/mobile challenge transport, sensitive field privacy, cookie/CSRF/origin/HTTPS/session-rotation behavior and revocation fence.
- Exact command/proof retention, retention legal basis and end-to-end adversarial/post-deployment review.

**Hard gate:** Until these contracts receive their respective independent approvals, no live platform appointment, reviewer command, nominee invitation/grant activation or protected financial/alliance authority may be enabled or treated as implemented. Existing personal account authentication and synthetic foundation remain unchanged.

## References and roadmap alignment

- [Roadmap v2.0 / reconciliation §11](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md) — keep P0–P8, PWC-03B.3/PWC-04C boundaries intact.
- [ADR-0004 NGO verification & authority](../decisions/ADR-0004-ngo-verification-and-representative-authority.md).
- [Platform officer identity and privilege separation](PWC-04C-PLATFORM-OFFICER-IDENTITY-AND-PRIVILEGE-SEPARATION-DECISION.md).
- [Manual officer provisioning](PWC-04C-MANUAL-PLATFORM-OFFICER-PROVISIONING-DECISION.md).
- [Representative invitation policy](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md).
- [NGO administrator permission matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md).
- [E review register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md), especially E10/E14.
- [GM/REAL privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md), especially GM05/GM06/GM07/GM10.

This documentation-only record is an approved **PWC-04C product decision**, not an extra roadmap subphase, new login system, or implementation/activation authorization.
