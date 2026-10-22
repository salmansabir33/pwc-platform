# Pakistan Welfare Club (PWC)
## Development Execution Plan v1.0 — Draft for Review

**Document status:** Working draft; implementation has not been authorized.  
**Prepared:** 22 October 2026  
**Pilot:** Faisalabad Chapter  
**Scope:** Citizen/volunteer mobile app, independent NGO management (mobile and web), PWC alliance/committee workspaces, PWC operations portal, Django API, PostgreSQL and supporting infrastructure.  
**Planning convention:** **[S]** user-selected *provisional* requirement; **[R]** recommended implementation/design; **[O]** unresolved decision; **[D]** deferred. No provisionally selected item is represented as constitutionally or technically final.

---

## 1. Executive execution strategy

The PWC ecosystem has four interconnected product domains: (1) citizens and volunteers, (2) independent NGO operations, (3) NGO-to-NGO collaboration and PWC-led projects, (4) PWC alliance governance and operations. All share one personal identity system; data and decision authority are **not shared by default**. The first publicly usable MVP consists of three coordinated milestones:

- **M1 — Secure institutional foundation:** accounts, identity, organizations and provisional verification, context-aware authorization, memberships, member imports and claiming, NGO administrators and basic directory/profile.
- **M2 — Independent NGO operations:** NGO volunteers, events, independent projects, tasks/milestones/resources/budgets, dues, donations, income/expense cashbooks with multiple accounts, approval policies, reports and operational UI.
- **M3 — Alliance collaboration and public participation:** public discovery, volunteer opportunity flows, controlled inquiries, PWC institutional membership, committees, meetings and proposals, NGO collaboration, authorized commitments and PWC projects.

**[R]** Build as a modular Django REST monolith backed by PostgreSQL; Flutter mobile application with feature-first modules, Riverpod and go_router; responsive NGO administrative web interface and separately secured PWC operations portal. Exact client-web implementation and detailed packages are not approved. Deliver complete vertical workflows with backend authorization, UI, tests and audit events—not isolated screens or tables.

**Fundamental rule [S]:** PWC owns/operates the platform but has no routine alliance-level access to independent NGO private membership, volunteers or finance. Shared collaboration requires explicit scope and consent; PWC membership does not confer authority over an NGO's operations.

## 2. Authoritative input documents and conflict-handling

| Input | Role in execution | Status |
|---|---|---|
| PWC Strategic & Product Foundation v1.0, Draft for Formal Review | Product scope, governance, P0/P1/P2 priorities and selected decisions | Provisional |
| PWC App Information Architecture & Navigation v1.0 | Mobile five-tab shell, workspace switcher and canonical screen IDs | Proposed |
| PWC Detailed Mobile & Web Screen Specification v1.0 | 72 screen definitions, high-risk flows HF-01–HF-10, acceptance tests | Proposed |
| PWC Identity, Authorization & Multi-NGO Data Model v1.0 | Isolation, relationships, claims, delegated permissions, project commitments | Proposed |
| PWC Django Backend & PostgreSQL Schema Foundation v1.0 | Suggested apps, table inventory, invariants, API boundaries, migrations | Proposed |
| PWC Flutter Frontend Architecture v1.0 | Client state, routing, cache partitioning, offline rules and testing | Proposed |

**[R]** Maintain a decision/requirement register in repository with source references, status (`selected-provisional`, `recommended`, `open`, `approved`, `deferred`), reviewer, date and implementation impact. When documents disagree, do not silently choose: issue an ADR (architecture decision record), secure review, and update all affected artifacts. Freeze API contracts, naming and database conventions *before* dependent work begins. Do not treat previous Coventure architecture as automatically authoritative for PWC.

## 3. Scope commitments and exclusions

### 3.1 P0 functional scope [S and supporting R]

