# PWC Design System v1.0 — implementation review

Date: 27 October 2026. Scope: existing NGO React portal, Operations React console,
and Flutter personal-identity client. **Engineering foundation, not live-service
or WCAG certification. Human acceptance is required; no automatic merge.**

## 1. Authority, baseline and boundaries

- Authority: [approved v1.0 specification](PWC_DESIGN_SYSTEM_v1.0.md). PR14 had
  committed its 375 lines as the file `docs/design`. That file is relocated,
  byte-for-byte unchanged, to the intended directory/file. No design approval is
  invented by this implementation review.
- Implementation starts at latest main `9880bd6e76e8a0fe927c42a10bb9f8cb46138514`,
  including merged PR13/04B. Inspected AGENTS, roadmap v2, ADR-0003, Flutter
  architecture, detailed screen specification, IA, current components and tests.
- No backend code, migrations, auth/API contracts, credential mechanisms, session
  invalidation, network activation, provisioning, approval, invitation issuance,
  grants or financial authority changes. Disabled transports remain disabled.
- Historical owner read/withdrawal contract seams remain; public applicant
  intake remains unavailable. No UI status implies NGO, alliance, staff, Board,
  finance or reviewer powers. No invented organizational statistics or records.

## 2. Tokens, typography and parity

`packages/design-tokens/tokens.v1.json` is the versioned semantic source;
`scripts/design_tokens.py` produces `generated.css` and Flutter `tokens.g.dart`.
`npm run tokens:check` detects adapter drift (Dart formatting whitespace ignored,
string contents preserved) and verifies six font/license copies against hashes.
Existing CSS aliases and package entry points remain available. The token package
is version **1.0.0**. No new production component/font-fetch dependencies.

All eleven approved colors are preserved. Companion values, all defined in the
manifest, include independent NGO/Operations hover/pressed, danger hover/pressed,
info/restricted, status backgrounds, disabled text/background and a darker
interactive boundary. Decorative `#D8E1E2` is **not** used as the sole input
boundary. Selection uses brand-soft background plus primary text; unknown,
restricted and unavailable must be named, never treated as success.

Representative measured WCAG sRGB contrast ratios (unrounded values used by tests):

| Foreground / background             |           Ratio | Use                                  |
| ----------------------------------- | --------------: | ------------------------------------ |
| Primary ink / white                 |         13.97:1 | Body/headings                        |
| Secondary text / white              |          6.26:1 | Supporting copy                      |
| NGO primary / white                 |          7.07:1 | Brand/action text and inverse button |
| Operations primary / white          |          8.33:1 | Brand/action text and inverse button |
| Success / success background        |          6.33:1 | Textual status                       |
| Warning / warning background        |          5.86:1 | Textual status                       |
| Danger / danger background          |          5.82:1 | Validation/error                     |
| Info / info background              |          7.36:1 | Info/restricted labels               |
| Disabled text / disabled background |          5.29:1 | Readable unavailable controls        |
| Control boundary / white; canvas    |  3.90:1; 3.63:1 | Interactive boundary                 |
| Focus / white                       |          5.66:1 | 3px visible keyboard ring            |
| White / danger hover; pressed       | 8.42:1; 10.85:1 | Destructive states                   |

Tests also require normal-text AA on white/canvas for the intended semantic
colors, white on every primary/hover/pressed state, and 3:1 control boundaries.
These are intended pairings, **not permission to combine arbitrary tokens**.

- Typography: 12/14/16/20/24/30/36; 16px body, tables at least 14px. Flutter
  TextTheme assigns the corresponding roles/line heights. Web retains responsive
  24–36px main headings, not smaller administrative table text.
- Spacing: 4/8/12/16/24/32/48; radii 6/12/16. Web fields 48px, buttons/links at
  least 44px; native targets 48dp. Layout dimensions remain content-driven; the
  old 1600px wide-screen adjustment is retained alongside 600/900/1200 reflow.
- Borders, focus, elevations and overlay are centralized. Web focus: 3px orange,
  4px offset; Flutter inputs/buttons use explicit focused borders and native
  component semantics. Light only; dark mode deferred.
