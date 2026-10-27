# PWC-04C — Consolidated technical security and implementation readiness review

**Date:** 27 October 2026 (Asia/Karachi). **Review baseline:** `origin/main`
`015d74ee3d67e0a955da54931993851b6d4a5191`, including merged PR #23.
**Verdict: NOT READY for a complete privileged-command implementation assignment.**
Product direction is adopted; independent implementation contracts remain unsigned.
This is an engineering assessment, not independent security certification, appointment,
legal advice, authority issuance, activation permission or a new roadmap subphase.
Documentation-only delivery; existing deny-default code and all historical records retained.

## 1. Authority, inspected sources and evidence standard

Read together, without replacing the existing policy registers:

- [AGENTS](../../AGENTS.md), [roadmap §§3, 11](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), README and local/tooling setup runbooks.
- [ADR-0002](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), especially §§4.5, 5.3–5.4, 6.2, 8–12; [ADR-0003](../decisions/ADR-0003-web-frontend-architecture.md), §§4–10, WEB-02/03/05/06/08/09; [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md), §§3, 6–7.1. Authentication ADR-0001 §§7–8 also governs locks, proofs and holds.
- [E register](PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md), original §3, effective §8.2, conflicts §8.3, offline amendment §9; [GM/REAL register](PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md), §§2–5.
- [Consolidated proposed contract v1.0](PWC-04C-CONSOLIDATED-AUTHORIZATION-SECURITY-CONTRACT-v1.0.md), §§1–9. It is **proposed technical contract**, not an independently signed protocol.
- Merged product records: [founding authority](PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md) (PR16), [representative invitation](PWC-04C-REPRESENTATIVE-INVITATION-AND-ACTIVATION-DECISION.md) (PR17), [admin matrix](PWC-04C-NGO-ADMINISTRATOR-PERMISSION-MATRIX.md) (PR19), [identity separation](PWC-04C-PLATFORM-OFFICER-IDENTITY-AND-PRIVILEGE-SEPARATION-DECISION.md) (PR20), [manual provisioning](PWC-04C-MANUAL-PLATFORM-OFFICER-PROVISIONING-DECISION.md) (PR21), [password/TOTP](PWC-04C-OPERATION-BOUND-PASSWORD-AND-TOTP-DECISION.md) (PR22); PR23 consolidated these. All are product-scope approvals only.
- [04A review](PWC-04A-NGO-REGISTRY-INTEGRATION-REVIEW.md), [04B review](PWC-04B-VERIFICATION-INTEGRATION-REVIEW.md), particularly its revised offline checkpoint; [Design System v1.0](../design/PWC_DESIGN_SYSTEM_v1.0.md) and its implementation review; canonical detailed screens/IA and Flutter architecture.

GitHub merge metadata was verified for PR16–23; latest main is PR23's merge.
A merge proves integration only. No named independent security, operations,
NGO-governance, database/API or privacy/legal acceptance of the missing contracts
was found in these records. Reviewer **functions** below must be assigned actual
accountable humans; a product owner cannot sign for their expertise implicitly.
Historic scaffold/branch descriptions in AGENTS and ADRs are not current reality.

### 1.1 Code evidence map (paths relative to repository root)

| Ref | Inspected implementation and actual boundary                                                                                                                                                                                                                                                                                                                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | `apps/backend/accounts/{models,security_models,sessions,session_authentication,mfa,mfa_views,registration,flow_security,delivery}.py`: personal authentication, verified contacts, current sessions/epochs, TOTP/recovery, personal intents and delivery infrastructure. No appointment source.                                                                               |
| C2  | `apps/backend/access/{models,registry,services,testing,security}.py`, migrations `0001/0002`, `db_roles.sql`: synthetic principals/tenant roots, only three read atoms, frozen reader/admin-probe v1 bundles, fixture source/process and **24-hour** grant ceiling. Runtime grant writes denied by separately provisioned role profile; fixture writer is not an HTTP issuer. |
| C3  | `apps/backend/organizations/{models,controlled_onboarding,controlled_views,controlled_urls,onboarding_policy}.py`, migrations `0007/0008`: structural record/snapshot/attestation/event models; non-writing preflight; generic requirements; controlled readers, mutations, invite and acceptance adapters always unavailable.                                                |
| C4  | `organizations/{registry,registry_views,verification,verification_views}.py`, migrations `0003–0006`: owner-scoped historical records, revisions/receipts/events, synthetic exercise seams. Default new applicant create/edit/submit denied; historical own reads/withdrawal retained. This is not current live onboarding.                                                   |
| C5  | `organizations/views.py`: four-field public projection selected by workspace `verified`, **not** field consent, mandate expiry or publication approval. Real verification must not inadvertently publish an NGO.                                                                                                                                                              |
| C6  | `organizations/controlled_contract.py`, `packages/api-contracts/{openapi-v1.json,generated/schema.ts}`, contract generators/checkers: schemas describe actual requirements/unavailable operations, not successful real officer/invite/grant DTOs. Historical success fixtures are not live acceptance.                                                                        |
| C7  | `apps/{ngo-web,pwc-ops}/src/{App,Registry,Verification,ControlledOnboarding}.tsx` as applicable; `packages/web-api/src/index.ts`, `packages/web-ui/src/*`: separated runtimes, hard-disabled W1 transport; shared tokens/components, gated feature UI and synthetic local preview. No ORG-06/25 authority workflow.                                                           |
| C8  | `apps/mobile/lib/{app,core,features,design}/`: disabled API by default; configured native HTTPS personal-only allowlist, secure credentials, session/context invalidation, personal ID screens, unavailable affiliations/workspaces and registry/verification seams. Generated DTO presence does not add domain transport.                                                    |

## 2. Executive blocker register

All findings below are **critical prerequisites for the proposed privileged feature**,
not claims of an exploitable live grant endpoint. Current unavailability is an
intentional mitigation, not a defect to remove during this review.

| ID  | Finding / consequence if bypassed                                                                                                                                                                                                 | Precise resolution before affected implementation                                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | Founding governance role is selected but no named designation, proofing, executor/confirmer trust anchor or officer writer exists (C1–3). Flags/fixtures would create forged platform power.                                      | Independently accept founding instrument, distinct vetted humans, exact offline bootstrap/renew/revoke matrix and protected provisioning mechanism (§4).                                           |
| B2  | GM01 still selects a synthetic-first command exercise, whereas PR23 lists proposed real command families. Neither is an approved executable charter.                                                                              | Sign exact environments/data/command allowlist for 03B.3 and 04C; distinguish synthetic exercise from real-domain implementation and from activation. Do not reinterpret PR23 as superseding GM01. |
| B3  | Platform/NGO action atoms, issuer/target bundles and independent NGO quorum remain unspecified. “Primary/Base” is not wildcard future authority.                                                                                  | Pin nonfinance action/bundle versions and per-command approval matrix, eligibility and revocation/source semantics (§4). Ordinary Admin has no privileged issuer power by title.                   |
| B4  | Personal assurance supports recent TOTP and personal contexts only; GM06 continuity fork unresolved. Reusing it verbatim could allow stale/new-factor substitution.                                                               | Independently accept fresh per-intent password **and newly supplied eligible TOTP**, factor continuity, failure/abuse and account-recovery rules (§5). No existing personal behavior changed here. |
| B5  | C3 account inequality/append-only snapshots do not establish legitimate actors or authorize state/event insertion. No real source, invite, acceptance, officer grant, command proof/receipt schema or restrictive writer profile. | Approve additive tenant/provenance constraints, state transition guards, least-privilege writer and complete lock graph (§6). Never relax C2 synthetic provenance/cap.                             |
| B6  | No exact immutable-recipient resolution, token delivery, acceptance, idempotent grant activation or unknown-outcome contract.                                                                                                     | Accept §4–6 command schemas, recipient/account collision rules, bounded token lifecycle, notice/outbox and receipt reconciliation.                                                                 |
| B7  | Twelve-month/90-day/72-hour/24-hour bounds have different clocks; source invalidation, approval validity and activation authorization are not fully related.                                                                      | Sign field-level clock origins/deadlines/calendar arithmetic and source cascades; distinguish invitation validity from short activation authorization (§4.3).                                      |
| B8  | External-reference taxonomy/privacy, independent-review evidence, authorized audit readers/notice obligations and publication coupling are incomplete.                                                                            | Accept minimal evidence/reference and command audit/notice contracts before schema/reader writes. Keep raw files unavailable; separate real publication from grant activation (E06/08/17).         |

