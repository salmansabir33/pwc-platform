"""03A.3 synthetic transport and PostgreSQL lifecycle tests. No MFA operations."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.contrib.sessions.models import Session as DjangoSession
from django.db import close_old_connections, connection, transaction
from django.test import (
    Client,
    RequestFactory,
    TestCase,
    TransactionTestCase,
    override_settings,
)
from django.utils import timezone

from . import sessions
from .flow_security import FlowProblem, new_secret
from .models import (
    User,
    UserContact,
    AuthSession,
    MobileCredential,
    MfaFactor,
    SecurityEvent,
)
from .registration import request_flow, confirm_flow
from .test_registration import FlowFixtures, TEST_CONFIG, PASSWORD, NEW_PASSWORD

NGO, OPS, API = "ngo.pwc.invalid", "ops.pwc.invalid", "api.pwc.invalid"
SESSION_CONFIG = dict(
    TEST_CONFIG,
    PWC_AUTH_SESSIONS_ENABLED=True,
    PWC_AUTH_SESSION_KEY=new_secret(),
    PWC_AUTH_PORTALS={f"https://{NGO}": "ngo_web", f"https://{OPS}": "pwc_ops"},
    ALLOWED_HOSTS=[NGO, OPS, API, "testserver"],
)


class SessionFixtures(FlowFixtures):
    def post_api(self, path, data, client=None, host=API, **extra):
        return (client or self.client).post(
            f"/api/v1/auth/{path}/",
            data=data,
            content_type="application/json",
            secure=True,
            HTTP_HOST=host,
            **extra,
        )

    def mobile(self, user, password=PASSWORD, label="Phone"):
        response = self.post_api(
            "mobile/login",
            {"email": user.email, "password": password, "device_label": label},
            client=Client(enforce_csrf_checks=True),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertFalse(response.cookies)
        return response.json()

    def get_me(self, token=None, client=None, host=API, **extra):
        if token:
            extra["HTTP_AUTHORIZATION"] = "Bearer " + token
        return (client or self.client).get(
            "/api/v1/auth/me/", secure=True, HTTP_HOST=host, **extra
        )

    def web(self, user, host=NGO, password=PASSWORD, client=None):
        client = client or Client(enforce_csrf_checks=True)
        token = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=host).json()[
            "csrf_token"
        ]
        response = self.post_api(
            "web/login",
            {"email": user.email, "password": password},
            client=client,
            host=host,
            HTTP_ORIGIN=f"https://{host}",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 200, response.content)
        return client, response

    def refresh(self, token):
        return self.post_api("mobile/refresh", {"refresh_token": token})

    def factor(self, user):
        session = AuthSession.objects.create(
            user=user,
            transport="mobile",
            portal="mobile",
            auth_epoch=user.auth_epoch,
            absolute_expires_at=timezone.now() + timedelta(hours=1),
        )
        return MfaFactor.objects.create(
            user=user,
            state="active",
            key_id="synthetic",
            encrypted_secret=b"synthetic-not-real-totp",
            confirmed_at=timezone.now(),
            enrollment_session=session,
            auth_epoch=user.auth_epoch,
            recovery_generation=user.recovery_generation,
            expires_at=timezone.now() + timedelta(minutes=5),
        )


@override_settings(**SESSION_CONFIG)
class BrowserSessionTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, self.contact = self.account()

    def test_csrf_even_anonymous_and_exact_origin(self):
        for extra in (
            {},
            {"HTTP_ORIGIN": f"https://{NGO}"},
            {"HTTP_ORIGIN": "https://evil.invalid"},
        ):
            response = self.post_api(
                "web/login",
                {"email": self.user.email, "password": PASSWORD},
                host=NGO,
                **extra,
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")
        self.assertFalse(AuthSession.objects.exists())

    def test_fixation_cookie_csrf_rotation_and_minimal_envelope(self):
        old = self.client.session
        old["synthetic"] = "old"
        old.save()
        self.client.cookies[settings.SESSION_COOKIE_NAME] = old.session_key
        old_key = old.session_key
        old_csrf = (
            self.client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO)
            .cookies[settings.CSRF_COOKIE_NAME]
            .value
        )
        client, response = self.web(self.user, client=self.client)
        cookie = response.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(settings.SESSION_COOKIE_NAME.startswith("__Host-"))
        self.assertTrue(cookie["secure"] and cookie["httponly"])
        self.assertEqual(cookie["domain"], "")
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertNotEqual(cookie.value, old_key)
        self.assertFalse(DjangoSession.objects.filter(pk=old_key).exists())
        self.assertNotEqual(client.cookies[settings.CSRF_COOKIE_NAME].value, old_csrf)
        data = response.json()
        self.assertEqual(set(data), {"user", "session", "recovery_hold_state"})
        self.assertNotIn("access_token", data)
        self.assertEqual(set(data["user"]), {"id", "preferred_language"})
        row = AuthSession.objects.get()
        self.assertNotIn(cookie.value, row.web_key_digest)
        self.assertEqual(row.portal, "ngo_web")
        self.assertEqual(client.session.get_expiry_date(), row.absolute_expires_at)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)

    def test_ops_lifetime_and_portal_cookie_cannot_cross_hosts(self):
        ngo, _ = self.web(self.user)
        self.assertEqual(self.get_me(client=ngo, host=OPS).status_code, 401)
        ops, response = self.web(self.user, host=OPS)
        row = AuthSession.objects.get(pk=response.json()["session"]["id"])
        self.assertEqual(row.absolute_expires_at - row.created_at, timedelta(hours=8))
        self.assertEqual(
            sessions.idle_deadline(row) - row.created_at, timedelta(minutes=15)
        )
        self.assertEqual(self.get_me(client=ops, host=NGO).status_code, 401)
        self.assertEqual(self.get_me(client=ngo, host=NGO).status_code, 200)

    def test_get_status_does_not_keep_session_alive_and_idle_boundary(self):
        client, _ = self.web(self.user)
        row = AuthSession.objects.get()
        original = row.last_interactive_at
        with patch(
            "accounts.sessions.timezone.now",
            return_value=original + timedelta(minutes=29),
        ):
            self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)
            self.assertEqual(
                client.get(
                    "/api/v1/auth/sessions/", secure=True, HTTP_HOST=NGO
                ).status_code,
                200,
            )
        row.refresh_from_db()
        self.assertEqual(row.last_interactive_at, original)
        with patch(
            "accounts.sessions.timezone.now",
            return_value=original + timedelta(minutes=30),
        ):
            self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)

    def test_browser_absolute_boundary_even_recent_activity(self):
        client, _ = self.web(self.user)
        row = AuthSession.objects.get()
        AuthSession.objects.filter(pk=row.pk).update(
            last_interactive_at=row.absolute_expires_at - timedelta(minutes=1)
        )
        with patch(
            "accounts.sessions.timezone.now", return_value=row.absolute_expires_at
        ):
            self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)

    def test_logout_requires_csrf_and_revokes_cookie(self):
        client, _ = self.web(self.user)
        self.assertEqual(
            self.post_api(
                "logout", {}, client=client, host=NGO, HTTP_ORIGIN=f"https://{NGO}"
            ).status_code,
            403,
        )
        token = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        response = self.post_api(
            "logout",
            {},
            client=client,
            host=NGO,
            HTTP_ORIGIN=f"https://{NGO}",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies[settings.SESSION_COOKIE_NAME]["max-age"], 0)
        self.assertEqual(AuthSession.objects.get().revocation_reason, "logout")
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)

    def test_legacy_django_cookie_cannot_bypass_registry(self):
        self.client.force_login(self.user)
        self.assertEqual(self.get_me(client=self.client, host=NGO).status_code, 401)
        self.assertFalse(AuthSession.objects.exists())

    def test_hostile_origin_and_spoofed_proxy_headers(self):
        token = self.client.get(
            "/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO
        ).json()["csrf_token"]
        response = self.post_api(
            "web/login",
            {"email": self.user.email, "password": PASSWORD},
            host=NGO,
            HTTP_ORIGIN="https://evil.invalid",
            HTTP_X_CSRFTOKEN=token,
            HTTP_X_FORWARDED_HOST=NGO,
            HTTP_X_FORWARDED_PROTO="https",
            HTTP_X_FORWARDED_FOR="192.0.2.88",
        )
        self.assertEqual(response.status_code, 403)
        response = self.client.post(
            "/api/v1/auth/web/login/",
            data={"email": self.user.email, "password": PASSWORD},
            content_type="application/json",
            HTTP_HOST=NGO,
            HTTP_X_FORWARDED_PROTO="https",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AuthSession.objects.exists())

    def test_wrong_cookie_binding_and_epoch_and_password_change(self):
        client, _ = self.web(self.user)
        row = AuthSession.objects.get()
        AuthSession.objects.filter(pk=row.pk).update(auth_epoch=2)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)
        AuthSession.objects.filter(pk=row.pk).update(auth_epoch=1)
        self.user.set_password(NEW_PASSWORD)
        self.user.save(update_fields=["password"])
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)

    def test_browser_relogin_rotates_even_same_user(self):
        client, first = self.web(self.user)
        key = client.cookies[settings.SESSION_COOKIE_NAME].value
        client, second = self.web(self.user, client=client)
        self.assertNotEqual(key, client.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertNotEqual(
            first.json()["session"]["id"], second.json()["session"]["id"]
        )
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 200)


@override_settings(**SESSION_CONFIG)
class MobileSessionTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, self.contact = self.account()

    def test_opaque_credentials_digests_only_and_live_profile(self):
        data = self.mobile(self.user)
        row = AuthSession.objects.get()
        self.assertEqual(row.absolute_expires_at - row.created_at, timedelta(days=30))
        self.assertEqual(
            sessions.idle_deadline(row) - row.created_at, timedelta(days=7)
        )
        self.assertEqual(data["expires_in"], 300)
        self.assertEqual(
            data["refresh_expires_at"], row.absolute_expires_at.isoformat()
        )
        self.assertEqual(data["token_type"], "Bearer")
        stored = repr(list(MobileCredential.objects.values())) + repr(
            list(SecurityEvent.objects.values())
        )
        for key in ("access_token", "refresh_token"):
            self.assertEqual(len(data[key]), 76)
            self.assertNotIn(data[key].split(".")[1], stored)
        self.assertNotIn(PASSWORD, stored)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 200)
        self.assertEqual(self.get_me(data["refresh_token"]).status_code, 401)
        digest = MobileCredential.objects.get(kind="access").secret_digest
        self.assertEqual(self.get_me(digest).status_code, 401)

    def test_rotation_supersedes_access_and_consumes_refresh(self):
        data = self.mobile(self.user)
        result = self.refresh(data["refresh_token"])
        self.assertEqual(result.status_code, 200)
        new = result.json()
        self.assertNotEqual(new["access_token"], data["access_token"])
        self.assertNotEqual(new["refresh_token"], data["refresh_token"])
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(self.get_me(new["access_token"]).status_code, 200)
        self.assertEqual(MobileCredential.objects.count(), 4)
        self.assertEqual(AuthSession.objects.get().credential_generation, 2)
        self.assertEqual(
            MobileCredential.objects.filter(
                kind="access", replaced_at__isnull=True
            ).count(),
            1,
        )
        self.assertEqual(
            MobileCredential.objects.filter(
                kind="refresh", consumed_at__isnull=True
            ).count(),
            1,
        )

    def test_replay_or_lost_response_revokes_only_that_family(self):
        first = self.mobile(self.user)
        second = self.mobile(self.user)
        new = self.refresh(first["refresh_token"]).json()
        replay = self.refresh(first["refresh_token"])
        self.assertEqual(replay.status_code, 401)
        self.assertEqual(self.get_me(new["access_token"]).status_code, 401)
        self.assertEqual(self.refresh(new["refresh_token"]).status_code, 401)
        self.assertEqual(self.get_me(second["access_token"]).status_code, 200)
        self.assertEqual(
            AuthSession.objects.get(pk=first["session"]["id"]).revocation_reason,
            "refresh_replay",
        )
        self.assertEqual(MobileCredential.objects.count(), 6)

    def test_guessed_refresh_selector_does_not_revoke(self):
        data = self.mobile(self.user)
        selector = data["refresh_token"].split(".")[0]
        self.assertEqual(self.refresh(selector + "." + "x" * 43).status_code, 401)
        self.assertIsNone(AuthSession.objects.get().revoked_at)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 200)
        self.assertEqual(MobileCredential.objects.count(), 2)

    def test_access_expiry_exact_five_minutes(self):
        data = self.mobile(self.user)
        row = MobileCredential.objects.get(kind="access")
        with patch("accounts.sessions.timezone.now", return_value=row.expires_at):
            self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 200)

    def test_refresh_never_renews_idle_or_absolute(self):
        data = self.mobile(self.user)
        row = AuthSession.objects.get()
        with patch(
            "accounts.sessions.timezone.now",
            return_value=row.created_at + timedelta(days=6),
        ):
            rotated = self.refresh(data["refresh_token"])
            self.assertEqual(rotated.status_code, 200)
        row.refresh_from_db()
        self.assertEqual(row.last_interactive_at, row.created_at)
        with patch(
            "accounts.sessions.timezone.now",
            return_value=row.created_at + timedelta(days=7),
        ):
            self.assertEqual(
                self.refresh(rotated.json()["refresh_token"]).status_code, 401
            )
        self.assertEqual(
            AuthSession.objects.get().absolute_expires_at, row.absolute_expires_at
        )

    def test_absolute_session_expiry_cannot_refresh_even_with_recent_activity(self):
        data = self.mobile(self.user)
        row = AuthSession.objects.get()
        AuthSession.objects.filter(pk=row.pk).update(
            last_interactive_at=row.absolute_expires_at - timedelta(minutes=1)
        )
        with patch(
            "accounts.sessions.timezone.now", return_value=row.absolute_expires_at
        ):
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        self.assertEqual(MobileCredential.objects.count(), 2)

    def test_current_logout_immediate_not_waiting_for_access_expiry(self):
        data = self.mobile(self.user)
        response = self.post_api(
            "logout", {}, HTTP_AUTHORIZATION="Bearer " + data["access_token"]
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        self.assertFalse(response.cookies)

    def test_disabled_epoch_or_raw_password_change_invalidate(self):
        data = self.mobile(self.user)
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        User.objects.filter(pk=self.user.pk).update(is_active=True, auth_epoch=2)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        User.objects.filter(pk=self.user.pk).update(
            auth_epoch=1, password=make_password(NEW_PASSWORD)
        )
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)

    def test_suspension_hook_revokes_and_reactivation_never_revives(self):
        data = self.mobile(self.user)
        sessions.suspend_account(self.user.pk)
        self.user.refresh_from_db()
        self.assertEqual(self.user.auth_epoch, 2)
        self.assertFalse(self.user.is_active)
        User.objects.filter(pk=self.user.pk).update(is_active=True)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)

    def test_registration_reset_revokes_browser_mobile_and_sets_hold(self):
        browser, _ = self.web(self.user)
        data = self.mobile(self.user)
        flow = request_flow("reset", self.user.email, "192.0.2.22")
        proof = self.proof(flow)
        self.assertIsNone(
            confirm_flow("reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.22")
        )
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        new = self.mobile(self.user, password=NEW_PASSWORD)
        self.assertEqual(new["recovery_hold_state"], "restricted")
        self.assertFalse(
            AuthSession.objects.filter(auth_epoch=1, revoked_at__isnull=True).exists()
        )

    def test_retired_contact_or_added_mfa_denies_existing_sessions(self):
        data = self.mobile(self.user)
        self.contact.retired_at = timezone.now()
        self.contact.is_primary = False
        self.contact.save()
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.contact.retired_at = None
        self.contact.is_primary = True
        self.contact.save()
        self.factor(self.user)
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)


@override_settings(**SESSION_CONFIG)
class SessionTransportTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()

    def test_native_login_rejects_browser_provenance_cookie_and_authorization(self):
        for extra in (
            {"HTTP_ORIGIN": f"https://{NGO}"},
            {"HTTP_SEC_FETCH_SITE": "same-origin"},
            {"HTTP_REFERER": f"https://{NGO}/"},
            {"HTTP_AUTHORIZATION": "Bearer ignored"},
        ):
            response = self.post_api(
                "mobile/login",
                {"email": self.user.email, "password": PASSWORD},
                **extra,
            )
            self.assertEqual(response.status_code, 400)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "untrusted"
        response = self.post_api(
            "mobile/login", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response.json()["error"]["code"], "TRANSPORT_NOT_ALLOWED")
        self.assertFalse(AuthSession.objects.exists())

    def test_mixed_credentials_reject_before_lookup_on_every_route(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "untrusted"
        for path in (
            "web/login",
            "mobile/login",
            "mobile/refresh",
            "me",
            "logout",
            "logout-all",
            "sessions",
        ):
            with self.subTest(path=path), patch(
                "accounts.sessions.locate",
                side_effect=AssertionError("must reject first"),
            ):
                if path in ("me", "sessions"):
                    response = self.client.get(
                        f"/api/v1/auth/{path}/",
                        secure=True,
                        HTTP_HOST=NGO,
                        HTTP_AUTHORIZATION="Bearer untrusted",
                    )
                else:
                    response = self.post_api(
                        path, {}, host=NGO, HTTP_AUTHORIZATION="Bearer untrusted"
                    )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(
                    response.json()["error"]["code"], "AMBIGUOUS_CREDENTIALS"
                )
        self.assertFalse(AuthSession.objects.exists())

    def test_refresh_body_only_no_access_header_cookie_or_browser_origin(self):
        data = self.mobile(self.user)
        for extra in (
            {"HTTP_AUTHORIZATION": "Bearer " + data["access_token"]},
            {"HTTP_ORIGIN": f"https://{NGO}"},
        ):
            self.assertEqual(
                self.post_api(
                    "mobile/refresh", {"refresh_token": data["refresh_token"]}, **extra
                ).status_code,
                400,
            )
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "untrusted"
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 400)
        self.assertEqual(MobileCredential.objects.count(), 2)

    def test_verified_canonical_only_no_public_username_backend(self):
        self.assertIsNone(authenticate(username=self.user.username, password=PASSWORD))
        self.assertEqual(
            authenticate(email=self.user.email.upper(), password=PASSWORD).pk,
            self.user.pk,
        )
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email.upper(), "password": PASSWORD}
            ).status_code,
            200,
        )
        legacy, _ = self.account("legacy", verified=False)
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": legacy.email, "password": PASSWORD}
            ).json()["error"]["code"],
            "INVALID_CREDENTIALS",
        )

    def test_non_enumerating_unknown_wrong_disabled_unverified(self):
        inactive, _ = self.account("disabled", active=False)
        legacy, _ = self.account("legacy", verified=False)
        envelopes = []
        for email, password in (
            (self.user.email, "wrong password"),
            (inactive.email, PASSWORD),
            (legacy.email, PASSWORD),
            ("absent@example.invalid", PASSWORD),
        ):
            response = self.post_api(
                "mobile/login", {"email": email, "password": password}
            )
            self.assertEqual(response.status_code, 401)
            error = response.json()["error"]
            self.assertEqual(error["code"], "INVALID_CREDENTIALS")
            envelopes.append((error["code"], error["message"], error["field_errors"]))
        self.assertTrue(all(value == envelopes[0] for value in envelopes))
        self.assertFalse(AuthSession.objects.exists())

    def test_mfa_login_denied_after_correct_password_without_creating_any_credentials(
        self,
    ):
        self.factor(self.user)
        before = AuthSession.objects.count()
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email, "password": "wrong"}
            ).status_code,
            401,
        )
        response = self.post_api(
            "mobile/login", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "MFA_REQUIRED")
        self.assertEqual(AuthSession.objects.count(), before)
        self.assertFalse(MobileCredential.objects.exists())

    def test_logout_all_and_other_revoke_deny_unimplemented_assurance(self):
        first = self.mobile(self.user)
        second = self.mobile(self.user)
        token = first["access_token"]
        response = self.post_api(
            "logout-all",
            {"assurance_proof": "forged"},
            HTTP_AUTHORIZATION="Bearer " + token,
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "STEP_UP_REQUIRED")
        response = self.client.delete(
            f"/api/v1/auth/sessions/{second['session']['id']}/",
            data={"assurance_proof": "forged"},
            content_type="application/json",
            secure=True,
            HTTP_HOST=API,
            HTTP_AUTHORIZATION="Bearer " + token,
        )
        self.assertEqual(response.status_code, 403)
        self.user.refresh_from_db()
        self.assertEqual(self.user.auth_epoch, 1)
        self.assertFalse(AuthSession.objects.filter(revoked_at__isnull=False).exists())

    def test_list_own_sessions_only_and_foreign_revoke_not_found(self):
        first = self.mobile(self.user, label="My Phone")
        other, _ = self.account("other")
        foreign = self.mobile(other)
        response = self.client.get(
            "/api/v1/auth/sessions/",
            secure=True,
            HTTP_HOST=API,
            HTTP_AUTHORIZATION="Bearer " + first["access_token"],
        )
        rows = response.json()["results"]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["device_label"], "My Phone")
        self.assertEqual(
            set(rows[0]),
            {
                "id",
                "device_label",
                "transport",
                "created_at",
                "last_interactive_at",
                "is_current",
            },
        )
        for target in (foreign["session"]["id"], str(uuid.uuid4()), "invalid-uuid"):
            response = self.client.delete(
                f"/api/v1/auth/sessions/{target}/",
                data={"assurance_proof": "x"},
                content_type="application/json",
                secure=True,
                HTTP_HOST=API,
                HTTP_AUTHORIZATION="Bearer " + first["access_token"],
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertEqual(self.get_me(foreign["access_token"]).status_code, 200)

    def test_login_shared_budget_and_forwarded_ip_not_trusted(self):
        for index in range(5):
            response = self.post_api(
                "mobile/login",
                {
                    "email": self.user.email.upper() if index % 2 else self.user.email,
                    "password": "wrong",
                },
                HTTP_X_FORWARDED_FOR=f"192.0.2.{index+1}",
            )
            self.assertEqual(response.status_code, 401)
        response = self.post_api(
            "mobile/login", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response.status_code, 429)
        self.assertTrue(int(response["Retry-After"]) > 0)
        self.assertFalse(AuthSession.objects.exists())

    def test_feature_flag_keys_proxy_and_portal_fail_closed(self):
        configs = [
            dict(PWC_AUTH_SESSIONS_ENABLED=False),
            dict(PWC_AUTH_SESSION_KEY=""),
            dict(PWC_AUTH_ABUSE_KEY=""),
            dict(SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO", "https")),
            dict(USE_X_FORWARDED_HOST=True),
        ]
        for config in configs:
            with override_settings(**config):
                response = self.post_api(
                    "mobile/login", {"email": self.user.email, "password": PASSWORD}
                )
                self.assertEqual(response.status_code, 503)
        with override_settings(PWC_AUTH_PORTALS={}):
            self.assertEqual(
                self.post_api(
                    "web/login",
                    {"email": self.user.email, "password": PASSWORD},
                    host=NGO,
                ).status_code,
                503,
            )
        with override_settings(SESSION_COOKIE_DOMAIN=".pwc.invalid"):
            self.assertEqual(
                self.post_api(
                    "web/login",
                    {"email": self.user.email, "password": PASSWORD},
                    host=NGO,
                ).status_code,
                503,
            )
        self.assertFalse(AuthSession.objects.exists())

    def test_unusable_password_retired_contact_and_longer_or_short_legacy_password(
        self,
    ):
        # Minimum applies when setting passwords, not silently to legacy login.
        self.user.set_password("old-short")
        self.user.save(update_fields=["password"])
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email, "password": "old-short"}
            ).status_code,
            200,
        )
        UserContact.objects.filter(user=self.user).update(
            is_primary=False, retired_at=timezone.now()
        )
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email, "password": "old-short"}
            ).status_code,
            401,
        )
        UserContact.objects.filter(user=self.user).update(
            is_primary=True, retired_at=None
        )
        self.user.set_unusable_password()
        self.user.save(update_fields=["password"])
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": self.user.email, "password": "old-short"}
            ).status_code,
            401,
        )

    def test_malformed_inputs_and_methods_no_secret_echo(self):
        for data in (
            {},
            {"email": self.user.email, "password": PASSWORD, "portal": "pwc_ops"},
            {
                "email": self.user.email,
                "password": PASSWORD,
                "device_label": "bad\nlabel",
            },
        ):
            response = self.post_api("mobile/login", data)
            self.assertEqual(response.status_code, 400)
            self.assertNotIn(PASSWORD, response.content.decode())
        response = self.client.get(
            "/api/v1/auth/mobile/login/", secure=True, HTTP_HOST=API
        )
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "POST")
        self.assertFalse(AuthSession.objects.exists())

    def test_all_auth_responses_no_store_and_no_referrer(self):
        response = self.post_api(
            "mobile/login", {"email": self.user.email, "password": PASSWORD}
        )
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        error = self.get_me("not-a-token")
        self.assertEqual(error.status_code, 401)
        self.assertEqual(error["Cache-Control"], "no-store")
        self.assertEqual(
            set(error.json()["error"]),
            {"code", "message", "field_errors", "request_id"},
        )

    def test_no_ngo_authority_from_login(self):
        from organizations.models import Organization, OrganizationAccess

        org = Organization.objects.create(
            name="Synthetic NGO", classification="registered"
        )
        grant = OrganizationAccess.objects.create(
            user=self.user, organization=org, role="admin", active=False
        )
        self.mobile(self.user)
        grant.refresh_from_db()
        self.user.refresh_from_db()
        self.assertFalse(grant.active or self.user.is_staff or self.user.is_superuser)
        self.assertEqual(OrganizationAccess.objects.count(), 1)


@override_settings(**SESSION_CONFIG)
class SessionConcurrencyTests(SessionFixtures, TransactionTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()
        self.assertEqual(connection.vendor, "postgresql")

    def parallel(self, actions):
        barrier = Barrier(len(actions))

        def run(action):
            close_old_connections()
            try:
                barrier.wait(timeout=15)
                return action()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(actions)) as pool:
            return list(pool.map(run, actions))

    def test_two_refreshes_one_descendant_then_replay_revokes_family(self):
        data = self.mobile(self.user)
        results = self.parallel(
            [lambda: sessions.refresh(data["refresh_token"], "192.0.2.1")] * 2
        )
        self.assertEqual(sum(isinstance(value, dict) for value in results), 1)
        self.assertEqual(
            sum(
                isinstance(value, FlowProblem) and value.code == "SESSION_INVALID"
                for value in results
            ),
            1,
        )
        self.assertEqual(MobileCredential.objects.count(), 4)
        self.assertEqual(AuthSession.objects.get().revocation_reason, "refresh_replay")
        descendant = next(value for value in results if isinstance(value, dict))
        self.assertEqual(self.get_me(descendant["access_token"]).status_code, 401)

    def test_concurrent_logins_one_independent_family_per_successful_command(self):
        def login():
            request = RequestFactory().post("/", secure=True, HTTP_HOST=API)
            return sessions.login(
                request, self.user.email, PASSWORD, "Phone", "mobile", "mobile"
            )

        results = self.parallel([login, login])
        self.assertTrue(all(isinstance(value, dict) for value in results))
        self.assertEqual(AuthSession.objects.count(), 2)
        self.assertEqual(MobileCredential.objects.count(), 4)
        self.assertEqual(len({value["session"]["id"] for value in results}), 2)
        self.assertEqual(
            SecurityEvent.objects.filter(event="auth.login_completed").count(), 2
        )

    def test_reset_racing_refresh_no_live_post_reset_credential(self):
        data = self.mobile(self.user)
        flow = request_flow("reset", self.user.email, "192.0.2.10")
        proof = self.proof(flow)
        results = self.parallel(
            [
                lambda: sessions.refresh(data["refresh_token"], "192.0.2.1"),
                lambda: confirm_flow(
                    "reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2"
                ),
            ]
        )
        self.assertIsNone(results[1])
        self.user.refresh_from_db()
        self.assertEqual(self.user.auth_epoch, 2)
        self.assertFalse(
            AuthSession.objects.filter(user=self.user, revoked_at__isnull=True).exists()
        )
        if isinstance(results[0], dict):
            self.assertEqual(self.get_me(results[0]["access_token"]).status_code, 401)
        else:
            self.assertEqual(results[0].code, "SESSION_INVALID")

    def test_suspension_racing_refresh_and_reactivation_no_revived_family(self):
        data = self.mobile(self.user)
        results = self.parallel(
            [
                lambda: sessions.refresh(data["refresh_token"], "192.0.2.1"),
                lambda: sessions.suspend_account(self.user.pk),
            ]
        )
        User.objects.filter(pk=self.user.pk).update(is_active=True)
        if isinstance(results[0], dict):
            self.assertEqual(self.get_me(results[0]["access_token"]).status_code, 401)
        self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
        self.assertEqual(AuthSession.objects.get().revocation_reason, "suspension")

    def test_internal_all_revocation_racing_refresh(self):
        data = self.mobile(self.user)

        def revoke():
            with transaction.atomic():
                owner = User.objects.select_for_update().get(pk=self.user.pk)
                sessions.revoke_all_locked(owner, "synthetic_logout_all")

        results = self.parallel(
            [lambda: sessions.refresh(data["refresh_token"], "192.0.2.1"), revoke]
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.auth_epoch, 2)
        if isinstance(results[0], dict):
            self.assertEqual(self.get_me(results[0]["access_token"]).status_code, 401)
        self.assertIsNotNone(AuthSession.objects.get().revoked_at)

    def test_reset_between_password_check_and_issuance_rejects_stale_login(self):
        flow = request_flow("reset", self.user.email, "192.0.2.10")
        proof = self.proof(flow)
        checked, released = Event(), Event()
        original = sessions.password_candidate

        def paused(*args):
            result = original(*args)
            checked.set()
            if not released.wait(timeout=15):
                raise AssertionError("reset did not complete")
            return result

        def login():
            close_old_connections()
            try:
                request = RequestFactory().post("/", secure=True, HTTP_HOST=API)
                return sessions.login(
                    request, self.user.email, PASSWORD, "Phone", "mobile", "mobile"
                )
            finally:
                close_old_connections()

        with patch(
            "accounts.sessions.password_candidate", side_effect=paused
        ), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(login)
            self.assertTrue(checked.wait(timeout=15))
            self.assertIsNone(
                confirm_flow("reset", flow["flow_id"], proof, NEW_PASSWORD, "192.0.2.2")
            )
            released.set()
            result = future.result(timeout=15)
        self.assertEqual(result.code, "INVALID_CREDENTIALS")
        self.assertFalse(AuthSession.objects.exists())
        self.assertFalse(MobileCredential.objects.exists())


@override_settings(**SESSION_CONFIG)
class SessionBindingAndAdapterTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()

    def test_moved_consumed_refresh_cannot_revoke_foreign_family_even_shared_legacy_hash(
        self,
    ):
        original = self.mobile(self.user)
        self.assertEqual(self.refresh(original["refresh_token"]).status_code, 200)
        other, _ = self.account("other")
        User.objects.filter(pk=other.pk).update(password=self.user.password)
        foreign = self.mobile(other)
        selector = sessions.parse_token(original["refresh_token"])[0]
        # Raw ORM can bypass full_clean; the HMAC owner/family binding must not.
        MobileCredential.objects.filter(pk=selector).update(
            session_id=foreign["session"]["id"]
        )
        self.assertEqual(self.refresh(original["refresh_token"]).status_code, 401)
        self.assertIsNone(
            AuthSession.objects.get(pk=foreign["session"]["id"]).revoked_at
        )
        self.assertEqual(self.get_me(foreign["access_token"]).status_code, 200)

    def test_cookie_data_cannot_select_different_registry_session(self):
        client, _ = self.web(self.user)
        other = self.mobile(self.user)
        state = client.session
        state["pwc_session_id"] = other["session"]["id"]
        state.save()
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)
        self.assertEqual(self.get_me(other["access_token"]).status_code, 200)

    def test_same_browser_reauthentication_retires_previous_registry_entry(self):
        client, first = self.web(self.user)
        _, second = self.web(self.user, client=client)
        old = AuthSession.objects.get(pk=first.json()["session"]["id"])
        self.assertEqual(old.revocation_reason, "reauthentication")
        self.assertIsNotNone(old.revoked_at)
        self.assertNotEqual(old.pk, uuid.UUID(second.json()["session"]["id"]))

    def test_refresh_owner_rechecked_after_selector_lookup(self):
        data = self.mobile(self.user)
        snapshot_id = sessions.parse_token(data["refresh_token"])[0]
        original = User.objects.select_for_update

        def moved(*args, **kwargs):
            MobileCredential.objects.filter(pk=snapshot_id).delete()
            return original(*args, **kwargs)

        with patch.object(User.objects, "select_for_update", side_effect=moved):
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        self.assertIsNone(AuthSession.objects.get().revoked_at)

    def test_default_disabled_and_missing_session_key_also_reject_existing_credentials(
        self,
    ):
        data = self.mobile(self.user)
        for config in (
            dict(PWC_AUTH_SESSIONS_ENABLED=False),
            dict(PWC_AUTH_SESSION_KEY=""),
        ):
            with override_settings(**config):
                self.assertEqual(self.get_me(data["access_token"]).status_code, 503)
                self.assertEqual(self.refresh(data["refresh_token"]).status_code, 503)

    def test_session_key_rotation_invalidates_both_transports_without_plaintext_fallback(
        self,
    ):
        data = self.mobile(self.user)
        browser, _ = self.web(self.user)
        with override_settings(PWC_AUTH_SESSION_KEY=new_secret()):
            self.assertEqual(self.get_me(data["access_token"]).status_code, 401)
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
            self.assertEqual(self.get_me(client=browser, host=NGO).status_code, 401)

    def test_explicit_drf_adapter_keeps_mixed_400_and_unavailable_503(self):
        from rest_framework.request import Request
        from rest_framework.exceptions import APIException
        from .session_authentication import PersonalAuthentication
        from rest_framework.test import APIRequestFactory

        raw = APIRequestFactory().get(
            "/",
            secure=True,
            HTTP_HOST=API,
            HTTP_AUTHORIZATION="Bearer forged",
            HTTP_COOKIE=f"{settings.SESSION_COOKIE_NAME}=forged",
        )
        with self.assertRaises(APIException) as caught:
            PersonalAuthentication().authenticate(Request(raw))
        self.assertEqual(caught.exception.status_code, 400)
        self.assertEqual(
            caught.exception.detail["error"]["code"], "AMBIGUOUS_CREDENTIALS"
        )
        raw = APIRequestFactory().get(
            "/", secure=True, HTTP_HOST=API, HTTP_AUTHORIZATION="Bearer forged"
        )
        with override_settings(PWC_AUTH_SESSIONS_ENABLED=False), self.assertRaises(
            APIException
        ) as caught:
            PersonalAuthentication().authenticate(Request(raw))
        self.assertEqual(caught.exception.status_code, 503)

    def test_drf_adapter_uses_live_registry_and_returns_no_private_authority(self):
        from rest_framework.request import Request
        from rest_framework.test import APIRequestFactory
        from rest_framework.exceptions import APIException
        from .session_authentication import PersonalAuthentication

        data = self.mobile(self.user)

        def raw():
            return Request(
                APIRequestFactory().get(
                    "/",
                    secure=True,
                    HTTP_HOST=API,
                    HTTP_AUTHORIZATION="Bearer " + data["access_token"],
                )
            )

        user, session = PersonalAuthentication().authenticate(raw())
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(str(session.pk), data["session"]["id"])
        AuthSession.objects.filter(pk=session.pk).update(
            revoked_at=timezone.now(), revocation_reason="synthetic"
        )
        with self.assertRaises(APIException) as caught:
            PersonalAuthentication().authenticate(raw())
        self.assertEqual(caught.exception.status_code, 401)

    def test_database_failure_never_falls_back_to_anonymous_login(self):
        from django.db import OperationalError

        with patch(
            "accounts.sessions.password_candidate",
            side_effect=OperationalError("sensitive details"),
        ):
            result = self.post_api(
                "mobile/login", {"email": self.user.email, "password": PASSWORD}
            )
        self.assertEqual(result.status_code, 503)
        self.assertNotIn("sensitive", result.content.decode())
        self.assertNotIn(PASSWORD, result.content.decode())
        self.assertFalse(AuthSession.objects.exists())

    def test_no_proxy_or_portal_body_override(self):
        with override_settings(USE_X_FORWARDED_PORT=True):
            self.assertEqual(
                self.post_api(
                    "mobile/login", {"email": self.user.email, "password": PASSWORD}
                ).status_code,
                503,
            )
        for config in (
            dict(PWC_AUTH_PORTALS={f"https://{NGO}": []}),
            dict(SESSION_COOKIE_NAME="unprefixed"),
        ):
            with override_settings(**config):
                self.assertEqual(
                    self.post_api(
                        "web/login",
                        {"email": self.user.email, "password": PASSWORD},
                        host=NGO,
                    ).status_code,
                    503,
                )
        with override_settings(
            PWC_AUTH_PORTALS={f"https://{NGO}": "ngo_web", f"https://{OPS}": "ngo_web"}
        ):
            self.assertEqual(
                self.post_api(
                    "web/login",
                    {"email": self.user.email, "password": PASSWORD},
                    host=NGO,
                ).status_code,
                503,
            )
        response = self.post_api(
            "mobile/login",
            {"email": self.user.email, "password": PASSWORD, "portal": "pwc_ops"},
        )
        self.assertEqual(response.status_code, 400)


@override_settings(**SESSION_CONFIG)
class AdditionalSessionRaces(SessionFixtures, TransactionTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()

    def test_suspension_between_password_verification_and_login_cannot_issue(self):
        checked, released = Event(), Event()
        original = sessions.password_candidate

        def paused(*args):
            result = original(*args)
            checked.set()
            if not released.wait(timeout=15):
                raise AssertionError("suspension did not commit")
            return result

        def login():
            close_old_connections()
            try:
                request = RequestFactory().post("/", secure=True, HTTP_HOST=API)
                return sessions.login(
                    request, self.user.email, PASSWORD, "Phone", "mobile", "mobile"
                )
            finally:
                close_old_connections()

        with patch(
            "accounts.sessions.password_candidate", side_effect=paused
        ), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(login)
            self.assertTrue(checked.wait(timeout=15))
            sessions.suspend_account(self.user.pk)
            released.set()
            result = future.result(timeout=15)
        self.assertEqual(result.code, "INVALID_CREDENTIALS")
        self.assertFalse(AuthSession.objects.exists())
        self.assertFalse(MobileCredential.objects.exists())

    def test_async_django_user_helper_cannot_bypass_registry(self):
        from asgiref.sync import async_to_sync
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.auth.middleware import AuthenticationMiddleware
        from .session_middleware import PersonalSessionMiddleware

        self.client.force_login(self.user)
        raw = RequestFactory().get(
            "/",
            secure=True,
            HTTP_HOST=NGO,
            HTTP_COOKIE=f"{settings.SESSION_COOKIE_NAME}={self.client.cookies[settings.SESSION_COOKIE_NAME].value}",
        )
        SessionMiddleware(lambda r: None).process_request(raw)
        AuthenticationMiddleware(lambda r: None).process_request(raw)
        self.assertTrue(async_to_sync(raw.auser)().is_authenticated)
        PersonalSessionMiddleware(lambda r: None)(raw)
        self.assertFalse(async_to_sync(raw.auser)().is_authenticated)


@override_settings(**SESSION_CONFIG)
class InFlightExpiryTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()

    def test_refresh_waiting_for_budget_cannot_issue_past_absolute_deadline(self):
        from django.db.models.query import QuerySet

        data = self.mobile(self.user)
        row = AuthSession.objects.get()
        clock = [timezone.now()]
        original = QuerySet.get_or_create

        def delayed(queryset, *args, **kwargs):
            result = original(queryset, *args, **kwargs)
            if kwargs.get("dimension") == "session":
                clock[0] = row.absolute_expires_at
            return result

        with patch(
            "accounts.sessions.timezone.now", side_effect=lambda: clock[0]
        ), patch.object(QuerySet, "get_or_create", new=delayed):
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        self.assertEqual(MobileCredential.objects.count(), 2)
        self.assertIsNone(MobileCredential.objects.get(kind="refresh").consumed_at)

    def test_logout_rechecks_access_deadline_at_mutation_not_before_body_validation(
        self,
    ):
        from . import session_views

        data = self.mobile(self.user)
        deadline = MobileCredential.objects.get(kind="access").expires_at
        clock = [timezone.now()]
        original = session_views.body

        def delayed(*args, **kwargs):
            result = original(*args, **kwargs)
            clock[0] = deadline
            return result

        with patch(
            "accounts.sessions.timezone.now", side_effect=lambda: clock[0]
        ), patch("accounts.session_views.body", side_effect=delayed):
            self.assertEqual(
                self.post_api(
                    "logout", {}, HTTP_AUTHORIZATION="Bearer " + data["access_token"]
                ).status_code,
                401,
            )
        self.assertIsNone(AuthSession.objects.get().revoked_at)


@override_settings(**SESSION_CONFIG)
class SessionContractFixtureTests(SessionFixtures, TestCase):
    def test_published_v1_keys_match_actual_server(self):
        import json
        from pathlib import Path

        fixtures = json.loads(
            (
                Path(__file__).resolve().parents[3]
                / "packages/api-contracts/auth-sessions-v1.fixtures.json"
            ).read_text()
        )
        user, _ = self.account()
        self.client = Client(enforce_csrf_checks=True)
        native = self.mobile(user)
        self.assertEqual(set(native), set(fixtures["mobile_success_keys"]))
        self.assertEqual(native["expires_in"], fixtures["access_lifetime_seconds"])
        self.assertEqual(
            set(self.get_me(native["access_token"]).json()),
            set(fixtures["me_success_keys"]),
        )
        _, browser = self.web(user)
        self.assertEqual(set(browser.json()), set(fixtures["web_success_keys"]))
        for key, value in fixtures["always_headers"].items():
            self.assertEqual(browser[key], value)
        error = self.get_me("invalid").json()["error"]
        self.assertEqual(set(error), set(fixtures["error_keys"]))


@override_settings(**SESSION_CONFIG)
class LoginFailureBudgetTests(SessionFixtures, TestCase):
    def test_successes_do_not_spend_or_reset_shared_failure_budget(self):
        from .models import AuthAbuseBucket

        self.client = Client(enforce_csrf_checks=True)
        user, _ = self.account()
        for index in range(4):
            self.assertEqual(
                self.post_api(
                    "mobile/login", {"email": user.email, "password": "wrong"}
                ).status_code,
                401,
            )
        for index in range(6):
            self.mobile(user)
        bucket = AuthAbuseBucket.objects.get(dimension="target", route="login:900")
        self.assertEqual(bucket.count, 4)
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": user.email, "password": "wrong"}
            ).status_code,
            401,
        )
        self.assertEqual(
            self.post_api(
                "mobile/login", {"email": user.email, "password": PASSWORD}
            ).status_code,
            429,
        )
        self.assertEqual(AuthSession.objects.count(), 6)


@override_settings(**SESSION_CONFIG)
class RefreshBudgetAndRetentionTests(SessionFixtures, TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.user, _ = self.account()

    def test_session_refresh_budget_cannot_be_bypassed_with_rotating_ip(self):
        data = self.mobile(self.user)
        now = timezone.now()
        with patch("accounts.sessions.timezone.now", return_value=now):
            for index in range(30):
                response = self.post_api(
                    "mobile/refresh",
                    {"refresh_token": data["refresh_token"]},
                    REMOTE_ADDR=f"192.0.2.{index+2}",
                )
                self.assertEqual(response.status_code, 200)
                data = response.json()
            response = self.post_api(
                "mobile/refresh",
                {"refresh_token": data["refresh_token"]},
                REMOTE_ADDR="192.0.2.99",
            )
            self.assertEqual(response.status_code, 429)
            self.assertEqual(
                MobileCredential.objects.filter(
                    kind="refresh", consumed_at__isnull=True
                ).count(),
                1,
            )
            self.assertEqual(self.get_me(data["access_token"]).status_code, 200)
        with patch(
            "accounts.sessions.timezone.now", return_value=now + timedelta(minutes=1)
        ):
            self.assertEqual(self.refresh(data["refresh_token"]).status_code, 200)

    def test_existing_cleanup_preserves_refresh_floor_and_cannot_resurrect_revoked_family(
        self,
    ):
        from .flow_cleanup import cleanup_flows

        data = self.mobile(self.user)
        next_data = self.refresh(data["refresh_token"]).json()
        cleanup_flows(100)
        self.assertEqual(
            MobileCredential.objects.filter(
                kind="refresh", consumed_at__isnull=False
            ).count(),
            1,
        )
        self.assertEqual(self.refresh(data["refresh_token"]).status_code, 401)
        cleanup_flows(100)
        self.assertEqual(self.get_me(next_data["access_token"]).status_code, 401)
        self.assertEqual(self.refresh(next_data["refresh_token"]).status_code, 401)
        row = AuthSession.objects.get()
        self.assertEqual(row.revocation_reason, "refresh_replay")
        with patch(
            "accounts.sessions.timezone.now", return_value=row.absolute_expires_at
        ):
            cleanup_flows(100)
            self.assertEqual(self.refresh(next_data["refresh_token"]).status_code, 401)
