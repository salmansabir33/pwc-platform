# PWC-03D — Standard Flutter CI verification

## Scope and pins

This verifies standard GitHub-hosted Ubuntu setup, not the PWC application. No mobile features, PR, Android build or iOS/device acceptance are delivered by this check.

- Runner: `ubuntu-24.04`, read-only repository permission, 25-minute timeout, no persisted checkout credentials.
- Maintained setup: `subosito/flutter-action@v2`, pinned to upstream commit `1a449444c387b1966244ae4d4f8c696479add0b2`, resolved from the upstream v2 ref through the GitHub API. Reviewed its `action.yaml` and `setup.sh`; caches disabled. The action uses official HTTPS artifact storage, not a mirror. Its download implementation does not independently enforce an archive SHA256; do not describe this as the custom checksum-verifying installer.
- Flutter: **3.35.7 stable**, upstream tag commit `adc901062556672b4138e18a4dc62a4be8f4b3c2`, verified through the official Flutter repository API. This is a deliberate exact stable baseline, not a claim to be latest stable. Its sound-null-safe Dart 3 toolchain is suitable for the intended architecture; actual Riverpod/router/secure-storage and complete application dependency compatibility remain untested because no PWC pubspec exists. The workflow asserts installed version, stable channel and exact upstream revision before accepting setup verification.
- Checkout: `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` (v4).
- Only the existing environment workflow and retained custom script trigger branch pushes; manual dispatch is available. This is not yet a main/PR application CI gate.

## Correction to the earlier custom probe

The custom code used `https://storage.googleapis.com/flutter_infra_release/flutter/releases/releases_linux.json`. The maintained setup action uses **`https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json`**. The extra `/flutter/` was an implementation error in our probe. Consequently, the old 404 did not establish an Actions installation restriction. The retained Python probe/base and recovery recipe have been corrected; the new workflow does not invoke that custom installer.

The prior checkpoint `8f468527a6aa4acd3c8e136593168b1f42ce91c8` and earlier checkpoints are preserved as ancestors, without rewriting history. Existing ADRs/backend/web/application configurations are unchanged.

## Requested checks

1. Conventional pinned setup action (no insecure TLS or mirrors).
2. Installed SDK revision assertion, `flutter --version`, `dart --version`, machine-readable version/channel assertions.
3. `flutter doctor -v` (native warning output is not native build acceptance).
4. Verified HTTPS `pub.dev/api/packages/flutter_lints` metadata retrieval and JSON package-name validation.
5. `flutter create --no-pub` in `RUNNER_TEMP`, dependency resolution with `flutter pub get`.
6. Generated-sample Dart format, static analysis and upstream counter widget smoke test.

No generated sample, SDK/cache or guessed lockfile enters Git. Failure stops dependent checks, with an always-run scope summary. Skipped steps are not passes.

## Execution result

Pending the first pushed standard-action workflow run. This report will be updated with its exact run/check/step outcome. No standard installation or smoke-test success is asserted by this pending record. If unsuccessful, stop at that failure rather than claiming a baseline is established.
