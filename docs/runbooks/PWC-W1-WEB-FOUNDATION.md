# PWC-W1 — Web foundation

**Date:** 24 October 2026

**Scope:** W1 implementation against approved [ADR-0003](../decisions/ADR-0003-web-frontend-architecture.md). Not live authentication, real NGO access, a production deployment or an MVP release.

## 1. Baseline and preservation

Started on `arena/ce7673c3-pwc-platform` with a clean tree, local and fetched remote HEAD both at required `b260ccf2ea3faacb7b74e4c1d4eb47f99511d823`. No reconciliation or stash was necessary for W1. Existing Django code, migrations, flags, wire fixtures and approved ADRs remain unchanged. Root AGENTS includes historical scaffold/branch statements; current merged code, approved ADRs and this assigned branch govern this task.

## 2. Structure and ownership

| Location                         | Responsibility                                                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `apps/ngo-web`                   | Independent NGO shell, route registration, public non-secret configuration and Vite artifact                                            |
| `apps/pwc-ops`                   | Independent Operations shell/routes/configuration/artifact; no NGO administration or privileged tools                                   |
| `packages/design-tokens`         | Semantic color, spacing, typography, focus and shape CSS tokens                                                                         |
| `packages/web-ui`                | Native accessible controls/layout, safe render boundary, presentational shell, honest readiness overview and synthetic UI specimens     |
| `packages/web-i18n`              | Typed English/Urdu resources, memory-only locale context, document language/direction                                                   |
| `packages/web-api`               | Closed relative-URL adapter, sanitized errors, fixture-backed narrow parsers, independent memory scope/cache lifecycle and invalidation |
| `packages/api-contracts`         | Existing unchanged backend synthetic wire-key fixtures; not generated OpenAPI                                                           |
| `tests/web`                      | Unit/component/contract/isolation tests and Chromium browser checks                                                                     |
| `.github/workflows/frontend.yml` | Clean install, quality checks, both builds and browser checks; separate from unchanged backend CI                                       |

Shared source is not shared runtime state. Each application constructs its own `ScopeState` and disabled `ApiClient`; there is no global singleton, user directory, role evaluator or service authority in a UI package. Shared components do not infer grants. Apps own their separate route trees even where presentational pages are shared.

## 3. Toolchain, install and commands

Validated locally with Node **22.22.3**, npm **10.9.8**; `.nvmrc`, engines and `packageManager` record this baseline. Use the root npm workspace lockfile; do not install separately inside each app. Maintained dependency versions were queried from the npm registry and pinned. Installation runs no package lifecycle scripts.

```bash
# From repository root; select Node via your usual version manager/.nvmrc
npm ci --ignore-scripts
npm run typecheck
npm run format:check
npm test
npm run build                           # both independent artifacts
npm run check                           # all of the above, excluding browsers
npm run build -w @pwc/ngo-web             # NGO only
npm run build -w @pwc/pwc-ops             # Operations only
npm run dev:ngo                          # port 5173
npm run dev:ops                          # port 5174, separate terminal
```

Output: `apps/ngo-web/dist` and `apps/pwc-ops/dist`; generated assets are ignored. Vite's workspace build does not itself typecheck: run root `typecheck`/`check` before acceptance. `format`/`format:check` explicitly target W1-owned files and never reformat the backend or existing contracts/ADRs. TypeScript strict mode includes unchecked-index/optional-property/unused-symbol checks. No separate ESLint policy is claimed by this slice.

Browser checks on a normal supported development/CI host:

```bash
npx playwright install --with-deps chromium
npm run build
npm run test:browser
```

Playwright serves both built artifacts with Vite preview, reusing existing local servers outside CI; stop stale servers first to ensure they serve current code. `CI=1` requires its own fresh ports. An already-installed compatible executable may be selected with `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/absolute/path`; this is test tooling only, never browser-bundled configuration. Browser traces/results are ignored. Browser tests use internal loopback URLs to drive local servers; browser application code has no localhost backend URL.

### Dependency choices

Runtime: React/React DOM **19.3.1**, React Router DOM **7.18.4** plus internal packages. Build/type tools: Vite **8.3.5**, React plugin **6.1.2**, TypeScript **5.9.3**. Test/style tools: Vitest **5.0.5**, jsdom **30.1.3**, Testing Library, user-event, jest-dom matchers, axe-core **4.14.0**, Playwright **1.64.1**, Prettier **3.9.10**; exact type/transitive versions are locked. Verify future upgrades deliberately. Installed dependency license metadata is checked as implementation evidence, not a legal license opinion.

