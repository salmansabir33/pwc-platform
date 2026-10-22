# Pakistan Welfare Club (PWC)
## Flutter Frontend Architecture v1.0 — Draft for Review

**Date:** 22 October 2026  
**Status:** WORKING DRAFT — NOT FORMALLY APPROVED  
**Initial rollout:** Faisalabad, Pakistan  
**Scope:** Flutter mobile application and shared frontend contracts with the NGO Management Web Portal and PWC Operations Web Console.  
**Source baseline:** PWC Strategic & Product Foundation v1.0; App Information Architecture & Navigation v1.0; Detailed Mobile & Web Screen Specification v1.0; Identity, Authorization & Multi-NGO Data Model Foundation v1.0; Django Backend & PostgreSQL Schema Foundation v1.0. Coventure frontend architecture is a precedent for engineering patterns, **not** a PWC product authority.

### Requirement labels
- **[S] User-selected, provisional** — selected in planning but not formally approved.
- **[R] Recommended** — proposed architecture requiring technical review.
- **[O] Open** — unapproved decision or unresolved backend contract.
- **[D] Deferred** — outside the initial MVP.

The mobile screen identifiers and navigation hierarchy in the PWC Screen Specification and Information Architecture are the source of truth for screen naming. This document describes **how to implement them**, not an alternate navigation taxonomy.

---

## 1. Executive architectural direction

**[S]** PWC directly owns and operates the platform. The ecosystem supports eligible non-member NGOs using independent software workspaces; PWC institutional membership unlocks additional alliance participation. An authenticated person can manage different NGO and PWC relationships using a **single personal account**. Public discovery, NGO operations and alliance collaboration coexist but never grant each other automatic authority.

**[R]** Use a **feature-first Flutter application** for Android and iOS, with a small, strictly reusable design system and infrastructure layer. Recommended frontend stack: Flutter stable (pin a tested SDK version during implementation), Dart, Riverpod for dependency injection/state, go_router for navigation and redirects, Dio or an equivalently tested HTTP client, Freezed/json_serializable or maintained comparable code generation, secure OS storage for secrets, and a purpose-built local cache. Package selections are recommendations, not approved technical decisions. Verify current library versions and platform requirements when implementation starts; this design intentionally pins no unverified version numbers.

**[R]** Use the same OpenAPI-defined backend contract for Flutter and the administrative web clients. The NGO web portal and the PWC operations portal may use a separate web framework, or Flutter Web if validated later; this draft does **not** assume Flutter Web has been approved. Detailed bulk operations are primarily web-based in the existing IA.

### 1.1 Non-negotiable frontend invariants
1. The active **personal / NGO / PWC / committee / project** context is always explicit when privileged actions are offered.
2. Privileged UI is based on server-issued **context-specific capabilities**, never broad labels such as `isAdmin` or a PWC Board title.
3. Hiding a button never substitutes for server-side authorization. The backend enforces every read/write, file, search, count and export.
4. Independent NGO private membership, volunteer and finance data is not exposed to PWC alliance roles by default.
5. A primary NGO administrator does **not** automatically receive finance privileges; separate finance authorization and recovery rules apply.
6. NGO and PWC institutional memberships are different relationships; standing volunteering and one-off activity participation are also different.
7. Provisional NGO workspaces cannot display as verified, publish misleading credentials, import broad sensitive records or administer an existing NGO until appropriate verification.
8. Public, Members Only and Private are content visibility states, **not** blanket authorization for private fields, finances or attendee lists.
9. Independent NGO projects, PWC-owned projects and jointly accepted projects display their actual ownership and obligations.
10. Financial UI represents **recorded** balances, approval states and unverified payment claims accurately. Never optimistically display a pending posting as settled.
11. Switching or losing an organization context invalidates the previous context's privileged cached data and pending screens.
12. PWC alliance departure does not silently delete an NGO's independently operated workspace.

---

## 2. Clients and responsibilities

| Surface | MVP function | Architectural approach |
|---|---|---|
| **PWC Flutter mobile app** | Public discovery, personal account, volunteering, applications, NGO routine actions, activity check-in, committee updates, notifications | One adaptive Flutter app with route-aware contextual workspaces |
| **Independent NGO web portal** | Bulk imports, complex member lists, membership policy setup, finance and approval work, advanced project tasks, exports | Web client sharing OpenAPI types and authorization semantics; technology [O] |
| **PWC operations web console** | Organization verification/claims, PWC membership, governance, operational review and restricted support | Separate privilege boundary and UX shell; no generic NGO database browser |
| **Public web pages** | Published NGO, event and initiative discovery | [R] Read-only web views/SEO approach, delivery method [O] |

**[R]** Do not build three separate login systems. Cross-client sessions are independent but map to the same `User`; the server is the authority for relationships and scopes.

