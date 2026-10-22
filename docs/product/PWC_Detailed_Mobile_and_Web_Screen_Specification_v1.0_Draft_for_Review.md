# Pakistan Welfare Club (PWC)
## Detailed Mobile & Web Screen Specification v1.0 — Draft for Review
**Date:** 22 October 2026  
**Status:** WORKING DRAFT — NOT FORMALLY APPROVED  
**Sources:** PWC Strategic & Product Foundation v1.0 (draft); PWC App Information Architecture & Navigation v1.0 (draft).  
**Decision tags:** `[S]` user-selected provisionally; `[R]` recommended interaction/design; `[O]` unresolved; `[D]` deferred.
> This is a product specification for review, not approved pixel-perfect design. The screen IDs and milestone allocations trace to the prior IA document. No new requirements are silently treated as adopted decisions. PWC owns/operates the platform, but neither the Board nor alliance administrators gain inherent access to independently owned NGO private records.
## 1. Delivery surfaces and conventions
| Surface | Main users | Key tasks |
|---|---|---|
| Mobile application | Citizens, volunteers, NGO members, authorized operators | Discovery, applications, participation, notifications, routine approvals and project updates |
| NGO web portal | Authorized NGO users | Bulk imports, membership configuration, volunteers, finance, projects, reporting, access management |
| PWC operations web console | Authorized PWC verification/admissions/committee/project staff | Review eligibility, membership, approve PWC initiatives, manage alliance operations |
| Exceptional technical operations | Separately authorized platform technicians | Narrowly scoped, audited support and security recovery |
**Interaction conventions [R]:** Context header always shows active `Personal`, `NGO`, `Committee`, `PWC project`, `PWC alliance`, or `Platform operations` scope. Screen-level permissions are advisory for the UI; all sensitive operations need server-side object-level authorization. A public item can contain separately restricted participant lists, budget actuals and attachments. Search, notifications and exports follow source-object permissions.
**Screen template:** Each screen specifies core displayed fields, user actions, permission & scope, states/validation, navigation, and release milestone. Required versus optional fields should be finalized through UX and schema review; items described here are `[R]` unless already recorded `[S]` in source foundations.
## 2. Primary mobile navigation
| Tab | Core content | Protected actions |
|---|---|---|
| Home | Highlights, upcoming activities, signed-in actionable summaries | Private cards only for logged-in authorized user |
| Discover | NGOs, projects, events, volunteer opportunities and public committees | Filters must not query private NGO data |
| Participate | Apply, register, inquire; track own applications | Sign-in / contact policy required before submit |
| Updates | Invitations, outcomes, reminder inbox | Authentication; redacted previews |
| Profile | Personal details, memberships, volunteering, privacy, Workspaces switcher | Workspace opened only after explicit authorization |
**Workspace switcher [R]:** Personal is default; authorized NGO and committee/project contexts appear with organization name and status. Deep links never silently change institution or bypass permissions. Large member/volunteer imports and full finance reports are web-first, while mobile supports small forms, status checks and approvals as feasible.
## 3. Detailed screen inventory and specifications
### A. Identity and public experience
#### PUB-01 — Home `[M3]`
- **Intent / content [R]:** Featured activities, announcements, personalized overview. **Primary displayed data:** Featured public activities, relevant updates and role-specific pending items.
- **User actions [R]:** Open directory, event, profile or workspace shortcut.
- **Audience and authority [R]:** Public / signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No private cross-organization information in personalized cards.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-02 — Discover Hub `[M3]`
- **Intent / content [R]:** Select NGOs, initiatives, events, opportunities, committees. **Primary displayed data:** Directory categories, sectors, filter chips and unified search results.
- **User actions [R]:** Choose NGOs/projects/events/opportunities; search/filter.
- **Audience and authority [R]:** Public. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Only public or requester-authorized content indexed.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-03 — NGO Directory `[M3]`
- **Intent / content [R]:** Filter by welfare sector, city, coverage, verification status. **Primary displayed data:** NGO public profiles, city/sector filters, approved status distinctions.
- **User actions [R]:** Search/filter, open NGO, initiate authorized inquiry.
- **Audience and authority [R]:** Public. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Verification terminology does not imply financial endorsement.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-04 — NGO Public Profile `[M1/M3]`
- **Intent / content [R]:** About, sectors, approved public leadership/contacts, public activities. **Primary displayed data:** Approved about/mission/sector/location/contact, public activities and public leaders.
- **User actions [R]:** Follow/open activity; send authorized contact request.
- **Audience and authority [R]:** Public. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No private ordinary member directory or donor details.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-05 — Projects Directory & Detail `[M3]`
- **Intent / content [R]:** Owner type, organizer, partner NGOs, published progress, participation. **Primary displayed data:** Project ownership type, summary, participants publicly approved, published updates.
- **User actions [R]:** Browse/open; register or volunteer when enabled.
- **Audience and authority [R]:** Public where published. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Never call an NGO-independent project a PWC project by default.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-06 — Events & Opportunities `[M2/M3]`
- **Intent / content [R]:** Lists, details, eligibility, dates, registration/apply. **Primary displayed data:** Opportunity/event cards, dates, eligibility, organizer, application steps.
- **User actions [R]:** Search, register, volunteer apply, cancel if permitted.
- **Audience and authority [R]:** Public. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Applicant data only to authorized organizer; event participation ≠ membership.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-07 — Public Committee Profile `[M3]`
- **Intent / content [R]:** Sector, purpose, published updates, contact route. **Primary displayed data:** Committee published sector description, convener, updates.
- **User actions [R]:** Open approved project/proposal summaries; contact where provided.
- **Audience and authority [R]:** Public where published. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No committee confidential minutes in public.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-08 — Collaboration / Assistance Inquiry `[M3]`
- **Intent / content [R]:** General inquiry; limited safe contact and routing. **Primary displayed data:** Inquiry type, target organization or PWC route, minimal contact and message.
- **User actions [R]:** Submit controlled collaboration/assistance inquiry.
- **Audience and authority [R]:** Signed-in (or controlled guest if approved). All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No formal beneficiary case file; sensitive attachments and public exposure prohibited.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-09 — My Participation `[M2/M3]`
- **Intent / content [R]:** Volunteer applications, event registrations, accepted assignments. **Primary displayed data:** My event registrations, opportunity applications, volunteering and outcomes.
- **User actions [R]:** Review status, accept/decline invitation, withdraw if allowed.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Do not show another participant’s application.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PUB-10 — Updates Inbox `[M2/M3]`
- **Intent / content [R]:** Invitations, outcomes, reminders, announcements. **Primary displayed data:** Personal notifications, source organization and permitted action.
- **User actions [R]:** Open deep link, mark read, respond to invitation.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No sensitive previews; recheck scope on deep-link open.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ID-01 — Register / Sign In `[M1]`
- **Intent / content [R]:** Account creation and authentication. **Primary displayed data:** Phone/email login or registration, credential confirmation, consent acknowledgements.
- **User actions [R]:** Create account; sign in; recover access.
- **Audience and authority [R]:** Public. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Duplicate contact, invalid code, rate-limited attempts; no account enumeration.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ID-02 — Personal Profile `[M1]`
- **Intent / content [R]:** Identity, basic preferences, contact controls. **Primary displayed data:** Display name, verified contact methods, city, interests, optional volunteer skills.
- **User actions [R]:** Edit profile; choose private/public display fields; confirm sensitive changes.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Missing required identity evidence, duplicate contact; preserve existing NGO memberships.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ID-03 — My Affiliations `[M1/M2]`
- **Intent / content [R]:** NGO memberships, volunteering links, PWC project associations. **Primary displayed data:** Separate NGO memberships, standing volunteer associations, activity participation and committee/project roles.
- **User actions [R]:** Open relationship detail; request correction; select authorized workspace.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Revoked relationship must disappear from privileged workspaces without deleting history.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ID-04 — Workspaces Switcher `[M1]`
- **Intent / content [R]:** Select authorized personal/NGO/PWC context. **Primary displayed data:** Available workspaces, institution labels, role badges, verification status.
- **User actions [R]:** Switch to exactly one organization/committee/project scope; return to Personal.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No access / suspended / expired role; cross-scope action blocked.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ID-05 — Privacy & Security `[M1]`
- **Intent / content [R]:** Account security, notifications, privacy controls. **Primary displayed data:** Sessions, notification preferences, profile privacy, data request and sign-out.
- **User actions [R]:** Update preferences; revoke session; initiate personal data request.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Reauthentication where needed; separate account closure from NGO record removal.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

