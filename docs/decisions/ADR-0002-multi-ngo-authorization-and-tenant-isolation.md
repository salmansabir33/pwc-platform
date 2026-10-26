# ADR-0002 — Multi-NGO authorization and tenant isolation

**Status: APPROVED — CORE MVP ARCHITECTURE; IMPLEMENTATION CONTRACTS SUBJECT TO DOCUMENTED GATES**

**Approval date:** 24 October 2026

**Approval authority:** Product owner, explicit PWC-02C continuation assignment.

**Approval scope:** Technical principles and synthetic-only personal/NGO kernel contracts
below. Institutional, operational, finance, signatory, governance, sharing and support
policies are not approved by this status. No implementation is performed or started here.

**Product-policy addendum — 27 October 2026:** The product owner's explicit consolidated owner-approval instruction adopts concrete NGO authority product direction and conditionally endorses cross-owner recommendations as individually recorded for E01–E18 and GM01–GM12 in [the consolidated matrix](../reviews/PWC-02E-VERIFICATION-AUTHORITY-DECISION-REGISTER.md#8-consolidated-product-owner-approval--27-october-2026) and [ADR-0004](ADR-0004-ngo-verification-and-representative-authority.md). This supplements, **does not expand**, the original 24 October core/synthetic implementation approval above. It does not approve command atoms/bundles, nonpersonal proofs, schema/writer/lock contracts, independent security/NGO-governance/legal/privacy/operations gates or real activation. D03/D05/D08–D10/D12–D14 retain their applicable non-product blockers; D04/D06/D07 finance/signatory/governance powers remain separately gated. Original D decision IDs, technical invariants and historical register are preserved. No legacy/synthetic promotion or runtime change follows.

**Date:** 2026-10-24

**Ticket:** PWC-02C; P1 architecture and contract decisions

**Repository:** `salmansabir33/pwc-platform`

**Verified base:** `origin/main`, `889fc2f6a6bddd384bcf7c3f907eb693459ddfd1`

**Working branch:** `arena/d8a3e024-pwc-platform`

**Decision owner:** Product owner and designated NGO/security/governance reviewers

**Implementation:** None authorized by this document. No new routes, grants or privileges exist as a result of this ADR.

## 1. Existing repository assessment and source authority

### 1.1 Verified starting point

A fresh fetch confirmed clean branch HEAD exactly equals latest origin/main at the
base above. GitHub PR #3 is MERGED, with that merge commit. The merged tree contains
PWC-03A.1–03A.4 and the integration-review corrections, not just an authentication
proposal. Preserve the original implementation and history:

| Existing component | Observed capability | Limitation / preservation requirement |
|---|---|---|
| `accounts.User` | UUID AbstractUser; auth epoch, recovery generation and persistent holds; identity contacts separate | Keep UUIDs, hashes, usernames, FKs and authentication semantics; one account across NGOs |
| `Organization` | UUID, name/city, registered/unregistered classification | Classification is neither eligibility verification nor representative authority |
| `OrganizationWorkspace` | One-to-one Organization; provisional/pending/verified/restricted/deactivated | Existing workspace PK is BigAutoField, not a UUID; use Organization UUID externally; do not replace identities |
| `OrganizationAccess` | User/organization FK, claimant/admin/members labels, active flag; unique organization/user/role | No validated authority provenance, action permissions, grant expiry, delegation or finance semantics; labels are NOT trusted authorization |
| Public organization views | AllowAny read-only projections of verified workspaces; four public fields | No private tenant endpoint or full consent/publication policy; do not widen projection |
| Authentication | Verified contacts, registration/reset, web CSRF/cookies, opaque mobile credentials, refresh rotation, online registry/epoch/factor checks | Default-off synthetic implementation; delivery/deployment/client release gates remain |
| MFA and assurance | TOTP, recovery codes, single-use exact personal-operation proofs; hold clearance and cookie rotation safeguards | `accounts.mfa.OPERATIONS` and `scope()` reject nonpersonal operations; there is NO generic NGO-proof integration today |
| `PersonalAuthentication` | Explicit DRF adapter backed by online session validation; cookie/Bearer separation | Not a business permission class; its request-level transaction does not protect a later domain write |
| Migrations | accounts 0001–0006; organizations 0001–0002 | Preserve every applied migration; 0006 protects used preauth metadata on reversal |
| Tests | Eight public-directory foundation cases; authentication constraints, workflows, races and integration regressions | Finance-named scaffold test checks a role value, not finance authorization; no private tenant/finance/import API acceptance yet |

The committed [authentication integration review](../reviews/PWC-03A-AUTHENTICATION-INTEGRATION-REVIEW.md)
records historical 247-test PostgreSQL acceptance. This design-only task does not
claim to rerun that suite or implement its future tenant integrations. Root AGENTS
and older roadmap status paragraphs predate merged authentication; those descriptions
are historical, not evidence that auth must be rebuilt. The current explicit task
branch supersedes AGENTS' old session pin. Neither document is edited here.

### 1.2 Requirements and traceability

Read with the repository's authority hierarchy, not as independent approvals:

- [AGENTS](../../AGENTS.md): NGO independence, no staff/finance shortcuts, PostgreSQL,
  backend enforcement, preserve identities/migrations and provisional decisions.
- [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), §§1–3:
  PWC-02C gates PWC-03B; PWC-03C contracts, PWC-02D web and PWC-02E verification
  decisions remain separate; full G1a includes future private isolation acceptance.
- [Strategic/Product Foundation](../product/PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md),
  §§1–5 and governance/release gates: NGO autonomy, personal multi-affiliation,
  distinct administrative jurisdictions and voluntary commitments.
- [Identity/Multi-NGO Foundation](../product/PWC_Identity_Authorization_and_Multi_NGO_Data_Model_Foundation_v1.0_Draft.md),
  §§2–4, 8–10, 12, 14–16: scoped relationships, imported people, explicit finance,
  authority recovery, independent commitments, support and negative-test requirements.
- [Django/PostgreSQL Foundation](../product/PWC_Django_Backend_and_PostgreSQL_Schema_Foundation_v1.0_Draft.md),
  §§1–4 and schema/security sections: modular monolith, scoped services, UUIDs,
  FK/ownership constraints and transactional side effects. Its illustrative auth
  tables are superseded by executable ADR-0001 implementation, not recreated here.
- [Information Architecture](../product/PWC_App_Information_Architecture_and_Navigation_v1.0_Draft.md),
  §§1–5, and [Screen Specification](../product/PWC_Detailed_Mobile_and_Web_Screen_Specification_v1.0_Draft_for_Review.md):
  ID-03/04 affiliations/switcher; ORG-01–06 and ORG-25 authority/settings;
  FIN-01–09 finance; COM-01–04, COL-01–05, PWC-01–05, GOV-01, OPS-01;
  HF-01/03/05/07/08/09/10 and §5 information-disclosure requirements.