---

## 3. Proposed Flutter repository layout

```text
apps/
  pwc_mobile/
    android/ ios/ web/                 # web only if approved as delivery surface
    lib/
      main.dart
      bootstrap.dart
      app/
        app.dart
        router/
          app_router.dart
          route_names.dart
          guards.dart
          redirect_intents.dart
        shell/
          public_shell.dart
          workspace_shell.dart
        theme/
          tokens.dart
          light_theme.dart
          dark_theme.dart
        localization/
      core/
        auth/
          session_controller.dart
          token_store.dart
          session_api.dart
        context/
          active_context.dart
          context_controller.dart
          capability_provider.dart
        network/
          api_client.dart
          auth_interceptor.dart
          error_mapper.dart
          request_ids.dart
        storage/
          secure_storage.dart
          cache_scopes.dart
        ui/
          widgets/
          forms/
          accessibility/
        errors/
        logging/
      features/
        public_discovery/
        identity_profile/
        organizations_onboarding/
        ngo_members/
        ngo_dues/
        ngo_volunteers/
        ngo_activities/
        ngo_projects/
        ngo_finance/
        ngo_admin_roles/
        alliance_membership/
        committees/
        collaborations/
        joint_projects/
        inquiries/
        notifications/
        reports_exports/
      shared/
        models/
        generated_api/
        formatting/
        widgets/
    test/
      unit/
      widget/
      integration/
    integration_test/
  ngo_web/                            # technology selection [O]
  pwc_ops_web/                        # technology selection [O]
packages/
  pwc_design_tokens/                  # optional Flutter-shared design package
  pwc_api_contract/                   # generated Dart client + common DTOs
  pwc_lints/                          # optional shared strict analysis rules
```

Each `features/<feature>/` should have a consistent internal layout:

```text
feature/
  data/
    dto/
    remote/
    local/                             # only when genuinely needed
    repositories/
  domain/
    entities/
    services/
    contracts/
  presentation/
    screens/
    widgets/
    controllers/
    state/
```

**[R]** Keep cross-feature imports behind explicit contracts. Do not let a finance screen import an NGO member widget to compute dues independently; both should consume backend-defined posted/assessed amounts.

---

## 4. Application lifecycle, authentication and account identity

### 4.1 User states
`guest → authenticating → authenticated → profile_setup_optional → active`; separate exception states include `session_expired`, `account_restricted`, `contact_verification_required` and `network_unavailable`. Exact server status names remain [O].

**[R]** A guest can browse public profiles. Write actions route to sign-in while saving a sanitized, expiring **return intent**; after successful login, recompute access and resume only if the target still exists and the request is permitted. Never automatically submit a previously staged irreversible action.

### 4.2 Token and session handling
- Access tokens should be short lived; refresh tokens/session credentials, where used, reside only in platform secure storage (Keychain/Android Keystore-backed).
- Avoid storing tokens in ordinary preferences, logs, analytics, route parameters or crash reports.
- Rotate refresh credentials according to backend contract; prevent simultaneous refresh races with a single-flight mechanism.
- Logout and account deactivation clear credentials, private caches and in-memory sensitive providers.
- Do not assume biometrics or passkeys are in MVP; optional unlock must not replace backend session validation.
- Web sessions require an appropriate separate browser-side threat model; do not blindly copy mobile token persistence to web.

### 4.3 Example session and identity abstractions [R]

```dart
sealed class AuthState { const AuthState(); }
class Guest extends AuthState { const Guest(); }
class Authenticated extends AuthState {
  final String userId;
  const Authenticated(this.userId);
}
class SessionExpired extends AuthState { const SessionExpired(); }

abstract interface class SessionRepository {
  Future<AuthState> restore();
  Future<void> logout();
  Future<void> refresh();
}
```

No organization role is an attribute of the user account by itself. Roles are grants within a **specific context**.

---

## 5. Active workspace and organization switching

### 5.1 Proposed context model [R]

```dart
enum WorkspaceKind { personal, ngo, pwcAlliance, committee, project }

class ActiveContext {
  final WorkspaceKind kind;
  final String? organizationId;
  final String? committeeId;
  final String? projectId;
  final String? membershipId;
  final int serverRevision;
  const ActiveContext({
    required this.kind,
    this.organizationId,
    this.committeeId,
    this.projectId,
    this.membershipId,
    required this.serverRevision,
  });
}
```

Context IDs are **identifiers, not evidence of authorization**. The API validates current grants on each request. A context can be selected only from a fresh, server-filtered list of memberships/assignments. Never rely solely on persisted `lastSelectedOrgId`.

