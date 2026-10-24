# ADR-0003 — Web frontend architecture and technology

**Status: PROPOSED — NOT APPROVED**  
**Task:** PWC-02D; P1 architecture/design only  
**Date:** 24 October 2026  
**Baseline:** `main` at `cb4ae6c7c1b7f08bd8b6c4a5b5a0a304f1276445`, including merged PRs #3 and #4  
**Decision sought:** React + TypeScript + Vite for the NGO administration portal and separately deployed PWC operations console, subject to the gates below.

> This document authorizes no implementation, deployment, feature activation, NGO authority, or privileged command. All choices here are recommendations pending human acceptance. Existing approved authentication and authorization ADRs take precedence. Source product documents retain their selected/provisional/open/deferred statuses and canonical screen identifiers. Engineering slices do not reduce M1–M3 P0 scope or constitute independent public releases.

## 1. Repository assessment and authoritative inputs

Read against the actual merged repository, not only its older scaffold descriptions:

- [AGENTS](../../AGENTS.md), [repository README](../../README.md), [repository ADR](ADR-0001-repository.md), [open decisions](OPEN-DECISIONS.md), and [local setup](../runbooks/LOCAL-SETUP.md).
- [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md): PWC-02D blocks web implementation; PWC-03C contracts and later trust/business slices remain separate work.
- [Strategic/Product Foundation](../product/PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md), [IA/navigation](../product/PWC_App_Information_Architecture_and_Navigation_v1.0_Draft.md), [detailed screens](../product/PWC_Detailed_Mobile_and_Web_Screen_Specification_v1.0_Draft_for_Review.md), and [Flutter architecture](../product/PWC_Flutter_Frontend_Architecture_v1.0_Draft.md). Mobile Flutter remains its own recommendation; administrative web technology was open. Illustrated Flutter API shapes are not implemented contracts.
- Approved [authentication ADR](ADR-0001-authentication-and-recovery.md) and [multi-NGO authorization ADR](ADR-0002-multi-ngo-authorization-and-tenant-isolation.md).
- [Authentication integration review](../reviews/PWC-03A-AUTHENTICATION-INTEGRATION-REVIEW.md), [registration](../runbooks/PWC-03A2-REGISTRATION.md), [sessions](../runbooks/PWC-03A3-SESSIONS.md), [MFA/assurance](../runbooks/PWC-03A4-MFA-ASSURANCE.md), [authorization kernel](../runbooks/PWC-03B1-AUTHORIZATION-KERNEL.md), [context enforcement](../runbooks/PWC-03B2-CONTEXT-ENFORCEMENT.md), [authorization foundation review](../reviews/PWC-03B-AUTHORIZATION-FOUNDATION-REVIEW.md), and [privileged-command decision register](../reviews/PWC-03B3-PRIVILEGED-GRANT-DECISION-REGISTER.md).
- [API contract package](../../packages/api-contracts/README.md), its auth/session, MFA and NGO-context fixtures; actual [auth routes](../../apps/backend/accounts/registration_urls.py), [root routes](../../apps/backend/config/urls.py), [public organization projection](../../apps/backend/organizations/views.py), and [authorization routes](../../apps/backend/access/urls.py).

### Observed readiness

| Area | Repository reality | Implication |
|---|---|---|
| Frontend | `apps/ngo-web`, `apps/pwc-ops`, `apps/mobile` and `packages/design-tokens` are reserved scaffolds, not working clients | No existing web implementation to preserve or migrate; no framework installed by this decision |
| Backend | Django/DRF/PostgreSQL; merged account security and default-off synthetic authorization foundation | Do not equate scaffold role fields with production grants |
| Contracts | Three checked JSON fixture sets, not generated OpenAPI or a published TypeScript SDK; registration/reset lack equivalent JSON fixtures | Narrow verified adapters first; PWC-03C must establish schema/versioning before broader generation |
| Public NGO reads | GET `/api/v1/organizations/` and `/api/v1/organizations/{uuid}/`; verified-workspace projection of `id`, `name`, `city`, `classification` only | Partial PUB-03/PUB-04 coverage, not full directory/search/profile publishing or workspace access |
| Personal security | Registration/reset, web sessions, session management, MFA and assurance routes exist behind operational gates | Candidate integration scope, not a production-ready browser deployment or all ID screens |
| NGO authorization | Four read-only synthetic context endpoints; independent default-off flags and isolated synthetic database/principal/batch/live-grant requirements | Not production ID-04 discovery or a real NGO dashboard/settings API |
| Business domains | No implemented onboarding, membership, volunteer, event, project, finance, alliance, committee, commitment or privileged support API workflows | Keep business routes unregistered until their backend contracts and policies are approved |

PR #3 (authentication) and PR #4 (authorization foundation/review) were verified merged before drafting. This ADR does not alter their code, approved decisions, IDs or migration history. No new backend/browser tests are claimed here; the validation for this task is document integrity and scope checking.

## 2. Options, comparison and proposed technology decision

Compare the **two private administrative surfaces**, not a public SEO website. Ratings below are qualitative engineering judgments, not measured benchmarks, price quotes or claims about the latest library versions.