1. One person may hold multiple independently verified NGO memberships, NGO volunteer enrollments, committee roles and PWC roles.
2. Eligible registered NGOs and credible eligible unregistered groups may obtain software access subject to category-specific verification; PWC alliance membership is a separate relationship.
3. A claimant receives a **limited provisional organization workspace** pending verification of organizational eligibility and authority; existing tenant records remain protected.
4. NGO-configurable member registration: open / approval / invitation; categories, renewals, reminders, grace policies, waivers, discounts, partial payments, exemptions and manual receipt records.
5. Member and volunteer manual creation plus CSV/Excel bulk import, unclaimed records and secure claim by identity plus controlled token or authorized NGO approval.
6. NGO-configurable volunteer enrollment: open / approval / invitation; separate standing enrollments from opportunity applications and event assignments.
7. Organization-private teams, roles, published leadership, announcements, activities and projects with tasks, teams, milestones, resources, basic budgets and progress.
8. NGO-private cash and multiple bank/cash registers; incomes, expenses, donations, membership receipts, transfers, reversals, configured direct-entry or independent approval; account-level summaries.
9. Confirmed NGO dues/donations produce **idempotently linked** account entries, respecting NGO approval mode. Unapproved records do not affect finalized balances.
10. NGO activity/project visibility: Public, Members Only, Private; sensitive fields and attachments remain separately protected.
11. Citizen discovery, registration, volunteering and general collaboration/assistance inquiries; **not** comprehensive beneficiary case management.
12. PWC member organizations: committees, meetings, proposals, joint initiatives, partnership requests and documented NGO-approved single/multi-approver commitments.
13. PWC own projects and funds must have separate accounting and roles from individual NGOs' private finances; exact PWC finance depth requires sign-off.
14. NGO alliance exit is different from platform workspace deactivation. Export, retention, deletion and administrator-recovery workflows are controlled.

### 3.2 Deferred unless separately approved [D]

Sensitive beneficiary case management, unrestricted public welfare-case intake, online payment gateway, comprehensive general ledger/double-entry accounting, bank reconciliation, payroll, procurement, advanced inventory, donor CRM, AI matching, multi-chapter operations, legally operative online election system, unrestricted direct messaging, and extensive custom workflow builders.

**[R]** P0 is a substantial MVP. Reduce complexity by simplifying optional UI and reporting depth, *not* by weakening authorization, financial correctness, participant consent or verified organizational authority.

## 4. Delivery governance and team structure

### 4.1 Accountability [R]

| Role | Responsibility and key outputs |
|---|---|
| Product owner (PWC) | Resolve business decisions, prioritize backlog, accept user journeys |
| NGO pilot representatives | Validate NGO-specific policies, trial imports/volunteering/finance, review accessibility |
| Technical lead / architect | ADRs, cross-domain interfaces, security invariants, integration quality |
| Backend engineers | Django domains, PostgreSQL migrations, authorization, services and APIs |
| Flutter engineers | Mobile navigation/workspaces, interactive features, API integration |
| Web frontend engineer(s) | NGO administration, PWC operations, CSV import and reporting UI |
| UI/UX designer | Design system, flows, all P0 screen states and usability testing |
| QA / test automation | Tenant-isolation negative tests, workflow and end-to-end regression |
| DevOps / security owner | Environments, secrets, backups/restores, monitoring, deployment and incident response |
| PWC legal/compliance adviser | Check entity status, software terms, privacy practices, charity/fundraising requirements |

One person may hold multiple responsibilities in a small team, but **review/approval authority for sensitive production access and financial controls should not be collapsed simply to save headcount**. Assign named owners and substitutes before implementation.

### 4.2 Work management [R]

- Git repository with branch protection, pull-request review, mandatory CI, issue IDs and versioned ADRs.
- Work tickets carry: requirement + screen ID, user role/context, endpoint, schema impact, business rules, error states, tests, acceptance evidence and dependency.
- Weekly integration review; regular NGO user-testing; risk and decision reviews at milestone gates.
- Definition of Ready: requirements unambiguous, cross-tenant permissions defined, API contract agreed, sample payloads, negative cases, design states, test data.
- Definition of Done: code reviewed; migrations validated; backend tests and client tests pass; audit/permission tests pass; documentation updated; feature verified in staging with representative roles.

## 5. Delivery tracks and parallel sequencing

| Track | Begins | Parallelizable work | Blockers |
|---|---|---|---|
| T0 Product/design/technical decisions | Immediately | UI patterns, domain map, threat-modeling | Material open legal/operating decisions |
| T1 Platform/infrastructure | Immediately after baseline | Repo, CI, envs, logging, migrations, auth skeleton | Hosting/secrets choices |
| T2 Identity/tenant access | After T1 schema baseline | Django auth and Flutter session shells | Immutable access contract required for all private modules |
| T3 NGO onboarding/membership | After T2 core | Screens, member import, claim, membership policies | Verified org/actor relationships |
| T4 NGO finance/dues | After membership identity | Financial screens, cashbook services, dues | Source-idempotency and approvals |
| T5 Volunteers/events/projects | After tenant access | Mobile/web screens and relevant APIs | Member/volunteer separation; visibility rules |
| T6 Alliance/committees/collaboration | After T2 and basic projects | PWC-specific workspaces, invitations, governance | NGO signatory/approval evidence |
| T7 Stabilization/pilot | After representative vertical slices | QA, training, rollout, operational simulations | All M1–M3 release gates |

