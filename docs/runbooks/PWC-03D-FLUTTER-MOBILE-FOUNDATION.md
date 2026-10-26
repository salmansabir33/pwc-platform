# PWC-03D — Flutter Mobile Foundation

Date: 26 October 2026.

**Status: BLOCKED BEFORE IMPLEMENTATION — inspection checkpoint only.** No mobile architecture, screen, credential store, client, Flutter project, dependency lockfile or test suite has been implemented by this checkpoint. PWC-03D is not complete. The sections below record verified prerequisites and the continuation contract, not delivered functionality.

## Repository and authority

Active branch `arena/f54f895c-pwc-platform` began clean at `0445840ab5d0850169d20e9a90099ab8b0c13cc6`, equal to freshly fetched `origin/main`. GitHub reports PRs #3–#6 merged. After fetching the existing shallow history, local ancestry checks confirmed their merge commits:

| PR  | Foundation       | Merge commit                               |
| --- | ---------------- | ------------------------------------------ |
| 3   | Authentication   | `889fc2f6a6bddd384bcf7c3f907eb693459ddfd1` |
| 4   | Authorization    | `cb4ae6c7c1b7f08bd8b6c4a5b5a0a304f1276445` |
| 5   | Web              | `cf82dec7adfc6f57e1152cabc6d1f0491d09a5b7` |
| 6   | Shared contracts | `0445840ab5d0850169d20e9a90099ab8b0c13cc6` |

Inspected root AGENTS, [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), the Flutter architecture, IA, detailed screen specification, Strategic/Product Foundation, approved auth/authorization/web ADRs, Django route/adapters and PWC-03C contracts/runbook. Historical scaffold statements do not supersede the current task authorization. No approved decision or product status is altered.

`apps/mobile/` contains only its reserved-path README. There is no existing Flutter source or lockfile to overwrite. Keep this path; do not copy the architecture draft's illustrative alternate directory name.

## Confirmed environment blocker

- `flutter` and `dart` were not found on PATH; a bounded search of `/opt`, `/usr/local` and `/home/user` found no executable installation.
- `java`, `adb`, `sdkmanager` and `xcodebuild` were not found on PATH. Absence on PATH alone is not proof that every possible SDK location was searched; no usable installation was identified.
- Direct HTTPS connection attempts to `https://pub.dev` and the official Flutter release metadata URL under `https://storage.googleapis.com/flutter_infra_release/flutter/releases/` failed with curl exit 35 (`SSL_ERROR_SYSCALL`). No credentials were sent.
- GitHub source access works. The upstream Flutter `bin/internal/update_dart_sdk.sh` explicitly downloads the Dart SDK from `storage.googleapis.com` by default. Flutter's cache implementation also uses that artifact host. A source checkout alone is not a runnable, dependency-resolved SDK.
- No unreviewed mirror, hand-written fake lockfile, downloaded toolchain binary in Git or unvalidated replacement credential library was introduced.

This is an acquisition/validation dependency, not a request to reapprove ordinary Riverpod/go_router decisions or split PWC-03D into smaller user-facing tickets. Resume the same complete assignment when a verified Flutter toolchain and package-resolution environment are available. GitHub-hosted Flutter validation is a possible future execution environment, but no mobile workflow or remote Flutter bootstrap was configured or tested in this checkpoint; existing backend/web CI is not mobile validation.

### What is needed to resume

Provide either a Flutter-capable development environment with access to the official SDK artifacts and Dart packages, or a verified offline Flutter/Dart SDK plus compatible package cache. Native acceptance additionally needs Android SDK/JDK/emulator or devices, and macOS/Xcode with iOS simulators/devices. Pin and verify the chosen stable SDK and package versions when they can actually be resolved and tested; this document intentionally does not invent version pins.

## Intended architecture — not implemented

The task authorizes feature-oriented Flutter/Dart, Riverpod DI/state and go_router. Separate:

- `lib/app/`: composition, router/redirects, lifecycle integration and locale selection.
- `lib/core/`: environment restrictions, typed contracts/transport, safe errors, secure credential/session abstractions and cancellation/generation fencing.
- `lib/design/` and localization resources: semantic reusable fields/buttons/feedback, responsive layouts, English and early Urdu/RTL.
- `lib/features/`: identity flows, personal summary, personal security/MFA/session management and an explicitly unavailable NGO-workspace surface.
- `test/`: deterministic model/controller/storage/transport/router/widget tests; `integration_test/` for separately evidenced native integration.

Choose maintained compatible dependencies and commit the resolver-produced lockfile, not manually guessed checksums. Prefer a bounded set of consumed DTOs from the canonical schema over a broad unused generated SDK. No generated source, package selection or architecture conformance is claimed yet.

## Verified contract boundaries

Canonical contract: `packages/api-contracts/openapi-v1.json`, OpenAPI 3.1, release 1.0.0, **32 paths / 47 operations / 39 schemas**. Its examples and historical fixtures remain synthetic; schemas do not activate APIs.

- Registration/verification and reset use implemented request/confirm/resend POST routes. Verification precedes password creation. Delivery is synthetic-only; do not promise an actual inbox email, SMS OTP or provider.
- Native login is `POST /api/v1/auth/mobile/login/`; native MFA completion is `POST /api/v1/auth/mobile/mfa/confirm/`. HTTP 202 is preauthentication, not a session.
- Native issuance, MFA completion and `POST /api/v1/auth/mobile/refresh/` must not send browser provenance, cookies or an access Authorization header. Refresh proof is body-only. Later personal requests use exactly one native opaque Bearer credential.
- Personal `me/`, logout, session inventory/revocation/logout-all, MFA enrollment/status/confirmation/removal/recovery-code rotation, personal intents/step-up/hold-clear exist behind default-off configuration. Operation-bound assurance must be obtained and consumed exactly as implemented.
- Password/contact-change APIs and editable rich profile APIs are not implemented. Existing password reset is not permission to invent those routes.
- The four NGO context read endpoints are isolated synthetic-only verification surfaces, not real mobile NGO discovery, administration, memberships or finance. Do not place them into a production workspace switcher.
- Keep backend direct-HTTPS, proxy-trust, expiry, revocation and hold guards intact. W1 web networking remains disabled.

## Screen mapping — planned subsets only

| Canonical ID | Safe task scope after implementation resumes                                         | Not yet available                                         |
| ------------ | ------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| ID-01        | Registration/verification/password creation, native login, MFA preauth and reset     | Live email/provider acceptance; phone/social login        |
| ID-02        | Read-only personal identity/session summary supported by `me/`                       | Rich profile, contact/password mutation endpoints         |
| ID-03        | Clearly unavailable affiliations surface if needed for canonical navigation          | Real membership/volunteer/project relationship discovery  |
| ID-04        | Personal context and isolated switching architecture, explicit unavailable NGO state | Real NGO/PWC/committee workspace access                   |
| ID-05        | Supported personal MFA, assurance, recovery holds and sessions                       | Unimplemented security commands, privileged NGO authority |

No screen in this table is delivered by this inspection checkpoint. Do not manufacture dashboards, memberships, grants or records.

## Credential and transport acceptance to implement

