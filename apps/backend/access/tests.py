"""ADR K01–K15 service/DB acceptance, on PostgreSQL; HTTP/discovery is .2."""
import importlib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Event
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.db import DatabaseError, IntegrityError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, TransactionTestCase, override_settings
from django.utils import timezone

from accounts import sessions
from accounts.models import AuthSession, User, MobileCredential
from accounts.test_sessions import SESSION_CONFIG
from organizations.models import Organization, OrganizationAccess, OrganizationWorkspace
from .context import resolve_context
from .models import AuthorizationEvent, NGOKernelState, NGOGrant, SyntheticPrincipal
from .registry import ACTIONS, BUNDLES, ENTER, READ, SETTINGS
from .security import KernelProblem, db_clock
from .services import evaluate, _eligible_actions, _state_queryset
from .testing import FixtureBatch

CONFIG = dict(SESSION_CONFIG, PWC_SYNTHETIC_AUTHORIZATION_ENABLED=True,
              PWC_AUTHORIZATION_ENVIRONMENT="synthetic_test")


def worker(function):
    close_old_connections()
    try:
        return function()
    finally:
        connection.close()


@override_settings(**CONFIG)
class KernelFixture(TransactionTestCase):
    def setUp(self):
        self.batch = FixtureBatch()
        self.user_id = self.batch.create_user()
        self.a, self.b = self.batch.create_tenant(), self.batch.create_tenant()
        self.request, self.session_id = self.request_for(self.user_id)

    def request_for(self, user_id):
        request = RequestFactory().get("/internal-test-only/", secure=True)
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=user_id)
            result = sessions.issue_locked(request, user, "Synthetic", "mobile", "mobile")
        request.META["HTTP_AUTHORIZATION"] = "Bearer " + result["access_token"]
        request._synthetic_refresh_token = result["refresh_token"]
        return request, uuid.UUID(result["session"]["id"])

    def revision(self, organization=None):
        return NGOKernelState.objects.get(organization_id=organization or self.a).revision

    def grant(self, organization=None, subject=None, **kwargs):
        organization = organization or self.a
        return self.batch.issue(organization, subject or self.user_id,
                                expected_revision=self.revision(organization), **kwargs)

    def check(self, organization=None, action=READ, **kwargs):
        return evaluate(self.request, kind="ngo", identifier=organization or self.a, action=action, **kwargs)

    def assert_problem(self, code, function):
        with self.assertRaises(KernelProblem) as caught:
            function()
        self.assertEqual(caught.exception.code, code)



