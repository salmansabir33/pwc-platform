import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from staging_fixtures import config, deploy, ROOT


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.value = config("/tmp/pwc-fixture-not-real")

    def invalid(self, field, value):
        self.value[field] = value
        with self.assertRaises((ValueError, TypeError)):
            deploy.metadata(self.value, synthetic=True)

    def test_exact_metadata(self):
        self.assertIs(deploy.metadata(self.value, synthetic=True), self.value)
        with self.assertRaises(ValueError):
            deploy.metadata(self.value)

    def test_invalid_hosts(self):
        for host in (
            "localhost",
            "127.0.0.1",
            "*.pwc.test",
            ".pwc.test",
            "https://ngo.pwc.test",
            "NGO.pwc.test",
            "ngo.pwc.test:443",
            "ngo.pwc.test/path",
            "ngo.pwc.test\n",
            "ngo.pwc.test.",
            "ops.pwc.test",
            "a..test",
            "ngo.pwc.invalid",
        ):
            with self.subTest(host=host):
                self.invalid("ngo_host", host)

    def test_unknown_options_and_duplicate_keys(self):
        self.value["PWC_AUTH_SESSIONS_ENABLED"] = "1"
        with self.assertRaises(ValueError):
            deploy.metadata(self.value, synthetic=True)
        with self.assertRaises(ValueError):
            json.loads(
                '{"ngo_host":"a","ngo_host":"b"}', object_pairs_hook=deploy.unique
            )

    def test_invalid_images_and_paths(self):
        for image in (
            "postgres:16",
            "postgres:latest",
            "repo@sha256:abc",
            "repo@sha256:" + "g" * 64,
            "${IMAGE}",
        ):
            self.value["images"]["postgres"] = image
            with self.assertRaises(ValueError):
                deploy.metadata(self.value, synthetic=True)
        self.value = config("/tmp/fixture")
        for path in ("relative", str(ROOT / "secret"), "/tmp/${SECRET}", "/tmp/a:b"):
            self.value["files"]["django_secret"] = path
            with self.assertRaises(ValueError):
                deploy.metadata(self.value, synthetic=True)

    def test_network_and_exposure(self):
        document = deploy.compose(self.value, Path("/tmp/rendered"))
        services = document["services"]
        self.assertEqual(
            {name for name, service in services.items() if "ports" in service},
            {"gateway"},
        )
        self.assertEqual(services["gateway"]["ports"], ["443:8443"])
        self.assertEqual(
            services["db"]["networks"], {"database": {"aliases": ["db.pwc.internal"]}}
        )
        self.assertEqual(set(services["app"]["networks"]), {"application", "database"})
        for name in ("routing", "application", "database"):
            self.assertTrue(document["networks"][name]["internal"])
        self.assertEqual(
            {
                name
                for name, service in services.items()
                if "public" in service["networks"]
            },
            {"gateway"},
        )
        self.assertIn("pgdata:/var/lib/postgresql/data", services["db"]["volumes"])
        for service in services.values():
            self.assertTrue(service["read_only"])
            self.assertEqual(service["cap_drop"], ["ALL"])
            self.assertNotIn("privileged", service)
            self.assertNotIn("network_mode", service)

    def test_gates_secrets_and_startup(self):
        document = deploy.compose(self.value, Path("/tmp/rendered"))
        app = document["services"]["app"]
        from config.environment import FLAGS

        for flag in FLAGS:
            self.assertEqual(app["environment"][flag], "0")
        self.assertEqual(app["environment"]["DB_SSLMODE"], "verify-full")
        for key in ("DJANGO_SECRET_KEY", "DB_PASSWORD", "PWC_AUTH_ABUSE_KEY"):
            self.assertNotIn(key, app["environment"])
            self.assertTrue(
                app["environment"][key + "_FILE"].startswith("/run/secrets/")
            )
        self.assertNotIn("db_owner_password", app["secrets"])
        self.assertEqual(document["services"]["migrate"]["profiles"], ["maintenance"])
        self.assertEqual(
            document["services"]["ngo"]["depends_on"],
            {"app": {"condition": "service_healthy"}},
        )
        self.assertEqual(app["healthcheck"]["test"][-1], "health")

    def test_separate_portals_and_no_header_trust(self):
        for name in ("ngo", "ops"):
            host = self.value[name + "_host"]
            rendered = deploy.portal(host)
            self.assertIn('if ($http_host != "' + host + '")', rendered)
            self.assertIn('if ($ssl_server_name != "' + host + '")', rendered)
            self.assertIn("proxy_ssl_verify on", rendered)
            self.assertIn("proxy_pass https://app.pwc.internal:8443", rendered)
            self.assertIn("proxy_pass_request_headers off", rendered)
            for header in (
                "Origin",
                "Referer",
                "Authorization",
                "X-CSRFToken",
                "Cookie",
            ):
                self.assertIn("proxy_set_header " + header, rendered)
            self.assertNotIn("X-Forwarded", rendered)
            self.assertNotIn("Access-Control-Allow", rendered)
            self.assertNotIn("http://", rendered)
            self.assertIn("ssl_reject_handshake on", rendered)
            self.assertIn("Cache-Control no-store always", rendered)

    def test_redacted_cli_and_missing_files_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(self.value))
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "infra/staging/deploy.py"),
                    "--config",
                    str(path),
                    "--output",
                    directory + "/out",
                    "--synthetic",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertNotIn(self.value["files"]["django_secret"], result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse((Path(directory) / "out").exists())

    def test_builds_are_distinct_and_no_runserver(self):
        value = deploy.compose(self.value, Path("/tmp/rendered"))["services"]
        self.assertNotEqual(value["ngo"]["image"], value["ops"]["image"])
        self.assertNotEqual(
            value["ngo"]["build"]["args"]["PORTAL"],
            value["ops"]["build"]["args"]["PORTAL"],
        )
        runtime = (ROOT / "infra/staging/runtime.py").read_text()
        self.assertNotIn("runserver", runtime)
        self.assertIn('call_command("migrate", check=True', runtime)
        gunicorn = (ROOT / "infra/staging/gunicorn.conf.py").read_text()
        self.assertIn("ssl.CERT_REQUIRED", gunicorn)
        self.assertIn("secure_scheme_headers = {}", gunicorn)
        self.assertIn('forwarded_allow_ips = ""', gunicorn)
        settings = (ROOT / "apps/backend/config/staging.py").read_text()
        self.assertIn("SECURE_PROXY_SSL_HEADER = None", settings)

    def test_permission_and_certificate_failures(self):
        # Full OpenSSL/permission/expiry negative tests also run in hosted stack.
        value = copy.deepcopy(self.value)
        with patch.object(Path, "is_symlink", return_value=True):
            with self.assertRaises(ValueError):
                deploy.files(value)
