"""Actual HTTP/PG owner-history integration; no privileged capability invented."""

import uuid
from datetime import timedelta
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.db import DatabaseError
from accounts.models import AuthSession
from django.utils import timezone
from .test_verification import VerificationFixtures, CONFIG
from .models import (
    Organization,
    OrganizationDraft,
    VerificationCase,
    RegistryEvent,
    RegistryReceipt,
    OrganizationAccess,
)
from access.models import NGOGrant


@override_settings(**CONFIG)
class WorkspaceTests(VerificationFixtures, TestCase):
    def setUp(self):
        self.setup_verification()
        self.verification = self.case()
        self.claim()

    def workspace(self, **params):
        return self.call("get", "workspace/", params)

    def test_owner_history_and_withdraw_are_actual_not_authority(self):
        with self.settings(PWC_LEGACY_ONBOARDING_TEST_EXERCISE=False):
            response = self.workspace()
            self.assertEqual(response.status_code, 200, response.content)
            item = response.json()["results"][0]
            self.assertEqual(item["id"], self.source["id"])
            self.assertTrue(item["can_withdraw"])
            self.assertFalse(item["verification"][0]["stale"])
            self.assertFalse(response.json()["administration_available"])
            self.assertFalse(response.json()["intake_available"])
            self.assertEqual(response["Cache-Control"], "no-store")
            # Real preserved withdrawal, without test exercise escape.
            result = self.call(
                "post", f"drafts/{item['id']}/withdraw/", {"revision": item["revision"]}
            )
            self.assertEqual(result.status_code, 200, result.content)
            current = self.workspace().json()["results"][0]
            self.assertEqual(current["state"], "withdrawn")
            self.assertFalse(current["can_withdraw"])
            self.assertTrue(current["verification"][0]["stale"])
            self.assertEqual(
                self.call(
                    "post", f"drafts/{item['id']}/withdraw/", {"revision": 1}
                ).status_code,
                409,
            )
            self.assertEqual(
                RegistryEvent.objects.filter(
                    draft_id=item["id"], action="withdraw"
                ).count(),
                1,
            )
            self.assertEqual(
                RegistryReceipt.objects.count(), 2
            )  # Historical create receipts only.
            self.assertFalse(OrganizationAccess.objects.exists())
            self.assertFalse(NGOGrant.objects.exists())
            self.assertEqual(
                self.call("post", "drafts/", {}, key=uuid.uuid4()).status_code, 503
            )

    def test_claim_target_details_are_never_joined_private_even_when_restricted(self):
        self.visible.workspace.state = "restricted"
        self.visible.workspace.save()
        item = self.workspace(kind="claim").json()["results"][0]
        self.assertIsNone(item["name"])
        self.assertIsNone(item["city"])
        self.assertIsNone(item["classification"])
        self.assertNotIn(
            self.visible.name.encode(), self.workspace(kind="claim").content
        )

    def test_other_person_has_no_rows_and_cannot_withdraw(self):
        result = self.call("get", "workspace/", token=self.other_token)
        self.assertEqual(result.json()["results"], [])
        self.assertEqual(
            self.call(
                "post",
                f"drafts/{self.source['id']}/withdraw/",
                {"revision": 1},
                token=self.other_token,
            ).status_code,
            404,
        )

    def test_latest_case_per_purpose_is_bounded_and_flag_respected(self):
        old = VerificationCase.objects.get(pk=self.verification["id"])
        old.state = "withdrawn"
        old.save()
        newer = self.case()
        response = self.workspace().json()
        self.assertEqual(
            [c["id"] for c in response["results"][0]["verification"]], [newer["id"]]
        )
        with self.settings(PWC_VERIFICATION_ENABLED=False):
            response = self.workspace().json()
            self.assertFalse(response["verification_available"])
            self.assertEqual(response["results"][0]["verification"], [])

    def test_state_filter_and_cursor_binding_without_other_tenant_counts(self):
        for i in range(21):
            OrganizationDraft.objects.create(
                organization=Organization.objects.create(
                    name=f"Fixture {i}", city="City", classification="unregistered"
                ),
                claimant=self.user,
                name=f"Synthetic {i}",
                city="City",
                classification="unregistered",
                match_key=f"{i:064d}",
            )
        first = self.workspace(state="draft").json()
        self.assertEqual(len(first["results"]), 20)
        cursor = first["next_cursor"]
        second = self.workspace(state="draft", cursor=cursor).json()
        self.assertEqual(len(second["results"]), 2)
        self.assertTrue(
            set(x["id"] for x in first["results"]).isdisjoint(
                x["id"] for x in second["results"]
            )
        )
        self.assertEqual(self.workspace(kind="claim", cursor=cursor).status_code, 400)
        self.assertEqual(
            self.workspace(state="withdrawn", cursor=cursor).status_code, 400
        )
        self.assertEqual(
            self.call(
                "get", "workspace/", {"cursor": cursor}, token=self.other_token
            ).status_code,
            400,
        )
        self.assertNotIn("count", first)

    def test_bad_filters_body_methods_and_unauthenticated(self):
        for params in (
            {"organization_id": str(self.visible.pk)},
            {"kind": "review"},
            {"state": "approved"},
            {"cursor": "forged"},
            {"kind": ["draft", "claim"]},
        ):
            self.assertEqual(self.workspace(**params).status_code, 400)
        self.assertEqual(self.call("post", "workspace/").status_code, 405)
        self.assertEqual(
            Client().get("/api/v1/registry/workspace/", secure=True).status_code, 401
        )
        self.assertEqual(
            self.call(
                "get", "workspace/", HTTP_ORIGIN="https://ngo.example"
            ).status_code,
            400,
        )

    def test_hold_inactive_expired_and_flag_denial(self):
        self.user.recovery_hold_state = "restricted"
        self.user.hold_set_at = timezone.now()
        self.user.hold_reason = "compromise"
        self.user.save()
        self.assertEqual(self.workspace().status_code, 403)
        self.user.recovery_hold_state = "clear"
        self.user.hold_set_at = None
        self.user.hold_reason = ""
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.workspace().status_code, 401)
        self.user.is_active = True
        self.user.save()
        with self.settings(PWC_REGISTRY_ENABLED=False):
            self.assertEqual(self.workspace().status_code, 503)
        with self.settings(PWC_ENVIRONMENT="production"):
            self.assertEqual(self.workspace().status_code, 503)
        AuthSession.objects.filter(user=self.user).update(
            revoked_at=timezone.now(), revocation_reason="logout"
        )
        self.assertEqual(self.workspace().status_code, 401)

    def test_database_failure_is_redacted_and_no_partial_projection(self):
        with patch(
            "organizations.workspace.history",
            side_effect=DatabaseError("private database detail"),
        ):
            # Patch the adapter binding, not a disconnected helper name.
            with patch(
                "organizations.workspace_views.history",
                side_effect=DatabaseError("private database detail"),
            ):
                result = self.workspace()
        self.assertEqual(result.status_code, 503)
        self.assertNotIn(b"private database detail", result.content)

    def test_expired_native_access_denied_without_projecting_history(self):
        with patch(
            "accounts.sessions.timezone.now",
            return_value=timezone.now() + timedelta(minutes=6),
        ):
            response = self.workspace()
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("results", response.json())

    def test_staff_and_legacy_admin_do_not_read_other_person_history(self):
        self.other.is_staff = True
        self.other.is_superuser = True
        self.other.save()
        OrganizationAccess.objects.create(
            organization=self.hidden, user=self.other, role="admin"
        )
        response = self.call("get", "workspace/", token=self.other_token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])
        self.assertNotIn(self.source["id"].encode(), response.content)

    def test_exact_reconciliation_is_owner_minimized_read_not_receipt(self):
        path = f"workspace/drafts/{self.source['id']}/"
        before = self.call("get", path)
        self.assertEqual(before.status_code, 200, before.content)
        self.assertEqual(
            before.json()["application"], self.workspace().json()["results"][0]
        )
        self.assertEqual(before["Cache-Control"], "no-store")
        foreign = self.call("get", path, token=self.other_token)
        missing = self.call(
            "get", f"workspace/drafts/{uuid.uuid4()}/", token=self.other_token
        )
        self.assertEqual(foreign.status_code, 404)
        foreign_error, missing_error = foreign.json()["error"], missing.json()["error"]
        foreign_error.pop("request_id")
        missing_error.pop("request_id")
        self.assertEqual(foreign_error, missing_error)
        self.assertEqual(self.call("post", path).status_code, 405)
        self.assertEqual(
            self.call("get", path, {"state": "withdrawn"}).status_code, 400
        )
        self.assertEqual(
            self.call("get", f"workspace/claims/{self.source['id']}/").status_code, 404
        )
        with self.settings(PWC_LEGACY_ONBOARDING_TEST_EXERCISE=False):
            result = self.call(
                "post", f"drafts/{self.source['id']}/withdraw/", {"revision": 1}
            )
            self.assertEqual(result.status_code, 200, result.content)
            # Caller may discard/loss the response. Current point read remains
            # available when the old list filter no longer contains the record.
            self.assertEqual(self.workspace(state="draft").json()["results"], [])
            after = self.call("get", path).json()
            self.assertEqual(after["application"]["state"], "withdrawn")
            self.assertEqual(after["application"]["revision"], 2)
            self.assertTrue(after["application"]["verification"][0]["stale"])
            self.assertFalse(after["administration_available"])
            self.assertNotIn("receipt", after)
            self.assertEqual(
                RegistryEvent.objects.filter(
                    draft_id=self.source["id"], action="withdraw"
                ).count(),
                1,
            )

    def test_point_read_rechecks_session_hold_and_deployment_gates(self):
        path = f"workspace/drafts/{self.source['id']}/"
        self.user.recovery_hold_state = "restricted"
        self.user.hold_set_at = timezone.now()
        self.user.hold_reason = "compromise"
        self.user.save()
        self.assertEqual(self.call("get", path).status_code, 403)
        self.user.recovery_hold_state = "clear"
        self.user.hold_set_at = None
        self.user.hold_reason = ""
        self.user.save()
        with self.settings(PWC_REGISTRY_ENABLED=False):
            self.assertEqual(self.call("get", path).status_code, 503)
        with self.settings(PWC_ENVIRONMENT="production"):
            self.assertEqual(self.call("get", path).status_code, 503)
        AuthSession.objects.filter(user=self.user).update(
            revoked_at=timezone.now(), revocation_reason="logout"
        )
        self.assertEqual(self.call("get", path).status_code, 401)

    def test_point_claim_does_not_disclose_private_target(self):
        row = self.workspace(kind="claim").json()["results"][0]
        result = self.call("get", f"workspace/claims/{row['id']}/")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(result.json()["application"], row)
        self.assertIsNone(row["name"])
        self.assertIsNone(row["city"])
        self.assertIsNone(row["classification"])
        self.assertFalse(OrganizationAccess.objects.exists())
        self.assertFalse(NGOGrant.objects.exists())
