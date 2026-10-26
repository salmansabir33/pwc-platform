"""Install only an official checksum-verified stable SDK for a temporary CI probe.

This is not the PWC mobile application or its final version pin. Never use a
mirror or disable certificate checks to make this diagnostic pass.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request

BASE = "https://storage.googleapis.com/flutter_infra_release/flutter/"
MANIFEST = BASE + "releases/releases_linux.json"


def select_release(manifest):
    revision = manifest["current_release"]["stable"]
    release = next(row for row in manifest["releases"]
                   if row["hash"] == revision and row["channel"] == "stable"
                   and row.get("dart_sdk_arch", "x64") == "x64")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Unexpected release revision")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", release["version"]):
        raise ValueError("Not a stable version")
    expected = f"stable/linux/flutter_linux_{release['version']}-stable.tar.xz"
    if release["archive"] != expected or not re.fullmatch(r"[0-9a-f]{64}", release["sha256"]):
        raise ValueError("Unexpected official archive/checksum")
    return release


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise SystemExit("Diagnostic installer is restricted to GitHub Actions")
    with urllib.request.urlopen(MANIFEST, timeout=60) as response:
        release = select_release(json.load(response))
    temporary = Path(os.environ["RUNNER_TEMP"])
    archive = temporary / "pwc-flutter-probe.tar.xz"
    subprocess.run(["curl", "--fail", "--location", "--proto", "=https",
                    "--tlsv1.2", "--retry", "2", "--output", str(archive),
                    BASE + release["archive"]], check=True, timeout=900)
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != release["sha256"]:
        raise SystemExit("Official Flutter archive SHA256 mismatch; refusing extraction")
    subprocess.run(["tar", "-xJf", str(archive), "-C", str(temporary)], check=True)
    sdk = temporary / "flutter"
    actual = subprocess.check_output(["git", "-C", str(sdk), "rev-parse", "HEAD"], text=True).strip()
    if actual != release["hash"]:
        raise SystemExit("SDK source revision differs from official release manifest")
    (temporary / "pwc-flutter-release.json").write_text(json.dumps(release, indent=2) + "\n")
    with open(os.environ["GITHUB_PATH"], "a") as stream:
        stream.write(str(sdk / "bin") + "\n")
    with open(os.environ["GITHUB_ENV"], "a") as stream:
        stream.write(f"FLUTTER_ROOT={sdk}\n")
    with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
        stream.write(f"version={release['version']}\n")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
        stream.write("## Official SDK used for environment probe\n\n")
        stream.write(f"Flutter {release['version']} / revision `{actual}`\n\n")
        stream.write(f"SHA256: `{release['sha256']}`\n\n")
        stream.write("Selected from official stable release metadata over verified HTTPS. "
                     "This diagnostic follows current stable; a future PWC application must pin its tested SDK.\n")
    print(json.dumps({key: release[key] for key in ("version", "hash", "sha256", "archive")}))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # Official public URLs only; do not dump environment or credentials.
        # Emit a bounded annotation because raw Actions log hosts may be
        # inaccessible from the workspace even when api.github.com works.
        message = f"SDK acquisition failed: {type(error).__name__}: {error}"
        message = message[:1200].replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::error title=Flutter SDK acquisition::{message}", flush=True)
        raise SystemExit(1) from None
