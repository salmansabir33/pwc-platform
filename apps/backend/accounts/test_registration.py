"""Synthetic-only acceptance of the PWC-03A.2 slice, using PostgreSQL."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from cryptography.fernet import Fernet
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import (
    Client,
    SimpleTestCase,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.utils import timezone

from .delivery import dispatch_one
from .email_identity import normalize_email
from .flow_security import FlowProblem, digest, unseal
from .models import (
    AssuranceIntent,
    AuthAbuseBucket,
    AuthChallenge,
    AuthSession,
    DeliveryIntent,
    MfaFactor,
    SecurityEvent,
    User,
    UserContact,
)
from .registration import confirm_flow, request_flow, resend_flow

# Ephemeral test-only keys, not checked-in operational credentials.
TEST_CONFIG = dict(
    PWC_AUTH_FLOWS_ENABLED=True,
    PWC_AUTH_DELIVERY_MODE="synthetic",
    PWC_AUTH_ABUSE_KEY=Fernet.generate_key().decode(),
    PWC_AUTH_DELIVERY_ACTIVE_KEY="synthetic-1",
    PWC_AUTH_DELIVERY_KEYS={"synthetic-1": Fernet.generate_key().decode()},
    PWC_AUTH_LINK_ORIGIN="https://pwc.invalid",
)
PASSWORD = "linen river quartz meadow"
NEW_PASSWORD = "saffron telescope floating otter"


class EmailProfileTests(SimpleTestCase):
    def test_executable_b1_vectors(self):
        vectors = {
            " User.Name+Tag@EXAMPLE.invalid ": "user.name+tag@example.invalid",
            "User@BÜCHER.invalid": "user@xn--bcher-kva.invalid",
            "User@Bu\u0308cher.invalid": "user@xn--bcher-kva.invalid",
            "User@faß.invalid": "user@xn--fa-hia.invalid",
            "u@xn--fa-hia.invalid": "u@xn--fa-hia.invalid",
            "u@ＦＯＯ.invalid": "u@foo.invalid",
            "u!tag@example.invalid": "u!tag@example.invalid",
        }
        for value, expected in vectors.items():
            with self.subTest(value=value):
                self.assertEqual(normalize_email(value), expected)
                self.assertEqual(normalize_email(expected), expected)
        for value in [
            None,
            42,
            "",
            "a@@example.invalid",
            "a..b@example.invalid",
            ".a@example.invalid",
            "a.@example.invalid",
            '"a"@example.invalid',
            "a b@example.invalid",
            "a\n@example.invalid",
            "a@example.invalid.",
            "a@example.invalid。",
            "a@-bad.invalid",
            "a@foo..invalid",
            "a@☃.invalid",
            "é@example.invalid",
            "ß@example.invalid",
            "a@exam\u200bple.invalid",
            "a" * 65 + "@example.invalid",
        ]:
            with self.subTest(value=value), self.assertRaises(ValidationError):
                normalize_email(value)
        self.assertNotEqual(
            normalize_email("a.b+tag@example.invalid"),
            normalize_email("ab@example.invalid"),
        )
        self.assertNotEqual(
            normalize_email("u@faß.invalid"), normalize_email("u@fass.invalid")
        )


class FlowFixtures:
    def account(self, name="member", *, verified=True, active=True):
        user = User.objects.create_user(
            username=f"{name}-{uuid.uuid4().hex[:8]}",
            email=f"{name}@example.invalid",
            password=PASSWORD,
            is_active=active,
        )
        contact = None
        if verified:
            contact = UserContact.objects.create(
                user=user,
                kind="email",
                display_value=user.email,
                normalized_value=user.email,
                verified_at=timezone.now(),
                is_primary=True,
            )
        return user, contact

    def new_flow(
        self, purpose="registration", email="new@example.invalid", ip="192.0.2.1"
    ):
        result = request_flow(purpose, email, ip)
        self.assertNotIsInstance(result, FlowProblem)
        return result

    def proof(self, flow):
        intent = DeliveryIntent.objects.get(
            challenge_id=flow["flow_id"], state="pending"
        )
        return unseal(intent.key_id, intent.encrypted_payload)["proof"]

    def mail_proof(self, flow):
        self.assertTrue(dispatch_one())
        for message in reversed(mail.outbox):
            if flow["flow_id"] in message.body:
                link = message.body.splitlines()[1]
                self.assertEqual(urlsplit(link).query, "")
                return parse_qs(urlsplit(link).fragment)["proof"][0]
        self.fail("Synthetic mail not delivered")

    def post(self, path, payload, **extra):
        return self.client.post(
            f"/api/v1/auth/{path}/",
            data=payload,
            content_type="application/json",
            **extra,
        )


@override_settings(**TEST_CONFIG)
class RegistrationTests(FlowFixtures, TestCase):
    def test_registration_is_atomic_personal_identity_without_login(self):
        flow = self.new_flow(email="New+Tag@EXAMPLE.invalid")
        proof = self.mail_proof(flow)
        with patch.object(
            User,
            "full_clean",
            side_effect=AssertionError("must not rely on full_clean"),
        ), patch.object(
            UserContact,
            "full_clean",
            side_effect=AssertionError("must not rely on full_clean"),
        ):
            response = self.post(
                "registration/confirm",
                {"flow_id": flow["flow_id"], "proof": proof, "password": PASSWORD},
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {"status": "verified"})
        user = User.objects.get(email="new+tag@example.invalid")
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(
            user.is_staff
            or user.is_superuser
            or user.groups.exists()
            or user.user_permissions.exists()
        )
        contact = UserContact.objects.get(user=user)
        self.assertTrue(contact.is_primary and contact.verified_at)
        self.assertEqual(user.auth_epoch, 1)
        self.assertFalse(AuthSession.objects.exists())
        self.assertNotIn("sessionid", response.cookies)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertFalse(
            DeliveryIntent.objects.filter(encrypted_payload__isnull=False).exists()
        )
        self.assertTrue(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)
        stored = repr(list(AuthChallenge.objects.values())) + repr(
            list(SecurityEvent.objects.values())
        )
        for secret in (proof, flow["flow_control"], PASSWORD):
            self.assertNotIn(secret, stored)

    def test_valid_proof_precedes_password_validation_and_weak_password_does_not_consume(
        self,
    ):
        flow = self.new_flow()
        proof = self.proof(flow)
        bad = self.post(
            "registration/confirm",
            {"flow_id": flow["flow_id"], "proof": "x" * 43, "password": "short"},
        )
        self.assertEqual(bad.json()["error"]["code"], "CHALLENGE_INVALID")
        weak = self.post(
            "registration/confirm",
            {"flow_id": flow["flow_id"], "proof": proof, "password": "short"},
        )
        self.assertEqual(weak.json()["error"]["code"], "VALIDATION_ERROR")
        self.assertIn("password", weak.json()["error"]["field_errors"])
        self.assertIsNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)
        self.assertEqual(
            self.post(
                "registration/confirm",
                {"flow_id": flow["flow_id"], "proof": proof, "password": PASSWORD},
            ).status_code,
            201,
        )
        self.assertEqual(
            self.post(
                "registration/confirm",
                {"flow_id": flow["flow_id"], "proof": proof, "password": PASSWORD},
            ).json()["error"]["code"],
            "CHALLENGE_INVALID",
        )

    def test_case_variant_pending_flows_cannot_create_duplicate_or_orphan_user(self):
        now = timezone.now()
        first = self.new_flow(email="Case@example.invalid")
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            second = self.new_flow(email="CASE@EXAMPLE.invalid")
        proofs = [self.proof(first), self.proof(second)]
        self.assertEqual(
            confirm_flow(
                "registration", first["flow_id"], proofs[0], PASSWORD, "192.0.2.2"
            ),
            {"status": "verified"},
        )
        result = confirm_flow(
            "registration", second["flow_id"], proofs[1], PASSWORD, "192.0.2.3"
        )
        self.assertEqual(result.code, "CHALLENGE_INVALID")
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserContact.objects.count(), 1)

    def test_failures_commit_count_invalidate_and_destroy_pending_ciphertext(self):
        flow = self.new_flow()
        proof = self.proof(flow)
        for _ in range(5):
            result = confirm_flow(
                "registration", flow["flow_id"], "x" * 43, PASSWORD, "192.0.2.2"
            )
            self.assertEqual(result.code, "CHALLENGE_INVALID")
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        self.assertEqual(challenge.failure_count, 5)
        self.assertIsNotNone(challenge.invalidated_at)
        self.assertIsNone(
            DeliveryIntent.objects.get(challenge=challenge).encrypted_payload
        )
        self.assertEqual(
            confirm_flow(
                "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        self.assertFalse(User.objects.exists())

    def test_wrong_purpose_expiry_and_get_preview_do_not_consume(self):
        flow = self.new_flow()
        proof = self.proof(flow)
        wrong = confirm_flow("reset", flow["flow_id"], proof, PASSWORD, "192.0.2.2")
        self.assertEqual(wrong.code, "CHALLENGE_INVALID")
        self.assertEqual(AuthChallenge.objects.get(pk=flow["flow_id"]).failure_count, 0)
        self.assertEqual(
            self.client.get("/api/v1/auth/registration/confirm/").status_code, 405
        )
        self.assertIsNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)
        with patch(
            "accounts.registration.timezone.now",
            return_value=timezone.now() + timedelta(minutes=31),
        ):
            result = confirm_flow(
                "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.2"
            )
            self.assertEqual(result.code, "CHALLENGE_INVALID")
            self.assertEqual(
                resend_flow(
                    "registration", flow["flow_id"], flow["flow_control"], "192.0.2.2"
                ),
                {"status": "accepted"},
            )
        self.assertFalse(User.objects.exists())

    def test_resend_control_cooldown_rotation_and_other_flow_isolation(self):
        now = timezone.now()
        first = self.new_flow()
        first_proof = self.proof(first)
        self.assertEqual(
            resend_flow(
                "registration", first["flow_id"], first["flow_control"], "192.0.2.2"
            ),
            {"status": "accepted"},
        )
        self.assertEqual(AuthChallenge.objects.get(pk=first["flow_id"]).generation, 1)
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            second = self.new_flow()
            second_proof = self.proof(second)
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=122),
        ):
            self.assertEqual(
                resend_flow("registration", first["flow_id"], "x" * 43, "192.0.2.2"),
                {"status": "accepted"},
            )
            self.assertEqual(
                AuthChallenge.objects.get(pk=first["flow_id"]).generation, 1
            )
            self.assertEqual(
                resend_flow(
                    "registration", first["flow_id"], first["flow_control"], "192.0.2.2"
                ),
                {"status": "accepted"},
            )
            rotated = DeliveryIntent.objects.get(
                challenge_id=first["flow_id"], generation=2
            )
            new_proof = unseal(rotated.key_id, rotated.encrypted_payload)["proof"]
            self.assertNotEqual(first_proof, new_proof)
            self.assertEqual(
                confirm_flow(
                    "registration", first["flow_id"], first_proof, PASSWORD, "192.0.2.2"
                ).code,
                "CHALLENGE_INVALID",
            )
            self.assertEqual(
                confirm_flow(
                    "registration",
                    second["flow_id"],
                    second_proof,
                    PASSWORD,
                    "192.0.2.3",
                ),
                {"status": "verified"},
            )
        self.assertEqual(AuthChallenge.objects.get(pk=second["flow_id"]).generation, 1)
        self.assertIsNone(
            DeliveryIntent.objects.get(
                challenge_id=first["flow_id"], generation=1
            ).encrypted_payload
        )

    def test_existing_new_and_ineligible_requests_share_shape_and_async_delivery(self):
        self.account("verified")
        self.account("legacy", verified=False)
        self.account("disabled", active=False)
        shapes = []
        with patch(
            "accounts.delivery.deliver_message",
            side_effect=AssertionError("HTTP must not send"),
        ):
            for email in [
                "verified@example.invalid",
                "legacy@example.invalid",
                "disabled@example.invalid",
                "unknown@example.invalid",
            ]:
                response = self.post("registration/request", {"email": email})
                self.assertEqual(response.status_code, 202)
                shapes.append(set(response.json()))
        self.assertTrue(all(shape == shapes[0] for shape in shapes))
        self.assertEqual(
            list(AuthChallenge.objects.values_list("eligible", flat=True)).count(True),
            1,
        )
        while dispatch_one():
            pass
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["unknown@example.invalid"])


@override_settings(**TEST_CONFIG)
class ResetTests(FlowFixtures, TestCase):
    def test_reset_revokes_sessions_advances_epoch_and_sets_hold_without_login(self):
        user, contact = self.account()
        now = timezone.now()
        session = AuthSession.objects.create(
            user=user,
            transport="web",
            portal="ngo_web",
            web_key_digest="b" * 64,
            auth_epoch=1,
            created_at=now,
            last_interactive_at=now,
            absolute_expires_at=now + timedelta(hours=2),
        )
        mobile = AuthSession.objects.create(
            user=user,
            transport="mobile",
            portal="mobile",
            auth_epoch=1,
            created_at=now,
            last_interactive_at=now,
            absolute_expires_at=now + timedelta(days=2),
        )
        assurance = AssuranceIntent.objects.create(
            user=user,
            session=session,
            auth_epoch=1,
            recovery_generation=0,
            operation="synthetic.operation",
            context_kind="ngo",
            context_id=uuid.uuid4(),
            request_digest="a" * 64,
            created_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        flow = self.new_flow("reset", user.email)
        proof = self.mail_proof(flow)
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            other = self.new_flow("reset", user.email, "192.0.2.4")
        response = self.post(
            "password-reset/confirm",
            {"flow_id": flow["flow_id"], "proof": proof, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertFalse(user.check_password(PASSWORD))
        self.assertEqual(
            (user.auth_epoch, user.recovery_generation, user.recovery_hold_state),
            (2, 1, "restricted"),
        )
        self.assertEqual(user.hold_reason, "password_reset")
        self.assertFalse(
            AuthSession.objects.filter(user=user, revoked_at__isnull=True).exists()
        )
        self.assertEqual(AuthSession.objects.count(), 2)
        for item in (session, mobile, assurance):
            item.refresh_from_db()
        self.assertEqual(session.revocation_reason, "password_reset")
        self.assertIsNotNone(assurance.invalidated_at)
        self.assertIsNotNone(
            AuthChallenge.objects.get(pk=other["flow_id"]).invalidated_at
        )
        self.assertIsNone(
            DeliveryIntent.objects.get(challenge_id=other["flow_id"]).encrypted_payload
        )
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.5"
            ).code,
            "CHALLENGE_INVALID",
        )
        self.assertNotIn("sessionid", response.cookies)
        self.assertTrue(dispatch_one())  # proof-free notification, generation N+1
        self.assertEqual(mail.outbox[-1].subject, "PWC password changed")
        self.assertNotIn(proof, mail.outbox[-1].body)

    def test_reset_preserves_mfa_and_stronger_review_hold(self):
        user, _ = self.account()
        factor = MfaFactor.objects.create(
            user=user,
            state="active",
            key_id="synthetic",
            encrypted_secret=b"synthetic-no-real-totp",
            confirmed_at=timezone.now(),
            enrollment_session=AuthSession.objects.create(
                user=user,
                transport="mobile",
                portal="mobile",
                auth_epoch=1,
                absolute_expires_at=timezone.now() + timedelta(hours=1),
            ),
            auth_epoch=1,
            recovery_generation=0,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        user.recovery_hold_state = "review_required"
        user.hold_set_at = timezone.now()
        user.hold_reason = "recovery_code"
        user.hold_factor = factor
        user.hold_factor_revision = factor.revision
        user.save()
        before = user.hold_set_at
        flow = self.new_flow("reset", user.email)
        self.assertIsNone(
            confirm_flow(
                "reset", flow["flow_id"], self.proof(flow), NEW_PASSWORD, "192.0.2.2"
            )
        )
        user.refresh_from_db()
        factor.refresh_from_db()
        self.assertEqual(user.recovery_hold_state, "review_required")
        self.assertEqual(user.hold_reason, "recovery_code")
        self.assertEqual(user.hold_set_at, before)
        self.assertEqual(user.hold_factor_id, factor.pk)
        self.assertEqual(factor.state, "active")
        self.assertEqual(factor.encrypted_secret, b"synthetic-no-real-totp")

    def test_reset_inert_for_legacy_duplicates_disabled_and_unknown(self):
        self.account("legacy", verified=False)
        self.account("legacy", verified=False)
        self.account("disabled", active=False)
        for email in [
            "legacy@example.invalid",
            "disabled@example.invalid",
            "unknown@example.invalid",
        ]:
            flow = self.new_flow("reset", email)
            self.assertFalse(AuthChallenge.objects.get(pk=flow["flow_id"]).eligible)
            result = confirm_flow(
                "reset", flow["flow_id"], self.proof(flow), NEW_PASSWORD, "192.0.2.2"
            )
            self.assertEqual(result.code, "CHALLENGE_INVALID")
        while dispatch_one():
            pass
        self.assertEqual(len(getattr(mail, "outbox", [])), 0)
        self.assertFalse(User.objects.exclude(auth_epoch=1).exists())

    def test_reset_rejects_stale_epoch_and_contact_owner_without_full_clean(self):
        user, contact = self.account()
        other, _ = self.account("other")
        flow = self.new_flow("reset", user.email)
        proof = self.proof(flow)
        AuthChallenge.objects.filter(pk=flow["flow_id"]).update(user=other)
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        AuthChallenge.objects.filter(pk=flow["flow_id"]).update(user=user)
        User.objects.filter(pk=user.pk).update(auth_epoch=2)
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        user.refresh_from_db()
        other.refresh_from_db()
        self.assertTrue(
            user.check_password(PASSWORD) and other.check_password(PASSWORD)
        )
        self.assertIsNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)

    def test_reset_rejects_retired_contact_disabled_user_and_expires_at_15_minutes(
        self,
    ):
        user, contact = self.account()
        flow = self.new_flow("reset", user.email)
        proof = self.proof(flow)
        UserContact.objects.filter(pk=contact.pk).update(
            retired_at=timezone.now(), is_primary=False
        )
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        UserContact.objects.filter(pk=contact.pk).update(
            retired_at=None, is_primary=True
        )
        User.objects.filter(pk=user.pk).update(is_active=False)
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        User.objects.filter(pk=user.pk).update(is_active=True)
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        self.assertEqual(
            challenge.expires_at - challenge.created_at, timedelta(minutes=15)
        )
        with patch(
            "accounts.registration.timezone.now", return_value=challenge.expires_at
        ):
            self.assertEqual(
                confirm_flow(
                    "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
                ).code,
                "CHALLENGE_INVALID",
            )
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))

    def test_reset_password_policy_unconsumed_and_wrong_endpoint_bound(self):
        user, _ = self.account()
        flow = self.new_flow("reset", user.email)
        proof = self.proof(flow)
        self.assertEqual(
            confirm_flow(
                "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        self.assertEqual(
            confirm_flow("reset", flow["flow_id"], proof, "short", "192.0.2.2").code,
            "VALIDATION_ERROR",
        )
        self.assertIsNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)
        user.refresh_from_db()
        self.assertEqual(user.auth_epoch, 1)


@override_settings(**TEST_CONFIG)
class TransportAndAbuseTests(FlowFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_browser_csrf_bootstrap_exact_origin_and_anonymous_protection(self):
        rejected = self.post(
            "registration/request",
            {"email": "a@example.invalid"},
            HTTP_ORIGIN="https://testserver",
            secure=True,
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(rejected.json()["error"]["code"], "CSRF_FAILED")
        token = self.client.get("/api/v1/auth/csrf/", secure=True).json()["csrf_token"]
        hostile = self.post(
            "registration/request",
            {"email": "a@example.invalid"},
            HTTP_ORIGIN="https://attacker.invalid",
            HTTP_X_CSRFTOKEN=token,
            secure=True,
        )
        self.assertEqual(hostile.status_code, 403)
        accepted = self.post(
            "registration/request",
            {"email": "a@example.invalid"},
            HTTP_ORIGIN="https://testserver",
            HTTP_X_CSRFTOKEN=token,
            secure=True,
        )
        self.assertEqual(accepted.status_code, 202)
        self.assertEqual(AuthChallenge.objects.count(), 1)

    def test_native_json_without_cookies_allowed_csrf_cookie_alone_not_session(self):
        self.client.get("/api/v1/auth/csrf/")
        self.assertEqual(
            self.post(
                "registration/request", {"email": "a@example.invalid"}
            ).status_code,
            202,
        )
        bad = self.client.post(
            "/api/v1/auth/registration/request/",
            data='{"email":"b@example.invalid"}',
            content_type="text/plain",
        )
        self.assertEqual(bad.status_code, 400)

    def test_mixed_and_authorization_transports_rejected_before_effects(self):
        self.client.cookies["sessionid"] = "synthetic-incidental"
        response = self.post(
            "registration/request",
            {"email": "a@example.invalid"},
            HTTP_AUTHORIZATION="Bearer synthetic",
        )
        self.assertEqual(response.json()["error"]["code"], "AMBIGUOUS_CREDENTIALS")
        self.client.cookies.clear()
        response = self.post(
            "registration/request",
            {"email": "a@example.invalid"},
            HTTP_AUTHORIZATION="Bearer synthetic",
        )
        self.assertEqual(response.json()["error"]["code"], "TRANSPORT_NOT_ALLOWED")
        self.assertFalse(AuthChallenge.objects.exists())
        self.assertFalse(AuthAbuseBucket.objects.exists())

    def test_incidental_logged_in_cookie_does_not_select_target_or_login_created_user(
        self,
    ):
        actor, _ = self.account("actor")
        self.client.force_login(actor)
        flow = self.new_flow()
        proof = self.proof(flow)
        token = self.client.get("/api/v1/auth/csrf/", secure=True).json()["csrf_token"]
        response = self.post(
            "registration/confirm",
            {"flow_id": flow["flow_id"], "proof": proof, "password": NEW_PASSWORD},
            secure=True,
            HTTP_ORIGIN="https://testserver",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(actor.pk))
        actor.refresh_from_db()
        self.assertTrue(actor.check_password(PASSWORD))
        self.assertEqual(User.objects.count(), 2)

    def test_account_independent_global_budget_shared_across_routes_and_clients(self):
        user, _ = self.account()
        with override_settings(PWC_AUTH_GLOBAL_SENDS_PER_HOUR=1):
            self.assertEqual(
                self.post(
                    "registration/request", {"email": "new@example.invalid"}
                ).status_code,
                202,
            )
            self.client = Client(enforce_csrf_checks=True, REMOTE_ADDR="192.0.2.22")
            response = self.post("password-reset/request", {"email": user.email})
            self.assertEqual(response.status_code, 429)
            self.assertTrue(int(response["Retry-After"]) > 0)
            self.assertEqual(response.json()["error"]["code"], "RATE_LIMITED")
        self.assertEqual(AuthChallenge.objects.count(), 1)

    def test_target_budget_is_shared_and_invalid_resend_cannot_spend_victim_budget(
        self,
    ):
        flow = self.new_flow()
        self.assertEqual(
            resend_flow("registration", flow["flow_id"], "x" * 43, "192.0.2.22"),
            {"status": "accepted"},
        )
        response = self.post(
            "password-reset/request",
            {"email": "NEW@example.invalid"},
            REMOTE_ADDR="192.0.2.23",
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(AuthChallenge.objects.count(), 1)
        target_counts = list(
            AuthAbuseBucket.objects.filter(dimension="target").values_list(
                "count", flat=True
            )
        )
        self.assertEqual(sorted(target_counts), [1, 2])

    def test_errors_are_sanitized_and_malformed_input_has_no_effect(self):
        for body in [
            {},
            [],
            {"email": None},
            {"email": "a@example.invalid", "redirect": "https://evil.invalid"},
            {"email": "not-mail"},
        ]:
            response = self.post("registration/request", body)
            self.assertEqual(response.status_code, 400)
            error = response.json()["error"]
            self.assertEqual(
                set(error), {"code", "message", "field_errors", "request_id"}
            )
            uuid.UUID(error["request_id"])
        self.assertFalse(AuthChallenge.objects.exists())
        with override_settings(PWC_AUTH_DELIVERY_KEYS={}):
            response = self.post("registration/request", {"email": "a@example.invalid"})
            self.assertEqual(response.status_code, 503)
            self.assertNotIn("synthetic-1", response.content.decode())

    def test_unavailable_database_returns_generic_503(self):
        from django.db import OperationalError

        with patch(
            "accounts.registration.spend",
            side_effect=OperationalError("sensitive infrastructure detail"),
        ):
            response = self.post("registration/request", {"email": "a@example.invalid"})
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("sensitive", response.content.decode())


@override_settings(**TEST_CONFIG)
class DeliveryTests(FlowFixtures, TestCase):
    def test_ciphertext_tamper_retries_bounded_and_erases_secrets_without_logging(self):
        flow = self.new_flow()
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        original = bytes(intent.encrypted_payload)
        self.assertNotIn(self.proof(flow).encode(), original)
        intent.encrypted_payload = original[:-1] + b"!"
        intent.save(update_fields=["encrypted_payload"])
        for attempt in range(1, 6):
            DeliveryIntent.objects.filter(pk=intent.pk).update(
                next_attempt_at=timezone.now()
            )
            self.assertTrue(dispatch_one())
            intent.refresh_from_db()
            self.assertEqual(intent.attempts, attempt)
        self.assertEqual(intent.state, "failed")
        self.assertIsNone(intent.encrypted_payload)
        self.assertIsNotNone(intent.secret_deleted_at)
        self.assertEqual(len(getattr(mail, "outbox", [])), 0)

    def test_provider_failure_is_async_retryable_then_success_erases_payload(self):
        flow = self.new_flow()
        with patch(
            "accounts.delivery.deliver_message",
            side_effect=RuntimeError("synthetic provider error"),
        ):
            self.assertTrue(dispatch_one())
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        self.assertEqual(intent.state, "pending")
        self.assertEqual(intent.attempts, 1)
        self.assertIsNotNone(intent.encrypted_payload)
        self.assertGreater(intent.next_attempt_at, timezone.now())
        DeliveryIntent.objects.filter(pk=intent.pk).update(
            next_attempt_at=timezone.now()
        )
        self.assertTrue(dispatch_one())
        intent.refresh_from_db()
        self.assertEqual(intent.state, "sent")
        self.assertIsNone(intent.encrypted_payload)
        self.assertEqual(len(mail.outbox), 1)

    def test_rotation_requires_old_key_and_unknown_key_fails_closed(self):
        flow = self.new_flow()
        from django.conf import settings

        keys = dict(settings.PWC_AUTH_DELIVERY_KEYS) | {
            "synthetic-2": Fernet.generate_key().decode()
        }
        with override_settings(
            PWC_AUTH_DELIVERY_KEYS={"synthetic-2": keys["synthetic-2"]},
            PWC_AUTH_DELIVERY_ACTIVE_KEY="synthetic-2",
        ):
            self.assertTrue(dispatch_one())
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        self.assertEqual(intent.state, "pending")
        DeliveryIntent.objects.filter(pk=intent.pk).update(
            next_attempt_at=timezone.now()
        )
        with override_settings(
            PWC_AUTH_DELIVERY_KEYS=keys, PWC_AUTH_DELIVERY_ACTIVE_KEY="synthetic-2"
        ):
            self.assertTrue(dispatch_one())
        intent.refresh_from_db()
        self.assertEqual(intent.state, "sent")

    def test_expired_mail_is_not_sent_and_expired_lease_can_be_reclaimed(self):
        flow = self.new_flow()
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        with patch(
            "accounts.delivery.timezone.now",
            return_value=timezone.now() + timedelta(minutes=31),
        ):
            self.assertTrue(dispatch_one())
        intent.refresh_from_db()
        self.assertEqual(intent.state, "expired")
        self.assertIsNone(intent.encrypted_payload)
        second = self.new_flow(email="other@example.invalid")
        DeliveryIntent.objects.filter(challenge_id=second["flow_id"]).update(
            state="leased",
            attempts=1,
            lease_expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertTrue(dispatch_one())
        self.assertEqual(
            DeliveryIntent.objects.get(challenge_id=second["flow_id"]).attempts, 2
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_or_resend_during_io_cannot_be_overwritten_by_stale_worker(self):
        flow = self.new_flow()
        proof = self.proof(flow)
        with patch(
            "accounts.delivery.deliver_message",
            side_effect=lambda *a: confirm_flow(
                "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.2"
            ),
        ):
            self.assertTrue(dispatch_one())
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        self.assertEqual(intent.state, "cancelled")
        self.assertIsNone(intent.encrypted_payload)
        self.assertIsNotNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)


@override_settings(**TEST_CONFIG)
class ConcurrentFlowTests(FlowFixtures, TransactionTestCase):
    def test_postgresql_same_proof_is_consumed_once(self):
        self.assertEqual(connection.vendor, "postgresql")
        flow = self.new_flow()
        proof = self.proof(flow)
        from threading import Barrier

        barrier = Barrier(2)

        def confirm(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = confirm_flow(
                    "registration",
                    flow["flow_id"],
                    proof,
                    PASSWORD,
                    f"192.0.2.{index+2}",
                )
                return (
                    result.code if isinstance(result, FlowProblem) else result["status"]
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, range(2)))
        self.assertEqual(sorted(results), ["CHALLENGE_INVALID", "verified"])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserContact.objects.count(), 1)

    def test_postgresql_two_flows_case_collision_rolls_back_losing_user(self):
        now = timezone.now()
        first = self.new_flow(email="Case@example.invalid")
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            second = self.new_flow(email="CASE@EXAMPLE.invalid")
        entries = [(first, self.proof(first)), (second, self.proof(second))]
        from threading import Barrier

        barrier = Barrier(2)

        def confirm(item):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                flow, proof = item
                result = confirm_flow(
                    "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.9"
                )
                return (
                    result.code if isinstance(result, FlowProblem) else result["status"]
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, entries))
        self.assertEqual(sorted(results), ["CHALLENGE_INVALID", "verified"])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserContact.objects.count(), 1)

    def test_postgresql_reset_confirmations_advance_epoch_once(self):
        user, _ = self.account()
        flow = self.new_flow("reset", user.email)
        proof = self.proof(flow)
        from threading import Barrier

        barrier = Barrier(2)

        def confirm(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = confirm_flow(
                    "reset", flow["flow_id"], proof, NEW_PASSWORD, f"192.0.2.{index+2}"
                )
                return result.code if isinstance(result, FlowProblem) else "reset"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, range(2)))
        self.assertEqual(sorted(results), ["CHALLENGE_INVALID", "reset"])
        user.refresh_from_db()
        self.assertEqual((user.auth_epoch, user.recovery_generation), (2, 1))


@override_settings(**TEST_CONFIG)
class CleanupAndHardeningTests(FlowFixtures, TestCase):
    def test_cleanup_preserves_replay_floor_then_erases_expired_ciphertexts_and_counters(
        self,
    ):
        from .flow_cleanup import cleanup_flows

        flow = self.new_flow()
        proof = self.proof(flow)
        confirm_flow("registration", flow["flow_id"], proof, PASSWORD, "192.0.2.2")
        second = self.new_flow(email="pending@example.invalid")
        self.assertEqual(cleanup_flows()["flows"], 0)
        self.assertTrue(AuthChallenge.objects.filter(pk=flow["flow_id"]).exists())
        with patch(
            "accounts.flow_cleanup.timezone.now",
            return_value=timezone.now() + timedelta(hours=2),
        ):
            with override_settings(
                PWC_AUTH_DELIVERY_KEYS={}, PWC_AUTH_FLOWS_ENABLED=False
            ):
                disposed = cleanup_flows()
        self.assertEqual(disposed["flows"], 2)
        self.assertEqual(disposed["payloads"], 1)
        self.assertFalse(AuthChallenge.objects.exists())
        self.assertFalse(DeliveryIntent.objects.exists())
        self.assertFalse(AuthAbuseBucket.objects.exists())
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(SecurityEvent.objects.exists())
        self.assertEqual(
            confirm_flow(
                "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.3"
            ).code,
            "CHALLENGE_INVALID",
        )

    def test_notice_retained_beyond_proof_deadline_but_not_beyond_own_deadline(self):
        from .flow_cleanup import cleanup_flows

        user, _ = self.account()
        flow = self.new_flow("reset", user.email)
        proof = self.proof(flow)
        now = timezone.now()
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(minutes=14),
        ):
            self.assertIsNone(
                confirm_flow("reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2")
            )
        with patch(
            "accounts.flow_cleanup.timezone.now",
            return_value=now + timedelta(minutes=16),
        ):
            self.assertEqual(cleanup_flows()["flows"], 0)
            self.assertTrue(dispatch_one())
            self.assertEqual(mail.outbox[-1].subject, "PWC password changed")
        with patch(
            "accounts.flow_cleanup.timezone.now",
            return_value=now + timedelta(minutes=30),
        ):
            self.assertEqual(cleanup_flows()["flows"], 1)
        self.assertTrue(User.objects.get(pk=user.pk).check_password(NEW_PASSWORD))

    def test_reset_request_does_not_change_password_epoch_sessions_or_hold(self):
        user, _ = self.account()
        before = (
            user.password,
            user.auth_epoch,
            user.recovery_generation,
            user.recovery_hold_state,
        )
        self.new_flow("reset", user.email)
        user.refresh_from_db()
        self.assertEqual(
            (
                user.password,
                user.auth_epoch,
                user.recovery_generation,
                user.recovery_hold_state,
            ),
            before,
        )
        self.assertFalse(AuthSession.objects.exists())

    def test_clear_hold_captures_existing_factor_and_transition_evidence(self):
        user, _ = self.account()
        session = AuthSession.objects.create(
            user=user,
            transport="mobile",
            portal="mobile",
            auth_epoch=1,
            absolute_expires_at=timezone.now() + timedelta(hours=1),
        )
        factor = MfaFactor.objects.create(
            user=user,
            state="active",
            key_id="synthetic",
            encrypted_secret=b"not-a-real-totp",
            confirmed_at=timezone.now(),
            enrollment_session=session,
            auth_epoch=1,
            recovery_generation=0,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        flow = self.new_flow("reset", user.email)
        self.assertIsNone(
            confirm_flow(
                "reset", flow["flow_id"], self.proof(flow), NEW_PASSWORD, "192.0.2.2"
            )
        )
        user.refresh_from_db()
        self.assertEqual(user.hold_factor_id, factor.pk)
        evidence = SecurityEvent.objects.get(event="auth.reset_completed")
        self.assertEqual(
            (evidence.previous_hold_state, evidence.new_hold_state),
            ("clear", "restricted"),
        )
        self.assertEqual((evidence.auth_epoch, evidence.recovery_generation), (2, 1))
        self.assertEqual(
            (evidence.factor_id_snapshot, evidence.factor_revision), (factor.pk, 1)
        )
        self.assertEqual(evidence.reason, "password_reset")

    def test_factor_with_foreign_enrollment_session_is_not_trusted_by_reset_service(
        self,
    ):
        user, _ = self.account()
        other, _ = self.account("other")
        session = AuthSession.objects.create(
            user=other,
            transport="mobile",
            portal="mobile",
            auth_epoch=1,
            absolute_expires_at=timezone.now() + timedelta(hours=1),
        )
        MfaFactor.objects.create(
            user=user,
            state="active",
            key_id="synthetic",
            encrypted_secret=b"not-real",
            confirmed_at=timezone.now(),
            enrollment_session=session,
            auth_epoch=1,
            recovery_generation=0,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        flow = self.new_flow("reset", user.email)
        self.assertEqual(
            confirm_flow(
                "reset", flow["flow_id"], self.proof(flow), NEW_PASSWORD, "192.0.2.2"
            ).code,
            "CHALLENGE_INVALID",
        )
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.recovery_hold_state, "clear")

    def test_ipv6_equivalences_and_forwarded_ip_do_not_bypass_budget(self):
        from .registration import spend

        for index in range(30):
            self.assertIsNone(
                spend(
                    "2001:db8::1" if index % 2 else "2001:0db8:0:0:0:0:0:1", "synthetic"
                )
            )
        self.assertEqual(spend("2001:db8::1", "synthetic").code, "RATE_LIMITED")
        self.assertEqual(
            AuthAbuseBucket.objects.filter(route="synthetic:900").count(), 1
        )
        for index in range(31):
            response = self.post(
                "registration/confirm",
                {"flow_id": str(uuid.uuid4()), "proof": "x" * 43, "password": PASSWORD},
                HTTP_X_FORWARDED_FOR=f"192.0.2.{index}",
            )
        self.assertEqual(response.status_code, 429)
        # Oversized attempts never allocate further flow buckets once IP denied.
        count = AuthAbuseBucket.objects.count()
        for index in range(5):
            self.post(
                "registration/confirm",
                {"flow_id": str(uuid.uuid4()), "proof": "x" * 43, "password": PASSWORD},
                HTTP_X_FORWARDED_FOR=f"198.51.100.{index}",
            )
        self.assertEqual(AuthAbuseBucket.objects.count(), count)
        self.assertEqual(
            SecurityEvent.objects.filter(event="auth.rate_limited").count(), 2
        )

    def test_retry_deadline_does_not_extend_resend_cooldown_or_flow_expiry(self):
        now = timezone.now()
        flow = self.new_flow()
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        original_deadline = challenge.expires_at
        DeliveryIntent.objects.filter(challenge=challenge).update(
            next_attempt_at=now + timedelta(minutes=8)
        )
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            self.assertEqual(
                resend_flow(
                    "registration", flow["flow_id"], flow["flow_control"], "192.0.2.2"
                ),
                {"status": "accepted"},
            )
        challenge.refresh_from_db()
        self.assertEqual(challenge.generation, 2)
        self.assertEqual(challenge.expires_at, original_deadline)

    def test_stale_lease_ack_cannot_overwrite_reclaimed_attempt(self):
        flow = self.new_flow()
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])

        def reclaim(*args):
            DeliveryIntent.objects.filter(pk=intent.pk).update(
                attempts=2, lease_expires_at=timezone.now() + timedelta(seconds=60)
            )

        with patch("accounts.delivery.deliver_message", side_effect=reclaim):
            dispatch_one()
        intent.refresh_from_db()
        self.assertEqual((intent.state, intent.attempts), ("leased", 2))
        self.assertIsNotNone(intent.encrypted_payload)

    def test_unapproved_live_mode_and_bad_link_origin_fail_closed_before_writes(self):
        for config in [
            dict(PWC_AUTH_DELIVERY_MODE="smtp"),
            dict(PWC_AUTH_LINK_ORIGIN="http://pwc.invalid"),
            dict(PWC_AUTH_LINK_ORIGIN="https://user:password@pwc.invalid"),
            dict(PWC_AUTH_LINK_ORIGIN="https://pwc.invalid/path"),
        ]:
            with override_settings(**config):
                response = self.post(
                    "registration/request", {"email": "a@example.invalid"}
                )
                self.assertEqual(response.status_code, 503)
        self.assertFalse(AuthChallenge.objects.exists())
        self.assertFalse(AuthAbuseBucket.objects.exists())

    def test_synthetic_request_timing_distributions_are_measured_without_provider_calls(
        self,
    ):
        from statistics import median
        from time import perf_counter

        groups = {
            name: []
            for name in (
                "registration_new",
                "registration_existing",
                "reset_eligible",
                "reset_unknown",
            )
        }
        with patch(
            "accounts.delivery.deliver_message",
            side_effect=AssertionError("No provider in HTTP path"),
        ):
            for group, samples in groups.items():
                for index in range(8):
                    email = f"{group}-{index}@example.invalid"
                    if group in ("registration_existing", "reset_eligible"):
                        user = User.objects.create(
                            username=f"{group}-{index}", email=email
                        )
                        UserContact.objects.create(
                            user=user,
                            kind="email",
                            normalized_value=email,
                            display_value=email,
                            verified_at=timezone.now(),
                            is_primary=True,
                        )
                    start = perf_counter()
                    response = self.post(
                        (
                            "password-reset/request"
                            if group.startswith("reset")
                            else "registration/request"
                        ),
                        {"email": email},
                        REMOTE_ADDR=f"192.0.2.{list(groups).index(group)+10}",
                    )
                    samples.append((perf_counter() - start) * 1000)
                    self.assertEqual(response.status_code, 202)
        print(
            "\nSynthetic request timing ms (8/group; not production side-channel certification): "
            + "; ".join(
                f"{name}: min={min(values):.2f}, median={median(values):.2f}, max={max(values):.2f}"
                for name, values in groups.items()
            )
        )


@override_settings(**TEST_CONFIG)
class LegacyCanonicalSafetyTests(FlowFixtures, TestCase):
    def test_idna_and_whitespace_legacy_aliases_remain_reserved_not_auto_linked(self):
        for index, (legacy, canonical) in enumerate(
            [
                ("Legacy@BÜCHER.invalid", "legacy@xn--bcher-kva.invalid"),
                (" space@example.invalid ", "space@example.invalid"),
                ("Other@Bu\u0308cher.invalid", "other@xn--bcher-kva.invalid"),
            ]
        ):
            User.objects.create(username=f"legacy-{index}", email=legacy)
            flow = self.new_flow(email=canonical)
            self.assertFalse(AuthChallenge.objects.get(pk=flow["flow_id"]).eligible)
            self.assertEqual(
                confirm_flow(
                    "registration",
                    flow["flow_id"],
                    self.proof(flow),
                    PASSWORD,
                    "192.0.2.2",
                ).code,
                "CHALLENGE_INVALID",
            )
        self.assertEqual(User.objects.count(), 3)
        self.assertFalse(UserContact.objects.exists())

    def test_large_anomaly_inventory_fails_closed_without_unbounded_scan(self):
        User.objects.bulk_create(
            [
                User(username=f"legacy-{index}", email=f"u{index}@bücher.invalid")
                for index in range(101)
            ]
        )
        flow = self.new_flow(email="unrelated@example.invalid")
        self.assertFalse(AuthChallenge.objects.get(pk=flow["flow_id"]).eligible)
        self.assertEqual(User.objects.count(), 101)


@override_settings(**TEST_CONFIG)
class AdditionalPostgresRaces(FlowFixtures, TransactionTestCase):
    def test_independent_reset_proofs_for_one_user_are_linearized(self):
        from threading import Barrier

        user, _ = self.account()
        now = timezone.now()
        first = self.new_flow("reset", user.email)
        with patch(
            "accounts.registration.timezone.now",
            return_value=now + timedelta(seconds=61),
        ):
            second = self.new_flow("reset", user.email)
        entries = [(first, self.proof(first)), (second, self.proof(second))]
        barrier = Barrier(2)

        def confirm(item):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                flow, proof = item
                result = confirm_flow(
                    "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.9"
                )
                return result.code if isinstance(result, FlowProblem) else "reset"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(confirm, entries))
        self.assertEqual(sorted(results), ["CHALLENGE_INVALID", "reset"])
        user.refresh_from_db()
        self.assertEqual((user.auth_epoch, user.recovery_generation), (2, 1))
        self.assertEqual(
            AuthChallenge.objects.filter(consumed_at__isnull=False).count(), 1
        )
        self.assertEqual(
            SecurityEvent.objects.filter(event="auth.reset_completed").count(), 1
        )

    def test_two_dispatchers_claim_one_current_intent(self):
        from threading import Barrier, Event

        flow = self.new_flow()
        entered, release, start = Event(), Event(), Barrier(2)

        def send(*args):
            entered.set()
            if not release.wait(timeout=10):
                raise AssertionError("second dispatcher blocked on mail I/O")

        def dispatch(index):
            close_old_connections()
            try:
                start.wait(timeout=10)
                result = dispatch_one()
                if not result:
                    release.set()
                return result
            finally:
                close_old_connections()

        with patch("accounts.delivery.deliver_message", side_effect=send) as adapter:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(dispatch, range(2)))
            self.assertEqual(adapter.call_count, 1)
        self.assertEqual(sorted(results), [False, True])
        self.assertTrue(entered.is_set())
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        self.assertEqual((intent.state, intent.attempts), ("sent", 1))
        self.assertIsNone(intent.encrypted_payload)

    def test_concurrent_public_requests_share_atomic_target_budget(self):
        from threading import Barrier

        barrier = Barrier(2)

        def request(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = request_flow(
                    "registration", "shared@example.invalid", f"192.0.2.{index+2}"
                )
                return (
                    result.code if isinstance(result, FlowProblem) else result["status"]
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(request, range(2)))
        self.assertEqual(sorted(results), ["RATE_LIMITED", "accepted"])
        self.assertEqual(AuthChallenge.objects.count(), 1)
        self.assertEqual(DeliveryIntent.objects.count(), 1)


@override_settings(**TEST_CONFIG)
class FinalSecurityEdges(FlowFixtures, TestCase):
    def test_flow_control_or_database_digest_never_substitutes_for_email_proof(self):
        flow = self.new_flow()
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        for value in (flow["flow_control"], challenge.proof_digest):
            self.assertEqual(
                confirm_flow(
                    "registration", flow["flow_id"], value, PASSWORD, "192.0.2.2"
                ).code,
                "CHALLENGE_INVALID",
            )
        self.assertFalse(User.objects.exists())
        self.assertIsNone(AuthChallenge.objects.get(pk=flow["flow_id"]).consumed_at)

    def test_notification_or_reset_does_not_restore_or_modify_ngo_grants(self):
        from organizations.models import Organization, OrganizationAccess

        user, _ = self.account()
        organization = Organization.objects.create(
            name="Synthetic NGO", classification="registered"
        )
        grant = OrganizationAccess.objects.create(
            organization=organization, user=user, role="admin", active=False
        )
        before = list(OrganizationAccess.objects.values())
        flow = self.new_flow("reset", user.email)
        self.assertIsNone(
            confirm_flow(
                "reset", flow["flow_id"], self.proof(flow), NEW_PASSWORD, "192.0.2.2"
            )
        )
        self.assertEqual(list(OrganizationAccess.objects.values()), before)
        self.assertFalse(User.objects.get(pk=user.pk).is_staff)
        self.assertEqual(OrganizationAccess.objects.get(pk=grant.pk).user_id, user.pk)

    def test_provider_failure_after_deadline_erases_payload_immediately(self):
        flow = self.new_flow()
        deadline = AuthChallenge.objects.get(pk=flow["flow_id"]).expires_at

        def delayed_failure(*args):
            # Advance only acknowledgement time, modeling timeout past expiry.
            raise TimeoutError("Synthetic timeout")

        with patch("accounts.delivery.deliver_message", side_effect=delayed_failure):
            real_now = timezone.now()
            # claim, pre-send guard, acknowledgement
            with patch(
                "accounts.delivery.timezone.now",
                side_effect=[real_now, real_now, deadline],
            ):
                self.assertTrue(dispatch_one())
        intent = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        self.assertEqual(intent.state, "expired")
        self.assertIsNone(intent.encrypted_payload)


@override_settings(**TEST_CONFIG)
class ResendConfirmationRace(FlowFixtures, TransactionTestCase):
    def test_postgresql_resend_and_old_proof_confirmation_serialize(self):
        from threading import Barrier

        flow = self.new_flow()
        proof = self.proof(flow)
        AuthChallenge.objects.filter(pk=flow["flow_id"]).update(
            last_issued_at=timezone.now() - timedelta(seconds=61)
        )
        # Isolate flow rotation from the independently tested fixed send budget.
        AuthAbuseBucket.objects.filter(dimension="target").delete()
        barrier = Barrier(2)

        def operate(index):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                result = (
                    resend_flow(
                        "registration",
                        flow["flow_id"],
                        flow["flow_control"],
                        "192.0.2.2",
                    )
                    if index
                    else confirm_flow(
                        "registration", flow["flow_id"], proof, PASSWORD, "192.0.2.3"
                    )
                )
                return (
                    result.code if isinstance(result, FlowProblem) else result["status"]
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            confirmation, resend = list(pool.map(operate, range(2)))
        self.assertEqual(resend, "accepted")
        self.assertIn(confirmation, ["verified", "CHALLENGE_INVALID"])
        challenge = AuthChallenge.objects.get(pk=flow["flow_id"])
        if confirmation == "verified":
            self.assertEqual(challenge.generation, 1)
            self.assertEqual(User.objects.count(), 1)
        else:
            self.assertEqual(challenge.generation, 2)
            self.assertEqual(User.objects.count(), 0)
            current = DeliveryIntent.objects.get(challenge=challenge, generation=2)
            replacement = unseal(current.key_id, current.encrypted_payload)["proof"]
            self.assertEqual(
                confirm_flow(
                    "registration", flow["flow_id"], replacement, PASSWORD, "192.0.2.4"
                ),
                {"status": "verified"},
            )
