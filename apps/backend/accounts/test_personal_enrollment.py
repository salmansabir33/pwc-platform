"""Full existing enrollment contracts over HTTPS Django clients + PostgreSQL.

Disposable .invalid mail uses the approved locmem dispatcher, never real delivery
or identities. Account ownership is not natural-person or Founder verification.
"""

from datetime import timedelta
from unittest.mock import patch
import pyotp
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from access.models import NGOGrant
from organizations.models import OrganizationAccess
from .models import User, UserContact, AuthSession, MfaFactor, SecurityEvent
from .test_mfa import MFA_CONFIG
from .test_sessions import SessionFixtures, NGO
from .test_registration import PASSWORD, NEW_PASSWORD


@override_settings(**MFA_CONFIG)
class PersonalEnrollmentJourneyTests(SessionFixtures, TestCase):
    def setUp(self):
        self.now = timezone.now()
        clock = patch("accounts.mfa.timezone.now", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.founder = Client(enforce_csrf_checks=True)
        self.verifier = Client(enforce_csrf_checks=True)

    def post_web(self, client, path, data):
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST=NGO).json()[
            "csrf_token"
        ]
        return self.post_api(
            path,
            data,
            client=client,
            host=NGO,
            HTTP_ORIGIN=f"https://{NGO}",
            HTTP_X_CSRFTOKEN=csrf,
        )

    def register(self, client, email, password):
        response = self.post_web(client, "registration/request", {"email": email})
        self.assertEqual(response.status_code, 202)
        flow = response.json()
        self.assertFalse(User.objects.filter(email=email).exists())
        proof = self.mail_proof(flow)
        self.assertNotIn(proof, str(flow))
        response = self.post_web(
            client,
            "registration/confirm",
            {
                "flow_id": flow["flow_id"],
                "proof": proof,
                "password": password,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.get_me(client=client, host=NGO).status_code, 401)
        user = User.objects.get(email=email)
        self.assertTrue(user.check_password(password))
        self.assertNotEqual(user.password, password)
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertFalse(user.groups.exists() or user.user_permissions.exists())
        self.assertTrue(
            UserContact.objects.filter(user=user, verified_at__isnull=False).exists()
        )
        return user, flow, proof

    def start_factor(self, client, user, password):
        response = self.post_web(
            client,
            "assurance/intents",
            {
                "operation": "mfa.enroll",
                "context": {"kind": "personal", "id": str(user.pk)},
                "command": {},
            },
        )
        self.assertEqual(response.status_code, 201)
        response = self.post_web(
            client,
            "step-up",
            {"intent_id": response.json()["intent_id"], "password": password},
        )
        self.assertEqual(response.status_code, 200)
        response = self.post_web(
            client,
            "mfa/enrollment/request",
            {"assurance_proof": response.json()["assurance_proof"]},
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def activate_factor(self, client, factor):
        response = self.post_web(
            client,
            "mfa/enrollment/confirm",
            {
                "enrollment_id": factor["enrollment_id"],
                "code": pyotp.TOTP(factor["secret"]).at(self.now),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "active")
        self.assertEqual(len(set(response.json()["recovery_codes"])), 10)
        return response.json()["recovery_codes"]

    def test_two_people_complete_registration_password_first_mfa_and_explicit_login_without_grants(
        self,
    ):
        first, _, _ = self.register(
            self.founder, "founder-fixture@example.invalid", PASSWORD
        )
        second, _, _ = self.register(
            self.verifier, "verifier-fixture@example.invalid", NEW_PASSWORD
        )
        self.assertNotEqual(first.pk, second.pk)
        self.web(first, password=PASSWORD, client=self.founder)
        self.web(second, password=NEW_PASSWORD, client=self.verifier)
        a = self.start_factor(self.founder, first, PASSWORD)
        b = self.start_factor(self.verifier, second, NEW_PASSWORD)
        self.assertNotEqual(a["secret"], b["secret"])
        cross = self.post_web(
            self.verifier,
            "mfa/enrollment/confirm",
            {
                "enrollment_id": a["enrollment_id"],
                "code": pyotp.TOTP(a["secret"]).at(self.now),
            },
        )
        self.assertGreaterEqual(cross.status_code, 400)
        self.assertFalse(MfaFactor.objects.filter(user=second, state="active").exists())
        ac, bc = (
            self.activate_factor(self.founder, a),
            self.activate_factor(self.verifier, b),
        )
        self.assertTrue(set(ac).isdisjoint(bc))
        self.now += timedelta(seconds=31)
        for user, password, factor in ((first, PASSWORD, a), (second, NEW_PASSWORD, b)):
            fresh = Client(enforce_csrf_checks=True)
            login = self.post_web(
                fresh, "web/login", {"email": user.email, "password": password}
            )
            self.assertEqual(login.status_code, 202)
            self.assertEqual(self.get_me(client=fresh, host=NGO).status_code, 401)
            challenge = login.json()
            response = self.post_web(
                fresh,
                "web/mfa/confirm",
                {
                    "challenge_id": challenge["challenge_id"],
                    "preauth_control": challenge["preauth_control"],
                    "method": "totp",
                    "code": pyotp.TOTP(factor["secret"]).at(self.now),
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                self.get_me(client=fresh, host=NGO).json()["user"]["id"], str(user.pk)
            )
            listing = fresh.get("/api/v1/auth/sessions/", secure=True, HTTP_HOST=NGO)
            self.assertEqual(listing.status_code, 200)
            returned = {r["id"] for r in listing.json()["results"]}
            foreign = {str(s.pk) for s in AuthSession.objects.exclude(user=user)}
            self.assertTrue(returned.isdisjoint(foreign))
        self.assertFalse(
            NGOGrant.objects.exists() or OrganizationAccess.objects.exists()
        )
        self.assertEqual(User.objects.count(), 2)
        self.assertEqual(MfaFactor.objects.filter(state="active").count(), 2)
        self.assertTrue(
            SecurityEvent.objects.filter(event="auth.mfa_activated").exists()
        )

    def test_duplicate_mailbox_and_replayed_proof_never_create_or_activate_another_identity(
        self,
    ):
        user, flow, proof = self.register(
            self.founder, "person@example.invalid", PASSWORD
        )
        replay = self.post_web(
            self.verifier,
            "registration/confirm",
            {"flow_id": flow["flow_id"], "proof": proof, "password": NEW_PASSWORD},
        )
        self.assertEqual(replay.status_code, 400)
        self.now += timedelta(seconds=61)
        duplicate = self.post_web(
            self.verifier, "registration/request", {"email": "PERSON@EXAMPLE.invalid"}
        )
        self.assertEqual(duplicate.status_code, 202)
        self.assertEqual(set(duplicate.json()), set(flow))
        self.assertEqual(User.objects.count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password(PASSWORD))
        self.assertFalse(AuthSession.objects.exists())

    def test_role_assignment_and_wrong_personal_context_are_rejected(self):
        for field in (
            "is_staff",
            "is_superuser",
            "role",
            "founder",
            "verifier",
            "user_id",
        ):
            response = self.post_web(
                self.founder,
                "registration/request",
                {"email": "person@example.invalid", field: True},
            )
            self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.exists())
        first, _, _ = self.register(self.founder, "one@example.invalid", PASSWORD)
        other, _, _ = self.register(self.verifier, "two@example.invalid", NEW_PASSWORD)
        self.web(first, client=self.founder)
        denied = self.post_web(
            self.founder,
            "assurance/intents",
            {
                "operation": "mfa.enroll",
                "context": {"kind": "personal", "id": str(other.pk)},
                "command": {},
            },
        )
        self.assertGreaterEqual(denied.status_code, 400)
        self.assertFalse(
            NGOGrant.objects.exists() or OrganizationAccess.objects.exists()
        )

    def test_password_recovery_revokes_only_owner_sessions_and_preserves_mfa_hold(self):
        first, _, _ = self.register(self.founder, "one@example.invalid", PASSWORD)
        other, _, _ = self.register(self.verifier, "two@example.invalid", NEW_PASSWORD)
        self.web(first, client=self.founder)
        self.web(other, password=NEW_PASSWORD, client=self.verifier)
        a = self.start_factor(self.founder, first, PASSWORD)
        self.activate_factor(self.founder, a)
        self.now += timedelta(seconds=61)
        flow = self.post_web(
            Client(enforce_csrf_checks=True),
            "password-reset/request",
            {"email": first.email},
        ).json()
        proof = self.mail_proof(flow)
        result = self.post_web(
            Client(enforce_csrf_checks=True),
            "password-reset/confirm",
            {"flow_id": flow["flow_id"], "proof": proof, "new_password": NEW_PASSWORD},
        )
        self.assertEqual(result.status_code, 204)
        self.assertEqual(self.get_me(client=self.founder, host=NGO).status_code, 401)
        self.assertEqual(
            self.get_me(client=self.verifier, host=NGO).json()["user"]["id"],
            str(other.pk),
        )
        first.refresh_from_db()
        self.assertTrue(first.check_password(NEW_PASSWORD))
        self.assertNotEqual(first.recovery_hold_state, "clear")
        self.assertTrue(MfaFactor.objects.filter(user=first, state="active").exists())
        self.assertFalse(
            NGOGrant.objects.exists() or OrganizationAccess.objects.exists()
        )
