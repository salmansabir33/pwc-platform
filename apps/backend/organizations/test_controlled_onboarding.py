"""Synthetic storage/preflight tests and actual default-deny rollout HTTP tests.
No test provisions real operators or claims evidence authenticity/activation.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.db import DatabaseError, IntegrityError, close_old_connections, transaction
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from .test_verification import VerificationFixtures, CONFIG
from .models import (
    ControlledOnboardingRecord as Record,
    ControlledOnboardingRevision as Revision,
    ControlledOnboardingEvent as Event,
    OfflineVerificationAttestation as Attestation,
    OrganizationAccess,
    OrganizationDraft,
    VerificationCase,
)
from .controlled_onboarding import preflight, PreflightConflict, command_available
from .onboarding_policy import POLICY
from .controlled_contract import ENTRIES

ROLLOUT = dict(CONFIG, PWC_LEGACY_ONBOARDING_TEST_EXERCISE=False)
ROOT = "/api/v1/controlled-onboarding/"


@override_settings(**ROLLOUT)
class RolloutTests(VerificationFixtures, TestCase):
    def setUp(self):
        with self.settings(PWC_LEGACY_ONBOARDING_TEST_EXERCISE=True):
            self.setup_verification()
            self.existing_case = self.case()

    def request(self, method, suffix, data=None, token=None, **headers):
        headers.setdefault("HTTP_AUTHORIZATION", "Bearer " + (token or self.token))
        return getattr(self.client, method)(
            ROOT + suffix,
            data=data or {},
            content_type="application/json",
            secure=True,
            **headers,
        )

    def test_default_rollout_denies_self_service_even_with_old_flags_enabled(self):
        for path, data in [
            (
                "drafts/",
                {"name": "New", "classification": "unregistered", "city": "City"},
            ),
            ("claims/", {"organization_id": str(self.visible.pk)}),
            (f"drafts/{self.source['id']}/submit/", {"revision": 1}),
        ]:
            response = self.call("post", path, data, key=uuid.uuid4())
            self.assertEqual(response.status_code, 503, response.content)
            self.assertEqual(
                response.json()["error"]["code"], "SELF_SERVICE_UNAVAILABLE"
            )
        self.assertEqual(
            self.call(
                "patch", f"drafts/{self.source['id']}/", {"revision": 1}
            ).status_code,
            503,
        )
        self.assertEqual(OrganizationDraft.objects.count(), 1)
        self.assertEqual(
            self.vcall("post", "cases/", self.payload(), key=uuid.uuid4()).status_code,
            503,
        )
        self.assertEqual(
            self.vcall(
                "post", f"cases/{self.existing_case['id']}/submit/", {"revision": 1}
            ).status_code,
            503,
        )
        self.assertEqual(VerificationCase.objects.count(), 1)

    def test_owned_history_read_and_withdrawal_are_preserved(self):
        for suffix in ("", "history/"):
            self.assertEqual(
                self.call("get", f"drafts/{self.source['id']}/" + suffix).status_code,
                200,
            )
        self.assertEqual(
            self.call(
                "post", f"drafts/{self.source['id']}/withdraw/", {"revision": 1}
            ).status_code,
            200,
        )
        self.assertEqual(
            self.vcall(
                "post", f"cases/{self.existing_case['id']}/withdraw/", {"revision": 1}
            ).status_code,
            200,
        )
        self.assertEqual(
            self.call(
                "get", f"drafts/{self.source['id']}/", token=self.other_token
            ).status_code,
            404,
        )

    def test_historical_test_exercise_is_not_a_development_or_production_escape(self):
        for env in ("development", "staging", "production"):
            with self.settings(
                PWC_ENVIRONMENT=env, PWC_LEGACY_ONBOARDING_TEST_EXERCISE=True
            ):
                self.assertEqual(
                    self.call("post", "drafts/", {}, key=uuid.uuid4()).status_code, 503
                )

    def test_requirements_are_generic_policy_not_user_entitlements(self):
        result = self.request("get", "requirements/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json(), POLICY)
        self.assertEqual(result["Cache-Control"], "no-store")
        self.assertNotIn("operator_id", result.json())

    def test_all_privileged_readers_and_commands_are_unavailable_without_enumeration(
        self,
    ):
        for _, path, method in ENTRIES:
            if path == "requirements/":
                continue
            path = path.replace("{pk}", str(uuid.uuid4()))
            response = self.request(
                method,
                path,
                None if method == "get" else {"approved": True, "document": "secret"},
            )
            self.assertEqual(response.status_code, 503, response.content)
            self.assertNotIn("secret", response.content.decode())
        self.assertFalse(Record.objects.exists())

    def test_staff_board_legacy_admin_cannot_bootstrap_operator_or_officer(self):
        from django.contrib.auth.models import Group

        self.user.is_staff = self.user.is_superuser = True
        self.user.save()
        self.user.groups.add(
            Group.objects.create(name="PWC Super Admin / Board / verification officer")
        )
        OrganizationAccess.objects.create(
            user=self.user, organization=self.visible, role="admin"
        )
        for command in (
            "create",
            "approve",
            "assign",
            "invite",
            "accept",
            "grant",
            "read",
        ):
            self.assertFalse(command_available(self.user, command))
        self.assertEqual(self.request("post", "records/").status_code, 503)
        self.assertEqual(
            self.request("post", f"records/{uuid.uuid4()}/approve/").status_code, 503
        )
        self.assertFalse(Record.objects.exists())
        with (
            self.settings(PWC_LEGACY_ONBOARDING_TEST_EXERCISE=True),
            patch(
                "organizations.controlled_views.command_available", return_value=True
            ),
        ):
            self.assertEqual(self.request("post", "records/").status_code, 503)
            self.assertFalse(Record.objects.exists())

    def test_unavailable_adapters_never_parse_or_persist_files_or_contact_data(self):
        with patch(
            "organizations.registry_views.RegistryParser.parse",
            side_effect=AssertionError("No parsing"),
        ):
            self.assertEqual(
                self.request(
                    "post",
                    "records/",
                    {"file": "private.html", "email": "secret@example.invalid"},
                ).status_code,
                503,
            )
        self.assertFalse(Revision.objects.exists())
        self.assertFalse(Attestation.objects.exists())
        self.assertFalse(Event.objects.exists())

    def test_auth_hold_revocation_transport_queries_csrf_and_methods(self):
        self.assertEqual(
            self.client.get(ROOT + "requirements/", secure=True).status_code, 401
        )
        self.assertEqual(
            self.request("get", "requirements/?private=true").status_code, 400
        )
        self.assertEqual(
            self.request(
                "get", "requirements/", HTTP_ORIGIN="https://ngo.pwc.invalid"
            ).status_code,
            400,
        )
        self.assertEqual(self.request("post", "requirements/").status_code, 405)
        client, _ = self.web(self.user)
        self.assertEqual(
            client.post(
                ROOT + "records/",
                {},
                content_type="application/json",
                secure=True,
                HTTP_HOST="ngo.pwc.invalid",
            ).status_code,
            403,
        )
        self.user.recovery_hold_state = "review_required"
        self.user.hold_set_at = timezone.now()
        self.user.hold_reason = "compromise"
        self.user.save()
        self.assertEqual(self.request("get", "requirements/").status_code, 403)
        self.assertEqual(self.request("post", "records/").status_code, 403)
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.request("post", "records/").status_code, 401)


class PreflightTests(TestCase):
    def proposal(self, **overrides):
        data = dict(
            state="submitted",
            revision=2,
            expected_revision=2,
            command="approve",
            initiator="a",
            actor="b",
            attestation_purposes=["organization_eligibility", "representative_mandate"],
        )
        data.update(overrides)
        return preflight(**data)

    def test_independent_preflight_has_no_database_or_authorization_effect(self):
        with self.assertNumQueries(0):
            result = self.proposal()
        self.assertEqual((result.next_state, result.next_revision), ("approved", 3))
        self.assertFalse(command_available(None, "approve"))
        self.assertFalse(Record.objects.exists())

    def test_self_review_stale_missing_lanes_and_terminal_states_rejected(self):
        for data in (
            {"actor": "a"},
            {"expected_revision": 1},
            {"expected_revision": True},
            {"state": "approved"},
            {"state": "withdrawn"},
            {"command": "activate"},
            {"attestation_purposes": ["organization_eligibility"]},
            {"actor": None},
        ):
            with self.assertRaises(PreflightConflict):
                self.proposal(**data)

    def test_return_correction_reject_withdraw_graph(self):
        self.assertEqual(self.proposal(command="return").next_state, "returned")
        self.assertEqual(
            self.proposal(state="returned", command="edit", actor="a").next_state,
            "returned",
        )
        with self.assertRaises(PreflightConflict):
            self.proposal(state="approved", command="edit", actor="a")
        self.assertEqual(
            self.proposal(state="returned", command="submit", actor="a").next_state,
            "submitted",
        )
        self.assertEqual(self.proposal(command="reject").next_state, "rejected")
        self.assertEqual(
            self.proposal(command="withdraw", actor="a").next_state, "withdrawn"
        )
        with self.assertRaises(PreflightConflict):
            self.proposal(command="withdraw")


@override_settings(**ROLLOUT)
class StorageTests(VerificationFixtures, TestCase):
    def setUp(self):
        self.setup_registry()
        self.record = Record.objects.create(initiator=self.user)
        self.snapshot = Revision.objects.create(
            record=self.record,
            revision=1,
            organization_name="Synthetic",
            city="Faisalabad",
            classification="unregistered",
            nominee_reference="NOMINEE_TEST",
            nomination_reference="NOMINATION_TEST",
            recorded_by=self.user,
        )

    def test_no_self_approval_or_unsupported_states_in_database(self):
        for data in (
            {"reviewer": self.user, "state": "approved"},
            {"state": "approved"},
            {"state": "verified"},
            {"revision": 0},
        ):
            with self.assertRaises(IntegrityError), transaction.atomic():
                Record.objects.filter(pk=self.record.pk).update(**data)
        self.assertFalse(OrganizationAccess.objects.exists())

    def test_cannot_replace_initiator_to_bypass_independence(self):
        with self.assertRaises(DatabaseError), transaction.atomic():
            Record.objects.filter(pk=self.record.pk).update(initiator=self.other)

    def test_history_references_and_attestations_are_immutable(self):
        attestation = Attestation.objects.create(
            snapshot=self.snapshot,
            purpose="organization_eligibility",
            evidence_reference="EVIDENCE_TEST",
            method_reference="METHOD_TEST",
            examined_at=timezone.now(),
            attestor=self.user,
        )
        from accounts.models import AuthSession

        event = Event.objects.create(
            snapshot=self.snapshot,
            actor=self.user,
            session=AuthSession.objects.filter(user=self.user).first(),
            action="recorded",
        )
        for obj in (self.snapshot, attestation, event):
            with self.assertRaises(DatabaseError), transaction.atomic():
                type(obj).objects.filter(pk=obj.pk).delete()
            with self.assertRaises(DatabaseError), transaction.atomic():
                type(obj).objects.filter(pk=obj.pk).update(created_at=timezone.now())

    def test_url_numeric_and_markup_are_not_reference_handles(self):
        for handle in (
            "https://private.invalid/file",
            "<script>private</script>",
            "123456789",
            "a" * 65,
        ):
            with self.assertRaises(DatabaseError), transaction.atomic():
                Revision.objects.create(
                    record=self.record,
                    revision=2,
                    organization_name="Synthetic",
                    city="City",
                    classification="registered",
                    nominee_reference=handle,
                    nomination_reference="NOM_TEST",
                    recorded_by=self.user,
                )

    def test_partial_snapshot_and_attestation_roll_back_with_audit_failure(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            snap = Revision.objects.create(
                record=self.record,
                revision=2,
                organization_name="Synthetic",
                city="City",
                classification="registered",
                nominee_reference="NOM_TEST",
                nomination_reference="NOM_TEST",
                recorded_by=self.user,
            )
            Attestation.objects.create(
                snapshot=snap,
                purpose="representative_mandate",
                evidence_reference="EVIDENCE_TEST",
                method_reference="METHOD_TEST",
                examined_at=timezone.now(),
                attestor=self.user,
            )
            Event.objects.create(
                snapshot=snap,
                actor=self.user,
                session_id=uuid.uuid4(),
                action="recorded",
            )
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertEqual(Revision.objects.count(), 1)
        self.assertFalse(Attestation.objects.exists())


@override_settings(**ROLLOUT)
class StorageRaceTests(VerificationFixtures, TransactionTestCase):
    def setUp(self):
        self.setup_registry()

    def test_duplicate_revision_transaction_race(self):
        record = Record.objects.create(initiator=self.user)
        barrier = Barrier(2)

        def worker(_):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    with transaction.atomic():
                        Revision.objects.create(
                            record_id=record.pk,
                            revision=1,
                            organization_name="Synthetic",
                            city="City",
                            classification="unregistered",
                            nominee_reference="NOM_TEST",
                            nomination_reference="NOM_TEST",
                            recorded_by_id=self.user.pk,
                        )
                    return "created"
                except IntegrityError:
                    return "conflict"
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, range(2)))
        self.assertEqual(sorted(outcomes), ["conflict", "created"])
        self.assertEqual(Revision.objects.filter(record=record).count(), 1)
