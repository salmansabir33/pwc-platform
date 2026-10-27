# PWC-04C — Initial NGO Administrator Permission Matrix

**Decision date:** 27 October 2026 (Asia/Karachi)  
**Status:** APPROVED — product scope; detailed capability IDs, issuer matrix, assurance and real grant activation remain implementation-gated  
**Source:** Explicit product-owner agreement to the PWC-04C Primary NGO Administrator / NGO Administrator proposal, including independently approved additional administrator appointments.

## 1. Role model

- **Primary NGO Administrator:** Officially nominated representative who, after external NGO/mandate verification, independent platform approval, recipient-bound invitation acceptance and an approved nonfinance grant operation, may manage the NGO's authorized nonfinance workspace. This designation does **not** confer finance, legal signatory, PWC alliance, other-NGO or platform-operator power.
- **NGO Administrator:** Scoped operator whose concrete permissions are assigned explicitly for one NGO; a generic administrator designation is not unrestricted workspace authority. An administrator may be limited to membership, volunteer, events, project or reporting operations. All actual privileges are based on current bounded grants checked server-side.
- **Primary is not a self-issuing root:** No self-promotion, self-approval, unsupervised replacement or automatic grant on NGO creation, Django staff status or contact possession. Multiple organizations remain isolated.

## 2. Product-level permission matrix

Legend: **Base** = authorized after precise nonfinance role activation and current tenant/source validity; **Scoped** = requires a separately assigned applicable functional capability and feature API; **Request** = can initiate but not decide an independently controlled authority change; **Excluded** = cannot be derived from these roles.

| Capability | Primary NGO Administrator | NGO Administrator | Boundary |
| --- | --- | --- | --- |
| NGO dashboard | Base | Base | Authenticated tenant-scoped data only, where API exists. |
| NGO profile and non-sensitive settings | Base | Scoped edit | Public publishing and sensitive governance fields require their own approval/consent policy. |
| Membership, categories and admissions | Base once module approved | Scoped | Member privacy, imports, claims and payments keep their independent controls. |
| Volunteers and assignments | Base once module approved | Scoped | Sensitive placement safeguarding applies. |
| Events and activities | Base once module approved | Scoped | Respect private/public visibility and attendance access. |
| Independent NGO projects/tasks | Base once module approved | Scoped | No implication of finance posting or inter-NGO commitments. |
| Nonfinance operational reports | Base once module approved | Scoped | Exports require exact explicit permission/privacy review. |
| Invite ordinary nonprivileged NGO users | Base when approved invitation contract exists | Scoped delegation only if expressly approved | Invite acceptance alone never creates higher authority. |
| Propose another NGO Administrator / removal | **Request only** | Excluded | Independent approved process; beneficiary cannot count as own approver. |
| Approve own admin appointment or promotion | Excluded | Excluded | No self-escalation, auto-approval or circular root. |
| Transfer/replace Primary NGO Administrator | Independently evidenced request only | Excluded | Fresh official nomination, independent verification and recipient-specific activation; no unilateral transfer. |
| NGO finances, dues posting, private financial exports | Excluded by admin status | Excluded by admin status | Finance-specific grant and approval policy (P6) separate. |
| Binding signatures/legal commitments | Excluded | Excluded | Separate documented signatory/NGO governance authority. |
| PWC alliance voting, institutional governance | Excluded | Excluded | Separate PWC institutional membership and governance domain. |
| NGO-private data of another organization | Excluded | Excluded | Explicit tenant isolation; membership in multiple NGOs requires separate grants. |
| Platform Super Admin/verification privileges | Excluded | Excluded | Platform appointment via separately reviewed offline process. |

**Clarification:** “Base” describes intended *role scope*, not an implemented blanket privilege: no UI/API may enable that action without its actual separately approved capability, operating module, current verified NGO and technical grant. Primary status alone does not override privacy, special-function or confirmation requirements.

## 3. Appointments and separation of duties

1. The initial Primary is the NGO's explicitly nominated individual, not a person chosen unilaterally by a platform operator. The platform Super Admin records and submits the offline verified mandate; independent Verification Officer approves the exact revision; nominee accepts a single-use, bound, maximum-72-hour invitation; privileged grant issuance follows its separately approved contract.
2. A Primary can **request** an additional Administrator with specified NGO, nominee, permissions, justification and expiry. The requester and beneficiary must not be their own final approver; independent approval is mandatory under an exact NGO-governance/issuer → command → target matrix still to be signed off.
3. NGO Administrators may invite ordinary nonprivileged users only if explicitly delegated that exact invitation capability. They cannot issue, approve, transfer, recover or revoke privileged NGO Administrator authority by default.
4. Current validity, revocation, suspension and context change must immediately deny affected capabilities, including deep links and stale open browser/mobile sessions. UI restrictions are conveniences; Django tenant-scoped checks are definitive.
5. Planned Primary departure requires independently confirmed successor acceptance before old role surrender where feasible; compromise containment/revocation must still be possible even if no replacement exists. Hold/recovery does not confer authority.
6. Do not interpret two *platform* reviewer identities as the NGO's constitutional signatory or quorum rule. NGO appointment legitimacy still depends on verified NGO governance and the accepted authority matrix.

## 4. Outstanding contracts and implementation boundaries

Before PWC-04C real administration is enabled, accountable security, NGO-governance, operations and relevant privacy/legal owners must approve exact backend capability codes, bounded role/bundle contents, appointment and revocation issuer matrices, human independence/conflicts, step-up/operation intent, source/expiry, protected DB writers, atomic retries/audit, notifications, dispute/recovery and representative invitation/grant contracts. Relevant E04/E09/E10/E11/E12/E14/E17 and GM01–GM12/REAL01–04 gates remain in force. No finance/signatory, alliance membership or privileged support is enabled.

A module's roadmap implementation can add its **feature-specific** capability later without retroactively expanding existing issued authority. No implied universal future grant; newly added sensitive capabilities require explicit policy/version and authorized issue/acceptance.

**Implementation readiness:** product policy accepted; exact implementation-bound privileged command contracts not automatically accepted. Until independently signed off, maintain deny-default adapters and no real admin appointment/grant issuance.

## 5. Traceability and documentation requirements

- [Roadmap v2.0 (including §11 execution reconciliation)](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md): P3/PWC-04C, later P4–P7 actual feature capabilities. Preserve P0–P8 and lettered subphases.
- [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md): NGO legitimacy, nominee mandate and offline controlled onboarding are separate.
- [Initial platform appointment](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md) and [recipient-bound invitation policy](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md) are prerequisites, not authority-issuing software.
- [Verification/E decision register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md) and [privileged/GM register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md) retain unresolved gates.
- [PWC Design System v1.0](../design/PWC_DESIGN_SYSTEM_v1.0.md) is the frontend visual standard.

This is a product decision record, **not a new roadmap subphase**. In the eventual PWC-04C implementation PR, amend the existing roadmap's dated reconciliation/status and corresponding ADR/register rows to reflect each separately approved/implemented command. Never describe a disabled UI/specimen as live administration.
