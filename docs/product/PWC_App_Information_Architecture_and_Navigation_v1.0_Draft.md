# Pakistan Welfare Club (PWC)
## App Information Architecture & Navigation v1.0 — Draft for Review
**Date:** 22 October 2026  
**Status:** WORKING DRAFT — NOT FORMALLY APPROVED  
**Initial deployment:** Faisalabad, Punjab, Pakistan  
**Source:** PWC Strategic & Product Foundation v1.0 (draft for formal review), plus provisionally selected user decisions in the PWC planning conversation.

> **Decision labels:** **[S]** explicitly selected provisionally by the user; **[R]** recommended information architecture; **[O]** open; **[D]** deferred. Screens, names, navigation routes, and ID identifiers in this document are proposals, not approved UI designs.

## 1. Product navigation principles
1. **[S] One connected ecosystem, three experiences:** public/citizen/volunteer; independent NGO operations; PWC alliance/governance and joint project coordination. **[R]** Add a web management portal and a distinct PWC operations console while reusing one backend.
2. **[S] One person may associate with several organizations and workspaces.** No duplicate login per role. Membership, volunteering, NGO administration, PWC committee assignment, and project membership are separately authorized relationships.
3. **[S] Independent NGO data remains NGO-controlled.** PWC alliance leadership does not automatically obtain internal NGO membership, volunteer, project, or finance access.
4. **[R] Discoverability does not imply manageability.** Public/Members-only/Private item visibility is distinct from private field/file access, editing, exporting, and participant-list access.
5. **[R] Progressive disclosure:** simple public app navigation; administration revealed only where permissions exist; complex bulk workflows primarily in web.
6. **[R] Explicit organization context on every administrative screen.** All operations with write access display the active NGO / PWC / committee / project context to reduce cross-organization mistakes.
7. **[R] Use clear labels for independent projects versus PWC-led / joint projects** and for expressions of interest versus formally accepted commitments.
8. **[R] Accessible, mobile-first baseline; allow localization, including Urdu-readiness, without claiming language support at MVP until approved.**

## 2. Delivery surfaces and responsibility
| Surface | Audience | Preferred responsibilities | MVP |
|---|---|---|---|
| PWC Mobile App | Guests, citizens, volunteers, NGO members/representatives, authorized committee/project users | Discovery, personal profile, participation, notifications, routine organization/project approvals, field updates | Yes |
| NGO Management Web Portal | Verified NGO users | Bulk member/volunteer imports, memberships, dues, restricted finance, projects, reports, organization roles/settings | Yes |
| PWC Operations Web Console | Authorized PWC staff | Verification, institutional memberships, committee management, project approvals, reports, platform operational controls | Yes |
| Public website / web views | Public | Public NGO/project/event discovery and PWC information | [R] Optional MVP web read-only surfaces, not an additional distinct backend |

**[R]** A user may reach the same authorized functional object from mobile or web; the server remains the source of truth. Features appearing on multiple surfaces should not create duplicate records.

## 3. Global content and route hierarchy

