"""Fictional fixtures only. No fixture loader/production seed or writer exists."""

import uuid
from datetime import timedelta
from unittest.mock import patch
from django.conf import settings
from django.core import signing
from django.db import IntegrityError, DatabaseError, connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, OrganizationWorkspace, OrganizationAccess
from django.contrib.auth import get_user_model
from .models import Opportunity
from .views import SALT

ROOT = "/api/v1/opportunities/"
FIELDS = {"id", "organization", "type", "title", "summary", "published_at"}


def organization(name="Fictional A", state="verified", city="Faisalabad"):
    owner = Organization.objects.create(
        name=name, city=city, classification="registered"
    )
    OrganizationWorkspace.objects.create(organization=owner, state=state)
    return owner


def opportunity(owner, state="PUBLISHED", **values):
    return Opportunity.objects.create(
        organization=owner,
        state=state,
        title=values.pop("title", "Fictional Welfare Role"),
        type=values.pop("type", "JOB"),
        summary="Fictional public summary",
        published_at=timezone.now() if state != "DRAFT" else None,
        withdrawn_at=timezone.now() if state == "WITHDRAWN" else None,
        **values,
    )


@override_settings(PWC_ENVIRONMENT="test", PWC_OPPORTUNITIES_TEST_EXERCISE=True)
class PublicOpportunityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.a = organization()
        self.b = organization("Fictional B", city="Lahore")
        self.visible = opportunity(self.a)

    def test_published_list_detail_and_explicit_projection(self):
        self.assertEqual(connection.vendor, "postgresql")
        result = self.client.get(ROOT)
        self.assertEqual(result.status_code, 200)
        value = result.json()["results"][0]
        self.assertEqual(set(value), FIELDS)
        self.assertEqual(
            set(value["organization"]), {"id", "name", "city", "classification"}
        )
        self.assertEqual(self.client.get(f"{ROOT}{self.visible.pk}/").json(), value)
        self.assertNotIn("count", result.json())
        for header, expected in {
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
        }.items():
            self.assertEqual(result[header], expected)
        self.assertTrue({"Cookie", "Authorization"} <= set(result["Vary"].split(", ")))

    def test_drafts_withdrawn_and_unknown_ids_share_not_found(self):
        hidden = [opportunity(self.a, "DRAFT"), opportunity(self.b, "WITHDRAWN")]
        hidden.append(type("Unknown", (), {"pk": uuid.uuid4()})())
        for row in hidden:
            response = self.client.get(f"{ROOT}{row.pk}/")
            self.assertEqual(response.status_code, 404)
            self.assertNotIn("title", response.json())
        self.assertEqual(len(self.client.get(ROOT).json()["results"]), 1)

    def test_all_nonpublic_ngo_states_and_missing_workspace_hide_records(self):
        for state in OrganizationWorkspace.State.values:
            if state == "verified":
                continue
            OrganizationWorkspace.objects.filter(organization=self.a).update(
                state=state
            )
            self.assertEqual(self.client.get(ROOT).json()["results"], [])
            self.assertEqual(
                self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 404
            )
        OrganizationWorkspace.objects.filter(organization=self.a).delete()
        self.assertEqual(self.client.get(ROOT).json()["results"], [])
        self.assertEqual(self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 404)

    def test_withdrawal_removes_previously_visible_list_and_detail(self):
        self.assertEqual(self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 200)
        Opportunity.objects.filter(pk=self.visible.pk).update(
            state="WITHDRAWN", withdrawn_at=timezone.now()
        )
        self.assertEqual(self.client.get(ROOT).json()["results"], [])
        self.assertEqual(self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 404)

    def test_cross_ngo_filter_never_expands_to_private_records(self):
        other = opportunity(self.b)
        private = opportunity(self.b, "DRAFT")
        for owner, expected in [(self.a, self.visible), (self.b, other)]:
            values = self.client.get(ROOT, {"organization_id": str(owner.pk)}).json()[
                "results"
            ]
            self.assertEqual([row["id"] for row in values], [str(expected.pk)])
        OrganizationWorkspace.objects.filter(organization=self.b).update(
            state="restricted"
        )
        response = self.client.get(ROOT, {"organization_id": str(self.b.pk)})
        self.assertEqual(response.json()["results"], [])
        self.assertNotIn(str(private.pk).encode(), response.content)

    def test_credentials_staff_superuser_and_ngo_role_do_not_widen_visibility(self):
        hidden = opportunity(self.b, "DRAFT")
        user = get_user_model().objects.create_user(
            username="fictional-staff", is_staff=True, is_superuser=True
        )
        OrganizationAccess.objects.create(user=user, organization=self.b, role="admin")
        self.client.force_authenticate(user=user)
        self.assertEqual(self.client.get(f"{ROOT}{hidden.pk}/").status_code, 404)
        self.client.force_authenticate(user=None)
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "fictional-invalid"
        response = self.client.get(ROOT, HTTP_AUTHORIZATION="Bearer fictional-invalid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

    def test_public_reads_do_not_resolve_ambient_identity_or_private_grants(self):
        self.client.cookies[settings.SESSION_COOKIE_NAME] = "fictional-invalid"
        with patch(
            "accounts.sessions.locate",
            side_effect=AssertionError("Identity lookup forbidden"),
        ):
            self.assertEqual(self.client.get(ROOT).status_code, 200)
            self.assertEqual(
                self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 200
            )

    def test_all_types_unicode_title_search_city_and_combined_filters(self):
        for kind in ("INTERNSHIP", "PROJECT"):
            value = opportunity(self.b, type=kind, title="Fictional اردو Welfare")
            response = self.client.get(
                ROOT,
                {
                    "q": "  اردو  ＷＥＬＦＡＲＥ ",
                    "city": "ＬＡＨＯＲＥ",
                    "type": kind,
                    "organization_id": str(self.b.pk),
                },
            )
            self.assertEqual(
                [row["id"] for row in response.json()["results"]], [str(value.pk)]
            )
        self.assertEqual(self.client.get(ROOT, {"q": "missing"}).json()["results"], [])
        self.assertEqual(
            self.client.get(ROOT, {"city": "missing"}).json()["results"], []
        )

    def test_pagination_is_bounded_stable_unique_and_rechecks_visibility(self):
        Opportunity.objects.all().delete()
        rows = [opportunity(self.a, id=uuid.UUID(int=i)) for i in range(1, 23)]
        first = self.client.get(ROOT).json()
        self.assertEqual(len(first["results"]), 20)
        self.assertEqual(
            [row["id"] for row in first["results"]], [str(row.pk) for row in rows[:20]]
        )
        Opportunity.objects.filter(pk=rows[20].pk).update(
            state="WITHDRAWN", withdrawn_at=timezone.now()
        )
        second = self.client.get(ROOT, {"cursor": first["next_cursor"]}).json()
        self.assertEqual([row["id"] for row in second["results"]], [str(rows[21].pk)])
        self.assertIsNone(second["next_cursor"])
        OrganizationWorkspace.objects.filter(organization=self.a).update(
            state="restricted"
        )
        self.assertEqual(
            self.client.get(ROOT, {"cursor": first["next_cursor"]}).json()["results"],
            [],
        )

    def test_cursor_filter_binding_tampering_expiry_and_invalid_payloads(self):
        for i in range(21):
            opportunity(self.a, title=f"Fictional {i}")
        token = self.client.get(ROOT).json()["next_cursor"]
        for changed in [
            {"q": "changed"},
            {"city": "changed"},
            {"type": "PROJECT"},
            {"organization_id": str(self.b.pk)},
        ]:
            self.assertEqual(
                self.client.get(ROOT, dict(changed, cursor=token)).status_code, 400
            )
        self.assertEqual(
            self.client.get(ROOT, {"cursor": token + "x"}).status_code, 400
        )
        with patch("django.core.signing.time.time", return_value=0):
            expired = signing.dumps({}, salt=SALT)
        self.assertEqual(self.client.get(ROOT, {"cursor": expired}).status_code, 400)
        for payload in ([], {}, {"filters": "wrong", "after": []}):
            self.assertEqual(
                self.client.get(
                    ROOT, {"cursor": signing.dumps(payload, salt=SALT)}
                ).status_code,
                400,
            )

    def test_input_validation_and_invalid_identifiers(self):
        for params in [
            {"unknown": "x"},
            {"state": "DRAFT"},
            {"q": ["a", "b"]},
            {"q": "\x00"},
            {"q": "x" * 251},
            {"city": "x" * 251},
            {"type": "staff"},
            {"organization_id": "invalid"},
            {"cursor": "x" * 1025},
        ]:
            self.assertEqual(self.client.get(ROOT, params).status_code, 400)
        self.assertEqual(
            self.client.generic(
                "GET", ROOT, b"{}", content_type="application/json"
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(f"{ROOT}{self.visible.pk}/", {"q": "x"}).status_code, 400
        )
        for identifier in ("not-a-uuid", "0", str(uuid.uuid4())):
            self.assertEqual(self.client.get(f"{ROOT}{identifier}/").status_code, 404)

    def test_no_write_or_framework_metadata_routes(self):
        for path in (ROOT, f"{ROOT}{self.visible.pk}/"):
            for verb in ("post", "put", "patch", "delete", "options", "head"):
                self.assertEqual(getattr(self.client, verb)(path).status_code, 405)
        self.assertEqual(Opportunity.objects.count(), 1)

    def test_rate_limit_is_shared_by_list_and_detail_and_never_discloses_data(self):
        for _ in range(30):
            self.assertEqual(
                self.client.get(f"{ROOT}{self.visible.pk}/").status_code, 200
            )
        response = self.client.get(ROOT)
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("results", response.json())
        self.assertNotIn(self.visible.title.encode(), response.content)

    def test_database_failure_is_redacted(self):
        for path in (ROOT, f"{ROOT}{self.visible.pk}/"):
            with patch(
                "opportunities.views.public_rows",
                side_effect=DatabaseError("private database note"),
            ):
                response = self.client.get(path)
            self.assertEqual(response.status_code, 503)
            self.assertEqual(
                response.json()["error"]["code"], "OPPORTUNITIES_UNAVAILABLE"
            )
            self.assertNotIn(b"private database note", response.content)


class LiveGateTests(TestCase):
    def test_closed_by_default_and_cannot_be_enabled_outside_test_profile(self):
        client = APIClient()
        for profile in ("development", "staging", "production", "test"):
            for exercise in (False, True):
                if profile == "test" and exercise:
                    continue
                with override_settings(
                    PWC_ENVIRONMENT=profile, PWC_OPPORTUNITIES_TEST_EXERCISE=exercise
                ):
                    for path in (ROOT, f"{ROOT}{uuid.uuid4()}/"):
                        with self.assertNumQueries(0):
                            response = client.get(path)
                        self.assertEqual(response.status_code, 503)
                        self.assertEqual(
                            response.json()["error"]["code"],
                            "OPPORTUNITIES_UNAVAILABLE",
                        )
                    self.assertEqual(client.post(ROOT, {}).status_code, 405)


class StorageInvariantTests(TestCase):
    def setUp(self):
        self.a = organization()
        self.b = organization("Fictional B")
        self.row = opportunity(self.a, "DRAFT")

    def rejected(self, **changes):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Opportunity.objects.filter(pk=self.row.pk).update(**changes)

    def test_constraints_hold_when_bypassing_model_validation(self):
        for changes in (
            {"type": "INVALID"},
            {"state": "INVALID"},
            {"title": "   "},
            {"organization_id": None},
            {"organization_id": uuid.uuid4()},
            {"state": "PUBLISHED"},
            {"state": "DRAFT", "published_at": timezone.now()},
        ):
            self.rejected(**changes)

    def test_ownership_and_uuid_cannot_be_reassigned(self):
        self.rejected(organization_id=self.b.pk)
        self.rejected(id=uuid.uuid4())

    def test_forward_only_lifecycle_and_immutable_publication_time(self):
        now = timezone.now()
        self.rejected(state="WITHDRAWN", published_at=now, withdrawn_at=now)
        Opportunity.objects.filter(pk=self.row.pk).update(
            state="PUBLISHED", published_at=now
        )
        self.rejected(state="DRAFT", published_at=None)
        self.rejected(published_at=now + timedelta(seconds=1))
        self.rejected(state="WITHDRAWN", withdrawn_at=now - timedelta(seconds=1))
        Opportunity.objects.filter(pk=self.row.pk).update(
            state="WITHDRAWN", withdrawn_at=now + timedelta(seconds=1)
        )
        self.rejected(state="PUBLISHED", withdrawn_at=None)
        self.rejected(state="DRAFT", published_at=None, withdrawn_at=None)

    def test_owning_ngo_deletion_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.a.delete()


class MigrationTests(TransactionTestCase):
    def test_additive_migration_reverses_and_reapplies_on_postgresql(self):
        from django.db.migrations.executor import MigrationExecutor

        self.assertEqual(connection.vendor, "postgresql")
        executor = MigrationExecutor(connection)
        try:
            executor.migrate([("opportunities", None)])
            self.assertNotIn(
                "opportunities_opportunity", connection.introspection.table_names()
            )
        finally:
            executor = MigrationExecutor(connection)
            executor.migrate([("opportunities", "0001_initial")])
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tgname FROM pg_trigger WHERE tgrelid = 'opportunities_opportunity'::regclass AND NOT tgisinternal"
            )
            self.assertIn(("pwc_opportunity_lifecycle_guard",), cursor.fetchall())
        self.assertEqual(Opportunity.objects.count(), 0)
