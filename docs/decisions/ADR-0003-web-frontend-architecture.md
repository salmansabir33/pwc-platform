# ADR-0003 — Web frontend architecture and technology

**Status: APPROVED — MVP WEB TECHNICAL FOUNDATION; LIVE INTEGRATION AND DEPLOYMENT GATED**
**Task:** PWC-02D; P1 architecture/design only
**Date:** 24 October 2026
**Baseline:** `main` at `cb4ae6c7c1b7f08bd8b6c4a5b5a0a304f1276445`, including merged PRs #3 and #4
**Technical approval:** 24 October 2026, explicitly authorized by the product owner in the PWC-02D finalization instruction. React + TypeScript + Vite and the bounded W1 foundation decisions below are approved.
**Verified prior checkpoint:** `8f9223767d841212c17683e1a28812891e2461dc`.

> **Approval boundary.** This is approval of the MVP web technical foundation, not production, governance, legal, operational, real-user authentication or real NGO authority approval. React/TypeScript/Vite; separate NGO Web and PWC Operations applications, builds, routes, sessions and deployments; shared tokens, accessible components, typed API/localization utilities; the shared Django REST backend; same-origin cookie/CSRF authentication without browser bearer tokens, a separate identity provider or unnecessary BFF; explicit NGO UUID backend paths; backend-authoritative authorization; English foundation with early Urdu/RTL testing; WCAG 2.2 AA; and the prohibition on treating synthetic probes as production functionality are approved technical decisions. Implementation still needs a separately authorized task and tests. Existing approved authentication and authorization ADRs take precedence. Product requirement statuses and canonical screen IDs are unchanged; M1–M3 P0 scope is not reduced. This finalization task makes documentation changes only.

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

## 2. Options, comparison and approved technology decision

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

**Approved: React + TypeScript + Vite for both apps.** These workflows benefit from native web semantics, typed DRF integration and static delivery without introducing a second server-side application tier. React does not enforce tenant security; backend contracts and negative tests do. Two bundles duplicate some assets and a TypeScript UI adds maintenance alongside Dart mobile; accept those costs instead of claiming universal code sharing.

Next.js is not rejected as insecure or incapable. Its SSR/SEO/server-component/BFF benefits do not currently justify the additional boundary for private administration; static-export Next.js is viable but offers no demonstrated requirement advantage here. Reconsider for a separately scoped public publishing/SEO product or an accepted server-rendering need, through another ADR, not a silent conversion of these portals.

Flutter Web is viable if a representative admin/accessibility spike later disproves this assessment, but the mobile recommendation alone is insufficient evidence. Do not change the mobile technology decision. Do not add a fourth framework without a concrete unmet requirement.

### Supporting implementation stack: bounded selection and version verification

- React, TypeScript strict mode and Vite are approved. React Router is a supporting implementation recommendation; client-rendered routing, no SSR/BFF in the foundation.
- TanStack Query for server state; React Hook Form + Zod for client validation (server validation stays authoritative); i18next/react-i18next for messages and locale.
- Semantic HTML/CSS and a small audited wrapper layer around React Aria Components for complex accessible controls; TanStack Table only where needed, with explicitly implemented semantic tables and keyboard behavior. Neither library makes a custom grid automatically accessible. Avoid two competing component suites or a homegrown complex widget framework.
- Vitest, Testing Library, MSW for contract-faithful synthetic test responses, Playwright and axe-based checks plus manual accessibility testing.
- Recommend npm workspaces, one root lockfile, supported Node LTS and pinned dependency/toolchain versions checked when implementation is authorized. Use `npm ci` in CI; no Nx/Turborepo or microfrontend runtime initially. Confirm compatibility, maintenance/security history and licenses before freezing exact versions. Nothing is installed or generated by this ADR.

Approval of the framework and shared-component approach is not approval of every named library/version. Verify supporting dependencies, compatibility, licenses and maintenance in the W1 implementation review. Keep W1 small: routing, a few accessible controls, locale utilities, the typed adapter and tests. Forms/query libraries may be introduced only for demonstrated foundation needs; defer TanStack Table, advanced grids and domain-specific widgets until their feature slices. No complete PWC-03C schema generator is required to begin W1 synthetic adapter tests.

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

These are approved separation/sharing responsibilities; new shared package names are implementation recommendations, not instructions to create folders in this documentation task. Apps own navigation, route loaders, permission composition, feature-specific API adapters and forms. Shared packages must not import app modules or infer roles/business policy. Share code factories, never a singleton QueryClient, session store or active NGO across apps. Do not put finance or privileged command logic into a universal `AdminService`.

