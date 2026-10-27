# PWC-04C — Platform Officer Identity and Privilege Separation Decision

**Date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product-level identity approach only; implementation/activation gated  
**Source:** Product owner explicitly approved reuse of existing PWC personal identities for Super Admin and Verification Officer, with separately issued and independently controlled platform authority.

## Approved direction

1. Initial Super Admin and Verification Officer use the **existing PWC personal identity/account system**. Do **not** establish a parallel platform-officer login database, nor treat login itself as organizational authority.
2. Each officer is linked to the **exact verified personal identity** specified in their authentic, signed **offline appointment record** issued by PWC's formally designated founding platform authority. Unverified contact ownership or a display name is insufficient to bind an appointment.
3. Platform operator/reviewer capability is a **separately issued, bounded, independently controlled grant**. Identity verification, MFA completion, PWC Board membership, Django `is_staff`/`is_superuser`, recovery status and synthetic fixture grants never confer it.
4. The initial Super Admin and independent Verification Officer are **distinct vetted humans**, not merely different account identifiers; no self-approval. Super Admin initiates controlled NGO onboarding; independent officer approves the exact revision once legitimately provisioned.
5. Platform roles do not imply access to NGO-private finances, rosters, records, cross-NGO administrative grants or PWC alliance governance. NGO representative appointment and recipient-bound invitation remain separate processes.
6. Expired, suspended, revoked or contested platform appointments immediately lose the corresponding authority; personal identity and lawful history persist separately, and personal recovery does not automatically reinstate grants.
7. All appointment, identity binding, issuance, acceptance, use, revocation and recovery operations require their own versioned, protected, minimally disclosed audit provenance and distinct authorized action pathways.

## Unresolved implementation contracts and sign-offs

This product choice **does not approve** real platform-officer provisioning or any privileged command. Before coding gated behavior, separately obtain security, platform operations, NGO governance and relevant privacy/legal authorization of:

- **Appointment root:** named founding appointing authority and authoritative signed designation, identity-proofing rubric, appointment format/evidence reference and custody, human-vetting and conflict checks.
- **Provisioning:** narrowly authorized initial provisioning tool/DB writer, independently approving confirmer, exact issuer → action → target matrix, prevention of circular bootstrap/self-grants, account linking and verified-email/identity collision handling.
- **Grant lifecycle:** scope, effective/maximum term, renewal, revocation, expiry, emergency containment, privileged recovery and audit; no automatic escalation from account flags.
- **Assurance and session control:** operation-bound canonical intent, fresh password/TOTP/MFA proof, continuity/re-enrollment/recovery restrictions including unresolved GM06, expiry, hold/dispute and anti-replay.
- **Data integrity:** transaction locks, concurrency, atomic immutable events/receipts, source provenance, restricted database writers, safe notice/outbox and negative authorization tests.
- **Activation:** provider/HTTPS/origin/CSRF configuration, security testing, operations runbook and explicit release acceptance.

Until these are independently accepted under applicable **E04/E09/E10/E11/E14/E17, GM01–GM12 and REAL01–REAL04** gates, keep real platform provisioning, controlled reviewer/approval commands, invitation issuance and NGO grant activation **unavailable**. Deny-default engineering foundations already merged must remain intact.

## Source traceability

- [Roadmap v2.0 and dated reconciliation](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md): P3/PWC-04C, PWC-03B.3 dependencies; P0–P8 unchanged.
- [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md): offline verification, distinct eligibility/nominee mandate, activation stages.
- [Founding appointment decision](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md).
- [Representative invitation decision](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md).
- [NGO administrator permission matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md).
- [Verification/E decision register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md) and [privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).

This is a documentation-only, product-owner-approved **PWC-04C decision**, not a new subphase or live authorization.
