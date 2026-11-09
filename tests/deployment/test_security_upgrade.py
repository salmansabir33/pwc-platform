"""Exercise the image upgrade script with isolated package-manager doubles."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from staging_fixtures import config, deploy, ROOT


FIXED_ZLIB = "1:1.3.dfsg+really1.3.1-1+deb13u1"


class SecurityUpgradeTests(unittest.TestCase):
    def run_upgrade(self, codename="trixie", os_id="debian", **versions):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "os-release").write_text(
                f"ID={os_id}\nVERSION_CODENAME={codename}\n"
            )
            script = (ROOT / "infra/staging/security-upgrade.sh").read_text()
            self.assertEqual(script.count(". /etc/os-release"), 1)
            # Use a private fixture; no system files or package database are changed.
            (root / "upgrade.sh").write_text(
                script.replace(". /etc/os-release", f'. "{root}/os-release"')
            )
            commands = {
                "apt-get": """#!/bin/sh
printf '%s\\n' "$*" >> "$CALL_LOG"
case "$*" in *"$FAIL_APT"*) [ -z "$FAIL_APT" ] || exit 1;; esac
""",
                "dpkg-query": """#!/bin/sh
for package do :; done
case "$package" in
    apt) printf %s "$APT_VERSION" ;;
    libapt-pkg*) printf %s "$LIBAPT_VERSION" ;;
    zlib1g) [ "$ZLIB_VERSION" != missing ] || exit 1; printf %s "$ZLIB_VERSION" ;;
    *) exit 1 ;;
esac
""",
                "rm": "#!/bin/sh\nexit 0\n",
            }
            for name, content in commands.items():
                path = root / name
                path.write_text(content)
                path.chmod(0o755)
            env = {
                **os.environ,
                "PATH": str(root) + os.pathsep + os.environ["PATH"],
                "CALL_LOG": str(root / "calls"),
                "APT_VERSION": versions.get("apt", "3.0.4"),
                "LIBAPT_VERSION": versions.get("libapt", "3.0.4"),
                "ZLIB_VERSION": versions.get("zlib", FIXED_ZLIB),
                "FAIL_APT": versions.get("fail_apt", ""),
            }
            result = subprocess.run(
                ["sh", str(root / "upgrade.sh")],
                capture_output=True,
                text=True,
                env=env,
            )
            calls = (root / "calls").read_text() if (root / "calls").exists() else ""
            return result, calls

    def test_trixie_requires_fixed_or_newer_zlib(self):
        for version, succeeds in (
            ("1:1.3.dfsg+really1.3.1-1+b1", False),
            (FIXED_ZLIB, True),
            ("1:1.3.dfsg+really1.3.1-1+deb13u2", True),
            ("missing", False),
        ):
            with self.subTest(version=version):
                result, calls = self.run_upgrade(zlib=version)
                self.assertEqual(result.returncode == 0, succeeds, result.stderr)
                self.assertIn("--only-upgrade zlib1g", calls)
                self.assertIn("--only-upgrade apt libapt-pkg7.0", calls)

    def test_bookworm_and_trixie_require_both_patched_apt_packages(self):
        for distro, minimum, old, library in (
            ("bookworm", "2.6.2", "2.6.1", "libapt-pkg6.0"),
            ("trixie", "3.0.4", "3.0.3", "libapt-pkg7.0"),
        ):
            for apt, libapt, succeeds in (
                (minimum, minimum, True),
                (old, minimum, False),
                (minimum, old, False),
            ):
                with self.subTest(distro=distro, apt=apt, libapt=libapt):
                    result, calls = self.run_upgrade(distro, apt=apt, libapt=libapt)
                    self.assertEqual(result.returncode == 0, succeeds)
                    self.assertIn("--only-upgrade apt " + library, calls)
                    if distro == "bookworm":
                        self.assertNotIn("zlib1g", calls)

    def test_unreviewed_distributions_fail_before_apt(self):
        for distro, os_id in (("forky", "debian"), ("trixie", "ubuntu")):
            with self.subTest(distro=distro, os_id=os_id):
                result, calls = self.run_upgrade(distro, os_id)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(calls, "")

    def test_apt_failures_abort_build(self):
        for failure in ("update", "libapt-pkg7.0", "zlib1g"):
            with self.subTest(failure=failure):
                result, _ = self.run_upgrade(fail_apt=failure)
                self.assertNotEqual(result.returncode, 0)

    def test_four_affected_services_build_from_remediated_dockerfiles(self):
        services = deploy.compose(config("/tmp/pwc-not-real"), Path("/tmp/rendered"))[
            "services"
        ]
        for service, dockerfile in (
            ("ngo", "portal"),
            ("ops", "portal"),
            ("db", "postgres"),
            ("gateway", "gateway"),
        ):
            with self.subTest(service=service):
                self.assertEqual(
                    services[service]["build"]["dockerfile"],
                    f"infra/staging/{dockerfile}.Dockerfile",
                )
                content = (ROOT / f"infra/staging/{dockerfile}.Dockerfile").read_text()
                self.assertIn(
                    "COPY infra/staging/security-upgrade.sh /tmp/pwc-security-upgrade.sh",
                    content,
                )
                self.assertIn("RUN sh /tmp/pwc-security-upgrade.sh &&", content)


if __name__ == "__main__":
    unittest.main()