### B. Independent NGO onboarding and operations
#### ORG-01 — Search / Claim / Create NGO `[M1]`
- **Intent / content [R]:** Check existing NGO, start claim or new draft. **Primary displayed data:** Organization name, geography, registration status, matching candidate entities.
- **User actions [R]:** Search existing; request claim; create new draft.
- **Audience and authority [R]:** Signed-in. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Duplicate candidate and disputed claim go to review, not direct ownership.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-02 — Provisional NGO Workspace `[M1]`
- **Intent / content [R]:** Draft profile, checklist, verification submission; restricted operations. **Primary displayed data:** Provisional status, profile completeness checklist, application draft.
- **User actions [R]:** Edit draft; save; submit verification.
- **Audience and authority [R]:** Provisional owner. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No existing NGO private data, member import, restricted finance or public verified badge.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-03 — NGO Verification Submission / Status `[M1]`
- **Intent / content [R]:** Category-specific documents, authority evidence, review status. **Primary displayed data:** Registered/unregistered evidence checklist, representative authority proof, review notes/status.
- **User actions [R]:** Upload evidence; submit; respond to reviewer requests.
- **Audience and authority [R]:** Provisional/scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Reject unsafe file types; restrict evidence; no automatic verification.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-04 — NGO Overview `[M1/M2]`
- **Intent / content [R]:** Pending tasks, membership totals, activities and allowed summaries. **Primary displayed data:** Organization context, pending applications, task summaries, approved public metrics.
- **User actions [R]:** Navigate to permitted modules; act on assigned reviews.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Never show finance amounts absent separately assigned finance scope.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-05 — NGO Profile Editor `[M1]`
- **Intent / content [R]:** Public fields and independent NGO settings. **Primary displayed data:** Name, description, sectors, contact preferences, approved public leaders, location, visibility.
- **User actions [R]:** Update draft; preview public page; publish under permissions.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Ordinary member directory stays private; public profile must not imply legal status.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-06 — Team & Permissions `[M1]`
- **Intent / content [R]:** Invite admins, assign roles, manage revocation. **Primary displayed data:** Team members, assignments, officeholder titles, granular permissions, role grant history.
- **User actions [R]:** Invite, grant, revoke, transfer primary control via enhanced process.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Prevent self-escalation and last-admin lockout; finance access separate.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-07 — Membership Overview / Roster `[M1]`
- **Intent / content [R]:** Filter and manage members; distinguish unclaimed records. **Primary displayed data:** Membership roster, category, claim status, membership status, dues summary subject to permissions.
- **User actions [R]:** Search, filter, create member, export if authorized.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Keep names/contact private; avoid broad PWC/global search indexing.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-08 — Membership Requests & Invites `[M1]`
- **Intent / content [R]:** Accept/decline, invite or open-join handling. **Primary displayed data:** Applications, invitations, selected enrollment mode, pending decision reasons.
- **User actions [R]:** Invite, approve, decline, request information, cancel invitation.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Open/approval/invite-only must be enforced server-side; no double approvals.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-09 — Member Detail `[M1]`
- **Intent / content [R]:** Membership state, category, validity and authorized details. **Primary displayed data:** Membership identifier, category, linked user if claimed, status, history, renewal information.
- **User actions [R]:** Edit scoped details; change category/status; start dues action.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Permission-check sensitive fields and historic changes.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-10 — Import Members `[M1]`
- **Intent / content [R]:** Upload, map columns, validate, review duplicates, import. **Primary displayed data:** CSV/XLSX upload, templates, field mapping, row validation, duplicate preview, import report.
- **User actions [R]:** Upload, preview, skip/correct conflicts, commit import.
- **Audience and authority [R]:** Scoped; web preferred. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No automatic login creation; atomic/retry-safe import batches; safe PII handling.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-11 — Membership Claim / Link `[M1]`
- **Intent / content [R]:** Verified identity + single-use token or NGO approval. **Primary displayed data:** Unclaimed record summary with minimal masked data; claim token or NGO approval status.
- **User actions [R]:** Claim record; verify identity; request NGO review.
- **Audience and authority [R]:** Signed-in + verified process. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Expired token, conflict, already-claimed, mismatched identity require safe recovery.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-12 — Member Categories / Rules `[M1/M2]`
- **Intent / content [R]:** Configure open/approval/invite, fees, renewal/expiry. **Primary displayed data:** Membership admission mode, categories, category fee, period, grace/expiry settings.
- **User actions [R]:** Add category; adjust rules; preview prospective change; save.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Historical assessments must not silently change after fee-rule edit.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-13 — Member Dues `[M2]`
- **Intent / content [R]:** Charges, adjustments, waivers, partial payments, receipts. **Primary displayed data:** Member assessments, concessions, payment allocations, due/renewal states, receipts.
- **User actions [R]:** Assess dues; grant authorized discount/waiver; register payment; reverse.
- **Audience and authority [R]:** Scoped; financial details separately scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Idempotent payment linkage; pending approvals do not count as finalized posted income.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-14 — Volunteer Roster / Enrollment `[M2]`
- **Intent / content [R]:** Applications, mode settings, approved relationships. **Primary displayed data:** Volunteer roster, relationship status, screening/qualification flags as permitted.
- **User actions [R]:** Enroll/import/invite, review enrollment, deactivate relationship.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Open volunteer roster does not imply access to sensitive field assignments.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-15 — Import Volunteers / Claim `[M2]`
- **Intent / content [R]:** Manual/CSV/Excel import and secure claim process. **Primary displayed data:** Volunteer import template, mappings, duplicate check, unclaimed relationship state.
- **User actions [R]:** Upload, validate, commit, initiate secure claiming.
- **Audience and authority [R]:** Scoped; web preferred. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Do not convert volunteer to formal NGO member or create login automatically.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-16 — Volunteer Opportunity Manager `[M2]`
- **Intent / content [R]:** Post opportunity, define roles, accept participants. **Primary displayed data:** Opportunity title, organizer, requirements, location, positions, dates, application state.
- **User actions [R]:** Create/publish, review applications, invite candidates, close opportunity.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Public listing must not reveal volunteer personal contacts.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-17 — Volunteer Assignments `[M2]`
- **Intent / content [R]:** Confirm assignments and participation. **Primary displayed data:** Volunteer assignment status, supervisor, activity details, participation evidence.
- **User actions [R]:** Assign, confirm/decline, mark attended/completed.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Only relevant organizer can confirm participation; no self-verification by default.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-18 — NGO Activities / Events `[M2]`
- **Intent / content [R]:** Create, publish, register, record attendance. **Primary displayed data:** Event details, venue/date, participant limits, visibility, registration and attendance.
- **User actions [R]:** Draft/publish, register participants, check in, close event.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Cannot publish private participant roster or sensitive attendance records.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-19 — NGO Projects `[M2]`
- **Intent / content [R]:** List, create, set visibility, track status. **Primary displayed data:** Project list, owner, status, visibility, planned dates, named manager.
- **User actions [R]:** Create, filter, archive/close authorized projects.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Project ownership cannot be changed into PWC-led by display label alone.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-20 — Project Detail & Team `[M2]`
- **Intent / content [R]:** Authorized team and participant access. **Primary displayed data:** Project description, team members, scoped roles, updates, linked activities.
- **User actions [R]:** Assign team, post updates, manage status.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Members-only/public project view masks internal tasks and restricted data.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-21 — Project Tasks / Milestones `[M2]`
- **Intent / content [R]:** Assignments and delivery progress. **Primary displayed data:** Task title, assignee, due date, priority, status; milestone dates/evidence.
- **User actions [R]:** Create/assign tasks; update progress; mark milestone complete.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No task visibility across NGO workspaces without explicit joint-project scope.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-22 — Project Resources / Budget `[M2]`
- **Intent / content [R]:** Resource needs, planned budgets, linked actuals. **Primary displayed data:** Resource type/quantity/status, budget categories, planned figures, linked actual summaries.
- **User actions [R]:** Add request, reserve authorized resources, revise project budget.
- **Audience and authority [R]:** Scoped; finance actuals additionally restricted. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Finance actuals visible only to specifically authorized users; estimates ≠ spending.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-23 — NGO Announcements `[M2]`
- **Intent / content [R]:** Publish to permitted audience. **Primary displayed data:** Audience, subject, message body, delivery channels, scheduling if supported.
- **User actions [R]:** Compose, preview, publish to authorized audience.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Never leak private membership/donor details in public notifications.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-24 — NGO Reports / Export `[M2]`
- **Intent / content [R]:** Authorized operational reports/export. **Primary displayed data:** Operational metrics, date-range filters, scoped export format.
- **User actions [R]:** Generate report; export member/project/volunteer records as permitted.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No cross-tenant aggregation or export beyond granted fields.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ORG-25 — NGO Settings / Workspace Exit `[M1/M2]`
- **Intent / content [R]:** Policy settings, data-export/deactivation initiation. **Primary displayed data:** Enrollment/privacy/finance preferences, verification, data export, alliance and software exit.
- **User actions [R]:** Update settings; request data export; initiate authorized deactivation.
- **Audience and authority [R]:** Scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Alliance withdrawal is not software deletion; retention law and identity separation.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

