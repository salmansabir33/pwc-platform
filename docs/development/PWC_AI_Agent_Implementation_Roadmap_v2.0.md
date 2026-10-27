# Pakistan Welfare Club (PWC)
## AI-Agent Implementation Roadmap v2.0 — Execution Baseline for Review
**Date:** 22 October 2026  
**Status:** Proposed execution sequencing; product and governance decisions remain provisional.  
**Repository:** `salmansabir33/pwc-platform`  
**Method:** Arena/Codex or equivalent agent; GitHub branch → tests → PR → human review → merge → sync locally.

## 0. Executive decision: what changes and what does not
This document **refines** the PWC Development Execution Plan v1.0, the M1 Engineering Backlog, and the architecture/screen specifications. It does not reduce the chosen P0 scope. M1, M2 and M3 **together** are the first public MVP; the phases below are smaller engineering delivery slices, not independent feature releases. Keep separate the institutional authority of PWC, the technical platform operator, and independent NGO administration.

**Current verified-by-report status:** PWC-01 completed on Arena branch `arena/9192ec62-pwc-platform`, commit `5c3c600`, PR open against `main`; eight backend tests reportedly pass on Python 3.11/PostgreSQL 16.2; GitHub Python 3.11/3.12 checks not yet confirmed passed; no PWC-02 code. The assistant has not independently inspected the PR diff. The initial local repository and GitHub remote exist. Do **not** redo PWC-01.

**Definition of 'approved':** Only a human-reviewed/accepted ADR or product decision becomes approved. An AI suggestion or an implementation commit alone does not approve governance, compliance, or high-risk business policy.

## 1. Work-management architecture

### 1.1 Five layers
1. **Strategic specification:** `docs/` planning foundations; requirement IDs and selected/provisional/open/deferred tags.
2. **Decisions:** `docs/decisions/` ADRs for specific high-risk technical choices; preserve source traceability.
3. **Implementation backlog:** one narrowly scoped ticket with dependencies, source screen IDs, allow/deny matrix, state transitions, API/data contracts, and acceptance tests.
4. **Agent implementation:** agent acts on `main` baseline in dedicated branch, changes only in-scope files, runs checks, documents uncertainty, opens PR; never autonomously merges.
5. **Human acceptance:** examine diff, CI, data migrations, privacy/security tests, demonstrated scenario, and unresolved items, then merge.

### 1.2 Standard branch/PR strategy
- Use ticket IDs `PWC-02A`, `PWC-02B`, `PWC-03A`, etc. Branches such as `agent/pwc-02a-auth-adr`; Arena-generated immutable session branches are acceptable.
- One PR per coherent vertical slice, ideally reviewable without mixing infrastructure, finance, frontend and unrelated redesign.
- A phase can have several tickets; **do not put the entire phase in one agent prompt**.
- Changes touching a shared contract must update OpenAPI/schema, server, affected clients and tests together, or explicitly split into contract-first and implementation PRs with stable versioning.
- Up-to-date base required. If a predecessor PR is unmerged, do not silently assume it is on `main`. Await its merge or clearly identify an explicit dependent branch strategy.
- No fabricated test passes; distinguish `not run`, `passed`, `failed`, and `blocked`.
- Clean and auditable commits; no autonomous direct pushes to `main`, force pushes, destructive reset or schema/data deletion.

### 1.3 Agent prompt efficiency principles
- State desired **outcome**, not hundreds of prescriptive code lines; reference exact source documents and screen IDs.
- Require agent to inspect actual repository before changes; no assumption that scaffolding is implemented.
- Specify hard scope limits, no-go security invariants, test matrix and reporting format.
- Give autonomy for local implementation details within approved architecture; require ADR for unresolved decisions rather than asking the user for every code detail.
- Do not ask an agent to 'implement PWC' or 'all M1' in a single session. Avoid open-ended refactors and duplicate documentation.
- Require test evidence for *negative authorization* as well as happy-path behavior.
- Reuse root `AGENTS.md`; task prompts add deltas instead of repeating all standards.

## 2. Phase map, dependencies and release gates