```text
PWC Digital Ecosystem
├─ Public & Personal Experience
│  ├─ Home
│  ├─ Discover
│  │  ├─ NGO Directory → NGO Profile
│  │  ├─ Projects & Initiatives → Project Detail
│  │  ├─ Activities & Events → Event Detail
│  │  ├─ Volunteer Opportunities → Opportunity Detail
│  │  └─ Sectoral Committees → Committee Public Profile
│  ├─ Participate
│  │  ├─ My Applications / Registrations
│  │  ├─ Volunteer Opportunities
│  │  └─ Collaboration / Assistance Inquiry (not case management)
│  ├─ Updates (Notifications & Invitations)
│  └─ Profile
│     ├─ Personal Details & Preferences
│     ├─ My NGO Memberships
│     ├─ My Volunteering & Participation
│     ├─ My Workspaces / Switch Organization
│     └─ Security & Privacy
├─ Independent NGO Workspace [specific NGO context]
│  ├─ Overview
│  ├─ Organization Profile & Settings
│  ├─ Members
│  │  ├─ Roster, Applications, Invitations, Import, Member Detail
│  │  └─ Categories, Fees, Renewal Settings, Dues
│  ├─ Volunteers
│  │  ├─ Roster, Applications, Invitations, Import, Volunteer Detail
│  │  └─ Opportunities, Assignments, Participation
│  ├─ Activities & Events
│  ├─ Projects (Teams, Tasks, Milestones, Resources, Budgets, Updates)
│  ├─ Finance [separately scoped restricted access]
│  │  ├─ Accounts, Income, Expenses, Donations, Transfers
│  │  ├─ Pending Approvals, Adjustments/Reversals, Reports
│  │  └─ Authorization & Finance Policy
│  ├─ Collaborations (invitations, offers, commitments)
│  ├─ Announcements
│  ├─ Team & Permissions
│  ├─ Reports & Exports
│  └─ Settings / Verification / Workspace Exit
├─ PWC Alliance Workspace [PWC context]
│  ├─ Alliance Overview
│  ├─ Institutional Memberships / Representatives
│  ├─ Board / General Assembly (limited MVP records)
│  ├─ Sectoral Committees
│  │  ├─ Profile, Members, Announcements, Meetings, Proposals
│  ├─ PWC / Joint Projects
│  ├─ Collaboration Requests & NGO Commitments
│  ├─ PWC Operational Announcements
│  └─ PWC Reports
└─ Platform Operations Console [privileged technical context]
   ├─ NGO Workspace Verification & Claims
   ├─ Public Content Moderation / Support Cases
   ├─ Technical Security & Access Logs
   └─ Retention / Export / Recovery Operations
```

**[R]** Financial data and security logs are not included in broad search, public feeds, global admin summaries or generic activity notifications.

## 4. Proposed mobile app information architecture

### 4.1 Primary bottom navigation — [R]
| Tab | Purpose | Typical contents | Guest access |
|---|---|---|---|
| **Home** | Relevant entry point | Featured campaigns, nearby/current activities, NGO spotlights, personalized pending actions after sign-in | Public content |
| **Discover** | Find organizations and welfare initiatives | Unified filters; NGO directory; projects; events; opportunities; committees | Public content |
| **Participate** | Act on relevant opportunities | Volunteer applications, registrations, offers of support, inquiries, commitments where authorized | Public browsing; account for submissions |
| **Updates** | Actionable communications | Invitations, approvals, schedule changes, relevant announcements | Login required |
| **Profile** | Personal records and workspace entry | Memberships, volunteer history, workspaces, settings, privacy | Login required |

**[R]** Search may be a persistent icon/action in Home and Discover; do not add an extra bottom tab until observed usage justifies it. **[R]** Never use a bottom-tab label such as “My NGO” when a user can manage multiple NGOs; show **Workspaces** with an explicit switcher.

### 4.2 Universal top-level actions — [R]
- Sign in / create account for guests; logout and account security for users.
- Context-aware **Switch Workspace**: Personal, NGO A, NGO B, PWC Committee X, PWC Project Y, PWC Alliance (only if authorized).
- Notification inbox with actionable deep links and context-checking.
- Search and filters by sector, organization, location, opportunity type, and visibility.
- Back navigation returns users to the previous context and never silently switches active organization.

### 4.3 Navigation for different individuals — [R]
- Guest: Public Home → Discover → Public detail → Sign in only at the point of participation.
- Citizen: Home → Discover → Apply/Register/Send Inquiry → My Participation.
- NGO member: Personal tabs + organization-specific members-only content; no internal admin workspace unless authorized.
- NGO admin: Personal tabs + NGO workspace switcher; administrative routes confined to chosen NGO.
- PWC committee convener: Personal tabs + named committee workspace.
- PWC Board member: Personal tabs + PWC governance workspace under assigned Board permissions, never automatic NGO admin access.

## 5. Proposed screen inventory

