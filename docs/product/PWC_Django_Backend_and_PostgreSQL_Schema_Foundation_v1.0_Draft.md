# Pakistan Welfare Club (PWC)
## Django Backend & PostgreSQL Schema Foundation v1.0 — Draft for Review

**Date:** 22 October 2026  
**Status:** WORKING DRAFT — NOT FORMALLY APPROVED  
**Scope:** Faisalabad-first PWC digital ecosystem: citizen/volunteer application, independent NGO workspaces, PWC alliance and committees, PWC-operated platform administration.  
**Precedent:** The PWC Strategic & Product Foundation v1.0, Information Architecture & Navigation v1.0, Detailed Mobile & Web Screen Specification v1.0, and Identity, Authorization & Multi-NGO Data Model Foundation v1.0. The Coventure Django Foundation is a *technical reference* and must not be assumed to confer PWC policy approvals.

**Status key:** **[S]** User-selected provisional requirement; **[R]** implementation recommendation; **[O]** unresolved requiring sign-off; **[D]** deferred. Neither [S] nor [R] constitutes formal sign-off. Table names, code snippets, indices and API paths below are [R] unless noted.

---

## 1. Executive architecture decision

**[S]** PWC directly owns and operates the platform, including SaaS-like NGO management for eligible organizations whether or not they join the alliance. NGO members, volunteers, independent activities, finances and internal decisions remain independently controlled by each NGO. PWC alliance business roles do not inherit tenant-administration privileges; software operator access for security/support must be independently controlled and audited.

**[R]** Deploy a *modular Django monolith* with Django REST Framework and PostgreSQL. Keep shared identity, public directory, tenant-admin, alliance, collaboration and finance components in separate Django apps with domain services and explicit transaction boundaries. Use a common database with mandatory `organization_id` on NGO-owned data initially; avoid per-organization Django projects or databases for MVP. Pair tenant-scoped ORM access with authenticated object permissions and negative-access tests. PostgreSQL RLS can be introduced as defense-in-depth on highest-risk tables only after thoroughly testing pooled connections and background workers. **Do not claim RLS is active until implemented.**

**[O]** Django/DRF, PostgreSQL, Redis/Valkey, Celery, object storage, hosting provider and Flutter/web frameworks are *technical recommendations*, not recorded user-approved PWC stack decisions. Infrastructure choices should be formally confirmed.

### 1.1 Non-negotiable invariants

1. One authenticated person has one `User`; they can hold multiple separate NGO/PWC relationships.
2. `Organization` is not equivalent to `PWCInstitutionalMembership`; platform eligibility does not confer alliance voting rights.
3. Imported NGO member and volunteer records do not create `User` accounts and are never auto-claimed on mere contact matching.
4. All NGO-private reads, writes, counts, files, imports, exports, background jobs and reports enforce the active tenant plus per-action authorization.
5. PWC Board and committee roles do not grant NGO financial or private membership access; an NGO primary administrator does not automatically gain finance access.
6. Projects distinguish NGO-owned, PWC-owned and joint ownership; public publication must not publish internal budgets or rosters.
7. An NGO's participation in a PWC project exists only after acceptance under that NGO's approved single- or multi-authorizer policy.
8. Dues and donation receipts generate at most one financial source posting; pending items do not affect posted balances.
9. Internal transfers are balanced and do not create income/expense. Posted entries are corrected through reversal, not deletion.
10. Withdrawal from PWC alliance and termination of the independent NGO software workspace are separate actions.

## 2. Proposed deployment and engineering boundaries [R]

```text
Flutter client / NGO web portal / PWC ops portal
         | TLS + authentication + API rate limits
         v
      Django REST API (stateless)
         |-- identity + access policy service
         |-- organizations + NGO domain services
         |-- PWC alliance + collaborations
         |-- scoped data exports and reports
         |-- transactional command handlers
         |
         +--> PostgreSQL (authoritative relational storage)
         +--> Redis/Valkey (optional cache and job broker)
         +--> Celery workers (imports, email, notifications, exports)
         +--> private object storage (attachments and export archives)
         +--> outbox dispatcher / notifications
```

Keep all business writes within PostgreSQL transactions; enqueue side effects only after commit or via durable transactional outbox. Cache must be permission-sensitive and tenant-qualified; never cache private NGO data under globally shared keys. Apply structured logs, health checks, migration checks, centralized error reporting, distributed tracing as needed, automated backups and tested restoration. Avoid premature microservices.

## 3. Recommended Django application boundaries [R]