**I versus A/U/R:** I blocks the affected command/schema/assurance implementation,
even in a synthetic test exercise when its contract is missing. A blocks real
powers; U blocks real evidence/personal-data intake/access; R blocks production.
Provider deployment, physical devices and production monitoring are not excuses
to postpone I decisions; conversely R-only facts do not block unrelated read-only
documentation or separately authorized deny-default preparation. F is an explicit
excluded/deferred domain, not an incomplete initial nonfinance implementation.

## 3. Complete requirement, approval and security gap matrix

Sources `E` = E register §§3/8.2/9; `G` = GM register §2 and E §8.2;
`R` = GM register §3 and ADR-0002 referenced D decisions. Row identifiers are exact
source references; product records in §1 refine, not delete, these dispositions.
**P** = concrete product direction adopted; **C** = conditional technical/cross-owner
endorsement; **NE** = independent acceptance not evidenced. NE is not a rejection
of accepted core ADR architecture. **S** security/auth; **N** NGO/founding governance;
**O** platform operations; **D** database; **API** API owner; **L** privacy/legal;
**A11y** accessibility/client acceptance. `T` references objective tests in §8.
The independent column names accountable functions, not fictitious people/signatures.

| Requirement/source                            | Product status                                                | Independent approval      | Current implementation                                                                    | Missing contract / required resolution                                                                                                       | Gate                                            | Accountable review / objective acceptance                                                                   |
| --------------------------------------------- | ------------------------------------------------------------- | ------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| E01 eligibility/evidence tracks (E)           | P; offline initial rollout adopted                            | NE N/L/S                  | C3 classification/attestation lanes; no evidentiary finding service                       | Pin registered jurisdiction rubric and informal corroboration/exclusions; reject certificate-only control                                    | I/A/U/R                                         | N/L/S; T1: missing corroboration cannot approve either lane                                                 |
| E02 matching/claims (E)                       | P; new public intake superseded                               | NE S/D/N                  | C4 normalized private matching/history; intake denied                                     | Exact issuer/jurisdiction/branch/reissued identifier namespace, duplicate controlled-record rules; no merge                                  | I/A; merge F                                    | S/D/N; T2: same-name NGOs coexist; rival claims never seize tenant                                          |
| E03 mandate/bootstrap (E; PR17)               | P; exact nominee acceptance adopted                           | NE N/S                    | C3 two lanes and unequal accounts, no real mandate                                        | Governance-form evidence, distinct natural-person/conflict check, initial bundle and activation source                                       | I/A/U/R                                         | N/S; T1/T3: one person/two accounts or beneficiary approval denied                                          |
| E04 reviewer IAM root (E; PR16/20/21)         | C; founding/manual/existing-identity direction adopted        | NE N/O/S/D                | No real platform appointment/grant service                                                | Named designation, executor/confirmer/recipient matrix and narrow writer; no staff shortcut                                                  | I/A/U/R                                         | N/O/S/D; T3: forged appointment, self-provision, expired officer denied                                     |
| E05 validity/renewal (E; PR17/23)             | P upper bounds, not operative settings                        | NE N/S                    | C2 fixture 24h only; no real expiry model                                                 | Explicit UTC origins, calendar term, effective/end, renewal approval/acceptance, min source cutoffs                                          | I/A/R                                           | N/S/D; T4: exact expiry/lock-wait and reissue boundaries, no grace                                          |
| E06 data lifecycle (E; offline revision)      | C minimum-data direction                                      | NE L/O/S                  | Immutable reference snapshots, no real retention schedule                                 | Approve field taxonomy, purpose/legal basis and mandatory provenance retention before storage; raw/backup schedules separate                 | I where schema-dependent; A/U/R                 | L/O/S; T5: forbidden personal/document values rejected, restore respects deletion/authority fences          |
| E07 evidence storage/access (E)               | C; raw uploads excluded initially                             | NE S/L/O                  | Raw upload/download service absent; C3 refuses payload processing                         | External custody/reference access contract now; provider/scan/stream/key/storage contract before any future raw evidence                     | I for reference readers; U/R; raw feature F now | S/L/O; T5: no file ingestion/URL fetch; unauthorised reference reader denied                                |
| E08 publication/consent (E)                   | P separate consent/badges                                     | NE N/L/API/S              | C5 verified-state four-field projection only                                              | Separate publication state/allowlist/consent and withdrawal before any real verified-workspace activation                                    | I for coupled transition; A/U/R                 | N/L/API/S; T6: grant/eligibility alone cannot publish or reveal nominee                                     |
| E09 appointments/revocation (E; PR19)         | P; additional-admin request + independent approval adopted    | NE N/S                    | C2 fixture revoke only, no real admin issuer                                              | Exact self-action/issuer/quorum matrix, nonfinance bundles and succession/cascade rules                                                      | I/A                                             | N/S; T3/T7: beneficiary/requester cannot finalize; compromised last-admin revoke allowed                    |
| E10 assurance/holds (E; PR22)                 | C; fresh password-plus-TOTP selected                          | NE S/auth                 | C1 personal intents/recent TOTP/hold checks                                               | Per-domain intent mapping, bootstrap factor eligibility and continuity; no generic recent-MFA proof                                          | I/A/U                                           | S/auth; T8: recent observation, recovery code or replacement factor cannot authorize command                |
| E11 provenance/writer (E)                     | C independent appointments preferred                          | NE S/D/O/N                | C2 strict fixture source; C3 immutable snapshots, mutable record shell                    | Separate real provenance/authority sources, exact mandate dependency and restricted writer/owner profile                                     | I/A/R                                           | S/D/O/N; T9: runtime direct-write and synthetic promotion fail at DB boundary                               |
| E12 disputes/appeals/recovery (E)             | P independent risk triage/fresh activation                    | NE N/L/S/O                | No adjudication/recovery command                                                          | Trigger scope, independent panel/conflicts, appeal/redacted reasons and safe recovery without old-admin prerequisite                         | I for branch; A/U/R                             | N/L/S/O; T7: report alone not freeze; upheld restriction blocks pending acceptance                          |
| E13 urgent restriction (E)                    | C restrict-only exception                                     | NE S/L/O                  | No incident authority tool                                                                | Named restrict-only responder/trigger, review deadline/notice exception and no automatic unfreeze                                            | I/A/R if included; support F                    | S/L/O; T7: restrict never grants/read-elevates; last compromised officer has no immunity                    |
| E14 atomic command contract (E)               | C                                                             | NE API/S/D                | C3 preflight only; C4 owner receipts not domain commands                                  | §6 exact schemas, proof/state/error/receipt/failure table and helper lock call graph                                                         | I/A/R                                           | API/S/D; T10/T11: one commit/event/receipt under concurrent retry; audit failure rolls back                 |
| E15 delegation (E)                            | P disabled initially                                          | NE N/S for future scope   | No parent-chain model                                                                     | Explicitly exclude now; later one-hop live-parent subset/lifetime/cascade contract                                                           | F; source distinction still I                   | N/S; T9: no delegation via admin bundle, no scope/limit splicing                                            |
| E16 finance/signatory/alliance (E)            | P excluded/separate                                           | NE finance/N/L/S          | No corresponding admin-derived authority                                                  | Retain P6/P7 distinct approval; no cross-domain grant atoms                                                                                  | F, not initial I                                | Domain owners; T12: Primary/Board/officer all denied finance/other-NGO powers                               |
| E17 audit/notices/readers (E)                 | C                                                             | NE API/O/S/L              | C1 security events; C2 authz events; C3 snapshots/events; auth delivery not domain outbox | Exact command audit/denial/readers/recipient/template/dedup/rate budgets; retention/provider/operations separately                           | I contract; A/U/R actual operation              | API/O/S/L; T5/T11/T13: no secrets, no unauthorized audit read, failure bounded/no second invitation         |
| E18 legacy/regrant (E)                        | P preserve/reverify, no promotion                             | NE N/S/D/O                | Legacy OrganizationAccess/history preserved, C2 fixture isolated                          | Inventory/classify/review explicit new grants, cutover/rollback/restore fences                                                               | I if regrant; A/R                               | N/S/D/O; T9/T14: restore cannot resurrect revoked authority or auto-promote legacy rows                     |
| GM01 exact charter (G)                        | P synthetic-first; issue/revoke preference not signed list    | NE S/API                  | No human grant-command writer                                                             | Resolve B2: signed commands, data/env exclusions and relationship to real 04C families                                                       | I; real A separately                            | S/API/product; T12: every nonlisted command denied regardless of role                                       |
| GM02 atoms/bundles/matrix (G)                 | C; PR19 scope not concrete atoms                              | NE S/API/N                | C2 only frozen read atoms                                                                 | New immutable versions and complete issuer→command→target-field/subset matrix                                                                | I                                               | S/API/N/product; T12: no wildcard, bundle drift, cross-grant scope union or future-feature auto-expansion   |
| GM03 issuer bootstrap (G)                     | P synthetic one-time, real root separate                      | NE S/O/D                  | FixtureBatch does offline synthetic writing only                                          | Exact fixture charter versus independently signed real appointment procedure; never reuse fixture evidence                                   | I; real A                                       | S/O/D/N; T3/T9: wrong batch/root/process or replay rejected                                                 |
| GM04 appointment/delegation (G)               | C                                                             | NE S/N/D                  | C2 no parents; C3 no source dependency graph                                              | Root appointment anchored to mandate versus live-parent delegation; specify revoke/compromise cascades                                       | I source; delegation F                          | S/N/D; T7/T9: ordinary issuer departure ≠ erase independent valid mandate; mandate revoked ⇒ dependent deny |
| GM05 subject eligibility (G)                  | P synthetic batch/hold bounds                                 | NE S/auth/N               | C1 hold/session checks; C2 batch checks                                                   | Explicit verified-identity/contact/factor eligibility and valid-from/end for each real recipient                                             | I; real A                                       | S/auth/N; T4/T8: unverified/held/expired-source recipient cannot accept/activate                            |
| GM06 factor continuity (G; PR22)              | C; fork **still unchosen**                                    | NE S/auth/O               | Personal removal revokes sessions, not platform duties                                    | Choose A block removal during protected duty vs B suspend protected eligibility; independent eligible reenrollment, no factor-reset loophole | I                                               | S/auth/O/product; T8: removal/replacement invalidates in-flight proofs and never grants via recovery        |
| GM07 canonical binding (G)                    | C                                                             | NE S/auth/API             | Personal command digest/intent only                                                       | Versioned server canonical fields and keyed digest with actor/session/security generations/contact/tenant/source/bundle/revisions            | I                                               | S/auth/API; T8/T10: altered target/scope/deadline/approver/contact invalidates proof                        |
| GM08 failure/idempotency (G)                  | C                                                             | NE API/S/auth             | C4 owner receipts; no privileged reconciliation                                           | Signed §6 failure table, exact key scope/retention/receipt access; semantic invalidation survives rollback as required                       | I                                               | API/S/auth; T10/T11: committed lost response reconciles once; unauthorised replay reveals nothing           |
| GM09 independence/quorum (G)                  | P no self-escalation/last-admin immunity                      | NE N/S/O                  | C3 unequal account check only                                                             | Natural-human/conflict/NGO quorum and authority continuity; two officers ≠ NGO constitutional quorum                                         | I; real A                                       | N/S/O; T3/T7: duplicate-human approval, requestor/beneficiary confirmation and implicit successor denied    |
| GM10 locks/deadlines (G)                      | C                                                             | NE S/auth/D               | Existing User-first personal/synthetic paths, no combined command                         | Complete selector/helper lock graph, all User locks up front, source/grant/domain order and final DB clock                                   | I                                               | S/auth/D; T11: deterministic independent-connection races with holds/reset/revoke/refresh/expiry            |
| GM11 durable schema/writer (G)                | C                                                             | NE S/D/O                  | Fixture guards and immutable history, no real issuer schema/profile                       | Additive schema/functions, trusted owners/search_path/EXECUTE, no runtime direct table writer and protected restore                          | I; real A/R                                     | S/D/O; T9/T14: raw SQL under runtime fails; function auth forged inputs denied                              |
| GM12 API/readers/notices (G)                  | C                                                             | NE API/S/O/L              | C6 requirements/unavailable schema and C4 redacted errors                                 | Exact command/read/status envelopes, no-store, owned receipts, cookie/CSRF vs native bearer, redacted telemetry/budgets                      | I; A/U/R                                        | API/S/O/L; T5/T10/T13: invalid transport, CSRF, enumeration and broad audit listing denied                  |
| REAL01 legitimacy/activation (R, D03)         | Product lifecycle selected, technical activation not approved | NE N/S/O/L                | No real mandate/admin activation                                                          | Accepted evidence/root/recovery/recipient/grant contracts plus actual independent evidence                                                   | I dependencies; A/U/R                           | N/S/O/L; T1/T3/T7: full nominated-recipient path; all missing source lanes fail closed                      |
| REAL02 inventory/cutover (R, D14)             | Preserve history/regrant direction adopted                    | NE N/S/D/O                | Legacy rows retained; no promotion path                                                   | Reviewed inventory outcomes, manual regrant, rollback and restore/revocation ledger                                                          | I when implementing cutover; A/R                | N/S/D/O; T14: legacy UUIDs survive and every real grant has new approved provenance                         |
| REAL03 later powers (R, D04/06/07/08)         | Explicit exclusion                                            | NE relevant domain owners | No powers from generic admin                                                              | Separate finance/signatory/alliance/support ADRs, not a 04C shortcut                                                                         | F/A for later domain                            | Domain/N/L/S; T12: no appointment can manufacture these atoms                                               |
| REAL04 real-data/operations (R, D09/10/12/13) | Safeguards endorsed, not release accepted                     | NE S/O/L/D/A11y           | Synthetic isolation/testing, default-off clients/settings                                 | Classification/consent/readers, deployment roles, monitoring/restore/load, device/HTTPS/provider evidence                                    | I for data/writer contract; A/U/R operation     | S/O/L/D/A11y; T5/T13–T15: real-role/isolation/restore/transport acceptance before pilot                     |