**[R]** Backend and client teams can work in parallel against versioned OpenAPI schemas and mock responses, but no frontend assumption replaces authoritative server checks.

## 6. Proposed repository and environments

```text
pwc/
  apps/
    backend/               # Django project, DRF, PostgreSQL migrations
    mobile/                # Flutter application
    ngo-web/               # Responsive independent NGO administration [technology O]
    pwc-ops/               # Segregated alliance/platform operations [technology O]
  packages/
    api-contracts/         # OpenAPI source or generated client models
    design-tokens/         # Shared source of visual semantics as suitable
  infra/                   # Deployment configuration, backup/restore runbooks
  docs/
    decisions/             # ADRs and decision register
    product/               # Product/screen specs and traceability
    runbooks/              # Operations, security and recovery
  tests/
    contracts/             # Multi-client API schema/response contracts
    end-to-end/            # Cross-surface scenario definitions
```

**[R]** Use separated local, CI, staging and production configurations; PostgreSQL backing service; private file/object storage; managed secrets; TLS; restricted admin network/access; asynchronous job runner for imports, exports and notifications; observability. Enforce migration checks and health checks in CI/deployment. Avoid using production personal/financial data in staging.

## 7. Cross-cutting platform work packages

| ID | Work package | Dependency | Deliverable / exit condition |
|---|---|---|---|
| CORE-01 | Repo, build pipeline, lint/types, test harness | T0 | Repeatable backend/Flutter/web build; CI rejects failing tests |
| CORE-02 | Environment, PostgreSQL, backups and secrets | CORE-01 | Encrypted backups, successful restore drill in staging |
| CORE-03 | User identity, contact verification and sessions | CORE-01 | Signed-in/out flows; safe token refresh and revocation |
| CORE-04 | NGO/PWC context and authorization engine | CORE-03 | Server-enforced per-action, per-tenant access; negative matrix passes |
| CORE-05 | Audit events, idempotency, outbox/jobs | CORE-04 | Protected event trail, retry-safe jobs and mutation contracts |
| CORE-06 | File/document access | CORE-04 | Private attachments with authorization-checked access |
| CORE-07 | Notifications and delivery preferences | CORE-05 | Scoped notifications; no sensitive payload leakage |
| CORE-08 | Search/public projections | CORE-04 | No confidential data in search/filter results |
| CORE-09 | OpenAPI and typed client generation | CORE-03 | Versioned endpoints, state/error contracts in CI |
| CORE-10 | Observability and service operations | CORE-01 | Health alerts, audit alerts, incident runbooks |

**Critical global constraints [R]:** tenant-qualified list/detail querysets; object checks on every mutation; org IDs and resource IDs checked consistently; no caching across organizations; scoped exports and imports; no unreviewed Django Admin backdoor for private NGO data; auditable privileged support access with expiry.

## 8. M1 — Secure institutional foundation

**Target outcome:** A person can establish a secure account; a legitimately authorized organization representative can obtain a workspace; that NGO can manage its own member relationships without exposing other NGOs.

| ID | Backend/data tasks | Client screens / integration | Dependency / acceptance |
|---|---|---|---|
| M1-01 | User, contact verification, session lifecycle | ID-01, ID-02, ID-05 | Auth tests and account recovery cases |
| M1-02 | Workspace context, role grants, permission checks | ID-03, ID-04; ORG-06 | Multiple NGO access isolated and context switches invalidate cached private data |
| M1-03 | Organization registry, duplicates, claimant and authority verification | ORG-01, ORG-02, ORG-03 | Provisional claimant cannot see existing NGO private data |
| M1-04 | Public profile/leadership visibility rules | ORG-05, PUB-04 | Ordinary members not listed publicly; approved leadership only |
| M1-05 | Organization settings, member category/mode/status models | ORG-07, ORG-08, ORG-09, ORG-12 | Open/approval/invite policy enforced server-side |
| M1-06 | Imported person/member records, CSV/XLSX parsing, dedup preview | ORG-10 | No auth users fabricated; re-import replay safety; no cross-tenant overlap |
| M1-07 | Claim tokens, identity and NGO approval for imported records | ORG-11 | Never claim based solely on name/contact coincidence |
| M1-08 | Team, delegated admin roles, transfer/recovery | ORG-06, ORG-25 | No unauthorized finance grant and no NGO takeover |
| M1-09 | NGO overview and initial reports | ORG-04 | Counts are tenant-restricted; only permitted aggregates |
| M1-10 | M1 security and demo rehearsal | all M1 | Full workflow demo with at least two NGOs and conflicting roles |

