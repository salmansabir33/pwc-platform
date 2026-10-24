"""PWC-03B.2: real Django/DRF HTTP and separate-connection PostgreSQL tests."""
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Event
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.db import DatabaseError, connection, transaction
from django.test import Client, override_settings
from django.utils import timezone

from accounts import sessions
from accounts.models import AuthSession, User, UserContact
from accounts.test_registration import PASSWORD
from organizations.models import Organization, OrganizationAccess
from . import services, tests as kernel_tests
from .models import AuthorizationEvent, NGOGrant, NGOKernelState
from .registry import ENTER, READ, SETTINGS
from .testing import FixtureBatch

HTTP_CONFIG = dict(kernel_tests.CONFIG, PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED=True)
DISCOVERY = "/api/v1/me/ngo-contexts/"


@override_settings(**HTTP_CONFIG)
class HTTPFixture(kernel_tests.KernelFixture):
    def setUp(self):
        super().setUp()
        self.client = Client(enforce_csrf_checks=True)

    def url(self, organization=None, resource="private-probe"):
        return f"/api/v1/ngo-contexts/{organization or self.a}/{resource}/"

    def http(self, path=None, *, client=None, auth=True, **extra):
        headers = {"HTTP_HOST": "api.pwc.invalid"}
        if auth:
            headers["HTTP_AUTHORIZATION"] = self.request.META["HTTP_AUTHORIZATION"]
        headers.update(extra)
        return (client or self.client).get(path or self.url(), secure=True, **headers)

    def discovery(self, **extra):
        return self.http(DISCOVERY, **extra)

    def browser(self):
        user = User.objects.get(pk=self.user_id)
        user.set_password(PASSWORD)
        user.save(update_fields=["password"])
        client = Client(enforce_csrf_checks=True)
        csrf = client.get("/api/v1/auth/csrf/", secure=True, HTTP_HOST="ngo.pwc.invalid").json()["csrf_token"]
        response = client.post("/api/v1/auth/web/login/", data={"email": user.email, "password": PASSWORD},
            content_type="application/json", secure=True, HTTP_HOST="ngo.pwc.invalid",
            HTTP_ORIGIN="https://ngo.pwc.invalid", HTTP_X_CSRFTOKEN=csrf)
        self.assertEqual(response.status_code, 200, response.content)
        return client

    def assert_error(self, response, status, code):
        self.assertEqual(response.status_code, status, response.content)
        self.assertEqual(set(response.json()), {"error"})
        self.assertEqual(set(response.json()["error"]), {"code", "correlation_id"})
        self.assertEqual(response.json()["error"]["code"], code)
        uuid.UUID(response.json()["error"]["correlation_id"])
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn(str(self.a), response.content.decode())
        self.assertNotIn(str(self.b), response.content.decode())


