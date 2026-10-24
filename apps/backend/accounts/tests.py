"""Synthetic schema tests, not evidence of implemented authentication flows."""

import uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError
from django.db.models.deletion import ProtectedError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .models import (
    AssuranceIntent,
    AuthAbuseBucket,
    AuthChallenge,
    AuthSession,
    DeliveryIntent,
    MfaFactor,
    MfaRecoveryCode,
    MobileCredential,
    SecurityEvent,
    UserContact,
)

User = get_user_model()


class SecurityFoundationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="synthetic-one")
        self.other = User.objects.create_user(username="synthetic-two")
        self.now = timezone.now()
        self.later = self.now + timedelta(hours=1)
        self.serial = 0

    def digest(self):
        self.serial += 1
        return f"{self.serial:064x}"

    def session(self, user=None, **overrides):
        data = dict(
            user=user or self.user,
            transport="mobile",
            portal="mobile",
            created_at=self.now,
            last_interactive_at=self.now,
            absolute_expires_at=self.later,
            auth_epoch=1,
        )
        data.update(overrides)
        return AuthSession.objects.create(**data)

    def contact(self, **overrides):
        data = dict(
            user=self.user,
            display_value="person+tag@example.invalid",
            normalized_value="person+tag@example.invalid",
        )
        data.update(overrides)
        return UserContact.objects.create(**data)

    def challenge(self, **overrides):
        data = dict(
            purpose="registration",
            flow_control_digest=self.digest(),
            proof_digest=self.digest(),
            created_at=self.now,
            expires_at=self.later,
        )
        data.update(overrides)
        return AuthChallenge.objects.create(**data)

    def factor(self, **overrides):
        data = dict(
            user=self.user,
            enrollment_session=self.session(),
            state="pending",
            encrypted_secret=b"synthetic-not-real-ciphertext",
            key_id="synthetic-key-id",
            auth_epoch=1,
            recovery_generation=0,
            created_at=self.now,
            expires_at=self.later,
        )
        data.update(overrides)
        return MfaFactor.objects.create(**data)

    def rejects(self, call):
        # Assert DB constraints (not only model/form validation).
        with self.assertRaises(IntegrityError), transaction.atomic():
            call()

    def test_user_defaults_preserve_unverified_legacy_identity(self):
        self.assertEqual(
            (
                self.user.auth_epoch,
                self.user.recovery_generation,
                self.user.recovery_hold_state,
            ),
            (1, 0, "clear"),
        )
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.user.contacts.count(), 0)
        self.assertEqual(AuthSession.objects.count(), 0)

    def test_epoch_and_hold_constraints(self):
        for data in [
            dict(auth_epoch=0),
            dict(recovery_generation=-1),
            dict(recovery_hold_state="unknown"),
            dict(recovery_hold_state="restricted"),
            dict(hold_set_at=self.now),
            dict(hold_factor_revision=1),
        ]:
            with self.subTest(data=data):
                self.rejects(
                    lambda: User.objects.filter(pk=self.user.pk).update(**data)
                )
        User.objects.filter(pk=self.user.pk).update(
            recovery_hold_state="restricted",
            hold_set_at=self.now,
            hold_reason="password_reset",
        )

    def test_verified_contact_unique_but_pending_does_not_reserve(self):
        self.contact()
        self.contact(user=self.other)
        self.contact(verified_at=self.now, is_primary=True)
        self.rejects(lambda: self.contact(user=self.other, verified_at=self.now))

    def test_retirement_releases_contact_without_moving_identity(self):
        old = self.contact(verified_at=self.now, retired_at=self.now)
        new = self.contact(user=self.other, verified_at=self.now)
        old.refresh_from_db()
        self.assertEqual(old.user_id, self.user.pk)
        self.assertNotEqual(old.user_id, new.user_id)

    def test_primary_requires_active_verified_and_only_one(self):
        self.rejects(lambda: self.contact(is_primary=True))
        self.rejects(
            lambda: self.contact(
                is_primary=True, verified_at=self.now, retired_at=self.now
            )
        )
        self.contact(is_primary=True, verified_at=self.now)
        self.rejects(
            lambda: self.contact(
                normalized_value="other@example.invalid",
                is_primary=True,
                verified_at=self.now,
            )
        )

    def test_only_email_kind_and_nonempty_values(self):
        self.rejects(lambda: self.contact(kind="phone"))
        self.rejects(lambda: self.contact(normalized_value=""))

    def test_no_unapproved_normalization_is_performed(self):
        # Caller-supplied canonical data only; B1 is deliberately NOT implemented.
        value = "Person.Name+Tag@example.invalid"
        contact = self.contact(display_value=value, normalized_value=value)
        contact.refresh_from_db()
        self.assertEqual(contact.normalized_value, value)
        self.assertNotIn(value, str(contact))

    def test_session_transport_and_expiry_checks(self):
        for data in [
            dict(transport="other"),
            dict(portal="pwc_ops"),
            dict(web_key_digest=self.digest()),
            dict(absolute_expires_at=self.now),
            dict(last_interactive_at=self.later),
            dict(auth_epoch=0),
            dict(revoked_at=self.now),
            dict(mfa_method="totp"),
        ]:
            with self.subTest(data=data):
                self.rejects(lambda: self.session(**data))
        self.session(transport="web", portal="ngo_web", web_key_digest=self.digest())
        self.rejects(lambda: self.session(transport="web", portal="ngo_web"))

    def test_challenge_states_and_eligible_ownership(self):
        self.challenge(purpose="reset", eligible=False)  # inert placeholder
        for data in [
            dict(expires_at=self.now),
            dict(purpose="other"),
            dict(consumed_at=self.now, invalidated_at=self.now),
            dict(purpose="reset", eligible=True),
            dict(generation=0),
            dict(purpose="preauth_mfa"),
        ]:
            with self.subTest(data=data):
                self.rejects(lambda: self.challenge(**data))
        self.challenge(
            purpose="reset",
            eligible=True,
            user=self.user,
            auth_epoch=1,
            target_contact=self.contact(verified_at=self.now),
        )

    def test_cross_owner_contact_validation(self):
        contact = self.contact(user=self.other)
        challenge = self.challenge(user=self.user, target_contact=contact)
        with self.assertRaises(ValidationError):
            challenge.full_clean()

    def test_digest_shapes_enforced_without_full_clean(self):
        self.rejects(lambda: self.challenge(proof_digest="raw-secret"))
        self.rejects(
            lambda: self.session(
                transport="web", portal="ngo_web", web_key_digest="not-a-digest"
            )
        )

    def test_one_current_credential_per_kind(self):
        session = self.session()
        first = MobileCredential.objects.create(
            session=session,
            kind="refresh",
            secret_digest=self.digest(),
            issued_at=self.now,
            expires_at=self.later,
        )
        self.rejects(
            lambda: MobileCredential.objects.create(
                session=session,
                kind="refresh",
                secret_digest=self.digest(),
                expires_at=self.later,
            )
        )
        first.consumed_at = self.now
        first.save(update_fields=["consumed_at"])
        MobileCredential.objects.create(
            session=session,
            kind="refresh",
            secret_digest=self.digest(),
            expires_at=self.later,
        )
        self.rejects(
            lambda: MobileCredential.objects.create(
                session=session,
                kind="access",
                secret_digest=self.digest(),
                expires_at=self.later,
                consumed_at=self.now,
            )
        )
        self.assertEqual(session.credentials.count(), 2)  # retain replay evidence

    def test_bearer_record_cannot_validate_for_web_session(self):
        session = self.session(
            transport="web", portal="ngo_web", web_key_digest=self.digest()
        )
        record = MobileCredential(
            session=session,
            kind="access",
            secret_digest=self.digest(),
            expires_at=self.later,
        )
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_factor_pending_and_active_uniqueness(self):
        first = self.factor()
        self.rejects(lambda: self.factor())
        first.state = "active"
        first.confirmed_at = self.now
        first.save(update_fields=["state", "confirmed_at"])
        self.factor()  # replacement can be pending while one active exists
        self.rejects(lambda: self.factor(state="active", confirmed_at=self.now))

    def test_factor_metadata_and_owner_checks(self):
        self.rejects(lambda: self.factor(state="active"))
        self.rejects(lambda: self.factor(encrypted_secret=b""))
        factor = self.factor(enrollment_session=self.session(user=self.other))
        with self.assertRaises(ValidationError):
            factor.full_clean()

    def test_recovery_code_digest_is_unique_and_owner_checked(self):
        factor = self.factor()
        data = dict(
            user=self.user,
            factor=factor,
            factor_revision=1,
            set_id=uuid.uuid4(),
            code_digest=self.digest(),
        )
        code = MfaRecoveryCode.objects.create(**data)
        self.rejects(lambda: MfaRecoveryCode.objects.create(**data))
        code.user = self.other
        with self.assertRaises(ValidationError):
            code.full_clean()

    def test_assurance_context_terminal_and_owner_constraints(self):
        data = dict(
            user=self.user,
            session=self.session(),
            auth_epoch=1,
            recovery_generation=0,
            operation="synthetic.operation",
            context_kind="ngo",
            context_id=uuid.uuid4(),
            request_digest=self.digest(),
            created_at=self.now,
            expires_at=self.later,
        )
        for change in [
            dict(context_kind="anything"),
            dict(consumed_at=self.now, invalidated_at=self.now),
            dict(operation=""),
        ]:
            self.rejects(lambda: AssuranceIntent.objects.create(**(data | change)))
        record = AssuranceIntent.objects.create(**(data | dict(user=self.other)))
        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_delivery_generation_payload_and_lease_checks(self):
        challenge = self.challenge()
        data = dict(challenge=challenge, generation=1, template="placeholder")
        DeliveryIntent.objects.create(**data)
        self.rejects(lambda: DeliveryIntent.objects.create(**data))
        for change in [
            dict(state="leased"),
            dict(key_id="key"),
            dict(encrypted_payload=b"cipher"),
            dict(encrypted_payload=b"cipher", key_id="key", secret_deleted_at=self.now),
        ]:
            self.rejects(
                lambda: DeliveryIntent.objects.create(
                    **(data | dict(generation=2) | change)
                )
            )

    def test_events_append_only_in_application_paths(self):
        event = SecurityEvent.objects.create(
            subject=self.user, event="synthetic.event", result="success"
        )
        for call in [
            lambda: event.save(),
            lambda: event.delete(),
            lambda: SecurityEvent.objects.filter(pk=event.pk).update(reason="rewrite"),
            lambda: SecurityEvent.objects.all().delete(),
            lambda: SecurityEvent.objects.bulk_update([event], ["reason"]),
        ]:
            with self.assertRaises(ValidationError):
                call()
        self.rejects(
            lambda: SecurityEvent(
                id=event.pk, event="replacement", result="success"
            ).save()
        )
        event.refresh_from_db()
        self.assertEqual(event.event, "synthetic.event")

    def test_security_fks_protect_history(self):
        self.contact()
        with self.assertRaises(ProtectedError):
            self.user.delete()

    def test_abuse_bucket_unique_and_nonnegative(self):
        data = dict(
            dimension="target",
            key_digest=self.digest(),
            route="synthetic",
            window_start=self.now,
            expires_at=self.later,
        )
        AuthAbuseBucket.objects.create(**data)
        self.rejects(lambda: AuthAbuseBucket.objects.create(**data))
        self.rejects(
            lambda: AuthAbuseBucket.objects.create(
                **(data | dict(route="other", count=-1))
            )
        )

    def test_password_policy_boundaries_and_manager_support(self):
        # Non-common passphrases: no composition rule, whitespace is preserved.
        validate_password("otter canvas violet dawn", user=self.user)
        validate_password("xQ7 " * 32, user=self.user)  # exactly 128, paste supported
        for password in ["Abcd!9876Xyz12", "xQ7 " * 33]:
            with self.assertRaises(ValidationError):
                validate_password(password, user=self.user)
        validate_password("cobaltwovenfern", user=self.user)  # 15 lowercase chars

    def test_deferred_authentication_routes_remain_absent(self):
        for path in [
            "contact-change/request/",
        ]:
            self.assertEqual(
                self.client.post(f"/api/v1/auth/{path}", {}).status_code, 404
            )