**M1 exit gate:** onboard two separate test NGOs; create/import members; claim an imported record; demonstrate that unauthorized NGO and PWC roles cannot read/write/extract other-tenant membership; recover an NGO administrator using documented checks; pass CI and staging smoke tests. NGO admission into the alliance remains separate from platform onboarding.

## 9. M2 — Independent NGO operations

**Target outcome:** A verified NGO can manage volunteer relationships, activities, structured projects, member dues and its private recorded finances independently.

| ID | Backend/data tasks | Client screens / integration | Dependency / acceptance |
|---|---|---|---|
| M2-01 | Member fee assessments, adjustments, exemption, partial payment, renewal engine | ORG-12, ORG-13 | Accurate outstanding dues and configurable expiry policy |
| M2-02 | Volunteer enrollment policies, rosters, imports and claims | ORG-14, ORG-15 | Volunteer relationship separate from formal NGO membership |
| M2-03 | Opportunities, applications, assignments, attendance | ORG-16, ORG-17; PUB-06, PUB-09 | Open enrollment never bypasses sensitive assignment screening |
| M2-04 | Activities/events with public/member/private visibility | ORG-18 | Participant roster and sensitive fields stay private |
| M2-05 | Independent project ownership, teams and visibility | ORG-19, ORG-20 | Project manager rights are project-scoped |
| M2-06 | Tasks, milestones, resource requirements, budget estimates | ORG-21, ORG-22 | Budget != posted actual expense; no implicit PWC ownership |
| M2-07 | Multi-account cashbook, income/expense/donations, transfers | FIN-01–FIN-05, FIN-07 | Balanced transfers; proper balances; tenant isolation |
| M2-08 | Finance approval policy, approver separation, recovery | FIN-06, FIN-09 | Direct vs approval mode, no self-approval in approval mode |
| M2-09 | Receipt linkage, idempotent posting, reversal and traceability | ORG-13, FIN-03, FIN-07 | Confirmed dues/donation source creates <=1 posting |
| M2-10 | Reports, exports, announcements, notifications | ORG-23, ORG-24, FIN-08 | Scoped exports; approved report permissions; no cross-tenant notification payload |
| M2-11 | M2 finance and operations rehearsal | all M2 | Full financial scenario including pending, posted, transfer and reversal |

**M2 exit gate:** one NGO runs member renewals, volunteer enrollment, an event and a structured project while maintaining independent multi-account balances; approval and direct workflows both work; results remain inaccessible to another NGO and PWC Board-only identities. All monetary amounts use agreed fixed-precision representation and deterministic posting services.

### 9.1 Finance-specific executable invariants [R]

- Transaction create and linked dues/donation receipt posting execute atomically, with unique source-kind/source-id keys scoped to organization.
- Repeated submissions or worker retries cannot duplicate financial entries.
- Approval workflow stores immutable decision evidence; posted balances exclude pending drafts.
- Account-to-account transfer changes opposite account balances by equal amount and has zero net impact on aggregate NGO income/expense.
- Reversal creates linked counter-entry; already-posted source records are not silently deleted.
- Changing finance authorization modes cannot auto-approve existing pending entries.
- Two different users are required for maker/checker in approval-required mode; NGOs unable to support this must choose direct-entry mode.
- Finance permissions are explicitly granted to NGO principals, **not inherited automatically** from primary NGO administrator or PWC roles.
- Project budget allocations and cashbook transactions are separate; actuals show only where finance permissions allow.

## 10. M3 — Alliance collaboration and public participation

**Target outcome:** A citizen can discover activities and volunteer; a committee can develop a proposal; independent NGOs can accept or decline specific PWC/joint-project commitments; PWC administers its own projects without taking control of NGO private records.

| ID | Backend/data tasks | Client screens / integration | Dependency / acceptance |
|---|---|---|---|
| M3-01 | Public indexes/projections, search and filters | PUB-01, PUB-02, PUB-03, PUB-05–PUB-07 | Public data only, published owner and verification labels |
| M3-02 | Public inquiry receipt and safe routing | PUB-08 | Controlled contact inquiry, not sensitive case-management system |
| M3-03 | My participation/updates and notification actions | PUB-09, PUB-10 | Users see own applications and permitted alerts only |
| M3-04 | PWC institutional application/admission/representatives | ALL-01, ALL-02, ALL-03 | PWC voting eligibility separate from platform NGO verification |
| M3-05 | Committee registry, membership and workspace | COM-01, COM-02 | Committee roles never grant NGO administrative/financial access |
| M3-06 | Committee meetings, agendas, notes and project proposal | COM-03, COM-04 | Meeting/project approvals preserve authorized decision trail |
| M3-07 | Collaboration requests/offers, shared visibility | Collaboration screens in detailed inventory | No publication of foreign NGO-private records |
| M3-08 | Versioned organization commitments, single/multi-approver policies | Joint-commitment screens in detailed inventory | One NGO's acceptance cannot bind another; stale approval rejected |
| M3-09 | PWC-owned/joint initiative workflow and participant reporting | PWC project screens in detailed inventory | Project approval != NGO opt-in; responsibility explicitly attributed |
| M3-10 | PWC alliance/technical operations console | Admin screens in detailed inventory | Different roles for governance vs platform support; audit of privileged actions |
| M3-11 | NGO alliance withdrawal without software termination | ORG-25, ALL-01 | Independent tenant data and access persist subject to platform status |
| M3-12 | Public/NGO/PWC three-sided pilot rehearsal | cross-surface | Citizen, two NGOs, committee and PWC officers complete joint initiative |

