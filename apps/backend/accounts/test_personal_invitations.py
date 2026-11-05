"""Actual PostgreSQL tests of the bounded issuance/email-proof implementation."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

from django.db import IntegrityError, close_old_connections, connection, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from . import personal_invitations as invitations
from .flow_security import FlowProblem, unseal
from .models import PersonalInvitation, SecurityEvent, User, UserContact
from .test_registration import TEST_CONFIG

CONFIG = dict(TEST_CONFIG, PWC_ENVIRONMENT="test")
SOURCE = "a" * 64
EMAIL = "recipient@example.invalid"


class Fixtures:
    def setUp(self):
        self.now = timezone.now()
        self.clock = patch(
            "accounts.personal_invitations.timezone.now", side_effect=lambda: self.now
        )
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.issuer = User.objects.create_user(
            username="officer", is_staff=True, is_superuser=True
        )
        self.source = patch(
            "accounts.personal_invitations.authorize_source", return_value=True
        )
        self.authority = self.source.start()
        self.addCleanup(self.source.stop)

    def issued(self):
        result = invitations.issue(self.issuer.pk, EMAIL, SOURCE, "192.0.2.1")
        self.assertIsInstance(result, dict)
        invitation = PersonalInvitation.objects.get(pk=result["invitation_id"])
        token = unseal(invitation.mail_key, invitation.mail_payload)["secret"]
        return invitation, token

    def proof(self, invitation, token):
        self.now += timedelta(seconds=61)
        result = invitations.request_confirmation(
            invitation.pk, token, EMAIL, "192.0.2.2"
        )
        self.assertEqual(result, {"status": "accepted"})
        invitation.refresh_from_db()
        return unseal(invitation.mail_key, invitation.mail_payload)["secret"]

    def confirm(self, invitation, token, proof, email=EMAIL):
        return invitations.confirm_email(
            invitation.pk, token, email, proof, "192.0.2.3"
        )


@override_settings(**CONFIG)
class PersonalInvitationTests(Fixtures, TestCase):
    def test_real_postgresql_and_exact_24_hour_constraint(self):
        self.assertEqual(connection.vendor, "postgresql")
        invitation, _ = self.issued()
        self.assertEqual(
            invitation.expires_at - invitation.created_at, timedelta(hours=24)
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            PersonalInvitation.objects.filter(pk=invitation.pk).update(
                expires_at=timezone.now()
            )

    def test_unknown_actual_source_denies_staff_and_configuration_shortcuts(self):
        self.source.stop()
        with override_settings(PWC_PERSONAL_INVITATION_ISSUER_ACCEPTED=True):
            result = invitations.issue(self.issuer.pk, EMAIL, SOURCE, "192.0.2.1")
        self.assertEqual(result.code, "AUTH_UNAVAILABLE")
        self.assertFalse(PersonalInvitation.objects.exists())

    def test_non_test_profiles_stop_every_operation_before_queries_or_source(self):
        for profile in ("development", "staging", "production"):
            with override_settings(PWC_ENVIRONMENT=profile):
                for operation in (
                    lambda: invitations.issue(
                        self.issuer.pk, EMAIL, SOURCE, "192.0.2.1"
                    ),
                    lambda: invitations.request_confirmation(
                        "bad", "bad", EMAIL, "192.0.2.1"
                    ),
                    lambda: invitations.confirm_email(
                        "bad", "bad", EMAIL, "bad", "192.0.2.1"
                    ),
                    lambda: invitations.cancel(self.issuer.pk, "bad"),
                ):
                    with (
                        self.assertNumQueries(0),
                        self.assertRaises(FlowProblem) as error,
                    ):
                        operation()
                    self.assertEqual(error.exception.code, "AUTH_UNAVAILABLE")
        self.authority.assert_not_called()

    def test_only_digests_and_encrypted_message_no_returned_secrets(self):
        invitation, token = self.issued()
        self.assertNotEqual(invitation.token_digest, token)
        self.assertNotIn(token.encode(), bytes(invitation.mail_payload))
        self.assertNotIn(token, str(list(SecurityEvent.objects.values())))
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(UserContact.objects.exists())

    def test_confirmation_is_recipient_bound_purpose_separated_and_single_use(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        self.assertEqual(
            self.confirm(invitation, token, token).code, "CHALLENGE_INVALID"
        )
        self.assertEqual(
            self.confirm(invitation, token, proof, "other@example.invalid").code,
            "CHALLENGE_INVALID",
        )
        self.assertEqual(
            self.confirm(invitation, token, proof), {"status": "email_verified"}
        )
        self.assertEqual(
            self.confirm(invitation, token, proof).code, "CHALLENGE_INVALID"
        )
        invitation.refresh_from_db()
        self.assertIsNone(invitation.mail_payload)
        self.assertEqual(invitation.proof_digest, "")
        self.assertEqual(User.objects.count(), 1)  # not a password/MFA/account writer

    def test_expiry_boundary_includes_email_confirmation(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        with patch(
            "accounts.personal_invitations.timezone.now",
            return_value=invitation.expires_at,
        ):
            self.assertEqual(
                self.confirm(invitation, token, proof).code, "CHALLENGE_INVALID"
            )
        invitation.refresh_from_db()
        self.assertIsNone(invitation.email_verified_at)

    def test_proof_expires_in_30_minutes_even_with_valid_invitation(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        with patch(
            "accounts.personal_invitations.timezone.now",
            return_value=invitation.proof_expires_at,
        ):
            self.assertEqual(
                self.confirm(invitation, token, proof).code, "CHALLENGE_INVALID"
            )

    def test_revoked_source_or_disabled_officer_cannot_confirm(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        self.authority.return_value = False
        self.assertEqual(
            self.confirm(invitation, token, proof).code, "CHALLENGE_INVALID"
        )
        self.authority.return_value = True
        self.issuer.is_active = False
        self.issuer.save()
        self.assertEqual(
            self.confirm(invitation, token, proof).code, "CHALLENGE_INVALID"
        )

    def test_other_actor_cannot_cancel_but_authorized_issuer_can(self):
        invitation, token = self.issued()
        other = User.objects.create_user(username="other", is_superuser=True)
        self.assertEqual(
            invitations.cancel(other.pk, invitation.pk).code, "AUTH_UNAVAILABLE"
        )
        self.assertEqual(
            invitations.cancel(self.issuer.pk, invitation.pk), {"status": "cancelled"}
        )
        self.now += timedelta(seconds=61)
        self.assertEqual(
            invitations.request_confirmation(
                invitation.pk, token, EMAIL, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        invitation.refresh_from_db()
        self.assertIsNone(invitation.mail_payload)

    def test_duplicate_pending_and_existing_account_are_refused_without_linkage(self):
        self.issued()
        later = timezone.now() + timedelta(seconds=61)
        with patch("accounts.personal_invitations.timezone.now", return_value=later):
            self.assertEqual(
                invitations.issue(
                    self.issuer.pk, EMAIL.upper(), SOURCE, "192.0.2.4"
                ).code,
                "STATE_CONFLICT",
            )
        User.objects.create_user(username="existing", email="existing@example.invalid")
        self.assertEqual(
            invitations.issue(
                self.issuer.pk, "existing@example.invalid", SOURCE, "192.0.2.5"
            ).code,
            "STATE_CONFLICT",
        )
        self.assertEqual(PersonalInvitation.objects.count(), 1)

    def test_bad_proofs_are_bounded_and_erase_pending_secrets(self):
        invitation, token = self.issued()
        self.proof(invitation, token)
        for _ in range(5):
            self.assertEqual(
                self.confirm(invitation, token, "x" * 43).code, "CHALLENGE_INVALID"
            )
        invitation.refresh_from_db()
        self.assertEqual(invitation.failures, 5)
        self.assertIsNotNone(invitation.cancelled_at)
        self.assertIsNone(invitation.mail_payload)

    def test_email_proof_transaction_rolls_back_if_audit_fails(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        with patch(
            "accounts.personal_invitations.audit", side_effect=RuntimeError("synthetic")
        ):
            with self.assertRaises(RuntimeError):
                self.confirm(invitation, token, proof)
        invitation.refresh_from_db()
        self.assertIsNone(invitation.email_verified_at)
        self.assertTrue(invitation.proof_digest)


@override_settings(**CONFIG)
class PersonalInvitationRaceTests(Fixtures, TransactionTestCase):
    def test_concurrent_confirmation_has_exactly_one_commit(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        barrier = Barrier(2)

        def attempt():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = self.confirm(invitation, token, proof)
                return result if isinstance(result, dict) else result.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: attempt(), range(2)))
        self.assertEqual(results.count({"status": "email_verified"}), 1)
        self.assertEqual(results.count("CHALLENGE_INVALID"), 1)
        self.assertEqual(
            SecurityEvent.objects.filter(
                event="auth.invitation_email_verified"
            ).count(),
            1,
        )


@override_settings(**CONFIG)
class AdditionalInvitationTests(Fixtures, TestCase):
    def test_invalid_email_fails_before_authority_and_database_io(self):
        with self.assertNumQueries(0):
            result = invitations.issue(
                self.issuer.pk, "not-an-email", SOURCE, "192.0.2.1"
            )
        self.assertEqual(result.code, "VALIDATION_ERROR")
        self.authority.assert_not_called()

    def test_new_proof_invalidates_old_proof_without_resetting_failures(self):
        invitation, token = self.issued()
        old = self.proof(invitation, token)
        new = self.proof(invitation, token)
        self.assertNotEqual(old, new)
        self.assertEqual(self.confirm(invitation, token, old).code, "CHALLENGE_INVALID")
        self.assertEqual(
            self.confirm(invitation, token, new), {"status": "email_verified"}
        )
        invitation.refresh_from_db()
        self.assertEqual(invitation.failures, 1)

    def test_expired_reissue_erases_old_mail_and_changes_token(self):
        invitation, token = self.issued()
        self.now = invitation.expires_at
        replacement, new_token = self.issued()
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.cancelled_at)
        self.assertIsNone(invitation.mail_payload)
        self.assertNotEqual(invitation.pk, replacement.pk)
        self.assertNotEqual(token, new_token)

    def test_issue_and_audit_are_one_transaction(self):
        with patch(
            "accounts.personal_invitations.audit", side_effect=RuntimeError("synthetic")
        ):
            with self.assertRaises(RuntimeError):
                invitations.issue(self.issuer.pk, EMAIL, SOURCE, "192.0.2.1")
        self.assertFalse(PersonalInvitation.objects.exists())
