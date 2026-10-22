# Pakistan Welfare Club (PWC)
## Strategic & Product Foundation v1.0 — Draft for Formal Review
**Date:** 22 October 2026  
**Status:** WORKING DRAFT — NOT APPROVED  
**Initial geography:** Faisalabad, Punjab, Pakistan  
**Source basis:** User-selected provisional decisions and discussions in this conversation. Legal-context notes are separated and cited with official URLs.  

> **Decision semantics.** **[S] Selected provisionally** means the user explicitly chose this direction, but it is not formally approved. **[R] Recommended** means an assistant-proposed implementation or safeguard, not yet chosen. **[O] Open** means a decision still required. **[D] Deferred** means intentionally reserved for later phases. None of these statements constitutes adoption of a constitution, policy, legal status, or final software specification.

---

## 1. Executive Foundation

### 1.1 Identity, model, mission
- **[S]** PWC is a hybrid **alliance of independent welfare organizations** and **platform for voluntary joint projects**; the Faisalabad Chapter is its first operating pilot. National–chapter arrangements are deferred until lessons from the pilot are available.
- **[S]** Member organizations retain independent governance, operations, assets, people, decisions, finances and obligations. PWC does not govern their independent affairs solely because they are members.
- **[S]** PWC can convene NGOs working in education, healthcare, career development, skills and employability, women's empowerment, poverty alleviation and other social welfare sectors, and create sectoral committees as activity and demand justify.
- **[S]** PWC can initiate, approve, fund and directly manage its own welfare projects, and facilitate multi-NGO voluntary projects with separately recorded commitments.
- **[R] Vision:** Independent in identity, united in purpose, stronger in impact.
- **[R] Digital product statement:** A PWC-operated digital welfare ecosystem helping independent NGOs run their own administration, helping citizens and volunteers participate, and helping PWC coordinate voluntary collaborative impact.

### 1.2 Institutional responsibility boundaries
- **[S]** PWC has no general right to audit the internal finances of independent NGOs, and membership alone does not make PWC responsible for independent NGO activities.
- **[R]** Treat this as a governance, contract and authorization rule **subject to applicable law**, not an unconditional legal immunity. PWC remains responsible for activities it actually conducts, funds, undertakes, administers or is otherwise legally responsible for; member NGOs remain responsible for their own statutory reporting and audits.
- **[R]** For funded joint-project components, request only the reporting and evidence agreed for those funds or required by applicable law, not unrestricted access to an NGO's unrelated books.
- **[S]** Resources, existing memberships, volunteer pools and property are **not** automatically committed to PWC; every collaboration or contribution is voluntary and specifically authorized.

## 2. Provisional Governance Framework

### 2.1 Membership and representation
- **[S]** Registered NGOs and credible unregistered welfare groups may participate under differentiated categories. **Voting in PWC Board elections is reserved for eligible registered full institutional members.**
- **[S]** Individuals may participate as associates and volunteers, **without institutional voting rights**.
- **[S]** Regular Governing Board has **11 voting directors**, nominated as authorized representatives by member organizations and elected by eligible institutional members.
- **[S]** Founding Board has a **24-month provisional period**, followed by a regular elected model.
- **[S]** Funding of PWC operations combines modest membership contributions with voluntary donations, grants and sponsorships.
- **[S]** Sectoral committees are activated gradually by interested members and demonstrated need.
- **[D]** Future national–chapter powers, elections and resource arrangements await Faisalabad pilot evaluation.

### 2.2 Recommended institutional organs
1. **[R] General Assembly / Members Council:** voting member organizations appoint authorized representatives; elect Board; receive reports; approve reserved constitutional decisions.
2. **[R] Governing Board:** 11 elected directors act collectively on PWC strategy, approved policies, budget and PWC projects, not internal member-NGO affairs.
3. **[R] Executive Secretariat:** carries out authorized daily PWC operations and coordination.
4. **[R] Sectoral Committees:** education, health, career/skills/livelihoods, women's empowerment, poverty alleviation, emergency relief, etc.; committees have conveners, membership, meetings, announcements, and project proposal capability at app launch.
5. **[R] Joint Project Teams:** temporary, project-scoped teams with explicit permissions and participation agreements.