| Django app | Owns | Must not own |
|---|---|---|
| `accounts` | users, credentials, contact verification, sessions, personal preferences | NGO membership authority |
| `access` | permission definitions, contextual role grants, authorization decisions | financial balances |
| `organizations` | organization registry, workspaces, verification, claims, public profiles | PWC institutional admission |
| `ngo_memberships` | categories, admission, imported person records, dues periods and status | PWC election eligibility |
| `volunteers` | profiles, standing enrollments, volunteer opportunities/applications/assignments | permanent NGO membership by implication |
| `activities` | NGO and PWC events, registration, attendance, announcements | unrestricted beneficiary cases |
| `projects` | independent/PWC/joint projects, teams, tasks, milestones, resources, budgets | binding NGO approvals by itself |
| `ngo_finance` | NGO-private accounts, dues/donation receipt postings, entries, transfers and approvals | PWC general ledger |
| `alliance` | PWC institutional membership, representatives, Board terms and committee administration | NGO internal leadership |
| `collaboration` | requests/offers, invitations, commitment policies, versioned approval and accepted commitments | another NGO's private project data |
| `pwc_finance` | PWC's own accountable funds and project tracking | member NGO account data |
| `inquiries` | narrowly scoped public contact and assistance inquiries | comprehensive case management [D] |
| `files` | attachments, metadata, scoped uploads/downloads | public file serving by raw object key |
| `audit` | security/business audit trail, support access approvals, lifecycle events | direct governance authority |
| `notifications` | notification outbox, delivery preferences, event fanout | domain write ownership |
| `exports` | scoped data export jobs, retention, deactivation support | foreign-tenant data aggregation |

**Dependency rule:** API serializers/views call domain services; domains may depend on accounts/access and well-defined cross-domain interfaces. They should not import another app's mutable ORM models deep inside arbitrary viewsets for business decisions. PWC alliance is a bounded domain, not a `super organization` allowed to join into all tenant tables.

## 4. Cross-cutting PostgreSQL conventions [R]

- UUID primary keys (`uuid.uuid4` or database-generated UUID consistently); UTC timestamps with timezone (`timestamptz`); `created_at`, `updated_at`, actor and state transition evidence.
- For tenant data, mandatory `organization_id REFERENCES organization(id)` and indexes beginning with `organization_id` for common tenant queries. Public/non-tenant identity data must be distinguished.
- Monetary amounts: `numeric(18,2)` for PKR-facing records if fixed-decimal is standardized; store `currency CHAR(3)` and never use float. Alternatively use integer minor units platform-wide, but select one method before migration 0001. This document's examples use decimal.
- PostgreSQL `CHECK` constraints for nonnegative monetary amounts, valid date ranges, allowed status values where stable, and exclusive ownership fields; actual status transitions are service-layer invariants.
- Case-insensitive contact identity uniqueness only for *verified and canonicalized* contact records according to chosen authentication design. Do not create unique keys on names.
- Foreign keys with `PROTECT` for historic financial/approval evidence, `RESTRICT` or explicit soft-deactivation for active organizations. No cascading deletion of posted entries through organization deletion.
- All internal cross-tenant references must validate ownership at command time. Because a conventional FK cannot enforce that project and child org IDs match, use composite uniqueness (`UNIQUE(id, organization_id)`) plus composite FK in SQL migrations where valuable, otherwise service-level checks and database triggers as appropriate.
- Explicit authorization on attachments, exports, autocomplete, admin screens, reports, background tasks and notification payloads.
- `version` integer for frequently contested updates and commitment proposals; conditional updates reject stale clients with 409/412.
- State and domain decision history is append-only where audit evidence matters; mutable cached status is allowed only with reconciliation tests.

## 5. Schema inventory — platform and identity [R]

| Table (suggested) | Essential columns | Important constraints/indexes |
|---|---|---|
| `accounts_user` | id, status, display_name, preferred_language, city, joined_at | status index; no imported people here |
| `accounts_user_contact` | id, user_id, kind, normalized_value, verified_at, primary | conditional uniqueness for verified contact; index user |
| `accounts_session` | id, user_id, refresh_token_hash, revoked_at, expires_at, device metadata | index user, expires; rotate/revoke securely |
| `access_role_definition` | id, domain, code, version, active | UNIQUE(domain, code, version) |
| `access_permission` | id, domain, code, classification | UNIQUE(code) |
| `access_role_permission` | role_id, permission_id | UNIQUE(role, permission) |
| `access_role_assignment` | id, user_id, role_id, scope_type, scope_id, granted_by, valid_from, valid_until, state | indexed (user, scope_type, scope_id, state); ensure scope valid via service and schema where feasible |
| `access_resource_grant` | id, user_id, resource_kind, resource_id, permission, expires_at | resource and user indexes; explicit resource check |
| `audit_event` | id, actor_id nullable, scope, organization_id nullable, action, object_type, object_id, occurred_at, before/after references, correlation_id | index scope+time, object+time; tamper-resistance strategy [O] |
| `support_access_request` | id, ticket_ref, staff_id, organization_id, requested_scope, reason, approver_id, expires_at, state | independent approval, expiration, full read/write audit |