- Native-backed secure storage must fail closed on unavailable/corrupt storage. No token in SharedPreferences, URLs, logs, ordinary files or source control. Keep temporary challenges/passwords/assurance/recovery codes transient and purge them at their display/request lifecycle boundaries.
- Serialize refresh. Persist a coherent versioned credential replacement; test write/read/cleanup failures and crash boundaries. A consumed refresh cannot be replayed safely: ambiguous results require clearing local credentials and re-login, not automatic retry.
- Restore a session only through current backend validation; never authorize a cached identity offline. Respect access expiry (300 seconds), mobile idle expiry (7 days) and absolute expiry (30 days); GET/status/list/refresh is not an idle keepalive.
- Clear local credentials, proofs and private caches on logout/invalidation even if a request fails; do not claim backend revocation without acknowledgement. Cancellation does not prove an unsafe command was rolled back.
- Prevent parallel rotation/logout and late responses from resurrecting credentials. Partition caches by personal/logical session/context/registry/revision/generation and suspend private views during required revalidation.
- Keep restricted and review-required holds distinct. Restricted hold clearance needs a new single-use captured pre-hold factor code; MFA does not grant NGO authority.
- Native backup exclusions, iOS Keychain accessibility/reinstall behavior, Android Keystore loss/restore and installation binding must be implemented and exercised, not inferred from a package name. Screenshot/recording/background-snapshot protection is platform-specific; document iOS limitations and avoid clipboard actions for displayed secrets.
- Use timeouts/cancellation, no-store sensitive transport and safe normalized errors. Bound any safe-read retry; never retry consumed refresh, proof or mutation ceremonies automatically.

## Setup/test/build commands — future, not executable project instructions yet

After provisioning and pinning the actual SDK, scaffold into the preserved reserved path and resolve/pin the selected dependencies. Only then will these application commands be meaningful:

```bash
flutter --version
flutter doctor -v
cd apps/mobile
flutter pub get
flutter analyze
flutter test
flutter build apk --debug
# On a provisioned macOS/Xcode runner:
flutter build ios --no-codesign
```

There is currently no `pubspec.yaml`, so do not report these application commands as run or passed. SDK pinning, generated platform projects, resolver lockfile, CI configuration and actual command results must be added during implementation.

## Required completion evidence

Before the consolidated PWC-03D PR: contract parsing/error/environment tests; registration/reset/login/MFA/hold/session tests; secure-store failure/backup/reinstall/atomic replacement tests; concurrent refresh/logout/stale-completion tests; route and NGO exclusion tests; English/Urdu/RTL/semantics/small-screen widgets; relevant native builds and honest device omissions; dependency/license review; complete internal security review and defect regressions.

This checkpoint changed documentation only. Flutter/Dart analysis, mobile tests and Android/iOS builds are **not run**. Backend/web regressions were not rerun because their implementation and dependencies were not modified; previous CI results must not be presented as mobile evidence.

See [the blocked mobile review record](../reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md). Resume the same PWC-03D assignment after the environment dependency is resolved; do not proceed to NGO onboarding, W2, finance or deployment.

## Environment recovery follow-up

The [environment diagnostic](PWC-03D-FLUTTER-ENVIRONMENT-DIAGNOSTIC.md) supersedes the earlier untested Actions observation: two actual isolated GitHub probe runs now exist, but SDK acquisition failed; no Flutter analysis/test/build ran. Local DNS/TCP work while TLS closes for required artifact/package hosts. A restricted, checksum/revision-validating environment workflow and installer were added, not PWC application CI or mobile implementation. The exact remote HTTP 404 and minimum Linux setup are recorded there. The original `f1adea79` checkpoint remains preserved; PWC-03D is still incomplete and no PR is opened.

## Standard Flutter CI verification update

The [standard-action verification report](PWC-03D-STANDARD-FLUTTER-CI.md) supersedes the earlier unestablished GitHub fallback: conventional pinned `subosito/flutter-action@v2` setup **succeeded**, verifying Flutter 3.35.7 stable / Dart 3.9.2, registry access, dependency resolution, sample formatting/analysis and generated upstream widget smoke testing. The old custom URL contained an extra `/flutter/` segment; its 404 did not prove standard installation impossible. The pinned smoke workflow is retained with scoped main/assigned-branch push and main-targeting PR triggers. This does not implement/test PWC application functionality, prove native builds or remove local Arena restrictions. No PWC-03D completion, security-review completion or merge-readiness is claimed, and no diagnostic-only PR is opened.