### 2.3 Unresolved governance articles
- **[O]** Founding-term start event, whether exceptional extensions are permissible and transition-election deadline.
- **[O]** Regular elected Board term (2 or 3 years, etc.), term limits and director removal/vacancy rules.
- **[O]** Whether the General Assembly elects specific offices or 11 directors who choose officeholders.
- **[O]** Maximum representation per NGO, affiliated-NGO concentration protections, nomination eligibility, election supervision, quorum, appeal process and voting disputes.
- **[O]** Formal PWC institutional admission/suspension, dues, voting qualification dates, conflict-of-interest rules and nonpartisanship implementation.
- **[O]** PWC registration/legal form, project fund controls, statutory audit requirements and bylaws. Do not finalize legal claims until checked against the chosen form.

## 3. Product Vision, Stakeholders and Delivery Surfaces

### 3.1 Four coordinated product domains
1. **[S] Independent NGO Management:** available in basic form to eligible platform organizations even when they are not formal PWC institutional members; alliance membership gives additional alliance benefits.
2. **[S] Public & Volunteer Experience:** discover NGOs, initiatives and events; register; volunteer; submit collaboration or assistance inquiries. **Formal welfare beneficiary case management is Phase 2** after proper safeguarding and operational readiness.
3. **[S] Collaboration & Project Engine:** collaboration requests, NGO offers, PWC projects and voluntary project commitments approved by authorized NGO representatives.
4. **[S] PWC Alliance & Governance:** institutional applications, member verification, committee workspaces, meetings and project proposals, Board and alliance operations.

### 3.2 Delivery surfaces
- **[R]** One mobile application for citizens, volunteers, NGO representatives and field/committee users, with permission-aware workspaces.
- **[R]** Web portal for detailed NGO administration, imports, finance, project planning and committee management; restricted PWC operations console for membership/verification and alliance governance.
- **[R]** One personal login may have multiple independent NGO memberships, volunteer relationships, roles and PWC assignments; application screens and APIs must always evaluate permissions in the correct organization/project context.

## 4. Identity and Authorization Foundation

### 4.1 Distinct primary concepts
- **User:** actual authenticated human with one personal identity.
- **Organization:** NGO/group with unique internal ID, registration classification and verified platform workspace status.
- **Organization administrator relationship:** verified authority to manage one organization's workspace.
- **NGO membership:** person belongs to a specific NGO, with category, status, renewal and dues.
- **NGO volunteer enrollment:** standing volunteer relationship, independent of NGO membership.
- **Volunteer application / assignment:** participation in a specific opportunity/activity/project, independent of both.
- **PWC institutional membership:** relationship between an NGO and the alliance, with category, voting eligibility and status.
- **PWC role/committee membership:** PWC-specific administrative or committee authority, not powers over NGO internal affairs.
- **Project commitment:** agreement by an authorized NGO representative under that NGO's internal approval policy.

### 4.2 Three administrative authority domains
- **Platform Operations:** PWC's technical responsibilities, security, verification support and lawful operations; privileged support access must be justified, time-limited where possible and audited.
- **Alliance Operations:** PWC institutional membership, committees, governance and PWC-owned funds/projects.
- **Organization Operations:** each NGO's private member roster, volunteer database, internal projects, records, roles and finance.

**[R] Security invariant:** no alliance-level permission grants read or export access to unrelated private NGO data; no NGO admin can access another NGO; all privacy controls enforced at the API, query, file and export levels (not only by hidden navigation).

## 5. NGO Onboarding and Verification

### 5.1 Workflow
**[S]** A representative may create a **limited provisional NGO workspace** prior to full verification. Sensitive and public-facing capabilities unlock only after applicable verification.

**[R]** Steps: create draft or claim request → deduplicate against existing organizations → provisional profile → upload category-appropriate evidence → verify organizational legitimacy/eligibility and representative's authority separately → activate appropriate NGO-admin workspace → optionally apply for separate PWC institutional membership.

