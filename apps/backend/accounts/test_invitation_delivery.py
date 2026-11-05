"""Outbox lease, retry, erasure, stale acknowledgement and SMTP integration."""

from datetime import timedelta
from unittest.mock import Mock, patch

from django.core import mail
from django.test import TestCase, override_settings

from . import personal_invitations as invitations
from .invitation_delivery import dispatch_one
from .flow_security import FlowProblem
from .test_personal_invitations import CONFIG, Fixtures
from .test_prepared_mail import PreparedMailFixtures
from .prepared_mail import PreparedSmtpAdapter


@override_settings(**CONFIG)
class InvitationDeliveryTests(Fixtures, TestCase):
    def test_synthetic_dispatch_sends_once_and_erases_payload(self):
        invitation, token = self.issued()
        self.assertTrue(dispatch_one())
        self.assertIn("#invitation_id=", mail.outbox[-1].body)
        self.assertIn(token, mail.outbox[-1].body)
        self.assertEqual(mail.outbox[-1].to, [invitation.recipient])
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_state, "sent")
        self.assertIsNone(invitation.mail_payload)
        self.assertFalse(dispatch_one())

    def test_five_bounded_retries_then_terminal_secret_erasure(self):
        invitation, _ = self.issued()
        adapter = Mock()
        adapter.send.side_effect = RuntimeError(
            "private provider payload must not escape"
        )
        for attempt in range(1, 6):
            self.assertTrue(dispatch_one(adapter=adapter))
            invitation.refresh_from_db()
            self.assertEqual(invitation.mail_attempts, attempt)
            self.now += timedelta(minutes=20)
        self.assertEqual(invitation.mail_state, "failed")
        self.assertIsNone(invitation.mail_payload)
        self.assertFalse(dispatch_one(adapter=adapter))
        self.assertEqual(adapter.send.call_count, 5)

    def test_expired_proof_and_revoked_source_are_not_sent(self):
        invitation, token = self.issued()
        self.proof(invitation, token)
        self.now = invitation.proof_expires_at
        adapter = Mock()
        dispatch_one(adapter=adapter)
        adapter.send.assert_not_called()
        invitation.refresh_from_db()
        self.assertIsNone(invitation.mail_payload)

    def test_source_revocation_prevents_send(self):
        invitation, _ = self.issued()
        self.authority.return_value = False
        adapter = Mock()
        dispatch_one(adapter=adapter)
        adapter.send.assert_not_called()
        invitation.refresh_from_db()
        self.assertIsNone(invitation.mail_payload)

    def test_corrupted_encrypted_payload_is_bounded_and_not_logged_or_raised(self):
        invitation, _ = self.issued()
        invitation.mail_payload = b"not-ciphertext"
        invitation.save()
        self.assertTrue(dispatch_one())
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_state, "pending")
        self.assertEqual(invitation.mail_attempts, 1)

    def test_new_generation_is_not_erased_by_stale_send_acknowledgement(self):
        invitation, token = self.issued()
        adapter = Mock()
        adapter.send.side_effect = lambda *args, **kwargs: self.proof(invitation, token)
        dispatch_one(adapter=adapter)
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_state, "pending")
        self.assertEqual(invitation.mail_generation, 2)
        self.assertIsNotNone(invitation.mail_payload)
        self.assertTrue(dispatch_one())
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_state, "sent")

    def test_cancel_during_inflight_send_cannot_resurrect_outbox(self):
        invitation, _ = self.issued()
        adapter = Mock()
        adapter.send.side_effect = lambda *args, **kwargs: invitations.cancel(
            self.issuer.pk, invitation.pk
        )
        dispatch_one(adapter=adapter)
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_state, "cancelled")
        self.assertIsNone(invitation.mail_payload)

    def test_expired_lease_can_be_recovered_without_unbounded_attempts(self):
        invitation, _ = self.issued()
        invitation.mail_state = "leased"
        invitation.mail_attempts = 1
        invitation.mail_lease_at = self.now - timedelta(seconds=1)
        invitation.save()
        self.assertTrue(dispatch_one())
        invitation.refresh_from_db()
        self.assertEqual(invitation.mail_attempts, 2)
        self.assertEqual(invitation.mail_state, "sent")

    def test_live_guard_precedes_config_database_and_adapter(self):
        adapter = Mock()
        for profile in ("development", "staging", "production"):
            with (
                override_settings(PWC_ENVIRONMENT=profile),
                self.assertNumQueries(0),
                self.assertRaises(FlowProblem),
            ):
                dispatch_one(adapter=adapter)
        adapter.send.assert_not_called()

    def test_expiry_cleanup_erases_pending_proof_without_creating_account(self):
        invitation, token = self.issued()
        self.proof(invitation, token)
        self.now = invitation.expires_at
        self.assertTrue(invitations.expire_one())
        invitation.refresh_from_db()
        self.assertIsNone(invitation.mail_payload)
        self.assertEqual(invitation.proof_digest, "")
        self.assertIsNotNone(invitation.cancelled_at)


@override_settings(**CONFIG)
class InvitationTlsTests(Fixtures, PreparedMailFixtures, TestCase):
    """Reuse the existing disposable TLS server, never an external provider."""

    def test_invitation_worker_through_prepared_smtp_actual_verified_tls(self):
        for mode in ("tls", "starttls"):
            with self.subTest(mode=mode):
                invitation, _ = self.issued()
                server = self.smtp(mode)
                adapter = PreparedSmtpAdapter(
                    self.configuration(port=server.server_address[1], mode=mode),
                    _backend_factory=self.trusted_backend,
                )
                self.assertTrue(dispatch_one(adapter=adapter))
                self.assertEqual(len(server.messages), 1)
                self.assertTrue(server.authenticated)
                invitation.refresh_from_db()
                self.assertEqual(invitation.mail_state, "sent")
                invitations.cancel(self.issuer.pk, invitation.pk)
                self.now += timedelta(hours=1)