| Engineering phase | Parent milestone | Goal | Main prerequisite | Acceptance gate |
|---|---|---|---|---|
| **P0 — Repository integration** | Foundation | Merge verified PWC-01 and get green CI | Existing PWC-01 PR | G0a: main CI clean; local sync |
| **P1 — Decision & contract freeze** | Foundation | Auth, scoped access, web choice, API conventions | P0 | G0b: blocking ADRs accepted |
| **P2 — Identity & access kernel** | M1 | Personal auth + contexts + tenant-secure APIs | P1 | G1a: auth/revocation/isolation tests |
| **P3 — NGO onboarding & verification** | M1 | Create/claim/verify org; scoped admin authority | P2 | G1b: takeover/provisional tests |
| **P4 — NGO membership & M1 UI** | M1 | Policies, applications, imports, secure claims, first full slice | P3 | **G1: M1 accepted** |
| **P5 — NGO activities, volunteers & projects** | M2 | Volunteer operations, events, private projects, tasks/budgets | G1 | G2a: independent NGO workflows |
| **P6 — Dues & private NGO finance** | M2 | Accurate money ledger, configured approvals, idempotent receipts, reports | P4 + P5 where linked | **G2: M2 accepted** |
| **P7 — Alliance, collaboration & citizen app** | M3 | Institutional PWC membership, committees, explicit commitments, discovery | G1, projects from P5 | **G3: M3 accepted** |
| **P8 — Security hardening, pilot & launch** | MVP release | Operations, accessible UX, restore drill, legal/policy and pilot approval | G1–G3 | **G4: first public MVP authorized** |

**Sequencing flexibility:** Build UI shell/design tokens and API contract consumers early once contracts are stable. After tenant-scoped authorization exists, independent volunteer/project and finance workstreams may run in parallel on separate branches with coordinated migrations. Never parallelize work that changes the same ownership/permission contracts without coordination.

## 3. Ticket roadmap: concrete coding-agent assignments

### P0 — Integrate PWC-01 (one human gate, not a coding task)
- `PWC-01-REVIEW`: inspect PR's `AGENTS.md`, two additive migration files, security hygiene, pinning, CI; confirm Python 3.11/3.12 checks green. Merge only when accepted.
- `PWC-01-SYNC`: `git switch main && git pull --ff-only origin main`; confirm clean tree and `AGENTS.md` is present.
- **Output:** trusted branch baseline. **Never re-run** completed audit as a new task.

### P1 — Decisions/contracts (small design PRs, then selective approvals)
- `PWC-02A`: Authentication ADR: login identity (email/password vs phone OTP/hybrid), verification, delivery dependency, recovery, session/token strategy for mobile/web, revocation, abuse/MFA; no code. **Blocking P2.**
- `PWC-02C`: Tenant authorization ADR and API convention: context semantics, denied-by-default capability registry, queryset/object/file/export checks, revocation, 403/404 decision, error envelope, idempotency/version expectations. **Blocking P2.**
- `PWC-02D`: Web delivery ADR: responsive NGO portal and segregated PWC operations portal technology, shared OpenAPI contracts, deployment/auth approach; implement no web UI until chosen. **Blocking web implementation only.**
- `PWC-02E`: M1 NGO verification policy review pack: tiered registered/unregistered evidence, authorized representative review, duplication/contested ownership, safe provisional capability. **Blocking the approval/activation branch of P3.**
- `PWC-02F`: Dev environment contract: Django/Python/PostgreSQL version matrix, migrations & CI, formatter/linter policy, test fixtures; no gratuitous re-scaffolding.
- **Gate:** Decision register identifies which choices are explicitly accepted, open, or deferred. Avoid coupling unrelated legal decisions to ordinary model scaffolding when no real blocker.

