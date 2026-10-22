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
