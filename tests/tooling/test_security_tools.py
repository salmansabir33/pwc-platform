"""Negative tests for tooling; synthetic markers are assembled, never real secrets."""

from pathlib import Path
import tempfile
import unittest

from scripts.python_lock import check_lock

from scripts.python_dependency_review import findings, pins
from scripts.security_checks import inspect_file, workflow_errors


class SecurityToolTests(unittest.TestCase):
    def test_reject_tracked_environment_and_cache(self):
        self.assertIn(
            "environment-file", inspect_file("apps/backend/.env.production", b"")
        )
        self.assertIn("machine-cache", inspect_file(".venv/a", b""))
        self.assertEqual(inspect_file(".env.example", b"replace-local-value"), [])

    def test_secret_patterns(self):
        for value in (
            b"-----BEGIN " + b"PRIVATE KEY-----",
            b"ghp_" + b"x" * 36,
            b"AKIA" + b"A" * 16,
        ):
            self.assertTrue(inspect_file("file.txt", value))

    def test_workflow_pin_and_permission_denials(self):
        base = "permissions:\n  contents: read\n"
        self.assertEqual(
            workflow_errors(base + "- uses: actions/checkout@" + "a" * 40), []
        )
        self.assertIn(
            "unpinned-action", workflow_errors(base + "- uses: actions/checkout@v4")
        )
        self.assertIn(
            "contents-read-required", workflow_errors("permissions: write-all")
        )
        self.assertIn(
            "privileged-workflow", workflow_errors(base + "pull_request_target:")
        )

    def test_exact_pins_only(self):
        self.assertEqual(
            pins("Django==5.2.18\npsycopg[binary]==3.3.6\n# comment"),
            {"django": "5.2.18", "psycopg": "3.3.6"},
        )
        for value in (
            "Django>=5",
            "-r runtime.txt",
            "pkg @ https://invalid",
            "pkg==1\npkg==2",
        ):
            with self.assertRaises(ValueError):
                pins(value)

    def test_advisory_not_silently_suppressed(self):
        packages = [("pkg", "1")]
        self.assertEqual(
            len(findings(packages, {"results": [{"vulns": [{"id": "TEST-1"}]}]})), 1
        )
        self.assertEqual(findings(packages, {"results": [{}]}), [])
        for response in (
            {"results": []},
            {"results": [None]},
            {"results": [{"error": "unavailable"}]},
            {"results": [{"vulns": [{"id": "bad\nvalue"}]}]},
        ):
            with self.assertRaises((ValueError, TypeError)):
                findings(packages, response)

    def test_lock_drift_missing_hash_and_invalid_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "requirements.lock"
            valid = "pkg==1 " + chr(92) + "\n    --hash=sha256:" + "a" * 64 + "\n"
            path.write_text(valid)
            check_lock(path, {"pkg": "1"})
            for invalid in (
                "pkg==1\n",
                valid.replace("pkg==1", "pkg==2"),
                valid.replace("a" * 64, "not-a-hash"),
            ):
                path.write_text(invalid)
                with self.assertRaises(ValueError):
                    check_lock(path, {"pkg": "1"})