- [Approved authentication ADR](ADR-0001-authentication-and-recovery.md), §§7–9:
  online authority, compatible locks, bounded operation proofs, hold restrictions
  and no business authority from authentication. File SHA256 preserved:
  `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
- [Existing open decisions](OPEN-DECISIONS.md): verification/recovery, granular
  permissions, storage/support, public disclosure, finance and signatories remain
  unresolved. §12 below records scoped approval and gates; it does not close or
  silently revise the existing register.

The product owner approved shared-schema Django/PostgreSQL, centralized deny-first
checks, explicit NGO context, queryset/object/field isolation, small pinned bundles,
current-database expiry/revocation, provenance/audit, no legacy promotion, unsupported
context/action denial, and no positive authorization cache or unrestricted multi-hop
delegation on **24 October 2026**. Only synthetic accounts, organizations and resources
may exercise the initial kernel. No automatic administration or real NGO claims.

Approval is not retroactive approval of every illustrative future design. **Precedence:**
§§3.2–3.3, 4.5, 5.3–5.4, 8, 10 and 12 define the resolved initial contract; other
model catalogs, finance, alliance, support, files and workload material describe gated
future extensions only. Source [S]/[R]/[O]/[D] labels in draft references remain unchanged.
This ADR does not approve bylaws, legal standing, financial authority, onboarding
evidence, retention periods or technical support governance.

## 2. Core security and governance invariants

1. Authentication identifies a human; MFA establishes bounded assurance. Neither
   grants membership, administration, representation, finance, support or signatory rights.
2. NGO membership, standing volunteering, event participation, workspace access,
   representative mandates and institutional alliance membership are separate records.
   One does not manufacture another. A finance employee need not be an ordinary NGO
   member, but must have separately authorized finance access.
3. NGO A and NGO B remain independent tenants even for the same person. A permission
   in A is not usable in B; no global `isAdmin`, default organization or master-NGO shortcut.
4. Board/officer/committee authority governs only its assigned PWC context. Alliance
   membership, PWC verification or PWC project approval grants no NGO-private access.
5. `is_staff`, `is_superuser`, Django Groups, professional titles and login portal
   names are not business authorization. No unrestricted admin site for business staff.
6. NGO workspace administration excludes finance visibility, transaction approval,
   financial delegation and legal commitments unless separately granted.
7. Organization legitimacy/eligibility, representative authority, operating grants,
   legal signatory mandate and public publication are distinct decisions.
8. Verified email/phone, domain ownership, similar names or matching imported data
   do not prove NGO leadership, representation, membership or record ownership.
9. A request needs explicit, valid context AND action permission AND matching object
   ownership AND lifecycle/field policy AND required assurance. Ambiguity denies.
10. Lists, counts, searches, related resources, files, jobs, exports and notifications
    enforce the same boundaries as object writes; navigation is never enforcement.
11. No authority escalation from self-delegation, broader role bundles, context switching,
    grant replay, cached capabilities, MFA recovery, new factors or support overrides.
12. NGO commitments require that NGO's authorized approval of the exact version.
    An offer, invitation, public interest or PWC approval is not a binding acceptance.
13. Revocation/expiry overrides grants and assurance. Historical evidence is preserved;
    losing authority does not rewrite executed financial or legal history.
14. Public visibility is a separately approved projection, not a bypass around private
    field/file permissions. Alliance exit and NGO software-workspace exit are separate.

## 3. Authorization context architecture

### 3.1 Recommended approach and alternatives

Recommend a **shared PostgreSQL modular Django monolith**, an `access` domain with
closed permission registry and explicit contextual role assignments, plus domain
services for object/lifecycle rules. Use maintainable DRF authentication/permission/
queryset patterns, not a general policy language, arbitrary expressions or a large
custom policy engine. RBAC supplies named action bundles; small explicit predicates
supply relationship, object, lifecycle and field constraints.

Rejected as primary designs: UI-only gates; User groups as global NGO roles;
JWT/cached claims as current authority; a per-user current-NGO field as implicit
scope; generic nullable tenant fields; platform-wide admin inheritance; adopting
an external policy engine without demonstrated need. Database-per-NGO adds migration,
cross-context and operational complexity without current evidence of need.

PostgreSQL RLS is **not active**. Consider it later as defense-in-depth for high-risk
tables after transaction-local context, pooled connections, workers, migration/DB
roles and fail-closed tests are reviewed. Do not use session-level tenant settings
that leak through reused connections; RLS would not replace service authorization.

### 3.2 Closed contexts, ownership and boundaries — D01 resolved

Only two context kinds are active in PWC-03B.1:

| Kind | Canonical representation | Authority rule |
|---|---|---|
| `personal` | Server-resolved authenticated User UUID | Existing ADR-0001 personal ownership and operation policies; no NGO grant implied |
| `ngo` | `/api/v1/ngo-contexts/{organization_uuid}/…` | Typed Organization FK through the kernel state; current qualifying grant required |

Use an immutable in-process `ResolvedContext(kind, subject_uuid)` value created by the
server, never a caller-supplied permission object. Do not add a generic context registry,
personal grant rows or polymorphic target FKs in .1. Existing Workspace BigAutoField
remains internal; Organization UUID is canonical externally. Alliance, committee,
project and operations contexts, service principals and all unknown kinds deny.
Future typed registries require additive review; no fabricated disabled context rows.

Private tenant tables have a mandatory Organization FK. Parent/child references must
have the same organization, enforced by composite FK/constraint or a reviewed database
trigger when introduced. A normal FK alone does not prove tenant equality. No private
resource with nullable tenant ownership is allowed in this kernel.

### 3.3 Context selection and switching — D11 resolved

The path Organization UUID is the sole authoritative NGO selector. No ContextSelection
model, selection token, required selection header or server-side remembered tenant in
.1. A frontend may remember a UUID locally as display state; every request still carries
the explicit path and is independently validated. There is no User.current_organization,
default tenant, tenant inferred from an object ID, or last-selected fallback.

Tenant ownership fields in write bodies are forbidden; a future parent identifier is
resolved only within the path tenant. Reject unexpected context/selection headers and
conflicting tenant query/body fields with 400; never use them to retarget a request.
Personal endpoints cannot dispatch NGO actions. Switching is a client navigation change,
not an authority mutation, session renewal, proof issuance or idle keepalive.

Client caches must be partitioned by identity and organization; cancel/tag requests,
discard late responses and clear private state on switch/revocation/logout. Selection
persistence cannot make an expired, revoked or unsupported context valid. .1 correctness
does not depend on a frontend implementation.

## 4. Proposed data model, roles and organizational authority

**Documentation contracts, not implemented migrations.** Sections 4.1–4.4 retain the
future logical catalog, not the .1 model list. Section 4.5 is the minimal .1 schema
contract; do not build the wider catalog in anticipation of later phases.
Use UUIDs for new records, UTC dates, protected historical FKs, bounded enums and
integer versions. Preserve existing Organization/Workspace identities and access
rows pending reviewed mapping; do not reinterpret `active=True` as verified authority.

### 4.1 Relationships and evidence

| Proposed record | Essential relationship and invariant |
|---|---|
| `OrganizationPersonRecord` | NGO-owned unclaimed/imported person; nullable explicitly verified linked User; source/notice/provenance; no cross-NGO automatic merge |
| `OrganizationMembership` | NGO + person record; category/status/validity; independent of User and operating grants |
| `OrganizationVolunteerEnrollment` | NGO + person; independent of membership and one-off activity participation |
| `OrganizationAuthorityMandate` | NGO + User + purpose (admin, grant-authorizer, finance-authorizer, signatory) + evidence reference, verifier, validity, state, version and delegation bounds; verified status does not itself create permissions |
| `OrganizationAuthorityChangeRequest` | Purpose, expected authority version, proposed change, independent evidence/approvals and outcome; no unilateral staff leadership replacement |
| `PWCInstitutionalMembership` | Organization ↔ alliance; separate classification/eligibility/term; does not create NGO access |
| `InstitutionalRepresentative` | Organization's approved alliance representative for specified purpose/term; not automatically an NGO operating administrator or legal signatory |
| Committee/project participation | Exact User/organization/context/role relationship and validity; only context-local rights |

Keep registered and eligible unregistered verification tracks separate without
assuming a registered label proves current representation. A pending/provisional
or unclaimed record has **no private operating authority**. A claimant may access
only its own claim/draft/evidence channel under claim-specific ownership rules,
not an existing tenant's records, grant creation, imports, finances or commitments.
Claim evidence is not public merely because the Organization is listed. Own claim/
draft access is a personal, applicant-owned channel, not entry to the claimed NGO
operating context; detailed onboarding contracts belong to PWC-02E/P3.

A future verification service must independently record organization eligibility
and representative mandate decisions. Activating a workspace does not issue grants.
Issuing an initial admin grant requires approved authority provenance and a separate
audited transition, even if one reviewed transaction eventually records both.

The bootstrap cannot require a nonexistent prior administrator or invent a platform
superuser exception. Recommend a single-use initial-activation authorization tied to
an independently reviewed NGO mandate, exact initial admin bundle/recipient and
case/policy version. A specifically authorized verifier executes that approved
transition; it grants the verifier no NGO access and cannot initialize finance or
signatory authority. Reject self-reviewed or replayed activation. The evidence,
approvers and independent NGO consent for this root transition are D03 blockers;
there is no live bootstrap path until approved. Later changes use ordinary scoped
grant-management authority and its provenance checks.

Allow multiple administrators through separate grants, not a single User FK owner.
Admin rights can be delegated to specified tasks/expiry, without signatory or
finance authority. Losing the last admin never authorizes automatic promotion of
another member, finance user or platform operator. Security revocation must not
be blocked just to retain a last administrator: freeze affected operations and use
reviewed recovery. Contested control blocks authority changes/commitments and other
high-risk operations conservatively; precise dispute read/continuity rules require
approval (§12). Support may preserve evidence/suspend risk, not decide NGO leadership.

### 4.2 Permission and grant records

| Proposed record | Contract |
|---|---|
| `PermissionDefinition` | Unique closed code, domain, allowed context kinds/resource types, action and sensitivity; version-controlled registry, no wildcard/caller-created codes |
| `RoleDefinition` / immutable `RoleVersion` | Domain/context type, code, pinned version; explicitly enumerated permission set; no silent privilege expansion when a definition changes |
| `RolePermission` | Unique role-version/permission; only matching namespace/type permitted; no runtime arbitrary predicates or unreviewed custom role editor |
| `ContextRoleAssignment` | Context FK, User FK, pinned role version, authority/provenance, issuer, validity, active/suspended/revoked state, optional bounded resource scope, revision and revocation evidence |
| `DelegationLink` | Parent assignment/mandate and approved subset; source must remain live, child expiry no later than source; default no redelegation; no cycles or self-created root authority |
| `ContextAuthorizationState` | One per context; monotonically increasing authorization revision; lock/serialization root for grants, lifecycle, authority, sharing and policy changes |
| `AuthorizationPolicyVersion` | Context-specific immutable policy version and effective state; governs delegation/approvals/assurance; missing required policy denies |
| `ContextSelection` | User/logical session/context + creation/expiry; no embedded permission authority |
| `AuthorizationEvent` | Actor/principal, context, action/result/reason, target/version references, authority/grant/policy revisions and correlation; append-oriented, no secrets/raw document bodies |
| `SupportAccessApproval` | Separate narrow tenant/resource/action scope, ticket/purpose, independently approved actor, short expiry, assurance and review evidence; disabled until procedure approved |
| `ServicePrincipal` / `ServiceAssignment` | Non-human workload identity, exact scopes/actions/purpose, expiry/revocation, credential reference and audit owner; never a synthetic superuser User |
| `AuthorizedJob` / export metadata | Requestor/session provenance, context, command/object versions, required permissions, policy/revisions, execution purpose and output ownership; snapshot is audit evidence, not permanent authority |

Grant creation requires a distinct grant-management permission, verified applicable
authority, approved delegation bounds and any required independent approvals. Having
permission to perform an action does **not** imply permission to delegate it. General
`ngo.access.manage` excludes `ngo.finance.access.manage` and signatory powers.
An admin may not use role editing, import, invitation or an API bulk action to give
themselves finance/signatory privileges. Root finance/bootstrap authority cannot
be derived from an earlier self-granted role. Revoked/expired parents disable child
delegations without waiting for asynchronous propagation; evaluation checks live
provenance. Recommend no multi-hop delegation initially; approval needed to widen it.

Do not require ordinary NGO membership as a universal prerequisite for all staff
roles; requirements are role-specific mandates/relationships. Conversely, active
membership alone is not an administrator grant. Where approved member-only content
policy derives access from membership, express that predicate explicitly and limit
it to content/self-records, not the complete roster or administrative workspace.

### 4.3 Illustrative bundles, not adopted institutional titles

| Bundle | Possible atoms | Deliberate exclusions |
|---|---|---|
| Member-content reader | Member-visible content and own claimed record under approved membership policy | Roster export, admin, finance, grants |
| Member manager | `ngo.members.read`, `.write`, `.import` if expressly included | Finance, volunteer scope by implication, identity claiming bypass |
| Volunteer coordinator | `ngo.volunteers.read`, `.manage` | Formal membership creation, finance |
| Workspace administrator | `ngo.workspace.configure`, `ngo.access.manage` with approved limits | Finance, signatory, all data by wildcard |
| Finance reader/recorder/approver/access-authorizer | Separately chosen §6 atoms and resource bounds | None of these implies all the others |
| NGO signatory | Explicit approved commitment action and mandate bounds | Operating/finance visibility or payment authorization by title alone |
| Committee convener / Board officer | Exact committee/alliance actions | Independent NGO authority |
| Technical operator | Scoped platform metadata/security operations | Business access absent separately approved support grant |

### 4.4 PostgreSQL constraints and indexes

- Typed context target FKs with exactly-one and kind/target consistency CHECKs;
  one registry context per target. NGO-local scope rows carry organization_id and
  enforce target ownership. An ordinary FK alone does not prove equal tenant ownership.
- Unique permission code, role code/version and role-version/permission pair.
  Pin assignment to immutable version. Type/namespace compatibility validated by
  services; use typed relational structures/constraints where joins are enforceable.
- CHECK validity `valid_until > valid_from`, consistent revoked timestamp/state,
  positive revisions, closed kinds/states; server UTC is authoritative. Expiry is
  checked at evaluation time, not dependent on a scheduled state-flip job.
- Avoid a naive partial unique “currently active by now()” index. Prefer unique
  grant identity plus an explicit current-slot/lineage model for competing versions;
  preserve historical assignments. Final duplicate/overlap policy is reviewed before migration.
- Tenant-first indexes on `(organization_id, id)`, `(organization_id, state, ...)`;
  grant indexes `(context_id, user_id, state, valid_until)` and reverse workspace
  listing `(user_id, state, context_id)`; event/job indexes by context/time/requestor.
- For same-tenant parent/child links, prefer composite UNIQUE `(organization_id,id)`
  with composite FK, via reviewed additive SQL where Django cannot express it.
  Service checks remain mandatory; do not assume `full_clean()` runs on save/bulk writes.
- No cascading destruction of mandates, decisions, posted finance, approvals or
  authorization evidence. Soft revocation and reviewed retention, not log deletion.

### 4.5 Resolved PWC-03B.1 additive schema and vocabulary — D02/D03/D09/D14

#### Minimal records

All new rows use UUID PKs, aware UTC timestamps, protected historical FKs and bounded
enums. Preserve accounts and organizations migrations unchanged. Suggested Django names
below are the implementation contract, not permission to create them in this task.

| Record | Required fields and database invariants |
|---|---|
| `NGOKernelState` | OneToOne Organization (PROTECT); immutable fixture batch UUID and evidence reference; created_at; `revision` bigint >=1; `mode` = `disabled` or `synthetic`; default disabled. This is the per-tenant lock root. No `real` mode in .1. Absence denies. |
| `SyntheticPrincipal` | OneToOne User (PROTECT), fixture batch UUID, non-sensitive evidence reference, created_at. Explicit synthetic-account attestation, not inferred from username/email. Immutable; no API to label existing real users. |
| `NGOGrant` | Organization, subject User, `role_code`, `role_version`, `scope_kind=organization`, `source_kind=synthetic_fixture`, `source_ref`, fixture batch UUID, `issuer_process=kernel_fixture_v1`, nullable issuing actor User, `verification_status` (`synthetic_verified` or `unverified`), `approval_evidence_ref`, `effective_at`, mandatory `expires_at`, `created_at`, `revision` >=1, `revoked_at`, `revoked_by` nullable User, `revoked_by_process`, `revocation_reason`. Issuing actor or allowlisted process required; process is always recorded for fixture creation. No runtime external verification or issuer self-assertion. |
| `AuthorizationEvent` | Organization (nullable only for discovery or unknown-context denials), actor User/session references where known, actor process if offline fixture, action, result, reason code, target UUID, grant UUID and role version if applicable, old/new context and grant revisions, fixture batch, correlation UUID, DB timestamp, non-sensitive evidence reference. Immutable append-only application interface. Historical FKs PROTECT; no raw commands or credentials. |

`NGOKernelState.mode=synthetic` attests that the organization is synthetic; its creation
must be in an explicit isolated fixture batch, not by relabeling a real organization.
The factory atomically creates new synthetic User/Organization records, attestations,
verified fixture Workspace, state root and creation audit; it cannot enroll an existing
real entity. Once created, batch/evidence/identity bindings are immutable. The only
later state-mode transition in .1 is synthetic → disabled (terminal); reenabling
requires a new fixture tenant, not toggling an old state. Root creation uses Organization
uniqueness within the factory transaction; no runtime get-or-create-on-missing fallback.
Only dedicated test/development databases may enable `PWC_SYNTHETIC_AUTHORIZATION_ENABLED`
(default false). Runtime requires the flag, synthetic state, synthetic subject attestation,
matching fixture batch and `source_kind=synthetic_fixture` together. Ordinary deployed
settings must not enable it. No automatic grant seeding on migrate/startup; no general
management command that can nominate arbitrary existing real accounts or NGOs. Test
fixture factory creates its own new accounts/organizations and records provenance; it
is not a production grant issuer. Missing or inconsistent synthetic attestations deny.
This boundary is an application/release safeguard, not protection against a malicious
DB owner; environment separation and release configuration checks remain mandatory.

Grant DB constraints: expiration > effective time and no more than 24 hours after effective time (synthetic fixture lifetime, not a real authority policy); role/version pair in the two frozen
pairs below; only the organization scope and listed source/verification values; positive
revision; nonempty source/evidence/process references; revocation is either entirely
absent or has timestamp, nonempty reason, and actor or named process. Partial unique
index on `(organization, subject, role_code, role_version)` WHERE revoked_at IS NULL.
Expiry/unverified rows occupy that slot until explicitly revoked; no time-dependent
partial index. Index `(organization, subject, revoked_at)` and `(organization, expires_at)`.
No hard delete, un-revoke, in-place role/scope/provenance/validity change or expiration
extension. Replace with a newly approved grant after revocation; UUIDs never reused.
Revocation is terminal and increments grant and tenant revisions exactly once.
Unknown role versions inserted by unsupported writers fail constraint/evaluation.

Cross-row synthetic eligibility is checked under the tenant lock by the only fixture
writer and independently on every evaluation. It is not falsely claimed to be enforced
by a single-row CHECK. Runtime application role cannot write grant/state/attestation
rows directly; future migrations must specify separate fixture-writer privileges and
an append-only audit writer. Django admin/bulk updates/raw SQL are not approved mutation
paths. DB-owner/migration credentials are outside runtime trust. PostgreSQL privilege
and trigger enforcement of immutable fields/revocation and audit update/delete denial
must be included in .1 migration acceptance, not left as an ORM convention.

#### Frozen closed registry: `ngo_kernel_v1`

Role bundles and permission registry live in version-controlled Python constants in
.1, not editable database policy tables, role editors or arbitrary JSON predicates.
No `PermissionDefinition`, `RoleVersion`, delegation, mandate, selection, support,
policy-engine or service-principal tables are required in .1.

| Server action | Exact meaning |
|---|---|
| `ngo.context.enter` | Enter/discover this synthetic NGO context; no domain data implied |
| `ngo.private_stub.read` | Read fixed non-sensitive synthetic probe projection in this NGO |
| `ngo.kernel_settings.read` | Read non-sensitive synthetic kernel settings projection only; not grants, people or security evidence |

| Role code / pinned version | Exact actions |
|---|---|
| `ngo_kernel_reader` / `1` | `ngo.context.enter`, `ngo.private_stub.read` |
| `ngo_kernel_admin_probe` / `1` | Reader actions plus `ngo.kernel_settings.read` |

The second bundle tests administrative separation; it is **not** a real NGO administrator
appointment and has no management/write/delegation powers. Membership/volunteering,
legacy `admin`/`members`/`claimant`, Board, staff, superuser, Groups and portal labels map
to neither bundle. No finance, signatory, governance, audit-reading, people, import,
file, export or grant-management action is in the registry. Unknown actions deny even
if a stale/forged role or MFA proof names them. Bundle version 1 is immutable; future
expansion creates a new reviewed version and new explicit grants, never changes v1.

Effective permissions are the union of live eligible grants **in one NGO**, minus all
hard denies. Each grant independently authorizes its complete action and bounds; never
combine one grant's scope with another's limits. .1 has organization-wide scope only:
no per-object/amount/account limits, allow wildcards, direct user permission exceptions,
custom roles, deny-grant language, parent grants or delegation. No live issuance,
revocation endpoint or self-service grant management. Revocation exists as a tested
fixture lifecycle service; its future human command requires separate permission and
assurance approval. A new grant after revocation is a new, explicit fixture event, not
an upsert that revives a revoked row.

#### Minimal private category

`NGO_PRIVATE_SYNTHETIC_V1` contains only bounded constant probe data and settings labels
for the synthetic NGO. Projection: organization UUID, fixed probe code, non-sensitive
label and context revision. No names/contact details/rosters/beneficiaries, free text,
financial balances, evidence documents, private files or exports. .1 can use in-memory
probe objects tagged with the Organization FK identity and tenant-filtered state rows;
no general-purpose private content model is needed. Both queryset and direct-object
helpers must demonstrate scoped lookup of the state/probe; foreign UUID and absent
UUID have the same outcome. Adding real private categories needs D09 classification,
consent, retention and field policy decisions before implementation.

## 5. Permission evaluation and enforcement contracts

### 5.1 Deny-first algorithm

All entry points use the same authoritative services; return internal structured
decisions, not only a boolean, but redact public reasons as §8 defines:

1. Authenticate exactly one allowed transport using existing personal auth. Reject
   inactive/expired/revoked/epoch-invalid sessions, invalid factor state and mixed
   credentials. Revalidate in the private-read/command authorization transaction,
   not only an earlier adapter transaction; request.user is not a grant. For workload
   calls, independently authenticate a live ServicePrincipal instead, apply §9.2's
   scope intersection, and reject human-only approval/assurance operations. A service
   cannot fabricate a User session or assert it has completed human MFA.
2. Resolve the explicit path context and principal binding (§3.3). Missing/conflicting/unknown kind,
   inactive target, ambiguous ownership or incompatible route denies. No default tenant.
3. Apply account recovery restrictions and context lifecycle/dispute/suspension gates.
   For the approved synthetic kernel, held/recovery-code sessions may use approved
   restricted personal flows only; all NGO discovery, projections and private access
   require clear hold. Never weaken ADR-0001 or let fresh MFA override a hold.
4. Resolve required action from a server-owned endpoint/command registry. Unknown
   action or disabled implementation/policy denies. Clients never choose the action
   code to authorize their own requested operation.
5. Query only that context's live, applicable, pinned grants and source mandates/
   delegation chain. Require appropriate relationship predicates, validity and
   resource bounds. Independent eligible grants may union allowed atoms **within
   that context**; hard lifecycle/hold/dispute/deny restrictions always override.
   An absent permission is a deny, not a prompt to search other contexts for it.
6. Scope queryset before lookup/filter/pagination/count/aggregation; verify parent,
   resource ownership, classification, permitted fields and object-state transition.
   No broad object lookup followed by a tenant check that leaks existence.
7. For future approved privileged commands only, require approved action-specific assurance where mapped (§6). Proof is necessary,
   never sufficient. No proof is consumed to operate on a foreign/unauthorized object.
8. Under compatible locks, recheck current authority/policy/grant/object versions,
   session deadlines and approval/separation-of-duty predicates. Enforce idempotency.
   Perform mutation, consume exact assurance, increment affected authorization
   revisions and append security/business evidence in one atomic transaction.
9. Before final commit check original authentication/proof/grant/mandate validity
   cutoffs; do not renew idle or extend a deadline to salvage stale authorization.
   Roll back provisional changes if validity expired. Publish side effects via
   on-commit/durable outbox, never external I/O while authority locks are held.

No arbitrary “deny grant” policy language initially. Explicit hard restrictions
have precedence over allow bundles; if future per-object denial overrides are
needed, define/test precedence rather than mixing ad hoc view exceptions.

### 5.2 Django/DRF and query boundaries

Proposed interfaces: `resolve_context(principal, route_kind, organization_uuid)`;
`authorized_queryset(principal, context, action, model)`;
`authorize_object(principal, context, action, object)`; transactional
`execute_authorized_command(...)`. Names are contracts, not implemented functions.

- Explicit `PersonalAuthentication` plus an action-mapped DRF permission class on
  every future private view. No reliance on default SessionAuthentication alone.
- `get_queryset()` starts scoped, including list/search/count/autocomplete. DRF
  object permission checks do not automatically protect lists or create operations.
- `perform_create`/domain service assigns owning context server-side; bulk/nested
  serializers reject foreign related IDs and unknown privilege fields. PATCH cannot
  move an object to another tenant. Nested URLs revalidate parent-child ownership.
- Serializers select field-level projections per action/classification; a permitted
  public project never exposes internal budget actuals, donors, members or private files.
- Domain services are authoritative for HTTP, management commands and jobs; view
  permissions are defense-in-depth, not the sole check before a later write.
- New private endpoints stay disabled until mapped actions, policies and negative
  tests exist. No claim that this ADR registers these permission classes globally.

### 5.3 Concrete PostgreSQL transaction, revision and audit protocol — D13

READ COMMITTED on the primary database; no replica, positive permission cache, process
mutex or check-then-write outside the transaction. Immutable registry constants may be
cached, never current eligibility. Every path, including tests/management/migrations,
that changes authorization state must follow this protocol or remain unavailable.

1. Resolve untrusted selectors without returning domain data, then start `atomic`.
   Preserve ADR-0001 lock prefix: **User(s) UUID order → active contact/factor rows stable
   ID order → AuthSession(s) UUID order → auth challenge/credential/intent rows in the
   existing auth helper order → NGOKernelState by Organization UUID → NGOGrant UUID →
   domain rows UUID → insert audit**. Ordinary .1 reads need only requesting User,
   current session/credential rows required by auth, and one state root. Fixture writes
   lock all affected subject/issuer Users up front; offline fixture work has no session
   and cannot impersonate a human request. Never lock a target User after a state root.
   No multi-tenant runtime command in .1. No auth helper that acquires earlier locks
   may be called after the domain root; audit actual helper call order in .1 review.
2. After locks are acquired, re-read active identity, logical session, epoch, transport
   credential generation, hold, deadlines, synthetic flags, workspace lifecycle and
   current grants from primary DB. Request adapter validation alone is insufficient.
   Only existing Workspace `verified` plus state synthetic is eligible; fixtures may
   explicitly create verified synthetic workspaces. Registration classification never
   establishes eligibility. Missing/restricted/deactivated workspace denies.
3. For fixture authority changes require expected tenant revision; for revocation also
   expected grant revision. Compare under lock before mutation. Missing precondition
   fails; stale value conflicts. Serialize all grant creation and revocation through
   the same state root, with the partial unique constraint as a second guard. Increment
   state revision on every creation, first revocation or synthetic lifecycle change.
   Immutable definitions never change in place. No independent expiry writer needed.
4. Grant eligibility is `effective_at <= clock_timestamp() < expires_at`, unrevoked,
   synthetic_verified and fully attested. Use DB wall-clock after lock wait, not
   transaction-start `now()`. Bound reads and materialize selected scalar projections
   under locks; no lazy ORM/serializer query after transaction exit, streaming or
   external I/O. Recheck original session/credential/grant cutoffs immediately before
   final decision/write and audit; deadline failure returns no protected data and
   rolls back provisional mutation. Expiry is checked even when revisions are equal.
5. Successful authority mutation and its audit event commit atomically. An audit insert
   failure rolls back mutation. Successful private reads/discovery also require durable
   access audit before releasing data; audit outage returns 503 with no protected body.
   Discovery locks eligible state roots in sorted order and rechecks grants; serialize
   only bounded pages (maximum 50). No foreign context details in denial events.
6. Denials/conflicts make no domain mutation. Record a bounded redacted denial event
   after rollback in a separate short transaction when necessary. If primary/audit is
   unavailable, fail closed with 503; safe external operational diagnostics are fallback
   telemetry, not a claim of durable DB audit. Configure lock timeout 2s, transaction
   statement timeout 5s for .1 acceptance. No silent retry after uncertain commit. A
   deadlock/serialization failure rolls back and returns retryable 503; client re-reads
   state before resubmitting. No .1 mutation API or idempotency-token system to invent.

Revocation linearizes at the locked authority transition: a read holding the root may
complete first; after revocation commits every newly authorized request denies. Bytes
already materialized/returned cannot be recalled. “Immediate” does not mean cancellation
of a read serialized before revocation. Expiry is evaluated at the final decision point,
not a guarantee about network delivery after the lock is released.

Audit schema records event IDs and revision transitions, never secrets or private
payloads. Runtime DB role has no audit UPDATE/DELETE and no direct grant UPDATE/DELETE;
reviewed narrowly privileged lifecycle functions/fixture role perform permitted writes.
Revocation/immutability triggers must reject resurrection even by a stale ORM save.
Fixture-only writer is absent from ordinary deployment credentials. Application `atomic`
alone is not a substitute for those privileges/constraints. Retention, legal holds,
operational monitoring and production throughput targets remain D13 release gates;
no automatic event purge in .1. Test data is disposable only as an entire isolated
synthetic environment, not by deleting individual security history rows.

### 5.4 Evaluation algorithm and deny precedence — D05 integration

For each protected request: authenticate existing supported transport → lock/revalidate
identity/session → require clear recovery hold → resolve exactly one supported context
→ require synthetic deployment/subject/tenant/batch and verified workspace → resolve
server-owned known action → query current tenant grants with pinned known bundles →
require `ngo.context.enter` and requested action → scope query/object by tenant and
classification → project allowlisted fields → recheck deadlines → persist audit and
materialize response → commit. A personal context uses only ADR-0001 personal rules,
not NGO grants. Discovery applies the same NGO entry predicates to each returned item.

Deny precedence is: unavailable authoritative dependencies (503, no fallback); invalid
authentication (401); malformed/conflicting context input (400); recovery hold (403);
unsupported/ineligible tenant, no entry grant or foreign/absent object (uniform 404);
known entered tenant but missing action/unsupported category (403); authorized target
with stale precondition (412) or invalid transition (409). Perform no target/version
lookup before entry authorization. Unknown action and disabled feature are always
hard denies, not inferred permissions. Deny beats every role, MFA observation and
stale capability. Authentication middleware's existing CSRF/transport errors retain
ADR-0001 semantics; do not normalize them into successful context responses.

| .1 operation | Auth/current grant | Hold clearance | MFA / step-up |
|---|---|---|---|
| Existing personal flows | ADR-0001 unchanged | Existing personal rules | Existing action policy unchanged |
| Discovery/entry/capabilities/probe/settings read | Active online session + current relevant NGO grant(s) | `clear` required | No additional recent MFA or operation proof for these non-sensitive synthetic reads; ordinary MFA login remains enforced |
| Fixture creation/revocation | Isolated offline test factory, not user API; attested synthetic batch and locked lifecycle service | Never a recovered-session escape route | No human assurance assertion; fixture-only provenance is not human authority |
| Live grant issue/revoke/delegate/admin transfer; finance/signatory/support/export | Disabled, no registry action or route | No override | Missing complete permission/retention/operation-bound assurance contract means deny |

Authentication/MFA never establishes NGO authority. No NGO intent is issued in .1;
`accounts.mfa.scope()` remains personal-only. Before any .2+ privileged command,
review its exact password+TOTP policy, retention, bound command/version/context and
lock-compatible intent integration. Preserve auth intent failure semantics: semantic
payload/version change invalidates the old intent and needs a new one; invalidation
and abuse counters must survive a rejected command. Transient transaction failure
rolls back provisional consumption; a committed success cannot execute twice. Do not
apply a blanket “all failures roll back intent invalidation” rule.

## 6. Financial authority separation and assurance integration

### 6.1 Explicit finance atoms

| Operation / screen | Proposed required atoms and bounds |
|---|---|
| Finance overview / FIN-01 | `ngo.finance.dashboard.read`; permitted aggregates only; no automatic donor/account detail |
| Cash/bank registers / FIN-02 | `ngo.finance.accounts.read`, `ngo.finance.register.read`; account-specific scope; separate `.accounts.manage` |
| Income/expenses / FIN-03/04 | `ngo.finance.income.record`, `.expense.record`, `.submit`; no implicit approval or export |
| Donations | `ngo.finance.donations.manage`; separate donor-private-field permission where approved; no platform donor-wide view |
| Membership dues / ORG-13 | `ngo.dues.manage` for assessments; separate `ngo.finance.dues_receipts.record` for authorized collection, NOT general finance visibility |
| Transfers / FIN-05 | `ngo.finance.transfer.submit` and mapped approve/post policy; validate both accounts in same NGO |
| Approvals / FIN-06 | `ngo.finance.approve` bounded by transaction/account/amount; `.post` where distinct; required independent approval count |
| Entry detail/corrections / FIN-07 | `.entries.read`, `.reverse`; immutable posted history, separately authorized correction |
| Reports/exports / FIN-08 | `.reports.read`, `.export`; neither dashboard nor entry access implies export |
| Policy/access / FIN-09 | `.policy.manage`, `.access.manage`; distinct root authority/provenance, not workspace access management |

No wildcard finance role. Bounds may include accounts, currencies, amount ceilings,
transaction kinds and validity. Server calculations enforce these bounds; a caller
cannot split transactions to evade an approval policy without detection rules.
Exact limits, aggregation rules and approval quorums require finance-policy approval.

NGO-selected `direct_entry` vs `approval_required` remains provisional source policy.
Direct entry still requires an explicit posting-capable grant; it is not global admin
access. Approval-required mode checks policy version, independent approved actors,
no prohibited self-approval and current authority at posting. No universal two-person
rule is silently imposed on NGOs eligible for approved single-authorizer mode.
Changing a policy cannot retroactively approve pending entries or broaden grants.

Dues confirmation requires a separate finance-authorized
`ngo.finance.dues_receipts.record` assignment before invoking the narrowly authorized
finance service to create one source-bound posting under the NGO's selected policy.
Membership/dues administration alone cannot invoke it or delegate that permission.
An expressly authorized collector still receives no general ledger read/create grant. Use unique source/idempotency keys,
validate selected account ownership and preserve pending/posted distinction. Fail
closed if policy cannot authorize that narrow integration. Do not implement the
ledger in the access kernel or expose bank balances through a dues endpoint.

Finance delegation/bootstrap/recovery requires an independently validated NGO
finance-authorizer mandate under the NGO's approved single/multiple-authorizer
policy. Admin, Board and platform roles cannot nominate themselves as finance root.
Immediate compromise revocation is allowed even for the last finance authority;
freeze affected activity and invoke reviewed recovery, not automatic admin inheritance.

### 6.2 Integrating existing operation-bound assurance

**Current compatibility gap:** auth's implemented assurance registry is personal-only;
existing `scope()`, `intent_command()`, `command_digest()` and `consume()` cannot simply
be called with arbitrary NGO context/action. Unknown operations presently deny, and
must continue to deny until an explicitly reviewed integration is implemented.

A follow-on contract must register each domain action with a validator/canonicalizer,
current-domain-authorization callback, resource/version binding and assurance policy.
Do not just append strings to `OPERATIONS`, bypass `scope()`, or add a client
`mfa_verified` flag. Reuse vetted auth primitives/lifetimes/ownership checks while
extending the interface and historical schema only via reviewed additive changes.

Suggested sensitive mappings (all proposed): finance approve/post/transfer/reverse,
financial access/policy delegation, sensitive exports, NGO admin/signatory transfers,
commitment acceptance/amendment and exceptional support elevation. Require password
plus still-active TOTP under ADR-0001's eligible live/recent observation rules;
proof ≤5 minutes and no later than original session/access/intent/grant/mandate cutoff.
The approved fresh-code hold-clear exception stays unchanged. Domain retention rules
must block protected actions when MFA is absent, not allow password-only fallback
following factor removal. The complete action/assurance matrix is an approval blocker.

Intent issuance authorizes the actor for the exact context/action/target/version/
canonical command using current grants. Proof binds logical User/session, auth epoch,
recovery generation, context, action, target/object version, policy/authorization
revision and keyed command digest. Secret fields never appear in ordinary audit or
stored raw command bodies. Final domain service rechecks all permissions/holds/
revisions under shared locks and consumes the exact proof atomically with mutation.
Changed amount/recipient/account/version/grant/context requires a new intent. Revoked
permission wins over valid MFA. Transient mutation failure rolls back provisional proof consumption; semantic
validation/state conflict invalidates the intent as required by ADR-0001 and §5.4;
owned successful replay is a conflict, not a second posting. Read-only permission checks
cannot substitute for this transactional boundary.

For queued commands requiring step-up, do not turn a short proof into an unbounded
worker credential: either execute the sensitive transition synchronously within its
proof deadline, or approve an explicit narrow, versioned execution authorization
whose semantics are separately reviewed. A normal export job's enqueue proof does
not authorize arbitrary later finance writes or bypass fresh download authorization.

## 7. Alliance, committees and cross-NGO collaboration

- Institutional alliance membership belongs to an Organization, not all its users.
  Board appointments/officer terms and committee assignments are distinct scoped
  records. Eligible voting representation depends on separately approved governance;
  electronic elections/national hierarchy remain deferred, not inferred from roles.
- Platform verification staff may decide an eligibility/evidence case under explicit
  permissions. Alliance admissions staff decide alliance membership. Neither can
  read NGO private operating records merely to perform their job.
- Committee members/conveners can access assigned meetings/proposals as granted.
  They cannot pledge NGO funds, volunteers, assets or legal authority by committee role.
- A joint/PWC project owns shared coordination data; each participating NGO retains
  its source records/ledger. Sharing requires an NGO-authorized, purpose/field/resource/
  audience/expiry-bounded `ProjectSharingGrant` and an explicit projection. Participant
  status is not blanket access. No all-tenant unions, raw shared storage paths or
  automatic cross-NGO roster/finance joins.
- Recommend versioned `NGOCommitmentPolicy`, `CommitmentProposal`, `ApprovalDecision`
  and `ProjectCommitment` records. Each participant NGO approves its own exact
  obligations with currently valid signatory/approval authority under its policy.
  Capture resource quantities, money/currency, scope, period, policy/version,
  required approvals and immutable accepted snapshot; validate mandate bounds.
- PWC approval only approves PWC's own undertaking. One NGO's approval cannot bind
  another. Interest/invitation/proposal is not acceptance; a public project badge is
  not permission to publish private evidence or bind a participating NGO.
- Final acceptance checks all approvals/current approver eligibility, conflicts of
  interest and object/policy versions in one transaction with the necessary NGO and
  project roots. Use an organization/proposal-version idempotency key; no duplicate
  commitment. Changed terms invalidate approvals and require a newly approved version.
  Admin status or MFA alone cannot supply signatory authorization.
- Revoking a signatory blocks future approvals immediately; it does not automatically
  cancel a legally accepted commitment. Withdrawal/amendment/cancellation follow
  separately approved agreement policy and preserve history. Emergency disputes freeze
  new high-risk decisions without pretending to adjudicate legal leadership.
- Sharing revocation stops new access/download/job output. Already delivered copies
  cannot be remotely recalled; retention/deletion obligations require agreements.
  Public/voluntary sharing is opt-in under approved publication rules, never a
  condition silently imposed by alliance admission or basic workspace activation.

## 8. Resolved initial API and frontend contracts — D11

These contracts are frozen for .1 service results and .2 HTTP adapters; they do not
assert endpoint existence. .1 builds no public-facing NGO API. .2 may expose only
synthetic read operations behind the same default-off environment gate, after its
assignment and PostgreSQL acceptance. No server selection persistence is needed.

### 8.1 Workspace discovery, selection and effective permissions

| Proposed .2 route | Contract |
|---|---|
| `GET /api/v1/me/ngo-contexts/` | Authenticated, clear hold; return only current eligible synthetic NGOs with `ngo.context.enter`. Cursor pagination, maximum 50, Organization UUID stable ordering. Empty 200 when none; never all registry organizations or legacy memberships. No private organization names needed. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/capabilities/` | Reauthorize entry; return context kind/UUID, registry version `ngo_kernel_v1`, current context revision, sorted effective action codes and earliest contributing grant expiry as advisory refresh hint. Not a bearer proof; expiry/revocation may invalidate immediately. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/private-probe/` | Requires `ngo.private_stub.read`; fixed §4.5 projection only. |
| `GET /api/v1/ngo-contexts/{organization_uuid}/kernel-settings/` | Requires `ngo.kernel_settings.read`; fixed synthetic settings projection only. |

No POST select route, header token or keepalive update. No HTTP grant-management route,
write stub or real business data. `Cache-Control: no-store` for all private responses;
no browser/shared-cache ETag validation that skips authorization. A capability projection
is informational only and cannot authorize the next request. Unsupported contexts have
no dispatcher/route and deny. Existing public directory endpoints remain unchanged.

### 8.2 Errors, preconditions and conflicts

Error envelope for new adapters: `{"error":{"code":"…","correlation_id":"…"}}`.
No foreign object identifiers, grant details or evidence in errors. Stable codes:
`invalid_context` 400 (malformed UUID, unexpected/conflicting context fields),
`authentication_required` 401, `recovery_hold` 403, `not_found` 404 (well-formed unknown,
ineligible/ungranted tenant or foreign/absent resource), `permission_denied` 403 only
inside an entered tenant, `precondition_required` 428, `revision_mismatch` 412,
`state_conflict` 409, `authorization_unavailable` 503. Existing authentication routes
retain their current schemas; no auth code changes in this task.

Read requests need no revision precondition; all reauthorize from current DB. Future
writes must supply `If-Match: "ngo:{uuid}:r{revision}"` and a target revision where
applicable; fixture lifecycle services take equivalent required integer arguments.
Missing is 428, malformed is 400, stale is 412, valid revision but invalid transition is
409. Entry/object authorization occurs before disclosing a current revision. A repeated
revocation may return an owned no-op result only when already revoked and the caller
supplies that current revision; never update audit/state twice. Unknown commit outcome
requires re-read, not blind retry/upsert. No idempotent replay of authority creation is
approved. .2 schema generation belongs to PWC-03C, not this documentation assignment.

## 9. Security, audit and non-HTTP threat analysis

| Threat | Required control |
|---|---|
| IDOR/BOLA, cross-tenant parent/child references | Scope before lookup; composite ownership constraints plus service validation; 404 absent/foreign |
| Role mass assignment / privilege inflation | Server action registry, pinned bundles, scoped grant-authorizer evidence; reject unknown grant fields/wildcards |
| Context confusion, two tabs, delayed mobile response | Explicit canonical path without authority-bearing selections, immutable captured request context; cache partitioning and response tags |
| Board/staff/deputy-as-superuser | No business inheritance; separate scoped grants and approved exceptional support path |
| TOCTOU revocation, stale roles/replicas | Shared context serialization, online primary DB checks, transaction-time validation and original deadlines |
| Valid proof reused in another action/NGO | Exact command/context/session/policy/version binding and atomic consumption; permissions rechecked |
| Imported-contact takeover | Unclaimed NGO records, no User creation or automatic matching; approved verified claim provenance |
| Finance indirect leakage | Separate aggregates/register/donor/export permissions; due-receipt projection minimized; no admin auto-finance |
| Public project exposing attachments/budgets | Explicit field-level projections and independently scoped file metadata/access |
| Queue confused deputy / poisoned tenant payload | Stored owner/purpose, actor/service scope intersection, execution-time reauthorization; no trust in serialized permissions |
| CSV/search/count/notification side channels | Same scoped query/projection throughout; sanitized errors, bounded queries, no sensitive previews |
| Role-definition upgrades / support abuse | Immutable role versions; explicit reviewed regrant; independent bounded support approvals and audit |

### 9.1 Files, reports and exports

Private file metadata references owner context, source object, classification and
storage key; the key/UUID is not access authority. Authorize upload initiation,
finalization, attachment linking, listing, thumbnail/preview and every download.
Validate all related ownership, malware/content handling and retention separately.
No public MEDIA_URL for private objects, user-supplied storage keys or unaudited
public redirects. Storage credentials belong to narrowly scoped services.

For strict immediate revocation on new downloads, prefer authenticated application
or gateway authorization at retrieval; freely reusable presigned URLs cannot give
that guarantee. If approved later, short-lived signed URLs require explicit residual
revocation-window acceptance and gateway/storage tests. Already delivered bytes
cannot be recalled. Range requests and streaming reauthorization need a documented
bounded policy, not an unqualified “instant revoke” promise.

Exports require a distinct permission plus step-up for sensitive datasets. Store
context/source versions, requestor and scope; reauthorize at execution, publication
and download. Grant loss cancels/withholds output and stops subsequent chunks;
partial artifacts stay inaccessible and are disposed by approved retention policy.
Export workers cannot widen filters, include unrelated NGO columns or mint reusable
public URLs. Reports, counts and derived balances need equivalent row/field scope.

### 9.2 Background jobs and service principals

No client-provided `system=true`, staff User impersonation or unbounded worker bypass.
On-behalf-of jobs carry actor/session provenance and exact tenant/action/resource/
purpose; effective authority is the **intersection** of current actor permission,
job scope and current service-principal assignment. Default proposal: revoked or
expired originating session cancels/pauses user-delegated jobs; allowing a narrowly
approved durable authorization to survive logout is a separate decision, not implicit.
Check account/hold/grant/context/expiry at pickup, each bounded batch and final
publication, with checkpointed transactional writes and idempotency.

Scheduled organization maintenance uses explicit workload assignments/purpose and
an authorized owner, not an absent-human bypass; it cannot approve commitments or
post discretionary finance merely because a queue is trusted. Multi-tenant sweeps
resolve/authorize each tenant independently and clear connection/task-local context
between work items. No ambient thread-local organization left in pooled connections.
Service-to-service callers need independently authenticated workload credentials,
rotation/revocation, action scope and audit provenance. Credential/provider selection
is operational work; this ADR creates no service keys, broker or endpoint.

### 9.3 Audit and exceptional technical access

Record grant/mandate/role/policy lifecycle, context-sensitive denials, authority
changes, finance/export/commitment transitions, support approval/use and jobs. Include
bounded reason code, actor vs executing principal, context, target/version, policy/
authorization revision, assurance intent reference, timestamp and correlation ID.
Successful sensitive mutation and evidence commit together; failures can use a
bounded separate denial record without rolling back necessary abuse counters.
No passwords, OTPs, recovery codes, proofs, token values, raw private files or full
financial payloads in events, metrics, job errors, URLs, tracing or analytics.

Existing auth SecurityEvent is scoped personal-security evidence, not a ready-made
general audit platform. Propose a linked AuthorizationEvent/domain audit contract;
correlate existing security events and future domain transactions without rewriting
auth history. Append-oriented application controls are not immutable external logs;
retention, read access, tamper evidence, alerting and failure handling need approval.
If required mutation audit cannot be recorded, fail closed for sensitive writes.

Application authorization does not cryptographically isolate tenants from a database
superuser or storage administrator. Shared-schema operation therefore also requires
least-privilege application DB credentials, separate migration/administrative access,
controlled and audited infrastructure break-glass, encrypted backups and protected
key access. A raw SQL/admin console must not become a business-support bypass.
DBA/storage compromise, external immutable audit and stronger per-tenant encryption
are explicit operational trust questions, not protections claimed by this ADR.

Technical support is disabled until approved purpose/evidence/reviewer rules exist.
Recommend independently approved short-lived resource/action-specific access,
mandatory assurance, ticket reference, notifications where appropriate and after-action
review. Ordinary platform operators and Board members remain denied. Support scope
must not by itself permit financial posting, legal commitments, grant delegation or
leadership recovery; those need their own NGO-authorized procedures. Exceptional
security suspension is not NGO business authority. No silent impersonation path.

## 10. Migration and implementation sequencing

This task changes only ADR-0002; it does not implement anything. PWC-03B.1 is design-ready
for a **separate assignment**, not started by approval of this document.

1. **PWC-03B.1 synthetic kernel:** additive §4.5 records/constraints/DB privileges,
   immutable registry, pure context resolution, centralized evaluation/scoped repository
   helpers, bounded synthetic probes, fixture-only creation/revocation lifecycle,
   durable audit and actual PostgreSQL security/race tests. No HTTP NGO adapters,
   UI, generalized engine, real authority, private files or auth proof extension.
2. **PWC-03B.2 scoped HTTP integration:** explicit context routes/discovery/capabilities
   and synthetic read adapters under §8; DRF auth/queryset/object/field enforcement;
   request errors/preconditions/CSRF/mixed transport regression and PostgreSQL A/B
   tests. Any privileged grant-management command is a separately gated sub-slice,
   not automatically approved as part of .2.
3. **PWC-03C, 03D and 02D:** generated schemas and client contracts, audit infrastructure
   evolution, file primitive only after D10; Flutter workspace/cache-clear behavior and
   independently approved web delivery choices. No premature sensitive file release.
4. **PWC-02E/P3:** real eligibility, representative verification, independent one-time
   bootstrap, disputed/last-admin recovery and team grant workflows only after D03/D05/
   D14 approvals. P4 memberships/imports and P5 volunteers/projects retain independent
   relationships and classification/consent gates. No role label promoted by migration.
5. **P6/P7/P8:** finance ADR/grants/signatories and commitments, alliance/governance and
   sharing, workload/support/files/export, then operational/production acceptance in
   their roadmap phases and separate policies. Disabled until approved and tested.

D14 safe migration: inventory legacy rows without exporting personal data; preserve
User UUIDs/password hashes, Organization UUIDs, Workspace PKs, memberships, all role
rows and historical FKs/security evidence. No grant backfill from labels/active flags,
name/contact matching or imported people. No cascade deletes or User replacement.
The new evaluator never consults legacy labels for allow. No dual-read fallback or
shadow infrastructure is needed where no legacy private permission engine exists.

A later reconciliation case references legacy row ID, proposed subject/NGO, independent
eligibility and representative evidence, reviewer identity/conflict checks, policy
version and explicit outcome. Human verification may result in a **new** grant with
its own provenance, not mutation/deletion of historical labels. Approvers/evidence for
real regrant remain blocked by D03/D14. Rejected/ambiguous rows stay nonauthoritative.
Rollback disables/drains kernel entry points and preserves grants/audit/revocations;
old software must not revive legacy authority. Used evidence schema reversal requires
reviewed forward-fix/restore, not destructive reverse migration. Test populated, empty,
expired/revoked and anomalous datasets with MigrationExecutor on PostgreSQL.

## 11. Automated acceptance-test matrix (required future work)

**All rows below are proposed tests, not executed capabilities.** Use real PostgreSQL
READ COMMITTED, independent connections/barriers for races and synthetic NGO A/B,
committee/project/alliance fixtures. Include HTTP/DRF transport, direct domain-service
calls, ORM constraint tests that bypass full_clean, and background job execution.
Parameterize list/detail/create/update/delete/bulk/search/count/file/export variants
for each implemented private resource. No SQLite replacement for acceptance.

| ID | Required allow/deny evidence | Trace / layer |
|---|---|---|
| AZ-01 | A reader can read allowed A rows; cannot enumerate/read/mutate B via UUID, nested URL, pagination/filter/order/search/count/error oracle | Identity AUTH-01; API + queryset + PG |
| AZ-02 | Same User with member manager A, finance reader B has only corresponding actions in each; selected A never uses B's grants | ID-03/04; service + HTTP |
| AZ-03 | Admin alone denied dashboard/register/donor/approve/export/access-delegate; explicit scoped finance grant allows only its atoms/accounts | Identity AUTH-03; FIN-01–09 |
| AZ-04 | Board/officer/committee User denied NGO records; independent verified NGO grant works only in its own context | Identity AUTH-02; GOV/COM |
| AZ-05 | is_staff/is_superuser/Groups/ops portal add no business privilege; absent/expired/wrong-scope support approval denies | OPS-01/HF-10 |
| AZ-06 | Provisional/pending/unclaimed applicant and unverified/expired representative denied admin/import/grant/finance; own claim evidence isolated | ORG-01–06/HF-01 |
| AZ-07 | Registered/unregistered classification alone grants nothing; workspace approval and mandate approval alone still require explicit operating assignment | Organization service + PG |
| AZ-08 | Member/volunteer/event/institutional relationships never auto-create each other or admin roles; member-only access restricted to approved fields | MEM/VOL/ID-03 |
| AZ-09 | Import produces unclaimed NGO-person rows, no User; same-contact/name rows in A/B stay separate; wrong/used/expired claim proofs cannot link | HF-03; PG integration |
| AZ-10 | Revoke/expire grant/mandate/parent delegation/context; next request denies even with warm cache, stale capability snapshot and valid MFA | Identity AUTH-05; PG + cache |
| AZ-11 | Pause mutation vs revocation with two connections: only valid serialized outcome commits; past-deadline grant/proof/session cannot commit | PG race and rollback assertions |
| AZ-12 | Concurrent contexts/tabs/late response/refresh cannot retarget requests; unexpected selection headers or mismatched path/body deny without foreign lookup | ID-04; API + future client |
| AZ-13 | Missing context, fabricated selection/capabilities/action code/role fields or any unsupported selector cannot grant anything | Contract negatives |
| AZ-14 | Pinned role upgrade does not broaden old grants; self-delegation/cycles/expired parent/resource/amount-bound escape denied | Service + constraints |
| AZ-15 | Last-authority compromise revocation works without promotion; dispute blocks unsafe transfers; recovery unavailable absent approved process | ORG-06/25/OPS-01 |
| AZ-16 | Dashboard/report/dues responses reveal no ungranted ledger/donor fields; cross-NGO receipt/account/transfer references rejected | HF-04/05; HTTP + PG |
| AZ-17 | Independent approvers/quorum/direct-entry rules obey selected policy; policy/amount/approver changes invalidate pending approval as specified | FIN-06/09; PG races |
| AZ-18 | MFA without domain grant denies; A proof fails in B/another session/action/version; revoke or hold after intent denies final command | Auth integration + PG |
| AZ-19 | Proof consumption, money/commitment/grant mutation and audit atomic; transient failure rolls back provisional consumption, semantic conflicts invalidate intent per ADR-0001; successful replay cannot execute twice | PG rollback/race |
| AZ-20 | File preview/download/range/upload-linking/metadata all enforce tenant/source scope; revoked export artifacts unavailable without public URL loophole | File service/storage integration |
| AZ-21 | Export rechecks at pickup/batches/publish/download; revoked role/session or stale context cancels/withholds output; no hidden columns/foreign counts | Worker + PG + storage |
| AZ-22 | User-delegated job cannot exceed actor ∩ job ∩ service scope; forged system flag/wrong tenant, expired workload assignment and pooled-context leakage deny | Background/service API |
| AZ-23 | PWC approval does not accept NGO commitment; correct single/multiple NGO approvers and mandate bounds required per NGO/version | COL-03/04/HF-08 |
| AZ-24 | Duplicate/changed terms/withdrawn approval/revoked signatory/concurrent accepts cannot double-bind or borrow another NGO's approval | PG integration/races |
| AZ-25 | Project participants receive only approved shared fields/files; sharing revocation stops new access; no private NGO ledger/roster joins | COL-05/HF-07/08 |
| AZ-26 | Public projection stays minimal; public visibility doesn't expose restricted subresources; notifications/logs/audit-reader endpoints avoid secrets/foreign data | PUB-04 + API/audit |
| AZ-27 | Alliance withdrawal removes only applicable alliance privileges, not independent tenant grants; deactivated workspace denies operations/jobs | HF-09; lifecycle tests |
| AZ-28 | Auth/storage/cache/authorization config failure denies; no anonymous/default-tenant/legacy-role fallback; consistent redacted error semantics | Fault injection |
| AZ-29 | Ordered additive migrations preserve UUID/hash/FKs and used evidence; no automatic legacy admin/finance grants; rollback guards prevent resurrection | MigrationExecutor + PG |
| AZ-30 | Existing 247 auth/public cases retained; new nonpersonal proof extension cannot bypass cookie/Bearer/CSRF/hold/replay/epoch/deadline protections | Whole backend regression |

G1a is not met by role-label tests, unit-only mocks or this ADR. Future client tests
must cover context cache clearing; endpoint existence, storage/worker integration
and actual PostgreSQL concurrency evidence must be reported separately and honestly.

### 11.1 PWC-03B.1 PostgreSQL acceptance gate

AZ-01–AZ-30 above remain future domain coverage, not all .1 features. For .1, finance,
files, sharing, signatory and workload positive paths must be **disabled**, never built
just to satisfy their future tests. Run the following on real PostgreSQL 16 with
TransactionTestCase/separate connections and deterministic barriers, not SQLite,
mocked locks, sleeps-only races or one shared connection. HTTP-specific assertions
are .2; .1 asserts equivalent service decisions and error categories.

| ID | Required case / observable outcome |
|---|---|
| K01 | A reader cannot list/count/read/probe B, even guessing B object/state UUID; queryset prefilter and direct lookup both return uniform absence; no foreign field leakage. |
| K02 | Same User is admin-probe in A and reader in B: settings allowed only A; union never crosses tenant; grant-scope/limit composition cannot launder bounds. |
| K03 | Membership/volunteer/legacy claimant/admin/members alone denies entry/settings; Board/staff/superuser/Groups do not change denial. Explicit admin-probe still denies every finance/signatory/grant-management action, including with valid MFA. |
| K04 | Expired, future-effective, unverified, revoked, unknown-version, unattested and legacy-only grants all deny; session revoked/epoch-invalid/expired or hold nonclear denies even with live grant. |
| K05 | Missing/malformed/conflicting/unsupported context fails closed; no selected/default fallback; foreign/absent object errors equivalent. No query target revision disclosure before authorization. |
| K06 | Revoke and then reauthorize on a new connection: immediate deny with old capabilities/MFA. Grant revision and context revision increase once, audit commits with revocation. |
| K07 | Barrier race read vs revoke: read may serialize first; if revoke commits first read denies. Expiry during state-lock wait or before final check denies without protected body; use DB wall clock. |
| K08 | Concurrent same-slot create: exactly one unrevoked row, second stale revision/conflict; revoked row cannot be un-revoked by stale ORM save/upsert/raw runtime SQL. Concurrent revoke vs create with old expected revision cannot resurrect authority; distinct new grant requires explicit new revision/event. |
| K09 | Stale/missing preconditions, repeated revoke and replacement: no duplicate transitions/events; no reused UUID, expiration extension or immutable role/provenance edit. |
| K10 | Audit insertion failure rolls back grant change; read audit failure returns no data; DB outage/lock timeout/deadlock fails closed. Complete denial audit where DB available; no phantom success on uncertain commit. |
| K11 | Synthetic flag off, missing/mismatched attestation/batch, real/unattested account or NGO, disabled state and nonverified/restricted workspace deny. Factory cannot relabel arbitrary existing real entities; ordinary deployment config and credentials cannot activate fixture writer. |
| K12 | PostgreSQL CHECK/partial uniqueness/PROTECT and runtime privileges/triggers reject malformed lifetimes, missing evidence/revocation fields, unknown bundle pair, duplicate current slots, audit deletion and direct grant/state mutation. Test with actual restricted runtime DB role, not only test-owner credentials. |
| K13 | Additive migrations preserve existing UUIDs/hashes/FKs/workspace IDs/legacy rows/auth evidence; no grants seeded from labels; destructive used-history reversal blocked; disable/rollback cannot revive authority. |
| K14 | Stable auth→context lock ordering under concurrent logout/reset/hold/factor/refresh and read/lifecycle transitions; no stale session write or reversed lock path. Bounded 50-item discovery page materializes under locks with no lazy queries; timeout behavior observable. |
| K15 | Retain existing auth/public regression suite; .2 adds cookie/Bearer/CSRF/mixed transport, path/body mismatch, HTTP error/no-store and revoked discovery/capability tests. Historical 247-test evidence is not a substitute for a fresh regression run. |

For every race assert final DB state, event revisions and both transaction outcomes,
not only status codes. Report PostgreSQL version, isolation level, connection/barrier
strategy and commands/results in implementation evidence. Audit performance/load and
production privilege provisioning remain explicit review gates.

## 12. Decision register, documented gates and handoff

The table below retains its **24 October 2026** disposition/provenance. For the owner product-policy portion accepted on **27 October 2026**, see the scoped addendum above and the thirty-decision matrix; no technical/independent approval is inferred and the core ADR status is unchanged.

Status vocabulary: **Approved for initial kernel** means the bounded synthetic .1
contract is resolved; **Approved in principle / narrower contract required** approves
only the stated principle; **Deferred** means no implementation in this kernel;
**Blocked** requires separate product/security/operational approval. Partial approvals
do not close broader OPEN-DECISIONS entries or authorize real users/data.

| ID | Status on 24 October 2026 | Resolved scope / remaining gate |
|---|---|---|
| D01 | Approved for initial kernel | Shared schema; personal and NGO only; path UUID, typed FK and server resolution (§3); all other kinds disabled. RLS deferred, not claimed. |
| D02 | Approved for initial kernel | Closed three-action `ngo_kernel_v1`, two v1 synthetic bundles, same-tenant union, organization scope, terminal revocation, mandatory expiry, no delegation or wildcard (§4.5). Real administration/member entitlements/custom roles remain blocked. |
| D03 | Approved in principle / narrower contract required | Mandatory source/issuer/verification/evidence/validity/revocation schema and synthetic provenance resolved (§4.5). Real eligibility/representative verification, expiry/revalidation, disputes, bootstrap/last-admin recovery blocked pending PWC-02E and NGO/security approval. |
| D04 | Blocked pending separate product/security approval | Finance root authority, independent delegation, account/currency/limits, maker-checker, threshold aggregation and self-approval. Admin/Board never inherit finance. P6 finance ADR required. |
| D05 | Approved in principle / narrower contract required | .1 active auth/current grant/clear hold; no extra MFA for fixed synthetic reads; existing personal policies unchanged (§5.4). Every privileged command/role-retention and nonpersonal proof extension blocked until complete matrix/canonicalization/locking/failure contract reviewed. |
| D06 | Blocked pending separate product/legal/security approval | Signatory evidence, distinct-human approvals, exact-version NGO commitments, withdrawal/amendment and legal consequences. No PWC binding of NGO. |
| D07 | Deferred until P7; activation blocked on governance approval | Institutional terms, Board/officer/committee/voting scope are not NGO access and not approved bylaws. |
| D08 | Blocked pending separate security/operational approval | Support access, independent approval, emergency suspension boundaries, notice/review and assisted recovery. No staff/superuser exception. |
| D09 | Approved in principle / narrower contract required | Only `NGO_PRIVATE_SYNTHETIC_V1` and its fixed allowlist approved (§4.5). Real private categories, beneficiary/donor data, consent, publication, retention, audit readers and sharing blocked. Existing public projection unchanged. |
| D10 | Deferred; release blocked on security/operational approval | Private storage/download revocation windows, signed URLs, exports/disposal and limits. No .1 file access. |
| D11 | Approved for initial kernel | Stateless path context, discovery/entry/capability/error/precondition contracts (§8); .1 internal service only, .2 synthetic HTTP adapters. Frontend technology and generated schemas retain 02D/03C gates. |
| D12 | Deferred; activation blocked on security/operational approval | Durable jobs, workload identities, post-logout authority and credential rotation. No .1 service-principal allow path. |
| D13 | Approved in principle / narrower contract required | Concrete .1 primary-DB locks, revisions, expiry, fail-closed audit and race gates (§5.3) resolved. Production retention, monitoring, incident response and throughput/lock-budget review remain operational blockers, not silently approved policy. |
| D14 | Approved in principle / narrower contract required | Preserve legacy rows, no label promotion or allow fallback; synthetic additive migration contract resolved (§10). Real inventory/regrant approvers, evidence and rollback operational sign-off blocked pending D03/D14 review. |

### Remaining blockers and readiness

No unresolved institutional decision blocks the **synthetic-only .1 contract as scoped**.
Implementation must still be separately assigned and satisfy PostgreSQL acceptance,
helper lock-order review, DB privilege/trigger enforcement, synthetic release guards
and regression tests. Failure to implement any such safeguard blocks that slice;
it is not permission to choose weaker defaults. No real NGO activation, private real
data, privileged grant-management route, finance, signatory, governance, support,
sharing, file/export or durable-workload authority is approved.

Auth default-off, synthetic delivery/privacy/deployment gates remain unchanged. This
ADR does not claim production readiness, legal approval, a completed G1a/G1 milestone,
or executed database acceptance. Retention and operational procedures must be approved
before persistent real-user events or data; no policy numbers are invented here.

**Consequences:** the small read-only synthetic kernel proves tenant isolation,
provenance and revocation without a large policy engine or real NGO claims. Coarse
locks serialize reads and grant changes per tenant; bounded projections/pages and
real PostgreSQL contention tests are required before optimizing. Later capabilities
require explicit new actions/role versions and approved policy rather than inheritance.

**Handoff:** ready for a separately assigned PWC-03B.1 synthetic authorization kernel.
Commit/push ADR-0002 only; no PR/merge and no implementation in this assignment.

### Documentation validation note

Validate status/date, all fourteen decision IDs, source links, retained JSON examples,
required contract/test IDs, whitespace and single-file scope. Preserve approved auth
ADR SHA256 and prior ADR commit ancestry. Backend/PostgreSQL acceptance cases in §11
are future requirements, not executed results of this documentation task.