### P2 — Secure identity & authorization kernel (M1)
- `PWC-03A`: Implement account registration/sign-in/verification/recovery/session lifecycle **against PWC-02A** with DRF endpoints and negative/abuse tests; `ID-01`, `ID-02`, `ID-05`. No NGO features.
- `PWC-03B`: Context-aware scope/grant/capability service, denied-by-default tenant-filtered access, revocation; synthetic NGO A/B fixture matrix; `ID-03`, `ID-04`; no generic `isAdmin` shortcuts.
- `PWC-03C`: API contract generation/schema/error conventions, audit-event foundation, file-access primitive and authorization regression harness; scoped infrastructure only.
- `PWC-03D`: Flutter bootstrapping + session + workspace shell, secure credential handling, personal tab navigation and context-clear-on-switch test; no premature finance UI. Block if runtime/platform support unavailable; report exact limitation.
- **G1a tests:** forged/suspended sessions rejected; revoked roles lose access; NGO A cannot enumerate/read/write NGO B; PWC-only Board role cannot obtain NGO private privileges; client context switching never renders prior NGO cache.

### P3 — NGO trust, onboarding and administration (M1)
- `PWC-04A`: Organization register/search/dedup/draft/claim state machine and limited provisional workspace; `ORG-01`,`ORG-02`; stop existing tenant takeover.
- `PWC-04B`: Revised initial rollout (product owner, 27 October 2026; ADR-0004 §7 / PWC-02E §9): offline evidence examination, controlled NGO/nomination recording by a specifically authorized platform operator, independent distinct-officer approval, recipient-bound nonfinance invitation/acceptance preparation and audit. No public NGO self-registration/claims or raw uploads. Organization legitimacy remains **separate** from representative authority; `ORG-03`, `PWC-01`. Exact reviewer-root/command/IAM/privacy/invitation contracts still gate affected implementation; grant activation remains 04C/03B.3. Earlier in-app tiered intake/queue/private-attachment direction is superseded for initial rollout, not erased from historical decisions.
- `PWC-04C`: Scoped roles, grants, team invitations and revocation; primary-admin transfer/recovery via approved evidence/policy; `ORG-06`, `ORG-25` relevant subset. No implied finance grants.
- `PWC-04D`: Published-only NGO profile/editor and NGO overview; approved leadership visibility only; `ORG-04`, `ORG-05`, `PUB-04`.
- **G1b:** disputed claim cannot seize existing workspace; provisional user cannot import/finance; public profile contains no private roster; technical/platform versus alliance permissions remain separate.

### P4 — NGO members/imports and complete M1 walkthrough
- `PWC-05A`: NGO-configured Open/Approval/Invitation admission, categories, member applications/invites, membership state; `ORG-07`–`ORG-09`, `ORG-12` *membership-policy only*; fees defined as configuration but **payment posting remains P6**.
- `PWC-05B`: Manual member records + CSV/XLSX staged preview/dedup/error report, idempotent commit, no auto-created `User`; `ORG-10`. Use synthetic files in tests.
- `PWC-05C`: Secure imported-member claim with verified identity + single-use expiring token or approved NGO review; replay, collision, expiry and cross-NGO negative tests; `ORG-11`.
- `PWC-05D`: M1 mobile/web integration for onboarding/membership/role actions, type-safe contract, loading/empty/403/409 states; initial NGO web portal after PWC-02D approval.
- `PWC-05E`: M1 end-to-end demo, two NGO fixtures, accessibility/basic localization checks, cross-role security suite; document evidence and deviations.
- **G1 M1 exit:** one person registers, claims/creates verified NGO, configures policies, imports/invites, member claims; NGO B and PWC Board are denied access to NGO A private records across API/search/file/export; role revocation immediate.

### P5 — NGO operational workflows (M2; can be split into independent streams)
- `PWC-06A`: Standing volunteer enrollment policies, manual/imported unclaimed volunteers, separate claim pathways; `ORG-14`,`ORG-15`.
- `PWC-06B`: Opportunities, applications, assignments/attendance, screening of sensitive assignments; `ORG-16`,`ORG-17`,`PUB-06`,`PUB-09` relevant subsets.
- `PWC-06C`: Events/activities (Public/Members Only/Private), registration, attendance, announcements; `ORG-18`,`ORG-23`.
- `PWC-06D`: Independent NGO projects, teams and project ownership/visibility; `ORG-19`,`ORG-20`.
- `PWC-06E`: Tasks, milestones, resource requirements and planned budget lines, project updates; `ORG-21`,`ORG-22`. Do not leak financial actuals to project managers.
- `PWC-06F`: Responsive NGO web + mobile routine flows, basic operational reports/export; `ORG-24` permitted scope.
- **G2a:** volunteer enrollment is not NGO membership; opportunity application does not silently enroll as volunteer; private activities/projects and participant details stay private; project budget != recorded expenditure.