### 5.2 Context switch transaction
1. User selects a workspace via `Profile → Workspaces` or a clearly visible switcher.
2. If there are unsaved edits, prompt to save/discard; do not silently submit.
3. Clear context-sensitive navigation history, transient forms, controller state and in-memory finance data.
4. Re-fetch `/me/contexts` or equivalent and server-authorized capabilities.
5. Open the context's permitted landing route; display selected NGO/PWC name prominently.
6. Re-key data providers and cache entries using `(userId, contextKind, contextId, resourceType, filters)`.
7. If context is revoked or inaccessible, display an access-removed state and return to personal workspace.

**Cross-tenant protection:** Switching from NGO A to NGO B must never display cached NGO A financial amounts, member names, volunteer contacts or exports, even momentarily. Privacy-critical providers should reset **before** painting the newly selected context.

### 5.3 Context and capability response [R; exact API to be agreed]

```json
{
  "context": {"kind":"ngo", "id":"<ngo-uuid>", "display_name":"Example Welfare Society"},
  "revision": 42,
  "capabilities": [
    "ngo.members.read", "ngo.members.manage",
    "ngo.projects.read", "ngo.projects.manage"
  ]
}
```

Capability strings are illustrative and do not replace the backend permission registry. Finance capabilities must not be inferred from `ngo.members.manage` or a leadership title.

---

## 6. Navigation architecture and route catalog

### 6.1 Public mobile shell — preserve existing IA [R]

**Home | Discover | Participate | Updates | Profile**

- **Home:** public features and personalized pending actions after login.
- **Discover:** NGOs, initiatives, events, volunteer opportunities and published committees.
- **Participate:** registrations, applications, collaboration/assistance inquiries and relevant actions.
- **Updates:** notifications, invitations, decisions and reminders.
- **Profile:** identity, memberships, volunteer history, settings and **Workspaces** entry.

Do not substitute a universal NGO dashboard as the initial landing page for every person; NGO admin is a contextual experience.

### 6.2 Contextual route shells [R]

```text
/                              -> Public Home
/discover                      -> Discover
/discover/organizations/:id    -> Public NGO profile
/discover/projects/:id         -> Published project
/discover/events/:id           -> Published event
/participate                   -> Applications/participation
/updates                       -> Notification inbox
/profile                       -> Personal profile
/profile/workspaces            -> Context chooser

/workspaces/ngo/:orgId/overview
/workspaces/ngo/:orgId/members
/workspaces/ngo/:orgId/volunteers
/workspaces/ngo/:orgId/activities
/workspaces/ngo/:orgId/projects
/workspaces/ngo/:orgId/finance       -> only if specifically authorized
/workspaces/ngo/:orgId/settings

/workspaces/pwc/committees/:committeeId
/workspaces/pwc/projects/:projectId
/workspaces/pwc/governance
```

Routes are recommendations, not approved API paths. Route parameters must be validated; guessing a UUID must never produce a private resource response. Preserve the screen IDs defined in the separate screen specification in route metadata and analytics identifiers.

### 6.3 Deep links and guarded navigation
- Parse intent → authenticate if needed → fetch resource → select/revalidate context → verify capability → navigate.
- If permission is missing, show `Access unavailable` without leaking whether a private resource exists.
- If content is gone, show `No longer available`; if a workspace is deactivated, show an explicit access/lifecycle message.
- Notification deep links may contain resource IDs and opaque navigation targets, **not** personal contact lists or financial values.
- All write buttons remain server-authorized after navigation; never reuse stale approval privileges.

---

## 7. Architecture by feature and traceability

The canonical screen IDs are defined in the Detailed Screen Specification. This table gives implementation responsibilities and milestone mapping rather than creating a competing inventory.

| Domain / screen family | Flutter responsibilities | Required server dependencies | Target |
|---|---|---|---|
| `PUB-*` Public discovery | Lists, search, detail, filters, public owner badges | Published-only directory APIs | M3 |
| `ID-*` Authentication and personal | Session UI, user preferences, affiliations, workspace switch | Identity + `/me` contexts | M1 |
| `NGO-*` Onboarding, settings | Provisional draft, verification states, organization context | Organization claim/verification/roles | M1 |
| `MEM-*` NGO membership | Invitation/application, roster, member detail, import status | NGO membership, category, claims, import jobs | M1/M2 |
| `VOL-*` Volunteers | Enrollment, opportunities, applications, assignments | Standing relationships, per-activity participation | M2 |
| `ACT-*` Activities/events | Publish, discover, register, check-in/participation updates | Ownership/visibility + attendance APIs | M2/M3 |
| `PRJ-*` Independent projects | Teams, tasks, milestones, resources, planned budget | Project service and scoped permission APIs | M2 |
| `FIN-*` Restricted finance | Accounts, receipts, expenses, transfers, approvals, reports | NGO finance posting/approval services | M2 |
| `COL-*` Collaborations | Request, offer, commitment review/acceptance | Versioned approvals and policy engine | M3 |
| `COM-*` Sectoral committees | Members, announcements, meetings, proposals | PWC committee and proposal APIs | M3 |
| `PWC-*` Alliance governance | Restricted PWC-related screens where mobile-suitable | Institutional membership/Board governance | M3/P1 |
| `OPS-*` Platform operations | Mobile only if separately justified | Restricted operations portal | Mostly web |

