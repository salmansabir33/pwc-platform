"""04B synthetic preparation: no files, reviewers or authority; actual PostgreSQL."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from unittest.mock import patch
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    transaction,
)
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from accounts.models import User, AuthSession
from accounts.session_authentication import PersonalAuthentication
from .test_registry import RegistryFixtures, CONFIG as REGISTRY_CONFIG
from .models import (
    VerificationCase,
    EvidencePreparation,
    VerificationEvent,
    VerificationReceipt,
    OrganizationWorkspace,
    OrganizationAccess,
)
from access.models import NGOGrant

CONFIG = dict(REGISTRY_CONFIG, PWC_VERIFICATION_ENABLED=True)
ROOT = "/api/v1/verification/"


class VerificationFixtures(RegistryFixtures):
    def setup_verification(self):
        self.setup_registry()
        self.source = self.draft()

    def vcall(self, method, path, data=None, *, key=None, token=None, **headers):
        headers.setdefault("HTTP_AUTHORIZATION", "Bearer " + (token or self.token))
        if key is not None:
            headers["HTTP_IDEMPOTENCY_KEY"] = str(key)
        return getattr(Client(), method)(
            ROOT + path,
            data=data or {},
            content_type="application/json",
            secure=True,
            **headers,
        )

    def payload(self, **overrides):
        return dict(
            source_kind="draft",
            source_id=self.source["id"],
            source_revision=1,
            purpose="organization_eligibility",
            **overrides,
        )

    def case(self, payload=None, **extra):
        response = self.vcall(
            "post", "cases/", payload or self.payload(), key=uuid.uuid4(), **extra
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def marker(self, case):
        response = self.vcall(
            "post",
            f"cases/{case['id']}/preparation/",
            {"case_revision": case["revision"], "prepared_offline": False},
            key=uuid.uuid4(),
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()


@override_settings(**CONFIG)
class VerificationTests(VerificationFixtures, TestCase):
    def setUp(self):
        self.setup_verification()

    def test_case_tracks_and_purposes_do_not_establish_any_authority(self):
        a = self.case()
        data = self.payload()
        data["purpose"] = "representative_mandate"
        b = self.case(data)
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(a["track"], "unregistered")
        self.assertFalse(OrganizationAccess.objects.exists())
        self.assertFalse(NGOGrant.objects.exists())
        self.assertEqual(
            OrganizationWorkspace.objects.get(
                organization_id=a["organization_id"]
            ).state,
            "provisional",
        )

    def test_registered_claim_lane_uses_public_category_not_eligibility(self):
        claim = self.claim().json()
        case = self.case(
            {
                "source_kind": "claim",
                "source_id": claim["id"],
                "source_revision": 1,
                "purpose": "organization_eligibility",
            }
        )
        self.assertEqual(case["track"], "registered")
        self.assertEqual(case["state"], "draft")
        self.assertEqual(
            OrganizationWorkspace.objects.get(organization=self.visible).state,
            "verified",
        )
        self.assertFalse(NGOGrant.objects.exists())

    def test_hidden_target_cannot_supply_current_private_category(self):
        claim = self.claim().json()
        OrganizationWorkspace.objects.filter(organization=self.visible).update(
            state="restricted"
        )
        response = self.vcall(
            "post",
            "cases/",
            {
                "source_kind": "claim",
                "source_id": claim["id"],
                "source_revision": 1,
                "purpose": "organization_eligibility",
            },
            key=uuid.uuid4(),
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(VerificationCase.objects.exists())

    def test_requirements_are_unapproved_not_a_document_rubric(self):
        case = self.case()
        result = self.vcall("get", f"cases/{case['id']}/requirements/").json()
        self.assertEqual(result["accepted_evidence_classes"], [])
        self.assertFalse(result["file_intake_available"])
        self.assertFalse(result["review_available"])
        self.assertEqual(result["rubric_status"], "unapproved")
        self.assertEqual(result["submission_effect"], "preparation_record_only")

    def test_preparation_replacement_withdrawal_and_history_snapshots(self):
        case = self.case()
        marker = self.marker(case)
        path = f"cases/{case['id']}/preparation/{marker['id']}/"
        response = self.vcall(
            "patch", path, {"case_revision": 2, "revision": 1, "prepared_offline": True}
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["revision"], 2)
        self.assertTrue(response.json()["prepared_offline"])
        self.assertEqual(self.vcall("get", path).json()["id"], marker["id"])
        response = self.vcall(
            "post",
            path + "withdraw/",
            {"case_revision": 3, "revision": 2, "prepared_offline": True},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "withdrawn")
        history = self.vcall("get", f"cases/{case['id']}/history/").json()["results"]
        self.assertEqual(sorted(x["revision"] for x in history), [1, 2, 3, 4])
        self.assertEqual(
            {x["prepared_offline"] for x in history if x["preparation_id"]},
            {False, True},
        )
        self.assertTrue(all("filename" not in x and "actor" not in x for x in history))

    def test_submission_is_preparation_only_and_freezes_markers(self):
        case = self.case()
        marker = self.marker(case)
        response = self.vcall("post", f"cases/{case['id']}/submit/", {"revision": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["state"], "submitted")
        self.assertEqual(
            self.vcall(
                "patch",
                f"cases/{case['id']}/preparation/{marker['id']}/",
                {"case_revision": 3, "revision": 1, "prepared_offline": True},
            ).status_code,
            409,
        )
        self.assertFalse(NGOGrant.objects.exists())
        self.assertEqual(
            OrganizationWorkspace.objects.get(
                organization_id=case["organization_id"]
            ).state,
            "provisional",
        )
        self.assertEqual(
            self.vcall("post", f"cases/{case['id']}/withdraw/", {"revision": 3}).json()[
                "state"
            ],
            "withdrawn",
        )
        self.assertEqual(
            self.vcall(
                "post", f"cases/{case['id']}/submit/", {"revision": 4}
            ).status_code,
            409,
        )

    def test_stale_source_blocks_mutation_but_not_withdrawal(self):
        case = self.case()
        self.call("post", f"drafts/{self.source['id']}/withdraw/", {"revision": 1})
        self.assertEqual(
            self.vcall(
                "post", f"cases/{case['id']}/submit/", {"revision": 1}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.vcall(
                "post",
                f"cases/{case['id']}/preparation/",
                {"case_revision": 1, "prepared_offline": False},
                key=uuid.uuid4(),
            ).status_code,
            409,
        )
        self.assertEqual(
            self.vcall(
                "post", f"cases/{case['id']}/withdraw/", {"revision": 1}
            ).status_code,
            200,
        )

    def test_cross_owner_source_impersonation_and_direct_objects(self):
        self.assertEqual(
            self.vcall(
                "post",
                "cases/",
                self.payload(),
                key=uuid.uuid4(),
                token=self.other_token,
            ).status_code,
            404,
        )
        case = self.case()
        marker = self.marker(case)
        for suffix in (
            "",
            "requirements/",
            "history/",
            "preparation/",
            f"preparation/{marker['id']}/",
            f"evidence/{marker['id']}/download/",
        ):
            self.assertEqual(
                self.vcall(
                    "get", f"cases/{case['id']}/" + suffix, token=self.other_token
                ).status_code,
                404,
            )
        self.assertEqual(
            self.vcall("get", "cases/", token=self.other_token).json()["results"], []
        )
        self.assertEqual(
            self.vcall(
                "post",
                f"cases/{case['id']}/withdraw/",
                {"revision": 2},
                token=self.other_token,
            ).status_code,
            404,
        )

    def test_cross_case_preparation_and_download_isolation(self):
        a = self.case()
        marker = self.marker(a)
        data = self.payload()
        data["purpose"] = "representative_mandate"
        b = self.case(data)
        for suffix in (
            f"preparation/{marker['id']}/",
            f"evidence/{marker['id']}/download/",
        ):
            self.assertEqual(
                self.vcall("get", f"cases/{b['id']}/" + suffix).status_code, 404
            )
        self.assertEqual(
            self.vcall(
                "patch",
                f"cases/{b['id']}/preparation/{marker['id']}/",
                {"case_revision": 1, "revision": 1, "prepared_offline": True},
            ).status_code,
            404,
        )

    def test_file_intake_is_always_unavailable_without_parsing_or_storage(self):
        case = self.case()
        marker = self.marker(case)
        with patch(
            "organizations.registry_views.RegistryParser.parse",
            side_effect=AssertionError("must not parse bytes"),
        ):
            response = self.vcall(
                "post",
                f"cases/{case['id']}/evidence/",
                {"filename": "secret.html", "content": "<script>private</script>"},
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "EVIDENCE_UNAVAILABLE")
        self.assertNotIn("secret.html", response.content.decode())
        self.assertEqual(
            self.vcall(
                "get", f"cases/{case['id']}/evidence/{marker['id']}/download/"
            ).status_code,
            503,
        )
        self.assertEqual(VerificationEvent.objects.count(), 2)
        self.assertEqual(EvidencePreparation.objects.count(), 1)

    def test_no_reviewer_bootstrap_staff_board_legacy_or_synthetic_shortcut(self):
        case = self.case()
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        OrganizationAccess.objects.create(
            user=self.user, organization_id=case["organization_id"], role="admin"
        )
        self.assertEqual(self.vcall("get", "reviewer-queue/").status_code, 503)
        for command in (
            "assign",
            "approve",
            "reject",
            "needs-information",
            "appeal",
            "suspend",
            "revoke",
            "grant",
            "publish",
        ):
            self.assertEqual(
                self.vcall(
                    "post",
                    f"cases/{case['id']}/{command}/",
                    {"reviewer_id": str(self.user.pk)},
                ).status_code,
                404,
            )
        self.assertFalse(NGOGrant.objects.exists())
        self.assertEqual(VerificationCase.objects.get(pk=case["id"]).state, "draft")

    def test_closed_inputs_reject_filenames_asserted_validity_urls_and_xss(self):
        for field in (
            "filename",
            "url",
            "storage_key",
            "contents",
            "hash",
            "evidence_class",
            "approved",
            "reviewer_id",
            "reason",
            "notes",
        ):
            body = self.payload()
            body[field] = "<script>secret</script>"
            response = self.vcall("post", "cases/", body, key=uuid.uuid4())
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("secret", response.content.decode())
        self.assertFalse(VerificationCase.objects.exists())

    def test_strict_scalar_types_and_no_invalid_review_states(self):
        for value in (True, "1", 0):
            data = self.payload()
            data["source_revision"] = value
            self.assertEqual(
                self.vcall("post", "cases/", data, key=uuid.uuid4()).status_code, 400
            )
        case = self.case()
        self.assertEqual(
            self.vcall(
                "post",
                f"cases/{case['id']}/preparation/",
                {"case_revision": 1, "prepared_offline": "true"},
                key=uuid.uuid4(),
            ).status_code,
            400,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            VerificationCase.objects.filter(pk=case["id"]).update(state="approved")

    def test_own_duplicate_and_purpose_bound_retry_keys(self):
        key = uuid.uuid4()
        response = self.vcall("post", "cases/", self.payload(), key=key)
        case = response.json()
        self.assertEqual(
            self.vcall("post", "cases/", self.payload(), key=key).json()["id"],
            case["id"],
        )
        self.assertEqual(
            self.vcall("post", "cases/", self.payload(), key=uuid.uuid4()).status_code,
            409,
        )
        data = self.payload()
        data["purpose"] = "representative_mandate"
        self.assertEqual(self.vcall("post", "cases/", data, key=key).status_code, 409)
        self.vcall("post", f"cases/{case['id']}/withdraw/", {"revision": 1})
        self.assertEqual(
            self.vcall("post", "cases/", self.payload(), key=key).json()["state"],
            "withdrawn",
        )
        self.assertEqual(VerificationEvent.objects.count(), 2)

    def test_preparation_retry_returns_current_state_and_never_resurrects(self):
        case = self.case()
        key = uuid.uuid4()
        path = f"cases/{case['id']}/preparation/"
        data = {"case_revision": 1, "prepared_offline": False}
        first = self.vcall("post", path, data, key=key).json()
        self.assertEqual(
            self.vcall("post", path, data, key=key).json()["id"], first["id"]
        )
        self.vcall(
            "post",
            path + first["id"] + "/withdraw/",
            {"case_revision": 2, "revision": 1, "prepared_offline": False},
        )
        self.assertEqual(
            self.vcall("post", path, data, key=key).json()["state"], "withdrawn"
        )
        self.assertEqual(VerificationEvent.objects.count(), 3)

    def test_stale_revision_and_case_revision_are_conflicts(self):
        case = self.case()
        marker = self.marker(case)
        self.assertEqual(
            self.vcall(
                "post", f"cases/{case['id']}/submit/", {"revision": 1}
            ).status_code,
            409,
        )
        self.assertEqual(
            self.vcall(
                "patch",
                f"cases/{case['id']}/preparation/{marker['id']}/",
                {"case_revision": 2, "revision": 3, "prepared_offline": True},
            ).status_code,
            409,
        )
        self.assertEqual(VerificationEvent.objects.count(), 2)

    def test_audit_failure_rolls_back_case_and_receipt(self):
        with patch(
            "organizations.verification.VerificationEvent.objects.create",
            side_effect=DatabaseError("private database detail"),
        ):
            response = self.vcall("post", "cases/", self.payload(), key=uuid.uuid4())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private database detail", response.content.decode())
        self.assertFalse(VerificationCase.objects.exists())
        self.assertFalse(VerificationReceipt.objects.exists())

    def test_audit_failure_rolls_back_preparation_and_parent_revision(self):
        case = self.case()
        with patch(
            "organizations.verification.VerificationEvent.objects.create",
            side_effect=DatabaseError(),
        ):
            response = self.vcall(
                "post",
                f"cases/{case['id']}/preparation/",
                {"case_revision": 1, "prepared_offline": True},
                key=uuid.uuid4(),
            )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(VerificationCase.objects.get(pk=case["id"]).revision, 1)
        self.assertFalse(EvidencePreparation.objects.exists())
        self.assertEqual(VerificationReceipt.objects.count(), 1)

    def test_database_history_receipt_immutability(self):
        self.case()
        for model in (VerificationEvent, VerificationReceipt):
            with self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.all().delete()
            with self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.update(created_at=timezone.now())

    def test_conditional_unique_case_and_preparation_in_database(self):
        case = self.case()
        self.marker(case)
        with self.assertRaises(IntegrityError), transaction.atomic():
            EvidencePreparation.objects.create(case_id=case["id"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            VerificationCase.objects.create(
                claimant=self.user,
                organization_id=case["organization_id"],
                draft_id=self.source["id"],
                source_revision=1,
                purpose="organization_eligibility",
                track="unregistered",
            )

    def test_hold_inactive_revoked_and_anonymous_deny_all_access(self):
        case = self.case()
        self.user.recovery_hold_state = "review_required"
        self.user.hold_set_at = timezone.now()
        self.user.hold_reason = "compromise"
        self.user.save()
        for method, path, data in [
            ("get", "cases/", None),
            ("post", f"cases/{case['id']}/submit/", {"revision": 1}),
            ("post", f"cases/{case['id']}/evidence/", {}),
        ]:
            self.assertEqual(self.vcall(method, path, data).status_code, 403)
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.vcall("get", "cases/").status_code, 401)
        self.assertEqual(Client().get(ROOT + "cases/", secure=True).status_code, 401)
        AuthSession.objects.filter(user=self.other).update(
            revoked_at=timezone.now(), revocation_reason="compromise"
        )
        self.assertEqual(
            self.vcall("get", "cases/", token=self.other_token).status_code, 401
        )

    def test_completion_expiry_rolls_back_new_case(self):
        auth = PersonalAuthentication.authenticate
        calls = 0

        def expire(adapter, request):
            nonlocal calls
            calls += 1
            return None if calls == 2 else auth(adapter, request)

        with patch.object(PersonalAuthentication, "authenticate", expire):
            self.assertEqual(
                self.vcall(
                    "post", "cases/", self.payload(), key=uuid.uuid4()
                ).status_code,
                401,
            )
        self.assertFalse(VerificationCase.objects.exists())

    def test_flags_production_and_parser_guards(self):
        for config in (
            {"PWC_VERIFICATION_ENABLED": False},
            {"PWC_REGISTRY_ENABLED": False},
            {"PWC_ENVIRONMENT": "production"},
        ):
            with self.settings(**config):
                self.assertEqual(self.vcall("get", "cases/").status_code, 503)
        for suffix in ("?private=true", "?cursor=forged", "?cursor=a&cursor=b"):
            self.assertEqual(self.vcall("get", "cases/" + suffix).status_code, 400)
        self.assertEqual(
            self.vcall(
                "get", "cases/", HTTP_ORIGIN="https://ngo.pwc.invalid"
            ).status_code,
            400,
        )

    def test_marker_edit_strict_revision_and_closed_fields(self):
        case = self.case()
        marker = self.marker(case)
        path = f"cases/{case['id']}/preparation/{marker['id']}/"
        for field, value in (
            ("revision", True),
            ("revision", "1"),
            ("case_revision", "2"),
            ("prepared_offline", 1),
            ("filename", "private"),
        ):
            data = {"revision": 1, "case_revision": 2, "prepared_offline": True}
            data[field] = value
            response = self.vcall("patch", path, data)
            self.assertEqual(response.status_code, 400)
            self.assertNotIn("private", response.content.decode())
        self.assertEqual(VerificationEvent.objects.count(), 2)

    def test_json_body_query_method_and_retry_key_bounds(self):
        self.assertEqual(self.vcall("post", "cases/", self.payload()).status_code, 400)
        case = self.case()
        path = f"cases/{case['id']}/"
        self.assertEqual(
            self.vcall("get", path + "?cursor=unexpected").status_code, 400
        )
        for method in ("post", "patch", "delete"):
            self.assertEqual(self.vcall(method, path, {"revision": 1}).status_code, 405)
        client = Client()
        for body in (
            '{"revision":1,"revision":1}',
            '{"revision":1,"notes":"' + "x" * 8200 + '"}',
        ):
            response = client.post(
                ROOT + path + "submit/",
                data=body,
                content_type="application/json",
                secure=True,
                HTTP_AUTHORIZATION="Bearer " + self.token,
            )
            self.assertEqual(response.status_code, 400)
        self.assertEqual(
            client.post(
                ROOT + path + "submit/",
                data="revision=1",
                content_type="application/x-www-form-urlencoded",
                secure=True,
                HTTP_AUTHORIZATION="Bearer " + self.token,
            ).status_code,
            415,
        )

    def test_owner_pagination_is_bounded_and_context_bound(self):
        case = self.case()
        base = VerificationCase.objects.get(pk=case["id"])
        VerificationCase.objects.bulk_create(
            [
                VerificationCase(
                    claimant=self.user,
                    organization=base.organization,
                    draft=base.draft,
                    source_revision=1,
                    purpose="organization_eligibility",
                    track="unregistered",
                    state="withdrawn",
                )
                for _ in range(22)
            ]
        )
        page = self.vcall("get", "cases/").json()
        self.assertEqual(len(page["results"]), 20)
        cursor = page["next_cursor"]
        self.assertTrue(cursor)
        self.assertEqual(
            len(self.vcall("get", "cases/?cursor=" + cursor).json()["results"]), 3
        )
        self.assertEqual(
            self.vcall(
                "get", "cases/?cursor=" + cursor, token=self.other_token
            ).status_code,
            400,
        )
        self.assertEqual(
            self.vcall(
                "get", f"cases/{case['id']}/history/?cursor=" + cursor
            ).status_code,
            400,
        )

    def test_cookie_origin_csrf_and_no_legacy_login_fallback(self):
        client, _ = self.web(self.user)
        self.assertEqual(
            client.post(
                ROOT + "cases/",
                self.payload(),
                content_type="application/json",
                secure=True,
                HTTP_HOST="ngo.pwc.invalid",
            ).status_code,
            403,
        )
        csrf = client.get(
            "/api/v1/auth/csrf/", secure=True, HTTP_HOST="ngo.pwc.invalid"
        ).json()["csrf_token"]
        response = client.post(
            ROOT + "cases/",
            self.payload(),
            content_type="application/json",
            secure=True,
            HTTP_HOST="ngo.pwc.invalid",
            HTTP_ORIGIN="https://ngo.pwc.invalid",
            HTTP_X_CSRFTOKEN=csrf,
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertIn("Authorization", response["Vary"])


@override_settings(**CONFIG)
class VerificationConcurrencyTests(VerificationFixtures, TransactionTestCase):
    def setUp(self):
        self.setup_verification()

    def race(self, action):
        barrier = Barrier(2)

        def worker(i):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return action(i)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(worker, range(2)))

    def test_duplicate_case_race(self):
        codes = self.race(
            lambda _: (
                self.vcall(
                    "post", "cases/", self.payload(), key=uuid.uuid4()
                ).status_code
            )
        )
        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(VerificationEvent.objects.count(), 1)

    def test_duplicate_submission_race(self):
        case = self.case()
        codes = self.race(
            lambda _: (
                self.vcall(
                    "post", f"cases/{case['id']}/submit/", {"revision": 1}
                ).status_code
            )
        )
        self.assertEqual(sorted(codes), [200, 409])
        self.assertEqual(VerificationEvent.objects.count(), 2)

    def test_exact_retry_race(self):
        key = uuid.uuid4()
        ids = self.race(
            lambda _: self.vcall("post", "cases/", self.payload(), key=key).json()["id"]
        )
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(VerificationReceipt.objects.count(), 1)

    def test_replacement_race_and_parent_revision(self):
        case = self.case()
        marker = self.marker(case)
        codes = self.race(
            lambda _: (
                self.vcall(
                    "patch",
                    f"cases/{case['id']}/preparation/{marker['id']}/",
                    {"case_revision": 2, "revision": 1, "prepared_offline": True},
                ).status_code
            )
        )
        self.assertEqual(sorted(codes), [200, 409])
        self.assertEqual(VerificationEvent.objects.count(), 3)
        self.assertEqual(EvidencePreparation.objects.get(pk=marker["id"]).revision, 2)

    def test_submit_versus_withdraw(self):
        case = self.case()
        codes = self.race(
            lambda i: (
                self.vcall(
                    "post",
                    f"cases/{case['id']}/{'submit' if i else 'withdraw'}/",
                    {"revision": 1},
                ).status_code
            )
        )
        self.assertEqual(sorted(codes), [200, 409])
        self.assertEqual(VerificationCase.objects.get(pk=case["id"]).revision, 2)

    def test_source_withdrawal_versus_submission(self):
        case = self.case()
        codes = self.race(
            lambda i: (
                self.call(
                    "post", f"drafts/{self.source['id']}/withdraw/", {"revision": 1}
                ).status_code
                if i
                else self.vcall(
                    "post", f"cases/{case['id']}/submit/", {"revision": 1}
                ).status_code
            )
        )
        self.assertEqual(codes[1], 200)
        self.assertIn(codes[0], (200, 409))
        self.assertFalse(NGOGrant.objects.exists())

    def test_committed_hold_before_case_lock_denies_create(self):
        ready = Event()
        auth = PersonalAuthentication.authenticate

        def observe(adapter, request):
            ready.set()
            return auth(adapter, request)

        def request():
            close_old_connections()
            try:
                return self.vcall(
                    "post", "cases/", self.payload(), key=uuid.uuid4()
                ).status_code
            finally:
                close_old_connections()

        with (
            ThreadPoolExecutor(max_workers=1) as pool,
            patch.object(PersonalAuthentication, "authenticate", observe),
        ):
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=self.user.pk)
                future = pool.submit(request)
                self.assertTrue(ready.wait(timeout=10))
                self.assertFalse(future.done())
                user.recovery_hold_state = "review_required"
                user.hold_set_at = timezone.now()
                user.hold_reason = "compromise"
                user.save()
            self.assertEqual(future.result(timeout=10), 403)
        self.assertFalse(VerificationCase.objects.exists())