| Criterion | React + TypeScript + Vite | Next.js + TypeScript | Flutter Web |
|---|---|---|---|
| DRF integration/contracts | Direct typed fetch adapters and eventual OpenAPI client; existing cookie/CSRF model remains explicit | Equally capable as a browser client; server fetch/actions introduce another credential/cache boundary | HTTP integration possible; requires separate Dart contracts/adapters and browser cookie/CSRF validation |
| Web security/maintenance | Static frontend plus backend authority; no extra application server or token mediator required; XSS/dependency risk remains | Secure when deliberately configured, but server/client boundaries, request caching and cookie forwarding need additional policy/tests | Does not remove XSS, session or CSRF obligations; web transport differs from native token mode |
| Admin forms/tables/reports/files | Native DOM, mature typed form/table tooling, semantic HTML and browser file APIs fit dense desktop work | Same React strengths; SSR is not necessary for authenticated grids/forms | Feasible, but dense data entry, browser semantics and accessible tables require specific web validation rather than assuming mobile widgets suffice |
| Urdu/English/RTL/a11y | Semantic DOM and direction-aware primitives offer a strong starting point; translation/keyboard/screen-reader testing still required | Same DOM advantages; SSR adds locale/hydration considerations | Localization/direction support exists; actual web semantics, assistive technology and Urdu font behavior need representative acceptance testing |
| Responsive/low bandwidth | Route splitting and small shared primitives; ordinary responsive HTML | Good browser UI, with optional SSR; benefit depends on a demonstrated requirement | Responsive layouts possible; assess initial download/startup, text rendering and low-end devices rather than promise equivalence |
| Hosting/cost | Static artifacts plus existing API/TLS infrastructure; simplest proposed runtime, not a guarantee of lowest total cost | Static export is possible for an appropriate subset; using server features adds runtime, patching and operations | Static hosting possible; asset/download and web QA costs must be measured |
| Flutter sharing | Share schema, fixtures, semantic tokens, product rules and test scenarios; not Dart widgets | Same limitation as React/Vite | Can share Dart models/widgets with mobile, but platform-specific storage, navigation, input and accessibility reduce literal reuse |
| Agent implementation/extensibility | Explicit route/module boundaries, one browser language and contract tests support small reviewable Arena/Codex slices | Productive ecosystem but more server/client and rendering choices for agents to get wrong | Productive if the team has strong Flutter-web expertise; do not optimize only for generated UI or nominal single-codebase claims |

**Recommend React + TypeScript + Vite for both apps.** These workflows benefit from native web semantics, typed DRF integration and static delivery without introducing a second server-side application tier. React does not enforce tenant security; backend contracts and negative tests do. Two bundles duplicate some assets and a TypeScript UI adds maintenance alongside Dart mobile; accept those costs instead of claiming universal code sharing.

Next.js is not rejected as insecure or incapable. Its SSR/SEO/server-component/BFF benefits do not currently justify the additional boundary for private administration; static-export Next.js is viable but offers no demonstrated requirement advantage here. Reconsider for a separately scoped public publishing/SEO product or an accepted server-rendering need, through another ADR, not a silent conversion of these portals.

Flutter Web is viable if a representative admin/accessibility spike later disproves this assessment, but the mobile recommendation alone is insufficient evidence. Do not change the mobile technology decision. Do not add a fourth framework without a concrete unmet requirement.

### Proposed implementation stack, subject to acceptance and version verification

- React, TypeScript strict mode, Vite and React Router; client-rendered routing, no SSR/BFF in the foundation.
- TanStack Query for server state; React Hook Form + Zod for client validation (server validation stays authoritative); i18next/react-i18next for messages and locale.
- Semantic HTML/CSS and a small audited wrapper layer around React Aria Components for complex accessible controls; TanStack Table only where needed, with explicitly implemented semantic tables and keyboard behavior. Neither library makes a custom grid automatically accessible. Avoid two competing component suites or a homegrown complex widget framework.
- Vitest, Testing Library, MSW for contract-faithful synthetic test responses, Playwright and axe-based checks plus manual accessibility testing.
- Recommend npm workspaces, one root lockfile, supported Node LTS and pinned dependency/toolchain versions checked when implementation is authorized. Use `npm ci` in CI; no Nx/Turborepo or microfrontend runtime initially. Confirm compatibility, maintenance/security history and licenses before freezing exact versions. Nothing is installed or generated by this ADR.

## 3. Application topology and boundaries

Two independent entry points/builds/deployments, with shared **source packages**, not one runtime with a privileged UI toggle:

```text
apps/ngo-web     NGO administration shell + its authorized feature modules
apps/pwc-ops     restricted platform/alliance operations shell + its modules
packages/design-tokens   semantic token source (existing reserved package)
packages/web-ui          proposed presentational/accessibility primitives
packages/web-api         proposed transport, schemas and normalization helpers
packages/web-i18n        proposed shared messages/locale utilities
packages/api-contracts   existing fixtures; future reviewed schemas/generation
apps/mobile             remains separate; consumes compatible contracts/tokens
```

These are proposed responsibilities, not instructions to create folders now. Apps own navigation, route loaders, permission composition, feature-specific API adapters and forms. Shared packages must not import app modules or infer roles/business policy. Share code factories, never a singleton QueryClient, session store or active NGO across apps. Do not put finance or privileged command logic into a universal `AdminService`.

Proposed deployment shape (hostnames remain unselected):

```text
HTTPS NGO origin -> NGO static assets + same-origin /api/v1/* -> Django
HTTPS OPS origin -> OPS static assets + same-origin /api/v1/* -> Django
                                  one identity/backend, no second user store
```

