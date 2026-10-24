# ADR-0002 — Multi-NGO authorization and tenant isolation

**Status: PROPOSED — NOT APPROVED**

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
  unresolved. §12 below is this proposal's review register; it does not close or
  silently revise the existing register.

All recommendations below, including payloads, role bundles and thresholds, are
**proposals**, not approved policy. Source [S] means selected provisionally, [R]
recommended, [O] open, [D] deferred. This ADR does not approve bylaws, legal standing,
financial authority, onboarding evidence or technical support governance.

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

### 3.2 Closed contexts, ownership and boundaries

| Context | Identity / ownership | Permission boundary |
|---|---|---|
| Personal | Authenticated User UUID | Own preferences, affiliations and participation; no NGO operating authority |
| NGO | Organization UUID; existing workspace attached | That NGO's tenant-owned records, bounded by resource/action/relationship |
| Alliance | Explicit singleton institutional context, not a master NGO | Institutional membership, approved PWC Board/officer business only |
| Committee | Committee UUID with alliance relationship | Assigned committee records; not member NGOs' rosters/accounts |
| Project | Project UUID, explicit owning kind/party | Authorized project collaboration records and approved shared projections |
| Platform operations | Dedicated operations context | Technical registry/security actions; no routine NGO business access |

NGO finance is an explicitly separate permission namespace **within the same NGO
ownership boundary**, not a second identity store or implied child-role inheritance.
PWC's own finances need a separate owner/policy; neither alliance finance nor a
joint project creates access to participating NGO ledgers.

Recommend an `AuthorizationContext` registry with real typed target FKs and an
exactly-one target constraint, rather than unvalidated `kind + arbitrary UUID` or
GenericForeignKey authority. Stable registry rows can reference future committee/
project models through later additive migrations. Initially allow only implemented
kinds; unused future kinds remain disabled, not fake rows. Personal context need
not create one grant per User; ownership is a dedicated personal rule.

Tenant-owned tables require `organization_id NOT NULL`, unless explicitly a global
registry or separately owned collaboration record. Project-owned records require
project ownership, not an ambiguous nullable NGO ID. A project reference does not
change the owner of an NGO's own task, budget or file. Cross-owner references need
an explicit shared projection/participation record, never a permission bypass join.

### 3.3 Context selection and switching

Recommend explicit per-request context, resolved from a bound selection and a
canonical resource URL. A server-held **ContextSelection** may remember a display
choice, bound to current logical AuthSession and context, with bounded expiry.
Its UUID is a selector, **not** an authentication or grant token. Several selections
may coexist per logical session for separate browser tabs; no mutable global
User.current_organization that silently retargets in-flight requests.

For private context APIs, require selection header and an explicit context-scoped
path. Resolve selection ownership by User/session, then compare its context with
path/body/parent ownership before domain access. Any conflicting context input
denies, without looking up an alternative tenant. Body organization IDs are either
forbidden or checked for exact equality; never trusted to set ownership. Switching
context does not change roles, renew login/idle time, rotate credentials into new
privileges, or validate an old proof for a different context.

Selection remains usable only while account/session/context and current entry
permission are valid. Web step-up cookie rotation and mobile refresh preserve the
logical session, so selections can remain bound; reset/logout/revocation/expiry
invalidates access through existing live session checks. Cap selection lifetimes
and row growth; GET/list/selection is not a keepalive loophole.

Clients must cancel/tag old-context requests, partition caches by user/context/
authorization version, discard late responses for a former context, clear private
screens/files/notifications on revocation/switch/logout, and refetch permissions.
Backend correctness does not depend on these client behaviors.

## 4. Proposed data model, roles and organizational authority

**Logical contracts only; names/fields are not migrations or final schemas.**
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
2. Resolve context selection and principal binding. Missing/conflicting/unknown kind,
   inactive target, ambiguous ownership or incompatible route denies. No default tenant.
3. Apply account recovery restrictions and context lifecycle/dispute/suspension gates.
   Proposal: held/recovery-code sessions may use approved restricted personal flows,
   not private operating/finance/support/commitment contexts. Exact business hold
   matrix needs approval; never weaken ADR-0001 or let fresh MFA override a hold.
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
7. Require approved action-specific assurance where mapped (§6). Proof is necessary,
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

