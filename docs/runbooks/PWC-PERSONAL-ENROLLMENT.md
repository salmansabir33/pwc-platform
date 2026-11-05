# Separate personal enrollment — Founder and AbuBakr

## Current delivery boundary

**Policy update (5 November 2026): initial enrollment is invitation-only.** Public
registration is now test-profile-only. No accepted personal-invitation issuer or
recipient/state/privacy contract exists, so issuance/acceptance stays unavailable.
See [controlled enrollment readiness](PWC-CONTROLLED-ENROLLMENT-READINESS.md) for
exact gates, the unwired SMTP adapter and staging preparation. Registration form
instructions describe synthetic regression only, not a public real-user path.

The React `/account` and `/account/confirm` screens now implement registration,
password reset, explicit proof/password confirmation and first-factor MFA setup.
They reuse the existing personal login, MFA challenge and session/history panel.
EN/UR, keyboard labels, generic errors and accessible status messages are included.
Flutter already implements these identity/security ceremonies; this change adds
a two-account regression rather than a second native authentication system.

**Actual enrollment is not enabled by this change.** The shipped browser route
has no injected credentialed transport; its controls truthfully remain disabled.
The Django public-flow flags remain off by default. Delivery is hardcoded locmem
and `flow_security.configured()` rejects non-synthetic delivery modes. Changing
`EMAIL_BACKEND` or supplying a native origin cannot enable accepted real delivery.
No approved recipient-bound _personal-account_ invitation alternative was found;
NGO representative invitation acceptance is a separate contract, not a bootstrap.
No real accounts, grants, delivery provider, migration or deployment are created.

To reach real enrollment requires these exact implementation/acceptance items:

1. ADR-0001 O1/O2: approved provider/region/sender/deliverability and delivery budget,
   abuse controls, worker operation, plus a reviewed replacement for the synthetic
   delivery adapter and its explicit mode guard. Do not retrieve a real person's
   proof from an outbox, database or logs as a workaround.
2. O4 real-user privacy/notices/eligibility/retention; O3 and ADR-0003 ingress,
   exact HTTPS link/portal origins, host/cookie/CSRF trust and operational controls.
3. W2 reviewed browser composition that explicitly supplies same-origin transport
   to `PersonalWorkspaceSession`, with actual browser/server acceptance for
   delivery links, cookies, rotation, expiry, lost responses and cross-tab erasure.
   Neither public registration nor live networking is authorized by the new UI.
   If the accepted rollout is invitation-only, implement/review that contract
   instead of turning unrestricted public registration on.
4. Explicit authorization before any Contabo deployment or real credential use.
   Staging preparation permission is not deployment permission. Normal CI/review
   gates still apply; Issue #40 remains unsuppressed.

These are personal-account delivery/transport gates, **not** a demand to complete
Founder/independence verification before an ordinary personal account can exist.

## Founder — future invitation recipient (not yet available)

1. Use your own inbox and browser/device. Wait for a recipient-bound invitation
   from an accepted issuer after the invitation contract is implemented/reviewed.
   Do not use public registration, an operator-supplied database proof or a shared
   invitation. The invitation recipient journey is not yet executable.
2. In the future accepted recipient flow, open only your own received link.
   Opening must not confirm an account or log you in. Choose your own unique password and confirm
   explicitly. Never send the password/proof to AbuBakr, an operator or an agent.
3. Sign in explicitly with the existing personal login form; then follow the MFA
   procedure below. Check your personal sessions and sign out on shared devices.
4. Keep the resulting personal account ID for the separately accepted identity and
   appointment-binding process. Do not put private identity evidence in Git/chat.
   The account has no Founder, staff, superuser, issuer, NGO or private-data grant.

## AbuBakr — separately, future invitation recipient

1. Use **your own** inbox, browser/device, unique password and separate invitation
   from the accepted issuer. Do not reuse the Founder's flow, credentials or seed.
2. Confirm only your own received proof and personally chosen password; sign in
   explicitly and enroll your own MFA as below. Check only your own sessions.
3. Your ordinary personal account is not independent-verifier activation. The
   Founder nomination and an account's existence do not establish distinct-person
   identity, independence, non-conflict, trusted issuer acceptance or review power.

Canonical duplicate email confirmation is rejected, not linked or overwritten;
request/resend messages avoid account enumeration. Email/name/GitHub ownership is
not a distinct-human check and never confers institutional authority.

## Personal MFA and recovery procedure — each person independently

- While signed into your own normal, clear-hold personal session, enter your own
  current password in the first-authenticator form. It requests the existing
  `mfa.enroll` personal intent and password step-up; it cannot replace an existing
  factor or bypass recovery restrictions. Existing factor management stays in
  the established security flow, not this first-enrollment form.
- Add the displayed secret to your own authenticator as time-based TOTP, six
  digits, 30 seconds. No external QR service receives it. Enter its current code
  and activate. Password entry and authenticator activation are explicit actions.
- Save the ten one-time recovery codes privately offline. They are shown only
  after confirmed activation and are not persisted by this screen. Select the
  hide button when saved; display also clears after five minutes, locale change,
  visibility/page exit, logout/invalidation or unmount. Pending enrollment secrets
  expire at the server deadline, with a five-minute maximum UI retention.
- Never share seed, password, proof, assurance proof or recovery codes. Recovery
  login remains restricted; a reset does not remove an active factor or grant
  authority. Do not repeatedly retry an uncertain MFA activation: check the
  established server MFA/security status and use its reviewed recovery path.

## Reuse and test boundaries

- Django `registration.py`/views, `delivery.py`, `mfa.py`/views, personal intents,
  step-up, CSRF/session/epoch handling, recovery holds and security audit are reused
  for credential/session/recovery semantics. A non-test public-registration guard
  now enforces invitation-only rollout; no invitation writer, provider wiring or
  migration is added.
- `PersonalEnrollmentClient` is explicitly injected, fixed-path, no-store,
  fresh-CSRF-per-POST and generation-fenced. It does not widen the foundational
  API allowlist. Proof links are scrubbed before parsing; no query-string proof,
  automatic confirmation, automatic login, role field or privilege operation.
- Tests: `accounts.test_personal_enrollment` exercises two real PostgreSQL users,
  distinct passwords/factors/sessions, duplicates, role injection, foreign personal
  context and cross-account session denial, replay and reset/hold preservation.
  `tests/web/personal-enrollment.test.tsx` covers transport gates, request/reset,
  fragment handling/StrictMode, expiry, cancellation, uncertainty, EN/UR axe checks,
  MFA activation, secret erasure and one-time recovery display. The new native
  regression uses the existing controller/fakes; CI must run its pinned SDK checks.
- Commands: `npm run check`, `npm run contracts:types:check`; with disposable
  PostgreSQL and the test profile, from `apps/backend`, `python manage.py test
accounts.test_personal_enrollment` and the full contract-instrumented suite;
  from `apps/mobile`, `flutter analyze` and `flutter test` with the pinned SDK.
  Test results do not establish actual email, browser-ingress or device acceptance.

## Verification and authority remain separate

Use existing Issue #42 for the exact trust dependencies. Account ownership,
identity/distinct-natural-person checks, appointment/responsibility binding,
independent nonconflicted review and trusted founding-source/issuer acceptance
remain separate steps. No protected writer/evidence upload is introduced here.
C1 R01–R08, locked04C §12/F1–F9/E05, the four-field public projection and all
protected activation/disclosure/finance gates are unchanged. The Founder cannot
self-verify; AbuBakr's separate account alone is not evidence of independence.
