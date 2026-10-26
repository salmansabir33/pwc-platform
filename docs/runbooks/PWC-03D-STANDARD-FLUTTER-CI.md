# PWC-03D — Standard Flutter CI verification

**Current implementation update:** The standard pinned Flutter/Dart setup is retained, but the workflow now validates the actual `apps/mobile` project, not the disposable sample. See the [foundation runbook](PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and [integration review](../reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md) for actual PWC source/test/build evidence and final pins. The sample-only scope/results below remain historical proof of SDK acquisition, not current application coverage. Checkout/setup-java pins were advanced to reviewed maintained v6/v5 revisions in the mobile workflow; Flutter 3.35.7 / Dart 3.9.2 and the pinned subosito v2 revision remain unchanged.

## Scope and pins

This verifies standard GitHub-hosted Ubuntu setup, not the PWC application. No mobile features, PR, Android build or iOS/device acceptance are delivered by this check.

- Runner: `ubuntu-24.04`, read-only repository permission, 25-minute timeout, no persisted checkout credentials.
- Maintained setup: `subosito/flutter-action@v2`, pinned to upstream commit `1a449444c387b1966244ae4d4f8c696479add0b2`, resolved from the upstream v2 ref through the GitHub API. Reviewed its `action.yaml` and `setup.sh`; caches disabled. The action uses official HTTPS artifact storage, not a mirror. Its download implementation does not independently enforce an archive SHA256; do not describe this as the custom checksum-verifying installer.
- Flutter: **3.35.7 stable**, upstream tag commit `adc901062556672b4138e18a4dc62a4be8f4b3c2`, verified through the official Flutter repository API. This is a deliberate exact stable baseline, not a claim to be latest stable. Its sound-null-safe Dart 3 toolchain is suitable for the intended architecture; actual Riverpod/router/secure-storage and complete application dependency compatibility remain untested because no PWC pubspec exists. The workflow asserts installed version, stable channel and exact upstream revision before accepting setup verification.
- Checkout: `actions/checkout@11d5960a326750d5838078e36cf38b85af677262` (v4).
- Scoped pushes to `main` and `arena/f54f895c-pwc-platform`, and pull requests targeting `main`, trigger for the environment workflow, retained diagnostic script or `apps/mobile/**`. Manual dispatch is configured. This is a disposable-sample smoke baseline, **not an application test gate**; future PWC source must gain actual dependency/format/analyze/test/build coverage before it can pass PWC-03D acceptance. No PR is opened just to install this workflow on main.

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

## Execution evidence

- [First standard-action run 40255281112](https://github.com/salmansabir33/pwc-platform/actions/runs/40255281112), commit `2c09cbb0e24a065613e5abc9fa3fc930ac2c697f`: **success**. Setup, exact SDK version/revision, doctor command, registry metadata retrieval, real dependency resolution, generated-sample formatting, analysis and upstream widget smoke test all passed.
- [Result-instrumentation follow-up 40255476288](https://github.com/salmansabir33/pwc-platform/actions/runs/40255476288), commit `94f0938e2d0f9d04a51e51c08c26f93d7291ec4b`: **failure**, specifically `Run upstream counter widget smoke test` (exit 1), which then combined `flutter test --machine` and custom JSON result aggregation. All preceding setup/network/resolver/format/analysis steps passed. Raw log retrieval failed with EOF on the redirected Actions log host; the available API annotations do not establish whether the test invocation or aggregation caused that failure. Do not count this failed step as a pass or invent a stack trace. Custom aggregation was removed, returning to the already-passing `flutter test --no-pub --reporter expanded` command.
- [Final baseline run 40255670141](https://github.com/salmansabir33/pwc-platform/actions/runs/40255670141), commit `1b9859272c1154a11734c80a836558160e22dfc7`, job/check `121356868280`: **success**, completed in **1 minute 40 seconds**. Every requested setup/version/doctor/registry/resolver/format/analyze/widget step passed; explicit notices confirm sample analysis and generated counter widget smoke success. No requested smoke check was skipped. The exact final workflow is retained as the Flutter CI smoke baseline. Later documentation-only commits do not retrigger this path-scoped workflow; this result applies to the unchanged workflow at the cited commit.

### Tooling/network details from annotations

- Flutter **3.35.7 stable**, framework revision **`adc901062556672b4138e18a4dc62a4be8f4b3c2`**; Dart **3.9.2**. Both exact SDK revision and machine-readable version/channel assertions passed.
- Verified HTTPS registry request fetched `flutter_lints` metadata from pub.dev; metadata reported latest **6.0.0**. This is registry metadata, **not a claim that the sample resolved that package version**. Separate `flutter pub get` succeeded with the generated template's own constraints.
- Doctor reported Ubuntu 24.04.5 LTS on Azure x86_64; Flutter, Chrome, connected devices and network resources marked successful. Android toolchain **warning** (SDK 37.0.0); Linux desktop toolchain **failure**; Android Studio **not installed**. The doctor command exits successfully while reporting these limitations. Detailed subcauses were not captured in API annotations, so no missing-package/license diagnosis is invented. This does not validate Android compilation or Linux desktop builds.
- Checkout produced a non-fatal Node 20 deprecation annotation (runner forced Node 24). No Flutter installation failure was reported in these standard-action runs.
- Raw logs are available to repository users via the run links; this sandbox's redirected-log access failed. Bounded explicit notices and step states provide the recorded evidence. No signed retrieval URL is retained in Git.

## Baseline and boundaries

The baseline is the pinned maintained setup plus disposable generated-project resolver/format/analyze/widget smoke checks. It does not install Flutter locally in Arena, resolve the intended application packages, or test PWC functionality. No Android APK, iOS/Xcode or secure-store/device acceptance is claimed. No archive-SHA256 verification is attributed to the maintained action (see provenance limitation above).

PWC-03D remains **not implemented / not merge-ready**. The successful standard setup supersedes the inference that another CI environment is necessarily required: GitHub-hosted Ubuntu can run Flutter here. Local Arena remains toolchain/network restricted. No ADR, backend/web configuration, API or mobile source change is justified by this verification.
