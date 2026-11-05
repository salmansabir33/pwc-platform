"""Offline staging/coexistence and public advisory extraction, not host acceptance."""

from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from infra.staging.advisory_report import main as advisories, rows
from infra.staging.readiness import coexistence
from staging_fixtures import config, deploy, ROOT


class EnrollmentPreparationTests(unittest.TestCase):
    def test_other_projects_and_database_ports_remain_untouched(self):
        report = coexistence(
            "pwc-staging",
            {
                "inventory_complete": True,
                "compose_projects": ["other-project"],
                "tcp_ports": [80, 5432],
            },
        )
        self.assertTrue(report["coexistence_preflight_passed"])
        self.assertFalse(report["deployment_authorized"])
        self.assertFalse(report["real_enrollment_ready"])
        self.assertFalse(report["actual_host_acceptance"])

    def test_occupied_https_or_project_name_blocks_without_resource_names_in_output(
        self,
    ):
        for projects, ports, code in (
            (["pwc-staging"], [], "COMPOSE_PROJECT_ALREADY_EXISTS_DO_NOT_OVERWRITE"),
            (
                ["other-project"],
                [443],
                "PUBLIC_443_OCCUPIED_DO_NOT_STOP_OTHER_PROJECTS",
            ),
        ):
            with self.subTest(code=code):
                report = coexistence(
                    "pwc-staging",
                    {
                        "inventory_complete": True,
                        "compose_projects": projects,
                        "tcp_ports": ports,
                    },
                )
                self.assertFalse(report["coexistence_preflight_passed"])
                self.assertIn(code, report["blockers"])
                self.assertNotIn("other-project", json.dumps(report))

    def test_missing_ambiguous_or_forged_inventory_cannot_pass(self):
        valid = {"inventory_complete": True, "compose_projects": [], "tcp_ports": []}
        for change in (
            {"inventory_complete": False},
            {"extra": True},
            {"tcp_ports": [True]},
            {"tcp_ports": [0]},
            {"compose_projects": ["bad\nvalue"]},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                coexistence("pwc-staging", {**valid, **change})

    def test_all_runtime_images_include_the_same_security_upgrade_and_gateway_is_built(
        self,
    ):
        document = deploy.compose(config("/tmp/pwc-not-real"), Path("/tmp/rendered"))
        services = document["services"]
        self.assertEqual(
            services["gateway"]["build"]["dockerfile"],
            "infra/staging/gateway.Dockerfile",
        )
        self.assertEqual(
            services["gateway"]["build"]["args"]["HAPROXY_IMAGE"],
            config("/tmp/pwc-not-real")["images"]["haproxy"],
        )
        for name in ("app", "portal", "postgres", "gateway"):
            self.assertIn(
                "sh /tmp/pwc-security-upgrade.sh",
                (ROOT / f"infra/staging/{name}.Dockerfile").read_text(),
            )
        upgrade = (ROOT / "infra/staging/security-upgrade.sh").read_text()
        self.assertIn("--only-upgrade apt", upgrade)
        self.assertIn("minimum=2.6.2", upgrade)
        self.assertIn("minimum=3.0.4", upgrade)
        self.assertIn("dpkg --compare-versions", upgrade)
        self.assertIn(
            "compose build --pull app ngo ops db gateway",
            (ROOT / "infra/staging/stack.sh").read_text(),
        )

    def reports(self, directory):
        root = Path(directory) / "trivy"
        root.mkdir()
        for index in range(1, 6):
            value = {
                "SchemaVersion": 2,
                "Metadata": {"NEVER_PRINT": "synthetic-private-config"},
                "Results": [
                    {
                        "Vulnerabilities": [
                            {
                                "VulnerabilityID": "CVE-2026-109518",
                                "PkgName": "apt",
                                "InstalledVersion": "3.0.3",
                                "FixedVersion": "3.0.4",
                                "Severity": "HIGH",
                            },
                            {
                                "VulnerabilityID": "CVE-2026-9538",
                                "PkgName": "fixture",
                                "InstalledVersion": "1.0",
                                "Severity": "CRITICAL",
                            },
                        ]
                    },
                    {"Vulnerabilities": None},
                ],
            }
            (root / f"image-{index}.json").write_text(json.dumps(value))
        return root

    def test_report_preserves_fixed_and_unfixed_without_configuration_or_annotation_truncation(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            self.reports(directory)
            output = StringIO()
            with redirect_stdout(output):
                evidence = advisories(directory)
            self.assertEqual(len(evidence), 10)
            self.assertEqual(sum(bool(row["FixedVersion"]) for row in evidence), 5)
            text = output.getvalue()
            self.assertNotIn("synthetic-private-config", text)
            messages = [line.split("::", 2)[-1] for line in text.splitlines()]
            self.assertLessEqual(len(messages), 10)
            self.assertTrue(all(len(m) < 4096 for m in messages))
            self.assertEqual(sum(len(json.loads(m)) for m in messages), 10)

    def test_missing_duplicate_or_malformed_reports_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.reports(directory)
            duplicate = Path(directory) / "image-1.json"
            duplicate.write_text((root / "image-1.json").read_text())
            with self.assertRaises(ValueError):
                rows(directory)
            duplicate.unlink()
            (root / "image-1.json").unlink()
            with self.assertRaises(ValueError):
                rows(directory)
            (root / "image-1.json").write_text("{}")
            with self.assertRaises(ValueError):
                rows(directory)