@override_settings(**CONFIG)
class KernelTests(KernelFixture):
    def test_k01_tenant_scoped_queryset_and_direct_object(self):
        self.grant()
        self.assertTrue(self.check().allowed)
        self.assertEqual(_state_queryset(self.a).filter(organization_id=self.b).count(), 0)
        self.assertFalse(self.check(self.b).allowed)
        foreign = self.check(object_organization_id=self.b)
        absent = self.check(object_organization_id=uuid.uuid4())
        self.assertEqual((foreign.status, foreign.code), (absent.status, absent.code))
        self.assertEqual(foreign.projection, ())
        self.assertTrue(self.check(object_organization_id=self.a).allowed)

    def test_k02_same_person_different_tenant_bundles(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        self.grant(self.b)
        self.assertTrue(self.check(action=SETTINGS).allowed)
        self.assertEqual(self.check(self.b, action=SETTINGS).status, 403)
        self.assertTrue(self.check(self.b).allowed)

    def test_k02_union_within_tenant_only_and_immutable_registry(self):
        self.grant()
        self.grant(role_code="ngo_kernel_admin_probe")
        self.assertEqual(set(self.check().actions), ACTIONS)
        self.assertFalse(self.check(self.b).allowed)
        with self.assertRaises(TypeError):
            BUNDLES[("ngo_kernel_reader", 1)] = ACTIONS
        self.assertIsInstance(BUNDLES[("ngo_kernel_reader", 1)], frozenset)

    def test_k03_legacy_staff_board_and_membership_labels_do_not_authorize(self):
        User.objects.filter(pk=self.user_id).update(is_staff=True, is_superuser=True)
        user = User.objects.get(pk=self.user_id)
        user.groups.add(Group.objects.create(name="PWC Board / member / volunteer"))
        for role in ("admin", "members", "claimant"):
            OrganizationAccess.objects.create(organization_id=self.a, user=user, role=role)
        self.assertEqual(self.check().status, 404)
        self.assertFalse(self.check(action=SETTINGS).allowed)

    def test_k03_admin_probe_no_finance_delegation_or_mfa_override(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        for action in ("ngo.finance.read", "ngo.finance.approve", "ngo.access.manage", "ngo.signatory.accept", "ngo.files.read", "ngo.export", "*", "unknown"):
            with self.subTest(action=action):
                self.assertFalse(self.check(action=action).allowed)
        # Even a valid authenticated session and caller-supplied MFA assertion isn't authority.
        self.request.META["HTTP_MFA_VERIFIED"] = "true"
        self.assertFalse(self.check(action="ngo.finance.read").allowed)

    def test_k04_expired_grant(self):
        now = timezone.now()
        self.grant(effective_at=now-timedelta(hours=2), expires_at=now-timedelta(hours=1))
        self.assertFalse(self.check().allowed)

    def test_k04_future_grant(self):
        self.grant(effective_at=timezone.now()+timedelta(hours=1))
        self.assertFalse(self.check().allowed)

    def test_k04_unverified_grant(self):
        self.grant(verified=False)
        self.assertFalse(self.check().allowed)

    def test_k04_unknown_bundle_defense_and_database_constraint(self):
        grant_id = self.grant()
        grant = NGOGrant.objects.get(pk=grant_id)
        for field, value in (("role_code", "unknown"), ("role_version", 2)):
            forged = SimpleNamespace(**{**grant.__dict__, field: value})
            self.assertEqual(_eligible_actions([forged], timezone.now())[0], set())
        self.assert_problem("permission_denied", lambda: self.grant(role_version=2))

    def test_k04_revoked_session_and_epoch(self):
        self.grant()
        User.objects.filter(pk=self.user_id).update(auth_epoch=2)
        self.assertFalse(self.check().allowed)

    def test_k04_hold_is_not_cleared_by_mfa_or_admin_probe(self):
        self.grant(role_code="ngo_kernel_admin_probe")
        User.objects.filter(pk=self.user_id).update(recovery_hold_state="restricted", hold_set_at=timezone.now(), hold_reason="password_reset")
        self.assertEqual(self.check().code, "recovery_hold")

    def test_k04_inactive_and_expired_session(self):
        self.grant()
        now = timezone.now()
        AuthSession.objects.filter(pk=self.session_id).update(created_at=now-timedelta(hours=2), last_interactive_at=now-timedelta(hours=2), absolute_expires_at=now-timedelta(seconds=1))
        self.assertFalse(self.check().allowed)

    def test_k05_contexts_fail_closed(self):
        self.grant()
        for kind, identifier in (("ngo", None), ("ngo", "not-uuid"), ("committee", self.a), ("operations", self.a), ("personal", self.user_id)):
            self.assertFalse(evaluate(self.request, kind=kind, identifier=identifier, action=READ).allowed)
        self.assertEqual(resolve_context("personal", self.user_id, personal_user_id=self.user_id).kind, "personal")
        with self.assertRaises(ValueError):
            resolve_context("personal", uuid.uuid4(), personal_user_id=self.user_id)

    def test_k06_revoke_is_immediate_and_noop_does_not_repeat(self):
        grant = self.grant()
        prior = self.check()
        self.assertTrue(prior.allowed)
        self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
        self.assertFalse(worker(lambda: self.check()).allowed)
        self.assertEqual(self.revision(), 3)
        self.assertEqual(NGOGrant.objects.get(pk=grant).revision, 2)
        before = AuthorizationEvent.objects.filter(result="change").count()
        self.batch.revoke(self.a, grant, expected_revision=3, expected_grant_revision=2)
        self.assertEqual(AuthorizationEvent.objects.filter(result="change").count(), before)

    def test_k09_precondition_conflicts_and_new_explicit_grant(self):
        self.assert_problem("precondition_required", lambda: self.batch.issue(self.a, self.user_id, expected_revision=None))
        self.assert_problem("revision_mismatch", lambda: self.batch.issue(self.a, self.user_id, expected_revision=99))
        grant = self.grant()
        self.assert_problem("revision_mismatch", lambda: self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=5))
        self.assertEqual(self.revision(), 2)
        self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
        self.assert_problem("revision_mismatch", lambda: self.batch.issue(self.a, self.user_id, expected_revision=2))
        new = self.grant()
        self.assertNotEqual(new, grant)
        self.assertEqual(NGOGrant.objects.get(pk=grant).revision, 2)

    def test_k10_audit_failure_read_and_issue_fail_closed(self):
        grant_count = NGOGrant.objects.count()
        with patch("access.testing.AuthorizationEvent.objects.create", side_effect=DatabaseError):
            self.assert_problem("authorization_unavailable", lambda: self.grant())
        self.assertEqual(NGOGrant.objects.count(), grant_count)
        self.assertEqual(self.revision(), 1)
        self.grant()
        with patch("access.services._audit", side_effect=DatabaseError):
            decision = self.check()
        self.assertEqual(decision.status, 503)
        self.assertEqual(decision.projection, ())

    def test_k10_audit_failure_revocation_rolls_back(self):
        grant = self.grant()
        with patch("access.testing.AuthorizationEvent.objects.create", side_effect=DatabaseError):
            self.assert_problem("authorization_unavailable", lambda: self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1))
        self.assertIsNone(NGOGrant.objects.get(pk=grant).revoked_at)
        self.assertEqual(self.revision(), 2)
        self.assertTrue(self.check().allowed)

    def test_k10_final_deadline_after_audit_uses_wall_clock(self):
        grant = self.grant(expires_at=timezone.now()+timedelta(seconds=30))
        deadline = NGOGrant.objects.get(pk=grant).expires_at
        before = AuthorizationEvent.objects.filter(result="allow").count()
        with patch("access.services.db_clock", side_effect=[timezone.now(), deadline]):
            self.assertFalse(self.check().allowed)
        self.assertEqual(AuthorizationEvent.objects.filter(result="allow").count(), before)

    def test_k11_gate_default_off_environment_and_database_name(self):
        self.grant()
        for values in ({"PWC_SYNTHETIC_AUTHORIZATION_ENABLED": False}, {"PWC_AUTHORIZATION_ENVIRONMENT": "production"}):
            with self.subTest(values=values), override_settings(**values):
                self.assertEqual(self.check().status, 503)
                self.assert_problem("authorization_unavailable", lambda: self.batch.create_tenant())
        with patch.dict(connection.settings_dict, NAME="real_production"):
            self.assertFalse(self.check().allowed)

    def test_k11_real_accounts_and_batch_mismatch_cannot_enroll(self):
        real = User.objects.create(username="legacy-real")
        self.assert_problem("not_found", lambda: self.batch.issue(self.a, real.pk, expected_revision=1))
        foreign_batch = FixtureBatch()
        foreign_user = foreign_batch.create_user()
        self.assert_problem("not_found", lambda: self.batch.issue(self.a, foreign_user, expected_revision=1))
        real_org = Organization.objects.create(name="Legacy", classification="registered")
        self.assert_problem("not_found", lambda: self.batch.issue(real_org.pk, self.user_id, expected_revision=1))
        self.assertFalse(NGOKernelState.objects.filter(organization=real_org).exists())

    def test_k11_disabled_is_terminal(self):
        self.grant()
        self.batch.disable(self.a, expected_revision=2)
        self.assertFalse(self.check().allowed)
        with self.assertRaises(IntegrityError), transaction.atomic():
            NGOKernelState.objects.filter(organization_id=self.a).update(mode="synthetic", revision=4)

    def test_k12_grant_constraints_immutability_and_terminal_revocation(self):
        grant_id = self.grant()
        for changes in ({"expires_at": timezone.now()+timedelta(hours=3)}, {"role_version": 2}, {"source_ref": ""}, {"organization_id": self.b}):
            with self.subTest(changes=changes), self.assertRaises(IntegrityError), transaction.atomic():
                NGOGrant.objects.filter(pk=grant_id).update(**changes)
        stale = NGOGrant.objects.get(pk=grant_id)
        self.batch.revoke(self.a, grant_id, expected_revision=2, expected_grant_revision=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            stale.save()
        with self.assertRaises(IntegrityError), transaction.atomic():
            NGOGrant.objects.filter(pk=grant_id).update(revoked_at=None)
        with self.assertRaises(IntegrityError), transaction.atomic():
            NGOGrant.objects.filter(pk=grant_id).delete()

    def test_k12_insert_constraints_slots_lifetime_and_cross_record_batch(self):
        original = NGOGrant.objects.get(pk=self.grant())
        fields = {f.attname: getattr(original, f.attname) for f in NGOGrant._meta.fields if f.name != "id"}
        cases = [
            ({}, "grant_unrevoked_slot_unique"),
            ({"role_code": "unknown"}, "grant_bundle_closed"),
            ({"role_version": 2}, "grant_bundle_closed"),
            ({"source_ref": ""}, "grant_evidence_required"),
            ({"scope_kind": "global"}, "grant_scope_source_closed"),
            ({"expires_at": original.effective_at}, "grant_lifetime_bounded"),
            ({"expires_at": original.effective_at+timedelta(hours=25)}, "grant_lifetime_bounded"),
            ({"revocation_reason": "without_timestamp"}, "grant_revocation_complete"),
        ]
        for changes, constraint in cases:
            # Use an empty slot except for the dedicated uniqueness test: one
            # failing constraint must not accidentally mask another missing one.
            base = fields if not changes else fields | {"organization_id": self.b}
            with self.subTest(changes=changes):
                with self.assertRaises(IntegrityError) as caught, transaction.atomic():
                    NGOGrant.objects.create(**(base | changes))
                self.assertEqual(caught.exception.__cause__.diag.constraint_name, constraint)
        with self.assertRaises(IntegrityError), transaction.atomic():
            NGOGrant.objects.create(**(fields | {"organization_id": self.b, "fixture_batch": uuid.uuid4()}))

    def test_k12_audit_and_attestations_immutable_and_ownership(self):
        grant = self.grant()
        event = AuthorizationEvent.objects.filter(grant_id=grant).get()
        for model, pk, field, value in ((AuthorizationEvent, event.pk, "reason_code", "changed"), (SyntheticPrincipal, SyntheticPrincipal.objects.get(user_id=self.user_id).pk, "fixture_batch", uuid.uuid4())):
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.filter(pk=pk).update(**{field: value})
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.filter(pk=pk).delete()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AuthorizationEvent.objects.create(organization_id=self.b, grant_id=grant, action="bad", result="change", reason_code="bad")
        other_user = self.batch.create_user()
        with self.assertRaises(IntegrityError), transaction.atomic():
            AuthorizationEvent.objects.create(organization_id=self.a, actor_id=other_user, session_id=self.session_id, action=READ, result="allow", reason_code="bad")

    def test_k12_workspace_changes_cannot_bypass_revision(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            OrganizationWorkspace.objects.filter(organization_id=self.a).update(state="restricted")

    def test_k12_database_parent_foreign_keys_protect_history(self):
        self.grant()
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM organizations_organization WHERE id=%s", [self.a])
                cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
        self.assertTrue(Organization.objects.filter(pk=self.a).exists())

    def test_k13_reverse_used_history_guard(self):
        module = importlib.import_module("access.migrations.0002_postgresql_guards")
        from django.apps import apps
        with self.assertRaises(RuntimeError):
            module.protect_used_history(apps, SimpleNamespace(connection=connection))

    def test_k14_existing_auth_guards_and_no_idle_keepalive(self):
        self.grant()
        before = AuthSession.objects.get(pk=self.session_id).last_interactive_at
        self.assertTrue(self.check().allowed)
        self.assertEqual(AuthSession.objects.get(pk=self.session_id).last_interactive_at, before)
        self.request.COOKIES["__Host-pwc_session"] = "mixed"
        self.assertFalse(self.check().allowed)

    def test_k15_http_routes_stay_disabled_by_default(self):
        # .2 adds routes, not default enablement. No credentials or DB allow path.
        for suffix in ("capabilities", "private-probe", "kernel-settings"):
            response = self.client.get(f"/api/v1/ngo-contexts/{self.a}/{suffix}/")
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json()["error"]["code"], "not_found")
            self.assertEqual(response["Cache-Control"], "no-store")



@override_settings(**CONFIG)
class KernelAdditionalTests(KernelFixture):
    def test_k03_real_totp_observation_does_not_create_grants_or_finance(self):
        import json
        import pyotp
        from accounts import mfa
        from accounts.models import MfaFactor
        from accounts.test_mfa import MFA_CONFIG
        with override_settings(**MFA_CONFIG):
            factor_id, secret = uuid.uuid4(), pyotp.random_base32()
            user = User.objects.get(pk=self.user_id)
            now = timezone.now()
            factor = MfaFactor.objects.create(id=factor_id, user=user, state="active",
                key_id="test", encrypted_secret=mfa.cipher("test").encrypt(json.dumps({
                    "user": str(user.pk), "factor": str(factor_id), "purpose": "totp-v1", "secret": secret,
                }).encode()), confirmed_at=now, enrollment_session_id=self.session_id,
                auth_epoch=user.auth_epoch, recovery_generation=user.recovery_generation,
                expires_at=now+timedelta(minutes=5))
            with transaction.atomic():
                User.objects.select_for_update().get(pk=user.pk)
                self.assertTrue(mfa.verify_totp(factor, pyotp.TOTP(secret).now()))
                mfa.observe(AuthSession.objects.select_for_update().get(pk=self.session_id), factor)
            self.assertEqual(self.check().status, 404)
            self.grant(role_code="ngo_kernel_admin_probe")
            self.assertTrue(self.check(action=SETTINGS).allowed)
            self.assertFalse(self.check(action="ngo.finance.read").allowed)
            User.objects.filter(pk=user.pk).update(recovery_hold_state="restricted", hold_reason="password_reset", hold_set_at=timezone.now())
            self.assertEqual(self.check().code, "recovery_hold")

    def test_k04_missing_attestation_and_nonverified_workspace(self):
        other = Organization.objects.create(name="Synthetic provisional", classification="registered")
        OrganizationWorkspace.objects.create(organization=other, state="provisional")
        NGOKernelState.objects.create(organization=other, mode="synthetic", fixture_batch=self.batch.id, evidence_ref="negative-fixture")
        self.grant(other.pk)
        self.assertEqual(self.check(other.pk).status, 404)
        user = User.objects.create(username="unattested-synthetic")
        from accounts.models import UserContact
        UserContact.objects.create(user=user, display_value="unattested@pwc.invalid", normalized_value="unattested@pwc.invalid", is_primary=True, verified_at=timezone.now())
        request, _ = self.request_for(user.pk)
        self.assertEqual(evaluate(request, kind="ngo", identifier=self.a, action=READ).status, 404)

    def test_k10_authoritative_database_failure(self):
        self.grant()
        with patch("access.services.NGOKernelState.objects.raw", side_effect=DatabaseError):
            result = self.check()
        self.assertEqual(result.status, 503)
        self.assertEqual(result.projection, ())

    def test_k11_router_or_snapshot_isolation_not_accepted(self):
        self.grant()
        with override_settings(DATABASE_ROUTERS=[object()]):
            self.assertEqual(self.check().status, 503)
        # Session default changed only on this test connection, restored afterwards.
        with connection.cursor() as cursor:
            cursor.execute("SET default_transaction_isolation = 'repeatable read'")
        try:
            self.assertEqual(self.check().status, 503)
        finally:
            with connection.cursor() as cursor:
                cursor.execute("SET default_transaction_isolation = 'read committed'")


@override_settings(**CONFIG)
class KernelRaceTests(KernelFixture):
    def wait_for_block(self, pid):
        import time
        deadline = time.monotonic() + 1.5
        while time.monotonic() < deadline:
            with connection.cursor() as cursor:
                cursor.execute("SELECT cardinality(pg_blocking_pids(%s))", [pid])
                if cursor.fetchone()[0]:
                    return
            time.sleep(0.01)
        self.fail("worker never reached a PostgreSQL lock wait")

    def observed(self, function, ready, pid):
        def run():
            connection.ensure_connection()
            pid.append(connection.connection.info.backend_pid)
            ready.set()
            return function()
        return worker(run)

    def test_k07_expiry_during_lock_wait(self):
        self.grant(expires_at=timezone.now()+timedelta(seconds=1))
        ready, pid = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                NGOKernelState.objects.select_for_update().get(organization_id=self.a)
                future = pool.submit(self.observed, self.check, ready, pid)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
                # Barrier is the observed PG lock; wait specifically for DB expiry.
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_sleep(GREATEST(0, EXTRACT(EPOCH FROM ((SELECT expires_at FROM access_ngogrant WHERE organization_id=%s) - clock_timestamp()))) + 0.03)", [self.a])
            decision = future.result(timeout=5)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "not_found")

    def test_k08_concurrent_same_slot_creation(self):
        barrier = Barrier(2)
        def create():
            barrier.wait(timeout=3)
            try:
                self.batch.issue(self.a, self.user_id, expected_revision=1)
                return "created"
            except KernelProblem as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(create), range(2)))
        self.assertCountEqual(results, ["created", "revision_mismatch"])
        self.assertEqual(NGOGrant.objects.filter(organization_id=self.a, revoked_at__isnull=True).count(), 1)
        self.assertEqual(self.revision(), 2)
        self.assertEqual(AuthorizationEvent.objects.filter(action="fixture_grant_create").count(), 1)

    def test_k08_concurrent_revoke_create_cannot_resurrect(self):
        grant = self.grant()
        barrier = Barrier(2)
        def revoke():
            barrier.wait(timeout=3)
            self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
            return "revoked"
        def create():
            barrier.wait(timeout=3)
            try:
                self.batch.issue(self.a, self.user_id, expected_revision=2)
                return "unexpected"
            except KernelProblem as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(worker, revoke), pool.submit(worker, create)
            self.assertEqual(first.result(timeout=5), "revoked")
            self.assertIn(second.result(timeout=5), ("revision_mismatch", "state_conflict"))
        self.assertEqual(NGOGrant.objects.filter(organization_id=self.a).count(), 1)
        self.assertIsNotNone(NGOGrant.objects.get(pk=grant).revoked_at)
        self.assertFalse(self.check().allowed)

    def race_read_revoke(self, read_first):
        grant = self.grant()
        locked, release, ready = Event(), Event(), Event()
        pid = []
        manager = AuthorizationEvent.objects
        original = manager.create
        action = READ if read_first else "fixture_grant_revoke"
        def pause(**kwargs):
            event = original(**kwargs)
            if kwargs.get("action") == action:
                locked.set()
                if not release.wait(4):
                    raise AssertionError("test barrier release timed out")
            return event
        def revoke():
            self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
            return "revoked"
        first, second = (self.check, revoke) if read_first else (revoke, self.check)
        with patch.object(manager, "create", side_effect=pause), ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(worker, first)
            self.assertTrue(locked.wait(2))
            try:
                f2 = pool.submit(self.observed, second, ready, pid)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
            finally:
                release.set()
            r1, r2 = f1.result(timeout=5), f2.result(timeout=5)
        decision = r1 if read_first else r2
        self.assertEqual(decision.allowed, read_first)
        self.assertIsNotNone(NGOGrant.objects.get(pk=grant).revoked_at)
        self.assertFalse(self.check().allowed)

    def test_k07_read_serializes_before_revocation(self):
        self.race_read_revoke(True)

    def test_k07_revocation_serializes_before_read(self):
        self.race_read_revoke(False)

    def test_k10_lock_timeout_fails_closed(self):
        self.grant()
        ready, pid = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                NGOKernelState.objects.select_for_update().get(organization_id=self.a)
                future = pool.submit(self.observed, self.check, ready, pid)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
                decision = future.result(timeout=4)
        self.assertEqual(decision.status, 503)
        self.assertEqual(decision.projection, ())

    def test_k14_auth_epoch_transition_before_read(self):
        self.grant()
        ready, pid = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=self.user_id)
                user.auth_epoch += 1
                user.save(update_fields=["auth_epoch"])
                future = pool.submit(self.observed, self.check, ready, pid)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
            decision = future.result(timeout=4)
        self.assertEqual(decision.status, 401)
        self.assertFalse(decision.allowed)

    def auth_transition_race(self, change):
        self.grant()
        ready, pid = Event(), []
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=self.user_id)
                future = pool.submit(self.observed, self.check, ready, pid)
                self.assertTrue(ready.wait(1))
                self.wait_for_block(pid[0])
                change(user)
            decision = future.result(timeout=4)
        self.assertFalse(decision.allowed)
        return decision

    def test_k14_logout_all_transition_before_read(self):
        decision = self.auth_transition_race(lambda user: sessions.revoke_all_locked(user, "logout_all"))
        self.assertEqual(decision.status, 401)

    def test_k14_hold_transition_before_read(self):
        def hold(user):
            user.recovery_hold_state = "restricted"
            user.hold_set_at = timezone.now()
            user.hold_reason = "password_reset"
            user.save(update_fields=["recovery_hold_state", "hold_set_at", "hold_reason"])
        self.assertEqual(self.auth_transition_race(hold).code, "recovery_hold")

    def test_k14_refresh_before_read_invalidates_old_credential(self):
        def refresh(user):
            # Same thread already owns User; auth refresh keeps canonical order.
            result = sessions.refresh(self.request._synthetic_refresh_token, "192.0.2.5")
            self.assertIsInstance(result, dict)
        self.assertEqual(self.auth_transition_race(refresh).status, 401)