**Caution:** `scope_type + scope_id` is a flexible authorization reference, not a free-form content owner. Maintain a closed scope registry and validate target existence. For especially sensitive grants, dedicated `organization_id`/`committee_id`/`project_id` nullable FK columns with an exactly-one constraint are safer than unvalidated generic scope identifiers.

## 6. Schema inventory — organizations and imported records [R]

| Table | Key fields | Key constraints |
|---|---|---|
| `organization` | id, legal_name, display_name, category, registration_classification, registration_reference nullable, region, public_status | no automatic uniqueness of name; controlled duplicate review |
| `organization_workspace` | id, organization_id, state, verified_at, onboarding_version, deactivated_at | UNIQUE(organization_id) |
| `organization_contact` | id, organization_id, contact_type, value, is_public, approved_for_publication | tenant-indexed; public fields opt-in |
| `organization_sector` | organization_id, sector_id | UNIQUE(org, sector) |
| `organization_claim` | id, organization_id nullable, requester_user_id, claim_kind, status, submitted_at | active claims reviewed; do not seize existing workspace |
| `organization_verification_case` | id, organization_id, applicant_id, verification_track, status, reviewer_id, decision_reason, decision_at | tiered registered/unregistered evidence; decision log |
| `organization_verification_evidence` | id, case_id, attachment_id, evidence_type, review_state | access protected, retention policy |
| `organization_person_record` | id, organization_id, linked_user_id nullable, original_name, contacts encrypted/limited, import_source, claim_state | UNIQUE(id, organization_id); no automatic cross-NGO merge |
| `person_claim_token` | id, organization_id, person_record_id, token_hash, expires_at, used_at, state | hash tokens; single use; rate limit |
| `organization_import_job` | id, organization_id, kind(member/volunteer), file_id, state, requested_by, summary, created_at | per-tenant validation, dry-run and errors artifact |
| `organization_export_job` | id, organization_id, scope, state, requested_by, expires_at, artifact_id | scoped export, approval and audit |

**Provisional-workspace gate:** before verified operational authority, user may edit *only their own draft/provisional application data*, not existing tenant records. Registered and unregistered organization verification use different evidence rubrics; legal eligibility for regulated activities remains separate from a platform badge.

## 7. Schema inventory — membership, dues and volunteering [R]

### 7.1 NGO membership

| Table | Key fields | Rules |
|---|---|---|
| `ngo_membership_policy` | organization_id, admission_mode, renewal_mode, grace_days, reminders_json, active | UNIQUE org; validate modes (`open`, `approval`, `invitation`) |
| `ngo_membership_category` | id, organization_id, label, fee, fee_currency, renewal_period, active | UNIQUE(org, normalized_label) among active; historic snapshots |
| `ngo_membership_application` | id, organization_id, applicant_user_id nullable, invitee_contact nullable, status, reviewer_id | prevent duplicate simultaneous active application to same category as appropriate |
| `ngo_membership` | id, organization_id, person_record_id, category_id, membership_no, status, admitted_at | UNIQUE(org, membership_no) when present; category/record must belong to same org |
| `ngo_membership_period` | id, membership_id, begin_at, end_at, due_at, grace_until, renewal_state, assessed_fee | begin < end; prevent overlapping active periods for same membership if policy requires |
| `ngo_dues_assessment` | id, period_id, assessed_amount, state | unique assessment generation key per period/version |
| `ngo_dues_adjustment` | id, assessment_id, amount, kind, reason, approved_by, state | nonnegative; cannot exceed agreed policy limits |
| `ngo_dues_payment` | id, assessment_id, amount, destination_account_id, source_reference, confirmation_state, financial_source_id | nonnegative; track allocation and posted state separately |

**[S]** Categories, fee waivers/discounts, partial payments, exemptions, renewals, configurable grace/expiry, manual receipts, Excel/CSV import and controlled claiming. **[R]** Membership state, dues state, and access role grants never collapse to a single enum. Do not overwrite old assessments when category prices change. Prevent partial-payment double allocation through locks/transactions.

### 7.2 Volunteers and activities

| Table | Key fields | Rules |
|---|---|---|
| `volunteer_profile` | id, user_id, skills/interests/location/availability | UNIQUE(user_id); individual privacy settings |
| `ngo_volunteer_policy` | organization_id, admission_mode, screening_settings | UNIQUE org; open/approval/invitation |
| `ngo_volunteer_enrollment` | id, organization_id, person_record_id, status, enrolled_at | no implicit NGO membership |
| `volunteer_opportunity` | id, organizer_kind, organizer_org_id nullable, project_id nullable, capacity, skills, visibility | enforce owner-kind XOR; protect private fields |
| `volunteer_application` | id, opportunity_id, applicant_user_id, status | conditional UNIQUE active application per user/opportunity |
| `volunteer_assignment` | id, opportunity_id, applicant_user_id, assigned_by, status | reject overcapacity in locked transaction |
| `activity` | id, owning_org_id nullable, pwc_owned boolean, name, visibility, status, starts_at, ends_at | owner XOR; public description separate sensitive fields |
| `activity_registration` | id, activity_id, user_id, status | UNIQUE(activity, user) for active registration |
| `activity_attendance` | id, registration_id, confirmed_by, confirmed_at, evidence_id nullable | UNIQUE(registration_id) subject to attendance model |
| `announcement` | id, owner_kind, owning_org_id nullable, committee_id nullable, visibility, status, body | owner fields mutually exclusive |