**M3 exit gate:** demonstrate a public volunteer journey and committee-originated proposal, NGO A accepting, NGO B declining, tracked organization-scoped commitments, attributed project outcomes, and unchanged private NGO membership/finance access. Public inquiry handling must not store protected welfare-case dossiers by accident.

## 11. Screen and journey traceability

Screens follow the canonical IDs from the App IA and Detailed Screen Specification; do not rename IDs during implementation without a documented update. Important journeys:

| Journey | Screen sequence (representative) | Backend services | Gate |
|---|---|---|---|
| Create/claim NGO | ID-01 → ORG-01 → ORG-02 → ORG-03 → ORG-04 | organizations, access, audit | M1 |
| Membership application | PUB-04 / ORG-08 → ORG-07 → ORG-09 | ngo_memberships | M1 |
| Bulk member import and claim | ORG-10 → ORG-11 → ID-03 | ngo_memberships, accounts | M1 |
| Member dues and linked finance | ORG-12 → ORG-13 → FIN-06/07 | ngo_memberships, ngo_finance | M2 |
| Volunteer participation | PUB-06 → PUB-09 → ORG-16/17 | volunteers, activities | M2/M3 |
| Independent NGO project | ORG-19 → ORG-20 → ORG-21/22 | projects, ngo_finance (authorized actuals) | M2 |
| Multi-account finance | FIN-02 → FIN-03/04/05 → FIN-06/07/08 | ngo_finance | M2 |
| Committee-originated collaboration | COM-02/03/04 → collaboration/commitments → project workspace | alliance, collaboration, projects | M3 |
| Withdrawal / deactivation | ALL-01 / ORG-25 → protected export/deactivation | organizations, alliance, exports, audit | M3 |

The user-facing mobile tabs remain **Home, Discover, Participate, Updates, Profile** [R], with explicit workspace selection for NGO/PWC contexts; there is no automatic cross-organization context bleed. Web interfaces carry dense administration and bulk operations.

## 12. API, contracts and data migration discipline

- Version API endpoints consistently (proposed `/api/v1/`); produce OpenAPI and typed client models from authoritative definitions.
- Define structured error types: authentication, authorization, validation, conflict/stale version, rate limit, temporary failure and idempotent replay; frontend displays appropriate recoverable states.
- Every private endpoint documents actor, organization context, allowed role/permission, object-ownership check, filtered fields and audit event.
- Write services for sensitive mutations; views should not perform multi-model posting directly.
- Use PostgreSQL transactions (`transaction.atomic`), `select_for_update` or equivalent for contested approval/posting, unique constraints for replay safety, and `transaction.on_commit`/outbox for notifications.
- Migration reviews include unique constraints, tenant indexes, referential integrity, deletion behavior and irreversible backfill plans; rollback should be rehearsed for critical migrations.
- Use version checks (`409`/`412` response convention to be ratified) for concurrent updates to joint commitments or finance policy.
- Secure file access through short-lived authorized mechanisms; object keys are not public permissions.
- Background jobs receive explicit tenant context, run idempotently and may not circumvent access policy.

### 12.1 Suggested database/app readiness sequence

1. `accounts`, `access`, `organizations`, `audit` and session ownership.
2. `ngo_memberships` with imported-person references and claims.
3. `volunteers`, `activities` and `projects` tenant scoped.
4. `ngo_finance` receipt/approval and accounts with constraints.
5. `alliance`, `collaboration` and separate `pwc_finance` scope.
6. `notifications`, `exports`, documents and public read projections at appropriate integration points.

**[R]** Do not treat the numeric list above as a mandate to delay critical shared infrastructure such as private-file authorization and auditing until late stages.

## 13. UI/UX and frontend implementation contracts