### C. Private NGO finance
#### FIN-01 — Finance Overview `[M2]`
- **Intent / content [R]:** Restricted balances, pending approvals, latest transactions. **Primary displayed data:** Account recorded balances, pending submissions, income/expense summaries, currency.
- **User actions [R]:** Filter period; open account/transaction; start authorized entry.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Restricted to finance scope; never placed on ordinary NGO or PWC alliance dashboard.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-02 — Cash & Bank Accounts `[M2]`
- **Intent / content [R]:** Create/manage account registers, opening balance references. **Primary displayed data:** Cash/bank register label, opening balance, active status, transaction totals.
- **User actions [R]:** Create account; edit metadata; view statement; close if eligible.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No silent deletion of used accounts or retroactive opening-balance changes.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-03 — Income / Donations `[M2]`
- **Intent / content [R]:** Entry, source, restricted donor fields, receipt links. **Primary displayed data:** Source type, date, amount, account, donor/source, purpose, receipt reference, attachment.
- **User actions [R]:** Save draft; submit/post according to mode; issue linked receipt record.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Donation vs dues classification; prevent duplicate postings from same receipt.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-04 — Expenses `[M2]`
- **Intent / content [R]:** Create/edit draft, categorize, attach evidence. **Primary displayed data:** Payee, amount, account, category, purpose, project tag, evidence file.
- **User actions [R]:** Draft, submit/post; correct/reverse with permission.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No negative cash amounts; account/NGO ownership validated server-side.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-05 — Transfers `[M2]`
- **Intent / content [R]:** Linked source/destination ledger entries. **Primary displayed data:** Source/destination within same NGO, amount, date, note.
- **User actions [R]:** Submit/post linked transfer.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Not income or expense; ensure atomic two-sided movement and no same-account transfer.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-06 — Financial Approvals `[M2]`
- **Intent / content [R]:** Approve/reject independent entries, separation of duties. **Primary displayed data:** Pending entry, submitter, supporting documents, approval history.
- **User actions [R]:** Approve, reject, return for correction.
- **Audience and authority [R]:** Authorized approver. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Submitter cannot approve own record in approval mode; access changes cannot self-approve.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-07 — Financial Entry Detail `[M2]`
- **Intent / content [R]:** Posted status, approval history, correction/reversal. **Primary displayed data:** Entry status, source receipt, account movements, prior adjustments, creator/approver.
- **User actions [R]:** View history; initiate permitted reversal/correction.
- **Audience and authority [R]:** NGO finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Posted records must retain audit history; do not directly overwrite posted amounts.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-08 — Finance Reports / Export `[M2]`
- **Intent / content [R]:** Recorded balances, reports by account/category/period. **Primary displayed data:** Per-account and consolidated recorded balances, categories, periods, export filters.
- **User actions [R]:** Run authorized report; export with logging.
- **Audience and authority [R]:** Explicit export scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Recorded balance ≠ reconciled bank balance; no alliance-wide financial view.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### FIN-09 — Finance Policy & Access `[M2]`
- **Intent / content [R]:** Direct/approval mode; separate finance-role authorizations and recovery. **Primary displayed data:** Approval mode, finance users, grants, recovery status, security events.
- **User actions [R]:** Change mode with checks; assign/revoke finance authority; initiate verified recovery.
- **Audience and authority [R]:** Restricted governance of finance scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No unapproved self-grant; pending entry effects not changed retroactively.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