@override_settings(**HTTP_CONFIG)
class ContextHTTPTests(HTTPFixture):
    def test_routes_roles_and_minimal_projections(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        self.grant(self.b)
        for org in (self.a, self.b):
            response = self.http(self.url(org))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(set(response.json()), {"organization_id", "context_revision", "probe_code", "label"})
            self.assertEqual(response.json()["organization_id"], str(org))
            self.assertIsInstance(response.json()["context_revision"], int)
        self.assertEqual(self.http(self.url(resource="kernel-settings")).status_code, 200)
        self.assert_error(self.http(self.url(self.b, "kernel-settings")), 403, "permission_denied")

    def test_capability_projection_sorted_pinned_and_advisory_expiry(self):
        now = timezone.now()
        self.grant(expires_at=now+timedelta(minutes=20))
        self.grant(role_code="ngo_kernel_admin_probe", expires_at=now+timedelta(minutes=10))
        response = self.http(self.url(resource="capabilities"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["actions"], sorted([ENTER, READ, SETTINGS]))
        self.assertEqual(data["context"], {"kind": "ngo", "organization_id": str(self.a)})
        self.assertEqual(data["registry_version"], "ngo_kernel_v1")
        self.assertEqual(data["context_revision"], 3)
        self.assertEqual(data["earliest_grant_expires_at"], (now+timedelta(minutes=10)).isoformat())

    def test_discovery_own_eligible_contexts_only(self):
        self.grant()
        self.grant(self.b, role_code="ngo_kernel_admin_probe")
        other = self.batch.create_user()
        foreign = self.batch.create_tenant()
        self.grant(foreign, other)
        response = self.discovery()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(set(data), {"results", "next_cursor"})
        self.assertEqual([item["organization_id"] for item in data["results"]], sorted([str(self.a), str(self.b)]))
        for item in data["results"]:
            self.assertEqual(set(item), {"kind", "organization_id", "context_revision"})
        self.assertIsNone(data["next_cursor"])
        self.assertNotIn(str(other), response.content.decode())
        self.assertNotIn(str(foreign), response.content.decode())
        self.assert_error(self.http(self.url(foreign)), 404, "not_found")

    def test_discovery_empty_is_audited_without_inventing_authority(self):
        response = self.discovery()
        self.assertEqual(response.json(), {"results": [], "next_cursor": None})
        self.assertTrue(AuthorizationEvent.objects.filter(action="discovery", result="deny", reason_code="no_eligible_contexts").exists())

    def test_unauthenticated_auth_before_context_validation(self):
        for path in (DISCOVERY, self.url(), self.url("bad-uuid", "capabilities")):
            response = self.http(path, auth=False)
            self.assert_error(response, 401, "authentication_required")
            self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_unknown_and_foreign_organizations_are_indistinguishable(self):
        self.grant()
        for org in (self.b, uuid.uuid4()):
            for resource in ("capabilities", "private-probe", "kernel-settings"):
                self.assert_error(self.http(self.url(org, resource)), 404, "not_found")

    def test_malformed_context(self):
        self.grant()
        for resource in ("capabilities", "private-probe", "kernel-settings"):
            self.assert_error(self.http(self.url("not-a-uuid", resource)), 400, "invalid_context")

    def test_every_query_is_closed_except_discovery_cursor(self):
        self.grant()
        for query in ("organization_id="+str(self.b), "ngo_id="+str(self.a), "action=ngo.finance.read", "role=ngo_kernel_admin_probe", "fields=*", "capabilities=*", "format=json", "cursor=bogus", "tenant_id=a&tenant_id=b"):
            with self.subTest(query=query):
                self.assert_error(self.http(self.url()+"?"+query), 400, "invalid_context")
        for query in ("role=ngo_kernel_admin_probe", "organization_id="+str(self.a), "limit=500", "fields=*", "cursor=", "cursor=a&cursor=b"):
            self.assert_error(self.http(DISCOVERY+"?"+query), 400, "invalid_context")

    def test_conflicting_and_matching_context_or_role_headers_rejected(self):
        self.grant()
        for header in ("HTTP_X_ORGANIZATION_ID", "HTTP_X_TENANT_ID", "HTTP_X_CONTEXT_SELECTION", "HTTP_CONTEXT_SELECTION", "HTTP_X_ROLES", "HTTP_X_CAPABILITIES", "HTTP_X_PERMISSION", "HTTP_X_ACTION"):
            self.assert_error(self.http(**{header: str(self.b)}), 400, "invalid_context")
        self.assert_error(self.http(HTTP_X_NGO_ID=str(self.a)), 400, "invalid_context")

    def test_get_body_is_not_a_context_or_claim_channel(self):
        self.grant()
        for body in ({"organization_id": str(self.b)}, {"role": "ngo_kernel_admin_probe"}, {}):
            response = self.client.generic("GET", self.url(), data=json.dumps(body), content_type="application/json",
                secure=True, HTTP_HOST="api.pwc.invalid", HTTP_AUTHORIZATION=self.request.META["HTTP_AUTHORIZATION"])
            self.assert_error(response, 400, "invalid_context")

    def test_legacy_staff_board_and_mfa_headers_cannot_create_permissions(self):
        user = User.objects.get(pk=self.user_id)
        user.is_staff = user.is_superuser = True
        user.save(update_fields=["is_staff", "is_superuser"])
        user.groups.add(Group.objects.create(name="PWC Board / member / volunteer"))
        for role in ("admin", "members", "claimant"):
            OrganizationAccess.objects.create(organization_id=self.a, user=user, role=role)
        self.assertEqual(self.discovery().json()["results"], [])
        self.assert_error(self.http(HTTP_MFA_VERIFIED="true"), 404, "not_found")
        self.grant()
        self.assert_error(self.http(self.url(resource="kernel-settings"), HTTP_MFA_VERIFIED="true"), 403, "permission_denied")

    def test_admin_probe_has_no_finance_delegation_or_governance_route(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        actions = self.http(self.url(resource="capabilities")).json()["actions"]
        self.assertEqual(set(actions), {ENTER, READ, SETTINGS})
        for resource in ("finance", "grants", "signatory", "governance", "export", "select"):
            self.assertEqual(self.http(self.url(resource=resource)).status_code, 404)
        self.assertEqual(self.http("/api/v1/committee-contexts/"+str(self.a)+"/capabilities/").status_code, 404)

    def test_expired_future_unverified_and_disabled_discovery_exclusions(self):
        now = timezone.now()
        self.grant(effective_at=now-timedelta(hours=2), expires_at=now-timedelta(hours=1))
        self.grant(self.b, verified=False)
        future = self.batch.create_tenant()
        self.grant(future, effective_at=now+timedelta(hours=1))
        disabled = self.batch.create_tenant()
        self.grant(disabled)
        self.batch.disable(disabled, expected_revision=2)
        self.assertEqual(self.discovery().json()["results"], [])
        for org in (self.a, self.b, future, disabled):
            self.assert_error(self.http(self.url(org)), 404, "not_found")

    def test_immediate_revocation_invalidates_capabilities_and_discovery(self):
        grant = self.grant(role_code="ngo_kernel_admin_probe")
        self.assertEqual(self.http(self.url(resource="capabilities")).status_code, 200)
        self.assertEqual(len(self.discovery().json()["results"]), 1)
        self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
        self.assertEqual(self.discovery().json()["results"], [])
        self.assert_error(self.http(self.url(resource="kernel-settings")), 404, "not_found")
        self.assert_error(self.http(self.url(resource="capabilities"), HTTP_IF_NONE_MATCH="*"), 404, "not_found")

    def test_stale_revisions_do_not_authorize_or_make_reads_conditional(self):
        reader = self.grant()
        admin = self.grant(role_code="ngo_kernel_admin_probe")
        self.batch.revoke(self.a, admin, expected_revision=3, expected_grant_revision=1)
        response = self.http(self.url(resource="capabilities"), HTTP_IF_MATCH=f'"ngo:{self.a}:r3"', HTTP_IF_NONE_MATCH="*")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["actions"], sorted([ENTER, READ]))
        self.assertEqual(response.json()["context_revision"], 4)
        self.assert_error(self.http(self.url(resource="kernel-settings")), 403, "permission_denied")

    def test_recovery_hold_revoked_session_and_suspension(self):
        self.grant()
        User.objects.filter(pk=self.user_id).update(recovery_hold_state="restricted", hold_reason="password_reset", hold_set_at=timezone.now())
        self.assert_error(self.discovery(), 403, "recovery_hold")
        self.assert_error(self.http(), 403, "recovery_hold")
        User.objects.filter(pk=self.user_id).update(recovery_hold_state="clear", hold_reason="", hold_set_at=None, is_active=False)
        self.assert_error(self.http(), 401, "authentication_required")
        User.objects.filter(pk=self.user_id).update(is_active=True)
        AuthSession.objects.filter(pk=self.session_id).update(revoked_at=timezone.now(), revocation_reason="logout")
        self.assert_error(self.discovery(), 401, "authentication_required")

    def test_unattested_authenticated_identity_and_real_ngo_not_activated_by_flags(self):
        real = User.objects.create(username="unattested-http")
        UserContact.objects.create(user=real, display_value="unattested-http@pwc.invalid", normalized_value="unattested-http@pwc.invalid", is_primary=True, verified_at=timezone.now())
        request, _ = self.request_for(real.pk)
        self.request = request
        self.assertEqual(self.discovery().json()["results"], [])
        self.assert_error(self.http(), 404, "not_found")
        org = Organization.objects.create(name="Legacy unattested organization", classification="registered")
        self.assert_error(self.http(self.url(org.pk)), 404, "not_found")

    def test_default_http_gate_all_methods_no_audit_or_data(self):
        self.grant()
        before = AuthorizationEvent.objects.count()
        with override_settings(PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED=False):
            for path in (DISCOVERY, self.url(), self.url(resource="capabilities"), self.url(resource="kernel-settings")):
                self.assert_error(self.http(path), 404, "not_found")
                for method in ("post", "options"):
                    response = getattr(self.client, method)(path, secure=True, HTTP_HOST="api.pwc.invalid")
                    self.assert_error(response, 404, "not_found")
        self.assertEqual(AuthorizationEvent.objects.count(), before)

    def test_http_gate_alone_cannot_bypass_safe_environment(self):
        self.grant()
        for values in ({"PWC_SYNTHETIC_AUTHORIZATION_ENABLED": False}, {"PWC_AUTHORIZATION_ENVIRONMENT": "production"}):
            with override_settings(**values):
                self.assert_error(self.http(), 503, "authorization_unavailable")
                self.assert_error(self.discovery(), 503, "authorization_unavailable")

    def test_no_cache_no_etag_and_no_idle_renewal(self):
        self.grant()
        before = AuthSession.objects.get(pk=self.session_id).last_interactive_at
        for path in (DISCOVERY, self.url(), self.url(resource="capabilities")):
            response = self.http(path, HTTP_IF_NONE_MATCH="*", HTTP_ACCEPT="text/html")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertIn("Authorization", response["Vary"])
            self.assertIn("Cookie", response["Vary"])
            self.assertNotIn("ETag", response)
            self.assertTrue(response["Content-Type"].startswith("application/json"))
        self.assertEqual(AuthSession.objects.get(pk=self.session_id).last_interactive_at, before)

    def test_disallowed_methods_are_uniform_and_never_mutate(self):
        self.grant()
        before = NGOGrant.objects.count()
        for method in ("post", "put", "patch", "delete", "options"):
            response = getattr(self.client, method)(self.url(), secure=True, HTTP_HOST="api.pwc.invalid")
            self.assert_error(response, 405, "method_not_allowed")
        self.assertEqual(NGOGrant.objects.count(), before)

    def test_tls_cookie_bearer_mixing_and_forged_credentials(self):
        self.grant()
        insecure = self.client.get(self.url(), HTTP_AUTHORIZATION=self.request.META["HTTP_AUTHORIZATION"], HTTP_HOST="api.pwc.invalid")
        self.assert_error(insecure, 400, "TRANSPORT_NOT_ALLOWED")
        self.assert_error(self.http(HTTP_AUTHORIZATION="Bearer not-a-token"), 401, "authentication_required")
        self.client.cookies["__Host-pwc_session"] = "not-a-registered-cookie"
        self.assert_error(self.http(), 400, "AMBIGUOUS_CREDENTIALS")

    def test_registered_browser_cookie_and_unregistered_cookie_denial(self):
        self.grant()
        browser = self.browser()
        self.assertEqual(self.http(client=browser, auth=False, HTTP_HOST="ngo.pwc.invalid").status_code, 200)
        self.assertEqual(self.http(DISCOVERY, client=browser, auth=False, HTTP_HOST="ngo.pwc.invalid").status_code, 200)
        self.assert_error(self.http(client=browser, HTTP_HOST="ngo.pwc.invalid"), 400, "AMBIGUOUS_CREDENTIALS")
        browser.cookies["__Host-pwc_session"] = "forged-django-cookie"
        self.assert_error(self.http(client=browser, auth=False, HTTP_HOST="ngo.pwc.invalid"), 401, "authentication_required")

    def test_existing_browser_csrf_protection_is_not_weakened(self):
        browser = self.browser()
        # No new unsafe endpoint; existing auth command still requires exact Origin/CSRF.
        response = browser.post("/api/v1/auth/logout/", data={}, content_type="application/json", secure=True, HTTP_HOST="ngo.pwc.invalid")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"]["code"], "CSRF_FAILED")

    def test_head_is_reauthorized_and_has_no_response_body(self):
        grant = self.grant()
        response = self.client.head(self.url(), secure=True, HTTP_HOST="api.pwc.invalid", HTTP_AUTHORIZATION=self.request.META["HTTP_AUTHORIZATION"])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
        response = self.client.head(self.url(), secure=True, HTTP_HOST="api.pwc.invalid", HTTP_AUTHORIZATION=self.request.META["HTTP_AUTHORIZATION"])
        self.assertEqual(response.status_code, 404)

    def test_db_and_audit_failure_return_only_503_envelope(self):
        self.grant()
        for target in ("access.services._audit", "access.services._locked_state", "access.views.services.evaluate"):
            with patch(target, side_effect=DatabaseError):
                self.assert_error(self.http(), 503, "authorization_unavailable")
        with patch("access.services._audit", side_effect=DatabaseError):
            self.assert_error(self.discovery(), 503, "authorization_unavailable")
        self.assertFalse(AuthorizationEvent.objects.filter(result="allow").exists())

    def test_auth_dependency_failure_is_503_not_anonymous_fallback(self):
        with override_settings(PWC_AUTH_SESSIONS_ENABLED=False):
            self.assert_error(self.http(), 503, "authorization_unavailable")

    def test_discovery_final_expiry_is_409_and_rolls_back_page_audits(self):
        expires = timezone.now()+timedelta(minutes=2)
        self.grant(expires_at=expires)
        with patch("access.services.db_clock", side_effect=[timezone.now(), timezone.now(), expires]):
            self.assert_error(self.discovery(), 409, "state_conflict")
        self.assertFalse(AuthorizationEvent.objects.filter(result="allow").exists())

    def test_final_auth_deadline_before_response(self):
        self.grant()
        deadline = timezone.now()
        with patch("access.services.sessions.authorization_deadline", return_value=deadline):
            self.assert_error(self.http(), 401, "authentication_required")
            self.assert_error(self.discovery(), 401, "authentication_required")
        self.assertFalse(AuthorizationEvent.objects.filter(result="allow").exists())

    def test_expired_bearer_is_never_a_cached_identity(self):
        from accounts.models import MobileCredential
        self.grant()
        now = timezone.now()
        MobileCredential.objects.filter(session_id=self.session_id, kind="access").update(
            issued_at=now-timedelta(minutes=10), expires_at=now-timedelta(minutes=1))
        self.assert_error(self.http(), 401, "authentication_required")
        self.assert_error(self.discovery(), 401, "authentication_required")

    def test_wrong_browser_portal_cookie_cannot_retarget_identity(self):
        self.grant()
        browser = self.browser()
        self.assert_error(self.http(client=browser, auth=False, HTTP_HOST="ops.pwc.invalid"), 401, "authentication_required")

    def test_final_grant_expiry_returns_no_private_http_payload(self):
        expires = timezone.now()+timedelta(minutes=2)
        self.grant(expires_at=expires)
        with patch("access.services.db_clock", side_effect=[timezone.now(), expires]):
            self.assert_error(self.http(), 404, "not_found")
        self.assertFalse(AuthorizationEvent.objects.filter(result="allow").exists())


@override_settings(**HTTP_CONFIG)
class DiscoveryPaginationTests(HTTPFixture):
    def create_page(self):
        organizations = []
        for _ in range(51):
            org = self.batch.create_tenant()
            self.grant(org)
            organizations.append(str(org))
        return sorted(organizations)

    def test_bounded_keyset_pages_and_user_session_bound_cursor(self):
        expected = self.create_page()
        first = self.discovery().json()
        self.assertEqual(len(first["results"]), 50)
        self.assertEqual([r["organization_id"] for r in first["results"]], expected[:50])
        cursor = first["next_cursor"]
        second = self.http(DISCOVERY+"?cursor="+cursor).json()
        self.assertEqual([r["organization_id"] for r in second["results"]], expected[50:])
        self.assertIsNone(second["next_cursor"])
        self.assert_error(self.http(DISCOVERY+"?cursor="+cursor+"x"), 400, "invalid_context")
        self.request, _ = self.request_for(self.user_id)
        self.assert_error(self.http(DISCOVERY+"?cursor="+cursor), 400, "invalid_context")
        other = self.batch.create_user()
        self.request, _ = self.request_for(other)
        self.assert_error(self.http(DISCOVERY+"?cursor="+cursor), 400, "invalid_context")

    def test_cursor_continuation_rechecks_revocation_not_snapshot(self):
        expected = self.create_page()
        cursor = self.discovery().json()["next_cursor"]
        target = uuid.UUID(expected[-1])
        grant = NGOGrant.objects.get(organization_id=target)
        self.batch.revoke(target, grant.pk, expected_revision=2, expected_grant_revision=1)
        self.assertEqual(self.http(DISCOVERY+"?cursor="+cursor).json(), {"results": [], "next_cursor": None})
        self.assert_error(self.http(DISCOVERY+"?cursor="+str(target)), 400, "invalid_context")

    def test_cursor_max_age_and_empty_or_oversized_inputs(self):
        self.grant()
        user = User.objects.get(pk=self.user_id)
        session = AuthSession.objects.get(pk=self.session_id)
        with patch("django.core.signing.time.time", return_value=timezone.now().timestamp()-4000):
            cursor = services._cursor(self.a, user, session)
        self.assert_error(self.http(DISCOVERY+"?cursor="+cursor), 400, "invalid_context")
        self.assert_error(self.http(DISCOVERY+"?cursor="+"x"*513), 400, "invalid_context")

    def test_empty_discovery_audit_outage_returns_503(self):
        with patch("access.services._audit", side_effect=DatabaseError):
            self.assert_error(self.discovery(), 503, "authorization_unavailable")


@override_settings(**HTTP_CONFIG)
class ContextHTTPRaceTests(HTTPFixture):
    wait_for_block = kernel_tests.KernelRaceTests.wait_for_block

    def race_read_revoke(self, *, read_first, discovery=False):
        grant = self.grant()
        locked, release, ready = Event(), Event(), Event()
        pid = []
        original = services._audit
        paused_action = ENTER if discovery else READ

        def pause(**kwargs):
            event = original(**kwargs)
            if kwargs.get("action") == paused_action and kwargs.get("result") == "allow":
                locked.set()
                if not release.wait(4):
                    raise AssertionError("HTTP barrier was not released")
            return event

        def read():
            client = Client(enforce_csrf_checks=True)
            return self.http(DISCOVERY if discovery else self.url(), client=client)

        def revoke():
            self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
            return "revoked"

        def observed(function):
            connection.ensure_connection()
            pid.append(connection.connection.info.backend_pid)
            ready.set()
            return function()

        # Revoke-first barrier must pause the fixture audit, not the read audit.
        manager = AuthorizationEvent.objects
        fixture_original = manager.create
        def pause_revoke(**kwargs):
            event = fixture_original(**kwargs)
            if kwargs.get("action") == "fixture_grant_revoke":
                locked.set()
                if not release.wait(4):
                    raise AssertionError("revocation barrier was not released")
            return event

        first, second = (read, revoke) if read_first else (revoke, read)
        patcher = patch("access.services._audit", side_effect=pause) if read_first else patch.object(manager, "create", side_effect=pause_revoke)
        with patcher, ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(kernel_tests.worker, first)
            try:
                self.assertTrue(locked.wait(2))
                f2 = pool.submit(kernel_tests.worker, lambda: observed(second))
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
            finally:
                release.set()
            r1, r2 = f1.result(timeout=5), f2.result(timeout=5)
        response = r1 if read_first else r2
        if discovery:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()["results"]), 1 if read_first else 0)
        else:
            self.assertEqual(response.status_code, 200 if read_first else 404)
        self.assertIsNotNone(NGOGrant.objects.get(pk=grant).revoked_at)
        self.assertEqual(self.revision(), 3)
        self.assertEqual(AuthorizationEvent.objects.filter(action="fixture_grant_revoke").count(), 1)
        self.assert_error(self.http(), 404, "not_found")
        self.assertEqual(self.discovery().json()["results"], [])

    def test_http_read_before_revocation(self):
        self.race_read_revoke(read_first=True)

    def test_http_revocation_before_read(self):
        self.race_read_revoke(read_first=False)

    def test_discovery_before_revocation(self):
        self.race_read_revoke(read_first=True, discovery=True)

    def test_revocation_before_discovery(self):
        self.race_read_revoke(read_first=False, discovery=True)

    def test_http_expiry_during_real_postgresql_root_wait(self):
        self.grant(expires_at=timezone.now()+timedelta(seconds=1))
        ready, pid = Event(), []
        def read():
            connection.ensure_connection()
            pid.append(connection.connection.info.backend_pid)
            ready.set()
            return self.http(client=Client(enforce_csrf_checks=True))
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                NGOKernelState.objects.select_for_update().get(organization_id=self.a)
                future = pool.submit(kernel_tests.worker, read)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM ((SELECT expires_at FROM access_ngogrant WHERE organization_id=%s) - clock_timestamp()))) + 0.03)", [self.a])
            self.assert_error(future.result(timeout=5), 404, "not_found")
        self.assertFalse(AuthorizationEvent.objects.filter(result="allow").exists())

    def test_discovery_locks_roots_in_sorted_bounded_order(self):
        for org in (self.b, self.a):
            self.grant(org)
        original = services._locked_state
        order = []
        def capture(identifier):
            order.append(identifier)
            return original(identifier)
        with patch("access.services._locked_state", side_effect=capture):
            self.assertEqual(self.discovery().status_code, 200)
        self.assertEqual(order, sorted([self.a, self.b]))
        self.assertLessEqual(len(order), 50)