Imported NGO volunteers use `organization_person_record` and an organization-scoped enrollment; one-off volunteers use application/assignment records without standing enrollment. Participation history requires organizer confirmation rather than inference from registration.

## 8. Schema inventory — independent projects and resources [R]

**[S]** MVP independent projects have teams, tasks, milestones, resource requirements, basic budgets, progress and Public/Members Only/Private visibility. Joint and PWC projects share some mechanics, but ownership/authority varies.

| Table | Essential fields | Notes |
|---|---|---|
| `project` | id, kind, owning_organization_id nullable, pwc_owner boolean, title, visibility, status, version, starts_at, ends_at | `kind=ngo/pwc/joint`; owner fields validated with kind; joint ownership via explicit project authority record |
| `project_team` | id, project_id, user_id, role, state | resource-scoped assignment |
| `project_task` | id, project_id, title, assignee_id nullable, due_at, status, priority | index(project, status, due_at) |
| `project_milestone` | id, project_id, title, target_at, status, completion_at | index(project, target_at) |
| `project_resource_requirement` | id, project_id, resource_kind, quantity, need_by, status, notes | commitments handled separately |
| `project_budget_line` | id, project_id, category, planned_amount, approved_amount nullable | nonnegative, currency; don't conflate with finance entries |
| `project_update` | id, project_id, author_id, publication_scope, update_body, created_at | redact private operational details from public projection |
| `project_outcome` | id, project_id, metric_name, measured_value, evidence_ref nullable, verified_by nullable | distinguish claimed from verified outcomes |

**Schema design note:** `kind + owning_organization_id + pwc_owner` is a compact example, not an endorsed polymorphic implementation. Final physical schema should use a properly constrained authority/ownership table or conditional FK design. A joint project's separate `project_commitment` rows express participating NGOs' accepted obligations, not co-ownership of those NGOs' private data.

## 9. Schema inventory — NGO-private finance [R]

### 9.1 Tables and critical keys

| Table | Important columns | Required constraint / access |
|---|---|---|
| `ngo_finance_policy` | organization_id, mode(direct/approval), grant_policy, recovery_policy_version | UNIQUE(org), change audit, no retroactive approval |
| `ngo_financial_account` | id, organization_id, kind(cash/bank), label, currency, opening_recorded_balance, active | UNIQUE(id, organization_id); no silent currency blending |
| `ngo_financial_source` | id, organization_id, source_kind, source_id, source_reference, state | UNIQUE(org, source_kind, source_id) or scoped equivalent |
| `ngo_financial_transaction` | id, organization_id, source_id nullable, kind, status, entered_by, submitted_at, approved_at, posted_at, version | UNIQUE(org, source_id, posting_role) when appropriate; exact lifecycle |
| `ngo_financial_leg` | id, transaction_id, organization_id, account_id, direction, amount, currency | amount > 0; account belongs to same org; no ambiguous sign |
| `ngo_financial_approval` | id, transaction_id, reviewer_id, decision, decided_at, policy_version | separate reviewer; reject stale policy/version |
| `ngo_financial_reversal` | id, original_transaction_id, reversal_transaction_id, reason, actor_id | UNIQUE(original_transaction_id) if single full reversal design |
| `ngo_donation` | id, organization_id, source_id, donor_ref nullable, anonymity, purpose/restriction, amount | private contact and restricted purpose |

**Design recommendation:** Model one `FinancialTransaction` header with one or more `FinancialLeg` rows. This makes all-or-nothing transfers and reversal more explicit than independent account-entry mutations. For the MVP cashbook, `income` and `expense` are categorized transaction kinds; a transfer has exactly two opposite-account legs and does not count toward operating income/expenses. Enforce same-currency transfer or require a separately designed FX capability [D].

### 9.2 Example SQL invariants (illustrative, adjust naming after model approval)

```sql
ALTER TABLE ngo_financial_leg
  ADD CONSTRAINT positive_leg_amount CHECK (amount > 0);

CREATE UNIQUE INDEX unique_financial_source_per_ngo
  ON ngo_financial_source (organization_id, source_kind, source_id);

CREATE UNIQUE INDEX unique_membership_number_per_ngo
  ON ngo_membership (organization_id, membership_no)
  WHERE membership_no IS NOT NULL;

CREATE INDEX idx_finance_tx_org_state_date
  ON ngo_financial_transaction (organization_id, status, posted_at DESC);
```

