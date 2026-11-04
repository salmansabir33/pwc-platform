"""Regressions on the existing deny-default boundary, not a Founder verifier.

Only disposable fixture identities are used. Different accounts/display names do
not prove different natural persons. No nomination is an authenticated source.
"""

from django.contrib.auth.models import Group

from accounts.models import User
from organizations.models import OrganizationAccess
from .models import AuthorizationEvent, NGOGrant
from .registry import ACTIONS, SETTINGS
from .tests import KernelFixture


class FounderNominationBoundaryTests(KernelFixture):
    def test_founder_and_nominee_display_names_do_not_grant_access(self):
        for display_name in ("Founder", "AbuBakr"):
            with self.subTest(display_name=display_name):
                User.objects.filter(pk=self.user_id).update(
                    first_name=display_name, is_staff=True, is_superuser=True
                )
                user = User.objects.get(pk=self.user_id)
                for title in (
                    "Founder oversight",
                    "Independent verifier nominee",
                    "Governance",
                    "Technical",
                    "Membership",
                    "Finance",
                    "Operations",
                ):
                    user.groups.add(Group.objects.get_or_create(name=title)[0])
                OrganizationAccess.objects.get_or_create(
                    organization_id=self.a, user=user, role="admin"
                )
                before = NGOGrant.objects.count()
                for organization in (self.a, self.b):
                    decision = self.check(organization)
                    self.assertFalse(decision.allowed)
                    self.assertEqual(decision.status, 404)
                    self.assertEqual(decision.projection, ())
                    self.assertEqual(decision.actions, ())
                self.assertEqual(NGOGrant.objects.count(), before)

    def test_caller_nomination_mfa_and_self_approval_assertions_are_not_authority(self):
        for header, value in (
            ("HTTP_X_PWC_FOUNDER", "true"),
            ("HTTP_X_PWC_VERIFIER", "AbuBakr"),
            ("HTTP_X_PWC_APPROVED_BY", str(self.user_id)),
            ("HTTP_MFA_VERIFIED", "true"),
            ("HTTP_X_PWC_EMERGENCY", "true"),
        ):
            self.request.META[header] = value
        decision = self.check()
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.projection, ())
        self.assertEqual(NGOGrant.objects.count(), 0)
        event = AuthorizationEvent.objects.filter(actor_id=self.user_id).latest(
            "created_at"
        )
        self.assertEqual(event.result, "deny")
        self.assertEqual(event.reason_code, decision.code)

    def test_existing_probe_grant_never_becomes_founder_or_membership_authority(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        before = NGOGrant.objects.count()
        for action in (
            # Deliberately unregistered attack strings, NOT proposed permission IDs.
            "platform.founder.verify.v1",
            "platform.verifier.appoint.v1",
            "platform.founder.activate.v1",
            "platform.emergency.read.v1",
            "ngo.membership.policy.read.v1",
            "ngo.membership.policy.change.v1",
            "ngo.membership.category.create.v1",
            "ngo.membership.category.update.v1",
            "ngo.membership.category.deactivate.v1",
        ):
            with self.subTest(action=action):
                self.assertNotIn(action, ACTIONS)
                decision = self.check(action=action)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, "permission_denied")
                self.assertEqual(decision.projection, ())
        self.assertEqual(NGOGrant.objects.count(), before)
        self.assertTrue(self.check(action=SETTINGS).allowed)

    def test_separate_nominee_account_cannot_approve_itself_or_founder_by_assertion(
        self,
    ):
        other = self.batch.create_user()
        nominee_request, _ = self.request_for(other)
        self.request = nominee_request
        self.request.META["HTTP_X_PWC_APPROVED_BY"] = str(other)
        self.request.META["HTTP_X_PWC_FOUNDER_ID"] = str(self.user_id)
        before = User.objects.count()
        self.assertFalse(self.check().allowed)
        self.assertFalse(self.check(self.b).allowed)
        self.assertEqual(User.objects.count(), before)
        self.assertEqual(NGOGrant.objects.count(), 0)
        # Authentication of two accounts is NOT proof of independent humans.
