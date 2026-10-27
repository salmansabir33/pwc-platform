# PWC Design System v1.0

**Project:** Pakistan Welfare Club (PWC) Digital Ecosystem  
**Document status:** Approved product design direction; technical implementation specification  
**Version:** 1.0  
**Date:** 27 October 2026  
**Repository target:** `docs/design/PWC_DESIGN_SYSTEM_v1.0.md`  
**Applies to:** NGO Web Portal (React), PWC Operations Console (React), PWC Mobile Application (Flutter)  
**Authority:** Product design direction approved in the PWC planning discussion. Component implementation, accessibility compliance, and deployment remain subject to testing and review.

---

## 1. Purpose and design principles

PWC Design System v1.0 defines a single visual and interaction language for the PWC Digital Ecosystem. Its approved direction is **Modern Professional SaaS**: trustworthy, clean, efficient, accessible, responsive, and suited to day-to-day NGO administration and public participation.

Principles:

1. **Clarity first.** Prioritize task completion, readable information, and visible next actions over decorative complexity.
2. **Consistent, not identical.** NGO Web, PWC Operations, and Flutter share semantic design rules but may differ in navigation and task density.
3. **Accessible by default.** Target WCAG 2.2 AA for web, practical mobile accessibility, logical focus order, visible state labels, and text scaling.
4. **Trustworthy feedback.** Never represent synthetic data, pending approvals, or disabled actions as operational success.
5. **Least-privilege presentation.** UI capability gates supplement—never replace—backend authorization.
6. **Bilingual readiness.** English-first foundation with Urdu/RTL-aware layouts and separately tracked translation completeness.
7. **Component reuse.** Introduce reusable tokens/primitives before per-screen styling; avoid multiple competing component suites.
8. **Progressive adoption.** Preserve safe existing code and align implemented screens without changing gated functionality.

### 1.1 Application identities

| Surface | Role | Accent | Layout intent |
|---|---|---|---|
| NGO Web Portal | NGO administration and management | NGO Green `#146451` | Desktop-first responsive administrative workspace |
| PWC Operations Console | Restricted platform operations and alliance oversight | Institutional Blue `#354E7A` | Independent, audit-oriented administrative workspace |
| PWC Flutter Mobile | Personal, membership, volunteer and relevant NGO tasks | Contextual green by default; semantic app accents | Mobile-first navigation and touch-friendly content |

All three use the same semantic hierarchy and feedback conventions. Distinct application branding must not imply any additional permission.

---

## 2. Foundations and design tokens

### 2.1 Approved light color palette

| Semantic token | Hex | Intended use |
|---|---|---|
| `brand.ngo.primary` | `#146451` | NGO Portal primary actions and emphasis |
| `brand.ops.primary` | `#354E7A` | PWC Operations primary actions and emphasis |
| `text.primary` | `#192F37` | Primary text and headings |
| `text.secondary` | `#52636B` | Secondary descriptions and supporting metadata |
| `surface.canvas` | `#F5F7F7` | App/page background |
| `surface.default` | `#FFFFFF` | Cards, dialogs, fields and standard surfaces |
| `border.default` | `#D8E1E2` | Separators and field/card borders |
| `focus.indicator` | `#AD480A` | Keyboard focus indicator |
| `status.success` | `#146451` | Success semantics, always with text/icon |
| `status.warning` | `#8A5200` | Warning semantics, always with text/icon |
| `status.danger` | `#B42318` | Error/destructive semantics, always with text/icon |

The palette above is **approved**. Companion token values for hover/pressed, status backgrounds, disabled controls, selection, info, charts and dark mode are **implementation-derived** and must be tested for contrast and documented before use. Never assume all combinations of approved colors pass contrast. Use labels/icons alongside color for critical states.

### 2.2 Theme modes

- **v1.0 default:** Light mode.
- **Dark mode:** Deferred; use semantic tokens rather than direct color literals so it can be added later without large component rewrites.
- Each React surface has its own primary accent but shares all neutral/status token meanings.
- Flutter maps to the same semantic token categories through `ThemeData` / `ColorScheme` and app theme extensions.
- Do not hardcode arbitrary brand colors in feature modules.