Proposed interfaces: `resolve_context(principal, selection, route)`;
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

### 5.3 Revocation, concurrency and caching

Context revisions advance transactionally for role activation/revocation, delegation,
mandate, policy, lifecycle and sharing changes. Auth User epochs remain personal
credential revocation; do not overload them to log users out of every NGO for one
NGO role change. Principal suspension still uses the existing auth lifecycle.

Preserve the auth lock prefix: **User → contact/factor → AuthSession(s)** before
context/domain authority locks; workload calls lock their ServicePrincipal after
any originating human auth prefix and before context roots. Lock challenge/intent/proof rows afterward in a
fixed implementation-reviewed order compatible with accounts services. Proposed
business lock order: NGO context roots in UUID order, then alliance, committee,
project, platform roots in fixed kind/UUID order, then grant/policy/domain rows
and proof rows under the agreed command order. Never acquire a User/session lock
or an earlier context root after taking a later root. Grant changes lock the actor's
auth prefix and affected context root; do not lock a target User late. Multi-context
commands acquire their complete sorted roots up front or split into independent
commands; no project-first path may later acquire NGO roots. Validate this detailed
order with the existing auth call graph and PostgreSQL races before implementation;
this ADR is not permission to change accounts lock order silently.

A minimal implementation may serialize private mutations per context root to make
revocation linearizable; optimize with proven finer locks only after measurement.
Revocation and a sensitive mutation share that root. If the mutation commits first,
revocation follows; if revocation commits first, mutation denies. An earlier read
may finish; do not promise to recall bytes already returned. Recheck between streamed
chunks/job batches and at downloads; no future access on stale authority.

Initial recommendation: no positive permission-decision cache for sensitive actions.
Read authorization metadata from the primary database in a coherent transaction;
no lagging replica/cache-only grant acceptance. Cache immutable role definitions,
and optionally projections keyed by principal/context/revision/policy/resource
version only after current revision/liveness is checked against authoritative state.
Expiry must still be checked against now; revision alone cannot detect clock expiry.
Cache outages never fall back to allow. Invalidation events improve UX, not correctness.

READ COMMITTED plus transaction.atomic alone is not a coherent multi-query policy
snapshot. Initial private-read implementation should hold the relevant authority
root locks through current grant/mandate checks and the bounded scoped data query,
then release before response/network I/O. Reacquire/recheck for subsequent streaming
chunks. A future shared-lock/single-snapshot optimization must prove equivalent
revocation semantics with PostgreSQL tests; a revision read followed by an
unsynchronized cache allow is not sufficient.

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
permission wins over valid MFA. Failed mutation rolls back proof consumption; owned
successful replay is a conflict, not a second posting. Read-only permission checks
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

## 8. Proposed API and frontend contracts

**Illustrative contract proposals only: these routes do not exist.** Use `/api/v1/`
and retain existing `/auth/` routes/envelopes/transports. Approve/generate schemas
in PWC-03C; no Flutter/web implementation or framework choice is made here.
Placeholders such as `<organization-uuid>` are not usable identifiers or credentials.

### 8.1 Listing, selecting and refreshing

| Method / suggested path | Contract |
|---|---|
| GET `access/contexts/` | Current authenticated principal's authorized entry contexts only; paginated, minimal labels/kinds, current capabilities/version; not a global NGO/member search |
| POST `access/context-selections/` | Explicit desired context; authorize entry now, bind to logical session; no grant changes or session-idle renewal |
| GET `access/context-selections/{id}/permissions/` | Recompute caller's current effective capabilities, field/resource limits, policy/revision and assurance requirements; no other users' grants/evidence |
| DELETE `access/context-selections/{id}/` | Remove caller's own display selection; not role revocation or logout |
| Private `ngos/{organization_id}/...` | Context-scoped routes plus selection header and action permission; explicit ownership; no unscoped private detail endpoint |

Illustrative selection request:

```json
{"context":{"kind":"ngo","id":"<organization-uuid>"}}
```

Illustrative 201 response:

```json
{
  "selection_id":"<server-generated-selection-uuid>",
  "context":{"kind":"ngo","id":"<organization-uuid>","label":"Synthetic NGO A"},
  "authorization_version":42,
  "policy_version":3,
  "capabilities":["ngo.members.read"],
  "constraints":{"finance_access":false},
  "assurance_requirements":{},
  "expires_at":"<server RFC3339 UTC deadline>"
}
```

Suggested private request headers: `X-PWC-Context-Selection: <selection-uuid>` and,
for mutations, `X-PWC-Authorization-Version: 42`, plus expected resource version.
These values are client preconditions, not trusted permissions. Unknown/stale/
malformed values never select another tenant or mint grants. Returned capabilities
are advisory; server recomputes on every request. A selected NGO does not imply
all actions or full field visibility. Pagination/search cannot reveal inaccessible
contexts, users or mandate evidence. ID-03 affiliations list is a different personal
relationship contract; mere membership does not add an administrative workspace.

If still authorized but versions changed, permission refresh returns current
revision/capabilities; GET need not mutate selection. Clear affected client caches
before reissuing commands with new preconditions. If entry was revoked, deny rather
than return an empty-permission response containing private context metadata.
No capability token is embedded in native refresh/access credentials. A selection
bound to one logical session cannot be replayed from another session or user.

Browser unsafe requests retain exact portal/CSRF requirements and secure cookies;
native X routes require exactly one Bearer mode, never cookie fallback. Selection
responses are no-store/no-referrer and do not renew personal idle time. Context
switches do not silently move between NGO and PWC portal hosts. Role changes may
prompt UI refresh via future notifications, but API checks do not wait for them.

### 8.2 Error and disclosure semantics

Use the auth-compatible envelope:

```json
{"error":{"code":"NOT_AUTHORIZED","message":"This action is not available.","field_errors":{},"request_id":"<server-correlation-uuid>"}}
```

Proposed domain errors (do not rename existing auth codes):

| Status/code | Semantics / disclosure boundary |
|---|---|
| 400 CONTEXT_REQUIRED / CONTEXT_MISMATCH / VALIDATION_ERROR | Missing selection, mutually conflicting context identifiers or schema failure; do not look up a second tenant to diagnose mismatch |
| 401 SESSION_INVALID | Missing/invalid/revoked/expired auth, existing auth semantics; never fallback to another transport/context |
| 403 NOT_AUTHORIZED | Known accessible context, insufficient action/field/authority; no foreign-object details |
| 403 CONTEXT_UNAVAILABLE | Owned session-bound selection is no longer eligible; generic, no private reason or new metadata |
| 403 STEP_UP_REQUIRED / MFA_REQUIRED / RECOVERY_RESTRICTED | Existing assurance/hold meanings; only after independent scope/action checks; never imply a foreign object's existence |
| 404 NOT_FOUND | Unknown or inaccessible context requested for selection, foreign selection, or object absent from authorized queryset; same envelope for absent/foreign |
| 409 STATE_CONFLICT | Authorized caller's stale policy/authorization/resource version or owned consumed proof; refetch/re-authorize, do not retry changed commands blindly |
| 429 RATE_LIMITED | Bounded abuse/expensive-query limits with Retry-After; never change authority |
| 503 AUTH_UNAVAILABLE / AUTHORIZATION_UNAVAILABLE | Existing auth infrastructure vs proposed domain-policy storage/configuration outage; fail closed, not anonymous/default-tenant fallback |

Authorization denial precedes stale-version/assurance detail disclosure. If a grant
is revoked, return a generic denial rather than an informative object's version
conflict. Filter inputs/ordering/counts/validation/FK errors must not become existence
oracles. Private 405s use correct Allow; private responses/errors are no-store and
no-referrer. Framework/proxy-wide exception-envelope standardization is separate
contract work; no secret stack traces or private record bodies in diagnostics.

## 9. Security, audit and non-HTTP threat analysis

