"""Synthetic MFA/assurance and real PostgreSQL races; no domain grants."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch

import pyotp
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import close_old_connections, connection
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from . import mfa
from .models import (
    User,
    AuthSession,
    AuthChallenge,
    MfaFactor,
    MfaRecoveryCode,
    AssuranceIntent,
    SecurityEvent,
    MobileCredential,
)
from .test_sessions import SessionFixtures, SESSION_CONFIG, API, NGO, OPS
from .test_registration import PASSWORD, NEW_PASSWORD
from .flow_security import new_secret

MFA_CONFIG = dict(
    SESSION_CONFIG,
    PWC_AUTH_MFA_ENABLED=True,
    PWC_AUTH_MFA_ACTIVE_KEY="test",
    PWC_AUTH_MFA_KEYS={"test": Fernet.generate_key().decode()},
    PWC_AUTH_MFA_PROOF_KEY=new_secret(),
)


class MfaFixtures(SessionFixtures):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()
        self.now = timezone.now() + timedelta(seconds=5)
        self.clock = patch("accounts.mfa.timezone.now", side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        self.auth = self.mobile(self.user)
        self.token = self.auth["access_token"]

    def call(self, path, data=None, token=None, **kwargs):
        if token is not False:
            kwargs["HTTP_AUTHORIZATION"] = "Bearer " + (token or self.token)
        return self.post_api(
            path, data or {}, client=Client(enforce_csrf_checks=True), **kwargs
        )

    def intent(self, operation, command=None, token=None):
        return self.call(
            "assurance/intents",
            {
                "operation": operation,
                "context": {"kind": "personal", "id": str(self.user.pk)},
                "command": command or {},
            },
            token=token,
        )

    def proof(self, operation, command=None, token=None, **extra):
        response = self.intent(operation, command, token)
        self.assertEqual(response.status_code, 201, response.content)
        response = self.call(
            "step-up",
            dict(intent_id=response.json()["intent_id"], password=PASSWORD, **extra),
            token=token,
        )
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()["assurance_proof"]

    def enrollment(self):
        proof = self.proof("mfa.enroll")
        response = self.call("mfa/enrollment/request", {"assurance_proof": proof})
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def activate(self):
        self.enrolled = self.enrollment()
        response = self.call(
            "mfa/enrollment/confirm",
            {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.codes = response.json()["recovery_codes"]
        return response

    def code(self, offset=0):
        return pyotp.TOTP(self.enrolled["secret"]).at(
            self.now + timedelta(seconds=offset)
        )

    def advance(self, seconds=30):
        self.now += timedelta(seconds=seconds)

    def challenge(self, user=None, client=None, host=API, web=False):
        user = user or self.user
        kwargs = {}
        if web:
            client = client or self.client
            csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=host).json()[
                "csrf_token"
            ]
            kwargs = dict(HTTP_ORIGIN="https://" + host, HTTP_X_CSRFTOKEN=csrf)
        response = self.post_api(
            "web/login" if web else "mobile/login",
            {"email": user.email, "password": PASSWORD},
            client=client or Client(),
            host=host,
            **kwargs,
        )
        self.assertEqual(response.status_code, 202, response.content)
        self.assertNotIn("access_token", response.json())
        return response.json()

    def finish(self, challenge, method="totp", code=None, **kwargs):
        return self.call(
            "mobile/mfa/confirm",
            dict(
                challenge_id=challenge["challenge_id"],
                preauth_control=challenge["preauth_control"],
                method=method,
                code=code or self.code(),
            ),
            token=False,
            **kwargs,
        )

    def held(self, state="restricted", factor=True):
        active = (
            MfaFactor.objects.filter(user=self.user, state="active").first()
            if factor
            else None
        )
        User.objects.filter(pk=self.user.pk).update(
            recovery_hold_state=state,
            hold_set_at=self.now + timedelta(microseconds=1),
            hold_reason="password_reset" if state == "restricted" else "recovery_code",
            hold_factor=active,
            hold_factor_revision=active.revision if active else None,
        )


@override_settings(**MFA_CONFIG)
class MfaTests(MfaFixtures, TestCase):
    def test_activation_encrypts_and_promotes_only_enrolling_session(self):
        other = self.mobile(self.user)
        response = self.activate()
        factor = MfaFactor.objects.get(state="active")
        self.assertNotIn(
            self.enrolled["secret"].encode(), bytes(factor.encrypted_secret)
        )
        self.assertEqual(len(self.codes), 10)
        self.assertEqual(len(set(self.codes)), 10)
        self.assertEqual(
            self.get_me(self.token).json()["session"]["assurance"]["method"], "totp"
        )
        self.assertEqual(self.get_me(other["access_token"]).status_code, 401)
        self.assertNotIn("secret", response.json())
        self.assertFalse(MfaFactor.objects.filter(state="pending").exists())

    def test_pending_is_not_mfa_and_cannot_satisfy_second_factor(self):
        self.enrolled = self.enrollment()
        self.assertEqual(
            self.get_me(self.token).json()["session"]["assurance"]["method"], "password"
        )
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email, "password": PASSWORD}
            ).status_code,
            200,
        )
        self.assertIsNone(MfaFactor.objects.get().confirmed_at)

    def test_wrong_enrollment_code_does_not_activate(self):
        self.enrolled = self.enrollment()
        for index in range(6):
            self.assertEqual(
                self.call(
                    "mfa/enrollment/confirm",
                    {"enrollment_id": self.enrolled["enrollment_id"], "code": "bad"},
                ).status_code,
                400,
            )
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            ).status_code,
            400,
        )
        self.assertFalse(MfaFactor.objects.filter(state="active").exists())

    def test_expired_enrollment(self):
        self.enrolled = self.enrollment()
        self.advance(300)
        # Expired access must be rotated without renewing session idle.
        self.token = self.refresh(self.auth["refresh_token"]).json()["access_token"]
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            ).status_code,
            400,
        )

    def test_confirmation_cannot_be_replayed(self):
        self.activate()
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            ).status_code,
            400,
        )
        self.assertEqual(MfaRecoveryCode.objects.count(), 10)

    def test_other_session_cannot_confirm_enrollment(self):
        other = self.mobile(self.user)
        self.enrolled = self.enrollment()
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
                token=other["access_token"],
            ).status_code,
            400,
        )

    def test_held_user_cannot_bootstrap_factor(self):
        self.held(factor=False)
        self.assertEqual(self.intent("mfa.enroll").status_code, 403)
        self.assertFalse(MfaFactor.objects.exists())

    def test_missing_password_and_client_mfa_flag_cannot_issue_assurance(self):
        row = self.intent("mfa.enroll").json()
        self.assertEqual(
            self.call(
                "step-up", {"intent_id": row["intent_id"], "password": "wrong"}
            ).status_code,
            400,
        )
        self.assertEqual(
            self.call(
                "step-up",
                {"intent_id": row["intent_id"], "password": PASSWORD, "mfa": "true"},
            ).status_code,
            400,
        )
        self.assertIsNone(AssuranceIntent.objects.get().proof_digest)

    def test_preauth_creates_no_authenticated_session(self):
        self.activate()
        before = AuthSession.objects.count()
        challenge = self.challenge()
        self.assertEqual(AuthSession.objects.count(), before)
        self.assertEqual(self.get_me(challenge["preauth_control"]).status_code, 401)
        self.assertFalse(
            AuthSession.objects.filter(mfa_method="", revoked_at__isnull=True).exists()
        )

    def test_totp_login_and_single_use_challenge(self):
        self.activate()
        self.advance()
        challenge = self.challenge()
        response = self.finish(challenge)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["session"]["assurance"]["method"], "totp")
        self.assertEqual(self.get_me(response.json()["access_token"]).status_code, 200)
        self.assertEqual(self.finish(challenge).status_code, 400)

    def test_timestep_cannot_be_accepted_by_another_challenge(self):
        self.activate()
        self.advance()
        first, second = self.challenge(), self.challenge()
        self.assertEqual(self.finish(first).status_code, 200)
        self.assertEqual(self.finish(second).status_code, 400)

    def test_skew_one_step_accepted_but_two_rejected(self):
        self.activate()
        self.advance(90)
        challenge = self.challenge()
        self.assertEqual(self.finish(challenge, code=self.code(60)).status_code, 400)
        self.assertEqual(self.finish(challenge, code=self.code(30)).status_code, 200)

    def test_old_timestep_and_malformed_codes_rejected(self):
        self.activate()
        self.advance(90)
        challenge = self.challenge()
        for code in (self.code(-60), "12345", "１２３４５６", "1234567"):
            self.assertEqual(self.finish(challenge, code=code).status_code, 400)

    def test_challenge_expiry(self):
        self.activate()
        challenge = self.challenge()
        self.advance(300)
        self.assertEqual(self.finish(challenge).status_code, 400)

    def test_wrong_control_does_not_spend_victim_factor(self):
        self.activate()
        challenge = self.challenge()
        challenge["preauth_control"] = new_secret()
        self.assertEqual(self.finish(challenge).status_code, 400)
        self.assertEqual(
            AuthChallenge.objects.get(purpose="preauth_mfa").failure_count, 0
        )

    def test_wrong_transport_and_method_rejected(self):
        self.activate()
        challenge = self.challenge()
        self.assertEqual(
            self.finish(challenge, HTTP_ORIGIN="https://" + NGO).status_code, 400
        )
        self.assertEqual(self.finish(challenge, method="email").status_code, 400)
        self.assertEqual(
            self.finish(challenge, HTTP_AUTHORIZATION="Bearer forged").status_code, 400
        )

    def test_recovery_login_sets_review_hold_keeps_factor_and_revokes_sessions(self):
        self.activate()
        challenge = self.challenge()
        response = self.finish(challenge, "recovery_code", self.codes[0])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["recovery_hold_state"], "review_required")
        self.assertEqual(
            response.json()["session"]["assurance"]["method"], "recovery_code"
        )
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.assertEqual(
            MfaFactor.objects.get(state="active").pk,
            uuid.UUID(self.enrolled["enrollment_id"]),
        )
        self.assertEqual(
            MfaRecoveryCode.objects.filter(consumed_at__isnull=False).count(), 1
        )

    def test_recovery_code_reuse_rejected(self):
        self.activate()
        self.assertEqual(
            self.finish(self.challenge(), "recovery_code", self.codes[0]).status_code,
            200,
        )
        self.assertEqual(
            self.finish(self.challenge(), "recovery_code", self.codes[0]).status_code,
            400,
        )

    def test_recovery_code_cannot_authenticate_as_another_user(self):
        self.activate()
        other, _ = self.account("other")
        # A foreign challenge cannot use these verifiers, even raw owner changes.
        ch = self.challenge()
        AuthChallenge.objects.filter(pk=ch["challenge_id"]).update(user=other)
        self.assertEqual(
            self.finish(ch, "recovery_code", self.codes[0]).status_code, 400
        )
        self.assertFalse(
            MfaRecoveryCode.objects.filter(consumed_at__isnull=False).exists()
        )

    def test_recovery_session_cannot_remove_enroll_clear_or_password_only_step_up(self):
        self.activate()
        data = self.finish(self.challenge(), "recovery_code", self.codes[0]).json()
        self.token = data["access_token"]
        for op in (
            "mfa.remove",
            "mfa.enroll",
            "mfa.recovery_codes.rotate",
            "recovery_hold.clear",
        ):
            self.assertEqual(self.intent(op).status_code, 403)
        row = self.intent("sessions.logout_all").json()
        self.assertEqual(
            self.call(
                "step-up", {"intent_id": row["intent_id"], "password": PASSWORD}
            ).status_code,
            403,
        )
        self.assertEqual(
            User.objects.get(pk=self.user.pk).recovery_hold_state, "review_required"
        )

    def test_recovery_rotation_revokes_old_set(self):
        self.activate()
        proof = self.proof("mfa.recovery_codes.rotate")
        result = self.call("mfa/recovery-codes/rotate", {"assurance_proof": proof})
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(len(result.json()["recovery_codes"]), 10)
        self.assertEqual(
            self.finish(self.challenge(), "recovery_code", self.codes[0]).status_code,
            400,
        )
        self.assertEqual(
            self.call(
                "mfa/recovery-codes/rotate", {"assurance_proof": proof}
            ).status_code,
            409,
        )

    def test_code_rotation_requires_totp_not_only_password(self):
        self.activate()
        self.advance(151)
        # Observation is still recent; age it without expiring mobile access.
        AuthSession.objects.filter(pk=self.auth["session"]["id"]).update(
            last_mfa_at=self.now - timedelta(minutes=6)
        )
        row = self.intent("mfa.recovery_codes.rotate").json()
        self.assertEqual(
            self.call(
                "step-up", {"intent_id": row["intent_id"], "password": PASSWORD}
            ).status_code,
            403,
        )

    def test_factor_removal_revokes_sessions_and_codes(self):
        self.activate()
        proof = self.proof("mfa.remove")
        self.assertEqual(
            self.call("mfa/remove", {"assurance_proof": proof}).status_code, 204
        )
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.assertFalse(MfaFactor.objects.filter(state="active").exists())
        self.assertFalse(
            MfaRecoveryCode.objects.filter(consumed_at__isnull=True).exists()
        )

    def test_factor_replacement_needs_old_totp_and_new_confirmation_then_relogin(self):
        self.activate()
        old = MfaFactor.objects.get(state="active")
        new = self.enrollment()
        response = self.call(
            "mfa/enrollment/confirm",
            {
                "enrollment_id": new["enrollment_id"],
                "code": pyotp.TOTP(new["secret"]).at(self.now),
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.get_me(self.token).status_code, 401)
        old.refresh_from_db()
        self.assertEqual(old.state, "revoked")
        self.assertGreater(MfaFactor.objects.get(state="active").revision, old.revision)

    def test_operation_proof_is_one_use_for_exact_target(self):
        other = self.mobile(self.user)
        command = {"session_id": other["session"]["id"]}
        proof = self.proof("sessions.revoke", command)
        path = "sessions/" + command["session_id"]
        self.assertEqual(self.call(path, {"assurance_proof": proof}).status_code, 405)

        def revoke():
            return Client().delete(
                "/api/v1/auth/" + path + "/",
                data={"assurance_proof": proof},
                content_type="application/json",
                secure=True,
                HTTP_HOST=API,
                HTTP_AUTHORIZATION="Bearer " + self.token,
            )

        self.assertEqual(revoke().status_code, 204)
        self.assertEqual(revoke().status_code, 409)
        self.assertEqual(self.get_me(other["access_token"]).status_code, 401)

    def test_cross_operation_proof_does_not_consume(self):
        proof = self.proof("mfa.enroll")
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 403
        )
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)
        self.assertEqual(
            self.call("mfa/enrollment/request", {"assurance_proof": proof}).status_code,
            201,
        )

    def test_foreign_target_denied_before_proof_consumption(self):
        proof = self.proof("sessions.logout_all")
        result = Client().delete(
            f"/api/v1/auth/sessions/{uuid.uuid4()}/",
            data={"assurance_proof": proof},
            content_type="application/json",
            secure=True,
            HTTP_HOST=API,
            HTTP_AUTHORIZATION="Bearer " + self.token,
        )
        self.assertEqual(result.status_code, 404)
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)

    def test_proof_cannot_move_to_another_session(self):
        other = self.mobile(self.user)
        proof = self.proof("sessions.logout_all")
        self.assertEqual(
            self.call(
                "logout-all", {"assurance_proof": proof}, token=other["access_token"]
            ).status_code,
            403,
        )
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)

    def test_unknown_domain_actions_and_cross_ngo_scope_default_deny(self):
        for op in ("finance.approve", "ngo.delegate", "support.elevate", "ngo.commit"):
            self.assertEqual(self.intent(op).status_code, 403)
        self.assertEqual(
            self.call(
                "assurance/intents",
                {
                    "operation": "sessions.logout_all",
                    "context": {"kind": "ngo", "id": str(uuid.uuid4())},
                    "command": {},
                },
            ).status_code,
            403,
        )
        self.assertFalse(AssuranceIntent.objects.exists())

    def test_assurance_expires_even_after_access_refresh(self):
        proof = self.proof("sessions.logout_all")
        self.advance(300)
        self.token = self.refresh(self.auth["refresh_token"]).json()["access_token"]
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 403
        )

    def test_epoch_invalidates_intents_and_preauth(self):
        self.activate()
        challenge = self.challenge()
        User.objects.filter(pk=self.user.pk).update(auth_epoch=99)
        self.assertEqual(self.finish(challenge).status_code, 400)
        self.assertEqual(self.intent("sessions.logout_all").status_code, 401)

    def test_revoked_session_cannot_issue_or_consume_proof(self):
        proof = self.proof("sessions.logout_all")
        self.call("logout")
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 401
        )
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)

    def test_infrastructure_failure_never_activates_or_downgrades(self):
        self.enrolled = self.enrollment()
        for config in (
            {"PWC_AUTH_MFA_KEYS": {}},
            {"PWC_AUTH_MFA_PROOF_KEY": ""},
            {"PWC_AUTH_MFA_ENABLED": False},
        ):
            with override_settings(**config):
                self.assertEqual(
                    self.call(
                        "mfa/enrollment/confirm",
                        {
                            "enrollment_id": self.enrolled["enrollment_id"],
                            "code": self.code(),
                        },
                    ).status_code,
                    503,
                )
        self.assertEqual(MfaFactor.objects.get().state, "pending")

    def test_tamper_and_wrong_key_fail_closed(self):
        self.activate()
        self.advance()
        challenge = self.challenge()
        with override_settings(
            PWC_AUTH_MFA_KEYS={"test": Fernet.generate_key().decode()}
        ):
            self.assertEqual(self.finish(challenge).status_code, 503)
            self.assertEqual(
                self.finish(challenge, "recovery_code", self.codes[0]).status_code, 503
            )
        self.assertIsNone(AuthChallenge.objects.get(purpose="preauth_mfa").consumed_at)

    def test_secret_ciphertext_is_bound_to_owner_and_factor(self):
        self.enrolled = self.enrollment()
        factor = MfaFactor.objects.get()
        plain = mfa.open_secret(factor)
        other, _ = self.account("other")
        factor.user = other
        with self.assertRaises(mfa.FlowProblem):
            mfa.open_secret(factor)
        self.assertEqual(plain, self.enrolled["secret"])

    def test_no_secret_in_ordinary_profile_status_or_audit(self):
        self.activate()
        challenge = self.challenge()
        me = self.get_me(self.token)
        status = Client().get(
            "/api/v1/auth/mfa/status/",
            secure=True,
            HTTP_HOST=API,
            HTTP_AUTHORIZATION="Bearer " + self.token,
        )
        ordinary = repr(
            [me.json(), status.json(), list(SecurityEvent.objects.values())]
        )
        for secret in [
            self.enrolled["secret"],
            *self.codes,
            challenge["preauth_control"],
        ]:
            self.assertNotIn(secret, ordinary)
        self.assertNotIn("code_digest", ordinary)
        self.assertEqual(
            status.json(),
            {"enabled": True, "pending": False, "recovery_hold_state": "clear"},
        )

    def test_review_hold_cannot_be_cleared_by_valid_totp(self):
        self.activate()
        self.held("review_required")
        self.assertEqual(self.intent("recovery_hold.clear").status_code, 403)
        self.assertEqual(
            User.objects.get(pk=self.user.pk).recovery_hold_state, "review_required"
        )

    def test_restricted_hold_without_prehold_factor_cannot_clear(self):
        self.activate()
        self.held(factor=False)
        self.assertEqual(self.intent("recovery_hold.clear").status_code, 403)

    def test_restricted_hold_clear_uses_same_prehold_factor_and_audit(self):
        self.activate()
        self.advance()
        self.held()
        self.advance()
        row = self.intent("recovery_hold.clear").json()
        response = self.call(
            "recovery-hold/clear",
            {
                "intent_id": row["intent_id"],
                "password": PASSWORD,
                "totp_code": self.code(),
            },
        )
        self.assertEqual(response.status_code, 204, response.content)
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.recovery_hold_state, "clear")
        self.assertIsNotNone(user.hold_cleared_event_id)

    def test_password_reset_retains_factor_and_hold(self):
        from .registration import request_flow, confirm_flow
        from .test_registration import FlowFixtures

        self.activate()
        factor = MfaFactor.objects.get(state="active")
        data = request_flow("reset", self.user.email, "192.0.2.88")
        proof = FlowFixtures.proof(self, data)
        result = confirm_flow(
            "reset", data["flow_id"], proof, NEW_PASSWORD, "192.0.2.88"
        )
        self.assertIsNone(result)
        factor.refresh_from_db()
        self.assertEqual(factor.state, "active")
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.recovery_hold_state, "restricted")
        self.assertEqual(user.hold_factor_id, factor.pk)

    def test_browser_preauth_requires_same_cookie_csrf_and_portal(self):
        self.activate()
        self.advance()
        client = Client(enforce_csrf_checks=True)
        challenge = self.challenge(client=client, host=NGO, web=True)
        data = dict(
            challenge_id=challenge["challenge_id"],
            preauth_control=challenge["preauth_control"],
            method="totp",
            code=self.code(),
        )
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)
        self.assertEqual(
            self.post_api("web/mfa/confirm", data, client=client, host=NGO).status_code,
            403,
        )
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        response = self.post_api(
            "web/mfa/confirm",
            data,
            client=client,
            host=NGO,
            HTTP_ORIGIN="https://" + NGO,
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn("access_token", response.json())
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)

    def test_browser_challenge_not_usable_in_native_flow(self):
        self.activate()
        self.advance()
        challenge = self.challenge(client=Client(), host=NGO, web=True)
        self.assertEqual(self.finish(challenge).status_code, 400)

    def test_intent_scope_cannot_be_reassigned_by_raw_orm(self):
        proof = self.proof("mfa.enroll")
        other = self.intent("sessions.logout_all").json()
        old = AssuranceIntent.objects.exclude(pk=other["intent_id"]).get()
        replacement = AssuranceIntent.objects.get(pk=other["intent_id"])
        AssuranceIntent.objects.filter(pk=old.pk).update(
            operation=replacement.operation, request_digest=replacement.request_digest
        )
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 403
        )

    def test_wrong_user_cannot_confirm_or_step_up_owned_records(self):
        self.enrolled = self.enrollment()
        other, _ = self.account("other")
        token = self.mobile(other)["access_token"]
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
                token=token,
            ).status_code,
            400,
        )
        row = self.intent("sessions.logout_all").json()
        self.assertEqual(
            self.call(
                "step-up",
                {"intent_id": row["intent_id"], "password": PASSWORD},
                token=token,
            ).status_code,
            400,
        )

    def test_totp_attempt_limit_is_shared_across_login_challenges(self):
        self.activate()
        self.advance()
        first, second = self.challenge(), self.challenge()
        for _ in range(5):
            self.assertEqual(self.finish(first, code="invalid").status_code, 400)
        self.assertEqual(self.finish(second).status_code, 400)
        self.advance(301)
        self.assertEqual(self.finish(self.challenge()).status_code, 200)

    def test_intent_confirmation_is_once_only_even_with_recent_totp(self):
        self.activate()
        row = self.intent("sessions.logout_all").json()
        data = {"intent_id": row["intent_id"], "password": PASSWORD}
        first = self.call("step-up", data)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.call("step-up", data).status_code, 400)
        self.assertEqual(
            self.call(
                "logout-all", {"assurance_proof": first.json()["assurance_proof"]}
            ).status_code,
            204,
        )
        self.assertEqual(self.get_me(self.token).status_code, 401)

    def test_hold_generation_change_invalidates_previously_issued_proof(self):
        proof = self.proof("sessions.logout_all")
        User.objects.filter(pk=self.user.pk).update(recovery_generation=50)
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 403
        )

    def test_held_user_cannot_consume_prehold_enrollment_proof(self):
        proof = self.proof("mfa.enroll")
        self.held(factor=False)
        self.assertEqual(
            self.call("mfa/enrollment/request", {"assurance_proof": proof}).status_code,
            403,
        )
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)

    def test_moved_preauth_scope_cannot_complete_under_another_portal(self):
        self.activate()
        self.advance()
        client = Client(enforce_csrf_checks=True)
        challenge = self.challenge(client=client, host=NGO, web=True)
        AuthChallenge.objects.filter(pk=challenge["challenge_id"]).update(
            portal="pwc_ops"
        )
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=OPS).json()[
            "csrf_token"
        ]
        response = self.post_api(
            "web/mfa/confirm",
            dict(
                challenge_id=challenge["challenge_id"],
                preauth_control=challenge["preauth_control"],
                method="totp",
                code=self.code(),
            ),
            client=client,
            host=OPS,
            HTTP_ORIGIN="https://" + OPS,
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 400)

    def test_browser_preauth_cannot_be_completed_by_cookie_copy_without_control(self):
        self.activate()
        self.advance()
        client = Client(enforce_csrf_checks=True)
        challenge = self.challenge(client=client, host=NGO, web=True)
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        response = self.post_api(
            "web/mfa/confirm",
            dict(
                challenge_id=challenge["challenge_id"],
                preauth_control=new_secret(),
                method="totp",
                code=self.code(),
            ),
            client=client,
            host=NGO,
            HTTP_ORIGIN="https://" + NGO,
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(response.status_code, 400)

    def test_browser_new_preauth_does_not_preserve_old_authenticated_principal(self):
        client, _ = self.web(self.user)
        self.activate()
        self.advance()
        # Another user logs into this browser while original user had a cookie.
        challenge = self.challenge(client=client, host=NGO, web=True)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)
        self.assertNotIn("access_token", challenge)

    def test_key_rotation_reads_old_factor_key_without_plaintext_fallback(self):
        self.activate()
        self.advance()
        challenge = self.challenge()
        with override_settings(
            PWC_AUTH_MFA_ACTIVE_KEY="new",
            PWC_AUTH_MFA_KEYS={
                **settings.PWC_AUTH_MFA_KEYS,
                "new": Fernet.generate_key().decode(),
            },
        ):
            self.assertEqual(self.finish(challenge).status_code, 200)

    def test_database_and_key_errors_have_no_secret_in_log_messages(self):
        self.activate()
        self.advance()
        challenge = self.challenge()
        with override_settings(
            PWC_AUTH_MFA_KEYS={"test": Fernet.generate_key().decode()}
        ), self.assertLogs("django.request", level="ERROR") as logs:
            result = self.finish(challenge)
        self.assertEqual(result.status_code, 503)
        rendered = " ".join(logs.output) + result.content.decode()
        for secret in (
            self.enrolled["secret"],
            challenge["preauth_control"],
            self.code(),
        ):
            self.assertNotIn(secret, rendered)

    def test_logout_all_denies_forged_proof_without_state_change(self):
        self.assertEqual(
            self.call(
                "logout-all", {"assurance_proof": uuid.uuid4().hex + "." + new_secret()}
            ).status_code,
            403,
        )
        self.assertEqual(self.get_me(self.token).status_code, 200)
        self.assertEqual(User.objects.get(pk=self.user.pk).auth_epoch, 1)

    def test_mfa_proof_expiry_cannot_be_extended_by_editing_timestamp(self):
        proof = self.proof("sessions.logout_all")
        AssuranceIntent.objects.update(expires_at=self.now + timedelta(minutes=10))
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 403
        )

    def test_challenge_password_hash_binding_rejects_unsafe_password_replacement(self):
        self.activate()
        self.advance()
        challenge = self.challenge()
        user = User.objects.get(pk=self.user.pk)
        user.set_password(NEW_PASSWORD)
        user.save(update_fields=["password"])
        self.assertEqual(self.finish(challenge).status_code, 400)

    def test_step_up_cannot_renew_already_expired_idle_session(self):
        proof = self.proof("sessions.logout_all")
        AuthSession.objects.filter(pk=self.auth["session"]["id"]).update(
            last_interactive_at=self.now - timedelta(days=7),
            created_at=self.now - timedelta(days=8),
        )
        self.assertEqual(
            self.call("logout-all", {"assurance_proof": proof}).status_code, 401
        )


@override_settings(**MFA_CONFIG)
class MfaRaces(MfaFixtures, TransactionTestCase):
    def race(self, *functions):
        self.assertEqual(connection.vendor, "postgresql")
        barrier = Barrier(len(functions))

        def execute(fn):
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return fn()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(functions)) as pool:
            results = list(pool.map(execute, functions))
        return results

    def test_competing_enrollment_confirmation_activates_once(self):
        self.enrolled = self.enrollment()

        def confirm():
            return self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            ).status_code

        self.assertEqual(sorted(self.race(confirm, confirm)), [200, 400])
        self.assertEqual(MfaFactor.objects.filter(state="active").count(), 1)
        self.assertEqual(MfaRecoveryCode.objects.count(), 10)

    def test_competing_totp_timesteps_issue_one_session(self):
        self.activate()
        self.advance()
        first, second = self.challenge(), self.challenge()
        self.assertEqual(
            sorted(
                self.race(
                    lambda: self.finish(first).status_code,
                    lambda: self.finish(second).status_code,
                )
            ),
            [200, 400],
        )
        self.assertEqual(AuthSession.objects.filter(revoked_at__isnull=True).count(), 2)

    def test_concurrent_recovery_code_use_consumed_once(self):
        self.activate()
        first, second = self.challenge(), self.challenge()
        self.assertEqual(
            sorted(
                self.race(
                    lambda: self.finish(
                        first, "recovery_code", self.codes[0]
                    ).status_code,
                    lambda: self.finish(
                        second, "recovery_code", self.codes[0]
                    ).status_code,
                )
            ),
            [200, 400],
        )
        self.assertEqual(
            MfaRecoveryCode.objects.filter(consumed_at__isnull=False).count(), 1
        )
        self.assertEqual(AuthSession.objects.filter(revoked_at__isnull=True).count(), 1)
        self.assertEqual(
            User.objects.get(pk=self.user.pk).recovery_hold_state, "review_required"
        )

    def test_operation_proof_racing_consumption_performs_one_action(self):
        other = self.mobile(self.user)
        command = {"session_id": other["session"]["id"]}
        proof = self.proof("sessions.revoke", command)

        def revoke():
            return (
                Client()
                .delete(
                    f'/api/v1/auth/sessions/{command["session_id"]}/',
                    data={"assurance_proof": proof},
                    content_type="application/json",
                    secure=True,
                    HTTP_HOST=API,
                    HTTP_AUTHORIZATION="Bearer " + self.token,
                )
                .status_code
            )

        self.assertEqual(sorted(self.race(revoke, revoke)), [204, 409])
        self.assertEqual(
            SecurityEvent.objects.filter(event="auth.session_revoked").count(), 1
        )

    def test_suspension_racing_mfa_completion_leaves_no_live_credentials(self):
        self.activate()
        self.advance()
        challenge = self.challenge()

        def suspend():
            mfa.sessions.suspend_account(self.user.pk)
            return None

        results = self.race(lambda: self.finish(challenge), suspend)
        response = results[0]
        self.assertIn(response.status_code, (200, 400))
        if response.status_code == 200:
            self.assertEqual(
                self.get_me(response.json()["access_token"]).status_code, 401
            )
        self.assertFalse(AuthSession.objects.filter(revoked_at__isnull=True).exists())

    def test_factor_replacement_racing_refresh_cannot_leave_old_family_live(self):
        self.activate()
        self.advance()
        other = self.finish(self.challenge()).json()
        new = self.enrollment()

        def replace():
            return self.call(
                "mfa/enrollment/confirm",
                {
                    "enrollment_id": new["enrollment_id"],
                    "code": pyotp.TOTP(new["secret"]).at(self.now),
                },
            )

        results = self.race(replace, lambda: self.refresh(other["refresh_token"]))
        self.assertEqual(results[0].status_code, 200, results[0].content)
        self.assertIn(results[1].status_code, (200, 401))
        self.assertEqual(self.get_me(self.token).status_code, 401)
        if results[1].status_code == 200:
            self.assertEqual(
                self.get_me(results[1].json()["access_token"]).status_code, 401
            )

    def test_reset_racing_mfa_completion_preserves_factor_and_invalidates_all_sessions(
        self,
    ):
        from .registration import request_flow, confirm_flow
        from .test_registration import FlowFixtures

        self.activate()
        self.advance()
        challenge = self.challenge()
        flow = request_flow("reset", self.user.email, "192.0.2.77")
        proof = FlowFixtures.proof(self, flow)
        result = self.race(
            lambda: self.finish(challenge),
            lambda: confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.77"
            ),
        )
        self.assertIsNone(result[1])
        self.assertIn(result[0].status_code, (200, 400))
        self.assertEqual(MfaFactor.objects.filter(state="active").count(), 1)
        self.assertFalse(AuthSession.objects.filter(revoked_at__isnull=True).exists())
        self.assertEqual(
            User.objects.get(pk=self.user.pk).recovery_hold_state, "restricted"
        )


@override_settings(**MFA_CONFIG)
class MfaContractTests(MfaFixtures, TestCase):
    def test_machine_readable_fixture_matches_enabled_wire_contract(self):
        import json
        from pathlib import Path

        fixture = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "packages/api-contracts/auth-mfa-v1.fixtures.json"
            ).read_text()
        )
        row = self.intent("mfa.enroll")
        self.assertEqual(set(row.json()), set(fixture["intent_keys"]))
        proof = self.call(
            "step-up", {"intent_id": row.json()["intent_id"], "password": PASSWORD}
        )
        self.assertEqual(set(proof.json()), set(fixture["step_up_keys"]))
        enrolled = self.call(
            "mfa/enrollment/request",
            {"assurance_proof": proof.json()["assurance_proof"]},
        )
        self.assertEqual(set(enrolled.json()), set(fixture["enrollment_keys"]))
        self.enrolled = enrolled.json()
        result = self.call(
            "mfa/enrollment/confirm",
            {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
        )
        self.assertEqual(set(result.json()), set(fixture["activation_keys"]))
        self.assertEqual(
            len(result.json()["recovery_codes"]), fixture["recovery_code_count"]
        )
        response = self.challenge()
        self.assertEqual(set(response), set(fixture["preauth_keys"]))
        self.assertEqual(response["expires_in"], fixture["maximum_lifetime_seconds"])


@override_settings(**MFA_CONFIG)
class MfaOwnershipTests(MfaFixtures, TestCase):
    def test_factor_with_foreign_enrollment_session_fails_closed(self):
        other, _ = self.account("other")
        other_data = self.mobile(other)
        self.activate()
        MfaFactor.objects.filter(user=self.user, state="active").update(
            enrollment_session_id=other_data["session"]["id"]
        )
        self.assertEqual(self.get_me(self.token).status_code, 401)
        response = self.post_api(
            "mobile/login", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(AuthChallenge.objects.filter(purpose="preauth_mfa").exists())

    def test_security_services_reject_cross_owner_rows_without_full_clean(self):
        self.activate()
        other, _ = self.account("other")
        factor = MfaFactor.objects.get(user=self.user, state="active")
        with self.assertRaises(mfa.FlowProblem):
            mfa.codes(other, factor)
        session = AuthSession.objects.get(pk=self.auth["session"]["id"])
        result = mfa.intent_request(
            other,
            session,
            {
                "operation": "sessions.logout_all",
                "context": {"kind": "personal", "id": str(other.pk)},
                "command": {},
            },
        )
        self.assertEqual(result.code, "SESSION_INVALID")
        self.assertEqual(
            MfaRecoveryCode.objects.filter(consumed_at__isnull=True).count(), 10
        )


@override_settings(**MFA_CONFIG)
class MfaContactBindingTests(MfaFixtures, TestCase):
    def test_retired_first_factor_contact_cannot_complete_preauth_even_without_epoch_hook(
        self,
    ):
        from .models import UserContact

        self.activate()
        self.advance()
        challenge = self.challenge()
        old = UserContact.objects.get(user=self.user, is_primary=True)
        UserContact.objects.filter(pk=old.pk).update(
            is_primary=False, retired_at=self.now
        )
        UserContact.objects.create(
            user=self.user,
            kind="email",
            display_value=old.display_value,
            normalized_value=old.normalized_value,
            is_primary=True,
            verified_at=self.now,
        )
        self.assertEqual(self.finish(challenge).status_code, 400)

    def test_changed_contact_value_invalidates_original_first_factor_binding(self):
        from .models import UserContact

        self.activate()
        self.advance()
        challenge = self.challenge()
        UserContact.objects.filter(user=self.user, is_primary=True).update(
            normalized_value="changed@example.invalid",
            display_value="changed@example.invalid",
        )
        self.assertEqual(self.finish(challenge).status_code, 400)


@override_settings(**MFA_CONFIG)
class RecoveredMfaRegressionTests(MfaFixtures, TestCase):
    def test_access_expiring_during_factor_confirmation_cannot_commit_activation(self):
        self.advance(240)
        self.enrolled = self.enrollment()
        deadline = MobileCredential.objects.get(
            kind="access", session_id=self.auth["session"]["id"]
        ).expires_at
        original = mfa.verify_totp

        def delayed(factor, code):
            valid = original(factor, code)
            self.now = deadline
            return valid

        with patch("accounts.mfa.verify_totp", side_effect=delayed):
            result = self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            )
        self.assertEqual(result.status_code, 401)
        self.assertEqual(MfaFactor.objects.get().state, "pending")
        self.assertFalse(MfaRecoveryCode.objects.exists())
        self.assertEqual(User.objects.get(pk=self.user.pk).auth_epoch, 1)
        # No partial state: a fresh access credential can complete the still-live enrollment.
        self.token = self.refresh(self.auth["refresh_token"]).json()["access_token"]
        self.assertEqual(
            self.call(
                "mfa/enrollment/confirm",
                {"enrollment_id": self.enrolled["enrollment_id"], "code": self.code()},
            ).status_code,
            200,
        )

    def test_migration_field_definition_does_not_call_mutable_model_helpers(self):
        import importlib

        with patch(
            "accounts.security_models.digest",
            side_effect=AssertionError("historical field depends on live helper"),
        ):
            module = importlib.reload(
                importlib.import_module("accounts.migrations.0005_mfa_preauth_binding")
            )
        self.assertEqual(
            module.Migration.operations[0].field.deconstruct()[1:],
            AuthChallenge._meta.get_field("client_digest").deconstruct()[1:],
        )

    def test_access_expiring_during_step_up_rolls_back_proof_and_activity(self):
        self.advance(240)
        intent = self.intent("sessions.logout_all").json()
        original = mfa.check_password
        deadline = MobileCredential.objects.get(
            kind="access", session_id=self.auth["session"]["id"]
        ).expires_at
        before = AuthSession.objects.get(
            pk=self.auth["session"]["id"]
        ).last_interactive_at

        def delayed(*args, **kwargs):
            valid = original(*args, **kwargs)
            self.now = deadline
            return valid

        with patch("accounts.mfa.check_password", side_effect=delayed):
            result = self.call(
                "step-up", {"intent_id": intent["intent_id"], "password": PASSWORD}
            )
        self.assertEqual(result.status_code, 401)
        self.assertIsNone(
            AssuranceIntent.objects.get(pk=intent["intent_id"]).proof_digest
        )
        self.assertEqual(
            AuthSession.objects.get(pk=self.auth["session"]["id"]).last_interactive_at,
            before,
        )

    def test_access_expiring_during_assured_logout_all_cannot_commit_revocation(self):
        self.advance(240)
        proof = self.proof("sessions.logout_all")
        deadline = MobileCredential.objects.get(
            kind="access", session_id=self.auth["session"]["id"]
        ).expires_at
        original = mfa.consume

        def delayed(*args, **kwargs):
            result = original(*args, **kwargs)
            self.now = deadline
            return result

        with patch("accounts.mfa.consume", side_effect=delayed):
            result = self.call("logout-all", {"assurance_proof": proof})
        self.assertEqual(result.status_code, 401)
        self.assertEqual(User.objects.get(pk=self.user.pk).auth_epoch, 1)
        self.assertIsNone(AssuranceIntent.objects.get().consumed_at)
        self.assertIsNone(
            AuthSession.objects.get(pk=self.auth["session"]["id"]).revoked_at
        )
