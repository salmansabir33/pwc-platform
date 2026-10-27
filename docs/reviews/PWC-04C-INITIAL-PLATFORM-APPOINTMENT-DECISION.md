# PWC-04C — Initial Platform Appointment Authority (Product Decision)

**Date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product governance direction only; technical/security/operations implementation gates remain open  
**Scope:** Initial rollout of offline NGO verification and controlled onboarding; dependency for PWC-04B / PWC-04C and PWC-03B.3  
**Decision source:** Explicit product-owner approval in the project discussion on 27 October 2026.

## Adopted product decision

1. **Founding appointing authority:** PWC's **formally designated founding platform authority** is responsible for issuing the initial, signed, **offline appointment records** for both (a) the first PWC Super Admin and (b) the first independent PWC Verification Officer. The appointing authority must itself be named and empowered in an authentic, approved governance record. This approval does **not** assert that such a specific record or person has already been established.
2. **Separate appointments:** The Super Admin and Verification Officer must be two distinct, independently vetted natural persons with separate written appointments, explicitly bounded duties, authority scope, validity and revocation process. Appointment alone is **not** account creation or privilege activation.
3. **Separation of duties:** The nominated Super Admin may initiate controlled NGO onboarding **only after** securely provisioned authority; a separately authorized Verification Officer must independently approve the exact submitted onboarding revision. Neither may approve their own submission, nominate themselves for NGO control through the platform, or bypass the NGO's signed representative nomination.
4. **Later changes:** Subsequent appointments, replacements, suspensions, revocations and recovery require a documented, independently reviewed, two-person-controlled authorization procedure. Emergency compromise restriction must not depend on preserving a compromised last administrator; exceptional privileges require separately approved containment rules.
5. **No automatic NGO access:** Neither founding authority, Board role, platform Super Admin role, reviewer role, Django `is_staff`/`is_superuser`, personal MFA, account recovery nor any synthetic grant creates universal NGO-private access or real permissions.
6. **Separate mandate/activation:** Offline organizational eligibility verification, NGO nomination, attestation approval, recipient-bound invitation acceptance and eventual nonfinance NGO grant activation remain distinct approvals and events. Finance, signatory, PWC alliance, collaboration and support authority are excluded.

## Required implementation contracts and unresolved approvals

This product decision settles **who is responsible for issuing the initial offline appointment letters at a governance level**. It does **not** close E04/GM/REAL implementation and release gates. Before any real operator/reviewer power is provisioned, separately document and obtain authorized security, platform-operations, NGO-governance and relevant privacy/legal review for:

- Identity and documentary provenance of the specific founding appointing authority; signed designation record; evidence authenticity and archival control.
- Initial platform IAM bootstrap performed by a specifically authorized provisioning mechanism/operator (not a general Django flag or fixture); separation of appointment issuer, provisioner and independent confirmer; recovery of the bootstrap root.
- Exact issuer → action → target matrix for initial, subsequent, expired, suspended and recovered appointments, with dual control, conflicts and distinct-human validation.
- Scope, expiry, renewal, suspension and immediate revocation of operator and reviewer powers, plus audit/nonrepudiation and incident escalation.
- Operation-bound assurance, credential enrollment and continuity, restricted DB writers, atomic transitions, version checks, receipts and immutable audit/outbox records.
- Notice, privacy, retention and external custody of signed offline appointment/evidence records; no real evidence upload implied.
- Recipient binding, token lifetime/delivery, acceptance and grant semantics for nominated NGO representatives (later PWC-04C / PWC-03B.3 contract).

**Until those independent contracts are approved, all real controlled readers, appointment/approval commands, invitation delivery and NGO grants remain deny-default/unavailable.** No implementation or production authorization is granted by this record. Engineering scaffolding may continue only within existing explicitly permitted boundaries.

## Documentation alignment and downstream acceptance

- Read alongside [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md), especially its §7 offline-onboarding decision and §7.1 unresolved gates.
- This record specifies the product-owner disposition for **E04** in the [verification authority decision register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md); it does not replace the other E01–E18 dispositions.
- The [privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md) continues to govern GM01–GM12 and REAL01–REAL04; no full GM contract is thereby approved.
- Codex/Arena must inspect this record before PWC-04C or any real operator/reviewer integration and must explicitly report what remains implementation-blocked vs approved. Follow the adopted [PWC Design System v1.0](../design/PWC_DESIGN_SYSTEM_v1.0.md) for UI work.
- Preserve P0–P8 roadmap and PWC-04B/04C lettered subphases; this is a decision record, **not** a new roadmap subphase.