### P6 — Dues and NGO restricted finance (M2; highest-risk scope)
- `PWC-07A`: **Finance ADR first**: decimal/currency, account opening balances, finance-specific grants/recovery, direct vs maker-checker approval, source/receipt status and reversals. Block financial writes until approved.
- `PWC-07B`: Tenant-private financial accounts, money transaction header/legs, cashbook entries, balance rules, transfers and reversal primitive; `FIN-01`,`FIN-02`,`FIN-04`,`FIN-05`,`FIN-07`.
- `PWC-07C`: Approvals: NGO chosen direct-entry or distinct maker/checker; finance permissions independently granted, immutable decisions, policy changes do not auto-post; `FIN-06`,`FIN-09`.
- `PWC-07D`: Dues periods, fees, assessments, waivers/discounts/exemptions, partial payments and renewals; `ORG-12`,`ORG-13`.
- `PWC-07E`: Donation receipts/confirmed dues source-to-ledger exactly-once link, atomic idempotency, concurrency/retry and pending-vs-posted semantics; `FIN-03`.
- `PWC-07F`: Finance reports & explicit restricted exports; mobile/web status accuracy; `FIN-08`.
- `PWC-07G`: Finance acceptance matrix, PostgreSQL concurrency tests, NGO A/B and PWC roles deny suite, transfer/reversal checks, pilot cashbook rehearsal.
- **G2 M2 exit:** recorded balance math correct; transfer produces 0 new NGO income/expense; pending approval excluded; no maker self-approval in approval mode; duplicate receipt retry never double-posts; no finance access merely via NGO admin or PWC alliance role.

### P7 — PWC alliance, citizen app, voluntary collaboration (M3)
- `PWC-08A`: PWC institutional application/admission and authorized organization representatives; registered full institutional voting eligibility **recorded** but electronic elections deferred; `ALL-01`–`ALL-03`, `GOV-01` limited.
- `PWC-08B`: Committee profiles, membership, meetings, announcements and proposals; `COM-01`–`COM-04`, `PWC-03`.
- `PWC-08C`: Public discovery search/filter, public-only projections, notices and safe general inquiries (not formal beneficiary case management); `PUB-01`–`PUB-08`, `PUB-10`.
- `PWC-08D`: Collaboration requests and offers with explicit scopes; `COL-01`,`COL-02`.
- `PWC-08E`: Versioned NGO commitments, one/multi-authorizer per NGO, delegation checks, stale approval invalidation, amendment/withdrawal workflow per approved terms; `COL-03`,`COL-04`.
- `PWC-08F`: PWC-led/joint project workspace, independent attribution of PWC money and NGO resources; `COL-05`, `PWC-04`,`PWC-05`. PWC project approval does not create an NGO commitment.
- `PWC-08G`: PWC operations and alliance-versus-platform staff separation, safe member/NGO withdrawal and authorized exports; `PWC-02`, `OPS-01` scoped.
- `PWC-08H`: Full Android/Flutter public-to-participation journey, committee→PWC→two NGO scenario, web portal integration; fix integration defects.
- **G3 M3 exit:** one citizen volunteers; committee submits proposal; NGO A accepts under its own approver policy, NGO B declines without penalty to unrelated membership; PWC never receives unrelated member rosters/finances; platform exit distinct from alliance exit.