These constraints do **not** by themselves enforce balanced transfers or account/transaction same-tenant ownership. Those require transactional domain services and additional composite FKs/triggers or rigorous invariants. Never represent a demo SQL fragment as a complete production schema.

### 9.3 Financial posting procedure

1. Authenticate actor; resolve exact NGO and finance permission; load versioned NGO finance policy.
2. Validate source receipt or manual input, currency, amount, destination account, category, organization ownership and receipt authorization.
3. Begin `transaction.atomic()`; lock affected source, dues assessment (if applicable), financial transaction and account records in deterministic order using `select_for_update()`.
4. Check idempotency/source uniqueness; reuse existing result for a retry.
5. In direct mode, validate sender's `finance.record` permission and post; in approval mode, stage pending and require separate finance approver to advance it.
6. On successful posting, create immutable legs and linked source record, update any cached balances atomically if used, and record audit/outbox events.
7. Return stable transaction ID and `recorded|pending|posted` semantics. Do not claim external bank verification.

A confirmed dues/donation receipt whose linked finance entry is pending must be visibly `pending posting`; only an approved posted entry changes account balances. Overpayment allocation, refunds and credits remain open policies.

### 9.4 Transfers, reversals and reports

- Transfer must be a single transaction with balanced outflow and inflow legs between accounts in the *same NGO and currency*. Posting is atomic.
- Posted corrections use referencing reverse transactions; no editing or deleting a posted money leg in place.
- Reports filter by owning org and posted state, expose both per-account and combined recorded balances, exclude transfers from income and expense totals, and explicitly separate restricted/unrestricted donation classifications.
- The finance API does not supply any PWC-wide private NGO financial dashboard; aggregate NGO finance data must not be assembled from privileged operator queries.

## 10. PWC alliance and governance schema [R]

| Table | Core fields | Requirement |
|---|---|---|
| `alliance_institutional_membership` | organization_id, class, status, admitted_at, ended_at | separate from platform tenant status |
| `alliance_representative` | membership_id, user_id, delegated_from/through, authorization_evidence, start/end | verify organization mandate |
| `alliance_board_term` | id, kind(founding/elected), starts_at, ends_at, status | 24-month founding term [S]; starting event [O] |
| `alliance_board_seat` | id, term_id, office/seat_no, current_appointee_id | regular Board 11 members [S]; position mapping [O] |
| `alliance_committee` | id, sector, title, status, convener_id nullable | activate progressively [S] |
| `alliance_committee_membership` | committee_id, user_id, organization_id nullable, role, status | professional advisers possible; not NGO delegation by default |
| `alliance_committee_meeting` | id, committee_id, schedule, agenda, minutes_state | committee MVP [S] |
| `alliance_committee_proposal` | id, committee_id, proposed_project_id nullable, status, version | proposal not a project approval |
| `alliance_resolution` | id, board_term_id nullable, resolution_type, state, approved_at | authority defined by adopted constitution [O] |

**[S]** Only eligible registered *full* PWC institutional members vote in regular Board elections; individual volunteers/associates do not. Election mechanism, candidate eligibility snapshot, quorum and seat positions remain [O]. **[D]** Formal electronic election infrastructure. Do not ship a pseudo-election UI that claims legal or constitutional authority before governance sign-off.

## 11. Collaboration and NGO-approved commitments [R]

| Table | Fields | Constraint |
|---|---|---|
| `collaboration_request` | id, requester_org_id or PWC owner, sector, description, status, visibility | owner validation |
| `collaboration_offer` | id, request_id, offering_org_id, submitted_by, status | no automatic obligation |
| `joint_project_invitation` | id, project_id, invited_org_id, status | UNIQUE active invitation per project/org |
| `ngo_commitment_policy` | organization_id, mode(single/multi), configured_authorizers, version | organization controls policy |
| `commitment_proposal` | id, project_id, organization_id, version, terms_snapshot, state, proposed_by | immutable approved version |
| `commitment_approval` | id, proposal_id, approver_id, authority_grant_id, decision, timestamp | unique approver-step; role valid at action time |
| `project_commitment` | id, proposal_id, project_id, organization_id, accepted_at, state, accepted_terms_hash | unique accepted version; audit commitments |
| `commitment_amendment` | id, parent_commitment_id, proposed_terms, version, state | require fresh authorization on substantive changes |

**[S]** An NGO may require one authorized signatory or multiple internal approvals. **[R]** Record proposal version, relevant delegation evidence and accepted terms hash; use optimistic concurrency and transactional approval state transitions. `interested`, `invited` and `pending_approval` are NOT `committed`. PWC's Board approving a project never bypasses the NGO's internal delegation policy. Withdrawal and legal obligations require project agreement terms [O].