**Labels:** M1/M2/M3 are implementation milestones together comprising the P0 MVP; P1/P2 are deferred. `Public` means discoverable subject to content visibility; `Signed-in` requires authentication; `Scoped` requires explicit NGO/PWC/committee/project authority.

### 5.1 Shared identity and public experience
| ID | Screen | Main actions / content | Access | Phase |
|---|---|---|---|---|
| PUB-01 | Home | Featured activities, announcements, personalized overview | Public / signed-in | M3 |
| PUB-02 | Discover Hub | Select NGOs, initiatives, events, opportunities, committees | Public | M3 |
| PUB-03 | NGO Directory | Filter by welfare sector, city, coverage, verification status | Public | M3 |
| PUB-04 | NGO Public Profile | About, sectors, approved public leadership/contacts, public activities | Public | M1/M3 |
| PUB-05 | Projects Directory & Detail | Owner type, organizer, partner NGOs, published progress, participation | Public where published | M3 |
| PUB-06 | Events & Opportunities | Lists, details, eligibility, dates, registration/apply | Public | M2/M3 |
| PUB-07 | Public Committee Profile | Sector, purpose, published updates, contact route | Public where published | M3 |
| PUB-08 | Collaboration / Assistance Inquiry | General inquiry; limited safe contact and routing | Signed-in (or controlled guest if approved) | M3 |
| PUB-09 | My Participation | Volunteer applications, event registrations, accepted assignments | Signed-in | M2/M3 |
| PUB-10 | Updates Inbox | Invitations, outcomes, reminders, announcements | Signed-in | M2/M3 |
| ID-01 | Register / Sign In | Account creation and authentication | Public | M1 |
| ID-02 | Personal Profile | Identity, basic preferences, contact controls | Signed-in | M1 |
| ID-03 | My Affiliations | NGO memberships, volunteering links, PWC project associations | Signed-in | M1/M2 |
| ID-04 | Workspaces Switcher | Select authorized personal/NGO/PWC context | Signed-in | M1 |
| ID-05 | Privacy & Security | Account security, notifications, privacy controls | Signed-in | M1 |

### 5.2 NGO onboarding and administration
| ID | Screen | Main actions / content | Access | Phase |
|---|---|---|---|---|
| ORG-01 | Search / Claim / Create NGO | Check existing NGO, start claim or new draft | Signed-in | M1 |
| ORG-02 | Provisional NGO Workspace | Draft profile, checklist, verification submission; restricted operations | Provisional owner | M1 |
| ORG-03 | NGO Verification Submission / Status | Category-specific documents, authority evidence, review status | Provisional/scoped | M1 |
| ORG-04 | NGO Overview | Pending tasks, membership totals, activities and allowed summaries | Scoped | M1/M2 |
| ORG-05 | NGO Profile Editor | Public fields and independent NGO settings | Scoped | M1 |
| ORG-06 | Team & Permissions | Invite admins, assign roles, manage revocation | Scoped | M1 |
| ORG-07 | Membership Overview / Roster | Filter and manage members; distinguish unclaimed records | Scoped | M1 |
| ORG-08 | Membership Requests & Invites | Accept/decline, invite or open-join handling | Scoped | M1 |
| ORG-09 | Member Detail | Membership state, category, validity and authorized details | Scoped | M1 |
| ORG-10 | Import Members | Upload, map columns, validate, review duplicates, import | Scoped; web preferred | M1 |
| ORG-11 | Membership Claim / Link | Verified identity + single-use token or NGO approval | Signed-in + verified process | M1 |
| ORG-12 | Member Categories / Rules | Configure open/approval/invite, fees, renewal/expiry | Scoped | M1/M2 |
| ORG-13 | Member Dues | Charges, adjustments, waivers, partial payments, receipts | Scoped; financial details separately scoped | M2 |
| ORG-14 | Volunteer Roster / Enrollment | Applications, mode settings, approved relationships | Scoped | M2 |
| ORG-15 | Import Volunteers / Claim | Manual/CSV/Excel import and secure claim process | Scoped; web preferred | M2 |
| ORG-16 | Volunteer Opportunity Manager | Post opportunity, define roles, accept participants | Scoped | M2 |
| ORG-17 | Volunteer Assignments | Confirm assignments and participation | Scoped | M2 |
| ORG-18 | NGO Activities / Events | Create, publish, register, record attendance | Scoped | M2 |
| ORG-19 | NGO Projects | List, create, set visibility, track status | Scoped | M2 |
| ORG-20 | Project Detail & Team | Authorized team and participant access | Scoped | M2 |
| ORG-21 | Project Tasks / Milestones | Assignments and delivery progress | Scoped | M2 |
| ORG-22 | Project Resources / Budget | Resource needs, planned budgets, linked actuals | Scoped; finance actuals additionally restricted | M2 |
| ORG-23 | NGO Announcements | Publish to permitted audience | Scoped | M2 |
| ORG-24 | NGO Reports / Export | Authorized operational reports/export | Scoped | M2 |
| ORG-25 | NGO Settings / Workspace Exit | Policy settings, data-export/deactivation initiation | Scoped | M1/M2 |

