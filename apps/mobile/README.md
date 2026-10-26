# PWC mobile

Flutter 3.35.7 stable / Dart 3.9.2, Riverpod, go_router and a contract-bound native personal identity client. Networking is visibly disabled unless `PWC_API_ORIGIN` is explicitly supplied as an approved bare HTTPS origin. Backend feature flags/defaults are unchanged; delivery remains synthetic-only.

See [the foundation runbook](../../docs/runbooks/PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and [integration review](../../docs/reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md) for actual CI evidence, screen/contract coverage, secure credential lifecycle and unexecuted native-device gates. Do not regenerate over the committed source or guess a lockfile.

```bash
flutter pub get --enforce-lockfile
dart format --output=none --set-exit-if-changed lib test integration_test
flutter analyze --no-pub
flutter test --no-pub --reporter expanded
flutter build apk --debug --no-pub
```

No production NGO workspace, memberships, finance, browser identity transport, live inbox delivery, deployment or release signing is provided by this client. Native device integration tests exist but require a separate device/emulator run; a VM widget test or successful APK does not establish secure-storage/backup/restore acceptance.
