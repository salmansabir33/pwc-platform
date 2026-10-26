# ADR-0004 — NGO verification and representative authority

**Status: PRODUCT-POLICY DIRECTION APPROVED — SECURITY / NGO-GOVERNANCE / LEGAL / PRIVACY / OPERATIONS AND IMPLEMENTATION GATES REMAIN**

Date: 26 October 2026. Package: **PWC-02E**, design and policy only.

Base inspected: `origin/main` at `beffabf697af7e1d443e68a2afa3eb16aaef41d9`, including merged PRs #3–#7. Assigned branch: `arena/4fb1b265-pwc-platform`.

Decision owners: product owner, NGO-policy representatives, security/authentication and database reviewers; privacy/legal/operations reviewers for their respective gates. These are required reviewer functions, not recorded approvals.

**Product approval date: 27 October 2026 (Asia/Karachi). Approval authority: PWC product owner, explicit “Consolidated Owner Approval of NGO Authority Policies” instruction in this conversation.** The [consolidated thirty-decision matrix](../reviews/PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md#8-consolidated-product-owner-approval--27-october-2026) records 14 concrete product selections and 16 conditional endorsements, their scope and all remaining gates. No named independent reviewer sign-off is inferred. Original 26 October design/base/branch provenance above is retained; approval-recording baseline is latest main `b6eac75426571109f76b78884d3aaa39e2272179`, including merged PR #9.

**This is partial, scoped approval, not blanket adoption of all technical proposals, legal policy or actual NGO powers. Merging this record does not authorize real NGO activation or PWC-03B.3/PWC-04 implementation. No production code, migrations, grant bundles, assurance operations or canonical OpenAPI contracts change.**

## 1. Context, precedence and executable reality

The [Strategic & Product Foundation](../product/PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md) §§1–5, 14–16 is the requirements source. Its [S]/[R]/[O]/[D] labels remain provisional/recommended/open/deferred, not ratified policy. The [Identity Foundation](../product/PWC_Identity_Authorization_and_Multi_NGO_Data_Model_Foundation_v1.0_Draft.md) §§1–4, 8–10, 15–18 and [Django/PostgreSQL Foundation](../product/PWC_Django_Backend_and_PostgreSQL_Schema_Foundation_v1.0_Draft.md) §§3–6 guide design, not policy approval.

[AGENTS.md](../../AGENTS.md) and [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md) P1–P3 require deny-first, evidence-based NGO authority and separate verification approval before P3 activation. Historical scaffold/toolchain/session-branch descriptions in AGENTS/roadmap are superseded by inspected merged implementation and the current assigned branch, not instructions to recreate existing foundations. Preserve those sources, including their historical context.

Approved decisions remain controlling within their recorded scope:

- [ADR-0001 authentication](ADR-0001-authentication-and-recovery.md): one personal identity, current online session/epoch/hold checks, operation-bound assurance, recovery does not confer business powers. The separately named [repository ADR-0001](ADR-0001-repository.md) is the historical starter decision, not the authentication approval.
- [ADR-0002](ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), especially §§3–5, 8–12: shared-schema isolation, immutable pinned bundles, provenance, terminal revocation, lock order, audit atomicity, no legacy promotion. D03/D05/D08–D10/D12–D14 retain real-authority/operational gates.
- [ADR-0003](ADR-0003-web-frontend-architecture.md): independent React NGO and OPS surfaces; backend authority; no Board/portal/route shortcut; W1 is not real-workspace activation.
- [PWC-03B.3 register](../reviews/PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md): GM01–GM12 and REAL01–REAL04 remain unresolved where not explicitly accepted by human reviewers. The 27 October record adopts concrete product direction only; remaining command/security/REAL contracts are not closed.

| Inspected implementation                                                                                               | Constraint for subsequent development                                                                                                                                                                                         |
| ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `organizations/models.py`                                                                                              | Organization UUID; name/city/classification. Workspace is one-to-one with BigAutoField PK and provisional/pending/verified/restricted/deactivated states. Preserve IDs/history; classification is not proof.                  |
| `OrganizationAccess`                                                                                                   | Legacy claimant/admin/member-manager labels lack verified provenance. Do not promote these rows.                                                                                                                              |
| `organizations/views.py`                                                                                               | Public list/detail expose only id/name/city/classification for workspace state `verified`. No consent workflow exists; this proposal must not widen that serializer or pretend a new publication gate is already enforced.    |
| `access/models.py`, registry, services, DB guards                                                                      | Only attested synthetic principals/tenants; `NGOKernelState.mode` disabled/synthetic; immutable `ngo_kernel_v1` read bundles, 24-hour grant ceiling, fixture-only source/process. Runtime cannot become a human grant writer. |
| `accounts/mfa.py` and auth services                                                                                    | Registered assurance operations are personal-only. NGO/platform intents require a separately approved extension and lock-compatible integration. MFA proves a factor, not an appointment.                                     |
| [PWC-03C contracts](../runbooks/PWC-03C-SHARED-API-CONTRACTS.md)                                                       | Canonical OpenAPI 3.1 describes current 32 paths/47 operations/39 schemas, not proposed onboarding. Existing context discovery is synthetic, not real affiliations.                                                           |
| [Flutter foundation](../runbooks/PWC-03D-FLUTTER-MOBILE-FOUNDATION.md), [W1 web](../runbooks/PWC-W1-WEB-FOUNDATION.md) | Personal foundation and tenant cache fences exist; NGO onboarding/OPS business tools are not enabled. Networking/device/live-integration gates remain.                                                                        |

## 2. Product-policy decision and gated design: independent trust planes

The product owner adopts the following independent trust-plane direction on **27 October 2026**, within the per-ID limits of the [decision register §8](../reviews/PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md#8-consolidated-product-owner-approval--27-october-2026). Its technical, evidence, governance, assurance, legal/privacy and operational details still require their recorded independent approvals before affected implementation/activation:

1. **Organizational identity** is the persistent institutional subject, not property owned by a login. A creator is an applicant, never the automatic owner of existing NGO data.
2. **Platform eligibility verification** establishes the NGO/group's suitability for the software under a versioned rubric. It is neither government registration nor a legal/fundraising certification.
3. **Representative mandate verification** establishes a named person's evidenced appointment, scope and validity from the organization's legitimate governance. A mandate is not itself a technical grant or a bank/legal signatory certificate.
4. **Workspace grants** authorize exact NGO-scoped actions from an approved mandate/appointment, bounded by pinned bundle/version, expiry and current lifecycle. General administration excludes finance, financial signatory, legal commitments and alliance powers.
5. **PWC institutional membership and representatives** are separate alliance relationships. NGOs may use eligible software without joining the alliance; leaving the alliance does not erase their workspace.
6. **Publication** is a separate approved, field-level disclosure decision. No provisional verified badge; no publication of evidence, ordinary rosters or personal contacts by default.

No relationship implies another: personal account owner; organizational contact; founder/creator claimant; verified legal/designated representative; appointed administrator; member; volunteer; finance operator; financial signatory; alliance representative; Board/committee member; verification officer. One person may hold several, each established independently in its own context. Holding one never supplies another relationship's missing evidence or permissions.

## 3. Product-approved direction and still-gated verification design

Use separate, revisioned state machines for organization verification, case adjudication, mandate, appointment, grant, workspace restriction and publication. Do not encode them in one `verified` boolean. Full transitions and all twelve workflows are specified in the [workflow architecture](../architecture/PWC-02E-NGO-VERIFICATION-AND-AUTHORITY-WORKFLOWS.md).

### 3.1 Registered and informal tracks

- Registered: collect claimed registration issuer, number and jurisdiction; independently corroborate authoritative registry/document provenance and current organizational decision appointing the representative. A certificate alone does not prove current control.
- Informal: do not invent a registration number/legal name. Establish declared group identity, credible welfare activity and governance/appointment evidence with independent corroboration under an approved rubric. Do not require fabricated government recognition. Eligibility and capability exclusions need product/legal approval.
- Names, logos, emails, phones, domains, uploaded stationery and social accounts are signals, not authority. No national identity number is a login, public key or routine deduplication index.
- Use conservative candidate matching and manual adjudication; no unique organization-name assumption, first-claim-wins allocation or automatic merge. Preserve branches/shared registration arrangements for human review.

### 3.2 Noncircular initial authority

A claimant submits a case without an NGO grant and can see only their own application. Independent, separately authorized verification officers validate organization eligibility and the NGO's own appointment decision; they do not appoint leadership at their discretion. Recommend distinct assessor and approving reviewer, neither applicant/beneficiary nor conflicted. Both approvals bind the same evidence, policy, person, scope and revisions.

A proposed single-use activation authorization binds the verified mandate, exact recipient User, NGO, initial nonfinance bundle/version, validity and expected authority revision. Recipient acceptance and approved assurance are required. Final activation atomically rechecks all prerequisites, consumes that authorization, writes the initial grant/provenance and audit, and changes workspace eligibility. It cannot return private data before success. No existing NGO admin is needed, avoiding circular bootstrap.

Reviewer authority is a **separate platform case-review permission**, provisioned through independently approved operational IAM with appointment provenance, expiry and audit; not `is_staff`, Board status, a synthetic fixture or an NGO grant. Its own root provisioning and command assurance remain approval blockers. There is no hidden super-admin fallback if qualified reviewers are unavailable.

### 3.3 Continuing authority and recovery

- Multiple representatives hold independent, scoped mandates. Organization policy defines which eligible humans must approve each appointment. Two accounts held by one human do not satisfy a distinct-human quorum.
- Recommend all initial real appointments be independently evidenced, nonfinance and nondelegable. Root representative changes require reviewed new mandate evidence; an administrator cannot manufacture a root mandate.
- Ordinary admin invitations require explicit appointment power and an approved organizational decision. Invite acceptance authenticates the recipient but is not the authority source. Bind single-use hashed tokens to exact recipient, NGO, mandate, bundle and expiry; do not invite/grant by loose contact matching.
- A nondelegated appointment depends on its verified mandate, not the issuer's continuing employment. Issuer authority is checked at issuance and retained in provenance; compromise triggers review of their appointments. Replacing/revoking a mandate terminates its dependent authority, not unrelated independently valid mandates.
- Temporary delegation is designed but **disabled in the initial recommendation**. A later approved one-hop subset must remain dependent on a live parent, no longer lived/broader than that parent, never confer grant-management/finance/signatory powers, and never create cycles or self-escalation.
- Last-admin convenience cannot preserve compromised access. Planned voluntary departure requires a verified replacement accepted first; compromise revocation proceeds even if it leaves zero admins. Recovery returns to independent mandate review, not personal-account recovery or Board selection.
- Credible contested authority freezes affected powers and dependent grants, with organization-wide restriction if scope cannot be safely isolated. Mere submission of an adverse claim does not automatically freeze an NGO. Independent triage, conflict rules and appeal authority must be approved.
- Neither clearing a personal recovery hold, installing MFA, resetting a password nor using a recovery code creates, renews or resurrects a mandate/grant. Eligible authenticated access still needs current domain authority.

## 4. Evidence, privacy and exceptional operations

Recommend case-scoped, purpose-limited access to minimal evidence, encrypted private object storage and backups, quarantine/scanning before review, private download authorization on every request, and no public/CDN/persistent signed download links. Reviewers see assigned case evidence, not tenant rosters/books. NGO admins do not automatically see another applicant's identity evidence; opposing submissions are segregated and reasons redacted for appeal.

Define approved retention schedules by class: incomplete uploads, adjudicated raw documents, decision/provenance extracts, authority/audit history, holds and backups. **No retention duration or Pakistani statutory requirement is asserted here.** Raw evidence deletion can preserve a minimized attestation/provenance record where approved; an expired/missing required attestation blocks renewal or authority rather than fabricating evidence. Legal/privacy owners must accept the schedule, notice, legal basis and deletion/hold rules before real intake.

Safety/legal exceptions remain **separately gated proposals under ADR-0002 D08**: a narrowly authorized responder may restrict service without reading NGO-private content; lawful disclosure/support would require distinct purpose/scope/approver/expiry/audit and legal validation. No universal browse/export permission, Board override, automatic support grant or hidden override endpoint is proposed. Infrastructure/DB-owner power remains an operational trust risk, not a business entitlement.

## 5. Technical integration and consequences

Retain Django/DRF/PostgreSQL shared schema and current identity/migration history. Proposed additive models, composite ownership constraints, approved narrow DB writers, transaction protocol, command contracts, UI states and negative tests are in workflow §§7–11. Every proposed endpoint is explicitly **NOT IMPLEMENTED**. Preserve frozen source/process/bundle restrictions; do not change `synthetic` to mean real or reuse personal assurance as domain authorization.

Benefits: noncircular onboarding, independent NGO control, auditable provenance, explicit recovery, bounded reviewer access, scalable indexed case queues and no finance/Board shortcuts. Costs: human verification capacity, privacy operations, issuer/approval IAM, serializing locks and independent review of contested evidence. An unavailable approver is an availability problem, not permission to weaken the quorum.

Alternatives rejected as recommendations: creator/contact possession as ownership; staff/Board override; legal registration equals administrator; PWC membership equals software eligibility; one universal `verified` flag; automatic legacy-grant promotion; irreversible first-claim ownership; automatic data merge; permanent unbounded grants; fixed invented legal document/retention rules.

## 6. Approval and implementation gates

The [decision register](../reviews/PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md) separates approved invariants from recommendations and records exact approvals, alternatives, consequences and blockers. It cross-maps GM01–GM12/REAL01–REAL04 and PWC-04A–D. No entry is self-approved here.

Readiness: product-policy direction recorded; remaining security/legal/NGO-governance/privacy/operations review and bounded implementation contracts are still required. PWC-04 policy-dependent transitions, PWC-03B.3 privileged commands and all real activation remain blocked until their applicable approvals and tests are accepted. Storage/retention/legal/operations gates block real evidence and release; finance/signatory/support/collaboration remain separately gated domains. Deferred elections, national chapters and production business modules are outside PWC-02E.

### 6.1 Reconciliation of scoped approval

Concrete product choices include registered/informal eligibility tracks, private segregated claims/no initial operational merge, independent mandate review and recipient acceptance, the existing E05 product upper bounds, separate consent/badges, safe appointment/last-admin/recovery policy, initial delegation exclusion and separation of finance/alliance powers. They are **not merely unselected proposals any longer**, but their joint-review gates remain. No operational parameter, quorum or evidence standard absent from the original recommendation is supplied.

In particular: E03's documented two platform reviewers is not an NGO/signatory quorum; E05's real upper bounds do not alter synthetic 24-hour grants or existing auth proof deadlines; E15 remains disabled initially despite owner endorsement of later bounded delegation; GM01's exact command list and GM06's MFA-retention fork remain incomplete. E13's restrict-only responder direction is conditional under ADR-0002 D08, not a new support/browse/appointment permission. Independent mandate-backed appointment and live-parent delegation require an exact source/cascade contract, not a weaker authority path. Revocation retains ADR-0002's committed-transition semantics and no grace, not a promise to recall delivered bytes or acknowledge a failed write.

The original workflow specification and technical recommendations remain a gated blueprint. The consolidated matrix, original E/GM rows and their alternatives/acceptance requirements jointly define the effective record. No product-owner endorsement substitutes for legal authority, NGO governance, security assurance or operational deployment approval.