Each host has its own host-only session cookie, CSRF bootstrap and portal-bound session registry. Use exact configured HTTPS origins, not subdomain wildcards. Signing in to NGO web does not transfer a cookie/token to operations. A person may use both portals with separate sessions and the same personal identity. No implicit SSO bridge, shared cookie Domain, cross-origin bearer handoff or session-bearing URL. Portal separation is origin/session/UX isolation, **not** an independent backend grant: an operations session/Board title never confers NGO-private authority. Backend authorization remains necessary even if someone calls an endpoint outside its intended UI.

Shared package changes require both builds/test suites. Keep independently roll-backable artifacts and app labels; a token/UI change must not silently widen navigation or permissions in either app.

## 4. Authentication integration and deployment compatibility

### Approved transport; no new auth protocol

All web requests use relative `/api/v1/...` URLs and `credentials: "same-origin"`. Browser code never sets an Authorization header or calls mobile login/refresh endpoints. The session cookie is `__Host-pwc_session`, Secure, HttpOnly, host-only, Path `/`, SameSite=Lax under the current contract. Do not copy cookies, bearer/refresh credentials, passwords, recovery codes or proofs into localStorage, sessionStorage, IndexedDB, application URLs, logs, analytics or persisted query caches.

CSRF is separate from session authority: obtain JSON `{csrf_token}` from GET `/api/v1/auth/csrf/`, keep the token in memory and attach the prescribed `X-CSRFToken` header to unsafe browser requests. Secure CSRF cookie handling remains backend-owned. Send the browser's real same-origin Origin/Referer behavior, not invented forwarding or origin headers. Public registration/reset/login mutations also require their approved CSRF and HTTPS protections. Reject mixed modes, rather than retrying with bearer credentials.

### Bootstrap and account-security flow

1. Start in an indeterminate auth state with no private render. Bootstrap CSRF and GET `/api/v1/auth/me/`; resolve to signed out, signed in, recovery hold, unavailable or error. `me/` provides identity/session state, not a universal NGO/operations capability.
2. Explicit POST `web/login/` with CSRF: 200 establishes the cookie session; 202 `mfa_required` is **preauthentication**, not an authenticated user. Complete `web/mfa/confirm/` using ephemeral challenge/control data, then bootstrap fresh CSRF and `me/`. Do not route a 202 directly into a workspace.
3. Registration request/resend/confirm and password-reset request/resend/confirm follow their exact generic responses, expiry/replay/error handling and explicit confirmation contracts. Registration confirmation creates no session; password reset does not auto-login. Honor throttles without exposing account existence.
4. Delivery currently emits `/account/confirm#...` with `flow_id`, `proof`, `purpose`. Preserve this link destination when defining frontend routing; validate purpose, capture proof in memory, immediately scrub the fragment via history replacement and render an explicit confirmation form. Never mutate on link GET, preload or preview; do not migrate proofs to query strings. Link-origin/portal ownership and real delivery acceptance remain deployment gates, not guessed dual-portal links.
5. ID-05 may integrate only implemented personal session/MFA/assurance operations using the exact wire contracts and assurance-intent bindings. No enabled password/contact-change API exists. Step-up is not permission acquisition; no generic privileged-operation button is justified by its existence.
6. Successful browser step-up or hold clearance rotates the cookie **and CSRF** while retaining the logical session/proof binding. Invalidate old CSRF state and re-bootstrap before another unsafe request; serialize security mutations to avoid rotation races. Recovery-hold clearance needs the approved fresh single-use captured pre-hold TOTP, not merely recent assurance. Render hold/expiry/invalid-proof states without a workaround.
7. Personal session list/revoke, logout and logout-all follow existing methods/statuses. Clear UI caches immediately on logout initiation; if server logout fails, do not claim the cookie was revoked—show a safe retry state. On 401/session invalidation, abort requests, purge private state and return to sign-in. On logout-all, other origins learn revocation through subsequent backend checks, not cross-origin browser broadcasts.

Transient passwords, preauth controls, intent proofs, enrollment material and one-time recovery-code displays stay outside normal form/query telemetry and are cleared on completion/cancel/navigation/expiry. Recovery-code display/download is only the approved explicit personal-security ceremony, never ordinary app persistence. No auth polling/heartbeat: GET/status/list requests do not renew idle lifetime, and focus refresh must not manufacture keep-alive activity.

### Hard compatibility gate: direct HTTPS versus proxies

The merged backend tests **direct TLS** and rejects forwarded host/port trust or `SECURE_PROXY_SSL_HEADER` pending O3 review. The ordinary HTTP Compose/runserver setup and Arena's TLS-terminating preview proxy are **not** accepted browser-login deployments. A static CDN + HTTP API upstream, permissive CORS or blindly setting Django proxy flags is not a valid implementation of the diagram above.

Before real browser integration, deployment/security owners must approve and demonstrate either:

- an ingress/service arrangement where Django genuinely receives direct HTTPS with the exact portal Host, secure cookies and correct origin validation, without unsupported forwarding trust; or
- a separately reviewed auth deployment extension that defines trusted TLS termination, canonical host/proto/port handling, header stripping, spoof resistance, client-IP/rate-limit behavior and corresponding backend/browser regression tests.

An upstream HTTPS connection alone is not evidence if an existing proxy changes Host or relies on forbidden trust settings. Do not change approved ADRs or backend flags as part of frontend scaffolding. Same-origin behavior must be tested at **both** exact hosts, including cross-portal cookie rejection. Existing session/auth/MFA flags, secrets, delivery and operational gates remain independent. Static shell previews can use synthetic tests with a conspicuous non-production boundary; they cannot prove real auth works.

## 5. Route/module architecture and authority-aware navigation

