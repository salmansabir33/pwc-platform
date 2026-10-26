"""Configuration regression tests; no database or operational secrets needed."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from config.environment import EnvironmentError, FLAGS, load_environment, origin


class EnvironmentTests(unittest.TestCase):
    def deployment(self):
        return {
            "PWC_ENVIRONMENT": "production",
            "DJANGO_SECRET_KEY": "s" * 60,
            "DJANGO_ALLOWED_HOSTS": "api.pwc.example.org",
            "DB_NAME": "pwc",
            "DB_USER": "pwc_runtime",
            "DB_HOST": "db.pwc.example.org",
            "DB_PASSWORD": "d" * 40,
            "DB_SSLMODE": "verify-full",
            "DB_SSLROOTCERT": "/run/secrets/db-ca.crt",
        }

    def test_defaults_are_disabled(self):
        config = load_environment({})
        self.assertEqual(config["PWC_ENVIRONMENT"], "development")
        self.assertTrue(all(config[key] is False for key in FLAGS))

    def test_profiles_are_closed(self):
        for value in ("prod", "", "TEST"):
            with self.subTest(value=value), self.assertRaises(EnvironmentError):
                load_environment({"PWC_ENVIRONMENT": value})

    def test_flags_are_exact_and_errors_redacted(self):
        for key in FLAGS:
            for value in ("true", "false", "yes", "", "sensitive-value"):
                with (
                    self.subTest(key=key, value=value),
                    self.assertRaises(EnvironmentError) as caught,
                ):
                    load_environment({key: value})
                self.assertNotIn(value, str(caught.exception)) if value else None

    def test_json_errors_are_redacted(self):
        for value in (
            "[1]",
            "null",
            '{"a":"secret","a":"other"}',
            '{"a":{}}',
            "sensitive-value",
        ):
            with (
                self.subTest(value=value),
                self.assertRaises(EnvironmentError) as caught,
            ):
                load_environment({"PWC_AUTH_DELIVERY_KEYS": value})
            self.assertNotIn("secret", str(caught.exception))
            self.assertNotIn("sensitive-value", str(caught.exception))

    def test_exact_https_origins(self):
        self.assertEqual(
            origin("https://ngo.example.org:8443", "origin"),
            "https://ngo.example.org:8443",
        )
        for value in (
            "http://ngo.invalid",
            "https://u:p@ngo.invalid",
            "https://ngo.invalid/",
            "https://ngo.invalid?q=secret",
            "https://ngo.invalid?",
            "https://ngo.invalid#",
            "https://ngo.invalid:",
            "https://*.invalid",
            "https://ngo.invalid#x",
            "https://ngo.invalid:0",
            "https://ngo.invalid:99999",
            "https://ngo.invalid\\evil",
            "https://ngo.invalid\n",
        ):
            with self.subTest(value=value), self.assertRaises(EnvironmentError):
                origin(value, "origin")

    def test_portal_map_matches_existing_closed_names(self):
        for mapping in (
            {"https://ngo.invalid": "admin"},
            {"https://a.invalid": "ngo_web", "https://b.invalid": "ngo_web"},
        ):
            with self.assertRaises(EnvironmentError):
                load_environment({"PWC_AUTH_PORTALS": json.dumps(mapping)})
        load_environment(
            {
                "PWC_AUTH_PORTALS": json.dumps(
                    {"https://ngo.invalid": "ngo_web", "https://ops.invalid": "pwc_ops"}
                )
            }
        )

    def test_database_port_and_tls_grammar(self):
        for key, value in (
            ("DB_PORT", "0"),
            ("DB_PORT", "65536"),
            ("DB_PORT", "abc"),
            ("DB_SSLMODE", "insecure"),
        ):
            with (
                self.subTest(key=key, value=value),
                self.assertRaises(EnvironmentError),
            ):
                load_environment({key: value})

    def test_synthetic_development_still_supported(self):
        load_environment({"PWC_AUTHORIZATION_ENVIRONMENT": "synthetic_development"})
        with self.assertRaises(EnvironmentError):
            load_environment({"PWC_AUTHORIZATION_ENVIRONMENT": "real"})

    def test_no_live_delivery_mode(self):
        with self.assertRaises(EnvironmentError):
            load_environment({"PWC_AUTH_DELIVERY_MODE": "smtp"})

    def test_hosts_do_not_accept_wildcards_or_urls(self):
        for value in (
            "*",
            ".example.org",
            "https://api.invalid",
            "api.invalid:8000",
            "bad-.invalid",
            "-bad.invalid",
            "",
        ):
            with self.subTest(value=value), self.assertRaises(EnvironmentError):
                load_environment({"DJANGO_ALLOWED_HOSTS": value})

    def test_disabled_deployment_profiles_validate_offline(self):
        for profile in ("staging", "production"):
            env = self.deployment() | {"PWC_ENVIRONMENT": profile}
            self.assertEqual(
                load_environment(env)["DB_OPTIONS"]["sslmode"], "verify-full"
            )

    def test_deployment_rejects_every_feature_enable(self):
        for key in FLAGS:
            with self.subTest(key=key), self.assertRaises(EnvironmentError):
                load_environment(self.deployment() | {key: "1"})

    def test_deployment_requires_explicit_database_and_secrets(self):
        for key in (
            "DJANGO_SECRET_KEY",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
            "DB_HOST",
            "DB_SSLROOTCERT",
        ):
            env = self.deployment()
            del env[key]
            with self.subTest(key=key), self.assertRaises(EnvironmentError):
                load_environment(env)

    def test_deployment_rejects_weak_tls_placeholders_and_local_hosts(self):
        for key, value in (
            ("DB_SSLMODE", "require"),
            ("DJANGO_SECRET_KEY", "test-only-" + "s" * 60),
            ("DJANGO_ALLOWED_HOSTS", "localhost"),
            ("PWC_AUTHORIZATION_ENVIRONMENT", "synthetic_test"),
        ):
            with self.subTest(key=key), self.assertRaises(EnvironmentError):
                load_environment(self.deployment() | {key: value})

    def test_deployment_settings_keep_direct_https_and_features_off(self):
        code = """
import django
django.setup()
from django.conf import settings
assert settings.SECURE_SSL_REDIRECT
assert settings.SECURE_PROXY_SSL_HEADER is None
assert not settings.USE_X_FORWARDED_HOST
assert not settings.USE_X_FORWARDED_PORT
assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
assert settings.PWC_AUTH_DELIVERY_MODE == 'synthetic'
assert not settings.PWC_AUTH_SESSIONS_ENABLED
assert not settings.PWC_SYNTHETIC_AUTHORIZATION_ENABLED
from django.test import Client
client = Client()
response = client.get('/api/v1/health/', HTTP_HOST='api.pwc.example.org', HTTP_X_FORWARDED_PROTO='https')
assert response.status_code == 301
assert response['Location'] == 'https://api.pwc.example.org/api/v1/health/'
response = client.get('/api/v1/health/', secure=True, HTTP_HOST='api.pwc.example.org', HTTP_X_FORWARDED_HOST='attacker.invalid')
assert response.status_code == 200
assert client.get('/api/v1/health/', secure=True, HTTP_HOST='attacker.invalid').status_code == 400
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[1],
            env=os.environ
            | self.deployment()
            | {"DJANGO_SETTINGS_MODULE": "config.settings"},
            capture_output=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            "Deployment settings subprocess failed (output redacted)",
        )