### 5.3 Private NGO finance (never alliance-wide by default)
| ID | Screen | Main actions / content | Access | Phase |
|---|---|---|---|---|
| FIN-01 | Finance Overview | Restricted balances, pending approvals, latest transactions | NGO finance scope | M2 |
| FIN-02 | Cash & Bank Accounts | Create/manage account registers, opening balance references | NGO finance scope | M2 |
| FIN-03 | Income / Donations | Entry, source, restricted donor fields, receipt links | NGO finance scope | M2 |
| FIN-04 | Expenses | Create/edit draft, categorize, attach evidence | NGO finance scope | M2 |
| FIN-05 | Transfers | Linked source/destination ledger entries | NGO finance scope | M2 |
| FIN-06 | Financial Approvals | Approve/reject independent entries, separation of duties | Authorized approver | M2 |
| FIN-07 | Financial Entry Detail | Posted status, approval history, correction/reversal | NGO finance scope | M2 |
| FIN-08 | Finance Reports / Export | Recorded balances, reports by account/category/period | Explicit export scope | M2 |
| FIN-09 | Finance Policy & Access | Direct/approval mode; separate finance-role authorizations and recovery | Restricted governance of finance scope | M2 |

### 5.4 Alliance, committees, collaboration and PWC operations
| ID | Screen | Main actions / content | Access | Phase |
|---|---|---|---|---|
| ALL-01 | Institutional PWC Membership | Apply, track status, select authorized representatives | NGO/PWC scoped | M3 |
| ALL-02 | Alliance Member Registry | Eligible PWC member roster and membership categories | PWC scoped / approved public summary | M3 |
| ALL-03 | PWC Dashboard | Member network, committee activity, joint initiatives | PWC scoped | M3 |
| COM-01 | Committee Directory & Profile | Sector, convener, purpose, approved roster | Public/scoped portions | M3 |
| COM-02 | Committee Workspace | Members, announcements, meetings, tasks relevant to proposals | Committee scope | M3 |
| COM-03 | Committee Meetings | Agenda, participation, notes, action items | Committee scope | M3 |
| COM-04 | Committee Proposal | Draft, submit, review status, referenced NGOs | Committee/PWC review scope | M3 |
| COL-01 | Collaboration Requests | Requests and offers, responding organizations | Public/NGO scope | M3 |
| COL-02 | Collaboration Detail | Scope, requested help, responses and authorized discussion | Request owner/participants | M3 |
| COL-03 | Proposed NGO Commitment | Declared contribution, responsible representative, approval mode | Specific NGO scope | M3 |
| COL-04 | Commitment Approvals | Single/multi-approval rules; acceptance/amendment/withdrawal | Delegated NGO approvers | M3 |
| COL-05 | Joint/PWC Project Workspace | Project lead, participating NGOs, permissions, milestones, outcomes | Project scope | M3 |
| PWC-01 | Organization Verification Queue | Authority checks, legal category evidence, duplicates | Platform verifier | M1 |
| PWC-02 | Institutional Membership Review | Approve/decline PWC membership and rights | Authorized PWC admissions staff | M3 |
| PWC-03 | Committee Administration | Activate committee, appoint conveners, scope access | PWC administration | M3 |
| PWC-04 | Joint Initiative Approval | Review proposed project, approval routing, execution scope | Delegated PWC authority | M3 |
| PWC-05 | PWC Announcements & Reporting | Official announcements, high-level project reports | PWC scoped | M3 |
| GOV-01 | Board & General Assembly Directory | Board roles, terms, representative records, published governance docs | Scoped / published summary | M3 limited |
| GOV-02 | Formal electronic elections | Nomination, ballot, tally, disputes | Eligible voters, governed by bylaws | P2 [D] |
| OPS-01 | Audit, Support and Recovery | Break-glass requests, security logs, access trace | Privileged technical operators only | M1/M2 |
| CASE-01 | Sensitive Welfare Case Intake | Triage, case files, referral and outcome controls | Specifically assigned safeguarding roles | P1/P2 [D] |
| PAY-01 | Online Donations & Payments | Payment processing, disbursement, reconciliation | Compliance-ready financial actors | P2 [D] |
| NAT-01 | Multi-chapter Operations | Chapter registration, roles, inter-chapter initiatives | Authorized chapter/national roles | P2 [D] |

