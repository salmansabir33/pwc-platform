import uuid
from django.test import TestCase, Client
from django.core import signing
from .models import Organization, OrganizationWorkspace

ROOT = "/api/v1/directory/"


class DirectoryTests(TestCase):
    def setUp(self):
        self.visible = Organization.objects.create(
            name="Synthetic Welfare", city="Faisalabad", classification="registered"
        )
        OrganizationWorkspace.objects.create(
            organization=self.visible, state="verified"
        )
        for state in ("provisional", "pending", "restricted", "deactivated"):
            value = Organization.objects.create(
                name="Hidden " + state, city="Faisalabad", classification="registered"
            )
            OrganizationWorkspace.objects.create(organization=value, state=state)

    def test_only_existing_four_fields_and_no_private_queries_or_cookie_auth(self):
        response = self.client.get(ROOT, HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            response.json()["results"],
            [
                {
                    "id": str(self.visible.pk),
                    "name": self.visible.name,
                    "city": "Faisalabad",
                    "classification": "registered",
                }
            ],
        )
        self.assertNotIn("count", response.json())

    def test_unicode_normalization_filters_and_empty(self):
        self.assertEqual(
            len(
                self.client.get(
                    ROOT, {"q": "ＳＹＮＴＨＥＴＩＣ", "city": "  FAISALABAD "}
                ).json()["results"]
            ),
            1,
        )
        self.assertEqual(
            self.client.get(ROOT, {"classification": "unregistered"}).json()["results"],
            [],
        )
        self.assertEqual(self.client.get(ROOT, {"q": "Hidden"}).json()["results"], [])

    def test_bounded_pagination_filter_binding_tamper_and_expiry(self):
        for i in range(21):
            obj = Organization.objects.create(
                name=f"Synthetic {i}", city="Faisalabad", classification="registered"
            )
            OrganizationWorkspace.objects.create(organization=obj, state="verified")
        first = self.client.get(ROOT).json()
        self.assertEqual(len(first["results"]), 20)
        cursor = first["next_cursor"]
        second = self.client.get(ROOT, {"cursor": cursor}).json()
        self.assertEqual(len(second["results"]), 2)
        self.assertTrue(
            set(r["id"] for r in first["results"]).isdisjoint(
                r["id"] for r in second["results"]
            )
        )
        self.assertEqual(
            self.client.get(ROOT, {"q": "different", "cursor": cursor}).status_code, 400
        )
        self.assertEqual(
            self.client.get(ROOT, {"cursor": cursor + "x"}).status_code, 400
        )
        from unittest.mock import patch

        with patch("django.core.signing.time.time", return_value=0):
            expired = signing.dumps(
                {"filters": "x", "after": str(uuid.uuid4())},
                salt="pwc.public-directory.v1",
            )
        self.assertEqual(self.client.get(ROOT, {"cursor": expired}).status_code, 400)
        OrganizationWorkspace.objects.filter(organization=self.visible).update(
            state="restricted"
        )
        self.assertNotIn(
            str(self.visible.pk),
            {r["id"] for r in self.client.get(ROOT).json()["results"]},
        )

    def test_query_validation_and_method_rejection(self):
        for params in (
            {"unknown": "x"},
            {"q": ["a", "b"]},
            {"q": "\x00"},
            {"q": "x" * 251},
            {"cursor": "x" * 1025},
            {"classification": "staff"},
        ):
            self.assertEqual(self.client.get(ROOT, params).status_code, 400)
        self.assertEqual(self.client.post(ROOT, {}).status_code, 405)

    def test_rate_limit_does_not_leak_results(self):
        for _ in range(30):
            self.assertEqual(self.client.get(ROOT).status_code, 200)
        response = self.client.get(ROOT)
        self.assertEqual(response.status_code, 429)
        self.assertNotIn("results", response.json())

    def test_dependency_failure_redacts_and_returns_unavailable(self):
        from unittest.mock import patch
        from django.db import DatabaseError

        with patch(
            "organizations.registry.matches",
            side_effect=DatabaseError("private database name"),
        ):
            response = self.client.get(ROOT)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"private database name", response.content)
        self.assertNotIn("results", response.json())