### P8 — Readiness, pilot, deployment (no public launch without sign-off)
- `PWC-09A`: CI required checks for backend, Flutter and web; dependency vulnerability/secret scanning, permission negative tests, docs/schema drift controls.
- `PWC-09B`: staging environment with non-production data, monitored services, protected attachment storage, backups and observed restoration exercise.
- `PWC-09C`: privacy, terms, lawful PWC operations/fundraising/legal form review; verification policy; retention/export/deactivation rules; public inquiry safeguarding and incident response. Human/legal sign-off required.
- `PWC-09D`: usability/accessibility/Urdu readiness review, pilot NGOs with different membership and finance policies, defects and UAT evidence.
- `PWC-09E`: release checklist, rollback plan, support/account recovery, monitoring and go/no-go decision.
- **G4:** Pilot/public launch requires security, operations, data/privacy, legal/compliance and product acceptance. No fixed dates or performance promises without team/capacity data.

## 4. Dependency rules for efficient parallelism
- **Always serial:** accepted auth ADR → auth code; tenant policy → protected NGO data; NGO verification → admin/member writes; finances ADR → ledger; commitment approval contract → NGO binding acceptance.
- **Parallel after P2:** design system/web portal shell; public published content; test fixture factories, CI; cautious independent volunteer/event and project services.
- **Parallel after P4:** NGO volunteers/events/projects and finance ADR; never work simultaneously on conflicting membership schema migrations without integration planning.
- **Parallel after G1/P5:** alliance committee domain and public discovery; collaboration approvals wait for project authority and NGO delegate model.
- **Merge discipline:** short branches, small PRs, main-based rebase/integration review, CI required; cross-cutting schema changes coordinate via contract-first PR.

## 5. Standard task contract (must accompany each agent prompt)

```text
Ticket / title:
Repository and base branch:
Goal (one vertical capability):
Source docs and canonical screen IDs:
Prerequisites (accepted ADR, merged PRs):
Scope IN / Scope OUT:
Actors, authorization, tenant/record ownership:
Required data/API/UI changes:
State transitions, idempotency and audit evidence:
Required success and negative tests:
Execution checks and exact environment limitations:
Documentation/migration expectations:
Final report / PR acceptance evidence:
```

**Task definition of done:** (a) authorized change scope, (b) meaningful working behavior not scaffolding alone, (c) unit/integration and adversarial tests, (d) safe migration/reversal where applicable, (e) versioned contract/update, (f) clean diff and CI, (g) truthful report, (h) PR submitted and not merged.

## 6. Reusable *efficient* agent prompt header

> You are the engineering agent for `salmansabir33/pwc-platform`. Work only on ticket **[ID]**. Start from the latest approved `main` and read root `AGENTS.md` and the **relevant** product/architecture sources in `docs/`. Inspect existing implementation and tests before coding; continue rather than rebuild. Follow the canonical screen IDs and documented provisional/approved/open/deferred decision statuses. Do not silently decide open legal, privacy, finance or governance policy. Implement only the specified end-to-end slice, including backend permission checks, migrations (when needed), API contract, client behavior (when in scope), audit and negative tests. Preserve unrelated files and never introduce real secrets/data. Run relevant checks and report commands/results honestly. On a dedicated branch, commit scoped changes and open a PR; never merge into `main` automatically. If blocked, report exact blocker and complete safe, independently valuable portions without inventing a successful test.

## 7. **Next prompt** — PWC-02A authentication ADR (ready after PWC-01 merge)

### Ticket: PWC-02A — Authentication, sessions and recovery ADR (design only)
**Goal:** Resolve the blocking identity/security design so coding can start confidently.

**Prompt to paste into Arena:**

> You are working on `salmansabir33/pwc-platform`, ticket **PWC-02A**, based on the latest **merged** `main`. Before beginning, verify the PWC-01 PR changes (including root `AGENTS.md`) exist on `main`; otherwise report the blocker rather than recreating them. Read `AGENTS.md`, the relevant Strategy, Identity/Authorization, Django Backend, Flutter Frontend and Execution Plan documents. Inspect the actual `accounts` model, dependency pins and REST scaffold. **Design only: do not write auth endpoints, change models, create migrations or edit product specifications.** Create one ADR under `docs/decisions/` evaluating email/password + verification, phone OTP and hybrid login appropriate for Pakistan; choose an explicitly recommended MVP default with tradeoffs, costs/provider dependencies and migration path, but mark any provider/pricing/legal decisions requiring confirmation. Specify session lifecycle for Django API, Flutter and web; access/refresh credential rotation/revocation; login/logout; email/phone verification; rate-limits, enumeration defense, password/contact recovery, step-up auth for NGO-admin/finance/platform ops, device sessions, secure logs and error contracts. Map the design to `ID-01`, `ID-02`, `ID-05`; preserve the principle that authentication never confers NGO/PWC rights. Include API-level request/response/error sketches, threat/negative-test matrix, transition plan from the current User model, and a split PWC-02B implementation backlog. State each unresolved blocking decision as an explicit review item. Commit ADR only, open a PR, **do not merge**. Report branch/commit/PR, exact reviewed sources, implementation implications, and decisions needed before coding.

