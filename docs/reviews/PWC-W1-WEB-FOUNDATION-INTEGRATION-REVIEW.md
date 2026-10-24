# PWC-W1 — Web Foundation Integration Review

**Date:** 24 October 2026

**Verdict: READY FOR HUMAN PR REVIEW — bounded W1 foundation, subject to final-head CI and owner acceptance.** Three confirmed findings were corrected with regressions. No unresolved Critical or High finding was identified in this bounded review; this is not a claim of complete security assurance. No live authentication, real NGO authority, production deployment or public MVP release is approved by this verdict.

## 1. Baseline, repository integrity and review scope

- Assigned branch: `arena/ce7673c3-pwc-platform`. Initial working tree was clean; HEAD and the fetched feature branch both matched required checkpoint `1c286acaf3f8be7aa18de71b4ea7c7539631f0f9`. No recovery, stash, reset, branch switch or history rewrite was needed in this review.
- Latest fetched `main`: `cb4ae6c7c1b7f08bd8b6c4a5b5a0a304f1276445`, containing merged authentication and authorization foundations. It is an ancestor of W1. Re-fetch/recheck before PR creation; if main advances, re-evaluate the actual base rather than silently claiming current integration evidence.
- Reviewed the complete branch diff against main: the proposed/approved ADR-0003 history and W1 are both on this feature branch. ADR-0003 is an expected **new file relative to main**, not a modification of the approved authentication/authorization contracts. The review corrections do not modify ADR-0003.
- Protected backend source, migrations, default configuration, API fixtures, existing backend workflow, AGENTS and product/screen documents remain unchanged against main. No Django settings, flags, secrets, role grants or database records were altered. The review introduces no dependencies or lockfile changes.

### Authority and references

[AGENTS](../../AGENTS.md), [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), approved [web ADR-0003](../decisions/ADR-0003-web-frontend-architecture.md), [authentication ADR-0001](../decisions/ADR-0001-authentication-and-recovery.md), [authorization ADR-0002](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), [IA/navigation](../product/PWC_App_Information_Architecture_and_Navigation_v1.0_Draft.md), [screen specification](../product/PWC_Detailed_Mobile_and_Web_Screen_Specification_v1.0_Draft_for_Review.md), [contract fixtures/readiness](../../packages/api-contracts/README.md), [authentication integration review](PWC-03A-AUTHENTICATION-INTEGRATION-REVIEW.md), and the [W1 runbook](../runbooks/PWC-W1-WEB-FOUNDATION.md).

The root instructions and roadmap contain historical scaffold/branch statements; the actual merged code, explicit current assignment and approved decisions govern their recorded scopes. Product provisional/open/deferred statuses and M1–M3 P0 scope are not changed.

Protected decision SHA256 values verified during review:

| Decision       | SHA256                                                             |
| -------------- | ------------------------------------------------------------------ |
| Authentication | `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294` |
| Authorization  | `93d30e1169c2ac0654803348ae4a01450b2fa4902b414a517b050692376a834f` |
| Web foundation | `734b9323dd35bde5fe67b1b0e7b4d4746231206c62b78b2f6d76e551a96a2496` |

## 2. Implemented scope and architecture compliance

| ADR requirement        | Reviewed implementation and assessment                                                                                                                                                                                                                                      |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Two applications       | Independent HTML/React roots, Vite configurations, route trees and dist artifacts under the existing NGO/Operations directories; no combined privileged-mode toggle                                                                                                         |
| Independent runtime    | Each mounted app calls its own runtime factory. Scope/cache/CSRF objects are instance-owned; no shared authenticated singleton, identity provider or query/session store                                                                                                    |
| Shared packages        | CSS design tokens and local font; native accessible UI primitives/presentational shell; typed transport/error/lifecycle utilities; typed English/Urdu locale provider. Shared UI imports no API-state package and shared source imports neither app; regression guard added |
| Narrow tooling         | Private npm workspaces and one pinned lockfile; strict TypeScript with optional/index/unused checks; native controls without speculative data grids, global state or rich widget frameworks                                                                                 |
| Routes and identifiers | Only foundation overview, accessibility/language specimen, state specimens and safe not-found routes. ID-01–05, ORG-04 and OPS-01 are canonical readiness references, not completed business screens. ADR's full 72-ID screen mapping is preserved                          |
| Authority separation   | No business endpoints, role hierarchy, finance inheritance, operational entry claim or grant commands. Authentication/assurance is not NGO authority; Board/platform status grants no NGO access                                                                            |
| Maintenance/CI         | Web clean-install/type/style/test/build/browser workflow is separate from the unchanged Python 3.11/3.12/PostgreSQL workflow. Both run on push/PR. No unrelated CI refactor                                                                                                 |