### D. Alliance, committees and collaboration
#### ALL-01 — Institutional PWC Membership `[M3]`
- **Intent / content [R]:** Apply, track status, select authorized representatives. **Primary displayed data:** Alliance application status, institutional category, nominated authorized representative.
- **User actions [R]:** Apply, submit evidence, track review; request withdrawal.
- **Audience and authority [R]:** NGO/PWC scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Platform eligibility and alliance membership stay independent.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ALL-02 — Alliance Member Registry `[M3]`
- **Intent / content [R]:** Eligible PWC member roster and membership categories. **Primary displayed data:** Approved institutional member summary, vote eligibility/class, public status where approved.
- **User actions [R]:** Search members; open eligible institutional profile.
- **Audience and authority [R]:** PWC scoped / approved public summary. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No private NGO roster or finance exposure.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### ALL-03 — PWC Dashboard `[M3]`
- **Intent / content [R]:** Member network, committee activity, joint initiatives. **Primary displayed data:** PWC-owned indicators, pending collaboration actions, committee and joint-project overview.
- **User actions [R]:** Open authorized alliance item; navigate project approvals.
- **Audience and authority [R]:** PWC scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Do not blend independent NGO impact into PWC-owned outcomes.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COM-01 — Committee Directory & Profile `[M3]`
- **Intent / content [R]:** Sector, convener, purpose, approved roster. **Primary displayed data:** Committee sector, convener, published purpose, permitted participants.
- **User actions [R]:** Discover; request participation if supported; open public updates.
- **Audience and authority [R]:** Public/scoped portions. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Committee status does not give authority over NGOs.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COM-02 — Committee Workspace `[M3]`
- **Intent / content [R]:** Members, announcements, meetings, tasks relevant to proposals. **Primary displayed data:** Committee members, announcements, meetings, proposals and role assignments.
- **User actions [R]:** Post permitted update; access meeting/proposal actions.
- **Audience and authority [R]:** Committee scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Scope is specific committee; no automatic NGO management rights.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COM-03 — Committee Meetings `[M3]`
- **Intent / content [R]:** Agenda, participation, notes, action items. **Primary displayed data:** Date/time, agenda, invited members, minutes and action items.
- **User actions [R]:** Schedule meeting; RSVP; publish notes; assign action.
- **Audience and authority [R]:** Committee scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Only permitted recipients access private minutes.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COM-04 — Committee Proposal `[M3]`
- **Intent / content [R]:** Draft, submit, review status, referenced NGOs. **Primary displayed data:** Problem statement, proposed impact, resources, interested NGOs, review state.
- **User actions [R]:** Draft, submit, revise after review.
- **Audience and authority [R]:** Committee/PWC review scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Approval by PWC never auto-commits member organizations.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COL-01 — Collaboration Requests `[M3]`
- **Intent / content [R]:** Requests and offers, responding organizations. **Primary displayed data:** Collaboration request owner, sector, assistance needed, deadline, visibility.
- **User actions [R]:** Create request if permitted; filter; express interest.
- **Audience and authority [R]:** Public/NGO scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Expression of interest is not an NGO commitment.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COL-02 — Collaboration Detail `[M3]`
- **Intent / content [R]:** Scope, requested help, responses and authorized discussion. **Primary displayed data:** Request details, participating replies, messages/clarifications where supported.
- **User actions [R]:** Offer help; review interest; invite to commitment step.
- **Audience and authority [R]:** Request owner/participants. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Participant-specific replies and private contact details protected.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COL-03 — Proposed NGO Commitment `[M3]`
- **Intent / content [R]:** Declared contribution, responsible representative, approval mode. **Primary displayed data:** NGO-specific proposed contribution, responsible parties, dates, conditions, approver policy.
- **User actions [R]:** Create proposal; send for authorized organizational approval.
- **Audience and authority [R]:** Specific NGO scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Cannot bind NGO without its configured approvers.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COL-04 — Commitment Approvals `[M3]`
- **Intent / content [R]:** Single/multi-approval rules; acceptance/amendment/withdrawal. **Primary displayed data:** Ordered/parallel approval steps, approver identity, immutable accepted scope.
- **User actions [R]:** Approve/reject/request revision; amend or withdraw with recorded procedure.
- **Audience and authority [R]:** Delegated NGO approvers. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No acceptance until required approvals complete; preserve version history.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### COL-05 — Joint/PWC Project Workspace `[M3]`
- **Intent / content [R]:** Project lead, participating NGOs, permissions, milestones, outcomes. **Primary displayed data:** PWC/joint project ownership, participation agreements, team, milestones, results.
- **User actions [R]:** Update approved project; report delivery; close scope.
- **Audience and authority [R]:** Project scope. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Project obligations limited to agreed commitments; private NGO projects stay separate.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