## 12. API boundary and authorization contract [R]

Suggested versioned API structure (not exact approved routes):

```text
/api/v1/me/                         user profile, affiliations, allowed contexts
/api/v1/public/organizations/        public NGO directory, redacted profiles
/api/v1/public/projects/             safely published initiatives
/api/v1/public/opportunities/        discover/register/apply
/api/v1/organizations/onboarding/    draft/claim/verification status
/api/v1/ngo/{org_uuid}/members/      tenant-scoped membership
/api/v1/ngo/{org_uuid}/volunteers/   tenant-scoped standing volunteer admin
/api/v1/ngo/{org_uuid}/activities/   NGO-owned activity commands
/api/v1/ngo/{org_uuid}/projects/     NGO-owned project commands
/api/v1/ngo/{org_uuid}/finance/      NGO-private finance, approvals and reports
/api/v1/ngo/{org_uuid}/settings/     membership, volunteer, finance policies
/api/v1/ngo/{org_uuid}/exports/      authorized export jobs
/api/v1/alliance/memberships/        PWC institutional admission
/api/v1/alliance/committees/         committee workspace
/api/v1/alliance/governance/         authorized Board records
/api/v1/collaborations/              requests and offers
/api/v1/projects/{id}/commitments/   versioned NGO acceptance commands
/api/v1/platform/verification/       platform-only verification tasks
/api/v1/platform/support-access/     exceptional technical workflows
```

**Contract conventions:** cursor or page-number pagination with firm caps; `organization_id` from validated URL/context not client-controlled serialized foreign key; explicit command endpoints for approvals/withdrawals rather than arbitrary PATCH; stable error code + safe message + trace ID; ID based lookups must not disclose whether foreign private objects exist. `Idempotency-Key` for financial commands, imports and commitment acceptance; `If-Match` or version for sensitive modifications; OpenAPI schemas and generated contract tests. Prefer 404 for inaccessible private foreign objects where information existence is sensitive; consistent 403 for known owned records lacking permissions. All reports and files require separate authorized endpoints.

### 12.1 Request authorization flow

```text
authenticate user
 -> verify user/session active
 -> resolve requested resource and its true owner scope
 -> verify requested org/context is active and authorized
 -> verify exact permission and any sensitive field restrictions
 -> verify command-specific business policy/state/version
 -> execute atomic domain service
 -> record audit + durable notification event
```

UI workspace switching is merely a navigation preference; the backend must independently evaluate every request. DRF `has_permission` without a tenant-filtered queryset is insufficient; `get_object` alone without scoping list/search/export is also insufficient.

### 12.2 Suggested Django service shape

```python
@transaction.atomic
def accept_commitment(*, actor, organization, proposal_id, expected_version):
    proposal = (
        CommitmentProposal.objects.select_for_update()
        .get(id=proposal_id, organization_id=organization.id)
    )
    require_permission(actor, 'project.commitment.approve', organization)
    require_current_version(proposal, expected_version)
    require_valid_ngo_approver(actor, organization, proposal)
    record_approval_once(proposal, actor)
    if commitment_policy_satisfied(proposal):
        create_accepted_commitment_once(proposal)
    return proposal
```

Illustrative pseudocode: does not yet implement all required validation (project eligibility, actor delegation version, evidence, unique constraints, idempotency, stale proposals and outbox handling). These checks are mandatory in implementation.

## 13. Asynchronous jobs, attachments and notification safety [R]

- `import_job`: verify user permission *when requested* and again at execution if applicable; parse Excel/CSV from private object storage; validate column schema; chunk with bounded transactions; produce tenant-scoped error reports; no authentication accounts from imports; deduplicate only within the NGO by explicit reviewed criteria.
- `export_job`: high-sensitivity operation requiring explicit NGO permission and optional step-up authentication; short-lived private artifact URL; audit download; exclude foreign organizations and PWC-only records.
- `notification_outbox`: commit transaction and outbox record in same database transaction; workers idempotently dispatch to selected provider; push notifications must not contain private financial details or sensitive inquiry content.
- Files: metadata includes owner domain, organization/project scope, classification, uploader, retention and virus scan state. No public raw bucket ACL for private attachments; signed URLs must be authorization-checked and short-lived.
- Work queues: bound retries and dead-letter inspection; never trust tenant IDs supplied in queue payload without revalidating policy/ownership.

## 14. Security, audit, and operational nonfunctional requirements [R/O]