| Threat | Required control |
|---|---|
| IDOR/BOLA, cross-tenant parent/child references | Scope before lookup; composite ownership constraints plus service validation; 404 absent/foreign |
| Role mass assignment / privilege inflation | Server action registry, pinned bundles, scoped grant-authorizer evidence; reject unknown grant fields/wildcards |
| Context confusion, two tabs, delayed mobile response | Session-bound explicit selections + canonical path, immutable captured request context; cache partitioning and response tags |
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

This task changes only this document. It does not modify the approved auth ADR,
OPEN-DECISIONS, models, tests, settings, migrations or client files.

1. **Review first:** approve this ADR's technical boundaries and explicitly decide
   blocking §12 policies. Approval may be scoped; unapproved domains remain disabled.
2. **PWC-03B kernel contract:** freeze closed action/context registry, grant provenance,
   denial semantics, lock order, lifecycle/revocation rules and acceptance fixtures.
   Synthetic fixtures may demonstrate policy; they cannot authorize real NGO authority.
3. **Additive schema:** introduce reviewed access/context/versioned-grant records and
   constraints after existing migrations. Inventory legacy OrganizationAccess rows
   without exporting personal data. Do not map `admin` or `members` to production
   privileges automatically; preserve rows and require documented verified regrant.
   No auth model replacement, mass session changes or global privilege backfill.
4. **Shadow comparison, never shadow allow:** safely compare proposed decisions on
   synthetic data; unknown legacy mappings deny. Avoid a permissive legacy fallback
   during dual-read/cutover. Audit reviewed mapping IDs/provenance and rollback plan.
5. **Enforcement slice:** implement services, explicit DRF permissions, scoped queries,
   context contracts and negative PostgreSQL tests behind default-off enablement.
   Preserve all existing 247 auth/public tests; added tenant tests must be independent
   and must not substitute for original auth regressions.
6. **Assurance integration:** separately review extension of personal-only auth
   interfaces/schema, command canonicalization, revision/hold binding and atomic
   consumption with domain changes. No sensitive domain route enabled before this.
7. **PWC-03C/03D and 02D:** approve/generated shared API schema/fixtures, private-file
   primitive and client cache/context/storage behavior before Flutter/web delivery.
   PWC-02E verification/bootstrap policy gates real admin activation in P3; finance
   (P6), alliance/commitments (P7) retain independent product/policy gates.
8. **Operational acceptance:** provenance inventory, access reviews, monitoring,
   restore/revocation drills, retention and workload identity/security tests before
   real-user activation. Auth default-off/synthetic limitations remain in force.

Migration tests must preserve User/Organization UUIDs, Workspace PKs, all relationship
FKs/password hashes, historical access labels and auth evidence. Test existing,
empty, anomalous and used-security datasets; explicit constraints/index plans and
no-drift checks. Used authorization/evidence schemas must refuse destructive reversal
or supply reviewed forward-fix/restore procedures, never erase revocations or revive
legacy grants. Rollback disables/drains affected endpoints/jobs and preserves evidence;
backward app compatibility must not re-enable old role-label authority. Role-policy
version migrations must not silently expand live grants. No production backfill or
reversible-data-loss claim is approved here.

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
| AZ-12 | Concurrent contexts/tabs/late response/refresh cannot retarget requests; mismatched selection/path/body denies without foreign lookup | ID-04; API + future client |
| AZ-13 | Missing context, fabricated selection/capabilities/action code/role fields or different-session selector cannot grant anything | Contract negatives |
| AZ-14 | Pinned role upgrade does not broaden old grants; self-delegation/cycles/expired parent/resource/amount-bound escape denied | Service + constraints |
| AZ-15 | Last-authority compromise revocation works without promotion; dispute blocks unsafe transfers; recovery unavailable absent approved process | ORG-06/25/OPS-01 |
| AZ-16 | Dashboard/report/dues responses reveal no ungranted ledger/donor fields; cross-NGO receipt/account/transfer references rejected | HF-04/05; HTTP + PG |
| AZ-17 | Independent approvers/quorum/direct-entry rules obey selected policy; policy/amount/approver changes invalidate pending approval as specified | FIN-06/09; PG races |
| AZ-18 | MFA without domain grant denies; A proof fails in B/another session/action/version; revoke or hold after intent denies final command | Auth integration + PG |
| AZ-19 | Proof consumption, money/commitment/grant mutation and audit atomic; failed validation/audit/deadline rolls back; successful replay cannot execute twice | PG rollback/race |
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