Native HTML controls suffice for W1. No custom complex widget framework, React Aria, data grid, form framework, TanStack Query/global store or i18next is needed yet. The small typed localization/context implementation is bounded to this specimen. ADR-recommended supporting libraries may be evaluated when real feature complexity warrants them, not installed speculatively. Noto Sans Arabic Variable **5.3.0** (Fontsource package, OFL-1.1) supplies one self-hosted unmodified Arabic WOFF2 subset (~167 kB), justified by missing Urdu glyphs in the sandbox system font. Its original copyright/license is distributed at `/third-party-notices/Noto-Sans-Arabic-OFL.txt` in both builds. No remote font service, analytics, identity or other third-party runtime service is integrated.

## 4. Configuration and preview

Each app has its own immutable `src/config.ts`: app ID, title, W1 stage and `network: 'disabled'`. `createFoundationRuntime()` always creates a disabled adapter; it does not trust a flag from the environment. **There is no live API enable variable or production API-base setting.** No `.env` or secrets are required for W1. Vite environment variables are browser-visible and must never contain secrets.

Both dev servers bind `0.0.0.0`, use distinct strict ports and accept localhost by default. For a proxied preview, start each with only its exact public hostname:

```bash
PWC_PREVIEW_HOST=YOUR_EXACT_NGO_PREVIEW_HOST npm run dev:ngo
PWC_PREVIEW_HOST=YOUR_EXACT_OPS_PREVIEW_HOST npm run dev:ops
```

Supply a hostname only, no scheme/path/wildcards. The Vite configuration validates its syntax and adds that one hostname rather than allowing arbitrary hosts. No API proxy is configured. Ordinary HTTP and a TLS-terminating preview remain **unreviewed live-auth topology**; W1 works because it makes no API calls. This is a development preview, not a deployed production service.

Future deployment must route `/api/` before SPA fallback and must not cache private responses. Vite's development history fallback is not a production API router: `/api/*` must not be used against this static preview as evidence of a backend response. Exact domains, TLS/certificate ownership, no-store/CSP/security headers, trusted source-IP handling and deployment rollback remain ADR-0003 WEB-02/09 gates.

## 5. Routes, canonical references and honest readiness

Both apps register only:

- `/`: foundation/readiness overview (no business records or metrics).
- `/foundation/accessibility`: local-only English/Urdu/control specimen; text is neither transmitted nor persisted.
- `/foundation/states`: clearly labeled static loading, empty and error specimens; no background process.
- Other paths: safe unavailable/not-found content with a local return link.

`ID-01` through `ID-05` appear only as canonical readiness references. NGO overview additionally references `ORG-04`; Operations references `OPS-01`. These are not clickable business routes and do not claim those screens are implemented. No login/registration/MFA forms, real selector, verification queue, roster, finance, governance, collaboration or support commands exist. There is no public directory integration, synthetic-probe UI or fabricated operational dashboard.

## 6. API infrastructure and security behavior

The default adapter refuses every request with `W1_NETWORK_DISABLED` before touching any transport. Only explicit synthetic-test transport injection exists; there is no ambient fetch fallback. The shipped shells never call the adapter. Enabling live traffic requires a separately reviewed W2 code change, not an environment toggle.

The narrow closed operation registry covers existing personal `csrf/`, `me/`, `mfa/status/`, `logout/`, `step-up/` and `recovery-hold/clear/` shapes under `/api/v1/auth/`. This is infrastructure, **not user journeys or a complete SDK**. It registers no login/registration, native/mobile, NGO, finance or operational command routes. Caller-supplied URLs, headers, bearer credentials, cookie values or cross-origin bases are not accepted.

Synthetic tests exercise:

- `credentials: 'same-origin'`, relative URLs, no-store, no-referrer and no redirect-following. CSRF bootstrap validates the masked token; it lives only in memory. Unsafe requests require it in `X-CSRFToken`; GET bodies are forbidden.
- Exact selected fields parsed at the trust boundary; `me/` yields identity/session/hold/verification, not roles or NGO permission. Enabled-MFA 202 remains preauth. Redacted login classification is a test helper, not a sign-in endpoint or proof store. `restricted` versus `review_required` remain distinct; only the former has the approved fresh-pre-hold-factor path.
- Single pending unsafe security command per client. Successful step-up/eligible hold clearance discards old CSRF and private cached state even if response decoding fails, preserving the logical identity/session partition. No mutation or CSRF auto-retry. W2 must handle lost-response ceremonies and real concurrent-tab/browser behavior against the backend.
- Safe handling of 401, 403, 404, 409, 429 and 5xx, network/non-JSON/malformed responses. Auth `{error:{code,message,field_errors,request_id}}` and synthetic authorization `{code,correlation_id}` normalize without rendering server messages/field values/bodies. Retry-After numeric seconds are exposed as advisory metadata; the client never retries automatically. HTTP-date Retry-After support remains outside this narrow adapter.
- Logout clears local state immediately, including when networking is disabled, CSRF is missing or server/network failure occurs, but failure is not reported as successful backend revocation. Current-request 401 invalidates session state; 403/409 clear affected private state. A late old-context 401 cannot invalidate a newly selected principal.
- AbortSignal plus generation fences before/after asynchronous response parsing. The generation also fences CSRF bootstrap completion. Transport ignoring abort still cannot repopulate the next identity/NGO cache. Already-cancelled requests fail before transport.

`ScopeState` partitions memory by app, principal, logical session, explicit organization, registry version, context revision, generation and caller operation key. No localStorage/sessionStorage/IndexedDB, service worker, offline private cache, auth heartbeat or positive authorization cache exists. Cache values are copied; tickets from another state cannot write. Switching/invalidation aborts requests and purges data; no first-NGO fallback, selection header or server-side remembered tenant is invented. This store is a small synthetic infrastructure primitive, not production context discovery or an authorization engine. Future operation keys must include relevant filter/object parameters and permissions must always be rechecked backend-side.

Same-origin BroadcastChannel sends only `session-invalidated` after logout/session invalidation, never identity/grants/proofs. A remote signal only clears state; it cannot authenticate. No cross-origin session bridge exists. Without BroadcastChannel support, the helper safely does nothing; W2 still needs authoritative revalidation on entry/resume and every protected backend request. Hidden-document/unmount lifecycle clears this application's state. Required live focus/visibility permission refresh and actual expiry enforcement are **W2/W3 acceptance**, not simulated frontend authority.

## 7. Accessibility/localization conventions

- Semantic header/nav/main/footer, skip link, route-title and heading-focus management; keyboard-operable native controls; small-screen disclosure with `aria-expanded`/`aria-controls` and hidden closed navigation.
- Visible focus rings, at least 44px button/control height, direction-aware logical CSS, labeled form fields with linked hints/error text and local status announcements. Decorative numerals/icons are hidden from accessible names but still meet visible contrast checks.
- Responsive layouts and contained semantic tables with captions/header scopes and a named keyboard-focusable scroll region; 320px reflow tested. No data grid or virtualization.
- Typed resources require English/Urdu key parity; locale is memory-only and resets to English on reload. Root `lang`/`dir` and shell direction change; mixed identifiers use `bdi`. Specimen drafts clear on language change. No assertion that all future product text is translated.
- No remote font service. One self-hosted Noto Sans Arabic subset prevents missing Urdu glyphs; its license/copyright were inspected and retained in both artifacts. Native Urdu shaping/readability review and product font acceptance remain future work. The catastrophic render-boundary fallback is deliberately minimal English; it renders no raw error and requires no functioning locale/router context. Main roots suppress raw caught-error telemetry; no third-party error reporting is configured.
- WCAG 2.2 AA is the target, not a conformance certificate. jsdom checks have no real canvas/contrast/layout; real Chromium axe checks include contrast. Automated results do not replace human screen-reader, native Urdu, zoom and supported browser/device acceptance.

## 8. Evidence and limitations

Initial typechecking found a widened direction literal; corrected with an explicit `ltr | rtl` type. Initial component selectors incorrectly included aria-hidden numerals; corrected to accessible names. Real Chromium checks caught low contrast on navigation numerals; opacity was removed. Visual inspection found missing Urdu glyphs with system-only fonts; a pinned, licensed, self-hosted Arabic font subset fixed the specimen. A browser assertion was corrected to follow the disclosure button's changed accessible label. No tests were removed to hide these findings.

