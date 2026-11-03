"""04D uses existing anonymous four-field reads, not a publication authority."""

import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Organization, OrganizationAccess, OrganizationWorkspace


class PublicSummaryIsolationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.a = Organization.objects.create(
            name="Synthetic NGO A", city="Faisalabad", classification="registered"
        )
        self.b = Organization.objects.create(
            name="Unpublished NGO B", city="Private city", classification="unregistered"
        )
        OrganizationWorkspace.objects.create(organization=self.a, state="verified")
        self.workspace = OrganizationWorkspace.objects.create(
            organization=self.b, state="provisional"
        )
        self.user = get_user_model().objects.create_user(
            username="private-member-canary", email="private@example.invalid"
        )
        OrganizationAccess.objects.create(
            organization=self.b, user=self.user, role="admin"
        )

    def detail(self, pk):
        return self.client.get(f"/api/v1/organizations/{pk}/")

    def test_exact_public_projection_never_contains_private_relationships(self):
        expected = dict(
            id=str(self.a.pk),
            name=self.a.name,
            city=self.a.city,
            classification=self.a.classification,
        )
        self.assertEqual(self.detail(self.a.pk).json(), expected)
        for path in ("/api/v1/organizations/", "/api/v1/directory/"):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            rows = response.json()
            if isinstance(rows, dict):
                rows = rows["results"]
            self.assertEqual(rows, [expected])
            self.assertNotIn("private-member-canary", response.content.decode())
            self.assertNotIn("private@example.invalid", response.content.decode())
            self.assertNotIn(self.b.name, response.content.decode())

    def test_membership_staff_and_superuser_do_not_publish_hidden_ngo(self):
        for staff, superuser in ((False, False), (True, False), (True, True)):
            self.user.is_staff, self.user.is_superuser = staff, superuser
            self.user.save()
            self.client.force_authenticate(user=self.user)
            self.assertEqual(self.detail(self.b.pk).status_code, 404)
            self.assertEqual(self.detail(self.a.pk).json()["id"], str(self.a.pk))

    def test_visibility_is_rechecked_and_no_other_ngo_is_substituted(self):
        for state in OrganizationWorkspace.State.values:
            self.workspace.state = state
            self.workspace.save()
            response = self.detail(self.b.pk)
            if state == "verified":
                self.assertEqual(response.json()["id"], str(self.b.pk))
                self.assertEqual(
                    set(response.json()), {"id", "name", "city", "classification"}
                )
            else:
                self.assertEqual(response.status_code, 404)
        self.workspace.delete()
        self.assertEqual(self.detail(self.b.pk).status_code, 404)
        self.assertEqual(self.detail(self.a.pk).json()["id"], str(self.a.pk))

    def test_missing_malformed_and_private_identifiers_never_return_public_fallback(
        self,
    ):
        for identifier in ("not-a-uuid", "0000", str(uuid.uuid4()), str(self.user.pk)):
            self.assertEqual(self.detail(identifier).status_code, 404)

    def test_public_summary_does_not_enable_mutation_or_publication(self):
        self.client.force_authenticate(user=self.user)
        for pk in (self.a.pk, self.b.pk):
            for method in (
                self.client.post,
                self.client.patch,
                self.client.put,
                self.client.delete,
            ):
                self.assertEqual(
                    method(
                        f"/api/v1/organizations/{pk}/",
                        {"name": "changed", "state": "verified"},
                        format="json",
                    ).status_code,
                    405,
                )
        self.a.refresh_from_db()
        self.workspace.refresh_from_db()
        self.assertEqual(self.a.name, "Synthetic NGO A")
        self.assertEqual(self.workspace.state, "provisional")

    def test_hidden_and_unknown_records_share_redacted_error_response(self):
        hidden = self.detail(self.b.pk)
        unknown = self.detail(uuid.uuid4())
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(hidden.json(), unknown.json())
        for response in (hidden, unknown, self.detail("not-a-uuid")):
            for canary in (
                self.b.name,
                self.b.city,
                self.user.email,
                self.user.username,
            ):
                self.assertNotIn(canary, response.content.decode())

    def test_two_public_ngos_keep_exact_target_projection_separate(self):
        self.workspace.state = "verified"
        self.workspace.save()
        for organization in (self.a, self.b):
            response = self.detail(organization.pk)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json(),
                {
                    "id": str(organization.pk),
                    "name": organization.name,
                    "city": organization.city,
                    "classification": organization.classification,
                },
            )