### 2.3 Typography

| Attribute | v1.0 standard |
|---|---|
| English family | Inter-first, with system sans-serif fallbacks |
| Urdu family | Noto Sans Arabic Variable with licensed, self-hosted font assets |
| Editorial Urdu | Nastaliq may be evaluated for selective editorial/branding content, not default administrative controls |
| Type sizes | `12, 14, 16, 20, 24, 30, 36px` |
| Body text | 16px base |
| Administrative tables | Normally 14px or larger |
| Weights | Use a restrained regular/medium/semibold/bold hierarchy |
| Alignment | Language-aware; do not force all RTL content into left-aligned containers |
| Number/identifier handling | Isolate mixed LTR strings in RTL contexts (`bdi` or equivalent) |

**Recommended role mapping** (implementation guidance; size values above are approved):

| Text role | Size | Suggested line height | Weight |
|---|---:|---:|---|
| Caption / metadata | 12px | 16–18px | Regular / medium |
| Table / supporting text | 14px | 20px | Regular / medium |
| Body | 16px | 24px | Regular |
| Section heading | 20px | 28px | Semibold |
| Page heading | 24px | 32px | Semibold |
| Major heading | 30px | 38px | Semibold |
| Display / hero | 36px | 44px | Bold |

Avoid truncating essential labels, permission states and financial amounts. Layout must adapt to user text scaling.

### 2.4 Spacing, shape and density

- Approved spacing: **4, 8, 12, 16, 24, 32, 48px**.
- Approved radii: **6px (small), 12px (medium), 16px (large)**.
- Standard form field height: **44–48px**.
- Interactive targets: **at least 44 × 44 CSS px on web**, with platform-equivalent accessible Flutter targets or documented compliant exceptions.
- Define semantic border thickness and elevation/shadow levels centrally. Prefer subtle separators and surfaces to heavy shadows.
- Maintain comfortable defaults; use deliberate compact density for large administrative tables without sacrificing legibility or target usability.

### 2.5 Iconography and imagery

- Adopt **one consistent outline icon style**, normally 20–24px; smaller decorative icons may be used where appropriate.
- Keep stroke width, alignment, metaphors and active/disabled appearance consistent. Prefer an existing well-maintained library rather than assembling competing icon sets.
- Label icon-only interactive controls accessibly; do not rely on icon shape alone for critical state.
- Illustrations and photography should be purposeful, respectful of NGO beneficiaries' privacy, and never imply a real endorsement or verified fact without authorization.
- Avoid decorative motion or images that increase initial download cost without functional value.

---

## 3. Components and interaction patterns

Each component must document its anatomy, variants, states, keyboard/touch behavior, accessibility semantics, localization and responsive behavior. Build advanced variants as actual workflows require them.

### 3.1 Buttons and actions

- **Primary:** one dominant action per task region.
- **Secondary:** lower-priority action, usually outlined/neutral.
- **Tertiary/text:** navigation or low-impact action.
- **Destructive:** distinct styling with confirmation appropriate to impact.
- Standard states: default, hover (web), focus-visible, pressed, disabled, busy/loading and complete/error feedback.
- Loading state blocks duplicate submissions where appropriate, but only server acknowledgement establishes success.
- Risky actions must show scope, target and consequences; do not require confirmation for every benign click.

### 3.2 Form controls

Standardize text fields, text areas, email/telephone inputs, passwords, selects, checkboxes, radios, switches, date/time fields, file selection where approved, search and filtered selection.

- Persistent visible labels; placeholder text is not the only label.
- Hint/error text linked semantically to fields.
- Required/optional indication consistent across applications.
- Validate at appropriate times, preserve safe inputs on recoverable errors and display server-authoritative failures.
- Do not automatically collect or persist sensitive documents when a workflow is explicitly offline.
- Security secrets are ephemeral and must not enter logs/analytics.