No whole mixed-owner row is marked closed. Later product records settle procedure
type, personal-account reuse, role boundaries, invitation ceiling and password/TOTP
direction, **not** the missing exact command contracts or named reviewer sign-offs.

## 4. Proposed authority lifecycle and exact command review package

**Everything in §§4–8 is proposed for independent review, not registered actions,
new endpoint guarantees or authorization to implement.** Reuse the existing v1
contract as policy reference; this review supplies missing engineering decisions
and testable proposals rather than a duplicate policy document.

### 4.1 State machines and issuer/action/target matrix

Separate durable sources; never one `verified` boolean or acceptance-as-grant:

| Plane / proposed states and transitions                                                                          | Actor/action/target and mandatory integrity                                                                                                                                                                                                                                                                                                                                                                |
| ---------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Founding designation: unverified → independently validated → retired/revoked                                     | Governance-authenticated signed founding instrument identifies appointing authority, exact policy/version and custodial reference. It cannot approve itself merely through a login. Reject unknown/expired/revoked instruments.                                                                                                                                                                            |
| Officer appointment: proposed → confirmed → provisioned/active → expired/suspended/revoked                       | Restricted executor proposes exact pre-existing verified User, officer action bundle, scope and term; independent named confirmer authorizes that version; narrow writer activates. Beneficiary cannot execute/confirm own grant. No public signup, Django toggle, generic owner credentials or fixture promotion. Renewal creates new authorization/version; revocation terminal.                         |
| External examination: eligibility and mandate each recorded → corroborated → expired/revoked/contested           | Authorized Super Admin records minimized, custody-controlled evidence references against exact NGO/nominee/revision; N-approved rubric determines sufficiency. Distinct signed findings; account email/contact is not mandate.                                                                                                                                                                             |
| Controlled record: draft/returned → submitted → approved/rejected/returned; draft/returned/submitted → withdrawn | Super Admin owns preparation; independent appointed Verification Officer reviews exact submitted revision with both lanes. Edits increment revision and invalidate pending approvals/intents; no editing approved snapshot. Current C3 preflight describes only this non-writing graph. Cross-row attestor/reviewer/actor legitimacy still missing.                                                        |
| Invite: authorized draft → issued/pending → accepted/declined/expired/revoked; delivery status separate          | Super Admin issues/revokes only for independently approved nomination and exact recipient; no arbitrary target. Delivery queued/sent/failed does not grant or reset expiry. Accept/decline only nominated authenticated verified User, exact NGO/role/scope/version, with required assurance; consumption terminal and atomic. Replacement token requires fresh authorization and supersedes old verifier. |
| Activation: accepted → grant_pending → activated or blocked                                                      | Protected writer alone creates exactly one bounded Primary nonfinance grant from accepted invitation + valid independent decision and mandate; acceptance records consent, not power. Failure remains pending/blocked; no automatic finance/profile publication. Activation authorization needs exact recipient/source/role/revision and deadline.                                                         |
| Additional Admin: requested → independently approved → invited → accepted → bounded grant                        | Primary **requests**, not finalizes; NGO-governance-approved independent issuer confirms exact functional subset/term. Ordinary Admin cannot appoint by title. A delegated ordinary-user invitation is not privileged appointment. No implicit permissions for modules not implemented yet.                                                                                                                |
| Revocation/succession: active → terminal revoked; successor separate fresh appointment                           | Authorized issuer/restrict-only incident actor under signed matrix fences affected grants immediately at committed transition; planned departure prefers accepted successor, but compromise may leave zero. Fresh official NGO nomination, verification, independent review and acceptance for replacement; no old-admin veto/root transfer.                                                               |
| Contested/recovery: credible risk → independently scoped restriction → reviewed resolution                       | Independent appointed triage, not any complaint or broad support user. Account recovery may restore personal login, never mandate/grant. Resolution requires current evidence and fresh authorization; no stale acceptance/proof resurrection or automatic unfreeze.                                                                                                                                       |