### Review checklist for PWC-02A
- Every recommended method can be implemented/tested without silently depending on unapproved paid SMS delivery.
- Mobile/web token/session storage is differentiated correctly.
- Recovery does not equate phone ownership to NGO organizational authority.
- High-risk admin/finance reauthentication is handled as a separate condition.
- NGO/PWC role grants cannot be forged through identity verification.
- Decisions remain draft until human approval.

## 8. Next PR sequence immediately after accepted ADRs
- PWC-02C tenant authorization ADR (can run in parallel with PWC-02A if separate changes and no conflicting base).
- PWC-02D web-client ADR (independently parallelizable).
- PWC-03A auth backend (after 02A acceptance).
- PWC-03B scoped access service (after 02C and auth identity assumptions).
- PWC-03D Flutter personal/account shell (contract-first after 03A).
- PWC-04A organization provisional/claim lifecycle (after scoped access).

## 9. Protect against common AI-agent failure patterns
- **False 'done':** Work incomplete without access denials, migrations, contract and integration where ticket requires them.
- **Big-bang task:** Never assign complete M1/M2/M3 in one request.
- **Unapproved design:** PWC governance/legal issues marked open; agent can recommend ADR but not implement constitutional elections or fund processing without review.
- **Broken tenant boundary:** No global NGO business admin shortcut, privileged Django Admin access or weak client-only guards.
- **Simulated finance correctness:** Must test PostgreSQL real transactions, concurrency and idempotency; no floating point balances.
- **Cross-branch collisions:** Dependent PRs integrate on accepted baseline and update migrations/contracts deliberately.
- **Unrealistic environment:** Local Snap Docker issue is not a blocker for cloud-tested tasks; CI/staging validation required; never claim local Docker is verified when it isn't.
- **Unnecessary docs churn:** Keep one issue/ADR and meaningful changes; avoid large duplicated plans every ticket.

## 10. Traceability and change control
Each PR description should link: work package ID → product scope and screen IDs → domain models → API schema → test evidence → deployment/migration effect → pending decisions. Change product scope only through explicit product-owner approval; update planning artifacts when approved. Preserve M1/M2/M3 completeness and deferred items until reviewed. This roadmap is the **operational work breakdown**, while the strategic foundation remains the authority for business intent.


---

## 11. Execution reconciliation and approved deviations — 27 October 2026

**Status:** Roadmap v2.0 remains the controlling P0–P8 / PWC-01–PWC-09 execution structure. This addendum records observed GitHub merge evidence and approved product changes; it does **not** silently declare gated features complete or retroactively rewrite the 22 October baseline. Original section 0's PWC-01/open-PR snapshot and sections 7–8's suggested next tasks are **historical as of 22 October** and are superseded for current scheduling by the dated status below. Original M1/M2/M3 first-public-MVP scope, canonical IDs, and human/security gates remain in force.

### 11.1 GitHub delivery ledger (verified against PR metadata on 27 October 2026)