The sandbox lacked a browser and system NSS libraries; early browser launches failed before running application checks. For local validation only, a Chromium 153 binary and its packaged runtime libraries were obtained through npm `@sparticuz/chromium@153.0.0` in an external tools directory, not added to repository dependencies. The executable/loader paths were passed through environment variables. Normal CI uses Playwright's managed Chromium install. This sandbox tooling is not needed in the application or committed lockfile.

Validation results are recorded below; no backend suite was rerun because no backend files changed. Current checks cover synthetic infrastructure and static UI only. They do not demonstrate real login, cookie attributes, browser CSRF/Origin enforcement, direct TLS, production permission refresh, MFA proof ceremonies or a real tenant workflow. No Firefox/WebKit, physical devices, assistive-technology audit, human Urdu review or external penetration test is claimed.

### Final local validation — 24 October 2026

This table records original W1 checkpoint `1c286aca`. See the [integration review](../reviews/PWC-W1-WEB-FOUNDATION-INTEGRATION-REVIEW.md) for subsequent corrections and fresh results.

| Check                                    | Actual result                                                                                                                                                                                      |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm ci --ignore-scripts`                | PASS; clean lockfile install                                                                                                                                                                       |
| `npm run typecheck`                      | PASS; strict TypeScript for both apps, packages and tests                                                                                                                                          |
| `npm run format:check`                   | PASS; W1 sources/docs/configuration                                                                                                                                                                |
| `npm test`                               | **78 passed**, 0 failed; API/lifecycle/contract/component/route/localization/DOM accessibility                                                                                                     |
| `npm run build`                          | PASS; independent NGO and Operations production artifacts                                                                                                                                          |
| `CI=1 … npm run test:browser`            | **9 passed**, 0 failed, Chromium 153; final run serves fresh production builds, including English/Urdu browser axe/contrast, 320px reflow, keyboard/skip/focus, safe deep links and zero API calls |
| `npm audit --audit-level=low`            | 0 reported vulnerabilities at validation time; not a security certification                                                                                                                        |
| Locked dependency license metadata       | No missing license fields; includes permissive licenses, MPL-2.0 tooling and OFL-1.1 font; metadata inspection is not legal approval                                                               |
| Font distribution                        | Original Noto copyright/OFL included unchanged in both artifacts; browser font-load check and visual specimen inspection passed                                                                    |
| Preview hosts                            | Both exact preview hosts return 200; arbitrary Host returns 403; this tests Vite host policy, not auth ingress                                                                                     |
| Backend/contracts/approved ADR integrity | Unchanged against required checkpoint; no backend regression run claimed                                                                                                                           |

Baseline output per app: JavaScript **280.99 kB** (~89.8 kB gzip), CSS **8.55 kB** (~2.60 kB gzip), one Arabic font **165.96 kB**, and ~0.5 kB HTML. These are measured build sizes, not approved bandwidth/startup budgets. No route splitting or private offline cache was added to this small foundation. Low-end/mobile network startup measurement remains future acceptance work.

## 9. W2/W3 and later prerequisites

- **W2:** review exact consumed auth/MFA fixtures and services (older session fixtures are incremental snapshots); fill missing contracts for any new consumed endpoints; explicitly authorize live client code and session/recovery flows; prove real ingress compatibility, cookie/CSRF/origin, rotation, expiry, lost responses, multi-tab invalidation and safe return/link handling. Real email needs its own approved provider/adapter implementation and link origin; existing backend delivery remains synthetic-only.
- **W3:** independently approve NGO eligibility and representative verification, real authority activation REAL01–REAL04 and production discovery/workspace/capability contracts. Enforce explicit path UUIDs and backend action/object/file/export scope; none of the synthetic probes becomes production functionality.
- **Later:** membership/import/claim, volunteers/events/projects, dues/finance, governance/committees/collaboration and exceptional operations require their own approved contracts and permission policies. Board/platform status grants no NGO-private access; NGO admin grants no finance. PWC approval cannot commit an independent NGO.
- **Deployment:** ADR-0003 preferred verified end-to-end HTTPS or separately reviewed trusted-termination extension; exact Host/scheme/origin, restricted ingress, sanitized forwarding/source-IP trust and abuse controls. No Django proxy setting or HTTPS gate is changed by W1.

Proceed only to human web-foundation integration review after the normal branch checkpoint. No PR, merge or W2 integration is authorized by the W1 completion report.