Matrix refinements needed: which confirmer may confirm each officer family, whether
appointment issuer/executor/confirmer must be three different humans, evidence
that nominee/reviewer accounts map to distinct people, and NGO additional-admin
quorum. Product requires independence, but **does not supply an NGO quorum number**.
Super Admin and Verification Officer have separate explicit platform bundles;
neither gets NGO member/finance reads, alliance powers or universal support.
Officers reusing personal identities must still pass appointment-specific proofing.

### 4.2 Candidate command schemas, capabilities and provenance

Command families follow PR23 §2. Recommend a closed registry, not `manage_all`:
`PLATFORM_OFFICER_BOOTSTRAP/RENEW/REVOKE`, `NGO_ONBOARD_SUBMIT/APPROVE/REJECT/RETURN`,
`NOMINEE_INVITE_ISSUE/REVOKE/ACCEPT/DECLINE`, `NGO_INITIAL_NONFINANCE_GRANT`,
`NGO_ADMIN_APPOINT/CHANGE/REVOKE`, `NGO_PRIMARY_REPLACE/RECOVER`, and scoped dispute
restriction/resolution. **Names are candidates, not approved action atoms.**
Review exclusions individually: replacement is new immutable grant + terminal
old grant, not role/expiry mutation; NGO_PRIMARY_REPLACE is not ordinary admin edit;
incident restriction is not an implicit discretionary grant or private reader.

Proposed closed input envelope (no extra/duplicate JSON keys):

```
contract_version, command_family, expected_versions,
actor_context {kind, id}, target {kind, id},
organization_id (NGO commands only), source_ids,
recipient_user_id (appointment/invite/grant commands),
bundle {code, version}, bounded_scope, effective_at, expires_at,
approval_id, nomination_revision, evidence_reference_ids,
intent_id, assurance_proof, idempotency_key
```

Per-family schema must forbid irrelevant fields, client actor/approver assertions,
client-computed digests/permissions and arbitrary role JSON. Trusted actor/session,
contact/factor revision, appointment identity and human conflict evidence come from
server state. Approval inputs bind immutable submitted revision and proposer,
not a client `approved=true`. Recipient acceptance has server-loaded exact offered
scope/version and an explicit consent confirmation; it cannot widen the offer.
A body never carries a raw document, password/TOTP outside the dedicated assurance
request, or a source interpreted as arbitrary external fetch URL.

Require separate, versioned records for founding designation, platform appointment,
independent confirmation, mandate/eligibility findings, invitation verifier,
acceptance, real grant source and command receipt/outbox. Preserve synthetic C2
rows/registry/constraints and legacy membership/history. Prefer dedicated real
source/grant tables over silently broadening synthetic fields; alternative additive
source design must preserve nonpromotion and equally strong DB constraints.

### 4.3 Deadlines and invitation identity ambiguity to resolve

- Use strict `effective_at <= DB clock < expires_at`, timezone-aware UTC and
  explicit server-issued clock origins; recheck after lock wait. Exact month
  arithmetic and term truncation require N/S approval, not a guessed 365-day rule.
- Product maxima: eligibility 12 months, mandate earlier written end/12 months,
  real nonfinance grant earlier source/mandate end/90 days, invite earlier source
  validity/issuance +72 hours, activation authorization at most 24 hours. Short
  assurance remains ≤5 minutes and bounded by all existing auth/source deadlines;
  no product bound extends a proof or fixture grant.