- Wireframe all P0 screens in canonical order; cover empty, loading, populated, failure, forbidden, stale, pending approval and offline states.
- Design tokens and shared components for forms, tables, filters, status chips, financial amounts and confirmation dialogs.
- Provide visible **acting-as context** on sensitive NGO workspaces; confirm NGO name when changing financial or administrative permissions.
- Keep personal profile, NGO membership, NGO volunteering, PWC institutional representation, committee membership and project assignments visually distinct.
- Route guards are convenience, not authorization; server determines capability and returned sensitive fields.
- On tenant switch or logout, clear tenant-keyed in-memory caches, pending forms and sensitive document references; never flash data from previously active NGO.
- No optimistic balance changes for money posting, approvals or binding NGO commitments; show pending/confirmed from authoritative server results.
- Offline capability is limited to safe read-only public/local drafts unless specific conflict-resolution and encryption requirements are approved; no offline financial posting or signature approvals in MVP.
- Urdu/localization readiness, accessibility (labels, contrast, keyboard/screen reader), and clear public/private content labels included in review; exact localization launch set [O].

## 14. Test strategy and release-quality gates

### 14.1 Test suites [R]

| Layer | Required coverage |
|---|---|
| Backend unit | State transitions, membership dues, policy engines, transfers, receipt idempotency, approval decisions |
| Backend integration | Real PostgreSQL constraints, concurrent writes, imports, notifications, exports, attachment authorization |
| Permission-negative matrix | NGO A vs B; PWC Board vs private NGO records; NGO admin vs restricted finance; project participants vs nonparticipants |
| Contract tests | OpenAPI/client schema validity, paging, error/state conventions, required tenant context |
| Flutter unit/widget | Session, workspace switch, route guards, finance states, form validation and accessibility |
| Web UI | Bulk import, permission forms, member administration, finance reports, committee approval views |
| E2E | F1–F8 navigation flows, HF-01–HF-10 high-risk flows, PWC/NGO cross-surface project scenario |
| Security | IDOR, privilege escalation, forged approvals, import poisoning, replay, export leakage, unsafe attachment access |
| Operations | Restore drill, migration/rollback simulation, worker retry, audit log retrieval, support-access revocation |

### 14.2 Mandatory no-go failures [R]

Release is blocked if any tenant-private data appears to unauthorized users; finance can double-post; organization commitments can be forged/implicitly created; member imports create unauthorized user accounts; exported files leak across tenants; a claim can attach on phone/name alone; production secrets are mishandled; or tested backup recovery is absent. Security-critical failures are not converted into known issues for public release.

### 14.3 Acceptance evidence per milestone

- M1: annotated verification cases, two-tenant read/write test report, imported-member claim replay and takeover tests.
- M2: signed-off financial transaction matrix, report totals, dual approval and direct-entry scenarios, private finance cross-role tests.
- M3: demo/evidence of committee proposal, multi-organization opt-in, versions/approvals and distinct PWC vs NGO attribution.
- All milestones: product owner review, automated tests, security/QA report, UX walk-through, performance baseline and operational readiness checklist.

## 15. Privacy, compliance and operational readiness

PWC as direct operator [S] must establish appropriate software terms, privacy notices, platform-support policies, a breach/incident response procedure, NGO data-export/retention policy, role-based security reviews, backup schedule and dispute/administrator-recovery process. These require qualified review against applicable law and actual activities. The app's NGO verification badge must not be represented as an NGO finance audit or a guarantee of legal fundraising authority.

For sensitive general assistance inquiries in P0, implement minimal fields and tightly restricted routing; no beneficiary health records, identity dossiers, generalized case notes or public case boards before Phase 2 safeguarding policy and review.

PWC project fundraising and independent NGO donation *recording* are different things. Money-collection/payment processing and fundraising compliance remain [O/D] until approved operating/legal design. Never imply recorded payments are independently bank-verified.

Technical break-glass staff access should require a reason/ticket, explicit approval, expiration, minimum scope and immutable audit evidence; the Board does not inherit it by holding office.

### 15.1 Deployment/readiness checklist [R]

- DNS/TLS/domain and secrets management confirmed.
- Production DB credentials least privilege; privileged admin access separated.
- PostgreSQL backup retention and restore drill recorded.
- Private object storage and attachment access verified.
- Asynchronous job queue retry/dead-letter or failure procedures documented.
- Monitoring: latency/error rates, failed sign-ins, verification anomalies, role changes, financial posting errors, cross-tenant denial alerts and job backlog.
- Support: escalation path, administrator recovery, imports, export requests, security incidents and user communication templates.
- Privacy notice and platform agreement accepted by pilot participants.
- Rollback and incident response plan rehearsed.

## 16. Pilot execution and adoption

