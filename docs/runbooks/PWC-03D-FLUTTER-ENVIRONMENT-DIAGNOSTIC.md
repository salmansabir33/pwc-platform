# PWC-03D — Flutter environment recovery diagnostic

Date: 26 October 2026.

**Implementation update:** the same PWC-03D assignment has resumed using verified GitHub-hosted Flutter. Actual app source, real resolver lockfile, personal identity/security flows and Android compilation now exist. See the [current foundation runbook](PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and [current integration review](../reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md). The blocked/unimplemented verdicts below are historical environment checkpoints, not the current source status. No local Arena Flutter execution is implied.

**Current update:** [standard Flutter CI verification succeeded](PWC-03D-STANDARD-FLUTTER-CI.md), including real SDK installation, pub dependency resolution, analysis and generated widget smoke testing on GitHub-hosted Ubuntu. The local Arena restrictions below remain, but a separate CI execution environment is no longer an unproven fallback. This document preserves the historical custom-probe results; it must not be read as a current assertion that GitHub Actions cannot run Flutter.

**Historical local outcome: Arena remains unable to run Flutter. PWC-03D application implementation is stopped, incomplete and not merge-ready. No PR is opened.** This is environment recovery in the same subphase, not a reduced implementation ticket. No mobile authentication, secure storage, MFA, screen or application test has been delivered.

## Correction: standard action verification follow-up

The earlier custom probe constructed an **incorrect URL**, with an extra `/flutter/` segment. The maintained `subosito/flutter-action@v2` source uses `https://storage.googleapis.com/flutter_infra_release/releases/releases_linux.json`. The historical 404 below is not evidence that standard installation is impossible. The retained script and Linux recipe now use the correct base. Historical failed-run URLs/observations remain recorded, but their inference is superseded by this correction and the [standard CI verification report](PWC-03D-STANDARD-FLUTTER-CI.md).

The workflow has been replaced with a conventional pinned setup action; the description of the custom workflow below describes those historical attempts, not its current contents. Local TLS restrictions remain distinct from the malformed-URL remote failure.

## 1. Repository recovery and preservation

Branch: `arena/f54f895c-pwc-platform`. The checkout had regressed to `0445840ab5d0850169d20e9a90099ab8b0c13cc6` with the two prior checkpoint documents untracked. Both files matched `f1adea79ae4e2bfe5769349f836c952decd674fc` byte-for-byte. Preserved an external archive (`/home/user/03d-environment-preservation.tar.gz`) and include-untracked stash, then fast-forwarded the same branch to the existing checkpoint. No work was discarded, branch changed or history rewritten. The stash/archive remain retained; identical documents were not reapplied over their committed versions.

Environment-probe commits descend from that preserved checkpoint. No backend code, approved ADR, schema, application feature flag, W1 network configuration or `apps/mobile` content was changed. The mobile directory still contains only its reserved-path README.

## 2. Exact local observations

| Area                  | Result                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| OS                    | Debian GNU/Linux 12 (bookworm), Linux 6.1.158+, x86_64                                                                          |
| PATH                  | `/usr/local/bin:/usr/bin:/bin:/usr/local/games:/usr/games`                                                                      |
| Flutter/Dart          | Neither executable on PATH; bounded search of `/opt`, `/usr/local`, `/usr/lib`, `/home/user`, `/tmp` found no installation      |
| Android/JDK/iOS       | `java`, `javac`, `adb`, `sdkmanager`, `xcodebuild` not found on PATH; `/usr/lib/jvm` absent                                     |
| SDK/cache locations   | No `/opt/flutter`, `/opt/android-sdk`, `/opt/hostedtoolcache`, user/root `.pub-cache` identified                                |
| Container alternative | `docker` and `podman` absent; no `/var/run/docker.sock`; no usable trusted build image identified                               |
| DNS                   | `pub.dev`, `storage.googleapis.com`, `dl.google.com` resolve; resolver file names `8.8.8.8`                                     |
| TCP                   | Python socket connections to port 443 on all three hosts succeed                                                                |
| TLS                   | Verified-default Python TLS wrapping ends with `SSLZeroReturnError` / EOF for all three required hosts                          |
| HTTP probes           | Both fresh IPv4 HEAD and GET attempts fail with curl exit 35, HTTP 000, `SSL_ERROR_SYSCALL` for the required hosts              |
| Control probes        | GitHub verified HTTPS works; PyPI GET returns HTTP 200, curl certificate verification result 0; Python verifies TLS 1.3 to PyPI |
| Certificates          | System CA bundle exists; curl uses OpenSSL 3.0.20; no insecure certificate flags used                                           |
| Proxy/config          | No proxy, Flutter, Dart/pub, Java/Android or custom certificate environment variable names found; no values/secrets dumped      |

Failed operations included:

```text
GET/HEAD https://pub.dev/api/packages/flutter_riverpod
GET/HEAD https://storage.googleapis.com/flutter_infra_release/flutter/releases/releases_linux.json
GET/HEAD https://dl.google.com/android/repository/repository2-1.xml
```

These are repeated host-selective failures, not missing DNS or a single transient timeout. Findings are consistent with this workspace's restricted outbound environment; the exact firewall/TLS intermediary cannot be established from the application sandbox. A missing CA bundle is not supported by the control results, and no server certificate was successfully negotiated for the failing hosts. Changing app code, disabling TLS verification, adding an untrusted mirror or inventing a lockfile is not a safe remedy.

`flutter doctor -v`, `flutter pub get`, `flutter analyze`, `flutter test` and native builds cannot execute locally because the toolchain and dependency cache are absent. No claim that those commands failed within an installed Flutter application is made: they were not run locally.

## 3. GitHub Actions: tested capability and failure

Existing backend/web workflows successfully ran for preserved commit `f1adea79`; that is not Flutter evidence. Reading repository-wide Actions permissions returned HTTP 403 (`Resource not accessible by integration`), but this does **not** mean Actions execution is disabled or GitHub authentication is broken.

Added a restricted diagnostic workflow, `.github/workflows/flutter-environment.yml`:

- Only pushes changing the probe workflow/script on this assigned branch trigger it.
- Read-only contents permissions, checkout pinned to verified commit `11d5960a326750d5838078e36cf38b85af677262`, with credential persistence disabled.
- Ubuntu 24.04, bounded 25-minute timeout, no secrets, app credentials, SDK/APK uploads or repository write permission.
- Installer accepts only official stable Linux x64 metadata, strict archive/version/revision syntax, HTTPS official artifact URL, matching SHA256 and matching source revision before using an SDK.
- Diagnostic follows official current stable **only for acquisition testing** and would record the selected release/hash. This is not a tested/pinned PWC application toolchain.
- Downstream steps would create a disposable upstream counter sample in `RUNNER_TEMP`, resolve candidate packages, check formatting, run analyze/widget tests and attempt an Android debug build. No sample source is added to `apps/mobile`.

The two actual attempts were:

1. [Initial probe 40252819116](https://github.com/salmansabir33/pwc-platform/actions/runs/40252819116): SDK-install step failed; no downstream Flutter check ran.
2. [Annotated probe 40252904537](https://github.com/salmansabir33/pwc-platform/actions/runs/40252904537): SDK-install step failed with the API-visible annotation **`SDK acquisition failed: HTTPError: HTTP Error 404: Not Found`**. The failing Python operation is retrieval of the official release metadata URL, before archive download/extraction.

Runner annotation confirms Linux x86_64, `java`/`javac` on PATH, and `adb`/`sdkmanager`/`flutter`/`dart` not on PATH. Tool presence alone does not establish Android SDK completeness or JDK compatibility. SDKs outside PATH were not exhaustively searched on the runner.

Raw Actions log retrieval from Arena failed with EOF at the redirected `results-receiver.actions.githubusercontent.com` host. Job step states and explicit annotations were retrieved successfully through `api.github.com`; bounded public failure annotations were added for that reason. No signed log URL is recorded here.

**Conclusion:** GitHub Actions can execute this workflow. It has **not** successfully validated Flutter in this repository. The remote HTTP 404 differs from local TLS closure; subsequent source inspection found the custom manifest URL was malformed (see correction above). Do not claim GitHub Actions is inherently incapable of Flutter, or claim it is a working fallback based only on a started job. Formatting/analyze/widget/APK steps were all **skipped**, not passed. Doctor/iOS/device validation also remains unperformed.

The diagnostic intentionally fails rather than marking unavailable prerequisites as green. Its branch/path-only trigger does not establish permanent mobile application CI; that must be finalized with the actual application and a tested SDK pin after recovery.

## 4. Checks actually executed

- Five local synthetic metadata/provenance checks: accepted one structurally valid official-form fixture; rejected wrong archive origin/path, missing checksum, prerelease version and malformed revision. These test installer selection guards, not any real SDK binary.
- Python syntax compilation for the installer passed.
- Probe workflow formatting and Git whitespace checks passed.
- Two GitHub probe attempts executed; both failed at SDK metadata acquisition. No mobile test count can be reported.
- No mobile dependencies were resolved or lockfile generated. No new app/security package vulnerability or native-storage review can be claimed.
- Existing backend/web workflows may also execute for pushed checkpoints. Their results are separate and do not validate Flutter or PWC mobile functionality.

## 5. Minimum reproducible Linux recovery setup

Use a toolchain-enabled Linux x86_64 environment with working, certificate-verified access to official Flutter artifacts and Dart package endpoints, or a verified offline SDK plus a complete compatible pub cache. For Android, permit official Android SDK/Google Maven, Maven Central and Gradle distribution/plugin downloads required by the selected toolchain, or provide their verified caches. Do not substitute unknown images or mirrors.

Typical Debian/Ubuntu prerequisites (not executed in this blocked workspace):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git unzip xz-utils zip \
  libglu1-mesa python3 openjdk-17-jdk
```

The final JDK/Android package versions must match the selected Flutter/Gradle toolchain; no Android build compatibility was established here. Provision the official Android command-line tools and verify their published checksum, set `ANDROID_HOME` and add its `cmdline-tools/latest/bin` and `platform-tools` to PATH. Install the platform/build tools required by the generated project and review the SDK license prompts. Do not invent package versions to satisfy a missing installation.

### SDK provenance and acquisition

The first prerequisite is a **successful** verified HTTPS fetch of the currently failing official release manifest. The following recipe is for an enabled environment; it is not a TLS/network workaround or a claim it ran here. Run from repository root:

```bash
export SDK_PARENT="$HOME/.local/share/pwc-flutter"
python3 - <<'PY'
import hashlib, json, os, subprocess, urllib.request
from pathlib import Path
from scripts.flutter_environment_probe import BASE, MANIFEST, select_release

with urllib.request.urlopen(MANIFEST, timeout=60) as response:
    release = select_release(json.load(response))
parent = Path(os.environ['SDK_PARENT'])
parent.mkdir(parents=True, exist_ok=True)
archive = parent / 'official-flutter.tar.xz'
subprocess.run(['curl', '--fail', '--location', '--proto', '=https',
                '--tlsv1.2', '--output', str(archive), BASE + release['archive']], check=True)
digest = hashlib.sha256()
with archive.open('rb') as stream:
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
assert digest.hexdigest() == release['sha256'], 'SDK checksum mismatch'
assert not (parent / 'flutter').exists(), 'Do not overwrite an existing SDK'
subprocess.run(['tar', '-xJf', str(archive), '-C', str(parent)], check=True)
actual = subprocess.check_output(['git', '-C', str(parent / 'flutter'),
                                  'rev-parse', 'HEAD'], text=True).strip()
assert actual == release['hash'], 'SDK revision mismatch'
(parent / 'release-provenance.json').write_text(json.dumps(release, indent=2) + '\n')
print(release['version'], actual, release['sha256'])
PY
export PATH="$SDK_PARENT/flutter/bin:$PATH"
flutter --version
flutter doctor -v
```

If official metadata is genuinely unavailable, stop and obtain a release archive **with independently published official checksum/revision provenance**, or repair the official endpoint access. Do not guess a checksum or remove validation to proceed. Keep SDKs/caches outside Git.

After provisioning, resolve and test a disposable sample first, pin the verified SDK and compatible packages, then resume the complete PWC-03D application at `apps/mobile` and commit only application source, platform configuration and resolver-generated lockfile. Required checks include `flutter pub get`, `dart format --output=none --set-exit-if-changed`, `flutter analyze`, `flutter test` and a representative Android build. A sample pass is only toolchain evidence, not PWC identity/security acceptance.

Linux cannot establish iOS acceptance: a macOS/Xcode environment and actual simulator/device testing remain necessary for Keychain accessibility/reinstall/backup, app lifecycle, screenshots/snapshots and native integration. Android secure-store/backup/restore and refresh concurrency likewise need the requested app implementation/tests, not merely a compiling sample.

## 6. Historical handoff (superseded for GitHub-hosted execution by the standard CI result)

A different verified toolchain/package-enabled execution environment, or a repaired official SDK/package path plus usable verified local caches, is required before application implementation resumes. No application-security requirement is weakened. No backend endpoint, NGO authority, web authentication, W2 or finance work is added. Existing `f1adea79` remains an ancestor, and no documentation-only PR is opened.

Continue the same full PWC-03D assignment once recovery is demonstrated. The [foundation runbook](PWC-03D-FLUTTER-MOBILE-FOUNDATION.md) and [blocked review](../reviews/PWC-03D-MOBILE-INTEGRATION-REVIEW.md) remain explicit incomplete records, not completion evidence.