- **Unresolved:** is PR23's 24h activation authorization created with onboarding
  approval, invitation, acceptance or a separate activation decision? If shared
  with invitation it may shorten a 72h maximum to 24h; that is not permission to
  extend either. Recommend separate short activation authorization after valid
  acceptance, tied to still-valid independent approval; obtain explicit approval
  of this interpretation before modeling clocks/renewal. Never auto-reapprove.
- **Unresolved:** PR17 permits personal signup while C3 nominee User is nullable.
  Recommend issue only after an exact pre-existing verified User/contact has been
  independently resolved; alternatively a pre-account invitation needs a separate
  governed identity-resolution binding before acceptance. No email-only claim,
  auto-link, first-login-wins or different-account substitution. NGO governance,
  security and product must choose the permitted signup/issuance ordering.
- Proposed token: at least 256 random bits, purpose-separated verifier/HMAC at
  rest and one active invitation per approved nomination/role version. No plaintext
  token in database/audit/receipts, ordinary URL query/path, analytics or persistence.
  Choose approved delivery: token-free link + separately entered code, or carefully
  reviewed fragment-to-memory exchange with immediate fragment removal, no third-party
  scripts and no-referrer. These are alternatives, **neither approved**. Persist
  issuance deadline once; resend/retry cannot extend it or create an unreviewed
  second bearer secret. Delivery failure/uncertainty is not acceptance.

## 5. Authentication, recovery, continuity and telemetry

C1 already performs password authentication, encrypted TOTP factors, timestep
anti-replay (current ±1 30s steps with a monotonic accepted-step fence), personal
session/credential rotation, epoch/recovery-generation checks and restricted/
review-required holds. `mfa.OPERATIONS` contains **six personal operations only**:
enroll, remove, recovery-code rotation, session logout-all, session revoke and
hold clear. Personal intent/proof ≤5 minutes binds user/session/epoch/recovery
and uses keyed command digests; factor revision and current state are checked.
`step_up()` can reuse an eligible recent-TOTP observation for personal operations;
hold-clear is stricter and needs a newly supplied pre-hold factor code. Removal
revokes sessions; it does not implement platform-officer factor retention.

**Compatibility gap, not a personal-auth vulnerability finding:** PR22 requires
fresh password plus current TOTP for the exact sensitive platform command. Do
not simply append operation strings or call personal `scope()/consume()` on NGO
objects; do not apply password-only fallback after factor removal. Propose a
separately accepted domain intent handler that:

1. Canonicalizes command fields server-side, authorizes current action/target and
   binds immutable command digest, User/session, auth epoch, recovery generation,
   contact identity/version, factor enrollment/revision, tenant/root/appointment/
   mandate/case/approval/grant revisions, bundle/policy version and all deadlines.
2. Issues an unguessable one-use challenge with ≤5-minute TTL, no later than the
   original session/access, authority/source or command deadline. Security must
   choose exact TTL, key versioning, nonce format, factor age and password/TOTP
   attempt order/budgets. Never store raw credentials or proposed secret payload.
3. Requires newly supplied eligible TOTP per protected intent, not a cached login
   MFA flag/recovery code. Existing timestep anti-replay may mean two actions in
   one timestep cannot both succeed; choose and test this UX/security constraint
   explicitly instead of relaxing replay prevention for throughput.
4. Rechecks every source and security generation under the approved shared locks;
   consumes proof with the decision/event/receipt. Revocation/hold/reset wins over
   valid MFA. Session rotation must either explicitly preserve a reviewed logical
   binding with current credential checks or invalidate the intent, never accept
   an old credential just because its logical session ID matches.

**GM06 alternatives:** A) prohibit factor removal while specified protected duties
are active (with independently controlled offboarding/recovery); B) allow personal
removal but immediately suspend protected-command eligibility until independently
approved eligible reenrollment/reprovisioning. Recommend **B for review** to avoid
trapping personal offboarding, with no automatic restoration and immediate intent
invalidation on factor change. A remains a legitimate selectable alternative.
Security/auth + operations + product must explicitly decide; this review selects
neither. Define legitimate initial factor enrollment separately from recovery
hold/replacement; an arbitrary cooldown duration is not invented here.

Telemetry proposal: redacted event ID, actor/process/function, command family,
tenant/source/policy/version, result/reason class, proof correlation (not secret),
security generation and receipt reference. Define narrow audit readers, failures/
lockout/DoS alarms, impossible independence, repeated recipient mismatch, unusual
issue/revoke and delivery backlog. No passwords, OTP/seed/verifier, document numbers,
raw external evidence, rosters or finance values in logs. Persist abuse accounting
outside rollback-prone domain transactions when required by approved auth policy;
audit outage must fail closed, not pretend successful command audit.

## 6. PostgreSQL, API and concurrency contract proposals

### 6.1 Invariants and least-privilege design

C3 has `controlled_no_self_review`, state/reviewer-shape checks, positive and unique
snapshot revision, separate attestation purposes, bounded opaque-handle regexes,
PROTECT relations, immutable initiator and UPDATE/DELETE-blocking history triggers.
These are useful **structural guards**. They do not check natural-person identity,
appointment eligibility, legal custody or a complete transition/event graph.
An authorized DB owner can insert an `approved` structural row without an approved
command; record state/revision edits are not yet a real restricted transition writer.
Regex-valid handles can still refer to sensitive material; syntax is not privacy proof.

C2's `pwc_kernel_lock` is read/lock-only SECURITY DEFINER, with PUBLIC execution
revoked and fixed search_path; `db_roles.sql` supplies a synthetic runtime profile.
It is **not** an installed production role inventory or general real-grant writer,
and it does not cover new controlled/invitation tables automatically.

Proposed additive invariants, signed off before migration:

- Every real source/approval/snapshot/invitation/acceptance/grant/event references
  the same tenant, nominee, policy and immutable approved revision, using explicit
  composite constraints or narrow guarded functions/triggers. Cross-row temporal
  policy cannot be claimed enforced by a simple SQL CHECK on another table.
- Independent actor/beneficiary/proposer restrictions, exact source kind, nonfinance
  bundle/version, valid interval, unambiguous authorized target and monotonic tenant/
  grant revisions. User inequality is necessary but not distinct-human proof.
- Unique command receipt key scope, nomination invitation slot, one acceptance per
  token and at most one activation grant per accepted source/version. Superseded/
  revoked/consumed objects cannot resurrect, including stale ORM saves or restore.
- Runtime may read narrowly scoped projections and invoke fixed validated functions,
  not INSERT/UPDATE/DELETE authority/attestation/receipt/audit tables arbitrarily.
  Function owners are non-login/non-runtime owners; revoke PUBLIC/CREATE/role
  inheritance/SET ROLE/TRUNCATE shortcuts; fixed trusted search_path, no dynamic SQL.
  DBA migrations/fixture credentials absent from workers. Test with actual restricted
  DB principals, not only a Django superuser connection.
- Exact locked audit/outbox/receipt rows append atomically with transition. History
  cannot be rewritten/deleted as rollback; used migrations forward-fix only. Actor
  sessions/provenance retained under approved privacy/retention, not erased by cascade.

### 6.2 Required transaction and lock graph

