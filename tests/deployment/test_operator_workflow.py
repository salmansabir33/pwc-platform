"""Disposable/mock execution only. Never contacts a host or seeds a deployment."""

import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from infra.staging import operate, provision, recovery
from staging_fixtures import certificates, config


class OperatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        self.value = config(self.root)
        # Real-host validators must never accept the reserved synthetic hosts.
        self.value.update(
            ngo_host="ngo-staging.coventure.pk", ops_host="ops-staging.coventure.pk"
        )
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps(self.value))
        self.config.chmod(0o600)

    def test_docker_execution_pins_local_context_and_drops_other_project_environment(
        self,
    ):
        with (
            patch.dict(
                os.environ,
                {
                    "COMPOSE_PROJECT_NAME": "unrelated",
                    "COMPOSE_PROFILES": "maintenance",
                    "DOCKER_CONTEXT": "remote",
                },
            ),
            patch.object(provision.subprocess, "run") as command,
        ):
            command.return_value.stdout = b"ok"
            self.assertEqual(provision.run("docker", "ps"), b"ok")
            args, keywords = command.call_args
            self.assertEqual(args[0], ["docker", "--context", "default", "ps"])
            self.assertNotIn("COMPOSE_PROJECT_NAME", keywords["env"])
            self.assertNotIn("COMPOSE_PROFILES", keywords["env"])

    def test_config_cas_retains_original_and_no_overwrite(self):
        before = self.config.read_bytes()
        sha = provision.digest(self.config)
        changed = copy.deepcopy(self.value)
        changed["project"] = "pwc-staging-new"
        provision.save_config(self.config, changed, sha)
        self.assertEqual(
            self.config.with_name("config.json.before-" + sha).read_bytes(), before
        )
        with self.assertRaises(ValueError):
            provision.save_config(self.config, self.value, sha)
        with self.assertRaises(FileExistsError):
            provision.write_new(self.config, b"overwrite")

    def test_private_path_and_permissions(self):
        self.config.chmod(0o644)
        with self.assertRaises(ValueError):
            provision.load(self.config)
        link = self.root / "link"
        link.symlink_to(self.config)
        with self.assertRaises(ValueError):
            provision.external(link)
        with self.assertRaises(ValueError):
            provision.external(Path.cwd() / "secret")

    def test_images_need_reviewed_digests_and_exact_config(self):
        sha = provision.digest(self.config)
        with self.assertRaises(ValueError):
            provision.apply_images(
                self.config, {k: "latest" for k in self.value["images"]}, sha
            )
        with self.assertRaises(ValueError):
            provision.apply_images(self.config, self.value["images"], "0" * 64)
        with patch.object(provision, "run", return_value=b"a" * 40 + b"\n"):
            provision.apply_images(self.config, self.value["images"], sha)
        self.assertEqual(provision.load(self.config)["release"], "a" * 40)
        self.assertEqual(provision.load(self.config)["files"], self.value["files"])

    def test_resolver_only_proposes_never_changes_config(self):
        before = self.config.read_bytes()
        references = ["reviewed@sha256:" + "b" * 64]
        with patch.object(
            provision,
            "run",
            side_effect=lambda *a: (
                json.dumps(references).encode() if "inspect" in a else b""
            ),
        ):
            provision.resolve_images(
                {k: "reviewed:tag" for k in self.value["images"]},
                self.root / "images.json",
            )
        self.assertEqual(self.config.read_bytes(), before)
        self.assertEqual(
            json.loads((self.root / "images.json").read_text())["python"], references[0]
        )

    def test_approval_binds_action_and_findings(self):
        bound = {"action": "bootstrap", "unfixed_high_critical": ["CVE-2026-1234"]}
        with self.assertRaises(ValueError):
            operate.authorize(bound, "wrong", None)
        risk = self.root / "risk.json"
        risk.write_text(
            json.dumps(
                {
                    "plan_sha256": operate.token(bound),
                    "reviewer": "named operator",
                    "accepted_unfixed_ids": bound["unfixed_high_critical"],
                }
            )
        )
        operate.authorize(bound, operate.token(bound), risk)
        changed = {**bound, "action": "expose"}
        with self.assertRaises(ValueError):
            operate.authorize(changed, operate.token(bound), risk)

    def test_health_requires_all_instances_healthy(self):
        for data in (
            [{"Service": "app", "State": "running", "Health": "unhealthy"}],
            [],
            [{"Service": "app", "State": "running", "Health": "healthy"}] * 2,
        ):
            with patch.object(operate, "run", return_value=json.dumps(data).encode()):
                with self.assertRaises(ValueError):
                    operate.healthy("manifest", ("app",))
        with patch.object(
            operate,
            "run",
            return_value=b'{"Service":"app","State":"running","Health":"healthy"}\n',
        ):
            operate.healthy("manifest", ("app",))

    def test_scan_rejects_image_mismatch_and_fixable_findings(self):
        images = {r: "sha256:" + "c" * 64 for r in operate.ROLES}
        bound = {"images": images}
        reports = self.root / "reports"
        reports.mkdir()
        (reports / "binding.json").write_text(json.dumps(bound))
        for index in range(1, 6):
            (reports / f"image-{index}.json").write_text(
                json.dumps(
                    {
                        "SchemaVersion": 2,
                        "Metadata": {"ImageID": images["app"]},
                        "Results": [{"Vulnerabilities": None}],
                    }
                )
            )
        with patch.object(
            operate, "binding", return_value=(self.value, "manifest", bound)
        ):
            operate.scan_binding(self.config, "render", reports)
            bad = reports / "image-1.json"
            data = json.loads(bad.read_text())
            data["Metadata"]["ImageID"] = "wrong"
            bad.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                operate.scan_binding(self.config, "render", reports)
            data["Metadata"]["ImageID"] = images["app"]
            data["Results"] = [
                {
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2026-1234",
                            "Severity": "HIGH",
                            "FixedVersion": "2",
                        }
                    ]
                }
            ]
            bad.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                operate.scan_binding(self.config, "render", reports)

    def test_offhost_command_pins_trust_and_rejects_shell_input(self):
        hosts = self.root / "known_hosts"
        hosts.write_text("operator supplied public host key\n")
        command = recovery.ssh_command(
            "backup@archive.example.org", hosts, "/private/backup.age", "a" * 64
        )
        self.assertIn("StrictHostKeyChecking=yes", command)
        self.assertIn("BatchMode=yes", command)
        for host, destination in [
            ("backup@host;id", "/backup"),
            ("backup@host", "/backup;id"),
        ]:
            with self.assertRaises(ValueError):
                recovery.ssh_command(host, hosts, destination, "a" * 64)

    def test_remote_ciphertext_publication_no_overwrite_and_readback(self):
        # Run exactly the fixed remote receiver locally against disposable files.
        destination = self.root / "backup.age"
        ciphertext = b"age-encryption.org/v1\nopaque encrypted bytes"
        import hashlib

        sha = hashlib.sha256(ciphertext).hexdigest()
        command = ["python3", "-c", recovery.REMOTE, str(destination), sha]
        completed = subprocess.run(
            command, input=ciphertext, capture_output=True, check=True
        )
        self.assertEqual(json.loads(completed.stdout)["sha256"], sha)
        subprocess.run(
            command, input=b"do not overwrite", capture_output=True, check=True
        )
        self.assertEqual(destination.read_bytes(), ciphertext)
        failed = subprocess.run(
            [*command[:-1], "b" * 64], input=b"", capture_output=True
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(destination.read_bytes(), ciphertext)

    def test_restore_requires_other_host_and_same_image_ids(self):
        encrypted = self.root / "backup.age"
        encrypted.write_bytes(b"encrypted fixture")
        source = {
            "source_machine": "source",
            "offhost_machine": "archive",
            "source_images": {"app": "image"},
            "sha256": provision.digest(encrypted),
        }
        receipt = self.root / "receipt.json"
        receipt.write_text(json.dumps(source))
        for machine in ("source", "archive"):
            with patch.object(
                operate,
                "binding",
                return_value=(
                    self.value,
                    "manifest",
                    {"machine": machine, "images": source["source_images"]},
                ),
            ):
                with self.assertRaises(ValueError):
                    recovery.restore_plan(self.config, "render", encrypted, receipt)
        with patch.object(
            operate,
            "binding",
            return_value=(
                self.value,
                "manifest",
                {"machine": "isolated", "images": {"app": "different"}},
            ),
        ):
            with self.assertRaises(ValueError):
                recovery.restore_plan(self.config, "render", encrypted, receipt)

    def test_unlabeled_canonical_volume_is_not_fresh(self):
        with patch.object(
            operate, "run", return_value=b"other_project_pgdata\npwc-staging_pgdata\n"
        ):
            self.assertTrue(operate.has_db_volume("pwc-staging"))
            self.assertFalse(operate.has_db_volume("pwc-staging-new"))

    def test_restore_never_touches_existing_volume(self):
        with (
            patch.object(
                recovery,
                "restore_plan",
                return_value=("manifest", {"action": "restore"}),
            ),
            patch.object(
                operate,
                "run",
                side_effect=[b"", (self.value["project"] + "_pgdata\n").encode()],
            ) as commands,
        ):
            with self.assertRaises(ValueError):
                recovery.rehearse(
                    self.config,
                    "render",
                    "backup",
                    "source",
                    "identity",
                    "receipt",
                    operate.token({"action": "restore"}),
                )
            self.assertEqual(commands.call_count, 2)

    def test_bootstrap_approval_precedes_every_docker_action(self):
        bound = {"images": {r: "image" for r in operate.ROLES}}
        with (
            patch(
                "sys.argv",
                [
                    "operate",
                    "bootstrap",
                    "--config",
                    str(self.config),
                    "--render",
                    "render",
                ],
            ),
            patch.object(
                operate, "scan_binding", return_value=(self.value, "manifest", bound)
            ),
            patch.object(operate, "run") as commands,
        ):
            self.assertEqual(operate.main(), 1)
            commands.assert_not_called()

    def test_approved_bootstrap_has_no_public_ingress_and_no_unreviewed_pull(self):
        bound = {"images": {r: "image" for r in operate.ROLES}, "action": "bootstrap"}
        argv = [
            "operate",
            "bootstrap",
            "--config",
            str(self.config),
            "--render",
            "render",
            "--approve-plan-sha256",
            operate.token(bound),
        ]
        with (
            patch("sys.argv", argv),
            patch.object(
                operate, "scan_binding", return_value=(self.value, "manifest", bound)
            ),
            patch.object(operate, "run", return_value=b"") as commands,
            patch.object(operate, "healthy"),
        ):
            self.assertEqual(operate.main(), 0)
            calls = [c.args for c in commands.call_args_list]
            self.assertEqual(len(calls), 5)
            self.assertEqual(calls[2][-1], "db")
            self.assertEqual(calls[3][-1], "migrate")
            self.assertEqual(calls[4][-1], "app")
            self.assertIn("--no-build", calls[2])
            self.assertFalse(
                any("gateway" in c or "ngo" in c or "ops" in c for c in calls)
            )

    def test_ingress_collision_fails_before_any_exposure(self):
        bound = {"images": {r: "image" for r in operate.ROLES}, "action": "expose"}
        argv = [
            "operate",
            "expose",
            "--config",
            str(self.config),
            "--render",
            "render",
            "--approve-plan-sha256",
            operate.token(bound),
        ]
        with (
            patch("sys.argv", argv),
            patch.object(
                operate,
                "deployment_binding",
                return_value=(self.value, "manifest", bound),
            ),
            patch.object(
                operate, "healthy", side_effect=[None, ValueError("missing ingress")]
            ),
            patch.object(
                operate, "require_free_ingress", side_effect=OSError("occupied")
            ),
            patch.object(operate, "run") as commands,
        ):
            self.assertEqual(operate.main(), 1)
            commands.assert_not_called()

    def test_running_container_image_must_match_scanned_id(self):
        rows = [
            {
                "Service": "app",
                "State": "running",
                "Health": "healthy",
                "ID": "container",
            }
        ]
        with patch.object(
            operate, "run", side_effect=[json.dumps(rows).encode(), b"wrong-image"]
        ):
            with self.assertRaises(ValueError):
                operate.healthy("manifest", ("app",), {"app": "approved-image"})

    def test_empty_public_probe_checks_both_hosts_and_closed_opportunities(self):
        requests = []

        class Client:
            def request(self, method, path, headers):
                self.path = path
                requests.append((method, path, headers))

            def getresponse(self):
                path = self.path

                class Response:
                    status = (
                        404
                        if "organizations" in path
                        else 503
                        if "opportunities" in path
                        else 200
                    )

                    def read(self, limit):
                        if "health" in path:
                            return b'{"status":"ok","service":"pwc-api"}'
                        if "organizations" in path:
                            return b'{"detail":"Not found"}'
                        if "opportunities" in path:
                            return b'{"error":{"code":"OPPORTUNITIES_UNAVAILABLE"}}'
                        return b'{"results":[],"next_cursor":null}'

                    def getheader(self, name):
                        return (
                            "application/json" if name == "Content-Type" else "no-store"
                        )

                return Response()

            def close(self):
                pass

        with patch.object(
            operate.http.client, "HTTPSConnection", return_value=Client()
        ):
            result = operate.verify(self.value)
        self.assertEqual(len(requests), 8)
        self.assertFalse(result["acceptance"])
        self.assertTrue(all(r[2] == {"Accept": "application/json"} for r in requests))

    def test_healthy_exact_bootstrap_repetition_is_noop(self):
        bound = {"images": {r: "image" for r in operate.ROLES}, "action": "bootstrap"}
        argv = [
            "operate",
            "bootstrap",
            "--config",
            str(self.config),
            "--render",
            "render",
            "--approve-plan-sha256",
            operate.token(bound),
        ]
        with (
            patch("sys.argv", argv),
            patch.object(
                operate, "scan_binding", return_value=(self.value, "manifest", bound)
            ),
            patch.object(
                operate, "run", return_value=b"existing container"
            ) as commands,
            patch.object(operate, "healthy"),
        ):
            self.assertEqual(operate.main(), 0)
            self.assertEqual(commands.call_count, 1)

    def test_public_probe_does_not_follow_redirects_or_accept_real_data(self):
        class Response:
            status = 200

            def read(self, limit):
                return b'{"results":[{"private":"not approved"}],"next_cursor":null}'

            def getheader(self, key):
                return "no-store"

        class Client:
            def request(self, method, path, headers):
                self.path = path
                assert headers == {"Accept": "application/json"}

            def getresponse(self):
                response = Response()
                if self.path.endswith("health/"):
                    response.read = lambda limit: b'{"service":"pwc-api"}'
                return response

            def close(self):
                pass

        with patch.object(
            operate.http.client, "HTTPSConnection", return_value=Client()
        ):
            with self.assertRaises(ValueError):
                operate.verify(self.value)


@unittest.skipUnless(
    os.getuid() == 0, "Real renderer bind-mount ownership requires disposable root"
)
class IssuerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.root.chmod(0o700)
        cls.value = config(cls.root)
        certificates(cls.value)
        # Paths and public hostnames are synthetic ONLY in this disposable test.

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(dir=self.root))
        self.config = self.directory / "config.json"
        self.config.write_text(json.dumps(self.value))
        self.config.chmod(0o600)
        self.csrs = {}
        for name in ("ngo_client", "ops_client"):
            self.csrs[name] = str(self.directory / (name + ".csr"))
            provision.run(
                "openssl",
                "req",
                "-new",
                "-key",
                self.value["files"][name + "_key"],
                "-subj",
                "/CN=pending",
                "-out",
                self.csrs[name],
            )
        # Fixtures use reserved domains; load is patched only at test boundary.
        self.loader = patch.object(
            provision, "load", side_effect=lambda p: json.loads(Path(p).read_text())
        )
        self.loader.start()
        self.addCleanup(self.loader.stop)

    def test_original_issuer_reuses_every_key_secret_and_other_ca(self):
        before = {n: Path(p).read_bytes() for n, p in self.value["files"].items()}
        issuer = self.root / "client_ca_key"
        issuer.chmod(0o600)
        output = self.directory / "issued"
        provision.clients(
            self.config, output, self.csrs, issuer, False, provision.digest(self.config)
        )
        changed = json.loads(self.config.read_text())
        for name, data in before.items():
            if name not in {n + "_cert" for n in provision.CLIENTS}:
                self.assertEqual(Path(changed["files"][name]).read_bytes(), data)
        provision.clients(
            self.config, output, self.csrs, issuer, False, provision.digest(self.config)
        )

    def test_replacement_requires_explicit_approval_rotates_all_three_only(self):
        issuer_dir = self.directory / "issuer"
        issuer_dir.mkdir(mode=0o700)
        key = issuer_dir / "new-ca.key"
        output = self.directory / "replacement"
        with self.assertRaises(ValueError):
            provision.clients(self.config, output, self.csrs, key, True, "wrong")
        self.assertFalse(key.exists())
        provision.clients(
            self.config, output, self.csrs, key, True, provision.digest(self.config)
        )
        changed = json.loads(self.config.read_text())
        self.assertEqual(key.stat().st_mode & 0o777, 0o600)
        self.assertNotEqual(
            changed["files"]["client_ca"], self.value["files"]["client_ca"]
        )
        for name in provision.CLIENTS:
            provision.checked_client(
                changed["files"][name + "_cert"],
                changed["files"][name + "_key"],
                changed["files"]["client_ca"],
                name,
            )
        for name in ("public_ca", "app_ca", "db_ca", *provision.deploy.PASSWORDS):
            self.assertEqual(changed["files"][name], self.value["files"][name])

    def test_offline_issuer_import_needs_no_ca_key_on_runtime_host(self):
        issuer = self.root / "client_ca_key"
        issuer.chmod(0o600)
        provision.clients(
            self.config,
            self.directory / "issuer-returned",
            self.csrs,
            issuer,
            False,
            provision.digest(self.config),
        )
        issued = json.loads(self.config.read_text())
        self.config.write_text(json.dumps(self.value))
        public_certificates = {
            name: issued["files"][name + "_cert"]
            for name in ("ngo_client", "ops_client")
        }
        provision.import_clients(
            self.config, public_certificates, provision.digest(self.config)
        )
        imported = json.loads(self.config.read_text())
        self.assertEqual(
            imported["files"]["health_cert"], self.value["files"]["health_cert"]
        )
        self.assertEqual(
            imported["files"]["client_ca"], self.value["files"]["client_ca"]
        )

    def test_bad_csr_or_issuer_never_switches_config(self):
        before = self.config.read_bytes()
        issuer = self.root / "client_ca_key"
        issuer.chmod(0o600)
        self.csrs["ngo_client"] = self.csrs["ops_client"]
        with self.assertRaises(ValueError):
            provision.clients(
                self.config,
                self.directory / "bad",
                self.csrs,
                issuer,
                False,
                provision.digest(self.config),
            )
        self.assertEqual(before, self.config.read_bytes())
