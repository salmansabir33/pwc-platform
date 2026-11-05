"""Actual disposable TLS SMTP; never a provider/deliverability acceptance test."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import socketserver
import ssl
import subprocess
import tempfile
from threading import Thread
from unittest.mock import Mock, patch

from django.core import mail
from django.core.mail.backends.smtp import EmailBackend
from django.test import SimpleTestCase, override_settings

from .delivery import deliver_message
from .prepared_mail import MailConfiguration, PreparedMailError, PreparedSmtpAdapter


class PreparedMailFixtures:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.directory = tempfile.TemporaryDirectory(prefix="pwc-synthetic-smtp-")
        root = Path(cls.directory.name)
        cert, key = root / "cert.pem", root / "key.pem"
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
                "/CN=localhost",
                "-addext",
                "subjectAltName=IP:127.0.0.1,DNS:localhost",
                "-keyout",
                str(key),
                "-out",
                str(cert),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.server_tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        cls.server_tls.load_cert_chain(cert, key)
        cls.client_tls = ssl.create_default_context(cafile=str(cert))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()
        super().tearDownClass()

    def configuration(self, *, port=465, mode="tls", **changes):
        values = dict(
            host="127.0.0.1",
            port=port,
            mode=mode,
            username="smtp-user",
            password="synthetic-mail-password",
            sender="sender@example.invalid",
        )
        values.update(changes)
        return MailConfiguration(**values)

    def send(self, adapter, **changes):
        values = dict(
            recipient="recipient@example.invalid",
            subject="Synthetic confirmation",
            body="Synthetic message, no real invitation.",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        values.update(changes)
        return adapter.send(**values)

    def trusted_backend(self, **kwargs):
        backend = EmailBackend(**kwargs)
        backend.ssl_context = self.client_tls
        return backend

    def smtp(self, mode, *, advertise_tls=True, reject_recipient=False):
        tls = self.server_tls

        class Handler(socketserver.StreamRequestHandler):
            def handle(self):
                self.server.connections += 1
                self.connection.settimeout(5)
                secure = mode == "tls"
                if secure:
                    self.connection = tls.wrap_socket(self.connection, server_side=True)
                    self.rfile = self.connection.makefile("rb")
                    self.wfile = self.connection.makefile("wb")
                self.wfile.write(b"220 synthetic SMTP\r\n")
                self.wfile.flush()
                while True:
                    line = self.rfile.readline(8192)
                    if not line:
                        break
                    command = line.split(b" ")[0].strip().upper()
                    if command == b"EHLO":
                        self.wfile.write(
                            b"250-localhost\r\n250 AUTH PLAIN\r\n"
                            if secure
                            else b"250-localhost\r\n250 STARTTLS\r\n"
                            if advertise_tls
                            else b"250 localhost\r\n"
                        )
                    elif command == b"STARTTLS" and not secure:
                        self.wfile.write(b"220 TLS required\r\n")
                        self.wfile.flush()
                        self.connection = tls.wrap_socket(
                            self.connection, server_side=True
                        )
                        self.rfile = self.connection.makefile("rb")
                        self.wfile = self.connection.makefile("wb")
                        secure = True
                        continue
                    elif command == b"AUTH" and secure:
                        self.server.authenticated = True
                        self.wfile.write(b"235 authenticated\r\n")
                    elif command == b"RCPT" and secure and reject_recipient:
                        self.wfile.write(b"550 recipient rejected\r\n")
                    elif command in {b"MAIL", b"RCPT"} and secure:
                        self.wfile.write(b"250 accepted\r\n")
                    elif command == b"DATA" and secure:
                        self.wfile.write(b"354 data\r\n")
                        self.wfile.flush()
                        data = bytearray()
                        while len(data) < 65536:
                            part = self.rfile.readline(8192)
                            if part in {b".\r\n", b""}:
                                break
                            data.extend(part)
                        self.server.messages.append(bytes(data))
                        self.wfile.write(b"250 accepted\r\n")
                    elif command == b"QUIT":
                        self.wfile.write(b"221 bye\r\n")
                        self.wfile.flush()
                        break
                    else:
                        self.wfile.write(b"550 rejected\r\n")
                    self.wfile.flush()

        class Server(socketserver.ThreadingTCPServer):
            daemon_threads = True

            def handle_error(self, *_):
                pass  # Expected failed certificate handshake; no payload logs.

        server = Server(("127.0.0.1", 0), Handler)
        server.messages, server.authenticated, server.connections = [], False, 0
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 5)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server


class PreparedMailTests(PreparedMailFixtures, SimpleTestCase):
    def test_real_starttls_and_implicit_tls_single_delivery(self):
        for mode in ("tls", "starttls"):
            with self.subTest(mode=mode):
                server = self.smtp(mode)
                adapter = PreparedSmtpAdapter(
                    self.configuration(port=server.server_address[1], mode=mode),
                    _backend_factory=self.trusted_backend,
                )
                self.send(adapter)
                self.assertTrue(server.authenticated)
                self.assertEqual(len(server.messages), 1)
                self.assertIn(b"Synthetic confirmation", server.messages[0])

    def test_untrusted_certificate_never_falls_back_or_delivers(self):
        for mode in ("tls", "starttls"):
            with self.subTest(mode=mode):
                server = self.smtp(mode)
                adapter = PreparedSmtpAdapter(
                    self.configuration(port=server.server_address[1], mode=mode)
                )
                with self.assertRaisesRegex(PreparedMailError, "^MAIL_UNAVAILABLE$"):
                    self.send(adapter)
                self.assertEqual(server.messages, [])
                self.assertFalse(server.authenticated)

    def test_starttls_downgrade_never_authenticates_or_delivers_plaintext(self):
        server = self.smtp("starttls", advertise_tls=False)
        adapter = PreparedSmtpAdapter(
            self.configuration(port=server.server_address[1], mode="starttls")
        )
        with self.assertRaisesRegex(PreparedMailError, "^MAIL_UNAVAILABLE$"):
            self.send(adapter)
        self.assertEqual(server.messages, [])
        self.assertFalse(server.authenticated)
        self.assertEqual(server.connections, 1)

    def test_real_recipient_rejection_never_delivers_or_retries(self):
        server = self.smtp("tls", reject_recipient=True)
        adapter = PreparedSmtpAdapter(
            self.configuration(port=server.server_address[1]),
            _backend_factory=self.trusted_backend,
        )
        with self.assertRaisesRegex(PreparedMailError, "^MAIL_UNAVAILABLE$"):
            self.send(adapter)
        self.assertEqual(server.messages, [])
        self.assertEqual(server.connections, 1)

    def test_expired_or_malformed_mail_never_connects(self):
        factory = Mock()
        adapter = PreparedSmtpAdapter(self.configuration(), _backend_factory=factory)
        for changes in (
            {"expires_at": datetime.now(timezone.utc) - timedelta(seconds=1)},
            {"expires_at": datetime.now()},
            {"recipient": "bad\r\nBcc: other@example.invalid"},
            {"subject": "bad\nsubject"},
            {"body": "x" * 8193},
        ):
            with (
                self.subTest(fields=list(changes)),
                self.assertRaises(PreparedMailError),
            ):
                self.send(adapter, **changes)
        factory.assert_not_called()

    def test_provider_exception_and_zero_acceptance_are_redacted_without_retry(self):
        for failure in (RuntimeError("synthetic payload/password"), None):
            connection = Mock()
            connection.__enter__ = Mock(return_value=connection)
            connection.__exit__ = Mock(return_value=False)
            connection.send_messages.side_effect = failure
            connection.send_messages.return_value = 0
            factory = Mock(return_value=connection)
            adapter = PreparedSmtpAdapter(
                self.configuration(), _backend_factory=factory
            )
            with self.assertRaisesRegex(PreparedMailError, "^MAIL_UNAVAILABLE$"):
                self.send(adapter)
            self.assertEqual(factory.call_count, 1)
            self.assertEqual(connection.send_messages.call_count, 1)

    def test_environment_requires_complete_tls_config_and_redacts_secrets(self):
        env = {
            "PWC_MAIL_HOST": "smtp.example.invalid",
            "PWC_MAIL_PORT": "587",
            "PWC_MAIL_TLS_MODE": "starttls",
            "PWC_MAIL_USERNAME": "smtp-user",
            "PWC_MAIL_PASSWORD": "synthetic-mail-password",
            "PWC_MAIL_FROM": "sender@example.invalid",
        }
        config = MailConfiguration.from_environment(env)
        self.assertNotIn("smtp-user", repr(config))
        self.assertNotIn("synthetic-mail-password", repr(config))
        for name in env:
            with self.subTest(missing=name), self.assertRaises(PreparedMailError):
                MailConfiguration.from_environment(
                    {k: v for k, v in env.items() if k != name}
                )
        for changes in (
            {"mode": "plain"},
            {"port": 0},
            {"host": "user@host"},
            {"sender": "bad"},
        ):
            with self.subTest(changes=changes), self.assertRaises(PreparedMailError):
                self.configuration(**changes)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend")
    def test_existing_dispatcher_still_cannot_select_real_mail_backend(self):
        with patch.dict(
            "os.environ", {"PWC_MAIL_TLS_MODE": "tls", "PWC_AUTH_DELIVERY_MODE": "smtp"}
        ):
            deliver_message(
                "fixture@example.invalid", "Synthetic only", "No live delivery"
            )
        self.assertEqual(mail.outbox[-1].to, ["fixture@example.invalid"])