### 5.2 Registered / unregistered verification
**[S]** Separate evidence requirements for formally registered and eligible unregistered groups. **[R]** Show distinct badges for registration status, platform authority verified and PWC institutional membership. Neither platform approval nor PWC membership represents an audit or unconditional guarantee.

**[R]** Provisional workspace should not expose an existing NGO's records, allow mass-import of people, grant financial administration or accept joint-project commitments as an organization before the required verification is completed. Availability of unregistered groups' operational functions and fundraising must conform to applicable law.

## 6. Independent NGO Membership Management

### 6.1 Policies and records
- **[S]** Each NGO configures **Open**, **Approval Required** or **Invitation Only** membership.
- **[S]** Members can be invited by an admin or apply themselves where the organization's settings allow it.
- **[S]** Organization-configurable membership categories, category-level fees and renewal periods.
- **[S]** Dues features include **waivers, discounts, partial payments and exemptions** with manually recorded payments.
- **[S]** NGO-specific reminders, grace periods and automatic/manual expiry rules.
- **[S]** Existing members without app accounts can be entered manually or imported by CSV/Excel; accounts are not automatically created for them.
- **[S]** Secure claims require verified personal identity plus a controlled claim token or authorized NGO approval where needed.
- **[S]** Ordinary member identities are not shown on public NGO pages. Only NGO-approved leaders and contact details are public.

### 6.2 Recommended separation
- **[R]** Membership *status*, renewal *status*, and dues/payment *status* are independent; unpaid dues need not imply immediate loss of membership.
- **[R]** Keep each assessment, adjustment, allocation, receipt and renewal period auditable; no silent deletion or double charging.
- **[R]** Import preview/deduplication, claim-token expiry/single-use, safe matching and history preservation.
- **[R]** Organization-defined member category does not automatically confer platform permissions.

## 7. NGO Volunteer System

- **[S]** Open, approval-required and invitation-only standing volunteer enrollment, configurable by NGO.
- **[S]** Existing volunteers can be manually added/imported by CSV/Excel as unclaimed records and securely linked later.
- **[S]** Volunteering is not automatically formal NGO membership.
- **[R] MVP:** skills/interests, basic availability, standing roster, public/eligible opportunities, opportunity applications, approval and assignment, participation confirmation, notifications.
- **[R]** A single activity application is not necessarily an ongoing NGO volunteer affiliation. Sensitive activities can require additional screening/approval even when standing enrollment is open.
- **[D]** Advanced shift management, automated dispatch, certificates and AI matching.

## 8. Independent NGO Administration and Projects

### 8.1 Team and roles
- **[S]** Each NGO configures administrative roles and restricted finance access separately. Leadership titles do not by themselves confer technical permissions.
- **[R] Roles:** primary administrator, membership manager, volunteer coordinator, project manager, communications manager, finance recorder, finance approver, restricted reviewer.
- **[R]** Account recovery and primary-admin transfer require proof of organizational authority and audit trail, not unilateral PWC intervention in an internal NGO dispute.

### 8.2 Projects and activities
- **[S]** NGO projects in MVP support **teams, tasks, milestones, resource requirements and basic budgets**, with objectives, ownership, status and updates.
- **[S]** Eligible activities and projects support **Public, Members Only and Private** visibility. This is content visibility, not authorization to see sensitive fields or edit.
- **[R]** Budget estimates separate from actual NGO finance transactions. Financial actuals can link by project only within the proper NGO finance permission context.
- **[R]** Events support publication, registration, assignments, attendance and organizer-controlled updates; NGO can publish an activity without making private registrants public.
- **[R]** Basic announcements, internal reports and exports; advanced document/asset/inventory workflows later.

## 9. Private NGO Finance & Membership Dues

