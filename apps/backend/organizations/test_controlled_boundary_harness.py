"""Disposable PostgreSQL structural probes, NOT a protected workflow writer.

No production role/function/schema is installed. No grants, appointments, proof,
receipt, reviewer decisions or domain transitions are created by this harness.
The test-only no-login role and its privileges are rolled back together.
"""

from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.db import DatabaseError, close_old_connections, connection, transaction
from django.test import TransactionTestCase
from psycopg import sql

from .models import ControlledOnboardingRecord as Record


class ControlledBoundaryHarnessTests(TransactionTestCase):
    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        self.actor = get_user_model().objects.create_user(
            username="shape-fixture", email="fixture@example.test"
        )
        self.record = Record.objects.create(initiator=self.actor)

    def test_disposable_unprivileged_role_cannot_read_lock_or_mutate_records(self):
        role_name = "pwc_shape_probe_" + uuid4().hex
        role = sql.Identifier(role_name)
        table = sql.Identifier(Record._meta.db_table)
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB "
                        "NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS"
                    ).format(role)
                )
                cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(role))
            for statement in (
                "SELECT * FROM {}",
                "SELECT * FROM {} FOR UPDATE",
                "UPDATE {} SET revision = revision + 1",
                "DELETE FROM {}",
                "INSERT INTO {} (id) VALUES (gen_random_uuid())",
                "TRUNCATE {}",
                "ALTER TABLE {} DISABLE TRIGGER ALL",
            ):
                with self.subTest(statement=statement):
                    with self.assertRaises(DatabaseError) as denied:
                        with transaction.atomic(), connection.cursor() as cursor:
                            cursor.execute(sql.SQL(statement).format(table))
                    self.assertEqual(denied.exception.__cause__.sqlstate, "42501")
            # Never leave a probe role or credentials behind, even on success.
            transaction.set_rollback(True)
        self.record.refresh_from_db()
        self.assertEqual((self.record.state, self.record.revision), ("draft", 1))
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [role_name])
            self.assertIsNone(cursor.fetchone())

    def test_structural_probe_failure_rolls_back_without_transition(self):
        with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
            with transaction.atomic():
                Record.objects.filter(pk=self.record.pk).update(revision=2)
                raise RuntimeError("synthetic failure")
        self.record.refresh_from_db()
        self.assertEqual((self.record.state, self.record.revision), ("draft", 1))

    def test_competing_connection_observes_postgresql_nowait_lock_failure(self):
        locked = Event()
        release = Event()
        pk = self.record.pk

        def holder():
            close_old_connections()
            try:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SET LOCAL lock_timeout = '2s'")
                        cursor.execute("SET LOCAL statement_timeout = '5s'")
                    Record.objects.select_for_update().get(pk=pk)
                    locked.set()
                    if not release.wait(10):
                        raise AssertionError("Fixture lock release timed out")
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(holder)
            try:
                self.assertTrue(locked.wait(10), "Fixture lock acquisition timed out")
                with self.assertRaises(DatabaseError) as blocked:
                    with transaction.atomic():
                        Record.objects.select_for_update(nowait=True).get(pk=pk)
                self.assertEqual(blocked.exception.__cause__.sqlstate, "55P03")
            finally:
                release.set()
                future.result(timeout=15)
        self.record.refresh_from_db()
        self.assertEqual((self.record.state, self.record.revision), ("draft", 1))