## 6. Workspace navigation rules

### 6.1 Personal vs organization contexts — [R]
- Personal context is default on sign in and the only context for a citizen without organizational authority.
- An NGO workspace exists only after an appropriate relationship and permission. Name, organization ID and access state appear in the header.
- Multiple NGO relationships can be listed simultaneously, but administrative actions always occur in exactly one active NGO context.
- Committee and PWC-project workspaces are **scoped to committee/project IDs** and do not inherit unrelated NGO admin rights.
- PWC Alliance and Platform Operations contexts are separate from NGO workspaces. A Board director has no implied platform-operations privilege.
- Deep links must verify authorization afresh and show a safe “not authorized / change workspace” experience when access has changed.

### 6.2 State-sensitive navigation — [R]
| State | Available navigation | Restricted actions |
|---|---|---|
| Guest | Public directory, details, published activities | Submit application/inquiry requiring identity, private content |
| Registered individual | Personal records, applications, profiles, authorized member content | NGO administration without relationship |
| Provisional NGO owner | Draft/edit own submitted information, verification progress | Existing NGO private records, public verified claims, member import, finance posting, alliance votes |
| Verified NGO operator | NGO tools according to explicitly assigned permissions | Other NGOs' internal data, PWC privileged actions |
| PWC institutional member | Eligible alliance routes in addition to independent NGO workspace | PWC Board powers without appointment |
| Committee member | Named committee workspace | Binding NGO/project commitments unless separately delegated |
| Suspended/removed representative | Public/personal access remains subject to account policy | Previously held NGO privileged operations |

## 7. Critical end-to-end navigation flows

### F1. Citizen becomes an activity volunteer — M2/M3
`Discover → Opportunity detail → Sign in / Complete volunteer profile → Apply → Updates: application outcome → My Participation → Attendance confirmation / completion`
- An event application does not automatically create an NGO membership or standing NGO volunteer relationship.

### F2. NGO creates its management workspace — M1
`Personal Profile → Workspaces → Add / Claim NGO → Search existing → Draft provisional workspace → Category-specific organization + representative verification → Approved NGO workspace → Team & Permissions`
- Detect duplicates and disputed organization claims before privileged access is granted.

### F3. NGO enrolls an individual member — M1/M2
`NGO Workspace → Members → Settings: open/approval/invitation → Apply or invite → NGO review if applicable → Member record → Category/renewal → Dues`
- Membership and payment statuses are distinct. Administrative rights are not derived automatically from member category.

### F4. NGO imports existing people — M1/M2
`NGO Workspace → Members/Volunteers → Import → Template/Upload → Map fields → Validate/duplicate review → Confirm import → Unclaimed record → Verified personal account claim + token or approval`
- Never mass-create authenticated personal accounts from import data. Keep member/volunteer imports separate.