### 9.1 Selected scope
- **[S]** Private basic income, expense and donation records with no general PWC alliance access.
- **[S]** **Multiple cash/bank account registers** with manual entries and account-level summaries.
- **[S]** Each NGO chooses **Direct Entry** or **Approval Required** posting. A small NGO may select Direct Entry if it cannot supply an independent approver.
- **[S]** NGO configures acceptable finance access authorization and a verified recovery procedure.
- **[S]** **Confirmed membership-dues and donation receipts generate linked financial entries** in the selected NGO account.

### 9.2 Recommended posting rules
1. Source receipt and finance posting have a unique one-to-one or otherwise explicitly modeled deduplicated relationship; retries cannot double post.
2. In approval-required mode, a receipt may be confirmed at source while the finance posting remains pending; only approved/postable entries affect finalized recorded balances.
3. Transfers between the same NGO's cash/bank accounts move balances but are not income or expense.
4. Posted finance entries retain audit history; corrections use reversals/controlled adjustments.
5. Restricted donor details and finance exports require separate permission grants.
6. The system labels its balances as **recorded** balances; it is not full accounting, bank verification or an audit.
7. Membership-dues assessments, waiver/discount decisions, partial payments, donation records, posted income and refunds must be explicitly reconciled in product behavior.
8. No PWC Board, alliance secretary or committee role carries implicit access to an independent NGO's financial records.

**[D]** Double-entry accounting, payroll, statutory audit automation, procurement, advanced bank reconciliation and integrated online payment collection.

## 10. PWC Alliance, Committees and Joint Collaboration

### 10.1 Alliance membership
**[S]** An NGO's software usage does not automatically make it a PWC member. Alliance applications, registered-voting-class eligibility, elected representation, renewal/status and PWC-specific rights are separate processes.

### 10.2 Committee launch scope
**[S]** Profiles, members, announcements, meetings and project proposals in initial launch. **[R]** Committee proposals route to authorized PWC review; this does not commit any member NGO or grant the committee authority over their independent work.

### 10.3 Collaboration and commitments
- **[S]** Only explicitly authorized NGO representatives can accept a joint-project commitment, under NGO policy requiring **one representative or multiple internal approvals**.
- **[R]** Collaboration lifecycle: request/invitation → expression of interest → scoped proposal → organization-specific internal approvals → recorded commitment → execution → change/withdrawal under agreement → closure.
- **[R]** Commitments should record who approved, resources, financial obligations if any, dates, deliverables and amendment history.
- **[R]** Each project is labeled independent NGO / PWC-led / joint consortium, with a clear legal/operational lead and reporting boundaries.

## 11. Public & Citizen Experience

**[S] MVP:** browse public NGO profiles, campaigns, events and initiatives; sign up; create volunteer profile; apply to volunteer; submit collaboration and basic assistance inquiries.

**[R]** Keep basic assistance inquiries distinct from formal beneficiary case files; collect minimum necessary data and route to a restricted, monitored intake queue. Do not expose sensitive medical, financial or child information publicly.

**[D] Phase 2:** formal confidential beneficiary case management, safeguarding and referrals once accountable case-handling teams, retention, consent and escalation policies exist.

## 12. UX, Screens and Workspaces

### 12.1 Mobile tabs (recommended)
- Home: personalized news, activities and commitments.
- Discover: NGOs, projects, causes and events.
- Initiatives: volunteering, collaboration and participation.
- Updates: invitations, notices and status changes.
- Profile: personal identity, affiliations, participation and contextual workspace entry.

### 12.2 Independent NGO workspace (recommended)
Dashboard; Profile & Settings; Members; Dues & Renewals; Volunteers; Team & Permissions; Activities/Events; Projects; Finance; Announcements; Reports/Exports; Collaboration.

### 12.3 PWC workspace (recommended)
Institutional Membership; Verification; Board & Governance; Sectoral Committees; PWC Projects; Joint Commitments; Announcements; PWC Finance; Analytics; Restricted Operations.

## 13. MVP Prioritization and Release Structure

### M1 — Secure Institutional Foundation [P0]
Personal identity; NGO profile creation, provisional workspace, duplicate detection, verification; role authorization; PWC institutional application separation; member categories and enrollment; CSV/Excel member import and secure claiming; public NGO directory and basic individual profile.