### E. PWC review, governance and technical operations
#### PWC-01 — Organization Verification Queue `[M1]`
- **Intent / content [R]:** Authority checks, legal category evidence, duplicates. **Primary displayed data:** Organization category, submitted authority evidence, duplicate flags, review history.
- **User actions [R]:** Request clarification; approve verification; decline with reason.
- **Audience and authority [R]:** Platform verifier. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Reviewer may not claim NGO leadership or bypass contested-authority review.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PWC-02 — Institutional Membership Review `[M3]`
- **Intent / content [R]:** Approve/decline PWC membership and rights. **Primary displayed data:** Alliance membership application, category and voting eligibility evidence.
- **User actions [R]:** Approve/decline, document result, notify NGO.
- **Audience and authority [R]:** Authorized PWC admissions staff. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Alliance admission is not platform verification; governance eligibility separately checked.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PWC-03 — Committee Administration `[M3]`
- **Intent / content [R]:** Activate committee, appoint conveners, scope access. **Primary displayed data:** Committee type, activation status, convener, membership, scope.
- **User actions [R]:** Create/activate committee; assign convener; close inactive group.
- **Audience and authority [R]:** PWC administration. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Committee roles grant no NGO internal powers.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PWC-04 — Joint Initiative Approval `[M3]`
- **Intent / content [R]:** Review proposed project, approval routing, execution scope. **Primary displayed data:** Proposal purpose, project ownership, budget request, decision routing.
- **User actions [R]:** Approve/reject/revise PWC project scope.
- **Audience and authority [R]:** Delegated PWC authority. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Approves PWC undertaking only; not external NGO commitments.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PWC-05 — PWC Announcements & Reporting `[M3]`
- **Intent / content [R]:** Official announcements, high-level project reports. **Primary displayed data:** Official PWC announcements, PWC-owned activity metrics and report periods.
- **User actions [R]:** Publish or export authorized PWC statements.
- **Audience and authority [R]:** PWC scoped. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Clearly distinguish PWC-led, joint verified and NGO independently reported results.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### GOV-01 — Board & General Assembly Directory `[M3 limited]`
- **Intent / content [R]:** Board roles, terms, representative records, published governance docs. **Primary displayed data:** Board member names, office title, term dates, member representation and approved records.
- **User actions [R]:** View directory; update authorized term/representation data.
- **Audience and authority [R]:** Scoped / published summary. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. No formal electronic election in MVP; no NGO finance authority.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### GOV-02 — Formal electronic elections `[P2 [D]]`
- **Intent / content [R]:** Nomination, ballot, tally, disputes. **Primary displayed data:** Elections, nominations and votes.
- **User actions [R]:** Deferred; no MVP screen actions.
- **Audience and authority [R]:** Eligible voters, governed by bylaws. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Constitutional voting rules must be formally approved first.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### OPS-01 — Audit, Support and Recovery `[M1/M2]`
- **Intent / content [R]:** Break-glass requests, security logs, access trace. **Primary displayed data:** Support case, verified requester, narrow scope, justification, audit events.
- **User actions [R]:** Request/review exceptional access; time-bound recovery; close incident.
- **Audience and authority [R]:** Privileged technical operators only. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Ordinary alliance roles cannot invoke break-glass; no routine browsing.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