- **Authentication:** verified email and/or mobile [O]; secure password/OTP flow; refresh rotation/session revocation; rate limits and account recovery; step-up MFA for privileged/finance users where feasible.
- **Authorization:** contextual RBAC with scoped, expiring grants; classification-aware resource authorization; fail-closed whenever NGO context is absent or invalid.
- **Support access:** request ticket, reason, approved minimal scope, time-limited elevation, full audit. Board role never authorizes support access. Prefer user-assisted support over reading raw tenant content.
- **Tenant boundaries:** dedicated cross-tenant tests, query-level isolation, encryption in transit, encrypted backups, segregated exports, tenant-safe caching, audit on finance, role and project decisions.
- **Privacy:** keep ordinary NGO members private; public NGO contacts/leaders only with organization-approved publication; consent/notice for imported personal records; defined personal/NGO exit lifecycle.
- **Reliability:** automated migrations, health/readiness endpoint, minimum viable dashboards, backup restore drills, staging security tests, CI lint/type/test gates.
- **Unresolved service levels [O]:** uptime objective, database backup interval, RPO/RTO, log retention, support SLAs, data center geography, local-language accessibility requirements.

### 14.1 Recommended security threat review

Threats to explicitly model: forged NGO claim, cross-tenant ID manipulation, bulk export privilege escalation, financial approval self-grant, double-posting from retries, orphaned role after volunteer/member removal, forged imported-person claim, public-project private-field leakage, stale proposal commitment, stolen support elevation, CSV formula injection and unsafe private-file links.

## 15. Test strategy and required acceptance matrix

| Test ID | Condition | Expected outcome |
|---|---|---|
| ISO-01 | NGO A user accesses NGO B members by guessed ID | No data returned or changed |
| ISO-02 | PWC Board member tries NGO private finance API | Denied absent distinct NGO finance grant |
| ISO-03 | NGO primary administrator calls finance export | Denied absent finance export grant |
| ISO-04 | Tenant filter is omitted in search, export or Celery job | Automated tests fail; no foreign records |
| ORG-01 | Claimant requests existing NGO before authority verification | No access to existing workspace records |
| ORG-02 | Eligible unregistered group applies | Appropriate separate verification track |
| ID-01 | Member CSV import of 500 people | No `User` accounts created |
| ID-02 | Contact match without claim token/NGO approval | No linking to existing person record |
| MEM-01 | NGO A open enrollment; NGO B invitation-only | Policies enforced independently |
| MEM-02 | Two partial payments concurrently allocated to same dues | No over-allocation or double posting |
| VOL-01 | Individual volunteers for an event | No automatic NGO membership |
| VOL-02 | Imported volunteer claims record | Does not grant standing NGO membership |
| FIN-01 | Same dues receipt processed twice | One financial source and one valid posting |
| FIN-02 | Pending approval | No effect on posted balances |
| FIN-03 | Submitter tries to approve own pending entry | Denied in approval-required mode |
| FIN-04 | Cash-to-bank transfer | Balanced legs, zero new operating income |
| FIN-05 | Reversal of posted expense | Original immutable, linked reversal present |
| FIN-06 | Changing approval mode with pending entries | Pending entries remain pending until explicit resolution |
| FIN-07 | Finance account from NGO B supplied in NGO A transaction | Rejected atomically |
| PROJ-01 | Public NGO project fetched by guest | Private roster/budget/attachments not exposed |
| PROJ-02 | Task update by unrelated NGO user | Denied |
| COL-01 | PWC approves joint project | No implicit NGO commitment |
| COL-02 | Two-approver policy; one approval given | Remains pending |
| COL-03 | Terms change after one approval | Previous approval does not authorize revised proposal |
| AUD-01 | Support access granted for expired ticket | Denied and logged |
| LIFE-01 | NGO withdraws from PWC | NGO software workspace remains intact |
| LIFE-02 | NGO exports and deactivates | Scoped data only; deletion/retention policy followed |

**Testing levels:** Django service/unit tests, model constraints, transaction/concurrency tests with actual PostgreSQL (not SQLite), API integration tests, role/tenant matrix tests, property-based tests for finance allocations, load tests for listing/imports, controlled restore drills and security review. Unit tests cannot replace multi-transaction PostgreSQL isolation testing.

## 16. Migration and delivery strategy [R]

### M1 — Identity and institutional foundation

1. Create custom `User` model **before** first migration; choose authentication/contact strategy [O].
2. Add organization registry/workspace, claim/verification and tenant-person records.
3. Add role/permission framework, NGO scoped services, public projections, audit, files and import processing.
4. Add membership policies/categories/applications/records, CSV/Excel imports and claim workflow.
5. Release only with cross-tenant negative access tests and primary-admin recovery validation.

### M2 — Independent NGO operations

1. Volunteer profiles/enrollments/opportunities/assignments and activity participation.
2. NGO projects, teams/tasks/milestones/resources/basic budgets.
3. Dues and membership-period policies.
4. NGO finance accounts, transactions/legs, approval, sources, transfer/reversal and links from approved dues/donations.
5. Finance permission matrix and concurrency tests before enabling write access; reports clearly labeled recorded, not audited balances.
6. NGO deactivation/export baseline.

### M3 — Public, PWC alliance and collaboration