Proposed **frontend** paths below are not new API routes, permission names or replacement screen IDs. Route registration follows API/policy readiness; this is a target structure, not permission to ship an empty business menu.

| Shell/module | Proposed route family | Context / guard |
|---|---|---|
| Both: authentication | `/sign-in`, `/register`, `/password-reset`, `/account/confirm` | Anonymous/security flow state; safe local return paths only |
| Both: personal account/security | `/account`, `/account/security` | Current personal session; only supported subsets of ID-02/ID-05 |
| NGO: authorized contexts | `/workspaces` | Future real context discovery, not synthetic production discovery |
| NGO: onboarding | `/onboarding/*` | Future create/claim/provisional contracts; no implied admin grant |
| NGO: dashboard/profile/settings/team | `/ngos/:organizationUuid/{overview,profile,settings,team}` | Explicit live NGO context and action-specific permission |
| NGO: members/dues/volunteers/events | `/ngos/:organizationUuid/{members,dues,volunteers,events}/*` | Separate domain actions; imported people are not automatically users |
| NGO: projects/announcements/reports | `/ngos/:organizationUuid/{projects,announcements,reports}/*` | Project ownership and data/export scope validated server-side |
| NGO: finance | `/ngos/:organizationUuid/finance/*` | Explicit finance grant; NGO administrator/project manager does not inherit it |
| NGO: alliance/collaboration | `/ngos/:organizationUuid/{alliance,collaboration}/*` | Authorized NGO representation; interest is not a binding commitment |
| Relevant NGO/OPS participation: committees/projects | `/committees/:committeeUuid/*`, context-specific project routes | Future explicit committee/project contracts; NGO discovery does not establish these scopes |
| OPS: platform verification | `/verification/*` | Future platform-verifier authority, distinct from alliance admission |
| OPS: alliance/governance/PWC projects | `/alliance/*`, `/committees/*`, `/initiatives/*`, `/governance/*`, `/announcements/*` | Future domain-specific PWC authority; no private NGO inheritance |
| OPS: restricted technical operations | `/operations/*` | Future privileged support/audit/recovery contracts and policy; not personal ID-05 |

Do not invent a production `ops.admin` or `isAdmin` claim to admit a signed-in person. Until an approved operations entry/capability contract exists, authentication may establish personal identity but cannot unlock operational tools. NGO administrative modules are not included in the operations shell. Direct links undergo the same loader checks as menu navigation. Unknown/deferred/unready routes return a safe not-found/unavailable boundary, not fabricated records or a disabled form pretending a workflow exists.

Use context-explicit breadcrumbs and persistent organization/ownership labels on every private route and dialog. Do not derive context from a user's first membership, a PWC title, a global mutable `selectedNgo`, headers, query/body overrides or a stale browser preference. Validate path parameters and object ownership on every backend request; a UUID is not authority. Preserve only safe local return paths, recheck access after login and do not redirect proofs or private state between origins.

Frontend guards/capability gates are UX only. The API must authorize every action, queryset, object, export and file; hidden navigation is never the allow/deny mechanism. PWC approval of its own initiative cannot bind NGO funds, volunteers or resources; NGO commitments need explicit authorized representation and their configured one/multiple internal approvals. NGO software usage, platform verification and PWC institutional membership remain separate.

## 6. Shared UI, localization and responsive interaction

Start with shared semantic color/spacing/type/focus/status tokens, shell/layout primitives, context header, breadcrumbs, accessible form controls, dialogs, loading/empty/error states, status/ownership/visibility badges, confirmation flows, pagination, semantic table wrappers and money/date display. Implement feature-specific approval timelines/file controls only when their contracts exist. Preserve screen IDs in route metadata and non-sensitive test identifiers for traceability.

Keep NGO and PWC identity/context visibly different without maintaining two incompatible design systems. Shared UI accepts presentation props; it does not decide grants. No client-generated role hierarchy or generic finance-enabled admin template.

- Recommend WCAG 2.2 AA as an explicit acceptance target, pending approval: semantic landmarks, skip link, route titles/focus, labeled controls, described validation, error summary, keyboard and visible focus, dialog focus restoration, live status announcements and non-color-only state.
- Recommend English/Urdu locale architecture and an early reviewed RTL specimen. Full Urdu launch coverage remains **open** in the Flutter/product foundation; this ADR does not relabel it selected. Store messages by stable keys, use CSS logical properties and `dir`, test mixed-direction identifiers/email/amounts with bidi isolation. Self-host only reviewed/licensed fonts; test Urdu shaping/readability and load cost. Do not mirror all icons or reverse numeric data indiscriminately.
- Use locale-aware date/number formatting with explicit timezone/underlying value semantics. Keep exact decimal/money values in server-specified strings/minor units; no binary-float accounting or hardcoded `Rs` data model. Backend defines currency, precision, rounding and posting rules.
- Desktop supports dense forms/tables; small screens use responsive sections and accessible horizontal table regions or task-appropriate cards, never silently drop critical columns/actions. Test 320 CSS-pixel reflow, zoom, large text and touch targets. Virtualization requires an accessible fallback and demonstrated benefit; server pagination first.
- Destructive, financial and binding-commitment actions need clear scoped confirmation and backend concurrency/idempotency contracts. Client validation improves feedback, not policy. No optimistic grant, balance, approval or commitment changes.

## 7. API client, state, context switching and error semantics

### Transport/contracts