**[R]** For design handoff, every screen implementation record should include `screen_id`, route, context, capability, API dependencies, loading/empty/error states, analytics classification and test IDs.

---

## 8. Feature design: independent NGO membership and dues

### 8.1 Membership modes [S]
Each NGO chooses **open**, **approval required**, or **invitation only**. Flutter must render the server-supplied current policy rather than assuming a global flow. NGO-specific membership categories, renewal dates, fees, waivers, discounts, exemptions and partial payments must be visible according to permitted access.

**Workflow:** `Discover NGO → request/accept invitation → eligibility form → pending/active result → category + dues status → renew/pay outside gateway → authorized manual receipt → linked finance posting state`.

Keep membership status, renewal status, dues status and platform permissions separate. Active but overdue, waived but active, expired but historically recorded, and invited but not claimed are all valid combinations.

### 8.2 Existing-member import and claim [S]
- Web portal should handle CSV/Excel upload, preview, column mapping, error review and idempotent import jobs. Mobile may show read-only import status; full import UX can remain web-first.
- Imported records do not create login accounts.
- Claiming requires verified identity **plus** controlled claim token or NGO approval, not a contact match alone.
- Surface duplicate/ambiguous claims to authorized reviewers; never disclose other members' sensitive details in error messages.
- Never optimistically display claim success until the backend commits the link.

### 8.3 Fee display [R]
Show itemized **assessment, adjustments, paid amount, pending confirmation and outstanding amount**. Label dues and voluntary donations separately. Do not update verified amounts locally on a button press.

---

## 9. Feature design: volunteering, events and public inquiries

### 9.1 Distinct objects
1. A person's **volunteer profile** (skills/interests/preferences).
2. A standing **NGO volunteer relationship** (open/approval/invitation mode).
3. An **activity volunteer application and assignment** (individual event/project participation).

A one-day activity sign-up must not silently enroll the person as an NGO member or permanent volunteer. NGO administrators can import unclaimed standing volunteer records through the same controlled process family as membership imports.

### 9.2 Opportunity application UI
Eligibility, location, dates, organizer, ownership badge, required qualifications, privacy notice, apply/withdraw actions, status history and organizer communications. For children/patients/sensitive projects, open volunteer registration never overrides per-assignment safeguarding rules.

### 9.3 Assistance inquiries — MVP limitation
**[S]** General assistance/collaboration inquiries are within public MVP; **formal case management is deferred to Phase 2**. Collect only minimal contact and purpose fields, avoid open-ended medical/identity evidence uploads in general inquiries, route to restricted recipients and show clear service/response expectations. The app must not misrepresent this as an emergency response hotline.

---

## 10. Feature design: NGO project management

**[S]** MVP project tools include teams, tasks, milestones, resource requirements, budgets and progress.

### 10.1 Project workspace presentation
- Header: owning organization, project kind (independent/PWC/joint), publication visibility and status.
- Overview: goals, dates, manager, milestones and latest authorized update.
- Teams and tasks: assignment, priority, due date, status, completion evidence.
- Resources: requested/committed quantity, steward, dates and notes.
- Budget: planned values separate from posted actual spending; actuals sourced from approved finance entries only where authorized.
- Activity stream: meaningful project transitions; never expose private financial or beneficiary details in public updates.

### 10.2 Optimistic updates
**[R]** Optimistically update reversible task checkboxes only if the server contract supports revision checks and rollback. Do **not** optimistically complete approvals, assign volunteer authority, commit another NGO, or post money.

### 10.3 Joint-project ownership
A committee proposal becoming a PWC project does not commit an NGO. The NGO's explicit policy-based approval (one authorized signatory or multiple internal approvals) is a separate workflow with proposal version, accepted scope and evidence of approvals.

---

## 11. Feature design: restricted NGO finance

### 11.1 Access boundary
A Finance tab must be absent unless the active NGO context includes appropriate **separately authorized finance capabilities**. Server access remains authoritative; screens show an access-removed state on revocation. The existence of PWC Board, NGO president or primary NGO admin status never implies finance read rights.

### 11.2 Finance surfaces [S/R]
- Account list: multiple cash/bank registers, currency and **recorded** balance.
- Income: donations, dues, other receipts with source/reference.
- Expenses: category, payee, account and attachments where authorized.
- Transfer: from account, to account, amount; recorded internal movement is not new income.
- Approvals: direct-entry or approval-required mode by NGO; distinct submitter/approver when approval mode is enabled.
- Reports: private period/account summaries; export requires separate permission.
- Corrections: reverse/adjust with reason and immutable history; no invisible destructive edits of posted financial records.