| Roadmap item | GitHub evidence | Reconciled status / difference from original ticket |
| --- | --- | --- |
| P0 / PWC-01 | PR #1 merged; PR #2 added roadmap execution authority | Foundation merged, not still pending as original §0 snapshot states. |
| P1 / PWC-02A, 02C, 02D | ADRs and dependent implementations referenced by PRs #3–#5 | Relevant architectural decisions were adopted; do not interpret technical ADR approval as live auth/NGO authority approval. |
| P1 / PWC-02E | PR #8 merged; product owner disposition PR #10 merged | Architecture and owner-specific options recorded; several E/GM/REAL security/operations/legal decisions remain implementation or activation gates. |
| P1 / PWC-02F | PR #9 merged | Environment/security tooling foundation delivered. |
| P2 / PWC-03A | PR #3 merged | Backend personal identity/auth foundation, operational delivery/production still gated. |
| P2 / PWC-03B | PR #4 merged | Synthetic, deny-default tenant authorization foundation; **PWC-03B.3 real privileged grant/authority mutations remain blocked**, not completed by synthetic tests. |
| P2 / PWC-03C | PR #6 merged | Canonical API contracts and cross-platform contract testing foundation. **Deviation / outstanding original scope:** broad shared audit-event and protected file-access primitives from original 03C were not thereby delivered as generalized services; carry them forward as explicit prerequisites in relevant slices, not assume completion. |
| P2 / PWC-03D | PR #7 merged | Flutter identity/shell foundation; live-networking/real-user acceptance remain gated. |
| Cross-cutting W1 web foundations | PR #5 merged | React/TypeScript/Vite NGO and Operations shells delivered **early** under ADR-0003's permitted sequencing flexibility; W1 is not a replacement/new numbered phase and is not live integration. |
| P3 / PWC-04A | PR #11 merged | Registry/claim/provisional engineering foundation retained; **initial-rollout applicant-driven registration/claim submissions were later closed server-side** by revised 04B policy. Historical data/read/withdrawal preserved. |
| P3 / PWC-04B | PR #12 (initial safely gated preparation), then PR #13 (revised offline controlled-onboarding preparation), both merged | **Approved scope change:** external organization/representative verification; authorized Super Admin initiates records, separate officer approves; no in-app evidence upload or public NGO self-onboarding in initial rollout. PR #13 delivers records/audit and disabled adapters/UI, **not** live reviewer commands, authority or invitations. Original ticket §3 P3 description is superseded for initial rollout by the revised PWC-04B row already present above and ADR-0004 §7. |
| Cross-cutting UI design standard | PR #14 (source documentation), then PR #15 (React/Flutter design foundation), merged | **Early authorized UI foundation**, not a new P0–P8 or PWC-numbered subphase. Design standard is `docs/design/PWC_DESIGN_SYSTEM_v1.0.md`; apply to all subsequent UI. Manual screen-reader, native Urdu/device, zoom, iOS and performance acceptance remain outstanding; design foundation is not feature completion. |
| P3 / PWC-04C product governance | PR #16 merged | Initial offline appointments of Super Admin and independent Verification Officer by PWC's formally designated founding platform authority accepted **at product level only**; initial platform operator IAM/bootstrap/assurance remain blocked pending independent approved contracts. |
| P3 / PWC-04C nominee acceptance | PR #17 **open/unmerged as of this audit** | Product-owner-approved recipient-bound, one-use, max-72-hour invitation and separate explicit nonfinance acceptance documented in the PR; do not claim it is on `main` until merged. Real invitation/acceptance/grant commands remain blocked. |
| P3 / PWC-04C implementation, 04D | No completion PR evidenced in reviewed #1–#17 history | Not implemented as live business capabilities; keep P3/G1b incomplete. |
| P4–P8 / PWC-05 to PWC-09 | No completion PR evidenced in reviewed #1–#17 history | Not started/accepted as complete; milestones G1/G2/G3/G4 remain unmet. |

This is a **PR/history and documentation-scope audit**, not an independent line-by-line implementation certification. Merged means integrated, **not** operationally live or all acceptance gates met.

### 11.2 Approved changes versus deviations requiring closure