One thin typed fetch adapter with fixed relative API prefix, JSON content-type/accept rules per endpoint, CSRF injection, AbortSignal support, status handling and normalized errors. An app supplies its own auth-generation/context state. Allow only declared endpoints/methods; do not turn a return URL into an arbitrary fetch target. Parse verified fixture-backed response shapes at the boundary; hand-written narrow types are not evidence of a generated backend contract. No catch-all schema guessing or unrestricted dictionary-to-command forwarding.

Future OpenAPI generation belongs to PWC-03C with versioning, compatibility review and contract tests. Generated clients still need web-only credential transport and response redaction. Existing fixtures are incremental slice snapshots: the session fixture includes earlier deferred assurance denials; consult the later MFA fixture, merged implementations and authentication integration review for superseding behavior. Resolve overlaps explicitly in contract tests rather than generating a contradictory SDK from all snapshots. Build fixtures must use synthetic data and match actual method/status/body behavior; MSW success mocks cannot establish an absent backend workflow.

Auth uses `code`, `message`, `field_errors`, `request_id`; synthetic authorization uses `code`, `correlation_id`. Ordinary Django/DRF errors and unregistered-route 404s are not guaranteed to share either envelope. Normalize into an internal error category plus safe support reference without assuming JSON or rendering raw response bodies. Distinguish 401, 403, non-disclosing 404, validation, conflict/stale revision, 429, unavailable and network failure. Respect retry hints where present; never auto-retry unsafe requests or CSRF failures, and do not promise idempotent commands until the backend defines keys/replay semantics.

### State ownership and anti-leakage rules

- URL: explicit context ID, non-sensitive pagination/filter state only; no search terms containing private PII or proofs. Router location state is not a secret store.
- Memory: auth lifecycle, transient CSRF, per-app QueryClient, pending security flows and local forms. No Redux/global business store, persisted private query cache, offline private mode or service-worker cache initially.
- Query keys partition by app/portal, principal, logical-session identifier where exposed, local auth generation, explicit context kind/ID, capability registry/version/revision where available, operation and parameters. Do not assume auth/session revision is the same as NGO capability revision.
- Share contracts, not session objects. Keep private data only as long as the active view needs it; remove inactive context queries and disable production query/devtools exposure of private payloads. Persist only approved non-sensitive preferences such as locale, not active grants or cached records.

**Switch protocol:** ask about unsaved edits before a voluntary switch; then close context-bound dialogs, suspend private rendering, increment a local context generation, abort old requests, remove old-context query data and clear selections/drafts. Resolve the destination from authoritative discovery, fetch its current capabilities and only then load private records. Validate the captured generation/principal/context before accepting any response, including requests whose abort arrived too late. Old results cannot populate a new workspace. A failed switch must not resurrect the old private view automatically. Revocation/expiry overrides unsaved-edit convenience.

**Permission refresh:** initial entry, context switch, return to focus/online/visibility, an advisory capability expiry and relevant action completion require backend revalidation. Suspend private rendering during required revalidation; deny/error responses purge affected state. Registry version/revision, permitted actions and earliest expiry are advisory display/cache hints, not grant tokens. No persisted capabilities, ETag/304 authorization shortcut or optimistic local role update. No periodic auth keep-alive; refresh must respect idle-expiry semantics. Concurrent requests always remain backend-authorized even while UI snapshots age.

**Invalidation:** logout, principal/session change, lost context, revocation, expiry, hold-state transitions or changed capability revision cancel pending work and purge appropriate private state. Use a same-origin BroadcastChannel carrying only a non-sensitive invalidation signal for sibling tabs; it conveys no identity, cookie, proof, grant or authorization. Other portal origins are not synchronized by this channel. Recheck with the backend rather than accepting another tab as authority. A stale background response must not reverse logout or return a previous tenant's content.

### Synthetic foundation boundary

Existing `/api/v1/me/ngo-contexts/` and `/api/v1/ngo-contexts/{organization_uuid}/{capabilities,private-probe,kernel-settings}/` support GET/HEAD synthetic verification only. Discovery accepts its declared cursor (at most 50 own contexts per page); signed cursors are not encrypted and do not promise stable snapshots. Explicit path context is the sole context input; no alternate selection/header/query/body mechanism. Every request reauthorizes and no 304 cache shortcut exists. Keep both default-off gates and isolated synthetic constraints. `kernel-settings` is not ORG-25; `private-probe` is not a roster/dashboard; the capability response is not a grant editor or real workspace API. If exercised later, isolate them in a test harness, never a production business menu or a new source of NGO authority.

## 8. Security, privacy, files and accessibility assurance

Same-origin does not eliminate XSS. React escaping is the default; avoid raw HTML injection, review any future rich-text sanitization and do not execute imported content. Recommend restrictive CSP (including frame-ancestors and connect-src), no inline/eval exceptions without review, anti-framing/content-type protections and no-referrer on account-security/proof pages. Auth/private responses remain no-store; do not cache `/api/`, proofs or private HTML in CDN/browser offline layers. Hashed public assets may be immutable. Validate response headers at actual ingress, not only component tests.

No secrets in Vite environment variables or bundles. Browser configuration contains only public non-secret settings; origin/portal/security keys remain backend/deployment-owned. No production source maps containing sensitive build configuration; use controlled artifact access for debugging. Do not inject third-party analytics/session replay into security/private workflows. Log screen ID, safe category and redacted support reference, not form values, proofs, member rosters, donor/bank details or raw server responses. Consent, retention and support access policy require separate approval.