### F5. NGO records dues, donation or expense — M2
`NGO Workspace → Dues/Finance → Record source receipt or expense → Select NGO financial account → Direct post OR submit for separate approval → Posted record → Account/report`.
- Idempotently link financial posting to confirmed dues/donation receipt; account balances change only on authorized posting. Multi-account transfers do not create income.

### F6. NGO manages its independent welfare project — M2
`NGO Workspace → Projects → New → Visibility and scope → Assign team → Tasks/milestones/resources → Budget → Updates → Completion report`.
- Public project page reveals only published details. NGO financial actuals require finance permission even for project managers without such authority.

### F7. Committee proposal becomes a PWC joint project — M3
`Committee Workspace → Meetings → Proposal → Authorized PWC review → Approved PWC initiative → Invite NGOs → NGO commitment workflow (1 or multiple approvers) → Accepted partner contributions → Project team → Updates/closure`.
- PWC approval is not NGO consent. “Interested” is not “Committed.”

### F8. NGO exits alliance or platform — M1/M2/M3
`NGO Settings → PWC Membership → Leave alliance` (removes alliance privileges, retains independently eligible software access) **versus** `NGO Settings → Data & Workspace → Export → Deactivation request → Retention/deletion workflow`.

## 8. Role-to-workspace access matrix
| Actor | Public/Personal | Own NGO member admin | Own NGO finance | Committee | Joint Project | PWC governance | Technical ops |
|---|---|---|---|---|---|---|---|
| Guest | Public | No | No | Public portion | Public portion | Public portion | No |
| Registered citizen | Yes | No | No | By assignment | By assignment | No | No |
| NGO ordinary member | Yes | Members-only content | No | By assignment | By assignment | No | No |
| NGO member manager | Yes | Explicit member-management scope | No by default | By assignment | By assignment | No | No |
| NGO finance user | Yes | Not implied | Explicit separately granted access | By assignment | By assignment | No | No |
| NGO primary administrator | Yes | Assigned NGO admin scope | **No automatic finance access** | By assignment | By commitment delegation | No | No |
| Committee convener | Yes | No unless also NGO role | No unless also finance role | Assigned committee | Project assignment | No unless also Board role | No |
| PWC Board director | Yes | No unless separately NGO role | No unless separately NGO role | As assigned | As assigned | Defined Board scope | No |
| PWC staff | Yes | No unless separately NGO role | No by alliance role | Assigned operations | Assigned PWC project | Assigned staff scope | No by default |
| Platform technical operator | Limited public | Exceptional controlled support only | Exceptional controlled support only | Exceptional controlled support only | Exceptional controlled support only | No policy powers | Narrow logged technical scope |

## 9. Search, notifications, documents and deep links
- **[R] Search:** only indexes public data or content authorized for the current user/context. Never index independent NGO finance, private member data, or sensitive inquiries in global search.
- **[R] Notifications:** personally scoped notifications for applications, renewals, assignments, committee meetings, approvals and invitations; content previews should exclude sensitive donor or beneficiary data.
- **[R] Shared content:** organization chooses Public, Members-only or Private for eligible activities and projects; restricted underlying financial/identity fields remain protected regardless of visibility.
- **[R] Documents:** private attachments require the same object-specific authorization as their parent record; unguessable URLs alone are insufficient access control.
- **[R] Errors:** display not-found / access denied / permission revoked / pending verification distinctly without confirming secret record existence.

## 10. MVP scope and delivery sequence
| Milestone | Exit condition | Primary screens |
|---|---|---|
| **M1 — Secure Institutional Foundation** | Authorized representative can establish NGO workspace, manage members and permissions, and isolate records from other NGOs | ID-01–05, ORG-01–12, PWC-01, OPS-01 |
| **M2 — NGO Operations** | NGO can handle volunteers, independent projects, member dues, finance and reports safely | ORG-13–25, FIN-01–09, PUB-06, PUB-09 |
| **M3 — Public Participation & PWC Alliance** | Citizen can participate; NGOs can collaborate; committees submit proposals; NGOs explicitly accept joint-project obligations | PUB-01–10, ALL-01–03, COM-01–04, COL-01–05, PWC-02–05, GOV-01 |