1. Public discovery and restricted public inquiries.
2. PWC institutional membership and authorized representatives, Board/committee metadata and meetings/proposals.
3. Collaboration requests/offers, project invitations and NGO-configurable approval policies.
4. Versioned commitments, joint project participation/progress, independent PWC finance jurisdiction.
5. End-to-end multi-organization tests and notifications.

**Dependency warning:** Public discovery and PWC announcements may be exposed progressively in staging, but the milestone grouping is not permission to launch unsafe incomplete financial or governance flows. The approved first-release definition includes all selected P0 elements across M1–M3.

### 16.1 Migration rules

- Number and review migrations; separate large data backfills from schema constraints where necessary.
- Introduce nullable/new fields, backfill, then enforce NOT NULL and uniques; review locking impact.
- Preserve historical source and audit keys; never regenerate IDs during data imports.
- Run rollback/recovery exercises; database rollback cannot always reverse published irreversible domain operations.
- Seed permission definitions via deterministic versioned migrations/management commands, not ad hoc administrator behavior.

## 17. Development handoff / definition of done

Each backend story requires: a source screen/flow ID, owning Django app, request/response contract, valid and invalid transitions, authorization and tenant scope, unique constraints and indexes, audit events, failure/error codes, idempotency/concurrency behavior, migrations/fixtures, unit and integration tests, documentation and any PWC/NGO privacy exposure review.

**Cross-cutting done gates:** No unaudited finance grants; no tenant data escape; no platform-admin business privilege shortcut; no unclaimed imported identities treated as authenticated users; no double posting; no implicit NGO commitments; no unapproved claim that provisional/associate organization is formally registered; no inclusion of deferred case-management, payments or online election workflows as if in scope.

## 18. Decision register — what remains open

| Topic | Status | Formal review requirement |
|---|---|---|
| PWC owns/operates platform | **[S]** | Document operator and legal obligations |
| Multi-tenant Django monolith/PostgreSQL | **[R]** | Confirm technology and infrastructure |
| Shared DB, tenant foreign keys; selective future RLS | **[R]** | Security architecture sign-off |
| NGO configurable finance recovery | **[S]** | Finalized recovery templates and evidence [O] |
| Single/multi NGO joint commitment approval | **[S]** | Delegation and acceptance evidence [O] |
| Separate registered/unregistered verification | **[S]** | Evidence rubrics and legal eligibility [O] |
| Legal registration and fundraising authority | **[O]** | Qualified Pakistan/Punjab legal review |
| Authentication channels, MFA and account recovery | **[O]** | Security/product selection |
| Finance refund/credit, receipt numbering, currency and opening-balance rules | **[O]** | Finance product owner review |
| Who approves break-glass access and audit retention | **[O]** | Independent accountability policy |
| NGO finance grant recovery and last administrator | **[O]** | Formal delegated-authority rules |
| Project-signature enforceability / withdrawal | **[O]** | Governance/legal review |
| Data retention and deletion intervals; exports | **[O]** | Legal and privacy review |
| Operational SLAs, RPO/RTO, hosting, notifications | **[O]** | Operations readiness review |
| Board election details and national chapter model | **[O]/[D]** | Separate governance process |

## 19. Recommended review and sign-off sequence

1. Product owner validates [S] requirements against the previously accepted *planning baseline*; fixes any misinterpretations.
2. NGO representatives check verification, membership, finance privacy, administrator recovery and portability.
3. Engineering/security reviews tenant isolation, authorization, finance transactions, outbox, exports and break-glass model.
4. Finance reviewer verifies the posting model, source idempotency, transfer balancing, reversals and partial dues.
5. Legal/governance review addresses organization verification and project/funding authority without presuming PWC can override member organizations or applicable law.
6. Approved physical schema and explicit migration plan may then be implemented; next companion deliverables: Django API Contract v1.0, Flutter Frontend Architecture v1.0 and Development Execution Plan.

---

## Appendix A — Traceability to PWC source documents

- **PWC Strategic & Product Foundation v1.0 Draft:** provisional policy, memberships, finance, NGO autonomy, M1–M3.
- **PWC App Information Architecture & Navigation v1.0 Draft:** client contexts, public/NGO/alliance/ops journeys.
- **PWC Detailed Mobile & Web Screen Specification v1.0 Draft:** public and NGO screens, 10 high-risk workflows, mobile/web operations.
- **PWC Identity, Authorization & Multi-NGO Data Model Foundation v1.0 Draft:** domain objects, jurisdiction separation, tenant/scoped access, finance invariants, 23 threat-oriented tests.
- **Coventure Django Backend Foundation v1.0:** reference for modular Django, DRF, PostgreSQL, service boundaries and infrastructure discipline only; PWC-specific business rules above control.

**Document ends — v1.0 draft for review, not code, migrations or approved physical database DDL.**