**[R]** Start with a small, representative pilot instead of a citywide invitation on day one. Suggested candidate cohort: at least one registered NGO, one eligible unregistered group, organizations using different membership admission policies, one with existing CSV/Excel rosters, one with two finance approvers, and one with direct-entry finance. Obtain permission for test data; prefer synthetic records for security and finance rehearsals.

Pilot journey: NGO onboarding → verify authority → import members/volunteers → configure categories and permissions → plan event/project → record dues and cashbook transactions → publish volunteer opportunities → complete PWC collaborative initiative → export relevant records. Gather friction points and audit evidence. Launch more widely only after pass/fail criteria and written PWC acceptance.

### 16.1 Suggested measurement framework [R]

| Area | Indicator (baseline and target TBD) |
|---|---|
| Onboarding | Time from initial organization draft to review-ready submission; verification backlog |
| NGO adoption | Number of verified active workspaces; active admin usage; successful imports |
| Participation | Activity applications, approvals, attendance confirmations |
| Collaboration | Requests issued, legitimate NGO approvals, completed joint tasks |
| Financial integrity | Unreconciled exception alerts, duplicate-post attempts rejected, pending approval age |
| Security | Unauthorized access attempts blocked, support-access review time, restore drill success |
| Quality | Error rate, crash-free sessions, median page/API latency, accessibility findings |

Do not invent baseline values or hard-code KPI targets until PWC sets its pilot scale and resources.

## 17. Dependency-aware backlog and build order

1. Baseline approval/ADRs and test matrix.
2. Repository, CI, environments, schema/version conventions.
3. Identity/session and tenant authorization kernel.
4. Organization verification, workspaces, role grants and secure admin recovery.
5. Member policy, records, imports and verified claims.
6. Membership dues source data and account/finance posting primitives.
7. Volunteer enrollments, opportunities, assignments and NGO activities.
8. Independent NGO projects, resources, tasks, milestones, budgets.
9. Complete restricted finance workflows, linkage, reversals and reports.
10. PWC membership, committees and proposal functions.
11. NGO collaboration/commitments and PWC project model.
12. Public mobile discovery/participation and notifications.
13. Pilot, hardening, release and transition to operations.

Parallel frontend work can begin earlier using approved API contracts; this list describes business dependency rather than a prohibition on concurrent design.

## 18. Work package ticket template

```text
Ticket: <M#-## / CORE-##>
Title:
Source documents + screen IDs:
Decision status: [S] / [R] / [O] / [D]
Actor + active context:
User goal:
Preconditions:
Expected state transitions:
API(s) + request/response/error samples:
Database entities and integrity constraints:
Authorization allow/deny matrix:
Audit events + notifications:
Client UI states (empty/loading/error/forbidden/offline):
Migration/backfill impact:
Tests (unit/integration/negative/E2E):
Acceptance evidence:
Dependency/owner/reviewer:
```

**Definition of completion:** Do not call a ticket done merely because its API returns 200 or the screen renders. Its domain permissions, state invariants, audit effects, error behavior and relevant tests must pass.

## 19. Risks, mitigations and phase gates

| Risk | Likelihood/impact (qualitative) | Mitigation / owner to assign |
|---|---|---|
| Ambitious multi-domain MVP causes schedule slippage | High / High | Vertical slices, stable gate criteria, exclude P1/P2 |
| Cross-tenant exposure | High impact | Central authorization, negative API tests, scoped files/exports/caches |
| Finance double posting or inconsistent dues | High impact | Unique sources, transaction locks, reversal and approval tests |
| Unauthorized NGO primary-admin claim | High impact | Provisional mode, categorized verification, documented recovery |
| NGO commitment created without approval | High impact | Versioned consent/approval proofs, stale-write rejection |
| Regulatory/fundraising misunderstanding | High impact | Legal review of operator, donation and charity activities before activation |
| Member/volunteer privacy leak on publication | High impact | Separate published projection, field-level guards, consent and QA |
| Complex configurable workflows become brittle | Medium–High | Restrict MVP to approved modes; state transition matrix |
| Data lock-in and difficult offboarding | Medium–High | Export and retention rules, rehearsed tenant deactivation |
| Weak production operations | High impact | Staging parity, backup/restore drill, on-call and incident procedures |

**Gate G0 — requirements/architecture ready:** product owner confirms provisional baseline for build purposes, unresolved blockers addressed, API/schema conventions accepted.  
**Gate G1 — M1 accepted:** identity/NGO trust and isolation proven.  
**Gate G2 — M2 accepted:** independently managed NGO operations and money correctness proven.  
**Gate G3 — M3 accepted:** three-sided collaboration and public participation proven.  
**Gate G4 — Pilot/public launch authorized:** operational, legal/privacy, UX and security review passed with accountable sign-offs.