The M1/M2/M3 milestones together form the selected **P0 initial-release scope**. A narrower launch can be proposed separately, but should not silently remove user-selected capabilities.

## 11. Nonfunctional and security acceptance rules
1. Backend permission checks are authoritative; hidden UI elements do not confer security.
2. Tenant/organization scoped queries prevent cross-NGO access; test all CRUD, search, exports, file downloads and background notifications.
3. Finance approval and transaction posting are atomic, idempotent, and auditable.
4. A person may have multiple NGO, PWC, committee and project relationships with distinct grants.
5. Provisional NGO users do not inherit real NGO records before claim/authority verification.
6. Role revocations, NGO exits and committee assignment changes invalidate privileged access appropriately.
7. Authorization of NGO joint-project commitment follows NGO-configured approver rules and records immutable evidence of acceptance/amendments.
8. Public organization profile does not expose the ordinary member roster by default; only organization-approved leadership/contacts are public.
9. Imported CSV/Excel member or volunteer rows do not create login accounts; verified claiming is required.
10. Private information must not leak through search suggestions, analytics, error details, logs, or notification previews.
11. PWC platform-owned technical access is separated from PWC alliance governance access and subject to exceptional access workflows, auditing and documented data policies.
12. Formal welfare case management, public sensitive case listings, direct payment processing, full accounting, and multi-chapter governance remain excluded from P0.

## 12. Open design decisions for formal review
| Ref | Decision | Interim IA assumption |
|---|---|---|
| IA-O1 | Whether initial mobile app is Android only or Android + iOS; web public availability | Responsive mobile-first interfaces, no store commitment assumed |
| IA-O2 | Whether PWC membership privileges enable collaboration features only for institutional members or also verified nonmembers | Show eligibility gates; alliance privileges differentiated |
| IA-O3 | Which users may submit general assistance inquiries as guests | Sign-in for inquiry until safe intake policy decided |
| IA-O4 | Exact NGO authority-verification documents for registered/unregistered groups | Separate review checklists per category |
| IA-O5 | PWC Board election tools and final constitutional office structure | Directory/basic records in MVP; election workflows deferred |
| IA-O6 | Cashbook controls for adjustments/refunds and NGO finance access recovery evidence | Restricted controls; detailed rules pending |
| IA-O7 | PWC itself as operator: privacy notices, terms, legal form, retention periods, incident and technical support procedure | Explicit policy/legal review required |
| IA-O8 | Whether PWC committee and NGO workspaces need full mobile management parity | Mobile routine actions; web bulk and complex functions |
| IA-O9 | Urdu language and accessibility acceptance level for initial launch | Design localization-ready; launch-language decision open |
| IA-O10 | Full data model, screens and navigation naming validation with users | Treat this as proposed architecture pending review |

## 13. Next artifact sequence
1. **Detailed Mobile & Web Screen Specification v1.0**: every P0 screen, fields, actions, empty/error states, permissions, acceptance criteria.
2. **Identity, Authorization & Multi-NGO Data Model Foundation**: person identity, organization workspaces, NGO/PWC membership, permissions, volunteer relationships, finance and projects.
3. **API & Backend Module Plan**: lifecycle transitions, idempotent finance posting, privacy scopes and workflow endpoints.
4. **UI/UX Wireframes and interactive prototypes** grounded in approved screens.
5. **Development Execution Plan** across M1/M2/M3 with security tests and milestones.

---
**Review note:** This document intentionally does not finalize legal registration, fund-collection compliance, Board election bylaws, data protection legal notices, operational verification policy or post-MVP beneficiary case management. It derives from the PWC Strategic & Product Foundation v1.0 draft and provides an information architecture recommendation, not a claim of formal sign-off.