Primary PostgreSQL READ COMMITTED; no positive permission cache or replica authority.
Untrusted selectors locate IDs without disclosing data; then acquire **all** relevant
Users (actor, beneficiary, reviewer/confirmer/source actors that must be current)
in stable UUID order **before** contact/factors → sessions → challenge/credential/
intent locks in audited auth-helper order → platform appointment/root and NGO
root in a globally defined stable order → grants → nomination/approval/invitation/
acceptance/domain/idempotency rows in stable order → immutable event/outbox inserts.
Platform-root ordering is a missing extension of ADR-0002's existing NGO lock graph;
DB/auth reviewers must validate helper calls, not approve this prose as executable.
No late User lock, unbounded multi-tenant command, external mail/network I/O or
serializer/lazy query after the protected transaction. Recheck DB wall clock after
wait and immediately before final decision/commit. Existing 2s lock/5s statement
bounds are reviewed foundation values, not a claimed real-workload SLA.

Atomic unit: authorize current sources + expected revisions + exact proof → consume
proof/token if applicable → transition/revisions → audit/outbox → idempotent receipt.
Fail any step: no authority/partial acceptance escapes. Revocation serializes through
the same roots and takes effect at committed transition; an earlier serialized read
may finish, but no newly authorized request may use revoked power. Delivered bytes
cannot be recalled. An invitation's acceptance and later grant are distinct durable
transitions; if separately queued, a worker cannot stretch a short assurance proof
into unbounded authority. Approve a fresh bounded activation authorization instead.

### 6.3 API, proof and unknown-result table to approve

Current C6 unavailable endpoints must retain their actual contract until an approved
implementation changes them. No successful API is invented by this document. Proposed
command/status DTOs need authoritative OpenAPI generation, checked success/error fixtures,
TypeScript/Dart generation and real response-runner acceptance before client integration.

| Condition                                                                  | Proposed result / proof and receipt handling                                                                                                                                                                             |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Missing/invalid session, wrong transport/CSRF, inactive or held actor      | Existing auth contract denial; no target existence leak, grant or receipt disclosure. No password/TOTP fallback.                                                                                                         |
| Unowned or invisible tenant/source/receipt                                 | Nonenumerating 404 or existing approved denial envelope; authorize before disclosing versions/conflicts.                                                                                                                 |
| Required version absent / stale owned version                              | 428 / 412; semantic mismatch invalidates the bound intent durably under reviewed failure taxonomy; no domain mutation.                                                                                                   |
| Owned already-applied key + identical intent                               | Return previously committed minimized receipt/status, not a second command or proof reuse; reauthorize receipt access and current identity.                                                                              |
| Same key, different canonical command; consumed token/new key; stale offer | 409 conflict; invalidate affected intent as specified, retain original receipt; no duplicate grant/acceptance.                                                                                                           |
| Bad/missing assurance or ineligible factor                                 | Approved 403/challenge error; bounded auth attempts/abuse evidence; exact retryable/invalidated status must be specified. No domain changes.                                                                             |
| Deadlock/lock timeout/dependency/audit/outbox failure before commit        | 503, full domain/provisional proof-consumption rollback. Preserve required denial/abuse evidence through reviewed separate transaction; never swallow failure as successful revoke.                                      |
| Connection lost during/after commit                                        | Client shows **unknown**, does not issue new key. Fetch owned receipt by original key/correlation; absence alone is not permission to replay with new authority. Reconcile current source/version before approved retry. |
| External notification failure after commit                                 | Transition/receipt remains authoritative; bounded deduplicated outbox retry, no new invite/expiry extension, explicit delivery status. No external I/O inside locks.                                                     |

Idempotency scope proposal: actor + command family + tenant/target + key, canonical
payload hash and source/version; exact URI/headers, status visibility, retention,
key expiry and safe tombstones are API/security/privacy decisions. Do not borrow
72-hour invite or 90-day grant durations for receipt retention. Emit minimized
no-store responses; no browser bearer transport, caching/private persistence or
foreign-context status oracle. Clients use same-origin cookie + CSRF; native uses
its reviewed HTTPS bearer path only after per-command allowlist extension approval.

## 7. Backend/API/React/Flutter readiness and canonical acceptance

| Surface / screens                    | Current classification                                                            | Needed integrated behavior / dependencies and acceptance                                                                                                                                                                                                            |
| ------------------------------------ | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Django personal ID-01/02/05 services | Implemented gated foundation; not platform authority                              | Preserve current flows; add approved domain assurance, continuity and generation checks only after B4. Validate HTTP against real PostgreSQL, not mocked success.                                                                                                   |
| Django synthetic ID-03/04 contexts   | Synthetic only                                                                    | New real source/tenant lifecycle and current capabilities; no promoting C2 fixtures or legacy roles. Backend must deny A/B lists/detail/counts/search/status/audit/export even when UI is bypassed.                                                                 |
| Backend controlled requirements      | Generic policy, implemented gated route                                           | Not caller entitlements. Controlled reads/commands still 503; leave so until B1–8.                                                                                                                                                                                  |
| Backend C3 record/attestation/event  | Structural preparation, not functional approval                                   | Complete source/time/state/actor/writer/lock guarantees, accurate API states and constrained readers. Tests of raw rows/preflight do not prove live command permissions.                                                                                            |
| PWC Operations PWC-01                | UI-only/gated preparation; local synthetic revision preview                       | Real appointed-officer entry, exact revision/both findings, conflict-aware independent approval, bounded intent/factors, receipt/delivery/unknown states. No raw upload. Depends on officer IAM, approved API and WEB-02/03/06.                                     |
| NGO Web ORG-06                       | **Not implemented**                                                               | Exact offered role/scope/term, nominee acceptance, team/grant history, Primary request-only additional-admin actions, independent approval and revoke. Distinguish pending/accepted-not-authorized/active/expired/revoked/blocked/declined. No finance entitlement. |
| ORG-25 relevant subset               | **Not implemented**                                                               | Governed Primary replacement/succession, restriction/exit distinction and current capabilities. Finance/privacy policy, export/deactivation beyond approved subset remain separate.                                                                                 |
| ID-01–05 React                       | Personal/business integration not implemented; W1 specimens not account workflows | Reuse personal schemas; cookie/CSRF/refresh/rotation/hold errors; explicit server-issued context, clear stale UI and no first-NGO choice. W2/W3 gates not waived.                                                                                                   |
| Flutter ID-01/02/05                  | Implemented personal subset; API disabled by default                              | Preserve secure storage, lifecycle protection, personal recovery; configured native networking is not NGO transport authorization. Current allowlist has no real admin commands.                                                                                    |
| Flutter ID-03/04; ORG-01/02/03       | Unavailable panels / gated contract seams                                         | Future real context and invitation/authority states need approved DTOs + narrow transport extension, revocation/hold cancellation and no persisted invite/proof secrets. Native coverage does not imply all dense operator functions belong on mobile.              |
| OPS-01 audit/support/recovery        | No real privileged tool; reference only                                           | Strict audit-reader/incident authority and minimized view, independent approvals; no universal NGO-private read. Exceptional support content access excluded.                                                                                                       |
| ORG-04/05/PUB-04                     | Separate 04D/publication branch, not completed by 04C                             | E08 consent/allowlist before real eligibility can influence current C5 projection; avoid inadvertent publication while leaving 04D scope separate.                                                                                                                  |

**No real end-to-end authority screen is fully functional.** Shared components are
functional presentation infrastructure, not command acceptance. PWC-01 is the
canonical queue; controlled preparation is its revised product flow, not a new
screen ID. ORG-06/25 are 04C's canonical team/recovery subset. Founding provisioning
is an offline restricted procedure, not a new public officer signup screen.