- English: bundled Inter variable TTF, 876,576 bytes, identical in web/native.
  Urdu: existing pinned Fontsource Noto Sans Arabic Variable web WOFF2 subset,
  165,960 bytes; native full variable TTF, 844,676 bytes. Font-size subsets and
  native shaping engines are not asserted pixel-identical. See
  [immutable font hashes/provenance](../../packages/design-tokens/font-provenance.json)
  and the adjacent OFL-1.1 licenses. Google Fonts assets were retrieved by
  immutable `google/fonts` Git blob via GitHub API; source never runs at runtime.
  No remote runtime font requests. Full TTF adds approximately 0.88MB per static
  portal deployment; compressed Latin-only packaging is a future optimization,
  not silently substituted typography.

## 3. Shared React component contract

Both apps consume the same `@pwc/web-ui` library. Components own presentation,
not session data, network requests, authority, retries or command proof.

| Area       | Implemented reusable API / behavior                                                                                                                                                                                                                                                                                                                                                   |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Actions    | Existing `Button`, with primary/secondary/tertiary/destructive; caller classes retained; busy supplies `aria-busy` and disables duplicate invocation. Native button semantics and default non-submit type retained.                                                                                                                                                                   |
| Fields     | Existing `TextField` honors caller IDs; visible label, linked hint/error, `aria-invalid`, native email/search/password/date/time types and required semantics. Separate visible required marker does not change label text. `TextArea`, `SelectField`, and labeled native `Choice` checkbox/radio use the same boundaries/target language. No custom calendar or unsafe file control. |
| Content    | Existing `Panel`/`Stack`, `Card`, `PageHeader`, textual `Badge`; captioned `DataTable` with scoped headers, real empty row and labeled keyboard-scroll region. No invented sort/filter behavior.                                                                                                                                                                                      |
| Pagination | Disabled absent cursors/callbacks; labels supplied by caller. Business pagination remains the existing server-cursor contract seam.                                                                                                                                                                                                                                                   |
| Feedback   | Existing loading/empty/error `StatePanel`, restricted/unavailable type support, `Banner`, `Skeleton`, associated inline errors, disabled/busy states. Semantic text accompanies color.                                                                                                                                                                                                |
| Modal      | Native `ConfirmDialog`: named dialog, inert modal background, explicit Tab/Shift+Tab cycle, cancel-first focus, Escape cancellation unless busy, return focus and scrollable small-screen bounds. No command executed internally.                                                                                                                                                     |
| Shell      | Logical sidebar/disclosure, skip link, separate accents, named breadcrumbs with actual route destination, localized title, disabled workspace-selector foundation. No first-NGO auto-selection, fake account menu or inferred operator context.                                                                                                                                       |
| Specimens  | Existing `/foundation/accessibility` demonstrates controls and technical token data only, in English/Urdu. Explicitly UI-only; local confirmation result says no command ran. Locale changes clear specimen drafts.                                                                                                                                                                   |

Foundation navigation remains **route navigation**, not fake ARIA tabs. Existing
feature pages inherit the common theme. Controlled onboarding now reuses labeled
date/select fields, without changing synthetic preview, independent-approver or
recipient-binding semantics. Historical withdrawal buttons use destructive presentation without altering their existing command/confirmation contracts. Gated feature headings can receive route focus;
status/alert copy retains its meaning and roles with shared banner styling.

### Advanced/unused component specifications (not an unused framework)

- Tabs: use only for same-page panels; roving tabindex, arrow/Home/End keys,
  `tab`/`tabpanel` relationships, selected state, and focus that survives updates.
  Do not replace route links with tabs or conceal unavailable authority.
- Filtered combobox: implement only with an approved search contract; bounded,
  server-scoped results, explicit label and query state, keyboard navigation,
  announced result/error/loading state, generation-bound cancellation. No mock
  organization choices or automatic first-result selection.
- Switches: only for immediate, reversible settings; visible label plus checked
  state and native touch target. No presentation-only toggle of live networking.
- Toasts: polite live region for confirmed benign updates; alerts for urgent
  failures, no timeout-only critical message. Unknown command outcome stays
  pending/unknown with safe status recovery, never optimistic success.
- Date/time: native labeled fields for existing needs. A future custom picker
  needs keyboard/calendar semantics, explicit timezone and a backend contract.
- Files, charts, financial summaries and bulk admin controls: not instantiated;
  require approved privacy/scan/storage/authorization/data contracts and accessible
  alternatives. A design example is not permission to upload real evidence.

## 4. Flutter equivalent and limits

`pwcTheme(operations: false, urdu: locale)` maps PwcTokens to light ColorScheme,
TextTheme, filled/elevated/outlined/text/icon buttons, input decoration, cards,
dialogs, navigation, app bars, dividers and snackbars. `PwcStatusTheme` supplies
non-Material status semantics. A future authorized Operations surface may request
its accent; no such authority or mobile operator console is enabled now.