The foundation is structurally compliant with ADR-0003's W1 scope. Small duplicated app-owned route/config files are intentional isolation rather than a second shared application runtime. No new product functionality was added in this review.

## 3. Confirmed findings and corrections

Severity reflects the bounded W1 exposure: networking is disabled and no real private data is loaded. The lifecycle defects would undermine safe integration if carried forward, but did not expose an active authentication or NGO workflow here.

| ID    | Severity / status | Confirmed defect                                                                                                                                                                                          | Correction and regression evidence                                                                                                                                                                                                                                                                                                 |
| ----- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| W1-M1 | Medium — resolved | `ApiClient.request('logout')` checked disabled networking/missing CSRF before clearing scope/cache. A locally blocked logout could retain private state                                                   | Capture only the existing CSRF value for an eligible request, then invalidate local state at logout initiation before transport preconditions. Disabled and missing-CSRF attempts now purge without sending; existing successful/server-failed logout tests still pass. No claim of backend revocation on failure                  |
| W1-M2 | Medium — resolved | Successful step-up/eligible hold-clear response invalidated CSRF/cache only after decoding. A malformed success payload or rejecting decoder retained old state despite the backend's successful rotation | Current-request validation and successful-rotation invalidation now run in decoder cleanup even when decoding fails. Preserve logical identity/session, not cached data or old CSRF. New step-up and hold-clear regressions assert contract failure, empty cache and required fresh bootstrap; stale-response fences remain intact |
| W1-L1 | Low — resolved    | Preview-host regex accepted leading-dot names, which Vite interprets as domain-suffix allowlisting, plus malformed DNS labels                                                                             | Both app configs now validate exact, bounded DNS labels and reject whitespace, suffix/wildcard notation, schemes, ports, paths and malformed/oversized labels. Tests exercise both configs and an explicitly allowed hostname                                                                                                      |

Reproduction before fixes: original suite passed 78/78. Adding the first regressions produced **12 failed / 80 passed**: four lifecycle cases and eight invalid-host cases failed for the expected assertions. Fixes and expanded boundary/host checks now pass. No existing tests were removed or skipped. A new boundary test initially selected a Node environment incompatible with the existing jsdom setup; that test was returned to the configured environment, without changing application behavior or weakening the setup.

## 4. Security/API-adapter assessment

- **Default-disabled networking verified:** both shipped factories create a disabled client; public configuration has no environment-based live switch. No ambient fetch fallback. Production-build browser checks recorded zero `/api/` requests across foundation routes and locale changes. Synthetic transport injection is test infrastructure, not a production client mode.
- **Closed transport:** operations resolve to fixed relative `/api/v1/auth/` paths. No arbitrary base URL, caller header bag, Authorization header, bearer/refresh storage, mobile issuance/refresh, permissive CORS or NGO command registry. Requests use same-origin credentials, no-store, no-referrer and reject redirects; unsafe requests require in-memory CSRF and JSON.
- **Lifecycle:** scope keys include portal/principal/logical session/NGO/registry/revision/generation. Switching/logout/invalidation clears memory and aborts requests; generation checks reject late responses even if transport ignores cancellation. External abort, body-parse races, late old-context 401, revision changes, cross-instance tickets and copied cache values are tested. Cache keys and scope IDs never create backend authority.
- **Rotation:** one pending unsafe command per client, explicit CSRF re-bootstrap after successful rotation, no automatic mutation replay. M1/M2 corrections cover blocked logout and decoding-failure paths. Real multi-tab rotation, ambiguous/lost-response ceremonies and live expiry remain W2 acceptance, not a claim supplied by these mocks.
- **Errors and leakage:** auth and synthetic authorization envelopes normalize safely; HTML/non-JSON/malformed responses fail without rendering raw server bodies/messages/field values. Current 401 clears session state; 403/409 clear private state. 429 exposes bounded numeric Retry-After metadata without auto-retry. No private query persistence, analytics, raw-error reporting or secret-bearing browser configuration was introduced.
- **Injection:** no raw HTML renderer or executable imported content. React/native input escaping and generic local feedback are exercised with an HTML/event-handler-like string; no injected element or script execution occurred. Error boundaries render a generic fallback rather than exception details.
- **Tabs and origins:** BroadcastChannel carries only a non-sensitive invalidation signal, never credentials/capabilities, and does not authenticate. Other origins do not share cookie/session state; lack of BroadcastChannel support must still be covered by authoritative W2 revalidation.
- **Backend not activated:** checked unchanged flow/session/MFA defaults and direct-HTTPS/proxy-trust guards. No backend or synthetic authorization endpoint was enabled, exposed through a new proxy, or used as production NGO functionality. No private/finance/verification/governance/support tool is reachable from these route trees.