Design System v1.0 already provides Inter/Noto Arabic, semantic light tokens,
React buttons/fields/cards/banners/status/modal/table/pagination and Flutter
ColorScheme/TextTheme/component themes. Reuse rather than introduce a UI framework.
Needed UX: explicit NGO/recipient/offered scope/term/approval revision, pending,
empty, restricted, unavailable, expired proof, stale 412, conflict 409, dependency
503, revoked/held, failed delivery and unknown result. Show no success until a
server receipt; accepted-but-not-authorized remains distinct from grant active.

Acceptance: keyboard/skip/route focus, modal containment/Escape/return focus,
associated errors and announced nonsecret status, measured contrast, ≥44px web/
48dp native targets, 320px reflow and large text/zoom, long names and isolated LTR
IDs within Urdu RTL, reduced motion, clear language. Axe/type/widget passes do not
replace screen-reader, native Urdu shaping/device and fluent translation review.
Token URLs/proofs must not enter browser storage, logs, analytic/referrer history,
clipboard automation or shared private caches. Invalidate in-flight UI on logout,
hold/revocation/credential or context change; never automatically replay a command.

## 8. Objective security and concurrency acceptance plan (future implementation)

These are required **future tests**, not executed tests of absent features.
Use isolated synthetic people/NGOs on actual PostgreSQL with independent connections,
barriers/events rather than timing sleeps. Record both serial orders and commit
linearization. No real documents/accounts or fabricated approvals in test evidence.

| Test                            | Objective acceptance                                                                                                                                                                                                                                                                                                                |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| T1 evidence and source validity | Registered/informal rubrics independently exercised; eligibility without mandate and mandate without eligibility cannot approve/activate; invalid custody/reference or withdrawn evidence fails.                                                                                                                                    |
| T2 matching and ownership       | Same-name different NGOs/branches remain distinct; foreign, hidden and absent identifiers yield indistinguishable denial; applicant/history access cannot acquire current authority.                                                                                                                                                |
| T3 bootstrap and independence   | Forged designation, expired appointment, wrong executor/confirmer, beneficiary=self, initiator=reviewer and two accounts of same vetted human rejected; only exact independently confirmed officer scope activates. Staff/superuser/Board/fixture never supplies it.                                                                |
| T4 time boundaries              | At source/invite/grant/proof deadline deny; test immediately before/equal/after, lock wait crossing expiry, timezone/leap-month arithmetic and resend no-extension. Product upper bounds never amend fixture or assurance cutoffs.                                                                                                  |
| T5 privacy and readers          | Reject forbidden PII/URLs/file ingestion and extra JSON keys; unauthorised audit/reference/status access gives no private existence/count. No credentials/tokens/seeds/evidence payload in captured logs, traces, browser storage or receipts.                                                                                      |
| T6 publication                  | Independently approved real eligibility/admin grant alone cannot put NGO/nominee/leadership contacts into public projection; explicit consent withdrawal fences publication without inventing financial/alliance effects.                                                                                                           |
| T7 revocation/recovery          | Race grant/mandate/officer revoke or dispute restriction against acceptance, activation, additional-admin request/approval and reads. If revoke commits first, no later allow; earlier serialized response is bounded. Planned succession separate; compromise can leave zero admins; recovery/restore never resurrects old grants. |
| T8 auth and factor continuity   | Cross-user/session/NGO/object/revision/scope intent substitution denied; stale credentials/epoch, password reset, hold, logout-all, new/recovery-code factor, removed/replaced TOTP and cached recent observation cannot satisfy protected command. Exact approved GM06 branch tested without breaking ordinary personal contracts. |
| T9 DB provenance/writers        | Runtime SQL cannot insert/update/delete authority, attestations/history/receipt or forge source; function argument forgery/cross-tenant linkage denied. Synthetic fixture/admin-probe/legacy role never real authority. Pinned bundles immutable; independent appointments versus later delegation tested separately.               |
| T10 replay/unknown result       | Concurrent same key/same intent gives one result/grant/event; different payload same key conflicts. Two accept attempts/token replay/new key cannot yield two grants. Drop response after commit, recover owned receipt without reexecuting, hide it from other principals; semantic invalidation is durable.                       |
| T11 atomic locks/faults         | Deterministic actor/recipient reset/hold/refresh/factor mutation/issuer revoke vs command, competing approve-return-edit and invite-revoke-accept; no deadlock caused by late User/helper lock. Inject DB/audit/receipt/outbox failure at each step: zero partial authority, bounded safe denial and exact retry semantics.         |
| T12 closed capabilities         | Complete positive/negative issuer→command→target matrix; Primary requests only, scoped Admin lacks privilege issuance; NGO A/B and Board/officer/finance/signatory/alliance denials across direct API/list/search/count/files/exports as applicable. Excluded APIs remain absent/denied, not mocked working.                        |
| T13 notices/transport/abuse     | Duplicate/bounce/suppressed/delayed mail, outbox retry/lost acknowledgment, recipient-contact changes and token URL handling; no renewal/second secret. Reject mixed bearer/browser provenance, Origin/CSRF spoofing, insecure native origin and wrong portal; verify bounded budgets and redacted alerts.                          |
| T14 migration/restore           | Fresh and upgraded DB preserve IDs/passwords/legacy/fixture constraints; used-history reverse refused; minimal runtime privileges proven; restore and forward correction retain revocation/deletion fences with manual regrant evidence.                                                                                            |
| T15 cross-platform E2E          | Backend real response fixtures/OpenAPI/TS/Dart parity; both portals and native account/context changes discard stale state; unknown result does not show success. Verify intended UI at 320px/large text/RTL and manual assistive-tech/native Urdu/browser/TLS acceptance before real activation.                                   |

## 9. Decisions, sign-off package and implementation order within existing roadmap

Do not hand the user multiple new phases/tasks. One eventual comprehensive 04C
assignment may use the following internal dependency order **after I contracts are
accepted**; this review stops before any such implementation.

1. **Close scope and trust (03B.3 dependency):** product + S/N/O sign B1–3 command
   charter, named appointment/identity/confirmer chain and exact bundles/NGO quorum.
   Choose permitted real-domain versus synthetic exercise boundaries explicitly.
2. **Close protocol/schema (03B.3 + 04C):** S/auth/D/API/N/L sign B4–8, GM06 choice,
   intent/failure table, recipient issuance order, expiry clocks, minimal references,
   source/invalidation/DB writer and helper lock graph, receipt/outbox/readers.
3. **Implement only authorized bounded substrate:** additive migrations/constraints,
   restrictive writers, source/revision controls, audit/receipts and restricted-role
   PostgreSQL tests. Preserve synthetic v1 and historical migrations; no raw uploads.
4. **Officer and record lifecycle:** manual restricted bootstrap/renew/revoke and
   current capability checks, then externally attested record submit/independent
   approve/reject/return under exact assurance/locks; no unreviewed fallback.
5. **Invitation → consent → separate grant:** recipient resolution, bounded delivery,
   explicit acceptance, current source revalidation and initial nonfinance grant;
   then scoped additional administrators, revoke/succession/contested recovery with
   independently approved matrices. Test unknown result and all races before clients.
6. **Contract consumers and feature acceptance:** generated actual APIs/fixtures,
   NGO ORG-06/25, PWC-01 and appropriate mobile workflow portions using Design System;
   preserve W1/native gate until approved live integration. Demonstrate two NGOs,
   restricted actors, rejected stale commands and revocation end-to-end.