### F. Deferred feature specifications
#### CASE-01 — Sensitive Welfare Case Intake `[P1/P2 [D]]`
- **Intent / content [R]:** Triage, case files, referral and outcome controls. **Primary displayed data:** Private case intake, assessment, assigned officer, referral/outcomes.
- **User actions [R]:** Deferred; no MVP screen actions.
- **Audience and authority [R]:** Specifically assigned safeguarding roles. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Safeguarding and formal case protocols required before activation.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### PAY-01 — Online Donations & Payments `[P2 [D]]`
- **Intent / content [R]:** Payment processing, disbursement, reconciliation. **Primary displayed data:** Direct payment capture, settlement, receipt reconciliation.
- **User actions [R]:** Deferred; no MVP screen actions.
- **Audience and authority [R]:** Compliance-ready financial actors. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Legal, payment-provider and donation compliance must be resolved.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

#### NAT-01 — Multi-chapter Operations `[P2 [D]]`
- **Intent / content [R]:** Chapter registration, roles, inter-chapter initiatives. **Primary displayed data:** National/chapter scopes, interchapter project links.
- **User actions [R]:** Deferred; no MVP screen actions.
- **Audience and authority [R]:** Authorized chapter/national roles. All modifications require authenticated permission for the active owner, committee or PWC scope; public availability never implies edit permission.
- **States, validation and security [R]:** Loading; empty; success; failed validation; access revoked; safe retry where applicable. Chapter governance not yet decided.
- **Navigation [R]:** Enter from the applicable directory, workspace dashboard, notification or parent list; on save return to the appropriate detail/list while preserving active context. Back/cancel must not silently submit changes.