Future upload/download/export features need approved backend authorization, ownership, storage, scanning/type/size and expiry contracts. Client accept/size hints are not security; do not expose permanent private file URLs, public storage buckets or route arbitrary storage URLs through the client. No CSV/XLSX parser/import commit or all-records export as foundation work. Future export handling must address spreadsheet formula injection, download auditing and approved retention. Private previews/blob URLs are temporary and revoked on context loss. PWC-wide analytics cannot aggregate private NGO finances by assumption.

Accessibility is a release obligation, not a framework badge. Automated checks must be combined with keyboard/screen-reader, Urdu/RTL, responsive and real task testing in §9. Public inquiry/case safeguards and finance controls cannot be inferred from generic UI components.

## 9. Testing, build, deployment and operational boundaries

Proposed future CI for both apps: pinned clean install, format/lint, strict typecheck, unit/component/contract tests, production builds, dependency/license/secret checks and Playwright smoke/security cases. Shared-package changes run both app pipelines. Keep generated assets/dependencies out of Git per existing conventions; publish versioned build artifacts, not a live dependency install at request time. Establish measured bundle/startup budgets on pilot low-bandwidth/low-end devices during foundation review; no invented performance pass thresholds here.

Required test layers:

1. Unit/contract: endpoint allowlist, typed parsing, CSRF/no-bearer transport, both error envelopes and non-JSON errors; context key separation, generation discard, decimal formatting and locale directions. Malformed data fails safely.
2. Components: all loading/empty/error/revoked/unavailable states, labeled validation, semantic table navigation, confirmation context, unsaved changes, focus restoration and no permission implied by absent/present menu items.
3. Browser, against synthetic backend fixtures in a reviewed TLS environment: register/reset explicit confirmation (no GET mutation), sign-in/MFA/hold, CSRF rotation, missing/stale CSRF, cookie attributes, expiry/logout/revoke/logout-all and no automatic unsafe replay. Include exact host/Origin and mixed-cookie/bearer/cross-portal negative cases. Mocked tests cannot substitute for real cookie/TLS acceptance.
4. Isolation/race matrix: one person with NGO A and B; only A grant; expired/revoked grant; NGO admin without finance; Board/platform role without NGO grant; unauthorized deep link; pending A response while switching to B; pending response after logout; different principal login in another tab; background/focus revalidation. Assert no stale private render as well as backend denial. Real file/export isolation waits for those APIs and is mandatory for their feature acceptance.
5. Accessibility/localization: axe checks plus keyboard-only and representative screen-reader/browser combinations (including at least one Windows and one mobile assistive-technology pairing), 200%/400% zoom, narrow viewport, English/Urdu mixed text, RTL focus/order, reduced motion, font loading and error recovery. Reviewer-approved matrix must state exact browsers/devices; test current supported Chromium/Firefox/WebKit rather than assume parity.

Build each SPA independently with history fallback for **frontend routes only**. Route `/api/` to the backend before fallback; a missing API must not become an HTML 200 page. Explicitly support `/account/confirm` without logging fragments (fragments must never be sent to the server). Serve assets/version metadata consistently, health-check the right service, and document compatible backend/client rollout and rollback. No environment may silently change origins or cookie policy at runtime.

Production/static origins, certificates, TLS termination, security headers, private storage, backup/restore, observability and support ownership require human approval. For later local static development bind Vite to `0.0.0.0` and narrowly allow the intended preview host; use relative API URLs and a reviewed same-origin proxy, never browser-facing localhost backend URLs. **That proxy configuration does not satisfy the direct-HTTPS auth gate.** Keep live auth unavailable in ordinary HTTP/TLS-terminating previews until approved; do not weaken backend checks to make a demo pass. No server is launched by this documentation task.

## 10. Canonical screen-to-module and API-readiness mapping

These identifiers refer to the detailed screen specification; grouped rows do not combine identities or change milestone/status labels. Route names above are proposals. **Implemented** below means repository endpoints exist, not enabled/approved for real deployment. **Blocked** means no matching business workflow contract, not permission to mock a production feature. Source M1/M2/M3 scope and deferred tags remain unchanged.

