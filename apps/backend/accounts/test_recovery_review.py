"""Regression tests for the independent-minded 03A.2 recovery review."""

from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.db.models.query import QuerySet
from django.test import TestCase, override_settings
from django.utils import timezone

from .flow_cleanup import cleanup_flows
from .models import AuthAbuseBucket, AuthChallenge, DeliveryIntent, User
from .registration import confirm_flow, request_flow, resend_flow, spend
from .test_registration import FlowFixtures, TEST_CONFIG, PASSWORD, NEW_PASSWORD


@override_settings(**TEST_CONFIG)
class RecoveryReviewTests(FlowFixtures, TestCase):
    def test_cleanup_between_selector_and_lock_is_generic_not_server_error(self):
        for operation in ("confirm", "resend", "inert_reset_confirm"):
            with self.subTest(operation=operation):
                purpose = (
                    "reset" if operation == "inert_reset_confirm" else "registration"
                )
                flow = self.new_flow(purpose, f"{operation}@example.invalid")
                proof = self.proof(flow)
                AuthChallenge.objects.filter(pk=flow["flow_id"]).update(
                    last_issued_at=timezone.now() - timedelta(seconds=61)
                )
                AuthAbuseBucket.objects.filter(dimension="target").delete()
                original = AuthChallenge.objects.select_for_update

                def cleanup_before_lock(*args, **kwargs):
                    DeliveryIntent.objects.filter(challenge_id=flow["flow_id"]).delete()
                    AuthChallenge.objects.filter(pk=flow["flow_id"]).delete()
                    return original(*args, **kwargs)

                with patch.object(
                    AuthChallenge.objects,
                    "select_for_update",
                    side_effect=cleanup_before_lock,
                ):
                    if operation == "resend":
                        result = resend_flow(
                            purpose, flow["flow_id"], flow["flow_control"], "192.0.2.2"
                        )
                        self.assertEqual(result, {"status": "accepted"})
                    else:
                        result = confirm_flow(
                            purpose, flow["flow_id"], proof, PASSWORD, "192.0.2.2"
                        )
                        self.assertEqual(result.code, "CHALLENGE_INVALID")
        self.assertFalse(User.objects.exists())

    def test_reset_request_handles_contact_removed_after_lookup(self):
        user, contact = self.account()
        original = User.objects.select_for_update

        def remove_contact(*args, **kwargs):
            contact.delete()
            return original(*args, **kwargs)

        with patch.object(
            User.objects, "select_for_update", side_effect=remove_contact
        ):
            flow = self.new_flow("reset", user.email)
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        self.assertFalse(challenge.eligible)
        self.assertIsNone(challenge.target_contact_id)
        self.assertIsNone(challenge.user_id)

    def test_resend_rechecks_cooldown_under_lock(self):
        flow = self.new_flow()
        AuthChallenge.objects.filter(pk=flow["flow_id"]).update(
            last_issued_at=timezone.now() - timedelta(seconds=61)
        )
        AuthAbuseBucket.objects.filter(dimension="target").delete()
        original = AuthChallenge.objects.select_for_update

        def other_resend_won(*args, **kwargs):
            AuthChallenge.objects.filter(pk=flow["flow_id"]).update(
                last_issued_at=timezone.now()
            )
            return original(*args, **kwargs)

        with patch.object(
            AuthChallenge.objects, "select_for_update", side_effect=other_resend_won
        ):
            self.assertEqual(
                resend_flow(
                    "registration", flow["flow_id"], flow["flow_control"], "192.0.2.2"
                ),
                {"status": "accepted"},
            )
        self.assertEqual(AuthChallenge.objects.get(pk=flow["flow_id"]).generation, 1)
        self.assertEqual(DeliveryIntent.objects.count(), 1)

    def test_retained_notice_does_not_starve_other_expired_payloads(self):
        now = timezone.now()
        user, _ = self.account()
        first = self.new_flow("reset", user.email)
        second = self.new_flow("reset", "unknown@example.invalid")
        proof = self.proof(first)
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(minutes=14),
        ):
            self.assertIsNone(
                confirm_flow(
                    "reset", first["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
                )
            )
        with patch(
            "accounts.flow_cleanup.timezone.now",
            return_value=now + timedelta(minutes=16),
        ):
            self.assertEqual(cleanup_flows(limit=1)["flows"], 1)
        self.assertTrue(AuthChallenge.objects.filter(pk=first["flow_id"]).exists())
        self.assertFalse(AuthChallenge.objects.filter(pk=second["flow_id"]).exists())
        self.assertTrue(
            DeliveryIntent.objects.filter(
                challenge_id=first["flow_id"],
                generation=2,
                encrypted_payload__isnull=False,
            ).exists()
        )

    def test_deep_small_json_is_a_sanitized_validation_error(self):
        self.client.raise_request_exception = False
        response = self.client.post(
            "/api/v1/auth/registration/request/",
            data="[" * 2000 + "0" + "]" * 2000,
            content_type="application/json",
            secure=True,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertFalse(AuthChallenge.objects.exists())

    def test_malformed_origins_and_budget_configuration_fail_closed(self):
        for index, origin in enumerate(
            [
                "https://pwc.invalid:99999",
                "https://pwc.invalid\\evil.invalid",
                "https://pwc.invalid\n",
                "https://pwc.invalid\t",
                "https://bad_host.invalid",
            ]
        ):
            with self.subTest(origin=origin), override_settings(
                PWC_AUTH_LINK_ORIGIN=origin
            ):
                response = self.post(
                    "registration/request", {"email": f"u{index}@example.invalid"}
                )
                self.assertEqual(response.status_code, 503)
        for budget in (0, -1, True, "100", None):
            with self.subTest(budget=budget), override_settings(
                PWC_AUTH_GLOBAL_SENDS_PER_HOUR=budget
            ):
                self.assertEqual(
                    self.post(
                        "registration/request", {"email": "budget@example.invalid"}
                    ).status_code,
                    503,
                )
        self.assertFalse(AuthChallenge.objects.exists())
        self.assertFalse(AuthAbuseBucket.objects.exists())

    def test_unsupported_legacy_anomaly_cannot_silently_release_reservation(self):
        User.objects.create(username="legacy", email="legacy@example.invalid.")
        flow = self.new_flow(email="legacy@example.invalid")
        self.assertFalse(AuthChallenge.objects.get(pk=flow["flow_id"]).eligible)
        self.assertFalse(
            DeliveryIntent.objects.exclude(template="placeholder").exists()
        )

    def test_abuse_bucket_lookup_itself_is_locked_against_cleanup(self):
        original = QuerySet.get

        def checked_get(queryset, *args, **kwargs):
            if queryset.model is AuthAbuseBucket:
                self.assertTrue(queryset.query.select_for_update)
            return original(queryset, *args, **kwargs)

        with patch.object(QuerySet, "get", new=checked_get):
            self.assertIsNone(spend("192.0.2.1", "review"))
            self.assertIsNone(spend("192.0.2.1", "review"))
        self.assertEqual(AuthAbuseBucket.objects.get().count, 2)