## 4. Detailed high-risk workflow contracts
### HF-01 NGO creation and claim
- **Path:** `ORG-01 → ORG-02 → ORG-03 → PWC-01 → ORG-04`
- **Invariant:** Draft workspace is never an entitlement to existing NGO data. Organization status, legal registration status, admin authority, and PWC institutional membership are separate facts.
- **Required UI states and test cases:** New claimant of existing name; rejected authority claim; duplicate registered ID; contested leadership; unregistered evidence category.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-02 Membership with configurable modes
- **Path:** `ORG-12 → ORG-08 → ORG-07 → ORG-09`
- **Invariant:** Open enrollment grants only ordinary membership where criteria pass; approval mode requires reviewer; invitation-only requires valid accepted invite. Titles do not grant administrative rights.
- **Required UI states and test cases:** Invite expired; application withdrawn; category retired; suspended member; duplicated invite/submit.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-03 Bulk member and volunteer import
- **Path:** `ORG-10 / ORG-15 → import preview → import report → ORG-11`
- **Invariant:** Upload parsed in NGO context, preview field mappings/duplicates, commit idempotent batch, create only unclaimed NGO-scoped records; personal account linking needs verified identity + token or NGO approval.
- **Required UI states and test cases:** Partial invalid rows; conflicting phone; multiple same names; imported record previously claimed; source-file PII retention.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-04 Dues and finance receipt integration
- **Path:** `ORG-13 → FIN-03 → FIN-06 if required → FIN-07 → FIN-08`
- **Invariant:** Assess dues, apply authorized concessions, allocate partial payment to assessment, link one source receipt to one posting; pending entries do not change posted account balance. No duplicate on retries.
- **Required UI states and test cases:** Discount exceeds due; reverse after renewal; partial overpayment; payment source cancellation; stale approval.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-05 Multi-account finance
- **Path:** `FIN-02 → FIN-03/04/05 → FIN-06 as needed → FIN-07/08`
- **Invariant:** Each journal record is scoped to NGO, signed amount rules apply, transfer creates atomic balanced account movements but no income/expense, posted entries corrected by reversal.
- **Required UI states and test cases:** Identical source/destination; insufficient funds policy open; account closure with existing entries; permission revoked mid-approval.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-06 Volunteer enrollment and participation
- **Path:** `PUB-06 → PUB-09; ORG-14/16/17`
- **Invariant:** Standing NGO volunteer relationship, formal NGO membership and one-event application are separate; open enrollment does not waive safeguarding checks for sensitive assignments.
- **Required UI states and test cases:** Over-capacity; declined application; consent withdrawn; volunteer without PWC login imported.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-07 Independent NGO project lifecycle
- **Path:** `ORG-19 → ORG-20 → ORG-21/22 → ORG-24`
- **Invariant:** One NGO owns an independent project; Public/Members Only/Private controls discovery; work assignment follows scoped grants; budget estimates and finance actuals are separate.
- **Required UI states and test cases:** Project manager without finance read scope; task owner removed; confidential attachment under public project.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-08 Joint project and commitment authorization
- **Path:** `COM-04 → PWC-04 → COL-03 → COL-04 → COL-05`
- **Invariant:** PWC approval covers PWC undertaking only. NGO commitment moves from interest/proposed to accepted only when that NGO’s configured single/multiple approvers finish approving a specific immutable version.
- **Required UI states and test cases:** Approval withdrawn; changed amount/term mid-approval; co-approver inactive; duplicate acceptance; partial NGO opt-out.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-09 Workspace and data exit
- **Path:** `ALL-01 or ORG-25 → export/leave/deactivation`
- **Invariant:** Alliance exit removes only alliance privileges; eligible NGO software tenant continues. Platform exit demands authorized exports, secure deactivation and lawful policy-based retention/deletion.
- **Required UI states and test cases:** Contested requester; outstanding financial records; pending joint commitment; historical records in external projects.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

### HF-10 Exceptional technical access
- **Path:** `OPS-01 → narrow request → independent approval → time-limited action → audit closure`
- **Invariant:** Ordinary PWC Board and admissions users cannot browse NGO private data. Exceptional access requires verified purpose, narrow scope, authorization, logging and after-action review.
- **Required UI states and test cases:** Emergency recovery; expired grant; attempted export; support operator also PWC Board member.
- **Acceptance [R]:** Authorized happy path completes; repeated submission is safely handled; unauthorized access via direct URL/API denied; audit evidence is available to appropriate owner without revealing another organization’s private records.