### 11.3 Strong frontend behavior
- Use decimal-safe formatted amounts; do not use binary floating point for arithmetic that decides money totals. The server calculates official figures.
- Require a stable client-generated idempotency key or server-issued operation token for sensitive submissions per approved API contract.
- Disable repeat-submit and display `Processing` until response; after uncertain network outcome, **query operation status**, don't blindly resend with a new key.
- On `409` stale version, reload authoritative balance/approval state and explain the conflict.
- Never persist finance records in ordinary offline caches, background analytics or plaintext logs.
- Pending approval entries are visually distinguished from posted entries; pending entries must not inflate posted balances.
- Donation and dues receipts link exactly once to the corresponding financial transaction. UI must not generate a second finance record itself.
- Approval-mode changes require privileged reauthorization and cannot retroactively post old drafts.

### 11.4 Example mutation result (illustrative)

```json
{
  "operation_id": "<uuid>",
  "record_id": "<uuid>",
  "posting_status": "pending_approval",
  "source": "membership_payment",
  "source_id": "<uuid>",
  "recorded_balance_changed": false
}
```

The server is the source of truth for whether an entry is approved, posted or reversed.

---

## 12. Committees and PWC alliance collaboration

**[S]** The committee MVP includes profiles, members, announcements, meetings and project proposals. Active committees form gradually based on demand and expertise. Membership in a committee does not confer authority over any member NGO.

### 12.1 Committee views
Public committee description; members/roles subject to consent and visibility; private committee notices; meeting agenda/date/attendance as authorized; proposal composer; submitted proposal status; and linkage to an approved PWC project.

### 12.2 Collaboration state UI
Suggested display states: `request published → interest expressed → proposal shared → NGO internal approval(s) → accepted commitment → in progress → completed/withdrawn per agreement`. Exact backend state names require alignment. Distinguish offers of help from **binding accepted commitments**.

### 12.3 Commitment approval safeguards
- Show the NGO legal/display name and acting authorized representative.
- Display exact project and commitment version, responsible NGO, resources, estimated costs, dates and exit/amendment terms.
- Render whether policy requires one or multiple internal approvals.
- Disable the final `Accept Commitment` action without verified current policy grants.
- Use an explicit confirmation screen with a human-readable summary; persist server-issued approval evidence.
- If the offer changes after review, invalidate stale approvals and require new acknowledgement.
- Declining a request must never affect the NGO's unrelated PWC membership or internal platform data.

---

## 13. Networking, notifications and search

### 13.1 Public discovery
Search NGOs, public initiatives, events, opportunities and committees by sector and location. Show a clear publisher/owner badge. Registered status, platform verification and PWC institutional membership must have **distinct terminology and visual signals**; never substitute one for the other.

### 13.2 Notification architecture [R]
Treat push notifications as hints to fetch server-authorized content, not as trusted instructions or a replicated database. Prefer neutral push bodies for sensitive activities (`An approval needs your attention`), not names, medical details or balances.

Define inbox event kinds: membership application/approval, invitation, volunteer response, renewal reminder, event change, project assignment, finance approval request (generic wording), committee meeting and joint commitment review. Use server event IDs to deduplicate.

### 13.3 Read receipts, messaging and real time
Full chat/social-feed infrastructure is **not** assumed in the MVP. Structured request/offer threads and notification inbox are sufficient initially; realtime sockets may be deferred until measured need exists. Poll or refresh on foreground for time-sensitive status, but do not promise emergency-grade alert delivery.

---

## 14. State management, cache and offline policy

### 14.1 Recommended state layers
- **App-level state:** auth lifecycle, user preference, active context, dynamic capabilities, routing intent.
- **Server-derived feature state:** paginated organization/member/project lists, details, inbox, finance summaries.
- **Local ephemeral form state:** unsaved entries, validators, current wizard step.
- **Durable local preferences:** language, non-sensitive UI settings, safe last workspace hint.

**[R]** Use `AsyncValue`-style explicit loading/data/error states (or equivalent) and immutable typed DTOs. Repositories adapt wire models to presentation models; UI should not parse generic JSON maps.

### 14.2 Cache policy by classification

| Data | Offline strategy |
|---|---|
| Public NGO profiles, event summaries | Optional limited TTL cache |
| Personal profile | Minimal secure cache where justified; clear on logout |
| Private NGO member/volunteer rosters | No persistent offline cache in MVP |
| Restricted NGO finance, donor records | No persistent offline cache in MVP |
| Joint commitments and approvals | Always fetch fresh before final action; no offline approval |
| Draft public inquiry | In-memory only initially; no sensitive offline retention |
| Push notification inbox | Server-authoritative; cached titles only if safe |

