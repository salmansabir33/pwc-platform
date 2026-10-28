"""Approved web ingress/cookie invariants on actual PostgreSQL. Synthetic only."""

from django.conf import settings
from django.test import Client, TestCase, override_settings
from .test_sessions import SessionFixtures, SESSION_CONFIG, NGO, OPS
from .test_registration import PASSWORD
from .models import AuthSession


@override_settings(**SESSION_CONFIG)
class WebIngressTests(SessionFixtures, TestCase):
    def setUp(self):
        self.user, _ = self.account("web-ingress")
        self.client, _ = self.web(self.user)

    def token(self):
        return self.client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]

    def test_cookie_contract_and_non_cacheable_no_redirect_json(self):
        client, response = self.web(self.user)
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["secure"])
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["domain"], "")
        self.assertEqual(cookie["path"], "/")
        self.assertEqual(cookie["samesite"], "Lax")
        for path in ("/api/v1/auth/csrf/", "/api/v1/auth/me/"):
            response = client.get(path, secure=True, HTTP_HOST=NGO)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertEqual(response["Referrer-Policy"], "no-referrer")
            self.assertNotIn("Location", response)
            self.assertNotIn("Access-Control-Allow-Origin", response)
        anonymous = Client().get("/api/v1/auth/me/", secure=True, HTTP_HOST=NGO)
        self.assertEqual(anonymous.status_code, 401)
        self.assertNotIn("Location", anonymous)

    def test_unsafe_csrf_cookie_configuration_fails_closed(self):
        for config in (
            {"CSRF_COOKIE_DOMAIN": ".pwc.invalid"},
            {"CSRF_COOKIE_SECURE": False},
            {"CSRF_COOKIE_PATH": "/api/"},
            {"CSRF_COOKIE_SAMESITE": "None"},
            {"CSRF_TRUSTED_ORIGINS": [f"https://{OPS}"]},
            {"CSRF_TRUSTED_ORIGINS": ["https://*.pwc.invalid"]},
        ):
            with self.subTest(config=list(config)), override_settings(**config):
                result = self.get_me(client=self.client, host=NGO)
                self.assertEqual(result.status_code, 503)
                self.assertNotIn(str(self.user.pk).encode(), result.content)

    def test_no_proxy_setting_can_convert_plaintext_to_credentialed_https(self):
        for headers in (
            {"HTTP_X_FORWARDED_PROTO": "https"},
            {"HTTP_FORWARDED": f"proto=https;host={NGO}"},
            {"HTTP_X_FORWARDED_PROTO": "http,https", "HTTP_X_FORWARDED_HOST": NGO},
        ):
            response = self.client.post(
                "/api/v1/auth/web/login/",
                {"email": self.user.email, "password": PASSWORD},
                content_type="application/json",
                HTTP_HOST=NGO,
                HTTP_ORIGIN=f"https://{NGO}",
                HTTP_X_CSRFTOKEN=self.token(),
                **headers,
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["error"]["code"], "TRANSPORT_NOT_ALLOWED")
        for config in (
            {"SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https")},
            {"USE_X_FORWARDED_HOST": True},
            {"USE_X_FORWARDED_PORT": True},
        ):
            with override_settings(**config):
                self.assertEqual(
                    self.get_me(client=self.client, host=NGO).status_code, 503
                )

    def test_host_and_origin_claims_cannot_rebind_cookie_or_logout_owner(self):
        before = AuthSession.objects.filter(
            user=self.user, revoked_at__isnull=True
        ).count()
        token = self.token()
        for origin in (
            f"https://{OPS}",
            f"https://{NGO}.evil.invalid",
            "null",
            f"http://{NGO}",
        ):
            response = self.post_api(
                "logout",
                {},
                client=self.client,
                host=NGO,
                HTTP_ORIGIN=origin,
                HTTP_X_CSRFTOKEN=token,
            )
            self.assertEqual(response.status_code, 403)
        self.assertEqual(
            AuthSession.objects.filter(user=self.user, revoked_at__isnull=True).count(),
            before,
        )
        for host in (OPS, NGO + ":444", "unlisted.invalid"):
            response = self.get_me(client=self.client, host=host)
            self.assertIn(response.status_code, (400, 401))
        response = self.get_me(
            client=self.client,
            host=NGO,
            HTTP_X_FORWARDED_HOST=OPS,
            HTTP_X_FORWARDED_PROTO="http",
            HTTP_X_FORWARDED_FOR="203.0.113.12",
            HTTP_FORWARDED=f"proto=http;host={OPS}",
        )
        self.assertEqual(response.status_code, 200)