## 12. Open decisions and approval gates

The following are review questions, not a list of already approved answers. They
refine the existing OPEN-DECISIONS register without changing its status. Safe default
where unresolved is deny/disabled, not technical staff discretion.

| ID | Owner decision required | Blocks / conservative proposal |
|---|---|---|
| D01 | Accept shared-schema contextual RBAC/predicate architecture, typed contexts and centralized enforcement; decide future RLS criteria | PWC-03B schema/service contract; no RLS claim |
| D02 | Approve initial per-domain role bundles, permission atoms, member-only entitlements and grantable subsets/custom-role limits | Production grant seeding; no wildcard/admin inheritance |
| D03 | Registered/unregistered verification evidence, who validates which mandate, expiry/revalidation, disputes and multiple/last-admin recovery | Real admin bootstrap/transfer; no contact-based authority or auto-migration |
| D04 | NGO-selected finance root authority/bootstrap/recovery, delegation, single vs multiple authorizers, amount/account/currency limits and self-approval constraints | Finance access/activation; ordinary admin/Board excluded |
| D05 | Approve sensitive action → assurance matrix, role-based MFA retention, hold effects on all private reads/writes, and auth interface extension | Nonpersonal proof integration/sensitive commands; deny missing policy |
| D06 | Signatory evidence, single/multiple NGO commitment approval, conflict rules, authority withdrawal, amendments and legal consequences | Binding commitments; PWC cannot bind NGO |
| D07 | Board/officer terms, institutional representatives/voting eligibility and committee/project entitlements within provisional governance | Alliance business activation; no elections/bylaw assumptions |
| D08 | Exceptional support independent approval, emergency suspension vs access, tenant notice, allowed fields/actions and recovery evidence | Support access remains disabled; no technical superuser business exception |
| D09 | Data classification/publication/consent, project sharing audience/purpose, donor privacy, retention/legal holds and audit-reader rules | Private sharing/exports/real data; minimal public projection retained |
| D10 | Private storage/download enforcement and acceptable signed-URL/stream revocation window, export disposal and limits | File/export release; authenticated retrieval preferred |
| D11 | Approve selection/header/version/error API contract and per-tab semantics; frontend schema/runtime/portal decisions | PWC-03C/03D clients; no generated API promise yet |
| D12 | Job lifetime after logout, durable authorizations, workload identity credential/rotation policy and allowed scheduled purposes | Background authority; default user jobs require live originating session |
| D13 | Approve revision/locking granularity, denial/audit failure policy, retention/monitoring, performance/load requirements and incident procedures | Production enforcement; linearizable sensitive checks over primary DB |
| D14 | Legacy OrganizationAccess inventory/regrant approvers and cutover/rollback evidence | Any real legacy mapping; no inferred validated grants |

Acceptance of this ADR's technical architecture does not approve every role bundle,
legal mandate, finance control or governance article. Record explicit scope/owner/date
for each decision before the corresponding implementation slice; keep remaining
capabilities disabled. Real-data/production authorization additionally retains all
ADR-0001 delivery/security/privacy/operations gates.

**Consequences:** explicit grant provenance and centralized scoped services add
implementation/audit work and may initially serialize writes per context. In return,
they make multi-NGO authority reviewable and revocation testable without a new policy
engine or changing personal identity. Versioned roles and negative tests reduce
silent expansion; remaining legal/organizational decisions are visible, not guessed.

**Handoff:** ready for product-owner/security/NGO architecture review as a proposal.
Commit/push this document only. Do not open/merge a PR for this assignment, do not
mark this ADR approved, and do not begin PWC-03B or NGO onboarding implementation.


### Design-task validation note

Validation for this assignment is document structure/status, relative source links,
JSON example syntax, whitespace and a single-file diff against the verified base.
Application code, migrations, tests and the approved authentication ADR remain
unchanged. No backend/PostgreSQL test execution, production enforcement, generated
API contract or approval is claimed for this documentation-only assignment.
