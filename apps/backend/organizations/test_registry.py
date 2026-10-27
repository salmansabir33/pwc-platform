"""04A PostgreSQL takeover/isolation/state/atomicity/race regression suite."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.db import (
    DatabaseError,
    IntegrityError,
    close_old_connections,
    connection,
    transaction,
)
from django.test import Client, TestCase, TransactionTestCase, override_settings
from accounts.models import AuthSession, AuthAbuseBucket, User
from accounts.test_sessions import SessionFixtures, SESSION_CONFIG
from access.models import NGOGrant
from .models import (
    Organization,
    OrganizationWorkspace,
    OrganizationAccess,
    OrganizationDraft,
    OrganizationClaim,
    RegistryEvent,
    RegistryReceipt,
)

CONFIG = dict(
    SESSION_CONFIG,
    PWC_REGISTRY_ENABLED=True,
    PWC_ENVIRONMENT="test",
    PWC_LEGACY_ONBOARDING_TEST_EXERCISE=True,
)
ROOT = "/api/v1/registry/"
FORM = {
    "name": "Synthetic Welfare",
    "classification": "unregistered",
    "city": "Faisalabad",
}


class RegistryFixtures(SessionFixtures):
    def setup_registry(self):
        self.user, _ = self.account("applicant")
        self.other, _ = self.account("rival")
        self.token = self.mobile(self.user)["access_token"]
        self.other_token = self.mobile(self.other)["access_token"]
        self.visible = Organization.objects.create(
            name="Public Synthetic Welfare",
            city="Faisalabad",
            classification="registered",
        )
        OrganizationWorkspace.objects.create(
            organization=self.visible, state="verified"
        )
        self.hidden = Organization.objects.create(
            name="Hidden Synthetic Welfare", classification="registered"
        )
        OrganizationWorkspace.objects.create(
            organization=self.hidden, state="restricted"
        )

    def call(self, method, path, data=None, *, token=None, key=None, **headers):
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

    def draft(self, **overrides):
        response = self.call(
            "post", "drafts/", dict(FORM, **overrides), key=uuid.uuid4()
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def claim(self, **extra):
        return self.call(
            "post",
            "claims/",
            {"organization_id": str(self.visible.pk)},
            key=uuid.uuid4(),
            **extra,
        )


@override_settings(**CONFIG)
class RegistryTests(RegistryFixtures, TestCase):
    def setUp(self):
        self.setup_registry()

    def test_create_is_not_authority_or_publication(self):
        draft = self.draft()
        self.assertFalse(OrganizationAccess.objects.exists())
        self.assertFalse(NGOGrant.objects.exists())
        self.assertEqual(
            OrganizationWorkspace.objects.get(
                organization_id=draft["organization_id"]
            ).state,
            "provisional",
        )
        self.assertEqual(RegistryEvent.objects.count(), 1)
        response = self.client.get(
            "/api/v1/organizations/" + draft["organization_id"] + "/"
        )
        self.assertEqual(response.status_code, 404)

    def test_lifecycle_and_own_history(self):
        d = self.draft()
        path = f"drafts/{d['id']}/"
        updated = self.call("patch", path, dict(FORM, name="Updated", revision=1))
        self.assertEqual(updated.status_code, 200, updated.content)
        sent = self.call("post", path + "submit/", {"revision": 2})
        self.assertEqual(sent.json()["state"], "submitted")
        self.assertEqual(
            self.call("patch", path, dict(FORM, revision=3)).status_code, 409
        )
        withdrawn = self.call("post", path + "withdraw/", {"revision": 3})
        self.assertEqual(withdrawn.json()["state"], "withdrawn")
        self.assertEqual(
            self.call("post", path + "withdraw/", {"revision": 4}).status_code, 409
        )
        history = self.call("get", path + "history/").json()["results"]
        self.assertEqual(sorted(e["revision"] for e in history), [1, 2, 3, 4])
        self.assertTrue(
            all(set(e) == {"id", "action", "revision", "created_at"} for e in history)
        )

    def test_claim_does_not_transfer_or_modify_existing_record(self):
        before = (self.visible.name, self.visible.city)
        response = self.claim()
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["state"], "pending")
        self.visible.refresh_from_db()
        self.assertEqual((self.visible.name, self.visible.city), before)
        self.assertFalse(OrganizationAccess.objects.exists())
        self.assertFalse(NGOGrant.objects.exists())
        self.assertEqual(
            OrganizationWorkspace.objects.get(organization=self.visible).state,
            "verified",
        )

    def test_two_rival_claimants_are_segregated_not_first_claim_wins(self):
        first = self.claim().json()
        rival = self.claim(token=self.other_token)
        self.assertEqual(rival.status_code, 201)
        self.assertEqual(len(self.call("get", "claims/").json()["results"]), 1)
        for suffix in ("", "history/"):
            self.assertEqual(
                self.call(
                    "get", f"claims/{first['id']}/" + suffix, token=self.other_token
                ).status_code,
                404,
            )
        self.assertEqual(
            self.call(
                "post",
                f"claims/{first['id']}/withdraw/",
                {"revision": 1},
                token=self.other_token,
            ).status_code,
            404,
        )

    def test_hidden_missing_and_provisional_claims_are_indistinguishable(self):
        for pk in (self.hidden.pk, uuid.uuid4(), self.draft()["organization_id"]):
            response = self.call(
                "post", "claims/", {"organization_id": str(pk)}, key=uuid.uuid4()
            )
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "NOT_FOUND")
        self.assertEqual(OrganizationClaim.objects.count(), 0)

    def test_own_draft_only_even_for_staff_board_and_legacy_admin(self):
        d = self.draft()
        self.other.is_staff = self.other.is_superuser = True
        self.other.save()
        OrganizationAccess.objects.create(
            organization_id=d["organization_id"], user=self.other, role="admin"
        )
        for method, suffix, data in (
            ("get", "", None),
            ("patch", "", dict(FORM, revision=1)),
            ("post", "submit/", {"revision": 1}),
            ("get", "history/", None),
        ):
            self.assertEqual(
                self.call(
                    method, f"drafts/{d['id']}/" + suffix, data, token=self.other_token
                ).status_code,
                404,
            )
        self.assertEqual(
            self.call("get", "drafts/", token=self.other_token).json()["results"], []
        )

    def test_contacts_aliases_classification_never_confer_authority(self):
        d = self.draft(
            contact_email=self.other.email,
            aliases=[self.visible.name],
            legal_name=self.visible.name,
            classification="registered",
        )
        self.assertEqual(d["state"], "draft")
        self.assertFalse(OrganizationAccess.objects.exists())
        self.assertFalse(NGOGrant.objects.exists())

    def test_same_actor_duplicate_normalization_and_no_global_name_lock(self):
        self.draft(name="Ａ  Welfare")
        response = self.call(
            "post", "drafts/", dict(FORM, name="a welfare"), key=uuid.uuid4()
        )
        self.assertEqual(response.status_code, 409)
        response = self.call(
            "post",
            "drafts/",
            dict(FORM, name="a welfare"),
            key=uuid.uuid4(),
            token=self.other_token,
        )
        self.assertEqual(response.status_code, 201)

    def test_duplicate_claim_withdraw_and_fresh_request(self):
        c = self.claim().json()
        self.assertEqual(self.claim().status_code, 409)
        self.assertEqual(
            self.call(
                "post", f"claims/{c['id']}/withdraw/", {"revision": 1}
            ).status_code,
            200,
        )
        self.assertEqual(self.claim().status_code, 201)

    def test_retry_key_owner_payload_operation_binding_and_current_state(self):
        key = uuid.uuid4()
        first = self.call("post", "drafts/", FORM, key=key).json()
        retry = self.call("post", "drafts/", FORM, key=key)
        self.assertEqual(retry.json()["id"], first["id"])
        self.assertEqual(RegistryEvent.objects.count(), 1)
        self.assertEqual(
            self.call("post", "drafts/", dict(FORM, name="Other"), key=key).status_code,
            409,
        )
        self.assertEqual(
            self.call(
                "post", "claims/", {"organization_id": str(self.visible.pk)}, key=key
            ).status_code,
            409,
        )
        self.call("post", f"drafts/{first['id']}/withdraw/", {"revision": 1})
        self.assertEqual(
            self.call("post", "drafts/", FORM, key=key).json()["state"], "withdrawn"
        )
        self.assertEqual(
            self.call(
                "post", "drafts/", FORM, key=key, token=self.other_token
            ).status_code,
            201,
        )

    def test_required_idempotency_key_and_strict_fields(self):
        for data, key in (
            (FORM, None),
            (dict(FORM, is_admin=True), uuid.uuid4()),
            (dict(FORM, state="verified"), uuid.uuid4()),
            (dict(FORM, name="\u202eSpoof"), uuid.uuid4()),
            (dict(FORM, aliases=["A"] * 6), uuid.uuid4()),
            (dict(FORM, name=5), uuid.uuid4()),
        ):
            self.assertEqual(
                self.call("post", "drafts/", data, key=key).status_code, 400
            )
        self.assertFalse(OrganizationDraft.objects.exists())

    def test_stale_and_malformed_revision(self):
        d = self.draft()
        for revision, status in ((2, 409), ("1", 400), (True, 400), (0, 400)):
            self.assertEqual(
                self.call(
                    "post", f"drafts/{d['id']}/submit/", {"revision": revision}
                ).status_code,
                status,
            )
        self.assertEqual(RegistryEvent.objects.count(), 1)

    def test_audit_failure_rolls_back_identity_draft_receipt(self):
        count = Organization.objects.count()
        with patch(
            "organizations.registry.RegistryEvent.objects.create",
            side_effect=DatabaseError("private DB detail"),
        ):
            response = self.call("post", "drafts/", FORM, key=uuid.uuid4())
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private DB detail", response.content.decode())
        self.assertEqual(Organization.objects.count(), count)
        self.assertFalse(OrganizationDraft.objects.exists())
        self.assertFalse(RegistryReceipt.objects.exists())

    def test_audit_failure_rolls_back_transition(self):
        d = self.draft()
        with patch(
            "organizations.registry.RegistryEvent.objects.create",
            side_effect=DatabaseError(),
        ):
            self.assertEqual(
                self.call(
                    "post", f"drafts/{d['id']}/submit/", {"revision": 1}
                ).status_code,
                503,
            )
        self.assertEqual(OrganizationDraft.objects.get(pk=d["id"]).revision, 1)
        self.assertEqual(OrganizationDraft.objects.get(pk=d["id"]).state, "draft")

    def test_history_and_receipts_immutable_in_database(self):
        self.draft()
        for model in (RegistryEvent, RegistryReceipt):
            with self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.all().delete()
            with self.assertRaises(DatabaseError), transaction.atomic():
                model.objects.update(
                    created_at=__import__(
                        "django.utils.timezone", fromlist=["now"]
                    ).now()
                )

    def test_database_duplicate_constraints(self):
        d = OrganizationDraft.objects.get(pk=self.draft()["id"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrganizationDraft.objects.create(
                organization=self.hidden,
                claimant=self.user,
                name="Bypass",
                classification="unregistered",
                match_key=d.match_key,
            )
        self.claim()
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrganizationClaim.objects.create(
                organization=self.visible, claimant=self.user
            )

    def test_search_unicode_whitespace_location_and_four_field_projection(self):
        self.visible.name = "Straße Ａ  Welfare"
        self.visible.save()
        result = self.call("get", "search/?q=STRASSE%20a&city=faisalabad")
        self.assertEqual(result.status_code, 200, result.content)
        self.assertEqual(len(result.json()["results"]), 1)
        self.assertEqual(
            set(result.json()["results"][0]), {"id", "name", "city", "classification"}
        )
        self.assertEqual(self.call("get", "search/?q=hidden").json()["results"], [])
        self.assertEqual(
            self.call("get", "search/?q=STRASSE&city=Karachi").json()["results"], []
        )

    def test_public_keyset_pagination_not_first_500_scan(self):
        for i in range(23):
            org = Organization.objects.create(
                name=f"Welfare {i}", classification="registered"
            )
            OrganizationWorkspace.objects.create(organization=org, state="verified")
        first = self.call("get", "search/?q=welfare").json()
        self.assertEqual(len(first["results"]), 20)
        second = self.call(
            "get", "search/?q=welfare&cursor=" + first["next_cursor"]
        ).json()
        self.assertEqual(len(second["results"]), 4)
        self.assertFalse(
            {r["id"] for r in first["results"]} & {r["id"] for r in second["results"]}
        )
        self.assertEqual(
            self.call(
                "get", "search/?q=other&cursor=" + first["next_cursor"]
            ).status_code,
            400,
        )
        self.assertEqual(
            self.call(
                "get",
                "search/?q=welfare&cursor=" + first["next_cursor"],
                token=self.other_token,
            ).status_code,
            400,
        )

    def test_invalid_query_cursor_and_control_input(self):
        for query in (
            "q=a",
            "q=wel&q=other",
            "q=wel&private=true",
            "q=wel&cursor=forged",
            "q=%E2%80%AEevil",
        ):
            self.assertEqual(self.call("get", "search/?" + query).status_code, 400)

    def test_hold_inactive_revoked_and_missing_principals_deny(self):
        from django.utils import timezone

        # Use real hold state constraints, not a fabricated invalid row.
        self.user.recovery_hold_state = "review_required"
        self.user.hold_set_at = timezone.now()
        self.user.hold_reason = "compromise"
        self.user.save()
        for method, route, data in [
            ("get", "drafts/", None),
            ("post", "drafts/", FORM),
        ]:
            self.assertEqual(
                self.call(method, route, data, key=uuid.uuid4()).status_code, 403
            )
        self.user.is_active = False
        self.user.save()
        self.assertEqual(self.call("get", "drafts/").status_code, 401)
        self.assertEqual(Client().get(ROOT + "drafts/", secure=True).status_code, 401)
        AuthSession.objects.filter(user=self.other).update(
            revoked_at=timezone.now(), revocation_reason="compromise"
        )
        self.assertEqual(
            self.call("get", "drafts/", token=self.other_token).status_code, 401
        )

    def test_default_off_and_production_remain_disabled(self):
        for settings in (
            {"PWC_REGISTRY_ENABLED": False},
            {"PWC_ENVIRONMENT": "production"},
        ):
            with self.settings(**settings):
                self.assertEqual(self.call("get", "drafts/").status_code, 503)
                self.assertEqual(
                    self.call("post", "drafts/", FORM, key=uuid.uuid4()).status_code,
                    503,
                )

    def test_cookie_csrf_and_mixed_transport(self):
        client, _ = self.web(self.user)
        response = client.post(
            ROOT + "drafts/",
            FORM,
            content_type="application/json",
            secure=True,
            HTTP_HOST="ngo.pwc.invalid",
        )
        self.assertEqual(response.status_code, 403)
        token = client.get(
            "/api/v1/auth/csrf/", secure=True, HTTP_HOST="ngo.pwc.invalid"
        ).json()["csrf_token"]
        response = client.post(
            ROOT + "drafts/",
            FORM,
            content_type="application/json",
            secure=True,
            HTTP_HOST="ngo.pwc.invalid",
            HTTP_ORIGIN="https://ngo.pwc.invalid",
            HTTP_X_CSRFTOKEN=token,
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 201, response.content)
        response = client.get(
            ROOT + "drafts/",
            secure=True,
            HTTP_HOST="ngo.pwc.invalid",
            HTTP_AUTHORIZATION="Bearer " + self.token,
        )
        self.assertEqual(response.status_code, 400)

    def test_abuse_budget_and_security_headers(self):
        AuthAbuseBucket.objects.filter(route="registry:900").update(count=30)
        # First call creates the route bucket; next exhaust it through real calls.
        for _ in range(31):
            response = self.call("get", "drafts/")
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(response["Referrer-Policy"], "no-referrer")
        self.assertIn("Authorization", response["Vary"])

    def test_duplicate_json_and_browser_bearer_are_rejected(self):
        response = Client().post(
            ROOT + "drafts/",
            data='{"name":"A","name":"B","classification":"registered"}',
            content_type="application/json",
            secure=True,
            HTTP_AUTHORIZATION="Bearer " + self.token,
            HTTP_IDEMPOTENCY_KEY=str(uuid.uuid4()),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            self.call(
                "get", "drafts/", HTTP_ORIGIN="https://ngo.pwc.invalid"
            ).status_code,
            400,
        )

    def test_expired_at_completion_rolls_back_mutation(self):
        from accounts.session_authentication import PersonalAuthentication

        authenticate = PersonalAuthentication.authenticate
        calls = 0

        def expire(adapter, request):
            nonlocal calls
            calls += 1
            if calls == 2:
                return None
            return authenticate(adapter, request)

        with patch.object(PersonalAuthentication, "authenticate", expire):
            self.assertEqual(
                self.call("post", "drafts/", FORM, key=uuid.uuid4()).status_code, 401
            )
        self.assertFalse(OrganizationDraft.objects.exists())
        self.assertFalse(RegistryEvent.objects.exists())

    def test_unimplemented_review_grant_evidence_and_members_commands(self):
        d = self.draft()
        for suffix in (
            "approve/",
            "reject/",
            "needs-information/",
            "evidence/",
            "grants/",
            "members/",
            "finance/",
        ):
            self.assertEqual(
                self.call("post", f"drafts/{d['id']}/" + suffix, {}).status_code, 404
            )


@override_settings(**CONFIG)
class RegistryConcurrencyTests(RegistryFixtures, TransactionTestCase):
    def setUp(self):
        self.setup_registry()

    def race(self, function):
        barrier = Barrier(2)

        def worker():
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return function()
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(lambda _: worker(), range(2)))

    def test_concurrent_duplicate_creates(self):
        codes = self.race(
            lambda: self.call("post", "drafts/", FORM, key=uuid.uuid4()).status_code
        )
        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(OrganizationDraft.objects.count(), 1)
        self.assertEqual(RegistryEvent.objects.count(), 1)

    def test_concurrent_exact_retry(self):
        key = uuid.uuid4()
        ids = self.race(
            lambda: self.call("post", "drafts/", FORM, key=key).json()["id"]
        )
        self.assertEqual(ids[0], ids[1])
        self.assertEqual(RegistryEvent.objects.count(), 1)

    def test_concurrent_claims(self):
        codes = self.race(lambda: self.claim().status_code)
        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(OrganizationClaim.objects.count(), 1)

    def test_withdraw_transition_race(self):
        d = self.draft()
        codes = self.race(
            lambda: (
                self.call(
                    "post", f"drafts/{d['id']}/withdraw/", {"revision": 1}
                ).status_code
            )
        )
        self.assertEqual(sorted(codes), [200, 409])
        self.assertEqual(RegistryEvent.objects.count(), 2)


class RegistryMigrationTests(TransactionTestCase):
    def test_legacy_upgrade_preserves_ids_roles_and_normalizes_without_publishing(self):
        from django.db.migrations.executor import MigrationExecutor
        from django.db.migrations.exceptions import IrreversibleError

        executor = MigrationExecutor(connection)
        old = [("organizations", "0002_alter_organizationaccess_id_and_more")]
        leaves = executor.loader.graph.leaf_nodes()
        executor.migrate(old)
        try:
            apps = executor.loader.project_state(old).apps
            org = apps.get_model("organizations", "Organization").objects.create(
                name="Straße Ａ  Welfare",
                city="Ｆaisalabad",
                classification="registered",
            )
            pk = org.pk
            executor = MigrationExecutor(connection)
            executor.migrate(leaves)
            current = Organization.objects.get(pk=pk)
            self.assertEqual(current.lookup_name, "strasse a welfare")
            self.assertEqual(current.lookup_city, "faisalabad")
            self.assertFalse(
                OrganizationWorkspace.objects.filter(organization=current).exists()
            )
            self.assertFalse(OrganizationDraft.objects.exists())
            user = User.objects.create(username="migration-only")
            OrganizationDraft.objects.create(
                organization=current,
                claimant=user,
                name="Preserved",
                classification="registered",
                match_key="a" * 64,
            )
            with self.assertRaises(IrreversibleError):
                MigrationExecutor(connection).migrate(old)
            self.assertTrue(OrganizationDraft.objects.exists())
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate(leaves)


@override_settings(**CONFIG)
class RegistryAuthorityRaceTests(RegistryFixtures, TransactionTestCase):
    def setUp(self):
        self.setup_registry()

    def test_committed_hold_before_user_lock_denies_create(self):
        from threading import Event
        from django.utils import timezone
        from accounts.session_authentication import PersonalAuthentication

        ready = Event()
        authenticate = PersonalAuthentication.authenticate

        def observe(adapter, request):
            ready.set()
            return authenticate(adapter, request)

        def request():
            close_old_connections()
            try:
                return self.call("post", "drafts/", FORM, key=uuid.uuid4()).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=1) as pool:
            with patch.object(PersonalAuthentication, "authenticate", observe):
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
        self.assertFalse(OrganizationDraft.objects.exists())
        self.assertFalse(RegistryEvent.objects.exists())

    def test_submit_against_withdraw_has_one_winning_revision(self):
        draft = self.draft()
        barrier = Barrier(2)

        def request(command):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                return self.call(
                    "post", f"drafts/{draft['id']}/{command}/", {"revision": 1}
                ).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(request, ["submit", "withdraw"]))
        self.assertEqual(sorted(codes), [200, 409])
        self.assertEqual(OrganizationDraft.objects.get(pk=draft["id"]).revision, 2)
        self.assertEqual(RegistryEvent.objects.count(), 2)
