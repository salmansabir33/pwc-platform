"""Invitation-to-account acceptance and real PostgreSQL race/rollback coverage."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pyotp
from django.contrib.auth.hashers import check_password
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, override_settings, Client

from . import personal_invitations as invitations
from .backends import password_candidate
from .flow_security import FlowProblem, unseal
from .models import (
    User,
    UserContact,
    AuthSession,
    MfaFactor,
    MfaRecoveryCode,
    PersonalInvitation,
)
from .test_personal_invitations import Fixtures, EMAIL
from .test_mfa import MFA_CONFIG
from .test_registration import PASSWORD
from .test_sessions import NGO, SessionFixtures

CONFIG = dict(MFA_CONFIG, PWC_ENVIRONMENT="test")


class CompletionFixtures(Fixtures):
    def staged(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        confirmed = self.confirm(invitation, token, proof)
        control = confirmed["enrollment_control"]
        staged = invitations.set_password(
            invitation.pk, token, EMAIL, control, PASSWORD, "192.0.2.4"
        )
        self.assertIsInstance(staged, dict)
        return invitation, token, control, staged

    def activate(self, invitation, token, control, staged, code=None):
        return invitations.activate(
            invitation.pk,
            token,
            EMAIL,
            control,
            code if code is not None else pyotp.TOTP(staged["secret"]).at(self.now),
            "192.0.2.5",
        )

    def assert_no_account(self):
        self.assertEqual(User.objects.count(), 1)
        for model in (UserContact, AuthSession, MfaFactor, MfaRecoveryCode):
            self.assertFalse(model.objects.exists())


@override_settings(**CONFIG)
class InvitationCompletionTests(CompletionFixtures, TestCase):
    def test_entire_ceremony_commits_only_at_mfa_and_never_auto_logs_in(self):
        invitation, token, control, staged = self.staged()
        self.assert_no_account()
        invitation.refresh_from_db()
        self.assertIsNone(invitation.consumed_at)
        self.assertNotIn(PASSWORD.encode(), bytes(invitation.ceremony_payload))
        self.assertNotIn(staged["secret"].encode(), bytes(invitation.ceremony_payload))
        self.assertIsNone(password_candidate(EMAIL, PASSWORD))
        result = self.activate(invitation, token, control, staged)
        self.assertEqual(result["status"], "complete")
        invitation.refresh_from_db()
        user = invitation.user
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertFalse(user.groups.exists() or user.user_permissions.exists())
        self.assertTrue(check_password(PASSWORD, user.password))
        self.assertEqual(UserContact.objects.get(user=user).normalized_value, EMAIL)
        self.assertEqual(MfaFactor.objects.get(user=user).state, "active")
        self.assertEqual(
            MfaRecoveryCode.objects.filter(user=user).count(),
            len(result["recovery_codes"]),
        )
        self.assertTrue(
            all(session.revoked_at for session in AuthSession.objects.filter(user=user))
        )
        self.assertIsNone(invitation.ceremony_payload)
        self.assertIsNone(invitation.mail_payload)
        self.assertEqual(invitation.control_digest, "")
        self.assertLess(invitation.consumed_at, invitation.expires_at)
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        self.assertEqual(
            invitations.cancel(self.issuer.pk, invitation.pk).code, "STATE_CONFLICT"
        )

    def test_missing_continuation_capability_cannot_set_password_or_activate(self):
        invitation, token, control, staged = self.staged()
        self.assertEqual(
            invitations.set_password(
                invitation.pk, token, EMAIL, "x" * 43, PASSWORD, "192.0.2.4"
            ).code,
            "CHALLENGE_INVALID",
        )
        self.assertEqual(
            self.activate(invitation, token, "x" * 43, staged).code, "CHALLENGE_INVALID"
        )
        self.assert_no_account()

    def test_bad_totp_rolls_back_every_new_auth_row_but_commits_failure_budget(self):
        invitation, token, control, staged = self.staged()
        for _ in range(5):
            self.assertEqual(
                self.activate(invitation, token, control, staged, code="not-code").code,
                "CHALLENGE_INVALID",
            )
            self.assert_no_account()
        invitation.refresh_from_db()
        self.assertEqual(invitation.failures, 5)
        self.assertIsNotNone(invitation.cancelled_at)
        self.assertIsNone(invitation.ceremony_payload)

    def test_all_steps_must_complete_before_24_hours_not_only_password(self):
        invitation, token = self.issued()
        self.now = invitation.expires_at - timedelta(seconds=120)
        proof = self.proof(invitation, token)
        control = self.confirm(invitation, token, proof)["enrollment_control"]
        staged = invitations.set_password(
            invitation.pk, token, EMAIL, control, PASSWORD, "192.0.2.4"
        )
        self.now = invitation.expires_at
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        self.assertTrue(invitations.expire_one())
        invitation.refresh_from_db()
        self.assertIsNone(invitation.ceremony_payload)
        self.assert_no_account()

    def test_setup_expires_after_five_minutes_and_can_be_replaced_before_deadline(self):
        invitation, token, control, staged = self.staged()
        self.now += timedelta(minutes=5)
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        replacement = invitations.set_password(
            invitation.pk, token, EMAIL, control, PASSWORD, "192.0.2.4"
        )
        self.assertNotEqual(staged["secret"], replacement["secret"])
        self.assertEqual(
            self.activate(invitation, token, control, replacement)["status"], "complete"
        )

    def test_cancellation_and_source_revocation_block_staged_credentials(self):
        invitation, token, control, staged = self.staged()
        self.authority.return_value = False
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        self.authority.return_value = True
        invitations.cancel(self.issuer.pk, invitation.pk)
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        self.assert_no_account()

    def test_existing_contact_race_never_links_or_changes_an_existing_person(self):
        invitation, token, control, staged = self.staged()
        other = User.objects.create_user(
            username="other", email=EMAIL, password="not the invited password"
        )
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        other.refresh_from_db()
        self.assertFalse(check_password(PASSWORD, other.password))
        self.assertFalse(MfaFactor.objects.exists())
        invitation.refresh_from_db()
        self.assertIsNone(invitation.user_id)

    def test_audit_failure_rolls_back_account_factor_codes_and_consumption(self):
        invitation, token, control, staged = self.staged()
        real = invitations.audit

        def fail_completion(invitation, action, **kwargs):
            if action == "completed":
                raise RuntimeError("synthetic audit failure")
            return real(invitation, action, **kwargs)

        with patch("accounts.personal_invitations.audit", side_effect=fail_completion):
            with self.assertRaises(RuntimeError):
                self.activate(invitation, token, control, staged)
        self.assert_no_account()
        invitation.refresh_from_db()
        self.assertIsNone(invitation.consumed_at)
        self.assertEqual(
            self.activate(invitation, token, control, staged)["status"], "complete"
        )

    def test_deadline_or_revocation_during_activation_rolls_back(self):
        invitation, token, control, staged = self.staged()
        from . import mfa

        real = mfa.enrollment_confirm

        def delayed(*args):
            result = real(*args)
            self.now = invitation.expires_at
            return result

        with patch("accounts.mfa.enrollment_confirm", side_effect=delayed):
            self.assertEqual(
                self.activate(invitation, token, control, staged).code,
                "CHALLENGE_INVALID",
            )
        self.assert_no_account()

    def test_new_email_confirmation_invalidates_old_control_and_resumes_with_password(
        self,
    ):
        invitation, token, control, staged = self.staged()
        proof = self.proof(invitation, token)
        renewed = self.confirm(invitation, token, proof)
        self.assertNotEqual(control, renewed["enrollment_control"])
        self.assertEqual(
            self.activate(invitation, token, control, staged).code, "CHALLENGE_INVALID"
        )
        invitation.refresh_from_db()
        self.assertIsNotNone(invitation.ceremony_payload)
        resumed = invitations.set_password(
            invitation.pk,
            token,
            EMAIL,
            renewed["enrollment_control"],
            PASSWORD,
            "192.0.2.4",
        )
        self.assertEqual(resumed["secret"], staged["secret"])
        self.assertEqual(
            self.activate(invitation, token, renewed["enrollment_control"], resumed)[
                "status"
            ],
            "complete",
        )

    def test_password_hashing_crossing_deadline_cannot_stage_credentials(self):
        invitation, token = self.issued()
        proof = self.proof(invitation, token)
        control = self.confirm(invitation, token, proof)["enrollment_control"]
        original = User.set_password

        def delayed(user, password):
            original(user, password)
            self.now = invitation.expires_at

        with patch.object(User, "set_password", delayed):
            result = invitations.set_password(
                invitation.pk, token, EMAIL, control, PASSWORD, "192.0.2.4"
            )
        self.assertEqual(result.code, "CHALLENGE_INVALID")
        invitation.refresh_from_db()
        self.assertIsNone(invitation.ceremony_payload)
        self.assert_no_account()

    def test_source_revocation_at_final_audit_fence_rolls_back_every_auth_row(self):
        invitation, token, control, staged = self.staged()
        original = invitations.audit

        def revoke(row, action, **kwargs):
            original(row, action, **kwargs)
            if action == "completed":
                self.authority.return_value = False

        with patch("accounts.personal_invitations.audit", side_effect=revoke):
            self.assertEqual(
                self.activate(invitation, token, control, staged).code,
                "CHALLENGE_INVALID",
            )
        self.assert_no_account()
        invitation.refresh_from_db()
        self.assertIsNone(invitation.consumed_at)

    def test_worker_erases_abandoned_setup_without_deleting_or_creating_people(self):
        invitation, token, control, staged = self.staged()
        self.now += timedelta(minutes=5)
        self.assertTrue(invitations.expire_one())
        invitation.refresh_from_db()
        self.assertIsNone(invitation.ceremony_payload)
        self.assertIsNone(invitation.cancelled_at)
        self.assert_no_account()
        replacement = invitations.set_password(
            invitation.pk, token, EMAIL, control, PASSWORD, "192.0.2.4"
        )
        self.assertNotEqual(replacement["secret"], staged["secret"])

    def test_non_test_password_activation_and_cleanup_guard_before_io(self):
        for profile in ("development", "staging", "production"):
            with override_settings(PWC_ENVIRONMENT=profile):
                for function in (
                    lambda: invitations.set_password(
                        "bad", "bad", EMAIL, "bad", PASSWORD, "192.0.2.1"
                    ),
                    lambda: invitations.activate(
                        "bad", "bad", EMAIL, "bad", "bad", "192.0.2.1"
                    ),
                    invitations.expire_one,
                ):
                    with self.assertNumQueries(0), self.assertRaises(FlowProblem):
                        function()


@override_settings(**CONFIG)
class CompletionRaceTests(CompletionFixtures, TransactionTestCase):
    def test_concurrent_activation_creates_exactly_one_account_and_factor(self):
        invitation, token, control, staged = self.staged()
        barrier = Barrier(2)

        def attempt(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = self.activate(invitation, token, control, staged)
                return result["status"] if isinstance(result, dict) else result.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(attempt, range(2)))
        self.assertCountEqual(results, ["complete", "CHALLENGE_INVALID"])
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(MfaFactor.objects.filter(state="active").count(), 1)

    def test_concurrent_cancellation_and_activation_have_one_linearized_outcome(self):
        invitation, token, control, staged = self.staged()
        barrier = Barrier(2)

        def attempt(cancel):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = (
                    invitations.cancel(self.issuer.pk, invitation.pk)
                    if cancel
                    else self.activate(invitation, token, control, staged)
                )
                return result["status"] if isinstance(result, dict) else result.code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            cancelled, completed = list(pool.map(attempt, (True, False)))
        invitation.refresh_from_db()
        if completed == "complete":
            self.assertEqual(cancelled, "STATE_CONFLICT")
            self.assertIsNone(invitation.cancelled_at)
            self.assertIsNotNone(invitation.consumed_at)
            self.assertEqual(User.objects.count(), 2)
        else:
            self.assertEqual(cancelled, "cancelled")
            self.assertEqual(completed, "CHALLENGE_INVALID")
            self.assertIsNone(invitation.consumed_at)
            self.assert_no_account()


@override_settings(**CONFIG)
class BrowserInvitationTests(CompletionFixtures, SessionFixtures, TestCase):
    def test_real_csrf_browser_journey_then_explicit_login_requires_mfa(self):
        invitation, token = self.issued()
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        base = {"invitation_id": str(invitation.pk), "token": token, "recipient": EMAIL}

        def post(operation, extra=None, **headers):
            return self.post_api(
                "web/invitations/" + operation,
                dict(base, **(extra or {})),
                client=client,
                host=NGO,
                HTTP_ORIGIN="https://" + NGO,
                HTTP_X_CSRFTOKEN=csrf,
                **headers,
            )

        self.now += timedelta(seconds=61)
        self.assertEqual(post("request-proof").status_code, 202)
        invitation.refresh_from_db()
        proof = unseal(invitation.mail_key, invitation.mail_payload)["secret"]
        response = post("confirm-email", {"proof": proof})
        self.assertEqual(response.status_code, 200, response.content)
        control = response.json()["enrollment_control"]
        response = post(
            "password", {"enrollment_control": control, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200, response.content)
        code = pyotp.TOTP(response.json()["secret"]).at(self.now)
        response = post("activate", {"enrollment_control": control, "code": code})
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn("sessionid", response.cookies)
        response = self.post_api(
            "web/login",
            {"email": EMAIL, "password": PASSWORD},
            client=client,
            host=NGO,
            HTTP_ORIGIN="https://" + NGO,
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 202, response.content)
        self.assertEqual(response.json()["status"], "mfa_required")

    def test_transport_csrf_unknown_id_and_live_gates(self):
        client = Client(enforce_csrf_checks=True)
        path = "/api/v1/auth/web/invitations/activate/"
        self.assertEqual(
            client.post(path, {}, secure=True, HTTP_HOST=NGO).status_code, 403
        )
        self.assertEqual(client.post(path, {}, HTTP_HOST=NGO).status_code, 400)
        self.assertEqual(
            client.post(
                path, {}, secure=True, HTTP_HOST=NGO, HTTP_AUTHORIZATION="Bearer bad"
            ).status_code,
            400,
        )
        with override_settings(PWC_ENVIRONMENT="staging"):
            with self.assertNumQueries(0):
                self.assertEqual(
                    client.post(path, {}, secure=True, HTTP_HOST=NGO).status_code, 503
                )