Context changes should invalidate all context-sensitive providers, including counts and searches. Do not implement offline mutation queues for finance or commitments without a dedicated conflict/idempotency design and security review.

### 14.3 Connectivity and time handling
Support retry for safe reads, visible `Last updated` when stale, explicit `Offline` states, and recoverable unsaved forms. Display local Pakistani dates/times but transmit server timestamps in UTC with offsets; never rely on client clock for deadlines or signing authority.

---

## 15. Error handling and backend API contracts

### 15.1 Standard client error categories [R]

| API outcome | User experience |
|---|---|
| `400/422` invalid input | Field-level errors, preserve non-sensitive form state |
| `401` unauthenticated/expired | Refresh once; if unavailable route to login with safe return intent |
| `403` forbidden | No privileged content shown; refresh capabilities and offer context switch |
| `404` unavailable | Generic not found/unavailable for private objects; avoid enumeration |
| `409/412` conflict/stale revision | Refresh server state, show review-and-retry guidance |
| `429` throttled | Respect retry information; prevent abusive loops |
| `5xx` / timeout | Neutral recoverable error; do not presume mutation failed or succeeded |

**[R]** Agree one machine-readable error envelope, e.g. `code`, `message`, `field_errors`, `request_id`, optional `retry_after`; this is a proposed contract, not an existing endpoint guarantee. API field naming must be derived from an approved OpenAPI schema.

### 15.2 Idempotent mutation and stale submissions
- Use dedicated mutation controllers with explicit `idle/submitting/succeeded/failed/unknown` states.
- The `unknown` state is mandatory for timeouts on finance, imports and commitments.
- Refresh authoritative state after server conflict before allowing another confirmation.
- Prefer ETag/If-Match or record `version` on contested updates as backend draft proposes.

### 15.3 Pagination and search
Cursor pagination is recommended for member/volunteer/transaction lists. Server applies tenant scoping before counts and searches; the client should never fetch everything and filter locally for permissions. Filters and cursors should be reset on workspace switch.

---

## 16. Design system and UX standards

### 16.1 Foundation tokens [R]
Create a small reusable set of spacing, typography, color semantics, elevations, borders, form sizing and component states. Specify semantic colors (`success`, `warning`, `danger`, `restricted`) rather than coupling statuses to decorative colors. All important states must have labels/icons, not color alone.

### 16.2 Shared components
`PwcScaffold`, `PublicBottomNav`, `WorkspaceHeader`, `WorkspaceSwitcher`, `CapabilityGate`, `OrganizationStatusBadge`, `OwnershipBadge`, `VisibilityBadge`, `ApprovalTimeline`, `StatusChip`, `MoneyAmount`, `PaginatedList`, `EmptyState`, `ErrorState`, `ConfirmationSheet`, `AuditTrailSummary`, `FilePickerField`, `SafeExternalLink`, and reusable field form controls. Naming is illustrative.

### 16.3 Accessibility and localization
- Minimum accessible touch targets, readable scaling and screen reader names for every action.
- Support empty/loading/error and validation states at large text sizes.
- Urdu and right-to-left layout readiness should be designed, but full Urdu localization is **[O]**, not promised as a selected MVP feature.
- Format Pakistani currency appropriately, avoid hard-coded `Rs` assumptions in money models, and preserve underlying numeric precision.
- Camera/photos and geolocation require explicit feature-specific consent; no continuous location tracking by default.

---

## 17. Logging, analytics, monitoring and privacy

**[R]** Measure user journeys without uploading NGO-private finances, member rosters or sensitive inquiry content. Example permitted event metadata: `screen_id`, action type, result, pseudonymous request ID, context kind and error code; organization identifiers should be minimized or pseudonymized for analytics.

- Do not include access tokens, CNIC values, phone numbers, donation amounts, patient or child information in telemetry.
- Separate audit evidence maintained server-side from ordinary UX telemetry.
- Crash reports should scrub form payloads, authorization headers and API responses.
- Feature flags must not bypass backend authorization; remote configuration controls presentation or rollout only.
- Prefer opt-in or legally appropriate analytics configuration with documented retention.

---

## 18. Security threat scenarios and tests