1. **PWC-04B product change — accepted:** The original self-service / document-upload approval path was replaced, for initial rollout, with offline NGO/representative evidence examination, Super Admin preparation and independent Verification Officer approval. Maintain E01 registered/informal standards, organization-versus-mandate separation, no private access implied by platform title, and no finance/signatory powers. See ADR-0004 §7, verification decision register §9 and PWC-04B runbook/review. Do not re-enable self-service by relying on §3's older PWC-04A wording.
2. **W1 / design system early delivery — permitted sequencing variance:** ADR-0003 allowed early web shells, shared UI tokens and design components; PRs #5 and #15 provided those foundations while preserving separated web origins and disabled transport. This does not complete the M1 first functional UI path, which remains PWC-05D/05E acceptance and approved networking dependent.
3. **PWC-03C reduction — partial delivery:** Contract/schema foundation was delivered, but generalized audit/file-access infrastructure was not included in that PR. Each future relevant subphase must identify and implement or explicitly gate necessary audited/file primitives. Do not mark original PWC-03C breadth as fully closed without a traceable contract change and tests.
4. **PWC-03B real command sequencing — open blocker:** PWC-03B.3 and the E/GM/REAL registers continue to block real platform operator/reviewer provisioning, invitation authority, first NGO nonfinance grants and recovery. The 04B default-off engineering foundation is not sufficient evidence of P3 completion. Finalize exact separate accountable approvals before allowing corresponding implementation.
5. **PWC-04C product decisions — accepted, technical scope pending:** Founding platform authority's offline signed appointments (PR #16) and product-level 72-hour nominee invitation/explicit acceptance (PR #17 pending merge) are recorded product changes. They do not substitute for issuer/target IAM, assurance, grant writer, privacy, notification, conflict/quorum and recovery contracts.
6. **Design-system governance — approved:** Future React and Flutter implementations must follow `docs/design/PWC_DESIGN_SYSTEM_v1.0.md`, reuse shared components, report screen coverage and distinguish UI-only/gated/demo from integrated features. Preserve unresolved manual acceptance in P8/PWC-09D.

### 11.3 Remaining roadmap and gate status

- **G0a/G0b:** Foundation PR/ADR work merged in part; cross-owner, operations and production approvals remain **open**. Do not equate merger of an ADR with all G0b sensitive policy gates closing.
- **G1a:** Synthetic authorization and identity tests exist; end-to-end real authority proof, integration/security acceptance and operational gates remain outstanding.
- **P3/G1b:** Offline trust foundations merged; real operator/reviewer provisioning, independent approval actions, exact nominated-recipient invitation, initial nonfinance grant activation, restricted public projection, and contested recovery are not yet authorized as completed. PWC-04C/04D must account for these.
- **P4/G1:** Member management and functional M1 frontend/integration acceptance pending; adapt the legacy G1 demo text (“user ... claims/creates verified NGO”) to the approved **externally verified, PWC-operated onboarding model**, without reducing membership scope or tenant isolation tests.
- **P5–P7/G2/G3:** Volunteers, projects, finance, alliance governance and citizen participation pending under their original tickets.
- **P8/G4:** Deployment, privacy/legal, real-device accessibility/Urdu and pilot sign-offs remain mandatory.

### 11.4 Mandatory change-control procedure for every future slice

Every Arena/Codex subphase must reconcile: **roadmap ticket → latest dated product/ADR decisions → canonical screens → implemented server/client/API/test coverage → pending gates → PR diff/CI**. Report deviations as **approved scope change**, **sequencing variance**, **partially implemented**, **deferred/open**, or **unauthorized deviation requiring correction**. Obtain explicit product-owner approval to change original P0–P8 or M1–M3 coverage; preserve original source/history; amend roadmap/status and linked decision records **in the same PR as the affected implementation**, or in a clearly linked preceding documentation PR. Never quietly redefine unfinished work as complete. One comprehensive engineering assignment per lettered subphase remains the preferred user handoff; ordinary incremental commits/internal reviews are not extra user-facing phases.

**Source links:** [ADR-0004](../decisions/ADR-0004-ngo-verification-and-representative-authority.md); [PWC-02E E register](../reviews/PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md); [PWC-03B.3 register](../reviews/PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md); [PWC-04C founding appointment](../reviews/PWC-04C-INITIAL-PLATFORM-APPOINTMENT-DECISION.md); [Design System](../design/PWC_DESIGN_SYSTEM_v1.0.md).
