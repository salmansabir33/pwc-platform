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

## Public NGO directory

`PWC_PUBLIC_DIRECTORY_ORIGIN` is a **separate, disabled-by-default** bare HTTPS
origin. It enables only anonymous, credential-free public reads; it does not
configure `PWC_API_ORIGIN` or enable identity, membership or NGO-private operations.
No backend flags or publication permissions are changed.

The directory loads on entry and supports the existing `q`, `city` and
`classification` (`registered` / `unregistered`) filters. “Load more” appends and
deduplicates cursor pages; a failed page retains previous results and retries the
same cursor. Editing filters cancels and clears the old search. Empty results,
unavailable/offline transport, loading and retry states are localized EN/UR.

Tapping an organization fetches the existing public organization-detail endpoint
again, rather than treating a list result as a current profile. Only the strict
`id`, `name`, `city`, `classification` contract is accepted; unavailable/withdrawn
profiles never fall back to cached fields. Returning refreshes the directory.
The generated public operation manifest contains only the exact directory and
organization-detail GETs; the personal operation allowlist is unchanged.

Run `flutter test test/directory_test.dart` for public-client and widget coverage,
including filters, append/retry, invalid/private responses, stale search/profile
completion and navigation. Test records are synthetic fixtures, not shipped data.