| ID | Scenario | Expected result |
|---|---|---|
| FE-SEC-01 | NGO A manager pastes NGO B private route | Protected screen unavailable; backend returns no private data |
| FE-SEC-02 | Switch NGO A → B while finance page open | A finance providers reset before B context paints |
| FE-SEC-03 | PWC Board director opens NGO finance deep link | Forbidden; Board status provides no finance capability |
| FE-SEC-04 | NGO Primary Admin without finance role selects Finance | No finance UI/route data or summary exposed |
| FE-SEC-05 | Provisional organization attempts bulk import | Action unavailable; API denies until verified |
| FE-SEC-06 | Person claims imported member record using contact only | Claim denied pending token/NGO verification |
| FE-SEC-07 | Pending donation receipt appears in finance report | Posted balance unchanged until required approval |
| FE-SEC-08 | Double-tap financial submit / retry after timeout | One authoritative posting per source, no duplicates |
| FE-SEC-09 | User modifies NGO joint commitment after approval | Existing approvals stale; explicit new authorization required |
| FE-SEC-10 | Public event detail contains private roster | Roster never included in public API/cache/UI |
| FE-SEC-11 | Finance access revoked while app foregrounded | Subsequent reads denied; finance view resets |
| FE-SEC-12 | Logout while sensitive screen open | Credentials and sensitive state cleared, cannot back-navigate |
| FE-SEC-13 | API 403/404 for private member | No cross-tenant existence leak in client messaging |
| FE-SEC-14 | Offline at commitment confirmation | No offline approval; user receives explicit connection requirement |
| FE-SEC-15 | Organization leaves alliance | Alliance routes disabled; independent workspace retained if eligible |
| FE-SEC-16 | Restricted file URL forwarded to another user | Backend authorization denies file download |

Use frontend widget/integration tests **and** independent backend negative-access tests. UI tests alone cannot establish tenant isolation.

---

## 19. Flutter test strategy and CI

### 19.1 Test pyramid
- **Unit:** DTO conversion, dues formatting, capability checks (display only), state controllers, route parsing, error envelopes, cache keys.
- **Widget:** guest/public screens; context badges; members-only visibility; approval states; finance confirmations; accessibility and RTL layout readiness.
- **Integration:** login → NGO verify flow; A/B context switches; volunteer application; project task updates; pending finance → approval; joint commitment multi-approver; session expiry and deep links.
- **End-to-end environment:** real Django API test fixtures with two NGOs, one PWC Board role, separate finance authorizations, mixed public/private projects and simulated stale writes.

### 19.2 CI quality gates [R]
1. Format, static analysis and lint checks.
2. Code generation determinism and serialization contract tests.
3. Unit/widget tests with deterministic fixtures.
4. Critical integration tests on supported platforms.
5. API schema compatibility check against backend OpenAPI version.
6. Secret/credential leakage checks and dependency vulnerability review.
7. Release build and signing from controlled CI with separate dev/stage/prod settings.

### 19.3 Release environments
`development`, `staging`, `production`, isolated backend URLs, keys and push credentials. The application must visibly identify nonproduction environments for testers. Never point debug builds at production NGO finance data without explicit authorization.

---

## 20. Delivery milestones mapped to existing plan

### M1 — Secure identity and institutional foundation
**Flutter:** public/guest shell; registration/sign-in; personal profile; `/me/contexts`; contextual workspace switcher; organization create/claim/provisional status; verification progress; NGO roster/applications/invitations; authorization-aware navigation; initial imports status; base design system.

**Dependencies:** Django `accounts`, `access`, `organizations`, `ngo_memberships`, `files`, verification and permission endpoints.  
**Exit:** A person may manage authorized NGO A but cannot see NGO B, including cached views; provisional privileges are constrained; imported member claiming is protected.

### M2 — Independent NGO operations
**Flutter:** volunteer enrollment and assignments; activities and events; independent projects with teams/tasks/milestones/resources/budgets; dues and renewal UI; restricted multi-account finance, entry and approval states; project/financial scoped reports; private announcements.

**Dependencies:** backend volunteer, activities, projects, finance, transaction approval and document APIs.  
**Exit:** An NGO operates its members, volunteers, projects and recorded finances without PWC alliance finance visibility; transaction idempotency and account transfer rules pass tests.

### M3 — PWC collaboration and public participation
**Flutter:** complete public discovery; event participation; citizen inquiry; collaboration requests; joint-project commitment review; committee meetings/announcements/proposals; PWC initiative views; actionable updates.

**Dependencies:** alliance, committees, collaboration versioning, notification inbox, publish visibility and PWC project APIs.  
**Exit:** Two NGOs voluntarily agree on a joint project through authorized representatives; citizen can discover and register for an activity; committee can submit proposal without binding NGOs.

**[D] Later:** formal welfare-case management, online payments, full accounting, complex elections, live chat/social feed, advanced matching/AI, cross-chapter management and advanced offline mutation queues.

---

## 21. Backend/frontend contract checklist before coding