7. **Separate activation/release:** REAL01/02/04 actual evidence, role inventory,
   custody/privacy, provider/HTTPS/CSRF/origin, independent security/ops drills,
   monitoring/restore/load/accessibility/device and human go/no-go. REAL03 powers,
   04D publishing, P4 membership, P6 finance and P7 alliance remain separate.

Every sign-off must state accepted option, named accountable reviewer, date,
contract/bundle/schema version, environment/data scope, test artifacts and residual
exclusions. A function assignment or positive synthetic test is not a signature.
Incomplete branch approval blocks that branch; do not relax global deny defaults.

### 9.1 Roadmap reconciliation and observed deviations

- P0–P8 and M1–M3 preserved. §11's PR17-open snapshot is now stale: PR17 merged
  `ca46a20`; PR19–23 added product direction/contracts. Append a dated correction,
  not rewrite the earlier audit as if it had always known later merges.
- Original 03C generalized audit/file primitives remain partial. Current append-only
  domain/auth events are not generalized protected file access. Correct by explicitly
  delivering required command audit/outbox/readers in 04C under approved contract;
  raw files remain excluded for offline rollout, not marked implemented.
- Approved offline 04B supersedes original applicant self-service. Keep old owner
  history/withdrawal, do not reopen intake based on obsolete workflow text. Legacy
  G1 “claims/creates verified NGO” demo must use controlled external verification.
- ORG-06's old “prevent last-admin lockout” recommendation must not prohibit urgent
  compromise revocation. Product E09/PR19 governs planned succession versus emergency;
  no need to rewrite canonical ID or silently choose a legal quorum.
- W1/design early delivery is permitted sequencing, not unauthorized scope reduction.
  Original PWC-05D/05E functional M1 integration, G1b and release gates remain open.
- **No additional unauthorized runtime deviation identified in the inspected bounded
  code**; that is not independent certification. C3 shell constraints and proposed
  contract prose leave known missing guarantees, explicitly carried above.

## 10. Validation ledger and handoff

Validation exercises unchanged foundations, not future commands, human identity
proofing, legal sufficiency or independent approval. Native SDK/Android/Docker are
absent locally; no Flutter/device/production pass will be inferred from old CI.
Exact commands/results and final immutable-head CI references are recorded below
and in the consolidated PR handoff. Source code, dependencies, workflows, generated
API artifacts, migrations and activation flags must remain unchanged.

### 10.1 Executed local checks

Environment: Python 3.11.2, actual
PostgreSQL 16.2, Node 22.22.3/npm 10.9.8. PostgreSQL is disposable, loopback-only,
synthetic test data. Temporary NPM-supplied PostgreSQL/Chromium binaries and shared
libraries live in excluded `.cache`, not application dependencies or shipped code.
Backend commands below use `PWC_ENVIRONMENT=test`, environment-supplied test secret,
`DB_NAME=pwc_review`, `DB_USER=pwc`, loopback port 55432 and `PYTHONPATH=apps/backend`.
These are local test values, not real-user or production configuration.

| Exact command / working directory                                                                                                                                                                                           | Outcome                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `.venv/bin/pip install --require-hashes -r requirements-ci.lock`; `.venv/bin/pip check` (root)                                                                                                                              | Installed pinned tooling/runtime; no broken requirements                                                        |
| `.venv/bin/python -m scripts.python_lock --check` (root)                                                                                                                                                                    | 12 runtime and 33 CI pinned versions/hash locks checked                                                         |
| `.venv/bin/python apps/backend/manage.py check` (root)                                                                                                                                                                      | 0 issues                                                                                                        |
| `.venv/bin/python apps/backend/manage.py makemigrations --check --dry-run` (root)                                                                                                                                           | No changes detected after DB setup                                                                              |
| `.venv/bin/python apps/backend/manage.py migrate --plan`, `migrate --noinput`, `migrate --check` (root, same Python prefix)                                                                                                 | Plan and application to fresh PostgreSQL completed; no pending migrations                                       |
| `.venv/bin/python -m contracts.check --check` (root, backend PYTHONPATH)                                                                                                                                                    | Generation/inventory/source/frozen compatibility, OpenAPI 3.1/security metadata and checked examples passed     |
| `../../.venv/bin/python manage.py test --testrunner contracts.testing.ContractRunner --verbosity 1` (`apps/backend`)                                                                                                        | **450 tests passed**, 373.936 seconds; **288 observed** route/method/status combinations, no contract mismatch  |
| `.venv/bin/python scripts/security_checks.py` (root)                                                                                                                                                                        | Tracked-file security scan: 0 findings                                                                          |
| `.venv/bin/python -m unittest discover -s tests/tooling -v` (root)                                                                                                                                                          | **6 tests passed**                                                                                              |
| `.venv/bin/ruff check apps/backend scripts tests/tooling` (root)                                                                                                                                                            | Passed                                                                                                          |
| `.venv/bin/ruff check --select E4,E7,E9,F apps/backend/config/environment.py apps/backend/accounts/test_environment.py scripts/security_checks.py scripts/python_dependency_review.py scripts/python_lock.py tests/tooling` | Passed                                                                                                          |
| `.venv/bin/ruff format --check` with that same six-path selection                                                                                                                                                           | Six files already formatted                                                                                     |
| `npm ci --ignore-scripts`; `npm run check` (root)                                                                                                                                                                           | Token/font parity, TypeScript, Prettier, **130 unit/contract tests**, both React production builds passed       |
| `npm run contracts:types:check` (root)                                                                                                                                                                                      | Canonical OpenAPI TypeScript drift check passed                                                                 |
| `LD_LIBRARY_PATH="$PWD/.cache/al2023/lib" PLAYWRIGHT_CHROMIUM_EXECUTABLE=/tmp/chromium npm run test:browser` (root)                                                                                                         | **21 tests passed**, 28.1 seconds, Chromium 153; unchanged UI gates, EN/UR/axe/reflow/focus and no API requests |
| `npm audit --audit-level=low` (root)                                                                                                                                                                                        | 0 vulnerabilities                                                                                               |
| `git diff --check`, documentation ID/link/preserved-prefix and docs-only checks                                                                                                                                             | Results recorded at final checkpoint/PR; no runtime edit permitted                                              |

Temporary-tool setup initially lacked PostgreSQL SONAME links/database creation;
resolved locally without repository changes. An initial full-suite command from
repository root discovered **zero** tests: not accepted as regression evidence;
rerun from `apps/backend` produced the 450-test result above. No SQLite substitute,
privileged activation or real verification data was used.

### 10.2 Unexecuted and final-head evidence

Flutter analysis/widget/Android/device/iOS checks are **not rerun locally** (SDK and
native toolchains absent); mobile CI path filtering does not ordinarily run on
these documentation-only changes. No prior mobile pass is relabeled a current
execution. Python 3.12, CI Docker image/dependency-advisory checks and hosted
browser regression are subject to existing final-head workflows; exact results,
immutable SHA and run links belong in the PR evidence comment, not inferred here.
Python hosted advisory queries were not run locally; npm advisory check is stated
separately. No new real-command/concurrency/device tests can pass for absent features.

**Handoff:** documentation review can proceed. A complete 04C implementation
assignment is **not safe to begin** until affected I contracts/sign-offs are
recorded. Independently authorized design/test-only preparation is different from
that complete assignment. No real authority, networking or next subphase begins.
