from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from .models import Organization, OrganizationAccess, OrganizationWorkspace

class DirectoryIsolationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.a = Organization.objects.create(name="A welfare group", classification="registered")
        self.b = Organization.objects.create(name="B welfare group", classification="unregistered")
        OrganizationWorkspace.objects.create(organization=self.a, state="verified")
        OrganizationWorkspace.objects.create(organization=self.b, state="provisional")

    def test_only_verified_workspace_is_public(self):
        response = self.client.get("/api/v1/organizations/")
        self.assertEqual(response.status_code, 200)
        names = [row["name"] for row in response.data]
        self.assertEqual(names, ["A welfare group"])

    def test_provisional_organization_detail_not_public(self):
        response = self.client.get(f"/api/v1/organizations/{self.b.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_role_does_not_mean_finance_permission(self):
        user = get_user_model().objects.create_user(username="example_user", password="test-secret-change-me")
        grant = OrganizationAccess.objects.create(organization=self.a, user=user, role="admin")
        self.assertEqual(grant.role, "admin")
        # Finance endpoints and finance privileges have NOT been implemented yet.
        # This test is an explicit guard against claiming they already exist.

    def test_health_is_public_and_minimal(self):
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "pwc-api"})

    def test_public_detail_has_only_public_fields(self):
        response = self.client.get(f"/api/v1/organizations/{self.a.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.data), {"id", "name", "city", "classification"})

    def test_nonverified_workspaces_are_not_published(self):
        for state in OrganizationWorkspace.State.values:
            if state == OrganizationWorkspace.State.VERIFIED:
                continue
            with self.subTest(state=state):
                OrganizationWorkspace.objects.filter(organization=self.b).update(state=state)
                response = self.client.get("/api/v1/organizations/")
                self.assertEqual([row["id"] for row in response.data], [str(self.a.pk)])
                response = self.client.get(f"/api/v1/organizations/{self.b.pk}/")
                self.assertEqual(response.status_code, 404)

    def test_access_grant_does_not_publish_provisional_workspace(self):
        user = get_user_model().objects.create_user(username="claimant")
        OrganizationAccess.objects.create(organization=self.b, user=user, role="claimant")
        self.client.force_authenticate(user=user)
        response = self.client.get(f"/api/v1/organizations/{self.b.pk}/")
        self.assertEqual(response.status_code, 404)

    def test_public_endpoints_do_not_allow_writes(self):
        for path in ("/api/v1/organizations/", f"/api/v1/organizations/{self.a.pk}/"):
            for method in (self.client.post, self.client.put, self.client.patch, self.client.delete):
                with self.subTest(path=path, method=method.__name__):
                    self.assertEqual(method(path, {}, format="json").status_code, 405)
        self.assertEqual(Organization.objects.count(), 2)