| Contract area | Proposed decision owner | Must confirm |
|---|---|---|
| Auth and refresh semantics | Backend/security | Token/session type, expiry, rotation, logout behavior |
| Context endpoint | Identity/access teams | `/me/contexts` shape, revisions, capability source |
| Permission identifiers | Backend/domain owners | Exact capability registry, scoped grants and denial patterns |
| Public profile statuses | Product/verification | Verified NGO vs registered NGO vs PWC member labels |
| Membership claim | Membership/security | Token/NGO approval protocol, rate limits and mismatch behavior |
| Financial posting | Finance/backend | Idempotency, pending vs posted balances, correction/refund states |
| Approval workflow | NGO finance and collaboration | Single/multiple authorizers, stale versions, self-approval rules |
| Documents/attachments | Backend/security | Signed URLs, scope, upload policies, virus scanning |
| Error format | Backend/frontend | Stable codes, request IDs, retry and field validation |
| Pagination & filters | Backend/frontend | Ordering, cursor shape, search boundaries |
| Notifications | Backend/mobile | Push payload minimization, deep-link shape, delivery semantics |
| Exports and deactivation | Product/legal/backend | Rights, retention, status and offline file handling |
| Locale and accessibility | Product/design | English/Urdu MVP scope, supported devices, contrast/testing targets |

**Contract freeze gate [R]:** Generate API models only after testable OpenAPI/JSON schema examples exist. A mock API can accelerate UI work but may not be treated as proof that backend permissions or financial workflows are implemented.

---

## 22. Open decisions and review register

### Confirmed as selected *provisionally* [S]
- Balanced public/volunteer, NGO and PWC alliance ecosystem.
- PWC directly operates the software; NGOs remain independent.
- Eligible nonmember NGOs can access basic NGO software; alliance membership confers additional benefits.
- Configurable membership and volunteer modes; secure import/claim; membership distinct from volunteering.
- Private NGO income/expense/donation recording, multiple accounts, configurable approvals, separate finance access, linked confirmed dues/donation receipts.
- Private/member/public project visibility and structured independent project management.
- Committee MVP profiles/members/announcements/meetings/proposals, voluntary and explicitly approved NGO commitments.
- Provisional NGO setup followed by category-appropriate verification, finance access recovery and controlled export/deactivation.

### Recommended, not yet approved [R]
- Flutter/Riverpod/go_router/Dio/typed code generation technical choices.
- Feature-first repository boundaries, context-clearing lifecycle, private cache prohibitions and modular shared API integration.
- Mobile-vs-web allocation; component names, routes, error/caching patterns and CI gates.
- Backend as source of truth for capability decisions; revision/idempotency-based mutation treatment.

### Open for sign-off [O]
1. Final Flutter version and package/version compatibility matrix.
2. NGO portal and PWC ops portal web framework choices.
3. Login factors, phone/email identity verification and session contract.
4. Final OpenAPI model names, capability codes and state transitions.
5. Attachment storage and secure download implementation.
6. Offline caching limits and exact retention durations.
7. Notifications transport/provider and consent model.
8. Supported handset/OS baseline; accessibility standard and Urdu in MVP or later.
9. Analytics privacy policy, technical support workflow and restricted access escalation.
10. Formal project commitment legal effect/e-signature requirements under applicable law.

### Review and approval sequence [R]
1. Product owner and NGO operations confirm screen/MVP traceability and visibility rules.
2. Security and backend engineers approve the context/authorization model, financial status contracts and tenant-isolation tests.
3. UI/UX confirms user journeys, accessibility, copy and differentiation of verified/membership statuses.
4. Flutter and web leads sign off platform framework choices, routes, typed API and build/test infrastructure.
5. Legal/organizational review confirms platform terms, privacy and institutional commitment language.
6. Only then promote this working draft to an approved architecture baseline.

---

## Appendix A — Mapping back to source documents

- **PWC Strategic & Product Foundation v1.0:** independent NGO autonomy; balanced ecosystem; member relationships; legal/operator distinction; MVP milestone ordering.
- **PWC App IA & Navigation v1.0:** public shell (Home, Discover, Participate, Updates, Profile); workspace switching; split mobile/web responsibilities; route intent and privacy.
- **PWC Detailed Mobile & Web Screen Specification v1.0:** source screen IDs (`PUB-*`, `ID-*`, `NGO-*`, `MEM-*`, `VOL-*`, `ACT-*`, `PRJ-*`, `FIN-*`, `COL-*`, `COM-*`, `PWC-*`, `OPS-*`), screen actions/validation and high-risk journeys.
- **PWC Identity, Authorization & Multi-NGO Data Model v1.0:** context grants, imported-record claiming, org verification, financial and collaboration domain boundaries.
- **PWC Django Backend & PostgreSQL Schema Foundation v1.0:** modular backend, tenant-scoped API, request authorization contract, finance idempotency/approval and nonfunctional test requirements.

**End of draft. All labels and technical choices remain subject to formal review.**