**Exit test:** Organization can safely manage members; a user with access to NGO A cannot read NGO B's private records through API, file URLs or exports.

### M2 — Independent NGO Operations [P0]
Standing volunteers and import, events, volunteer applications, independent NGO projects with teams/tasks/milestones/resources/budgets; dues and renewals; basic multi-account financial records and configured approvals; linked donation/dues posting; NGO announcements and basic reports.

**Exit test:** One NGO completes membership/dues, volunteer/event, project and finance workflows with correct approval and recorded-balance behavior.

### M3 — Alliance Collaboration & Public Participation [P0]
Public discovery and inquiries; NGO collaboration requests/offers; explicit project commitments with one/multi-approver NGO policy; PWC-led and joint initiatives; committee profiles, membership, meetings, announcements and proposals; PWC operational approval tools.

**Exit test:** A public participant can volunteer; two independent NGOs can knowingly accept a shared initiative without PWC acquiring their internal administrative authority.

### Post-MVP [P1/P2, deferred]
Formal welfare case management, specialized safeguarding workflows, advanced NGO governance minutes, resources marketplace, restricted direct donation payments, advanced project finance and donor CRM, verified volunteer passports, AI-assisted matching and future nationwide chapter system.

**[R] Scope warning:** This is an ambitious MVP. Keep workflows complete but deliberately simple; support desktop/web for bulk finance/import/planning tasks, mobile for discovery, participation and routine administration.

## 14. Nonfunctional Requirements and Acceptance Guardrails

- **[R] Isolation:** organization- and project-scoped authorization at all endpoints, exports, files, search indexes, notifications and analytics.
- **[R] Auditability:** record creator, organization, approvals, time, changes, reversal and administrative role change history.
- **[R] Data trust:** identity claims and imported records do not become authenticated or accepted automatically on phone/name similarity alone.
- **[R] Finance integrity:** transactional/idempotent posting, correct transfer math and secure correction; no PWC aggregate private NGO finance dashboard.
- **[R] Privacy:** beneficiary and donor data minimized; authorization, encryption, backups, secure recovery, account takeover protection and breach response defined.
- **[R] Data portability:** export of eligible NGO records, workspace deactivation and policy-based retention or lawful deletion; leaving the alliance does not delete the NGO platform tenant.
- **[R] User experience:** Urdu and English readiness; clear separation of personal, NGO and PWC contexts; low-bandwidth considerations for Pakistani users.
- **[R] Governance safety:** only verified/authorized NGO signatories may commit resources; PWC approvals do not bind member NGOs automatically.

## 15. Formal Review: Decision Register

### 15.1 Key user-selected provisional decisions [S]
1. Hybrid alliance + project platform; independent NGOs; Faisalabad pilot.
2. PWC may directly operate approved projects and manage its own project funds.
3. No general auditing authority over independent NGO finances; no automatic responsibility for their independent acts.
4. Inclusive registered and eligible unregistered participants, differentiated membership; only eligible registered full PWC institutional members vote.
5. 11 elected Board directors nominated by member NGOs, following a 24-month founding Board period.
6. Individual associates/volunteers have no institutional vote; modest member contributions plus donations/grants/sponsorship.
7. Gradual sectoral committees; national-chapter model deferred.
8. Balanced public, volunteer, NGO and alliance product; formal welfare case management deferred to Phase 2.
9. All eligible NGOs may access basic management; PWC members gain additional alliance benefits.
10. NGO open/approval/invitation membership; admin invitation and self-application; flexible categories, fees, renewals, waivers, partial payments and exemptions.
11. Members private; approved leadership/contact information public; CSV/Excel/manual member import and secure claiming.
12. Separate NGO membership and volunteering; volunteer enrollment modes and existing volunteer import.
13. NGO projects have teams, tasks, milestones, resource requirements and budgets; Public/Members Only/Private visibility.
14. Private multi-account NGO income/expense/donation recording with NGO-configurable Direct Entry or Approval Required mode, linked confirmed dues/donation receipts and separated finance access.
15. NGO representatives receive provisional workspace before verification; registered/unregistered evidence is tiered.
16. NGO participation commitment uses one or multiple internal approvers as chosen by the NGO.
17. PWC directly owns and operates the platform; finance authorization recovery configurable by NGO, with verified recovery.
18. Authorized data export, platform deactivation and policy-based retention/deletion.

