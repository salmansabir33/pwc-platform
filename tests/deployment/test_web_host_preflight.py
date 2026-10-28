"""Unit checks for the observer, NOT production-host evidence."""

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "preflight", Path(__file__).resolve().parents[2] / "scripts/web_host_preflight.py"
)
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)


class PreflightTests(unittest.TestCase):
    def test_requires_real_separate_exact_https_named_hosts(self):
        for value in (
            "http://ngo.example.org",
            "https://ngo.pwc.invalid",
            "https://127.0.0.1",
            "https://localhost",
            "https://ngo.example.org/",
            "https://x@ngo.example.org",
            "https://*.example.org",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                preflight.portal_pair(value, "https://ops.example.org")
        with self.assertRaises(ValueError):
            preflight.portal_pair(
                "https://ngo.example.org", "https://ngo.example.org:444"
            )

    def test_cookie_values_never_emitted(self):
        result = preflight.cookie_observations(
            ["csrftoken=synthetic-secret; Secure; Path=/; SameSite=Lax"]
        )
        self.assertTrue(result["csrf_secure"])
        self.assertTrue(result["csrf_host_only"])
        self.assertNotIn("synthetic-secret", str(result))
        bad = preflight.cookie_observations(
            ["csrftoken=synthetic; Domain=.example.org; Path=/api; SameSite=None"]
        )
        self.assertFalse(bad["csrf_secure"])
        self.assertFalse(bad["csrf_host_only"])
        self.assertFalse(bad["csrf_root_path"])
        self.assertFalse(bad["csrf_safe_same_site"])

    def test_dns_private_targets_not_probed(self):
        with (
            patch.object(
                preflight.socket,
                "getaddrinfo",
                return_value=[(2, 1, 6, "", ("127.0.0.1", 443))],
            ),
            patch.object(preflight, "request_observation") as request,
        ):
            self.assertEqual(
                preflight.observe("https://ngo.example.org")["failure"],
                "DNS_NOT_PUBLIC",
            )
            request.assert_not_called()

    def test_failures_are_redacted_not_accepted(self):
        with patch.object(
            preflight.socket, "getaddrinfo", side_effect=OSError("sensitive exception")
        ):
            result = preflight.observe("https://ngo.example.org")
            self.assertFalse(result["observed"])
            self.assertNotIn("sensitive", str(result))


if __name__ == "__main__":
    unittest.main()