### 3.3 Content and data display

- **Cards:** concise title, context, status and relevant actions; avoid dense nested card layouts.
- **Data tables:** descriptive header/caption, sorting only where supported, server-scoped filtering, pagination, empty state, horizontal overflow when necessary and keyboard-operable controls.
- **Status chips/badges:** textual state + semantic color; registered, PWC-verified, organization eligibility, representative mandate and alliance membership are distinct concepts.
- **Timelines/audit summaries:** chronological readable events with actor role, time and scope only where authorized.
- **Money amounts:** localize display; keep authoritative arithmetic server-side and use exact decimal-safe models.
- **Charts:** use only for meaningful measured data; give text summaries and accessible alternatives.

### 3.4 Feedback and overlays

Standardize:

- Page/section loading states, skeletons, empty states, permission-denied and service-unavailable states.
- Inline form errors, banners, transient toast messages and confirmation dialogs.
- Pending/unknown outcomes for sensitive commands when the network response is inconclusive; never optimistically claim verification or financial approval.
- Dialog focus management, escape behavior, background interaction blocking and return focus.
- No misleading simulated onboarding approvals, verified badges or fabricated dashboard statistics.

### 3.5 Navigation

- Navigation mirrors approved information architecture and canonical screen IDs.
- Clearly identify current destination, active NGO context, role-relevant sections and location in multi-step workflows.
- Show a safe access-unavailable state for deep links lacking authorization; do not reveal private resource existence.
- Workspace switching must clear or invalidate old-context private UI state before rendering a new workspace.
- No automatic selection of the first NGO as an authority decision.

---

## 4. Application layout specifications

### 4.1 NGO Web Portal — React

Use the NGO green accent with a responsive administrative shell:

- Left sidebar on spacious layouts; accessible disclosure navigation on narrow layouts.
- Header with page/app identity, current organization and relevant account controls.
- Breadcrumbs when hierarchy benefits the user.
- Page title, concise description and one obvious primary action.
- Reusable summary-card, filter/search, table, detail and edit-form patterns.
- Distinguish organization verification status from platform capability and public publication permission.
- Do not show functional screens or links to unimplemented or unapproved NGO privileges.

### 4.2 PWC Operations Console — React

Use Institutional Blue, a separate build/session/navigation tree and an audit-oriented admin shell:

- Clear operator context, action boundaries and restrictions.
- Controlled offline-verification record presentation and review-state displays only as permitted by currently approved command contracts.
- Visible initiator/approver distinction in the UI, with actual separation enforced on the server.
- Explicit records of pending, approved, rejected, returned and disabled status where backed by approved APIs.
- Never infer authority from Board membership, generic staff flags or framework superuser status.
- No built-in universal NGO-private data access.

### 4.3 PWC Mobile App — Flutter

- Mobile-first hierarchy with bottom navigation for approved high-frequency destinations.
- Use `ThemeData`, `ColorScheme`, `TextTheme`, component themes and reusable widgets aligned with web semantic tokens.
- Cards, forms, touch targets and feedback suitable for small screens.
- Direction-aware widgets and text scaling, including Urdu/RTL presentation.
- Dense operator consoles and complex imports may remain web-only; do not duplicate every admin feature on mobile.
- Security/authority boundaries remain backend-enforced; mobile screen availability does not confer permission.

### 4.4 Responsive behavior

Suggested design-breakpoint starting points: **600px, 900px, 1200px**. These are implementation guidance, not hard assumptions about devices. Choose actual changes based on content reflow and testing.

- Test web layouts at 320px width and larger, including browser zoom and text scaling.
- Tables may scroll horizontally in a labeled, keyboard-accessible region rather than shrinking unreadably.
- Headers/navigation collapse gracefully; no horizontal overflow for standard forms/cards.
- Preserve touch-friendly actions on mobile-sized browser windows.

---

## 5. Localization, accessibility and inclusive UX

### 5.1 Language and RTL