### 15.2 Important recommendations pending selection [R]
- One vote per eligible voting NGO; no automatic extra vote for size/contribution.
- Founding Board safeguards and mandatory election timetable.
- Organization ownership verification separate from legal-status verification and PWC membership.
- Clear legal/project owner labels, dedicated project agreements and fund-custody accountability.
- Technical support break-glass access with recorded justification and independent logging.
- Distinct finance source/payment/approval/posting statuses and immutable transaction history.
- Mobile plus web portal/operations console, shared identity and isolated tenant scopes.
- Explicit privacy and safeguarding policy prior to confidential welfare case management.

### 15.3 Material decisions still open [O]
**Legal and institutional:** PWC legal registration form; draft charter and legal capacity to own software/hold funds; verified constitution; charity/fundraising compliance; institutional-voting legal compatibility; Board term, elections and office allocation; founding term start date; specific committee and project authorization thresholds.

**Platform governance:** PWC-as-operator service agreement and NGO data-processing terms; whether the platform is offered free/per-tier long-term; technical administrator appointment; privacy/support break-glass governance; data portability/retention schedules; breach response accountability.

**Organization verification:** Accepted evidence by registration category; authority verification for contested leadership; unregistered group capability limits; appeal processes.

**Financial:** Approved finance recovery modes and fallback; roles that may approve waivers/finance configuration changes; receipt allocation/refunds; account-opening balances; post-approval change policies; financial currency and fiscal-year settings.

**Project/collaboration:** Single vs multiple NGO internal approval configuration; project agreement requirements and cancellation/withdrawal; who accepts liability for joint deliverables; project budget-sharing granularity.

**Public inquiries:** Intake owner, response standards, moderation, emergency messaging and boundaries before Phase 2.

**MVP delivery:** first-wave NGO cohort and number of platform users; mobile/web allocations; infrastructure budget, testing and launch governance; offline support scope.

## 16. Recommended Formal Review and Sign-off Sequence

**Gate A — Institutional and Legal:** decide lawful PWC form; confirm board/membership/election compatibility; determine permitted fundraising/project and platform activities.

**Gate B — Trust & Data:** approve NGO autonomy/data-access policy, service agreement, verification policies, role authorization/recovery and finance design invariants.

**Gate C — Product MVP:** confirm P0 screens/workflows, acceptance criteria, launch pilot organizations and explicitly deferred features.

**Gate D — Execution:** produce detailed architecture, database/permission schemas, API contracts, Flutter/web screen specs, QA plan and milestone implementation tickets.

**Formal approval status:** None of the above is formally approved yet; do not treat this draft as PWC constitution, legal advice or finalized development scope.

## Appendix A — Official Legal Context (for verification, not an adopted legal model)

- SECP Section 42 licensing explanation: https://www.secp.gov.pk/licensing/section-42-companies/
- SECP updated Section 42 guidebook: https://www.secp.gov.pk/document/section-42-guidebook-english-and-urdu/
- Punjab Social Welfare Department on NGO registration and oversight: https://swd.punjab.gov.pk/ngos_registration
- Punjab Voluntary Social Welfare Agencies (Registration and Control) Ordinance, 1961: https://swd.punjab.gov.pk/system/files/Voluntary%20Social%20Welfare%20Agencies%20%28Registration%20%26%20Control%29%20Ordinance%201961.pdf

The chosen registration framework may impose requirements that affect financial reporting, Board composition, election procedures, oversight and operation of the software. The autonomy principle is a limit on PWC's contractual/organizational authority, not a waiver of lawfully required disclosure to regulators or other legally entitled parties.
