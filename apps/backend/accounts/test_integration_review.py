"""Cross-module synthetic acceptance and regressions from the 03A review."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from django.conf import settings
from django.contrib.sessions.models import Session as DjangoSession
from django.core import mail
from django.db import DatabaseError, close_old_connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone

from . import mfa, sessions
from .delivery import dispatch_one
from .flow_security import unseal
from .registration import request_flow, confirm_flow
from .models import (
    AssuranceIntent,
    AuthAbuseBucket,
    AuthChallenge,
    AuthSession,
    SecurityEvent,
    User,
    UserContact,
)
from .test_mfa import MFA_CONFIG, MfaFixtures
from .test_registration import PASSWORD, NEW_PASSWORD
from .test_sessions import API, NGO


class WebReviewFixtures(MfaFixtures):
    def web_command(self, client, path, data):
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        return self.post_api(
            path,
            data,
            client=client,
            host=NGO,
            HTTP_ORIGIN="https://" + NGO,
            HTTP_X_CSRFTOKEN=csrf,
        )

    def web_intent(self, client, operation="mfa.enroll"):
        response = self.web_command(
            client,
            "assurance/intents",
            {
                "operation": operation,
                "context": {"kind": "personal", "id": str(self.user.pk)},
                "command": {},
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()["intent_id"]


@override_settings(**MFA_CONFIG)
class IntegrationReviewRegressions(WebReviewFixtures, TestCase):
    def test_successful_web_step_up_rotates_cookie_registry_and_csrf(self):
        client, auth = self.web(self.user)
        old_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        old_csrf = client.cookies[settings.CSRF_COOKIE_NAME].value
        copied = Client()
        copied.cookies[settings.SESSION_COOKIE_NAME] = old_key
        intent = self.web_intent(client)
        response = self.web_command(
            client, "step-up", {"intent_id": intent, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 200)
        new_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertTrue(new_key != old_key)
        self.assertTrue(client.cookies[settings.CSRF_COOKIE_NAME].value != old_csrf)
        session = AuthSession.objects.get(pk=auth.json()["session"]["id"])
        self.assertEqual(session.web_key_digest, sessions.web_digest(new_key))
        self.assertFalse(DjangoSession.objects.filter(session_key=old_key).exists())
        self.assertEqual(self.get_me(client=copied, host=NGO).status_code, 401)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)
        # Stable logical session binding: rotation must not strand its proof.
        used = self.web_command(
            client,
            "mfa/enrollment/request",
            {
                "assurance_proof": response.json()["assurance_proof"],
            },
        )
        self.assertEqual(used.status_code, 201)

    def test_failed_web_step_up_does_not_rotate_cookie(self):
        client, _ = self.web(self.user)
        old_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        intent = self.web_intent(client)
        response = self.web_command(
            client, "step-up", {"intent_id": intent, "password": "wrong"}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(client.cookies[settings.SESSION_COOKIE_NAME].value, old_key)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)

    def test_rotation_expiry_rolls_back_assurance_and_registry(self):
        client, auth = self.web(self.user)
        old_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        intent = self.web_intent(client)
        deadline = self.now + timedelta(seconds=1)
        AuthSession.objects.filter(pk=auth.json()["session"]["id"]).update(
            absolute_expires_at=deadline
        )
        original = sessions.web_digest

        def expire_during_rotation(key):
            if key != old_key:
                self.now = deadline
            return original(key)

        with patch("accounts.sessions.web_digest", side_effect=expire_during_rotation):
            response = self.web_command(
                client, "step-up", {"intent_id": intent, "password": PASSWORD}
            )
        self.assertEqual(
            response.status_code, 401, response.json().get("error", {}).get("code")
        )
        row = AssuranceIntent.objects.get(pk=intent)
        self.assertIsNone(row.proof_digest)
        self.assertFalse(
            SecurityEvent.objects.filter(event="auth.step_up_completed").exists()
        )
        self.assertEqual(
            AuthSession.objects.get(pk=auth.json()["session"]["id"]).web_key_digest,
            original(old_key),
        )
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)

    def test_hold_clear_cannot_reuse_recent_totp_without_a_new_code(self):
        self.activate()
        self.advance()
        self.held()
        self.advance()
        # Recent TOTP is deliberately available, but predates the hold.
        self.assertTrue(
            mfa.recent(
                AuthSession.objects.get(pk=self.auth["session"]["id"]),
                mfa.active(self.user),
            )
        )
        for path, code in (
            ("step-up", ""),
            ("step-up", None),
            ("recovery-hold/clear", ""),
        ):
            intent = self.intent("recovery_hold.clear").json()["intent_id"]
            response = self.call(
                path, {"intent_id": intent, "password": PASSWORD, "totp_code": ""}
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "RECOVERY_RESTRICTED")
            self.assertIsNone(AssuranceIntent.objects.get(pk=intent).proof_digest)
        self.assertEqual(
            User.objects.get(pk=self.user.pk).recovery_hold_state, "restricted"
        )
        self.assertFalse(
            SecurityEvent.objects.filter(event="auth.recovery_hold_cleared").exists()
        )
        self.assertEqual(
            SecurityEvent.objects.filter(
                event="auth.recovery_hold_denied",
                subject=self.user,
                previous_hold_state="restricted",
                new_hold_state="restricted",
            ).count(),
            3,
        )

    def test_hold_clear_requires_fresh_code_even_after_mfa_login(self):
        self.activate()
        self.advance()
        self.held()
        self.advance()
        auth = self.finish(self.challenge()).json()
        intent = self.intent("recovery_hold.clear", token=auth["access_token"]).json()[
            "intent_id"
        ]
        empty = self.call(
            "recovery-hold/clear",
            {"intent_id": intent, "password": PASSWORD, "totp_code": ""},
            token=auth["access_token"],
        )
        self.assertEqual(empty.status_code, 403)
        self.advance()
        cleared = self.call(
            "recovery-hold/clear",
            {"intent_id": intent, "password": PASSWORD, "totp_code": self.code()},
            token=auth["access_token"],
        )
        self.assertEqual(cleared.status_code, 204)
        self.assertEqual(User.objects.get(pk=self.user.pk).recovery_hold_state, "clear")

    def test_rotation_database_failure_restores_request_store_and_old_mapping(self):
        client, auth = self.web(self.user)
        old_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        intent = self.web_intent(client)
        original = AuthSession.save

        def fail_mapping_save(row, *args, **kwargs):
            if kwargs.get("update_fields") == ["web_key_digest"]:
                raise DatabaseError("synthetic mapping failure")
            return original(row, *args, **kwargs)

        with patch.object(AuthSession, "save", new=fail_mapping_save):
            response = self.web_command(
                client, "step-up", {"intent_id": intent, "password": PASSWORD}
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "AUTH_UNAVAILABLE")
        self.assertEqual(client.cookies[settings.SESSION_COOKIE_NAME].value, old_key)
        self.assertIsNone(AssuranceIntent.objects.get(pk=intent).proof_digest)
        self.assertEqual(
            AuthSession.objects.get(pk=auth.json()["session"]["id"]).web_key_digest,
            sessions.web_digest(old_key),
        )
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)

    def test_web_hold_clear_rotates_cookie_without_granting_domain_authority(self):
        self.activate()
        self.advance()
        self.held()
        self.advance()
        client = Client(enforce_csrf_checks=True)
        challenge = self.challenge(client=client, web=True, host=NGO)
        login = self.web_command(
            client,
            "web/mfa/confirm",
            {
                **{key: challenge[key] for key in ("challenge_id", "preauth_control")},
                "method": "totp",
                "code": self.code(),
            },
        )
        self.assertEqual(login.status_code, 200)
        old_key = client.cookies[settings.SESSION_COOKIE_NAME].value
        copied = Client()
        copied.cookies[settings.SESSION_COOKIE_NAME] = old_key
        self.advance()
        intent = self.web_intent(client, "recovery_hold.clear")
        cleared = self.web_command(
            client,
            "recovery-hold/clear",
            {
                "intent_id": intent,
                "password": PASSWORD,
                "totp_code": self.code(),
            },
        )
        self.assertEqual(cleared.status_code, 204)
        self.assertTrue(client.cookies[settings.SESSION_COOKIE_NAME].value != old_key)
        self.assertEqual(self.get_me(client=copied, host=NGO).status_code, 401)
        self.assertEqual(
            self.get_me(client=client, host=NGO).json()["recovery_hold_state"], "clear"
        )
        self.assertFalse(self.user.organizationaccess_set.exists())

    def test_every_auth_route_has_405_envelope_and_explicit_allow(self):
        from .registration_urls import urlpatterns

        before = AuthAbuseBucket.objects.count()
        for route in urlpatterns:
            path = str(route.pattern).replace(
                "<str:session_id>", "00000000-0000-0000-0000-000000000001"
            )
            expected = (
                "GET"
                if path in ("csrf/", "me/", "sessions/", "mfa/status/")
                else ("DELETE" if path.startswith("sessions/") else "POST")
            )
            with self.subTest(path=path):
                response = Client().put(
                    "/api/v1/auth/" + path,
                    data={},
                    content_type="application/json",
                    secure=True,
                )
                self.assertEqual(response.status_code, 405)
                self.assertEqual(response["Allow"], expected)
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertEqual(response.json()["error"]["code"], "METHOD_NOT_ALLOWED")
        self.assertEqual(AuthAbuseBucket.objects.count(), before)

    def test_public_proof_commands_reject_unapproved_proxy_trust(self):
        before = AuthChallenge.objects.count()
        for config in (
            {"SECURE_PROXY_SSL_HEADER": ("HTTP_X_FORWARDED_PROTO", "https")},
            {"USE_X_FORWARDED_HOST": True},
            {"USE_X_FORWARDED_PORT": True},
        ):
            with self.subTest(config=config), override_settings(**config):
                response = self.post_api(
                    "registration/request",
                    {"email": "proxy@example.invalid"},
                    client=Client(),
                )
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["error"]["code"], "AUTH_UNAVAILABLE")
        self.assertEqual(AuthChallenge.objects.count(), before)

    def test_all_public_commands_reject_http_before_work(self):
        before = (
            AuthChallenge.objects.count(),
            AuthAbuseBucket.objects.count(),
            User.objects.count(),
        )
        for prefix in ("registration", "password-reset"):
            for command in ("request", "resend", "confirm"):
                response = Client().post(
                    f"/api/v1/auth/{prefix}/{command}/",
                    data={
                        "request": {"email": "http@example.invalid"},
                        "resend": {"flow_id": "invalid", "flow_control": "invalid"},
                        "confirm": {
                            "flow_id": "invalid",
                            "proof": "invalid",
                            (
                                "password"
                                if prefix == "registration"
                                else "new_password"
                            ): PASSWORD,
                        },
                    }[command],
                    content_type="application/json",
                    HTTP_X_FORWARDED_PROTO="https",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "TRANSPORT_NOT_ALLOWED"
                )
                self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            before,
            (
                AuthChallenge.objects.count(),
                AuthAbuseBucket.objects.count(),
                User.objects.count(),
            ),
        )


@override_settings(**MFA_CONFIG)
class AuthenticationJourneys(MfaFixtures, TestCase):
    """Every journey starts through public registration, worker and login APIs."""

    def account(self, name="journey", **unused):
        email = f"{name}@example.invalid"
        count = User.objects.count()
        response = self.post_api(
            "registration/request", {"email": email.upper()}, client=Client()
        )
        self.assertEqual(response.status_code, 202)
        flow = response.json()
        self.assertEqual(User.objects.count(), count)
        self.assertTrue(dispatch_one())
        link = next(
            message.body.splitlines()[1]
            for message in mail.outbox
            if flow["flow_id"] in message.body
        )
        proof = parse_qs(urlsplit(link).fragment)["proof"][0]
        self.assertEqual(urlsplit(link).query, "")
        response = self.post_api(
            "registration/confirm",
            {
                "flow_id": flow["flow_id"],
                "proof": proof,
                "password": PASSWORD,
            },
            client=Client(),
        )
        self.assertEqual(response.status_code, 201)
        self.assertNotIn(settings.SESSION_COOKIE_NAME, response.cookies)
        user = User.objects.get(email=email)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.organizationaccess_set.exists())
        return user, UserContact.objects.get(user=user, is_primary=True)

    def reset_via_api(self):
        self.advance(61)  # shared registration/reset delivery cooldown, not bypassed
        response = self.post_api(
            "password-reset/request", {"email": self.user.email}, client=Client()
        )
        self.assertEqual(response.status_code, 202)
        flow = response.json()
        self.assertTrue(dispatch_one())
        link = next(
            message.body.splitlines()[1]
            for message in mail.outbox
            if flow["flow_id"] in message.body
        )
        proof = parse_qs(urlsplit(link).fragment)["proof"][0]
        response = self.post_api(
            "password-reset/confirm",
            {
                "flow_id": flow["flow_id"],
                "proof": proof,
                "new_password": NEW_PASSWORD,
            },
            client=Client(),
        )
        self.assertEqual(response.status_code, 204)

    def test_registration_login_mfa_reset_revokes_both_transports_and_refresh(self):
        browser, _ = self.web(self.user)
        self.activate()
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        self.advance()
        browser = Client(enforce_csrf_checks=True)
        challenge = self.challenge(client=browser, web=True, host=NGO)
        csrf = browser.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        completed = self.post_api(
            "web/mfa/confirm",
            {
                **{key: challenge[key] for key in ("challenge_id", "preauth_control")},
                "method": "totp",
                "code": self.code(),
            },
            client=browser,
            host=NGO,
            HTTP_ORIGIN="https://" + NGO,
            HTTP_X_CSRFTOKEN=csrf,
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 200)
        self.reset_via_api()
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertEqual(user.recovery_hold_state, "restricted")
        self.assertIsNotNone(mfa.active(user))
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        self.assertEqual(self.refresh(self.auth["refresh_token"]).status_code, 401)
        challenge = self.post_api(
            "mobile/login",
            {"email": user.email, "password": NEW_PASSWORD},
            client=Client(),
        )
        self.assertEqual(challenge.status_code, 202)
        self.assertNotIn("access_token", challenge.json())
        logged_in = self.finish(challenge.json())
        self.assertEqual(logged_in.status_code, 200)
        self.assertEqual(logged_in.json()["recovery_hold_state"], "restricted")
        denied = self.intent("mfa.enroll", token=logged_in.json()["access_token"])
        self.assertEqual(denied.status_code, 403)

    def test_recovery_code_login_then_reset_preserves_review_hold(self):
        self.activate()
        self.advance()
        recovered = self.finish(
            self.challenge(), method="recovery_code", code=self.codes[0]
        )
        self.assertEqual(recovered.status_code, 200)
        recovered_token = recovered.json()["access_token"]
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.reset_via_api()
        user = User.objects.get(pk=self.user.pk)
        self.assertEqual(user.recovery_hold_state, "review_required")
        self.assertIsNotNone(mfa.active(user))
        self.assertEqual(self.get_me(recovered_token).status_code, 401)
        self.assertFalse(user.organizationaccess_set.exists())

    def test_suspension_blocks_cookie_access_and_refresh_after_registration(self):
        browser, _ = self.web(self.user)
        sessions.suspend_account(self.user.pk)
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        self.assertEqual(self.refresh(self.auth["refresh_token"]).status_code, 401)
        response = self.post_api(
            "mobile/login",
            {"email": self.user.email, "password": PASSWORD},
            client=Client(),
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "INVALID_CREDENTIALS")

    def test_mobile_refresh_rotation_and_replay_does_not_revoke_other_family(self):
        other = self.mobile(self.user)
        refreshed = self.refresh(self.auth["refresh_token"])
        self.assertEqual(refreshed.status_code, 200)
        self.assertEqual(self.get_me(self.token).status_code, 401)
        self.assertEqual(self.get_me(refreshed.json()["access_token"]).status_code, 200)
        self.assertEqual(self.refresh(self.auth["refresh_token"]).status_code, 401)
        self.assertEqual(self.get_me(refreshed.json()["access_token"]).status_code, 401)
        self.assertEqual(self.get_me(other["access_token"]).status_code, 200)

    def test_assurance_never_maps_ngo_or_finance_or_staff_to_authority(self):
        User.objects.filter(pk=self.user.pk).update(is_staff=True, is_superuser=True)
        for operation, context in (
            ("finance.post", {"kind": "personal", "id": str(self.user.pk)}),
            ("mfa.enroll", {"kind": "ngo", "id": str(self.user.pk)}),
            ("platform.support", {"kind": "platform", "id": str(self.user.pk)}),
        ):
            response = self.call(
                "assurance/intents",
                {"operation": operation, "context": context, "command": {}},
            )
            self.assertEqual(response.status_code, 403)
        self.assertFalse(AssuranceIntent.objects.exists())
        self.assertFalse(self.user.organizationaccess_set.exists())

    def test_disabled_switches_fail_closed_after_successful_registration(self):
        for switch in (
            "PWC_AUTH_SESSIONS_ENABLED",
            "PWC_AUTH_MFA_ENABLED",
        ):
            with self.subTest(switch=switch), override_settings(**{switch: False}):
                response = self.call(
                    "assurance/intents",
                    {
                        "operation": "mfa.enroll",
                        "context": {"kind": "personal", "id": str(self.user.pk)},
                        "command": {},
                    },
                )
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json()["error"]["code"], "AUTH_UNAVAILABLE")


class PreauthRollbackGuardTests(TransactionTestCase):
    def tearDown(self):
        # Historical targets must not leave later-app migrations unapplied for
        # following tests (04A adds organizations leaves beyond the old target).
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    leaf = ("accounts", "0006_guard_used_preauth_bindings")
    older = ("accounts", "0004_flow_cooldown_and_transition_evidence")

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        targets = [
            target,
            ("organizations", "0002_alter_organizationaccess_id_and_more"),
        ]
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_unused_preauth_metadata_can_reverse_and_reapply(self):
        try:
            self.migrate(self.older)
            apps = self.migrate(self.leaf)
            self.assertEqual(
                apps.get_model("accounts", "AuthChallenge").objects.count(), 0
            )
        finally:
            self.migrate(self.leaf)

    def test_used_preauth_metadata_blocks_reverse_before_dropping_columns(self):
        try:
            apps = self.migrate(self.leaf)
            Challenge = apps.get_model("accounts", "AuthChallenge")
            row = Challenge.objects.create(
                purpose="preauth_mfa",
                transport="mobile",
                portal="mobile",
                flow_control_digest="a" * 64,
                proof_digest="c" * 64,
                client_digest="b" * 64,
                factor_revision=1,
                device_label="Synthetic device",
                expires_at=timezone.now() + timedelta(minutes=5),
            )
            with self.assertRaises(IrreversibleError):
                self.migrate(self.older)
            preserved = Challenge.objects.get(pk=row.pk)
            self.assertEqual(preserved.factor_revision, 1)
            self.assertEqual(preserved.device_label, "Synthetic device")
            self.assertIn(
                self.leaf, MigrationExecutor(connection).loader.applied_migrations
            )
        finally:
            self.migrate(self.leaf)

    def test_legacy_uuid_hash_email_and_ngo_relationship_survive_all_six_migrations(
        self,
    ):
        from django.contrib.auth.hashers import make_password, check_password

        old = ("accounts", "0002_alter_user_options_alter_user_is_active")
        try:
            apps = self.migrate(old)
            Legacy = apps.get_model("accounts", "User")
            emails = [
                "",
                "Person@example.invalid",
                "person@example.invalid",
                "person@bücher.invalid",
                " spaced@example.invalid ",
                "odd@example.invalid.",
            ]
            encoded = make_password("old-short")
            users = [
                Legacy.objects.create(
                    username=f"legacy-review-{i}", email=email, password=encoded
                )
                for i, email in enumerate(emails)
            ]
            org = apps.get_model("organizations", "Organization").objects.create(
                name="Synthetic legacy NGO", classification="registered"
            )
            grant = apps.get_model(
                "organizations", "OrganizationAccess"
            ).objects.create(user_id=users[0].pk, organization_id=org.pk, role="admin")
            for target in (self.leaf, old, self.leaf):
                apps = self.migrate(target)
                restored = list(
                    apps.get_model("accounts", "User").objects.order_by("username")
                )
                self.assertEqual(
                    [user.pk for user in restored], [user.pk for user in users]
                )
                self.assertEqual([user.email for user in restored], emails)
                self.assertTrue(all(user.password == encoded for user in restored))
                self.assertTrue(check_password("old-short", restored[0].password))
                preserved = apps.get_model(
                    "organizations", "OrganizationAccess"
                ).objects.get(pk=grant.pk)
                self.assertEqual(
                    (preserved.user_id, preserved.organization_id),
                    (users[0].pk, org.pk),
                )
                if target == self.leaf:
                    self.assertEqual(
                        apps.get_model("accounts", "UserContact").objects.count(), 0
                    )
                    self.assertTrue(
                        all(
                            user.auth_epoch == 1 and user.recovery_hold_state == "clear"
                            for user in restored
                        )
                    )
        finally:
            self.migrate(self.leaf)


@override_settings(**MFA_CONFIG)
class WebRotationRaces(WebReviewFixtures, TransactionTestCase):
    def race(self, *functions):
        self.assertEqual(connection.vendor, "postgresql")
        barrier = Barrier(len(functions))

        def run(function):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(functions)) as pool:
            return list(pool.map(run, functions))

    def copy_browser(self, source):
        client = Client(enforce_csrf_checks=True)
        for name in (settings.SESSION_COOKIE_NAME, settings.CSRF_COOKIE_NAME):
            client.cookies[name] = source.cookies[name].value
        return client

    def test_competing_web_step_ups_rotate_once_and_reject_old_cookie(self):
        browser, _ = self.web(self.user)
        intents = [self.web_intent(browser), self.web_intent(browser)]
        clients = [self.copy_browser(browser), self.copy_browser(browser)]
        results = self.race(
            *[
                lambda i=i: self.web_command(
                    clients[i],
                    "step-up",
                    {"intent_id": intents[i], "password": PASSWORD},
                ).status_code
                for i in range(2)
            ]
        )
        self.assertEqual(sorted(results), [200, 401])
        self.assertEqual(
            AssuranceIntent.objects.filter(proof_digest__isnull=False).count(), 1
        )
        self.assertEqual(
            SecurityEvent.objects.filter(event="auth.step_up_completed").count(), 1
        )
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        winner = clients[results.index(200)]
        self.assertEqual(self.get_me(client=winner, host=NGO).status_code, 200)

    def test_reset_racing_web_rotation_cannot_leave_cookie_or_proof_live(self):
        from .models import DeliveryIntent

        browser, _ = self.web(self.user)
        intent = self.web_intent(browser)
        flow = request_flow("reset", self.user.email, "192.0.2.61")
        delivery = DeliveryIntent.objects.get(challenge_id=flow["flow_id"])
        proof = unseal(delivery.key_id, delivery.encrypted_payload)["proof"]
        results = self.race(
            lambda: self.web_command(
                browser, "step-up", {"intent_id": intent, "password": PASSWORD}
            ).status_code,
            lambda: confirm_flow(
                "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.62"
            ),
        )
        self.assertIn(results[0], (200, 401))
        self.assertIsNone(results[1])
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        self.assertFalse(
            AuthSession.objects.filter(user=self.user, revoked_at__isnull=True).exists()
        )
        self.assertIsNotNone(AssuranceIntent.objects.get(pk=intent).invalidated_at)
        user = User.objects.get(pk=self.user.pk)
        self.assertTrue(user.check_password(NEW_PASSWORD))
        self.assertEqual(user.recovery_hold_state, "restricted")