@override_settings(**CONFIG)
class KernelPrivilegeTests(KernelFixture):
    def test_k12_actual_restricted_runtime_and_fixture_roles(self):
        grant = self.grant()
        runtime, fixture = "pwc_rt_" + uuid.uuid4().hex, "pwc_fx_" + uuid.uuid4().hex
        from psycopg import sql
        def execute(statement):
            with connection.cursor() as cursor:
                cursor.execute(statement)
        try:
            for role in (runtime, fixture):
                execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT").format(sql.Identifier(role)))
                execute(sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(sql.Identifier(role)))
            # Existing auth needs row locks/writes, but access authority is separately restricted.
            execute(sql.SQL("GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {}").format(sql.Identifier(runtime)))
            from pathlib import Path
            provisioning = Path(__file__).with_name("db_roles.sql").read_text()
            execute(provisioning.replace(':"runtime_role"', '"' + runtime + '"').replace(':"fixture_role"', '"' + fixture + '"'))
            execute(sql.SQL("SET ROLE {}").format(sql.Identifier(runtime)))
            self.assertTrue(self.check().allowed)  # Lock function works without state UPDATE.
            for statement in (
                "UPDATE access_ngogrant SET revoked_at=NULL", "UPDATE access_ngokernelstate SET revision=revision+1",
                "INSERT INTO access_syntheticprincipal SELECT * FROM access_syntheticprincipal LIMIT 1",
                "DELETE FROM access_authorizationevent", "TRUNCATE access_authorizationevent",
            ):
                with self.subTest(statement=statement), self.assertRaises(DatabaseError), transaction.atomic():
                    execute(statement)
            self.assert_problem("authorization_unavailable", lambda: self.grant(self.b))
            self.assertTrue(self.check().allowed)
            execute("RESET ROLE")
            execute(sql.SQL("GRANT SELECT, INSERT, UPDATE ON access_ngogrant, access_ngokernelstate TO {}").format(sql.Identifier(fixture)))
            execute(sql.SQL("GRANT SELECT, INSERT ON access_authorizationevent, access_syntheticprincipal TO {}").format(sql.Identifier(fixture)))
            execute(sql.SQL("GRANT SELECT, UPDATE ON accounts_user TO {}").format(sql.Identifier(fixture)))
            execute(sql.SQL("SET ROLE {}").format(sql.Identifier(fixture)))
            self.batch.revoke(self.a, grant, expected_revision=2, expected_grant_revision=1)
            with self.assertRaises(IntegrityError), transaction.atomic():
                NGOGrant.objects.filter(pk=grant).update(revoked_at=None)
            with self.assertRaises(DatabaseError), transaction.atomic():
                AuthorizationEvent.objects.all().delete()
        finally:
            execute("RESET ROLE")
            for role in (runtime, fixture):
                execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))