## 5. Permission and information-disclosure requirements
- **`personal`: Own public/profile, applications, affiliations; no organizational manage scope inferred.**
- **`ngo:{id}`: Every membership, volunteer, project, and finance record scoped by owning NGO. Membership relationship ≠ administrator role.**
- **`ngo:{id}:finance`: View, record, approve, reverse, export and access-manage are distinct grants. Primary NGO administrator has no implicit finance read.**
- **`committee:{id}`: Committee membership, meeting and proposal scope; no automatic authority to bind represented NGOs.**
- **`project:{id}`: Joint project participants receive only authorized project data and specifically shared commitments/financial evidence.**
- **`pwc:alliance`: Admission, sectoral coordination, Board records, PWC projects; not NGO private roster or accounts.**
- **`platform:operations`: Separate privileged technical realm; exception access is time-bound, justified and auditable.**
**Field-level privacy:** A publicly listed NGO may publish approved officeholders and contacts, but never a complete private roster. Public events must not expose private participants, donor identities, case details, or restricted attachments. Status/error messages should not disclose secret record existence.
## 6. Shared UI design requirements and components [R]
| Component | Behavioral requirement |
|---|---|
| Workspace header | Owner identity, scope badge, verified/provisional status, switch action; confirmation for dangerous context switch. |
| Scoped table/list | Server-filtered records, pagination, safe search, permission-based row actions, export gated separately. |
| Status badge | Explicit draft/pending/approved/declined/active/expired where appropriate; never equate payment with membership status. |
| Form pattern | Required/optional indicators, inline validation, autosave only for nonbinding drafts, reviewed confirmation for binding actions. |
| Upload/import wizard | Template download, upload, mapping, row-level preview, duplicate resolution, idempotent commit, summary. |
| Approval timeline | Approvers, statuses, timestamps, returned-for-correction, immutable approval version; no self-approval in finance approval mode. |
| Finance amount display | Currency PKR by default assumption [R/O]; recorded vs pending clearly labeled; multi-account context prominent. |
| Empty/restricted states | Helpful first-use actions and unambiguous access denied; avoid leaking cross-NGO existence or filenames. |
| Notifications | Minimal previews, source organization context, authorized deep-link revalidation, quiet controls. |
| Responsive and accessible layout | Mobile safe tap targets, form labels, keyboard navigation on web, scalable text, Urdu-ready strings if adopted. |
| Confirmation dialogs | Apply to irreversible remove/reversal, organization exit, financial posting, project commitment and authority transfer. |
## 7. Cross-screen testing and acceptance matrix
| Test ID | Scenario | Expected result |
|---|---|---|
| T01 | NGO A staff requests NGO B member/export endpoint | Forbidden; no record content leaked. |
| T02 | PWC Board user requests NGO A finance balance | Forbidden absent separately issued NGO A finance grant. |
| T03 | Provisional NGO owner searches existing duplicate NGO | No takeover or private data exposure; verification pathway. |
| T04 | Imported unclaimed person logs in | No automatic link by matching name/phone; claim verification required. |
| T05 | Dues receipt submit retried twice | One source payment and no double posting. |
| T06 | Approval-required finance entry submitted by X | X cannot finalize own entry; account balance pending until Y approves. |
| T07 | Transfer between NGO accounts | Paired balanced movements; no extra income/expense. |
| T08 | Published project contains private budget/participant list | Public sees permitted summary only. |
| T09 | PWC approves joint project without NGO approval | NGO status remains uncommitted. |
| T10 | NGO changes required approvers mid-commitment | Re-evaluate safely; cannot silently approve previous version. |
| T11 | NGO resigns from PWC alliance | NGO software workspace persists if otherwise eligible. |
| T12 | NGO requests platform exit | Data export and retention/deactivation flow; no instant arbitrary deletion. |
| T13 | Notification deep link after permission revoked | Access denied and safe route fallback. |
| T14 | Technical operator requests unlogged finance access | Denied or escalated; no routine support bypass. |
| T15 | Open volunteer enrollment for sensitive role | Assignment still follows role-specific safeguarding requirements. |
## 8. Scope and release sequence
| Milestone | Screens | Completion gate |
|---|---|---|
| **M1** Secure foundation | `ID-01–05`, `ORG-01–12`, `PWC-01`, `OPS-01` | NGO verification and scoped member management work without cross-tenant access |
| **M2** NGO operations | `ORG-13–25`, `FIN-01–09`, `PUB-06`, `PUB-09` | Independent NGO can manage volunteers, projects and cashbook safely |
| **M3** Public + alliance | `PUB-01–10`, `ALL-01–03`, `COM-01–04`, `COL-01–05`, `PWC-02–05`, `GOV-01` | Citizen participation, committee proposals and voluntary NGO commitment operate end-to-end |
| **Deferred** | `GOV-02`, `CASE-01`, `PAY-01`, `NAT-01` | No unintended MVP promise for voting, welfare cases, direct payment rails or national chapters |
## 9. Open decisions and explicit assumptions `[O]`
- Final legal/operational PWC registration and platform service/data terms, safeguarding, technical support and privacy retention policies.
- Launch targets: Android versus Android+iOS, read-only website scope, Urdu support at launch, accessibility acceptance, offline operation.
- Approved registration evidence checklist for legal organizations and eligible unregistered groups; disputed organizational leadership recovery process.
- Exact NGO fee/renewal carry-forward, overpayments/refunds, finance reversal, negative recorded balance and cashbook fiscal periods.
- Finance authorization-recovery proofs and eligible designated approvers; dual control for high-risk configuration changes.
- Published leadership visibility/consent and formal public inquiry routing, moderation and service handling.
- NGO project agreement templates, responsible parties and withdrawal/termination rules; joint-project risk acceptance.
- PWC alliance electoral bylaws, founding term start and legal compatibility; electronic elections remain deferred.
- NGO export schemas, legal retention durations, offboarding deadlines, storage/data access terms.
- Organization-specific permissions defaults, tier pricing/free tier detail, and capability differences for nonmember NGOs.
## 10. Traceability and review status
- **Screens imported from IA v1.0:** 72 IDs. Each ID, screen name, access and phase is traced to that document; detailed fields/actions/states in this draft are `[R]` unless directly selected `[S]` in foundation.
- **Governance and scope authority:** PWC Strategic & Product Foundation v1.0 draft for review; provisional user choices reflected there.
- **Approvals:** Product, governance, legal and UI design sign-offs have **not** occurred. Draft version numbers document iteration, not formal approval.
- **Next documents:** Identity/Authorization/Multi-NGO Data Model; detailed backend/API workflow contracts; UI wireframes and design tokens; M1–M3 development execution plan.