The adapter is intentionally not a full SDK. Registration/reset schemas, live login/MFA journeys, full response validation for future consumed operations, expiry/permission-refresh orchestration and HTTP-date Retry-After support must not be inferred from W1. Do not bypass the network guard as an alternative to W2 review.

## 5. Accessibility, RTL and responsive assessment

Fresh Chromium tests exercised both production artifacts:

- Semantic landmarks, native labels/hints/errors, table header/caption structure, skip link, route heading focus/title updates and keyboard submission.
- Visible 3px keyboard focus outline, accessible disclosure names/expanded state and closed mobile navigation.
- All three foundation pages at **320px** in English and Urdu, font-ready overflow checks and automated WCAG-tagged axe rules including contrast. Contained table scrolling is not body overflow.
- Root language/direction changes and actual desktop sidebar relocation to the RTL side, not merely a `dir` attribute assertion. Independent app locale/navigation state verified across origins.
- Static loading/empty/error specimens are labeled as specimens, with no fabricated running process or business result. Existing component checks cover safe render failures and generic errors.
- Pinned, self-hosted Arabic subset remains local; original Noto copyright/OFL is byte-identical in both distributions. No runtime font-service request or new font/dependency was added by this review.

Limitations: no physical screen-reader/assistive-technology audit, native Urdu translation/shaping acceptance, Firefox/WebKit run, physical device testing or complete zoom/performance matrix. jsdom cannot validate visual contrast; the real Chromium pass complements it but does not establish full WCAG conformance. Full Urdu launch coverage and product font acceptance remain separate decisions.

## 6. Fresh validation and dependency/build evidence

Environment: Node **22.22.3**, npm **10.9.8**, strict TypeScript **5.9.3**, Chromium **153**. Sandbox browser uses the externally installed executable/runtime libraries described in the runbook; CI uses Playwright's managed browser. No browser binary or generated build/test artifact is committed.