- The current foundation is English-first with Urdu/RTL readiness; **complete Urdu coverage is not implied**.
- Keep source strings in typed localization resources where practical; no business text embedded in generic component internals.
- Use logical CSS properties on web and `Directionality`-aware Flutter widgets.
- Switch root text direction where appropriate while isolating dates, emails, IDs, URLs and other LTR runs.
- Test real Urdu shaping, line height, labels, form errors and navigation in native browsers/devices.
- Format local Pakistani time and currency for display without altering server-authoritative UTC timestamps or numeric models.

### 5.2 Accessibility acceptance

Target WCAG 2.2 AA for web and equivalent practical Flutter accessibility:

- Verify contrast for all new foreground/background combinations (including states).
- Provide visible keyboard focus and predictable tab order.
- Use semantic headings, labels, field error associations and accessible names.
- Support screen readers, keyboard navigation and appropriate touch targets.
- Support reduced motion where animation exists.
- Check large-text overflow, zoom, English/Urdu RTL, empty/error/disabled states and small-screen reflow.
- Use automated axe/browser and component tests **plus manual keyboard, screen-reader and Urdu/device reviews**; automated passes are not proof of complete conformance.

---

## 6. Engineering implementation contracts

### 6.1 React web foundations

Existing architecture: two independent **React + TypeScript + Vite** applications, with shared source packages and separated runtime state.

Expected locations (verify actual repo layout before changes):

- `packages/design-tokens/`: approved semantic tokens and foundational CSS.
- `packages/web-ui/`: accessible presentational components and layout patterns.
- `packages/web-i18n/`: locale resources and direction handling.
- `apps/ngo-web/`: NGO Portal routes, feature-specific UI and application shell.
- `apps/pwc-ops/`: PWC Operations routes, feature-specific UI and application shell.

Implementation rules:

1. Source core tokens centrally; avoid duplicated hardcoded hex values and arbitrary spacing.
2. Both web applications should use shared primitive components but distinct portal navigation and accent contexts.
3. Preserve disabled API-network posture unless a separately accepted integration contract authorizes activation.
4. Do not install a new complex UI framework by default; use native accessible controls or proven supporting libraries for demonstrated needs.
5. Avoid local authorization inference from display roles; the backend remains authoritative.
6. Keep permission/recovery/loading/unknown-outcome patterns reusable but not falsely operational.

### 6.2 Flutter foundations

Expected app path: `apps/mobile/` (inspect actual package structure).

Implement or align:

- Central semantic palette mapping with NGO/PWC contextual accents.
- `ThemeData`, `ColorScheme`, `TextTheme`, shared spacing/radius constants, and standard component themes.
- Reusable accessible button, input, card, badge, state and navigation widget patterns based on demonstrated needs.
- Direction-aware RTL styling and scalable text.
- Tests that compare approved semantic token values/roles to their web equivalents through a maintained manifest or explicit mapping.

**Share definitions and meaning across React and Flutter—not widget source code.**

### 6.3 Design tokens and versioning

Maintain a canonical readable manifest or equivalent spec for semantic colors, scales and component choices. Prefer generated/adapted platform token sources if the build system justifies them; do not introduce unnecessary generation complexity.

Changes to approved foundational values require recorded product/design approval and impact review. Implementation-derived interaction tokens require contrast and regression review, but do not automatically constitute a new major design-system version.

---

## 7. Screen completion and quality gates

Every relevant frontend feature must have a traceable record:

| Field | Required evidence |
|---|---|
| Canonical screen ID | Match approved PWC screen specification |
| Surface | NGO Web / PWC Operations / Flutter |
| Route and context | Correct screen destination and organization/portal context |
| Design-system use | Shared tokens, reusable components and documented exceptions |
| API readiness | Backend contract and integration status (or explicitly gated) |
| Interaction states | Loading, empty, error, restricted, success and unknown where applicable |
| Accessibility | Keyboard/touch, semantics, focus, contrast, text scaling and RTL checks |
| Responsive behavior | Browser/device evidence for actual supported sizes |
| Tests | Component, contract, browser/device and relevant end-to-end coverage |
| Readiness label | `fully functional`, `implemented but gated`, `UI-only`, `backend-only` or `not implemented` |