| Canonical screen IDs | Module / intended surface | Actual readiness and boundary |
|---|---|---|
| ID-01 | Authentication; both portals | Implemented registration/reset/web login and MFA subset; delivery, transport, real browser/storage/operations acceptance gated |
| ID-02 | Personal profile/account; both as appropriate | `auth/me/` identity/session read only; no full profile editor/preferences contract |
| ID-03 | Personal affiliations; NGO entry | Synthetic NGO-context discovery is not full memberships/volunteer/committee/project affiliations; production relationship APIs blocked |
| ID-04 | Workspace switcher; NGO plus separately scoped PWC entry | Synthetic discovery/capability reads only; real NGO and committee/project/OPS context/entry contracts blocked |
| ID-05 | Personal privacy/security; both | Implemented sessions/logout/revoke and MFA/assurance/hold subset; privacy preferences, data requests, contact/password change and closure not implied |
| ORG-01, ORG-02, ORG-03 | Search/claim/create, provisional onboarding, verification; NGO | Blocked P3 onboarding/evidence/authority APIs and PWC-02E policy; no create/claim UI command inferred from Organization model |
| ORG-04, ORG-05 | NGO overview/profile editor; NGO | Private dashboard/editor blocked; public four-field organization read does not cover these workflows |
| ORG-06 | Team and permissions; NGO | Synthetic capabilities are read-only; invitations/grant/transfer/recovery commands blocked pending contracts/policy |
| ORG-07, ORG-08, ORG-09 | Roster, requests/invites, member detail; NGO | Blocked membership CRUD/admission/PII access APIs |
| ORG-10, ORG-11, ORG-12 | Member import, claim/link, categories/rules; NGO | Blocked staged/idempotent imports, secure claim and policy APIs; imported record is not automatic authenticated identity |
| ORG-13 | Dues; NGO | Blocked assessments/renewals/linked posting APIs; not finance access inheritance |
| ORG-14, ORG-15 | Volunteer enrollment/roster, import/claim; NGO | Blocked standing-volunteer and import/claim APIs, distinct from membership |
| ORG-16, ORG-17, ORG-18 | Opportunities, assignments, activities/events; NGO | Blocked opportunity/application/assignment/attendance/event APIs |
| ORG-19, ORG-20, ORG-21, ORG-22 | Projects, detail/team, tasks/milestones, resources/planned budget; NGO | Blocked project ownership/team/planning APIs; planned budget does not authorize financial actuals |
| ORG-23, ORG-24, ORG-25 | Announcements, reports/exports, settings/exit; NGO | Blocked publishing/export/retention/settings commands; synthetic `kernel-settings` is not ORG-25; alliance exit does not delete tenant |
| FIN-01, FIN-02, FIN-03, FIN-04, FIN-05 | Finance overview/accounts/income/expenses/transfers; NGO | All blocked: finance policy, exact amounts, ledger and posting contracts; explicit finance grants only |
| FIN-06, FIN-07, FIN-08, FIN-09 | Finance approvals/detail/reports/access; NGO | All blocked: approval/reversal/export/access commands; no generic admin enablement; no PWC private-NGO finance dashboard |
| ALL-01, ALL-02, ALL-03 | Institutional membership, alliance registry, PWC dashboard; NGO application / OPS management by scope | All business APIs blocked; alliance admission, software access and platform verification are separate |
| COM-01, COM-02, COM-03, COM-04 | Committee directory/profile, workspace, meetings, proposal; authorized participant/OPS scopes | Blocked committee/membership/meeting/proposal APIs; committee role confers no NGO-internal authority |
| COL-01, COL-02, COL-03, COL-04, COL-05 | Collaboration request/detail, proposed NGO commitment, approvals, joint/PWC project; NGO/OPS by ownership | All blocked: explicit signatory, one/multi-approval, agreement and project APIs; PWC approval cannot bind NGO resources |
| PWC-01, PWC-02 | Verification queue, institutional review; OPS | Blocked evidence/review/decision contracts; verification and alliance admission must not be collapsed |
| PWC-03, PWC-04, PWC-05 | Committee administration, joint initiative approval, announcements/reporting; OPS | All blocked; limited delegated PWC scope and explicit initiative ownership, not NGO access |
| GOV-01 | Board/General Assembly directory; scoped published/governance view | Blocked approved representation/term/publication APIs; Board status not NGO authority |
| OPS-01 | Audit/support/recovery; restricted OPS | Blocked privileged access/evidence/audit contracts and decision gates; personal `auth/*` recovery is not break-glass support |
| PUB-01, PUB-02 | Home/discover; public/citizen surface, not admin-shell scope | No implemented home/discover workflow APIs; no public-site framework/SEO approval here |
| PUB-03, PUB-04 | NGO directory/public profile; public surface with relevant links from NGO web | Only existing verified organization list/detail four-field read projection; search/rich profiles/full publication contract not present |
| PUB-05, PUB-06, PUB-07, PUB-08, PUB-09, PUB-10 | Public projects/events/committees/inquiry/participation/updates; public/citizen surface | Blocked matching public/participation APIs and appropriate privacy/safeguarding controls; retain M1–M3 source scope without adding to these admin builds |
| GOV-02 | Formal electronic elections | Deferred, not a launch route; constitutional/voting approval required |
| CASE-01, PAY-01, NAT-01 | Case management, direct payment, national/chapter expansion | Deferred; no foundation routes, fake workflows or implied policy approval |

No currently implemented API authorizes a complete real NGO workspace, PWC operational workflow or private financial module. Health is liveness, not dashboard readiness. Keep test-only fixtures/harnesses visibly synthetic and out of production navigation; do not ship placeholder business screens as evidence of completion.

## 11. Phased implementation proposal after approval

| Slice | Preconditions | Bounded deliverable and exit evidence |
|---|---|---|
| W0 — decisions/contracts | Human acceptance of this ADR's relevant choices, deployment owner and API gap review | Record accepted/open items, exact supported toolchain/library versions, reviewed auth topology and contract work tickets; no business authority |
| W1 — web foundation | W0 framework/tooling acceptance | Two independent builds/shells, tokens, locale/RTL specimen, routing/error/accessibility primitives, contract adapters and synthetic test harness; no business menu/API claims |
| W2 — personal account integration | Approved HTTPS/browser topology, applicable auth operational gates, verified fixture/schema gaps closed for consumed endpoints | ID-01 and supported ID-02/ID-05 subsets in both portals; real browser cookie/CSRF/MFA/session/hold negative tests; no OPS tool entry or real NGO switcher without contracts |
| W3 — production context and M1 NGO slice | Real-context activation review, P3 backend onboarding/verification/role contracts and PWC-02E decisions | ID-03/ID-04 real subset plus ORG-01–ORG-12/ORG-25 relevant subsets and PWC-01 only as contracts land; two-NGO isolation, claim/import and revocation evidence; do not bundle all these screens in one agent ticket |
| W4 — independent NGO operations | M1 gate and appropriate P5/P6 backend contracts | Separate small volunteer/event/project/dues/finance/report slices; each requires its policy, action matrix and end-to-end negatives; no partial ledger disguised as complete finance |
| W5 — alliance/collaboration/operations | Relevant P7 policies/contracts, delegated authority and privileged-command approvals | Scoped ALL/COM/COL/PWC/GOV-01 workflows, distinct platform and alliance navigation; OPS-01 only after its independent approval |
| W6 — pilot/release | M1–M3 gates plus P8 security/legal/operations acceptance | Accessibility/localization/performance evidence, backup/restore, monitoring/support, staged pilot and human launch decision |