class MigrationCompatibilityTests(TransactionTestCase):
    old = [
        ("accounts", "0002_alter_user_options_alter_user_is_active"),
        ("organizations", "0002_alter_organizationaccess_id_and_more"),
    ]
    new = [
        ("accounts", "0004_flow_cooldown_and_transition_evidence"),
        ("organizations", "0002_alter_organizationaccess_id_and_more"),
    ]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def test_upgrade_and_unused_reverse_preserve_legacy_data(self):
        old_apps = self.migrate(self.old)
        try:
            LegacyUser = old_apps.get_model("accounts", "User")
            Org = old_apps.get_model("organizations", "Organization")
            Grant = old_apps.get_model("organizations", "OrganizationAccess")
            password_hash = make_password("old-short")
            users = [
                LegacyUser.objects.create(
                    username=f"legacy-{i}", email=email, password=password_hash
                )
                for i, email in enumerate(
                    ["", "Person@example.invalid", "person@example.invalid"]
                )
            ]
            org = Org.objects.create(name="Synthetic NGO", classification="registered")
            grant = Grant.objects.create(user=users[0], organization=org, role="admin")
            ids = [u.pk for u in users]
            new_apps = self.migrate(self.new)
            NewUser = new_apps.get_model("accounts", "User")
            self.assertEqual(
                list(
                    NewUser.objects.filter(pk__in=ids)
                    .order_by("username")
                    .values_list("pk", flat=True)
                ),
                ids,
            )
            self.assertEqual(
                set(NewUser.objects.values_list("password", flat=True)), {password_hash}
            )
            self.assertTrue(all(NewUser.objects.values_list("is_active", flat=True)))
            self.assertEqual(
                set(
                    NewUser.objects.values_list(
                        "auth_epoch", "recovery_generation", "recovery_hold_state"
                    )
                ),
                {(1, 0, "clear")},
            )
            self.assertEqual(
                list(
                    NewUser.objects.order_by("username").values_list("email", flat=True)
                ),
                ["", "Person@example.invalid", "person@example.invalid"],
            )
            from django.contrib.auth.hashers import check_password

            self.assertTrue(
                check_password("old-short", NewUser.objects.get(pk=ids[0]).password)
            )
            self.assertEqual(
                new_apps.get_model("accounts", "UserContact").objects.count(), 0
            )
            self.assertEqual(
                new_apps.get_model("organizations", "OrganizationAccess")
                .objects.get(pk=grant.pk)
                .user_id,
                ids[0],
            )
            reversed_apps = self.migrate(self.old)
            self.assertEqual(
                list(
                    reversed_apps.get_model("accounts", "User")
                    .objects.order_by("username")
                    .values_list("pk", flat=True)
                ),
                ids,
            )
            self.assertEqual(
                reversed_apps.get_model("organizations", "OrganizationAccess")
                .objects.get(pk=grant.pk)
                .organization_id,
                org.pk,
            )
        finally:
            self.migrate(self.new)

    def test_changed_epoch_alone_blocks_reverse(self):
        User.objects.create_user(username="epoch-used", auth_epoch=2)
        with self.assertRaises(IrreversibleError):
            self.migrate(self.old)
        self.assertEqual(User.objects.get(username="epoch-used").auth_epoch, 2)

    def test_transition_evidence_reverse_refuses_before_dropping_columns(self):
        user = User.objects.create_user(username="audited-reset", auth_epoch=2)
        evidence = SecurityEvent.objects.create(
            subject=user,
            event="auth.reset_completed",
            result="success",
            auth_epoch=2,
            recovery_generation=1,
            previous_hold_state="clear",
            new_hold_state="restricted",
        )
        with self.assertRaises(IrreversibleError):
            self.migrate(self.old)
        preserved = SecurityEvent.objects.get(pk=evidence.pk)
        self.assertEqual(preserved.auth_epoch, 2)
        self.assertEqual(preserved.new_hold_state, "restricted")
        self.assertIn(
            ("accounts", self.new[0][1]),
            MigrationExecutor(connection).loader.applied_migrations,
        )

    def test_used_schema_cannot_be_destructively_reversed(self):
        user = User.objects.create_user(username="synthetic-used")
        UserContact.objects.create(
            user=user,
            display_value="used@example.invalid",
            normalized_value="used@example.invalid",
        )
        with self.assertRaises(IrreversibleError):
            self.migrate(self.old)
        self.assertEqual(UserContact.objects.count(), 1)
        self.assertIn(
            ("accounts", self.new[0][1]),
            MigrationExecutor(connection).loader.applied_migrations,
        )


class ConcurrentConstraintTests(TransactionTestCase):
    def test_concurrent_verified_contact_insert_has_one_owner(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections

        users = [
            User.objects.create_user(username=f"parallel-{i}").pk for i in range(2)
        ]
        barrier = Barrier(2)

        def insert(user_id):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    with transaction.atomic():
                        UserContact.objects.create(
                            user_id=user_id,
                            display_value="parallel@example.invalid",
                            normalized_value="parallel@example.invalid",
                            verified_at=timezone.now(),
                        )
                    return "created"
                except IntegrityError:
                    return "conflict"
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(insert, users))
        self.assertCountEqual(results, ["created", "conflict"])
        self.assertEqual(UserContact.objects.count(), 1)
        self.assertEqual(User.objects.count(), 2)  # no merging identities