Approved logical deployment separation (hostnames remain unselected; concrete deployment acceptance remains gated):

```text
HTTPS NGO origin -> NGO static assets + same-origin /api/v1/* -> Django
HTTPS OPS origin -> OPS static assets + same-origin /api/v1/* -> Django
                                  one identity/backend, no second user store
```

Each host has its own host-only session cookie, CSRF bootstrap and portal-bound session registry. The cookie name may be the same on both hosts; cookies must not be parent-domain shared. Sibling subdomains can be same-site, so SameSite is not a substitute for CSRF and exact Origin validation. Use exact configured HTTPS origins, not subdomain wildcards. Signing in to NGO web does not transfer a cookie/token to operations. A person may use both portals with separate sessions and the same personal identity. No implicit SSO bridge, shared cookie Domain, cross-origin bearer handoff or session-bearing URL. Portal separation is origin/session/UX isolation, **not** an independent backend grant: an operations session/Board title never confers NGO-private authority. Backend authorization remains necessary even if someone calls an endpoint outside its intended UI.

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
6. Successful browser step-up or hold clearance rotates the cookie **and CSRF** while retaining the logical session/proof binding. Invalidate old CSRF state and re-bootstrap before another unsafe request; serialize security mutations to avoid rotation races. Eligible `restricted` recovery-hold clearance needs the approved fresh single-use captured pre-hold TOTP, not merely recent assurance. `review_required` is not self-clearable through this flow; lost-all-factors or review-required recovery must not acquire a workaround. Render hold/expiry/invalid-proof states without a workaround.
7. Personal session list/revoke, logout and logout-all follow existing methods/statuses. Clear UI caches immediately on logout initiation; if server logout fails, do not claim the cookie was revoked—show a safe retry state. On 401/session invalidation, abort requests, purge private state and return to sign-in. On logout-all, other origins learn revocation through subsequent backend checks, not cross-origin browser broadcasts.

Transient passwords, preauth controls, intent proofs, enrollment material and one-time recovery-code displays stay outside normal form/query telemetry and are cleared on completion/cancel/navigation/expiry. Recovery-code display/download is only the approved explicit personal-security ceremony, never ordinary app persistence. No auth polling/heartbeat: GET/status/list requests do not renew idle lifetime, and focus refresh must not manufacture keep-alive activity.

### HTTPS deployment addendum: preferred end-to-end TLS

**Approved architecture, subject to deployment/security testing; no operational activation approved.** Prefer:

```text
Browser HTTPS -> controlled edge reverse proxy
                 |-- exact NGO Host -> NGO static build
                 |-- exact OPS Host -> OPS static build
                 `-- /api/v1/* -> certificate-verified private HTTPS
                                  -> TLS-capable production application server
                                  -> Django with genuine secure WSGI/ASGI scheme
```

1. Preserve the canonical public Host selected from the exact portal-host allowlist. Django must see `https` and that Host so its computed origin matches the configured `ngo_web` or `pwc_ops` portal. Reject unknown/malformed Host and invalid authority/port combinations; do not derive identity from forwarded Host, JSON or a portal label. Certificate/SNI routing and HTTP Host must follow a documented validated mapping.
2. Verify the upstream certificate chain, validity and expected server name; never disable certificate verification. Restrict backend ingress to controlled edge peers with firewall/network policy and authenticated upstream access; assess mTLS. Monitor certificate expiry/rotation. The backend cannot be an alternate public ingress.
3. Strip client-supplied `Forwarded` and `X-Forwarded-*` headers, including host/protocol/port/client-IP claims, before constructing any explicitly approved ingress metadata. Reject conflicting/duplicate framing and authority information. Do not append untrusted protocol values or treat a browser header as evidence of TLS.
4. TLS must reach the application-serving layer that supplies Django's request scheme. A second proxy that terminates HTTPS and then sends ordinary HTTP to the application recreates the compatibility problem. An encrypted upstream alone is not proof that Django observes the correct Host/scheme.
5. Source-IP trust is a separate O3 decision: current abuse budgets use `REMOTE_ADDR`. With a proxy that may identify the edge rather than the end user, measure aggregate/NAT behavior; do not claim per-client budgets work. Approve either authenticated, peer-restricted source-address propagation with spoof/rate-limit tests, or explicitly tested aggregate-proxy budgets plus edge controls. No arbitrary X-Forwarded-For trust, ad hoc middleware, or silent abuse-budget relaxation is authorized. Document which hop supplies each address and retain sufficient non-secret operational evidence under the approved privacy policy.

### Existing direct-HTTPS compatibility and trusted-termination alternative

The merged `accounts/sessions.py::configured()` and `accounts/flow_security.py::configured()` reject forwarded host/port trust and any non-None `SECURE_PROXY_SSL_HEADER`. Handlers also enforce `request.is_secure()`. Therefore the preferred architecture preserves `SECURE_PROXY_SSL_HEADER=None`, `USE_X_FORWARDED_HOST=False`, and `USE_X_FORWARDED_PORT=False`, and proves genuine HTTPS at Django's application-serving boundary. It is compatible in principle, not already deployment-tested or production-approved. Do not use Django's development server for production.

If hosting requires TLS termination followed by a non-TLS application hop, a **separately reviewed backend/security change** is mandatory. A prospective Django setting is `SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https")`, but setting it now makes existing auth gates fail closed; this ADR neither enables it nor authorizes bypassing those gates. A future extension must:

- Restrict and verify the immediate proxy peer/network path. Django's header tuple alone is not a proxy-IP allowlist.
- Make the trusted edge overwrite the protocol header with one canonical value derived from the actual client-facing transport; reject missing, conflicting, duplicate or comma-separated values under the reviewed single-hop contract. Reject any direct/untrusted request attempting to assert HTTPS. If additional hops are introduced, review the entire chain rather than assuming first/last header values are safe.
- Retain canonical Host validation and keep forwarded-host/port trust disabled unless separately justified. Review secure-redirect behavior to avoid loops, insecure paths or credential-bearing redirects.
- Update both explicit auth configuration gates only through an approved implementation contract and regression tests while preserving HTTPS enforcement, cookie/portal binding and source-IP/abuse controls. Never merely remove the guards.

### CSRF/origin and delivery boundaries

Use exact Django `ALLOWED_HOSTS` and exact HTTPS `PWC_AUTH_PORTALS`, Secure/HttpOnly/host-only session cookies and Secure host-only CSRF cookies. Preserve anonymous unsafe-request CSRF and exact Origin/Referer checks. Same-origin routing needs no broad `CSRF_TRUSTED_ORIGINS` expansion: leave it empty unless a specific additional origin is separately reviewed. Do not whitelist sibling portals or wildcard origins to repair routing; no permissive credentialed CORS. Preserve incoming browser Origin/Referer, not an invented proxy value. Configure secure redirects/HSTS and other headers at the reviewed ingress/application layers; unsafe plaintext authentication/proof/password requests must fail rather than rely on redirects to protect already-submitted secrets.

Registration/reset delivery is currently synthetic-only, including the backend delivery-mode gate. Real email requires a separately approved provider/adapter implementation, secrets, abuse/operational acceptance and link-origin ownership; flipping a flag is not enough. W1 requires none of these.

### Concrete ingress and browser acceptance tests

Before live W2 use, security/deployment reviewers must record results at **both exact portal hosts**:

- Real browser sign-in, MFA preauth/confirmation, session bootstrap and explicit account-confirm link handling; GET/preview cannot mutate registration/reset state.
- Backend-observed Host, HTTPS scheme and portal origin are correct; unknown Hosts, mismatched authority/ports and malformed ingress fail. Forwarded host/proto/port/IP spoofing, duplicate/comma values and direct-backend attempts cannot change trust or budgets.
- Upstream wrong-name/untrusted/expired certificates fail closed; backend ingress is peer-restricted and certificate rotation is demonstrated. Where headers are trusted under a later extension, untrusted peers cannot set them.
- Secure/HttpOnly/host-only/Path/SameSite cookie attributes and Secure CSRF cookie behavior; NGO cookie manually replayed at OPS is rejected by portal binding and vice versa. Sibling-origin unsafe requests fail even when SameSite permits cookie attachment.
- Missing/stale CSRF, absent/incorrect Origin or invalid Referer, cookie-plus-bearer ambiguity and browser use of native issuance routes fail without side effects.
- Login/step-up/eligible hold clearance rotate cookie/CSRF as specified; old cookie/CSRF fail; session revoke/logout/logout-all, idle/absolute expiry and cross-tab invalidation work. Recovery-required states cannot bypass approved restrictions, and no polling renews idle lifetime.
- Source-IP spoofing, concurrent abuse, proxy-aggregate and shared-NAT/load behavior retain effective controls. Never adopt client IP from untrusted headers.
- `/api/` is neither cached nor replaced by SPA HTML; unsafe HTTP requests fail; redirects, no-store/no-referrer, CSP/anti-framing and controlled error logging do not leak secrets. Document compatible rollout/rollback and remaining operational gates.

No such deployment/browser tests are claimed by this documentation approval. Ordinary HTTP Compose/runserver and Arena's TLS-terminating preview proxy are not accepted live-auth environments. W1 may use clearly labeled synthetic contract tests and static previews without weakening backend checks.

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

- **Approved target: WCAG 2.2 AA**, subject to implementation evidence: semantic landmarks, skip link, route titles/focus, labeled controls, described validation, error summary, keyboard and visible focus, dialog focus restoration, live status announcements and non-color-only state.
- **Approved: English frontend foundation with locale architecture and early Urdu/RTL testing/specimen.** Full Urdu launch coverage remains **open** in the Flutter/product foundation; this ADR does not relabel it selected. Store messages by stable keys, use CSS logical properties and `dir`, test mixed-direction identifiers/email/amounts with bidi isolation. Self-host only reviewed/licensed fonts; test Urdu shaping/readability and load cost. Do not mirror all icons or reverse numeric data indiscriminately.
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

## 11. Implementation gates and phased scope

**W1 architecture is approved; implementation starts only in a separately authorized task.** W1 does not require live email delivery, production domains, production ingress, real NGO grants or a complete generated API schema. Live W2 use, W3 authority and later business features retain independent gates.

| Slice | Preconditions | Bounded deliverable and exit evidence |
|---|---|---|
| W0 — approval record/toolchain preparation | Technical approval recorded here; narrow implementation task | Preserve this decision register, verify supported versions/licenses and consumed synthetic contracts; identify owners for later gates, without making their resolution a W1 prerequisite |
| W1 — Web Foundation | Approved foundation choices; supporting dependency checks and separate implementation authorization | Two independently buildable application shells/routes, shared small accessible UI/token primitives, English localization plus Urdu/RTL specimen, typed same-origin API adapter and synthetic contract tests. No live credentials, business menus or claims of operational authority |
| W2 — Authentication and Personal Security Integration | Verified current auth/MFA/session contracts, fixture gaps closed for consumed endpoints; real ingress compatibility and applicable security/delivery approvals **before live use** | ID-01 and supported read-only ID-02/personal-security ID-05 subsets; browser CSRF/cookie/MFA/recovery/session invalidation tests. Mocked development can precede live ingress acceptance but is not real integration evidence; no OPS tool or real NGO switcher |
| W3 — Real NGO Contexts | Independently approved NGO eligibility/representative verification, real authority activation (REAL01–REAL04), production workspace/discovery/capability contracts and relevant PWC-02E/P3 gates | Real ID-03/ID-04 subsets and explicit backend path contexts with two-NGO isolation/revocation evidence; ORG onboarding/team/profile and PWC-01 verification workflows only in separately approved contract-backed slices, never by relabeling synthetic probes |
| W4 — independent NGO operations | Relevant membership/P4, volunteer/project/P5 and dues/finance/P6 APIs, policies and permission matrices | Separate complete membership/import/claim, volunteer/event/project, dues/finance/report slices; no admin finance inheritance or invented ledger/export APIs |
| W5 — alliance/collaboration/operations | Relevant P7 APIs, governance/representation/signatory policies, delegated permissions and privileged-command approvals | Contract-backed ALL/COM/COL/PWC/GOV-01 workflows; OPS-01 requires its independent support/exceptional-access policy. PWC approval cannot bind NGO resources |
| W6 — pilot/release | M1–M3 gates plus P8 security/legal/operations acceptance | Accessibility/localization/performance evidence, backup/restore, monitoring/support, staged pilot and explicit human launch decision |

W labels organize frontend engineering only; they do not replace roadmap P0–P8 or M1/M2/M3. Each implementation ticket names canonical IDs, methods/shapes, versions, allow/deny matrix, state transitions and negative tests. Missing business APIs block their workflows, not W1. No automatic follow-on implementation, feature activation or release is authorized by this documentation task.

## 12. Final decision register and unresolved choices

**Approval record: 24 October 2026, product-owner PWC-02D finalization instruction.** The four status categories are: **Approved for W1**; **Approved architecture / testing required**; **Blocked before live integration**; **Deferred to deployment/later business phase**. Compound WEB entries explicitly split their approved direction from unresolved execution details. Neither this register nor a commit supplies missing security/governance approval.

| ID | Approved decision and status | Recommended execution / alternative / risk | Remaining approval or evidence; timing |
|---|---|---|---|
| WEB-01 | **Approved for W1:** React/TS/Vite, separate NGO/OPS apps/builds/routes/sessions/deployments; shared tokens, accessible components, typed API/localization utilities; shared Django REST backend | Minimal shared source packages, not shared runtime state. Next.js or Flutter Web would require a new justified decision; avoid premature table/framework infrastructure | Supporting libraries, exact compatible versions, package-manager/Node pinning and licenses remain implementation-review choices before installation; passing two-app build/test evidence required |
| WEB-02 | **Approved architecture / testing required:** preferred end-to-end verified TLS, canonical Host/scheme and origin binding. **Blocked before live integration:** actual ingress acceptance | §4 verified HTTPS upstream with restricted ingress; alternative trusted TLS termination needs separately reviewed backend/security extension. Risk: false secure scheme, spoofed metadata or proxy-aggregate budgets | Security/deployment owner: exact hosts/certificates, ingress/server selection, source-IP trust, abuse tests and real browser evidence before live W2; no proxy setting changes approved |
| WEB-03 | **Approved architecture / testing required:** same-origin cookie/CSRF, existing MFA/session/recovery contracts; no browser bearer tokens, separate identity provider or unnecessary BFF. **Blocked before live integration:** operational activation | Current personal flows only; synthetic testing may start in W1. Risk: treating 202/assurance/recovery as full authority, losing rotated CSRF or pretending real delivery exists | Auth/security owner: fixture/service reconciliation, flow tests, applicable keys/flags, link-origin ownership and ingress acceptance; real delivery provider/adapter separately reviewed before real mail |
| WEB-04 | **Approved for W1:** narrow typed relative-URL adapter, synthetic verified fixtures, safe normalization of distinct error envelopes. **Approved architecture / testing required:** eventual reviewed schemas/generation | Manual bounded verified types first; no fabricated universal SDK or contradictory slice snapshots. Full PWC-03C is not a W1 blocker | API owner: missing registration/reset fixtures and exact consumed contracts before those W2 integrations; generation/versioning plan before broader generated consumers |
| WEB-05 | **Approved for W1:** explicit NGO UUID backend paths, backend-authoritative authorization, tenant cache isolation; synthetic probes never production functionality. **Blocked before live integration:** real NGO contexts | Synthetic two-NGO isolation tests only; no real switcher built from fixture discovery. Risk: stale cross-tenant state or fixture-to-real authority promotion | Authorization/product owners: PWC-02E, real workspace contracts and REAL01–REAL04 before W3 activation; no real authority approved here |
| WEB-06 | **Approved architecture / testing required:** independent platform/alliance/NGO domains; Board/platform status grants no NGO access; NGO administration grants no finance. **Deferred to later business phase:** operational entry/tools | Personal security is not OPS-01; no `isAdmin` shortcut. Risk: operational shell mistaken for an authority grant | Security/governance/API owners: explicit OPS entry/capabilities and per-command contracts; GM01–GM12 remain independently unresolved where applicable, before relevant implementation |
| WEB-07 | **Deferred to later business phases:** onboarding evidence, imports/files/exports, finance, institutional membership, commitments and support workflows | Only complete approved API/policy-backed vertical slices; do not expose invented business forms or fake datasets. No policy option is selected here | Relevant policy/backend owners: PWC-02E and each domain's authority, evidence, posting, signatory, storage and retention contracts before its feature; these are not W1 blockers |
| WEB-08 | **Approved for W1:** English foundation, early Urdu/RTL testing and WCAG 2.2 AA target. **Approved architecture / testing required:** accessible responsive primitives | Small representative specimen first; alternative full bilingual launch is not approved. Risk: “RTL-ready” or automated axe checks misrepresented as complete localization/accessibility | Product/accessibility owners: browser/assistive-tech matrix and specimen evidence during W1; full Urdu launch coverage, translations/fonts and measured performance budgets remain open before release |
| WEB-09 | **Approved architecture / testing required:** no browser secrets/persisted private caches; secure artifact and deployment separation. **Deferred to operational deployment:** concrete hosting/operations/privacy choices | Versioned independent artifacts, no API caching, reviewed headers/CSP and rollback. No hosting vendor or legal/retention policy selected | Operations/security/privacy owners: exact deployment, secret rotation, logging/retention, support, incident/restore and maintenance evidence before real operation; only bounded CI/build evidence required for W1 |
| WEB-10 | **Deferred to later product/business decisions:** public web/SEO delivery and separately scoped PWC-owned finance. Elections/cases/payments/national expansion retain existing deferred statuses | Keep outside W1 and do not silently extend these admin builds. Risk: technology approval mistaken for product/governance scope approval | Product/governance owners: separate scoped decisions and APIs if requested; no launch routes or new policy approvals here |

**Still unresolved:** supporting toolchain/library versions and maintenance choices; exact production domains, ingress/server and certificate ownership; source-IP trust and abuse-control acceptance; trusted-termination extension if required; real email provider/adapter and link origin; consumed contract gaps and broader PWC-03C generation; real workspace and OPS entry contracts; all future business policies/APIs; launch Urdu coverage, browser matrix, performance budgets and operational/legal/privacy approvals. Resolve each at its stated gate, not all before W1. Framework approval does not close any live-activation gate.

## 13. Acceptance criteria and documentation task boundary

### W1 — foundation acceptance (implementation evidence still required)

- [ ] A separately authorized W1 task uses the technical approvals dated 24 October 2026 and preserves this gate ledger; approved auth/authorization ADRs unchanged.
- [ ] Two independent NGO/OPS builds and route shells; shared typed/presentational primitives but no shared runtime/session/context singleton; reviewed compatible versions, licenses and reproducible lockfile.
- [ ] Small accessible controls/layout/error states, English messages and early Urdu/RTL mixed-text specimen; WCAG 2.2 AA target supported by automated and manual foundation checks, without claiming complete product conformance or Urdu launch coverage.
- [ ] Typed relative-URL adapter with same-origin credentials, CSRF injection, no browser bearer/mobile auth, bounded response validation and normalization of both declared errors and non-JSON failures.
- [ ] Clearly labeled synthetic contract tests for auth states, MFA preauth, CSRF rotation/invalidation, expiry/logout, context partitioning, in-flight generation discard and cross-principal/tenant stale-response prevention. These prove client behavior only, not real backend/browser/TLS acceptance.
- [ ] No secrets in artifacts, persisted private data, production fixture menus, invented operational capabilities/business workflows, or real NGO grants. OPS shell grants no tool access; tests represent NGO-admin-without-finance and Board-without-NGO-grant denials without inventing a production API.
- [ ] Canonical screen metadata traces only supported/tested subsets; unimplemented and deferred business routes remain unregistered. Preserve all §10 identifiers and source requirement statuses.
- [ ] Both apps pass configured type/lint/component/contract/build checks and appropriate synthetic browser smoke tests; limitations and baseline bundle/interaction measurements recorded honestly. No backend tests are claimed from mocked acceptance.

**Not W1 prerequisites:** live email, production domains/ingress, production cookies, real users/NGO workspaces, all business APIs, complete generated SDK, full Urdu translation or production legal/operations sign-off. Their absence must not be concealed by mocks or bypasses.

### W2/W3 and production acceptance remain independent

Live W2 requires verified consumed authentication/MFA/session contracts, real browser cookie/CSRF/session/recovery behavior, §4 ingress compatibility and applicable WEB-02/03/04 security approvals. W3 additionally requires approved NGO verification, real authority activation, backend workspace contracts and REAL01–REAL04. Later business workflows require their own backend allow/deny, file/export, finance, governance and commitment acceptance. Production activation still requires WEB-09 and roadmap release gates; approval here is not real-user or pilot authorization.

### Finalization provenance and scope

Before editing, the assigned branch was at `cb4ae6c7c1b7f08bd8b6c4a5b5a0a304f1276445` with an untracked ADR. The remote feature branch was fetched and verified at expected checkpoint `8f9223767d841212c17683e1a28812891e2461dc`; the untracked ADR matched its remote blob byte-for-byte. A checksum-verified external preservation copy and an include-untracked stash were retained, then the **existing branch** fast-forwarded to that checkpoint. No prior commit was recreated and no file content was discarded or history rewritten.

This documentation task updates only ADR-0003, validates sections/local links/canonical-ID coverage/whitespace/single-file scope, then makes a normal commit/push to `arena/ce7673c3-pwc-platform` and verifies remote commit/tree and clean status. No frontend/backend code, Django settings, dependencies, migrations or existing approved auth/authorization ADRs change. No PR is opened or merged. Stop after the documentation checkpoint; implementation requires another task.