These W labels organize frontend engineering only and do not replace roadmap P0–P8 or product M1/M2/M3. Each implementation ticket names canonical IDs, API methods/shapes, grant matrix, state transitions, contract versions and negative tests. No automatic follow-on implementation from approval of a subset; separate authorized tasks and reviewed PRs are required. This task stops after the proposed ADR and repository checkpoint, without a PR.

## 12. Approval register, blockers and unresolved decisions

All rows remain **OPEN / NOT APPROVED by this ADR**. Review can accept the framework separately from production activation; accepted choices must be recorded explicitly, not inferred from commits.

| Gate | Decision / evidence required | Proposed accountable reviewer |
|---|---|---|
| WEB-01 | React/TS/Vite, two apps, source sharing, package/component/test strategy; pin compatible maintained versions/licenses before install | Technical/product owner |
| WEB-02 | Exact portal hosts, ingress/direct-HTTPS compatibility or separately reviewed auth O3 extension; spoof/cross-portal/CSRF live-browser tests | Backend security + deployment owner |
| WEB-03 | Auth/session/MFA/delivery operational approvals, confirmation link-origin ownership, real browser handling and rollout/rollback; do not flip default-off flags casually | Authentication/security owner |
| WEB-04 | Contract/schema/error/versioning plan (PWC-03C), missing registration/reset fixtures, supported endpoint adapters; distinguish synthetic-only gates from real workspace rollout | API/backend owner |
| WEB-05 | Production NGO context discovery/selection/capabilities and revocation; REAL01–REAL04 remain independent activation gates; no repurposing synthetic APIs | Authorization + product owner |
| WEB-06 | Operations entry and platform/alliance/NGO permission boundaries; privileged grant/support commands remain subject to GM01–GM12 and their separate approval pack | Security/governance owner |
| WEB-07 | PWC-02E evidence/authority/contested-claim policy; per-domain finance, import, files, institutional membership, signatory/commitment and support contracts before those features | Respective policy + backend owners |
| WEB-08 | WCAG target, supported browser/assistive-tech matrix, English/Urdu launch coverage, translation/font review, responsive/performance budgets | Product/accessibility owner |
| WEB-09 | Hosting/artifact/security-header/CSP/retention/logging/observability/private-file/legal and support ownership; approved runtime/toolchain maintenance plan | Operations/privacy + technical owner |
| WEB-10 | Public web/SEO delivery and PWC-owned finance scope if separately requested; deferred elections/cases/payments/national features remain deferred | Product/governance owner |

Lack of a universal production business API is an implementation blocker for affected screens, not a reason to broaden synthetic permissions. No browser route, framework choice, tenant selector, UI role badge, MFA proof or platform title can close backend policy gates. Framework acceptance alone is not launch acceptance.

## 13. Foundation acceptance criteria and task boundary

For a future **web foundation** to be accepted, reviewers must see:

- [ ] Explicit human decision on WEB-01 and a recorded accepted/open gate ledger; approved auth/authorization ADRs unchanged unless separately reviewed.
- [ ] Independent NGO and OPS production builds with shared typed primitives but no shared runtime/session/context; documented exact versions, reproducible lockfile and dependency/license/security review.
- [ ] No secrets in browser artifacts; no bearer/mobile auth, persisted private data, third-party replay or production business fixture menus. No hidden-nav-only access control.
- [ ] Traceability to all canonical IDs in §10; only implemented/approved subsets registered, with missing and deferred capabilities honestly identified. Source requirement statuses and M1–M3 P0 scope preserved.
- [ ] Contract-faithful auth/error handling and full state-machine tests; real ID-01/ID-05 integration accepted only after WEB-02/03/04. Ordinary static preview is not auth evidence.
- [ ] Proven context partitioning/clearing, in-flight generation discard, same-origin tab invalidation, permission refresh/revocation and idle-expiry behavior; no cross-NGO or cross-principal stale render. Synthetic tests are labeled and cannot activate real workspaces.
- [ ] Clear operations no-authority state until an approved OPS entry contract; NGO admin without finance and Board/platform without NGO grant remain denied backend-side.
- [ ] Accessible responsive English/Urdu/RTL specimen with manual and automated results; approved launch-language and browser matrix before claiming localization completion.
- [ ] CI type/lint/component/contract/browser/build results for both apps; measured performance and documented remaining limitations rather than invented pass claims.
- [ ] Approved ingress/cookie/CSRF/security-header acceptance, deployment/rollback and support ownership before real integration/activation. Future file/export/finance tests are independently mandatory when those modules exist.

**Acceptance of this documentation task is narrower:** create only this proposed ADR; check source references, canonical-ID coverage and diff hygiene; preserve all app/backend/approved ADR files; make a normal commit/push on the assigned fresh branch and verify remote SHA/tree/clean status. Do not install frameworks, generate frontend code, change migrations or activate flags. Do not open or merge a PR. Stop after the documented checkpoint and report unresolved approvals.
