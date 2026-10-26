# PWC-03D — Flutter Mobile Identity & Application Foundation

Date: 26 October 2026. Same comprehensive PWC-03D assignment, not a new subphase.

## Status and provenance

Actual mobile source now exists in `apps/mobile`; the prior **blocked-before-implementation** verdict is historical. Required checkpoint `aa1c41c506f068521fb327124a1b7bbf8a18a07a` and the earlier `f1adea79` diagnostics are preserved as ancestors. No reset, force push, backend/web/ADR change or new API is authorized by this work.

The [environment diagnostic](PWC-03D-FLUTTER-ENVIRONMENT-DIAGNOSTIC.md) and [standard setup evidence](PWC-03D-STANDARD-FLUTTER-CI.md) remain retained. Local Arena cannot execute Flutter; GitHub-hosted Ubuntu is the execution environment. The initial real-project [run 40270238837](https://github.com/salmansabir33/pwc-platform/actions/runs/40270238837) passed analysis, **95 actual PWC tests**, hosted-package review and Android debug compilation. This was a bootstrap checkpoint, not the final strict formatting/lockfile gate. Final evidence is recorded in the [integration review](../reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md).

PWC mobile is not production deployed. Live delivery, rich profiles, NGO workspaces and device-security acceptance are not manufactured by this foundation.

## Toolchain and dependencies

- Flutter **3.35.7 stable**, framework revision `adc901062556672b4138e18a4dc62a4be8f4b3c2`, bundled Dart **3.9.2**.
- `subosito/flutter-action@1a449444c387b1966244ae4d4f8c696479add0b2` (maintained v2); official HTTPS SDK storage, caches disabled. This action does not independently enforce SDK archive SHA256; installed framework revision/version/channel are asserted. Do not attribute the historical custom installer's checksum validation to this action.
- Direct pins: Riverpod 2.6.1, go_router 16.3.0, flutter_secure_storage 9.2.4, http 1.5.0; Flutter SDK localization/test/integration_test packages and flutter_lints 5.0.0. These are tested exact baseline pins, not claims to be the newest package releases. Riverpod's non-codegen ChangeNotifier provider API avoids generated state/tooling drift.
- `pubspec.lock` is real Flutter/Dart resolver output recovered from CI, with published package SHA256s; no guessed lockfile. All platform templates originate from the exact pinned `flutter create` command, then receive reviewed native hardening. No SDK/cache/signing key is committed.
- Android: Temurin JDK 17; SDK platform 36 and NDK 27.0.12077973 (verified against the pinned Flutter `FlutterExtension.kt`), build-tools 35.0.0. Release signing is deliberately unconfigured; release is not silently debug-signed.
- Supported generated hosts: Android (minimum SDK 24 from Flutter) and iOS (template deployment target 13). No Flutter Web or Linux desktop delivery is approved by this implementation.

## Architecture

| Area                                | Responsibility                                                                                                                              |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `lib/app`                           | Riverpod dependency composition, go_router redirects, locale state, lifecycle cover, adaptive personal shell                                |
| `lib/core/contracts.g.dart`         | 32 deterministic typed models/nested models and 22 consumed personal operations, generated from canonical PWC-03C                           |
| `lib/core/contract_validation.dart` | Required/extra-field/type/union/enum/UUID/time and bounded-value validation; safe exceptions                                                |
| `lib/core/api.dart`                 | HTTPS native transport, operation allowlist, JSON/status checks, size/total timeout limits, no cookies/provenance/redirects/retries/logging |
| `lib/core/storage.dart`             | One versioned native encrypted credential record, native generation binding and read-back verification                                      |
| `lib/core/session_controller.dart`  | Serialized authentication/refresh/commands, server-validated identity, stale-result fencing, transient challenges, context clearing         |
| `lib/features`                      | Identity ceremonies; read-only personal profile; explicit unavailable affiliations/workspaces; personal security                            |
| `lib/design`                        | Accessible labeled secret fields and safe live-region feedback                                                                              |
| `test`                              | Canonical examples, transport/model/controller/storage-channel/navigation/widget/localization tests                                         |
| `integration_test`                  | Real native-vault lifecycle harness with synthetic API; requires device/emulator, not counted as executed unit/widget coverage              |

All private caches are memory-only and scoped to a disposable generation. Every actor/session restoration, invalidation, context attempt and navigation switch clears the generation. There is no active NGO cache/registry: organization activation is explicitly denied. Future private-context code must add actual server-granted contexts and context/registry-revision keys, not turn this denial surface into synthetic discovery.

## Implemented canonical screens and flows

| Screen | Delivered behavior                                                                                                                                                                                                                                                 | Honest boundary                                                                                                                                             |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ID-01  | Native email/password sign-in; 202 preauth; TOTP or recovery-code completion; registration request/resend/proof+password confirmation; reset request/resend/proof+new-password confirmation; cancellation/expiry/error states; cold/explicit resume                | Synthetic backend delivery only. No inbox/SMS/social promises, deep-link proof ingestion or credential-bearing URLs                                         |
| ID-02  | Backend `me` identity UUID, session UUID/absolute expiry, verification and recovery hold status, local/server sign-out result                                                                                                                                      | Read-only; API does not expose rich profile/email/contact editing or password-change commands                                                               |
| ID-03  | Affiliations unavailable explanation                                                                                                                                                                                                                               | No fake memberships, volunteering or relationships                                                                                                          |
| ID-04  | Explicit personal context and unavailable NGO workspace surface; context invalidation architecture                                                                                                                                                                 | Does not call synthetic NGO discovery/capability/probe/settings endpoints; no Board/staff/admin shortcut                                                    |
| ID-05  | MFA status; operation-bound password/TOTP assurance; enrollment secret/manual authenticator confirmation; one-time recovery-code display/rotation; factor removal; session inventory/revocation/logout-all; restricted-hold clearance; review-required explanation | Personal MFA is not NGO authority. Review-required recovery cannot be cleared by factor codes. User-controlled device labels/server messages are not echoed |

The personal shell uses a navigation rail on wide layouts and bottom navigation on narrow layouts, scrollable width-bounded forms, native Material touch targets, semantic labels/live feedback, explicit English/Urdu selection and Flutter RTL localization delegates. No NGO onboarding/W2/finance/operations feature is enabled.

## Contract consumption

Canonical source remains `packages/api-contracts/openapi-v1.json`, OpenAPI 3.1 / release 1.0.0, 32 paths / 47 operations / 39 schemas. It is unchanged. The generator binds its SHA256 and consumes only 22 native/public-personal operations; 40 canonical positive request/response examples exercise the consumed subset.

Consumed IDs: `registrationRequest`, `registrationResend`, `registrationConfirm`, `resetRequest`, `resetResend`, `resetConfirm`, `mobileLogin`, `mobileMfaConfirm`, `mobileRefresh`, `me`, `logout`, `sessions`, `revokeSession`, `logoutAll`, `mfaStatus`, `createIntent`, `stepUp`, `enrollMfa`, `confirmMfa`, `removeMfa`, `rotateRecovery`, `clearHold`.

No native call can invoke browser login/CSRF, synthetic NGO context APIs, arbitrary URL paths, role/capability fields or unavailable mutations. Request bodies and status-dependent responses are checked against the consumed canonical schemas. A 202 response is never a session; unknown success statuses/extra fields/malformed responses fail closed. Serialized models detach nested JSON and redact `toString`.

Regenerate with the pinned toolchain:

```bash
python3 scripts/mobile_contracts.py
python3 scripts/mobile_contracts.py --check
```

The drift check needs Dart formatting, not hand-edited generated output or a new contract version.

## Credential lifecycle and native privacy

1. Passwords, challenges, verification controls, TOTP codes, enrollment material, intents, proofs and recovery codes are transient. Secret fields disable selection, suggestions, autocorrect, autofill hints and IME personalized learning; fields are cleared on submission/disposal. Recovery codes have no clipboard/share/copy action. Dart immutable strings cannot promise memory zeroization or defense from a privileged debugger/keyboard/accessibility service.
2. Only the native credential store persists access/refresh credentials, together in one versioned encrypted record. Android uses the plugin's encrypted preferences backed by Keystore; iOS uses non-synchronizable `unlocked_this_device` Keychain accessibility. There is no SharedPreferences/plaintext/log/URL credential fallback; only a **non-secret generation UUID** is stored in an app-private native marker.
3. The marker is excluded from backup. Native invalidation synchronously replaces it before deleting the encrypted record. Android uses AtomicFile plus fd sync; iOS atomic protected-file write plus synchronization. This addresses Android plugin 9.2.4's asynchronous `SharedPreferences.apply()` deletion: an older encrypted record reappearing after a crash has the wrong generation and is rejected.
4. Before refresh, invalidate/delete/read-verify the old record **before** sending the single-use proof. On interruption, corruption, uncertain network outcome, failed replacement/read-back or stale response, erase local authority and require sign-in. No consumed proof is retried. A crash may sacrifice a session; availability is never preferred over replay safety.
5. Restore requires rotation and fresh `me`; offline cached identity is never authority. The access deadline is conservatively bounded from request start and by refresh/idle/absolute deadlines, including fresh `me`. Background/access expiry hides identity, cancels I/O, clears transient/private state and requires revalidation; no background keepalive extends idle life.
6. Epoch fences plus a serialized queue prevent concurrent rotation or late login/refresh/mutation responses from resurrecting credentials after logout/navigation/invalidation. Failed secure deletion locks access until deletion can be verified. Local logout happens even if server revocation cannot be confirmed, with a distinct warning.
7. Android disables backup/transfer of app-private domains, cleartext traffic and screenshots/recording through FLAG_SECURE; singleTask limits ordinary duplicate foreground engines. iOS uses ATS and a native inactive-window cover plus Flutter lifecycle cover. iOS cannot generally prevent user screenshots/recording. Reinstall/restore/OS rollback/Keystore/Keychain failure and physical crash guarantees still need device acceptance; a passing APK is not that evidence.

## Run and validate

Use the pinned SDK in a toolchain/package-enabled environment. The API origin must be an operator-approved **bare HTTPS origin**, without credentials/path/query/fragment. Default builds have networking disabled and visibly state that fact. Backend registration/session/MFA feature flags remain default-off; enabling a test backend is a separate operator configuration, not an app capability claim.

```bash
cd apps/mobile
flutter --version
flutter doctor -v
flutter pub get --enforce-lockfile
dart format --output=none --set-exit-if-changed lib test integration_test
flutter analyze --no-pub
flutter test --no-pub --reporter expanded
flutter build apk --debug --no-pub
# Only for an approved, enabled synthetic HTTPS test backend:
flutter run --dart-define=PWC_API_ORIGIN=https://approved-test-api.example.invalid
# Separate physical/emulator native acceptance, not executed by the VM suite:
flutter test integration_test/credential_lifecycle_test.dart -d DEVICE_ID
```

From repository root, run the contract drift check and dependency reviews in the configured CI environment. The final workflow must check, not rewrite, formatting and lockfile resolution. Diagnostic bootstrap notices were temporary source acquisition (including actual resolver output), never SDK/APK/secret upload or a disposable counter-app substitute.

## Device and deployment gates

- Android devices/emulators: actual native vault lifecycle harness; process kill at every barrier/delete/issue/write boundary; backup/cloud/device transfer/reinstall; Keystore invalidation; FLAG_SECURE/recents/lifecycle/multiwindow; accessibility at large text scales; Urdu glyphs/RTL on actual fonts; revoked-session and hold flows against enabled HTTPS backend.
- macOS/Xcode + iOS simulator/device: host compilation/signing/entitlements, native channel/Keychain accessibility and retained-keychain reinstall mismatch, protected-data lock/unlock, backup/restore, inactive snapshots, screenshot limitations, VoiceOver/RTL. Linux cannot certify these.
- Live email/provider delivery, approved app links, production endpoint configuration, release signing, privacy/legal/operational review, deployment and NGO/finance authority are not delivered here. No deployment or NGO onboarding follows automatically from this subphase.