class KernelMigrationTests(TransactionTestCase):
    def test_k13_additive_migration_preserves_legacy_no_backfill_and_guards_reverse(self):
        executor = MigrationExecutor(connection)
        executor.migrate([("access", None)])
        try:
            user = User.objects.create(username="preserved-user", password="unusable-history-value")
            org = Organization.objects.create(name="Historical", classification="registered")
            workspace = OrganizationWorkspace.objects.create(organization=org, state="verified")
            row = OrganizationAccess.objects.create(organization=org, user=user, role="admin")
            account_migrations = list(connection.cursor().execute("SELECT name FROM django_migrations WHERE app='accounts' ORDER BY name").fetchall())
            executor = MigrationExecutor(connection)
            executor.migrate([("access", "0002_postgresql_guards")])
            self.assertEqual(User.objects.get(pk=user.pk).password, "unusable-history-value")
            self.assertEqual(OrganizationWorkspace.objects.get(pk=workspace.pk).organization_id, org.pk)
            self.assertEqual(OrganizationAccess.objects.get(pk=row.pk).role, "admin")
            self.assertEqual(NGOGrant.objects.count(), 0)
            self.assertEqual(NGOKernelState.objects.count(), 0)
            self.assertEqual(account_migrations, list(connection.cursor().execute("SELECT name FROM django_migrations WHERE app='accounts' ORDER BY name").fetchall()))
            with override_settings(**CONFIG):
                FixtureBatch().create_tenant()
            with self.assertRaises(RuntimeError):
                MigrationExecutor(connection).migrate([("access", "0001_initial")])
            self.assertTrue(NGOKernelState.objects.exists())
        finally:
            MigrationExecutor(connection).migrate([("access", "0002_postgresql_guards")])