@override_settings(**HTTP_CONFIG)
class RuntimeHTTPPrivilegeTests(HTTPFixture):
    def test_discovery_and_private_http_work_without_state_write_privileges(self):
        from psycopg import sql
        self.grant()
        runtime, fixture = "pwc_http_rt_"+uuid.uuid4().hex, "pwc_http_fx_"+uuid.uuid4().hex
        def execute(statement):
            with connection.cursor() as cursor:
                cursor.execute(statement)
        try:
            for role in (runtime, fixture):
                execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(sql.Identifier(role)))
                execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
            execute(sql.SQL("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(runtime)))
            provisioning = Path(__file__).with_name("db_roles.sql").read_text()
            execute(provisioning.replace(':"runtime_role"', '"'+runtime+'"').replace(':"fixture_role"', '"'+fixture+'"'))
            execute(sql.SQL("SET ROLE {}").format(sql.Identifier(runtime)))
            self.assertEqual(self.discovery().status_code, 200)
            self.assertEqual(self.http().status_code, 200)
            self.assertEqual(self.http(self.url(resource="capabilities")).status_code, 200)
            self.assert_error(self.http(self.url(resource="kernel-settings")), 403, "permission_denied")
            with self.assertRaises(DatabaseError), transaction.atomic():
                execute("UPDATE access_ngokernelstate SET revision=revision+1")
        finally:
            execute("RESET ROLE")
            for role in (runtime, fixture):
                execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


@override_settings(**HTTP_CONFIG)
class CheckedContextFixtureTests(HTTPFixture):
    def test_machine_readable_contract_matches_real_http(self):
        fixture = json.loads((Path(__file__).resolve().parents[3] / "packages/api-contracts/ngo-contexts-v1.fixtures.json").read_text())
        self.grant()
        responses = {}
        for name, suffix in fixture["routes"].items():
            path = fixture["prefix"] + suffix.replace("{organization_uuid}", str(self.a))
            if name == "kernel_settings":
                self.assert_error(self.http(path), 403, "permission_denied")
                self.grant(role_code="ngo_kernel_admin_probe")
            response = self.http(path)
            self.assertEqual(response.status_code, 200)
            responses[name] = response
            for header, value in fixture["always_headers"].items():
                self.assertEqual(response[header], value)
            for value in fixture["vary"]:
                self.assertIn(value, response["Vary"])
        discovery = responses["discovery"].json()
        self.assertEqual(set(discovery), set(fixture["discovery_keys"]))
        self.assertEqual(set(discovery["results"][0]), set(fixture["discovery_item_keys"]))
        capabilities = responses["capabilities"].json()
        self.assertEqual(set(capabilities), set(fixture["capability_keys"]))
        self.assertEqual(set(capabilities["context"]), set(fixture["context_keys"]))
        self.assertEqual(capabilities["registry_version"], fixture["registry_version"])
        self.assertEqual(capabilities["actions"], fixture["role_actions"]["ngo_kernel_reader/1"])
        self.assertEqual(self.http(self.url(resource="capabilities")).json()["actions"], fixture["role_actions"]["ngo_kernel_admin_probe/1"])
        for name in ("private_probe", "kernel_settings"):
            self.assertEqual(set(responses[name].json()), set(fixture["resource_keys"]))
        error = self.http(self.url(self.b))
        self.assertEqual(set(error.json()["error"]), set(fixture["error_keys"]))
        self.assertEqual(error.status_code, fixture["errors"][error.json()["error"]["code"]])
        self.assertEqual(services.PAGE_SIZE, fixture["discovery"]["page_size"])
