"""Invitation-only policy closes live registration without inventing an issuer."""

from io import StringIO
from unittest.mock import patch
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from .enrollment_readiness import readiness
from .flow_security import FlowProblem
from .models import User, AuthChallenge, DeliveryIntent
from .registration import request_flow, resend_flow, confirm_flow
from .test_mfa import MFA_CONFIG
from .test_sessions import SessionFixtures
from .test_registration import PASSWORD


@override_settings(**MFA_CONFIG)
class InvitationPolicyTests(SessionFixtures, TestCase):
    def test_all_non_test_profiles_deny_request_resend_and_confirmation_before_io(self):
        for profile in ("development", "staging", "production"):
            with (
                self.subTest(profile=profile),
                override_settings(PWC_ENVIRONMENT=profile),
            ):
                with patch("accounts.registration.configured") as configured:
                    for operation in (
                        lambda: request_flow(
                            "registration", "fixture@example.invalid", "127.0.0.1"
                        ),
                        lambda: resend_flow(
                            "registration", "id", "control", "127.0.0.1"
                        ),
                        lambda: confirm_flow(
                            "registration", "id", "proof", PASSWORD, "127.0.0.1"
                        ),
                    ):
                        with (
                            self.assertNumQueries(0),
                            self.assertRaises(FlowProblem) as error,
                        ):
                            operation()
                        self.assertEqual(error.exception.code, "AUTH_UNAVAILABLE")
                        self.assertEqual(error.exception.status, 503)
                    configured.assert_not_called()
        self.assertFalse(User.objects.exists())
        self.assertFalse(AuthChallenge.objects.exists())
        self.assertFalse(DeliveryIntent.objects.exists())

    def test_https_request_fails_closed_without_disclosing_target_or_making_flow(self):
        with override_settings(PWC_ENVIRONMENT="staging"):
            response = self.post_api(
                "registration/request", {"email": "fixture@example.invalid"}
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "AUTH_UNAVAILABLE")
        self.assertNotIn("fixture@example.invalid", str(response.content))
        self.assertFalse(User.objects.exists() or AuthChallenge.objects.exists())

    def test_test_profile_regression_is_not_a_live_invitation_or_bootstrap(self):
        flow = request_flow("registration", "fixture@example.invalid", "127.0.0.1")
        proof = self.mail_proof(flow)
        with override_settings(PWC_ENVIRONMENT="development"):
            with self.assertRaises(FlowProblem):
                confirm_flow(
                    "registration", flow["flow_id"], proof, PASSWORD, "127.0.0.1"
                )
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        self.assertIsNone(challenge.consumed_at)
        self.assertFalse(User.objects.exists())
        confirmed = confirm_flow(
            "registration", flow["flow_id"], proof, PASSWORD, "127.0.0.1"
        )
        self.assertEqual(confirmed, {"status": "verified"})
        self.assertFalse(User.objects.get().is_staff)
        self.assertFalse(User.objects.get().is_superuser)

    def test_no_invitation_endpoint_or_environment_acceptance_shortcut(self):
        for path in ("/api/v1/auth/invitations/", "/api/v1/auth/invitations/accept/"):
            self.assertEqual(self.client.post(path, {}).status_code, 404)
        with override_settings(PWC_PERSONAL_INVITATION_ISSUER_ACCEPTED=True):
            report = readiness()
        self.assertEqual(report["policy"], "invitation_only")
        self.assertFalse(report["ready_for_real_enrollment"])
        self.assertEqual(
            report["invitation_issue_and_accept"], "implemented_test_profile_only_live_source_unavailable"
        )

    def test_read_only_preflight_returns_failure_and_exact_dependencies(self):
        output = StringIO()
        with self.assertNumQueries(0), self.assertRaises(CommandError):
            call_command("check_personal_enrollment_readiness", stdout=output)
        value = output.getvalue()
        for dependency in (
            "PE-ISSUER",
            "PE-CONTRACT",
            "O1-O2",
            "O4",
            "O3-W2",
            "IDENTITY",
        ):
            self.assertIn(dependency, value)
        self.assertNotIn(PASSWORD, value)
        self.assertFalse(User.objects.exists() or DeliveryIntent.objects.exists())
