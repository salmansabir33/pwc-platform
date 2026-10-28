"""Pure structural preparation never supplies live reviewer authority."""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from datetime import timedelta
import uuid
from django.test import SimpleTestCase
from django.utils import timezone
from .controlled_preparation import prepare_submission
from .controlled_onboarding import PreflightConflict


class PreparationTests(SimpleTestCase):
    def setUp(self):
        self.actor = uuid.uuid4()
        self.record = SimpleNamespace(
            pk=uuid.uuid4(), revision=1, state="draft", initiator_id=self.actor
        )
        self.snapshot = SimpleNamespace(
            pk=uuid.uuid4(),
            record_id=self.record.pk,
            revision=1,
            recorded_by_id=self.actor,
            classification="unregistered",
            organization_name="Synthetic",
            city="City",
            nomination_reference="SYNTHETIC_NOMINATION",
            nominee_reference="SYNTHETIC_PERSON",
            nominee_id=None,
        )
        self.now = timezone.now()
        self.rows = [
            SimpleNamespace(
                pk=uuid.uuid4(),
                purpose=p,
                snapshot_id=self.snapshot.pk,
                attestor_id=self.actor,
                examined_at=self.now,
                evidence_reference="SYNTHETIC_CASE",
                method_reference="SYNTHETIC_METHOD",
            )
            for p in ("organization_eligibility", "representative_mandate")
        ]

    def prepare(self, **overrides):
        data = dict(
            record=self.record,
            snapshot=self.snapshot,
            attestations=self.rows,
            actor_id=self.actor,
            expected_revision=1,
            now=self.now,
        )
        data.update(overrides)
        return prepare_submission(**data)

    def test_packet_is_immutable_minimized_nonwriting_and_not_an_approval(self):
        packet = self.prepare()  # SimpleTestCase forbids database access.
        self.assertEqual(packet.source_revision, 1)
        self.assertEqual(packet.proposed_revision, 2)
        self.assertFalse(packet.recipient_resolved)
        self.assertFalse(packet.command_available)
        with self.assertRaises(FrozenInstanceError):
            packet.proposed_revision = 9
        self.assertEqual(self.record.state, "draft")
        self.assertNotIn("SYNTHETIC_CASE", repr(packet))

    def test_stale_revision_wrong_actor_and_terminal_states(self):
        for values in (
            {"expected_revision": 2},
            {"expected_revision": True},
            {"actor_id": uuid.uuid4()},
        ):
            with self.assertRaises(PreflightConflict):
                self.prepare(**values)
        self.record.state = "approved"
        with self.assertRaises(PreflightConflict):
            self.prepare()

    def test_snapshot_and_attestation_cross_source_or_changed_nomination_rejected(self):
        self.snapshot.revision = 2
        with self.assertRaises(PreflightConflict):
            self.prepare()
        self.snapshot.revision = 1
        self.rows[0].snapshot_id = uuid.uuid4()
        with self.assertRaises(PreflightConflict):
            self.prepare()

    def test_duplicate_or_missing_lanes_unknown_and_future_examination(self):
        for rows in (
            self.rows[:1],
            [self.rows[0], self.rows[0]],
            self.rows + self.rows[:1],
        ):
            with self.assertRaises(PreflightConflict):
                self.prepare(attestations=rows)
        self.rows[0].examined_at = self.now + timedelta(seconds=1)
        with self.assertRaises(PreflightConflict):
            self.prepare()

    def test_no_url_document_content_or_naive_date(self):
        self.snapshot.nominee_reference = "https://private.example.invalid"
        with self.assertRaises(PreflightConflict):
            self.prepare()
        self.snapshot.nominee_reference = "SYNTHETIC_PERSON"
        with self.assertRaises(PreflightConflict):
            self.prepare(now=self.now.replace(tzinfo=None))
