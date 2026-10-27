# PWC-04C — Governance and Independent Reviewer Role Arrangements

**Decision date:** 27 October 2026 (Asia/Karachi)  
**Status:** PRODUCT-OWNER CONFIRMED ROLE ARRANGEMENTS — INDIVIDUAL APPOINTMENTS AND INDEPENDENT SIGN-OFFS PENDING  
**Roadmap:** PWC-04C; dependencies under PWC-03B.3 and the E/GM/REAL registers. No new phase.

## 1. Confirmed role arrangements

The product owner answered six sequential governance/reviewer questions and confirmed the following **role-level arrangements**:

| Question | Function | Confirmed arrangement | Important separation |
| --- | --- | --- | --- |
| Q1 | Founding platform authority | **PWC Chairman / President** serves as the official founding appointing authority for initial platform officers. | Signed appointment evidence and legal/governance basis remain to be produced and verified. |
| Q2 | Initial platform officers | **Two different individuals** will be appointed as PWC Super Admin and Verification Officer. | Reviewer cannot approve their own onboarding submissions; independence evaluated as real persons, not only separate accounts. |
| Q3 | Initial officer permission provisioning | **A designated technical administrator**, with a **separate independent confirmer**. | Executor/confirmer/beneficiary separation and the exact bounded provisioning authority require operational/security review. |
| Q4 | Security and authentication | **A designated Cybersecurity / Information Security Specialist**. | Reviews sensitive command assurance, MFA/TOTP, recovery, GM06 factor continuity and revocation; cannot self-certify unreviewed implementation. |
| Q5 | Database and API security | **A designated Senior Backend / Database Architect**. | Reviews Django/PostgreSQL authorization, tenant isolation, privileged DB writers, provenance, transactions, OpenAPI and tests. |
| Q6 | Legal and data privacy | **A legal adviser working jointly with a data privacy specialist**. | Joint review covers evidence/reference handling, lawful processing, retention, audit readers, notices, recovery and data rights. |

These are the selected **organizational arrangements**, not verified individual identities, signed mandates, security review decisions, or deploy/activation authorizations.

## 2. Functional ownership of AUTH-01 through AUTH-09

This mapping identifies whom to invite to review, not unilateral permission to approve on another reviewer's behalf.

| Contract | Required participation under the approved package |
| --- | --- |
| AUTH-01 founding chain | Chairman/President as founding governance authority; technical administrator; independent confirmer; security specialist; legal/privacy where evidence custody applies. |
| AUTH-02 exact privileged charter and issuer matrix | Founding governance authority, appointed operations representatives, security specialist and Senior Backend/Database Architect/API owner. |
| AUTH-03 v1 nonfinance permissions | Product owner, founding/NGO governance delegate, security specialist and backend/API reviewer. |
| AUTH-04 password+TOTP, GM06 and account recovery | Cybersecurity/Information Security Specialist as primary independent security reviewer, with operations and privacy input. |
| AUTH-05 provenance, writers, transactions | Senior Backend/Database Architect as primary technical reviewer, plus cybersecurity specialist and technical operations. |
| AUTH-06 invitation, nominee consent and activation | NGO governance, security, API, technical operations and legal/privacy representatives. |
| AUTH-07 expiry, revocation and succession | NGO governance, security, database/API and technical operations. |
| AUTH-08 evidence custody, notices and audit privacy | Legal adviser **and** data privacy specialist as joint reviewers, with governance, security and operations input. |
| AUTH-09 deployment and activation | Technical administrator/operations function, security, privacy/legal and product owner; separate independent release acceptance. |

The Super Admin and Verification Officer are **operational beneficiaries/actors**, not automatic independent security reviewers. The Chairman/President's founding appointment authority does not bypass independent technical checks or independently approve the Chairman/President's own beneficial grant.

## 3. Formal appointment and sign-off record — required next

For **each actual human** assigned, independently record in an access-controlled appointment dossier (do not publish private contact/identity evidence in the open repository):

- Full name or approved nonpublic identifier; role and represented organization.
- Appointing authority and verified source instrument/reference; appointment start/end and scope.
- Actual-person independence and conflicts of interest, including beneficial owner, operator, reviewer, confirmer, nominee or technical implementer overlaps.
- Qualifications/scope for security, database/API and legal/privacy review.
- Revocation and replacement path and approval date.
- Approval of a specific immutable technical contract version, environment and allowed commands, supported by test/evidence and explicit remaining exclusions.

**No individual names or signatures have yet been supplied. No appointment is claimed complete.**

## 4. Mandatory operational controls

1. The Chairman/President must separately issue authentic initial officer appointments; product-owner text is not the signed instrument itself.
2. The two platform officers must be **different verified natural persons** with personal accounts and separately authorized, bounded platform grants.
3. The designated technical administrator may execute only an approved restricted command on verified signed source; the independent confirmer must not be the same person as executor or beneficiary.
4. Security and database/API reviews must explicitly accept applicable AUTH, E, GM and REAL implementation contracts. A passing test suite or a merged documentation PR is insufficient.
5. The legal adviser and privacy specialist jointly assess applicable AUTH-08 and privacy-dependent subcontracts; do not invent a statutory retention period or rely on public GitHub for private verification papers.
6. Privileged actions remain deny-default; real officer provisioning, reviewer decisions, invitation issuance, grant activation, NGO-private audit reads and production release must not be enabled until their precise independent acceptance gates close.

## 5. Outstanding coordination questions (not silently decided)

- Actual identity and legally grounded designation of the PWC Chairman/President; authorization evidence and contingency succession.
- Names/identifiers and individual appointment records of both initial platform officers.
- Technical administrator and independent confirmer identities; assignment overlap restrictions.
- Named security specialist and backend/database architect, experience and organizational independence.
- Named legal adviser and privacy specialist; division of responsibilities and joint signature protocol.
- Actual sign-off dates, contract versions, accepted conditions, review test evidence and **AUTH-01 through AUTH-09 decisions**, all currently **PENDING**.

## 6. References

- [PWC-04C Implementation Authorization Package](PWC-04C-IMPLEMENTATION-AUTHORIZATION-PACKAGE-v1.0.md).
- [PWC-04C Implementation Readiness Review](PWC-04C-IMPLEMENTATION-READINESS-REVIEW.md).
- [PWC-04C consolidated security contract](PWC-04C-CONSOLIDATED-AUTHORIZATION-SECURITY-CONTRACT-v1.0.md).
- [PWC-04C manual officer provisioning](PWC-04C-MANUAL-PLATFORM-OFFICER-PROVISIONING-DECISION.md).
- [PWC-04C officer identity separation](PWC-04C-PLATFORM-OFFICER-IDENTITY-AND-PRIVILEGE-SEPARATION-DECISION.md).
- [E verification authority register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md).
- [GM/REAL privileged grant register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).

**Implementation verdict unchanged:** No complete real PWC-04C privileged implementation until the affected I contracts are individually accepted by the authorized, independent reviewers; A/U/R gates still govern activation, intake and release.
