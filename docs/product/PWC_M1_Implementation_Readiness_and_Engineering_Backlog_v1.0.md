# Pakistan Welfare Club (PWC)
## M1 Implementation Readiness & Engineering Backlog v1.0 — Draft for Review

**Status:** Engineering planning draft; not implementation approval.  
**Basis:** PWC Strategic & Product Foundation v1.0, Information Architecture v1.0, Detailed Screen Specification v1.0, Identity/Authorization/Data Model v1.0, Django/PostgreSQL Foundation v1.0, Flutter Frontend Architecture v1.0, Development Execution Plan v1.0.  
**Scope:** M1 (secure institutional foundation) and necessary cross-cutting CORE work.  
**Important:** No source repository has been supplied or modified; task estimates, owners, hosting and release dates are not assumed.

## 1. Delivery goal

Demonstrate one end-to-end safe workflow: **create account → register or claim a provisional NGO workspace → verify NGO authority → configure NGO membership policy → invite/import member → claim that member securely → switch between NGO contexts → prove unauthorized access is denied.**

M1 must prove *independent NGO administration* without making NGOs subsidiaries of PWC. PWC's alliance role grants no routine access to NGO-private member, volunteer, internal project or finance records. Platform support privileges must be independently governed, narrowly scoped, time-bound and logged.

## 2. Decisions versus recommendations

- **Provisional product selections:** PWC operates platform; eligible nonmember NGOs may use basic software; verification paths differ for registered/unregistered entities; limited provisional workspace; NGOs configure membership mode (open/approval/invitation); bulk CSV/Excel import; secure record claiming; NGO-scoped roles; one user can act for multiple NGOs; PWC alliance membership is independent.
- **Recommended implementation:** Django/DRF + PostgreSQL modular backend; Flutter mobile with typed API client; versioned OpenAPI; feature/role-scoped web portal; server-side tenant predicates; separate authenticated actor vs active workspace context; structured audit events; jobs/outbox for potentially long-running imports/notifications.
- **Not finalized:** NGO evidence checklist; OTP/email authentication and recovery providers; web portal framework; verification operators and escalation; retention/deletion policies; hosting/deployment; timeline, engineering owners and budget; Urdu availability; operating entity's legal/regulatory details.

## 3. Proposed code boundaries (subject to repository review)

```text
apps/backend/        Django API; modular apps: identity, organizations, authorization, ngo_membership, pwc_membership, audit, notifications
apps/mobile/         Flutter public and NGO workspaces
apps/ngo-web/        NGO admin portal (framework open)
apps/pwc-ops/        Segregated PWC/platform operations interface (framework open)
packages/api-contracts/  OpenAPI and typed client generation
docs/decisions/      ADRs; open decision register
tests/               Backend, security, API-contract, and E2E scenarios
infra/               Local/staging/prod config, backup/restore and runbooks
```

**Architecture constraint:** Django Admin must not accidentally expose NGO-private data to unscoped alliance staff; organization-scoped domain APIs must enforce permissions on the server.

## 4. Engineering backlog (M1)

| Ticket | Work package | Prerequisites | Deliverable and acceptance evidence |
|---|---|---|---|
| CORE-01 | Repository baseline, lint, CI and test services | Repo access | CI runs Django tests, format/lint, migration checks and Flutter checks; no secrets committed |
| CORE-02 | PostgreSQL environments, secret and backup design | CORE-01; hosting decision | Environment separation; staged restore rehearsal; no real beneficiary/member data in staging |
| CORE-03 / M1-01 | Personal user, verified contacts, login, logout, session recovery | Authentication ADR | Valid/invalid/expired/revoked credentials tested; secure token storage in client |
| CORE-04 / M1-02 | Active NGO context and authorization kernel | CORE-03 | Actor + selected tenant + permission checked for each endpoint; NGO-A/NGO-B isolation tests pass |
| M1-03 | NGO registry, provisional draft, duplicates, claim review and verification | CORE-04; evidence policy | No existing NGO private data visible to claimant; separate org verification and rep authority decisions |
| M1-04 | Public projection, leader publication controls | M1-03 | Ordinary members never public by default; public directory only approved fields |
| M1-05 | NGO settings, categories, applications, invitations, membership states | CORE-04 + M1-03 | Open/approval/invitation enforced on server, including direct API attempts |
| M1-06 | Unclaimed existing members: manual entry, CSV/XLSX parsing, preview and import | M1-05; storage/import policy | Duplicate/error preview; safe replay; zero auto-created auth users; no cross-tenant row access |
| M1-07 | Claim tokens, verification and NGO approval fallback | M1-06 + contact verification | Single-use expiring token; verified claimant; mismatched/expired/replay denied; membership history preserved |
| M1-08 | NGO admin/team grants and authority recovery | CORE-04; recovery decision | Role revocation; controlled primary-admin transfer; no self-grant of restricted finance privilege |
| M1-09 | NGO dashboard initial restricted metrics | M1-05 | Member counts only from active tenant and permitted scope |
| CORE-05 | Audit events, mutation idempotency and jobs | CORE-04 | Authority changes, imports and claims audited; retries cannot create duplicates |
| CORE-06 | Private attachment/document access foundation | CORE-04 | Presigned or proxied access scoped and expiring; no public URLs to private evidence |
| CORE-09 | Versioned OpenAPI contract and typed clients | CORE-03 | Contract fixtures, typed error/status states and CI checks |
| M1-10 | End-to-end M1 demo, security review and UAT | All applicable M1 tickets | Two-NGO scripted demo + negative access suite + exit evidence signed off |