| Check                                                | Result                                                                                                                                              |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm ci --ignore-scripts`                            | PASS, clean locked install; no lifecycle scripts                                                                                                    |
| Original-checkpoint `npm run check`                  | PASS: typecheck, scoped format, **78 tests**, both builds                                                                                           |
| Original production-build browser suite              | **9 passed**, no failures                                                                                                                           |
| Confirmed-defect reproduction                        | **12 failed / 80 passed** before fixes, expected failures documented above                                                                          |
| Final `npm run typecheck` and `npm run format:check` | PASS                                                                                                                                                |
| Final `npm test`                                     | **108 passed / 0 failed**: 50 API/lifecycle/contract, 32 component/route/localization, 24 preview-config, 2 package-boundary tests                  |
| Final `npm run build`                                | PASS; independently generated NGO and Operations artifacts                                                                                          |
| Final `CI=1 … npm run test:browser`                  | **11 passed / 0 failed**, fresh production preview servers, no reuse of development servers                                                         |
| `npm audit --audit-level=low`                        | **0 reported vulnerabilities** at review time; not a security certification                                                                         |
| Dependency/lock integrity                            | No manifest or lockfile change in this review; clean install compatible with pinned Node/npm; all locked external packages declare license metadata |
| Font notice/artifacts                                | Original notice preserved in each build; no source maps, private data, dependency trees or binary artifacts staged                                  |
| Scope/whitespace/reference checks                    | Protected tree/blob comparisons, canonical IDs, local Markdown links and Git whitespace checks required before commit                               |

Final measured artifacts per app: approximately **280.95 kB JavaScript**, **8.55 kB CSS**, **165.96 kB Arabic WOFF2** and ~0.5 kB HTML. Build output is ignored. These are size measurements, not low-bandwidth startup acceptance or approved performance budgets. License metadata includes permissive licenses, MPL-2.0 tooling and the OFL-1.1 font; inspection is not legal approval.

No local backend suite was rerun because backend/configuration/migration files are unchanged. Existing checkpoint CI was independently verified successful: [web run 40107986631](https://github.com/salmansabir33/pwc-platform/actions/runs/40107986631) and [backend run 40107986532](https://github.com/salmansabir33/pwc-platform/actions/runs/40107986532), including Python 3.11/3.12. These results belong to `1c286aca`, **not the later corrections**. Final-head push/PR web and backend checks must be verified on GitHub; this committed review does not predict their outcome. The final task report/PR checks provide live status.

Local validation logs are outside Git (`/home/user/w1-review-*.log`); tests and commands in the repository are the reproducible evidence. Scoped style checking is Prettier plus TypeScript diagnostics; no new ESLint policy is claimed.

## 7. Remaining blockers and next assignments

1. **Human W1 review/merge gate:** inspect the full ADR+W1+corrections diff and require green final-head web/backend CI and current PR merge checks. One PR only; no automatic merge, branch rewrite or production activation.
2. **W2 contracts:** authorize a separate personal-auth integration slice; reconcile consumed current auth/MFA schemas/fixtures, explicit confirmation/link handling, live cookie/CSRF/session/recovery/rotation/expiry/invalidations and safe lost-response behavior. There are no live forms or network toggles to switch on here.
3. **W2 ingress:** approve exact hosts, real direct HTTPS at the application-serving boundary, verified upstream certificates, canonical Host/scheme/portal binding, restricted ingress, forwarded-header stripping, source-IP trust/abuse budgets and browser acceptance. The alternative trusted TLS termination still requires a separately reviewed backend/security change. Do not alter Django proxy settings or disable HTTPS guards to make a preview work.
4. **Delivery:** real registration/reset email requires its own approved provider/adapter/operational and link-origin work; current backend delivery is synthetic-only. W1 does not close these gates.
5. **W3:** independently approved NGO eligibility/representative verification, REAL01–REAL04 authority activation and real discovery/workspace/capability contracts. Synthetic probes are not a migration shortcut to production contexts.
6. **Later:** membership/imports, volunteers/events/projects, dues/finance, alliance/governance/collaboration, files/exports and exceptional support require their respective policies/APIs/action matrices. Admin does not imply finance; Board/platform does not imply NGO-private access; PWC approval cannot bind an NGO.
7. **Release:** supported browser/assistive-tech/native Urdu/performance evidence, privacy/legal/retention, security headers/CSP, monitoring, support, backup/restore and explicit pilot/launch approval remain open.

## 8. Explicit merge-readiness assessment

**W1 implementation is suitable for a human-reviewed PR after these corrections.** All confirmed findings in this bounded review are resolved; no unresolved Critical/High issue was identified. This is not an unconditional merge instruction: require successful checks on the exact final head/PR merge candidate and human acceptance. Do not substitute the earlier checkpoint's green checks for current ones.

Merging this foundation would add the approved technical ADR and deliberately disconnected client infrastructure only. It would not establish working live authentication, real NGO authority, operational privileges, full accessibility/localization acceptance or production readiness. Stop after PR preparation. Recommended next task is human review of this PR, followed by a separately scoped W2 contract/HTTPS readiness assignment—not automatic live integration.