## 20. Unresolved decisions requiring sign-off [O]

1. **PWC entity/legal compliance:** Registration/operating framework, financial and charitable activities, applicable data and retention duties. PWC operator selection is [S], but legal formalities are not approved.
2. **Web client stack and deployment:** Responsive Flutter Web versus a separate web framework; split of NGO vs PWC ops admin routes, hosting architecture.
3. **Authentication:** Phone OTP/email methods, age eligibility, recovery, session duration and provider choices.
4. **Organization verification evidence:** Required registered/unregistered documentation, SLA, escalation and disputed ownership process.
5. **PWC finance depth:** Whether PWC-owned finance needs the same cashbook features and exactly which grant/donation workflows activate at MVP.
6. **Finance access recovery:** NGO-chosen authorization methods and exact fallback when valid officeholders are unavailable.
7. **NGO commitment authorization:** One/multiple approval design, proof of delegation, deadline, amendment, withdrawal and dispute handling.
8. **Retention and export policy:** Periods, export formats, legal holds, record deletion/archiving and response timelines.
9. **Public inquiry safeguarding:** Allowed inquiry fields, intended recipients, retention and escalation.
10. **Language/accessibility:** Urdu/English launch commitments, translation ownership and assisted onboarding.
11. **Release/capacity planning:** Team size, available budget, target pilot cohort, hosting and expected concurrent users; no fixed delivery dates until known.
12. **Formal governance choices:** Legal constitution, first Board election mechanics and national/chapter relationship remain independently open and must not be invented by software design.

Decisions not required for a given milestone may remain open until that milestone's design gate, **but no unresolved high-risk privacy, finance, identity or authority rule may be waived to ship**.

## 21. Practical execution plan and next actions

1. Confirm this execution plan as the current **draft for engineering review** rather than an authorized delivery contract.
2. Create ADRs for hosting, web architecture, authentication, fixed-precision money, token/session policy and tenant isolation.
3. Turn CORE + M1–M3 work packages into issue tickets with owners, traces, tests and provisional estimates.
4. Establish CI and a staging environment; automate PostgreSQL-backed authorization regression first.
5. Complete the G0 decisions/contract freeze and commence M1 vertical-slice delivery.
6. Conduct pilot NGO workflow reviews at each milestone; revise only with controlled change decisions.
7. Release only after G4 evidence and explicit approval.

### Recommended first vertical slice [R]

**Create account → create/claim NGO draft → verify administrative authority → switch to NGO workspace → configure membership mode → invite or import one member → securely link membership → prove that NGO B and PWC Board cannot access it.**

This sequence proves the hardest architectural assumption—that PWC can operate one platform for many independent NGOs without crossing their trust boundaries—before money, public participation and joint-project commitments add complexity.

---

## Appendix A. Requirement → implementation → evidence map

| Requirement | Core implementation | Main test evidence |
|---|---|---|
| Personal account with multiple contexts | CORE-03/04, M1-01/02 | NGO A/B context switching |
| Provisional NGO verification | M1-03 | Existing org takeover denied |
| Distinct PWC institutional membership | M3-04 | Nonmember software NGO has no vote |
| Separate member and volunteer records | M1-05/06, M2-02/03 | Volunteer has no implied NGO membership |
| Import/secure claim | M1-06/07, M2-02 | No auto-created accounts; replay fails safely |
| Private finance access | CORE-04, M2-07/08 | NGO administrator without finance scope denied |
| Finance receipt integration | M2-01/09 | Exactly one source posting |
| Multi-cash/bank transfers | M2-07 | Zero new income/expense |
| NGO private/public visibility | M1-04, M2-04/05 | Members-only/private excluded publicly |
| Independent projects and budgets | M2-05/06 | No automatic PWC responsibility |
| Voluntary joint commitments | M3-07/08/09 | One NGO accepts, another declines |
| Alliance exit != platform closure | M3-11, CORE-06 exports | NGO private data unaffected by alliance resignation |

## Appendix B. Planning assumptions and document boundaries

- All architecture, schema, route, permission and workflow details require technical review before production use.
- The present plan does **not** claim software has been built, code has been audited, legal requirements have been satisfied or deadlines have been estimated from an actual team capacity plan.
- Time, staffing and costs intentionally remain unestimated until product owner supplies resource assumptions. Ticket effort estimates should be produced by implementing team after G0.
- Parent requirement sources are PWC planning drafts listed in §2, not the Coventure project artifacts.
- The original IA and screen specification remain authoritative for final screen ID spellings. This execution plan references them rather than duplicating all 72 screen definitions.