**Suggested sequence:** CORE-01/02 → CORE-03 → CORE-04 → M1-03/04/08 → M1-05 → M1-06/07 → M1-09/10, with CORE-05/06/09 integrated as dependencies. UI flows may be prototyped in parallel against an approved API contract.

## 5. Minimal M1 domain entities

- **User / VerifiedContact / Session**: one human identity; contact verification and session lifecycle.
- **Organization**: stable organization identity, public verification indicators, current operating status; an organization's legal registration is separate from platform verification.
- **OrganizationClaim / VerificationCase**: provisional claim, evidence pointers, claimant authority, reviewer decision and history.
- **OrganizationPolicy**: organization-specific member admission mode and later extended settings.
- **OrganizationRelationship / RoleGrant**: authorized links between user and NGO; permission grants with effective/revoked state.
- **MembershipCategory / NGOIndividualMembership**: member status/category distinct from administrative permissions.
- **MembershipApplication / Invitation**: individual request and NGO approval/acceptance events.
- **ImportedMemberRecord / ImportBatch / ClaimToken**: unclaimed records; staged validation and secure linkage.
- **PWCMembership**: independent institutional PWC membership; no automatic coupling with platform eligibility.
- **AuditEvent / FileReference / Notification**: cross-cutting security and traceability components.

Use explicit foreign keys, restrictive uniqueness and tenant-context checks. Do not permit client-supplied organization IDs to bypass server authorization; reject mismatched object and path organization contexts. Exact column definitions and indexes must be finalized against the backend foundation and actual codebase.

## 6. Authorization decision examples

| Actor + context | Action | Expected |
|---|---|---|
| Unverified NGO claimant | Read existing organization's member list | Denied |
| Verified NGO-A membership officer | Review NGO-A application | Allowed if granted |
| Same officer in NGO-B context | Read NGO-A member record | Denied |
| PWC Board member | Export NGO-A private roster | Denied without independent, valid NGO authorization |
| NGO-A membership officer | Read NGO-A finance data | Denied unless separately granted finance scope |
| Authenticated member | Claim existing record using name-only match | Denied |
| Approved NGO representative | Publish approved NGO public leadership contact | Allowed with publication authorization and appropriate consent |
| User switching NGO-A → NGO-B | View old NGO-A cached private page | Must clear/hide and refetch under NGO-B context |

## 7. First end-to-end vertical slice: step-by-step acceptance

1. Account A registers, verifies contact and authenticates.
2. A creates a provisional NGO-A workspace, but cannot publish a verified institutional profile or access existing NGO records.
3. Reviewer accepts separate organization eligibility and representative-authority evidence for NGO-A.
4. A configures 'approval required' membership and invites or approves a member.
5. A imports a small CSV containing valid, duplicate and invalid rows: preview counts and row feedback are correct.
6. A valid unclaimed member claims via verified identity and expiring one-time token or NGO approval; no second login account is created.
7. A second user with NGO-B access cannot query, update, search, export or retrieve files belonging to NGO-A.
8. PWC Board context cannot read NGO-A's private membership or finance records.
9. Revoking an NGO-A administrator ends access without removing organization data.
10. Logs and test output show denied attempts, verified claims, authorization changes and no sensitive data leaked in notification bodies.

## 8. Testing / quality gates

**Automated suites:** authentication/session; role-and-tenant permission matrix; organization-claim conflicts; duplicate/replay imports; claim-token expiry/reuse; list/detail/search leakage; file/export isolation; cache invalidation on context switch; API contract snapshot and error states; audit event integrity.

**M1 'no-go' failures:** any private cross-tenant read/write; PWC alliance role bypassing NGO access rules; provisional claimant takeover; imported record creating an authenticated identity silently; token replay successful; role recovery without evidence; unscoped private file download or export; privileged access without auditable justification.

**M1 exit evidence:** passing CI summary, migration checks, staging demonstration, two-NGO negative test log, verified account-claim test, administrator recovery rehearsal, and named owner/reviewer acceptance.

## 9. G0 prerequisites — decisions needed before code affecting them

| Decision | Recommended next action | Blocking? |
|---|---|---|
| Source repository and branch conventions | Provide current repository or select a new repository | Blocks actual implementation |
| Authentication and recovery approach | Approve email/phone verification and account-recovery ADR | Blocks identity implementation |
| NGO eligibility and authority evidence | Approve registered/unregistered document categories and conflict escalation | Blocks verification logic |
| Tenant model and role permissions | Approve base authorization contract and negative-test matrix | Blocks private CRUD |
| Web portal framework | Choose Flutter Web vs separate web frontend after team review | Blocks web implementation, not backend schema |
| Hosting/secret management | Choose staging deployment and backup/operator controls | Blocks live/staging rollout |
| Privacy/retention and technical support access | Approve interim data-handling policy with legal review | Blocks production personal-data processing |
| Language/accessibility commitments | Set launch locale/accessibility criteria | Blocks production UX acceptance |
| Pilot NGO cohort | Identify consenting test organizations and designated representatives | Blocks real-world UAT, not synthetic tests |

Other unresolved PWC constitution and national chapter questions can remain open if they do not affect the M1 platform trust model; no legal-compliance obligation is overridden by provisional requirements.

## 10. Recommended immediate execution order

1. Approve this engineering backlog for issue creation (not as final PWC constitution).
2. Establish repository/environment access, engineering owner and CI conventions.
3. Write short ADRs for authentication, tenant isolation, organization verification, support access, and web frontend choice.
4. Implement CORE-01 through CORE-04 with two-NGO negative tests *before* private membership interfaces.
5. Deliver the first vertical slice and rehearse the M1 exit gate.
6. Expand to all M1 tickets, then use the M2 requirements for finance and NGO operations.

**Development status:** Planning artifact only. No repository created or changed and no application code implemented by this document.