`SecretField` retains no-autofill/no-suggestions/no-autocorrect/no-personalized-IME
and selection restrictions; only its local border override is removed so shared
input theming applies. `Notice` stays compatible. Small `PwcBadge`,
`PwcStatePanel` and native `pwcConfirm` helpers provide equivalents without a
component framework. ID-03/04 unavailable views adopt the state panel. Existing
bottom navigation, RTL, lifecycle protection and session redirects remain; the
wide navigation transition now uses the 900dp shared guidance. Touch/text-scaling
checks are widget evidence, not physical-device or screen-reader certification.

## 5. Canonical screen / readiness matrix

| Canonical scope                                                    | React                                                                             | Flutter                                                | Actual readiness after styling                                                                                       |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Foundation shells, specimen, interface states                      | Both independent portals, all existing routes styled                              | Shared Material theme and navigation                   | **UI-only**; specimen interactions functional locally                                                                |
| ID-01 register/sign-in/MFA/recovery                                | Unregistered auth routes remain unavailable                                       | Existing personal identity screens inherit theme       | **Implemented but gated** native transport configuration; no live networking activated; web **not implemented**      |
| ID-02 personal profile                                             | Reference only, not a fabricated profile/dashboard                                | Existing authenticated identity/session summary themed | Native implemented personal subset; broader profile editor deferred; web **not implemented**                         |
| ID-03 affiliations                                                 | Reference only                                                                    | Existing unavailable panel themed                      | Discovery **not implemented**; no membership inferred                                                                |
| ID-04 workspace switcher                                           | Disabled shell foundation; no real choices                                        | Existing unavailable panel and navigation themed       | **UI-only**, real workspace discovery/activation gated                                                               |
| ID-05 privacy/security                                             | Reference only                                                                    | Existing personal security flows inherit theme         | Native implemented personal subset; real-device/security acceptance still independent; web **not implemented**       |
| ORG-01 / ORG-02 registry/provisional workspace                     | Existing registry preparation/history UI styled, all default controls unavailable | Existing registry UI inherits theme                    | **Implemented but gated** contract seams; no public registration/claims, authority or existing-NGO access            |
| ORG-03 verification preparation/status                             | Shared fields/actions/alerts styled; files and transport still unavailable        | Existing preparation UI inherits theme                 | **Implemented but gated**, no evidence acceptance or verification                                                    |
| PWC-01 controlled onboarding / verification review                 | Operations preparation restyled; reviewer command UI remains absent/disabled      | No new operator workflow                               | **Implemented but gated**; independent operator/reviewer, assurance, recipient acceptance, 04C/03B.3 remain separate |
| ORG-04 overview / OPS-01 audit-support-recovery                    | Canonical readiness references, no fabricated business dashboard                  | No new business screen                                 | Business features **not implemented** by this work                                                                   |
| All other canonical NGO/alliance/committee/project/finance screens | No new routes/actions                                                             | No new routes/actions                                  | **Not implemented** here; original roadmap gates unchanged                                                           |

Styling is inherited across present native feature modules, not an assertion that
every screen received independent native visual/device acceptance. Backend-only
contracts and unfinished requirements retain their prior dispositions.

## 6. Browser/visual evidence

Reproducible test: `tests/web/browser/design-system.spec.ts`. Four gated routes
are checked at both 1440px and 320px, in English and Urdu, with browser axe, no
page overflow and disabled/absent command assertions. Foundation tests add
keyboard/skip/route focus, invalid/error association and independent portal state.
Component tests cover names and intended contrast pairs. Font requests remain
same-origin; no API requests are introduced.

Fourteen actual Chromium screenshots are retained in [evidence/](evidence/):

- [NGO desktop overview](evidence/ngo-overview-en-desktop.png) ·
  [Operations desktop overview](evidence/ops-overview-en-desktop.png)
- [NGO dialog/focus](evidence/ngo-dialog-en-desktop.png) ·
  [Operations dialog/focus](evidence/ops-dialog-en-desktop.png)
- [NGO Urdu/320px components](evidence/ngo-components-ur-mobile.png) ·
  [Operations Urdu/320px components](evidence/ops-components-ur-mobile.png)
