# PWC-04C — Representative Invitation and Activation (Product Decision)

**Decision date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product policy only; security, NGO-governance, privacy, IAM and implementation gates remain open  
**Scope:** First-rollout offline NGO onboarding, nominated representative invitation and initial **nonfinance** NGO authority  
**Source:** Product owner explicitly approved the six-step invitation and activation recommendation on 27 October 2026.

## Approved product workflow

1. **Prerequisites:** The NGO has been verified externally, its authoritative representative nomination recorded, and the exact onboarding record revision independently approved by a Verification Officer distinct from the initiating Super Admin. These events remain separate.
2. **Invitation initiation:** An appropriately authorized PWC Super Admin initiates a **single-use, recipient-bound** invitation addressed to the exact nominee in the approved nomination record; the Super Admin does not create the nominee's password, enroll their MFA or accept on their behalf.
3. **Delivery and validity:** Deliver only to the nominee's **verified email address**, using the separately approved delivery and anti-enumeration contract. Product validity is **72 hours maximum from issuance**, without renewal grace, and is also capped by the nomination/organization/approval validity. Expired or revoked invitations cannot be activated; fresh authorization is required to replace them.
4. **Personal identity:** The nominee signs in or creates a personal identity, verifies their email, and completes the required authentication/assurance. Email control alone does not establish NGO mandate or suffice as the complete operation-bound assurance contract.
5. **Explicit informed acceptance:** Before accepting, the nominee sees the exact NGO identity, proposed nonfinance administrative role, scope, validity and material restrictions and explicitly accepts that exact authorized version. The system must reject a recipient mismatch, stale revision, revoked mandate, expired approval/invite, assurance failure, or unknown recipient.
6. **Authority boundary:** Only **after** valid acceptance and an independently approved grant-issuance command may the precisely scoped **nonfinance** NGO administrator authority become effective. Acceptance must not automatically create finance, signatory, PWC alliance, Board, collaboration or cross-NGO powers.
7. **Representative changes:** Changing, replacing, suspending or recovering an NGO representative requires fresh governance-valid NGO nomination, external verification where necessary, independent platform approval and a fresh recipient-specific activation. No old nominee, Super Admin or current NGO administrator may silently transfer the appointment.

## Invariants and safe failures

- Personal account registration, personal email verification, MFA and personal recovery never themselves create NGO authority.
- No applicant self-registration/claim path is reopened; onboarding starts from approved PWC-operated offline verification.
- Prohibit replays, duplicate activation, blind retry, race with approval/nomination revocation and cross-organization acceptance. Require atomic authorization revalidation, revision-bound intent, immutable audit/receipt and idempotent recovery for unknown outcomes under an **approved** command contract.
- Never publish private nomination evidence or send secrets in public status, URLs, logs or unapproved notification channels. No upload of raw verification evidence is implied.
- A previously authenticated user may represent multiple NGOs, but each NGO mandate and technical grant is independently reviewed and explicitly accepted; no ambient first-NGO selection.
- User-visible statuses must distinguish pending, expired, revoked, declined, accepted-but-not-yet-authorized, activated and unavailable; avoid fabricated success.

## Outstanding implementation and activation blockers

This approval resolves the **product** direction and 72-hour invitation maximum; it does **not** authorize implementation of real invitation issuance/acceptance or grant activation until affected technical/security and NGO-policy contracts are approved. In particular, record and obtain independent acceptance for:

- The specific approved NGO-nomination evidence rubric and assurance of recipient identity, including email change/reuse, unverified contact and preexisting account collisions.
- Exact invitation state machine, token length/entropy, storage/hashing, expiry computation, delivery provider, suppression, safe regeneration/reissue, resend/revoke, and ownership of failed or bounced delivery.
- Exact operator → invitation → nominee issuer/action/target permission matrix; distinct-human approval/provisioning requirements, conflicts, expiry, suspension and recovery.
- Operation-bound intent, fresh factor and step-up requirements (including the unresolved GM06 recovery-factor boundary); replay prevention, hold restrictions and proof retention.
- Atomic DB writer/constraints/locks, idempotency receipts, audit and redacted notice policy; secure cross-portal URLs and HTTPS/origin/cookie/CSRF deployment requirements.
- Exact **initial nonfinance administrative bundle** (permission set, 90-day upper-bound rules subject to fresh approval, and NGO-governance expiry), grant provenance, cascade and revocation semantics under PWC-03B.3/GM commands.

Until accepted by the accountable security, operations, NGO-governance and relevant privacy/legal reviewers, **keep real reviewer/controlled commands, invitation token generation/delivery, acceptance and NGO authority grants unavailable**. Documentation/test-only or otherwise explicitly permitted deny-default engineering preparation remains separate from activation.

## Traceability

Read together with:

- [ADR-0004 — NGO verification and representative authority](../decisions/ADR-0004-ngo-verification-and-representative-authority.md), especially §7 and §7.1.
- [Initial platform appointment authority decision](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md), merged in PR #16.
- [E01–E18 verification authority register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md), especially E03/E04/E05/E09/E10/E12/E14/E17 and the revised offline disposition.
- [GM01–GM12 and REAL01–REAL04 privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).
- [PWC Design System v1.0](../design/PWC_DESIGN_SYSTEM_v1.0.md), governing React/Flutter implementation.

**Roadmap:** Preserve P0–P8 and lettered subphases. This record belongs to the PWC-04C product decision process and is **not** a new user-facing subphase or authorization to start gated commands.