**A visually complete screen does not equal a working business feature.** For full feature completion, required backend behavior, frontend behavior, secure integration and acceptance tests must all be satisfied. Gates must be explicitly shown, not reclassified silently.

### 7.1 Mandatory regression and review

For design-system implementation and later changes, run relevant:

- TypeScript typecheck and web builds for **both** independent portals.
- React component/unit/contract and browser regression tests.
- Keyboard/contrast/axe checks, including representative screens and 320px reflow.
- Flutter static analysis, widget tests, localization/RTL and supported Android builds.
- Cross-platform token parity checks.
- Manual visual review and representative screenshots, including Urdu where applicable.
- Security-sensitive tests for navigation, no false authority, and disabled workflow integrity.

Record actual commands/results. Never claim a test ran because it is listed in the acceptance plan.

---

## 8. Migration and governance

### 8.1 Adoption plan

1. Inventory current React/Flutter styles, shared controls and canonical screen mapping.
2. Align existing token implementations with this approved document.
3. Add missing semantic/component variants when current screens need them.
4. Refactor safe existing screens incrementally without regressing role isolation or disabled workflows.
5. Validate accessibility, RTL, responsive behavior and cross-platform parity.
6. Record open issues without claiming complete app implementation.

### 8.2 Governance

- This document is the v1.0 product visual standard for future PWC frontend work.
- ADR-0003 continues to govern **web technical architecture**; approved security/auth decisions and canonical screen IDs remain authoritative in their domains.
- Feature-specific requirements cannot silently override security gates or organizational authority policy.
- A reusable component or token is preferred to unique screen styling; exceptions need written justification.
- Significant palette/typography/navigation changes require product-owner approval and appropriate versioned documentation.
- Every future comprehensive Arena/Codex subphase prompt should reference this file, require frontend coverage, and report actual readiness.

### 8.3 Explicit exclusions

This design system **does not**:

- Activate live NGO onboarding, verification officers, invitations or real grants.
- Approve real API networking, deployment, privileged commands or private document storage.
- Authorize finance/signatory/alliance authority.
- Complete every canonical screen, fully localize Urdu or certify WCAG conformance.
- Introduce an unapproved new roadmap phase or change the existing P0–P8/subphase structure.

---

## 9. Definition of done for Design System v1.0 implementation

The repository-level implementation is review-ready when:

1. This specification is committed under `docs/design/` and referenced from the project development guidance.
2. Core semantic colors, typography, spacing and radii are consistently represented in React and Flutter.
3. Existing shared UI primitives support the documented interactions and accessibility standards relevant to present screens.
4. Current applicable screens are aligned or individually listed as exceptions/deferred work.
5. Both React builds and Flutter checks pass; browser/accessibility and cross-platform token-parity evidence is recorded.
6. A review file states exact implementation coverage, remaining gaps, visual evidence and any manual review still needed.
7. Security and integration gates remain unchanged unless separately approved.
8. A consolidated PR is available for human review; merge is not automatic.

---

## 10. Related repository specifications

- `docs/decisions/ADR-0003-web-frontend-architecture.md` — approved React web architecture and integration gates.
- `docs/runbooks/PWC-W1-WEB-FOUNDATION.md` — existing web token/accessibility foundation and implementation status.
- `docs/product/PWC_Flutter_Frontend_Architecture_v1.0_Draft.md` — Flutter structure and design recommendations.
- `docs/product/PWC_Detailed_Mobile_and_Web_Screen_Specification_v1.0_Draft_for_Review.md` — canonical screen definitions.
- `docs/product/PWC_App_Information_Architecture_and_Navigation_v1.0_Draft.md` — application navigation and context model.
- `packages/design-tokens/tokens.css` — current web token implementation, to be brought into v1.0 compliance.

**Document control:** PWC Design System v1.0 is the approved design direction. It is **not** evidence that code changes or repository PRs have already been created.