- NGO registry: `ngo-registry-en-1440.png`, `ngo-registry-ur-320.png`
- NGO verification: `ngo-verification-en-1440.png`, `ngo-verification-ur-320.png`
- Operations controlled onboarding: `ops-controlled-en-1440.png`, `ops-controlled-ur-320.png`
- Operations review: `ops-review-en-1440.png`, `ops-review-ur-320.png`

Agent screenshot inspection checked hierarchy, spacing, accents, modal focus and
narrow-screen RTL clipping; it caught adjacent review links and missing 44px
link targets, which were corrected. Automated modal testing caught a native
browser Tab edge escaping to browser chrome; explicit cycling was added and
retested. These are **not human design approval**, pixel-diff golden baselines,
native screenshots, or evidence of fluent Urdu editorial review. Screenshots
contain no real user/organization data; technical specimen rows are labeled.
CI retains browser screenshots and JUnit for seven days; Git retains this bounded
review selection. Final run/immutable source linkage belongs in the PR evidence
comment, avoiding a self-referential commit hash in this file.

## 7. Executed checks and release gate

Local environment: Node 22.22.3/npm 10.9.8. Native Flutter SDK/Android toolchain
is unavailable in this sandbox; the official pinned CI is the native execution
authority, **not** the temporary WASM formatter used for local source formatting.
Local Chromium 153.0.8010.0 was supplied through the existing executable override
with temporary, untracked runtime libraries; CI installs its pinned Playwright
Chromium normally. No test dependency change is shipped to the applications.

| Check                                                  | Actual observed result                                                                                                                                                                |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `npm run check`                                        | Token/font drift check, TypeScript, Prettier, **130/130** Vitest tests and **both** production builds passed                                                                          |
| `npm run test:browser` with local Chromium override    | **21/21**, zero failures/skips; browser axe WCAG 2/2.1/2.2 AA tags, modal, RTL, reflow, fonts and security boundaries                                                                 |
| `npm run contracts:types:check`                        | Unchanged OpenAPI TypeScript generation passed                                                                                                                                        |
| `npm audit --audit-level=low`                          | **0 vulnerabilities**                                                                                                                                                                 |
| Approved-spec relocation                               | Original main blob equals relocated file hash                                                                                                                                         |
| Latest-main ancestry / whitespace                      | Main ancestor verified; `git diff --check` passed                                                                                                                                     |
| Pinned Flutter CI at source checkpoint `0d6c60f`       | Flutter **3.35.7**, Dart **3.9.2**; clean static analysis; **143 tests passed** (138 preserved plus 5 new/expanded design checks); format and canonical mobile contract checks passed |
| Native dependency review at that checkpoint            | **60** resolved hosted versions, **0** OSV findings; 60 license files reviewed (Apache/BSD/MIT); fonts separately OFL-1.1                                                             |
| Android app/harness build and backend full regressions | Final exact-head results/run links must be confirmed in the consolidated PR evidence comment before merge; not inferred from old PR13 or intermediate checks                          |

Final PR must link successful checks on its immutable head: web, Flutter analysis/
widgets/contract/format/dependency review, Android app and credential-harness
builds, both backend Python/PostgreSQL jobs and their actual counts. Backend is
unchanged but its regressions are still required. An early native analysis run
found three missing braces; fixed, then clean analysis and 143 tests were observed.
Cancelled superseded runs do not count as passing acceptance.

## 8. Remaining acceptance / explicit exclusions

- Human product-owner visual review and PR merge decision; no auto-merge.
- Manual NVDA/VoiceOver/TalkBack, real browser zoom (200% CSS text scaling is not
  equivalent), keyboard/browser matrix and physical-device/native Urdu shaping,
  variable-font weights, text scaling, touch, safe areas and navigation acceptance.
- Full Urdu localization/editorial review, especially existing gated feature copy;
  font readiness and example translation do not prove complete localization.
- Native screenshots/iOS build and performance/device acceptance remain unrun;
  Android build is not a device test. Native widget tests use test rendering and
  do not certify real font glyphs. No broad accessibility-conformance claim.
- No dark mode, charts, custom calendars/comboboxes, upload picker, complex bulk
  tables, real account menu or fake NGO workspace options introduced.
- No 04C/04D work, grant/finance activation, deployment or next roadmap task.
  ADR-0003, security ADRs and E01–18/GM01–12 independent acceptance remain intact.
- AGENTS and the token package README require future frontend tasks to adopt the
  approved visual standard, retain versioned semantics, reuse shared components,
  report exceptions and preserve actual readiness/security gates.
