"""Disposable direct-TLS browser → Django → actual PostgreSQL, synthetic only.

Run after building auth-harness. Not deployed, no proxy headers, fixture routes,
production networking toggle, real identity data or live-ingress acceptance.
"""

import json
import mimetypes
import os
from pathlib import Path
import ssl
import subprocess
import sys
import tempfile
from threading import Thread
from socketserver import ThreadingMixIn
import unittest
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()
from django.conf import settings  # noqa: E402
from django.core.handlers.wsgi import WSGIHandler  # noqa: E402
from django.test import override_settings  # noqa: E402
from django.test.utils import setup_databases, teardown_databases  # noqa: E402
from accounts.test_mfa import MFA_CONFIG, MfaFixtures
from accounts.test_registration import PASSWORD
from accounts.models import AuthSession
from django.utils import timezone
from datetime import timedelta
import pyotp
from accounts.test_sessions import NGO, OPS  # noqa: E402
from organizations.test_verification import CONFIG, VerificationFixtures  # noqa: E402
from organizations.models import RegistryEvent, OrganizationAccess  # noqa: E402
from access.models import NGOGrant  # noqa: E402


class TLSHandler(WSGIRequestHandler):
    def get_environ(self):
        assert isinstance(self.connection, ssl.SSLSocket)
        env = super().get_environ()
        env["HTTPS"] = "on"  # Actual socket TLS, never a forwarded-header trust rule.
        return env

    def log_message(self, *_):
        pass  # Never log session/cookie payloads.


class Server(ThreadingMixIn, WSGIServer):
    daemon_threads = True


class Fixtures(VerificationFixtures, unittest.TestCase):
    pass


class BrowserMfaFixtures(MfaFixtures, unittest.TestCase):
    pass


def run():
    if settings.PWC_ENVIRONMENT != "test":
        raise SystemExit(
            "Requires explicit PWC_ENVIRONMENT=test and disposable PostgreSQL"
        )
    if not str(settings.DATABASES["default"]["NAME"]).startswith("pwc_synthetic_"):
        raise SystemExit(
            "Requires explicitly named disposable pwc_synthetic_* database"
        )
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.postgresql":
        raise SystemExit("PostgreSQL required")
    build = ROOT / ".cache/auth-harness"
    if not (build / "index.html").is_file():
        raise SystemExit("Build the NONSHIPPED auth-harness first")
    database = setup_databases(verbosity=0, interactive=False)
    try:
        with (
            tempfile.TemporaryDirectory() as temporary,
            override_settings(
                **dict(
                    CONFIG,
                    **{
                        k: v
                        for k, v in MFA_CONFIG.items()
                        if k.startswith("PWC_AUTH_MFA")
                    },
                )
            ),
        ):
            cert, key = Path(temporary) / "cert.pem", Path(temporary) / "key.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "1",
                    "-subj",
                    "/CN=synthetic.invalid",
                    "-addext",
                    f"subjectAltName=DNS:{NGO},DNS:{OPS}",
                    "-keyout",
                    str(key),
                    "-out",
                    str(cert),
                ],
                check=True,
                capture_output=True,
            )
            handler = WSGIHandler()

            def app(env, start):
                if env["PATH_INFO"].startswith("/api/"):
                    return handler(env, start)
                path = (build / env["PATH_INFO"].lstrip("/")).resolve()
                if not path.is_relative_to(build.resolve()) or not path.is_file():
                    path = build / "index.html"
                content = path.read_bytes()
                start(
                    "200 OK",
                    [
                        (
                            "Content-Type",
                            mimetypes.guess_type(str(path))[0]
                            or "application/octet-stream",
                        ),
                        ("Content-Length", str(len(content))),
                        ("Cache-Control", "no-store"),
                    ],
                )
                return [content]

            server = make_server(
                "0.0.0.0", 0, app, server_class=Server, handler_class=TLSHandler
            )
            port = server.server_port
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert, key)
            server.socket = context.wrap_socket(server.socket, server_side=True)
            portals = {
                f"https://{NGO}:{port}": "ngo_web",
                f"https://{OPS}:{port}": "pwc_ops",
            }
            with override_settings(PWC_AUTH_PORTALS=portals):
                f = Fixtures()
                f.setup_verification()
                f.case()
                source = f.source["id"]
                # Browser performs real password/MFA login; no positive cookie injection.
                mf = BrowserMfaFixtures()
                mf.user, _ = f.account("browser-mfa")
                mf.auth = mf.mobile(mf.user)
                mf.token = mf.auth["access_token"]
                enrolled = mf.enrollment()
                activation = mf.call(
                    "mfa/enrollment/confirm",
                    {
                        "enrollment_id": enrolled["enrollment_id"],
                        "code": pyotp.TOTP(enrolled["secret"]).now(),
                    },
                )
                mf.assertEqual(activation.status_code, 200)
                negatives = {}
                for name in ("revoked", "expired", "inactive"):
                    user, _ = f.account("browser-" + name)
                    client, response = f.web(user, host=f"{NGO}:{port}")
                    session_id = response.json()["session"]["id"]
                    if name == "revoked":
                        AuthSession.objects.filter(pk=session_id).update(
                            revoked_at=timezone.now(), revocation_reason="logout"
                        )
                    elif name == "expired":
                        AuthSession.objects.filter(pk=session_id).update(
                            created_at=timezone.now() - timedelta(hours=2),
                            last_interactive_at=timezone.now() - timedelta(hours=1),
                            absolute_expires_at=timezone.now() - timedelta(seconds=1),
                        )
                    else:
                        user.is_active = False
                        user.save()
                    negatives[name] = [
                        {
                            "name": m.key,
                            "value": m.value,
                            "url": f"https://{NGO}:{port}/",
                            "secure": True,
                            "httpOnly": bool(m["httponly"]),
                            "sameSite": "Lax",
                        }
                        for m in client.cookies.values()
                    ]
                fixture = {
                    "port": port,
                    "certificate": str(cert),
                    "source": source,
                    "accounts": {
                        "owner": f.user.email,
                        "foreign": f.other.email,
                        "ops": f.user.email,
                        "mfa": mf.user.email,
                    },
                    "password": PASSWORD,
                    "mfaSecret": enrolled["secret"],
                    "recoveryCode": activation.json()["recovery_codes"][0],
                    "negatives": negatives,
                }
                # Historical fixtures only; actual browser workload has intake closed.
                with override_settings(PWC_LEGACY_ONBOARDING_TEST_EXERCISE=False):
                    thread = Thread(target=server.serve_forever, daemon=True)
                    thread.start()
                    try:
                        subprocess.run(
                            ["node", "tests/end-to-end/authenticated-workspace.mjs"],
                            cwd=ROOT,
                            env={
                                **os.environ,
                                "PWC_SYNTHETIC_BROWSER_FIXTURE": json.dumps(fixture),
                            },
                            check=True,
                        )
                    finally:
                        server.shutdown()
                        server.server_close()
                        thread.join()
                assert (
                    RegistryEvent.objects.filter(
                        draft_id=source, action="withdraw"
                    ).count()
                    == 1
                )
                assert not OrganizationAccess.objects.exists()
                assert not NGOGrant.objects.exists()
                print(
                    "Direct TLS synthetic browser/Django/PostgreSQL: PASS; one withdrawal event, no authority granted. NOT live W2 acceptance."
                )
    finally:
        teardown_databases(database, verbosity=0)


if __name__ == "__main__":
    run()
