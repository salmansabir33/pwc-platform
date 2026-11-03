"""Pure preparation tests. No fixture is a source of operator authority."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
import json
from types import SimpleNamespace
from uuid import uuid4

from django.test import SimpleTestCase
from .controlled_command_shape import (
    CommandShapeError,
    MAX_BYTES,
    MAX_SOURCE_REVISION,
    SHAPE_ACTIONS,
    check_source_shape,
    parse_shape,
)
from .controlled_onboarding import command_available, preflight
from .controlled_preparation import prepare_submission


def source_fixture():
    """Unsaved structural doubles only: no account, role, session or DB write."""
    actor = uuid4()
    record = SimpleNamespace(
        pk=uuid4(),
        organization_id=uuid4(),
        revision=1,
        state="draft",
        initiator_id=actor,
    )
    snapshot = SimpleNamespace(
        pk=uuid4(),
        record_id=record.pk,
        revision=1,
        recorded_by_id=actor,
        classification="unregistered",
        organization_name="Synthetic",
        city="City",
        nomination_reference="SYNTHETIC_NOMINATION",
        nominee_reference="SYNTHETIC_PERSON",
        nominee_id=None,
    )
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    attestations = tuple(
        SimpleNamespace(
            pk=uuid4(),
            snapshot_id=snapshot.pk,
            purpose=purpose,
            attestor_id=actor,
            examined_at=now,
            evidence_reference="SYNTHETIC_REFERENCE",
            method_reference="SYNTHETIC_METHOD",
        )
        for purpose in ("organization_eligibility", "representative_mandate")
    )
    return record, snapshot, attestations, now


class CommandShapeTests(SimpleTestCase):
    def setUp(self):
        self.record, self.snapshot, self.attestations, self.now = source_fixture()
        self.value = {
            "command": "ngo.onboard.submit.v1",
            "record_id": str(self.record.pk),
            "snapshot_id": str(self.snapshot.pk),
            "organization_id": str(self.record.organization_id),
            "expected_revision": 1,
        }

    def parse(self, **overrides):
        return parse_shape(json.dumps(dict(self.value, **overrides)).encode())

    def test_closed_shapes_are_immutable_and_never_executable(self):
        for command in SHAPE_ACTIONS:
            shape = self.parse(command=command)
            self.assertFalse(shape.executable)
            self.assertFalse(command_available(None, command))
            with self.assertRaises((FrozenInstanceError, TypeError, AttributeError)):
                shape.executable = True
        with self.assertRaises(TypeError):
            SHAPE_ACTIONS["approve"] = "approve"
        self.assertNotIn(str(self.record.pk), repr(self.parse()))

    def test_existing_submission_preparation_reused_without_writes(self):
        shape = self.parse()
        self.assertIsNone(
            check_source_shape(shape, record=self.record, snapshot=self.snapshot)
        )
        packet = prepare_submission(
            record=self.record,
            snapshot=self.snapshot,
            attestations=self.attestations,
            actor_id=self.record.initiator_id,
            expected_revision=shape.expected_revision,
            now=self.now,
        )
        self.assertFalse(packet.command_available)
        self.assertEqual(self.record.state, "draft")
        self.assertEqual(self.record.revision, 1)

    def test_existing_review_preflight_is_not_authorization(self):
        for command, action in SHAPE_ACTIONS.items():
            if action == "submit":
                continue
            shape = self.parse(command=command)
            proposal = preflight(
                state="submitted",
                revision=1,
                expected_revision=shape.expected_revision,
                command=action,
                initiator=self.record.initiator_id,
                actor=uuid4(),
                attestation_purposes=[a.purpose for a in self.attestations],
            )
            self.assertEqual(proposal.next_revision, 2)
            self.assertFalse(shape.executable)
            self.assertFalse(command_available(None, command))
            self.assertEqual(self.record.state, "draft")

    def test_privileged_fields_commands_and_missing_fields_rejected(self):
        for key in (
            "actor",
            "approved",
            "assurance_proof",
            "password",
            "totp",
            "bundle",
            "idempotency_key",
        ):
            with self.subTest(key=key), self.assertRaises(CommandShapeError):
                self.parse(**{key: "sensitive-canary"})
        for command in (
            "approve",
            "ngo.onboard.review.*",
            "ngo.nominee.accept.v1",
            "ngo.primary.issue.v1",
            None,
            {},
            True,
        ):
            with self.subTest(command=command), self.assertRaises(CommandShapeError):
                self.parse(command=command)
        for field in self.value:
            value = dict(self.value)
            del value[field]
            with self.assertRaises(CommandShapeError):
                parse_shape(json.dumps(value).encode())

    def test_noncanonical_ids_and_revision_coercion_rejected(self):
        for value in (0, -1, True, 1.0, "1", None, MAX_SOURCE_REVISION + 1):
            with self.subTest(revision=value), self.assertRaises(CommandShapeError):
                self.parse(expected_revision=value)
        for field in ("record_id", "snapshot_id", "organization_id"):
            for value in (
                str(uuid4()).upper(),
                uuid4().hex,
                "00000000-0000-0000-0000-000000000000",
                [],
                1,
            ):
                with self.subTest(field=field), self.assertRaises(CommandShapeError):
                    self.parse(**{field: value})
        self.assertIsNone(self.parse(organization_id=None).organization_id)
        self.assertEqual(
            self.parse(expected_revision=MAX_SOURCE_REVISION).expected_revision,
            MAX_SOURCE_REVISION,
        )
        with self.assertRaises(CommandShapeError):
            replace(self.parse(), expected_revision=True)

    def test_duplicate_malformed_oversized_and_non_json_values_redacted(self):
        raw = json.dumps(self.value).encode()
        cases = (
            raw[:-1] + b',"expected_revision":1}',
            b"[]",
            b"null",
            b"{",
            b"\xff",
            b'"sensitive-canary"',
            b" " * (MAX_BYTES + 1),
            raw.decode(),
            raw.replace(b'"expected_revision": 1', b'"expected_revision": NaN'),
            raw.replace(b'"expected_revision": 1', b'"expected_revision": Infinity'),
        )
        for data in cases:
            with self.subTest(kind=type(data).__name__):
                with self.assertRaises(CommandShapeError) as error:
                    parse_shape(data)
                self.assertEqual(
                    str(error.exception), "Invalid controlled command shape"
                )

    def test_source_tenant_snapshot_and_revision_substitution_rejected(self):
        other_record, other_snapshot, _, _ = source_fixture()
        for changes in (
            {"record_id": str(other_record.pk)},
            {"snapshot_id": str(other_snapshot.pk)},
            {"organization_id": str(other_record.organization_id)},
            {"organization_id": None},
            {"expected_revision": 2},
        ):
            with self.subTest(changes=changes), self.assertRaises(CommandShapeError):
                check_source_shape(
                    self.parse(**changes), record=self.record, snapshot=self.snapshot
                )
        self.snapshot.record_id = other_record.pk
        with self.assertRaises(CommandShapeError):
            check_source_shape(self.parse(), record=self.record, snapshot=self.snapshot)

    def test_missing_source_fields_have_only_redacted_shape_errors(self):
        for target, fields in (
            ("record", ("pk", "organization_id", "revision")),
            ("snapshot", ("pk", "record_id", "revision")),
        ):
            for field in fields:
                record = SimpleNamespace(**vars(self.record))
                snapshot = SimpleNamespace(**vars(self.snapshot))
                delattr(record if target == "record" else snapshot, field)
                with self.subTest(target=target, field=field):
                    with self.assertRaises(CommandShapeError) as error:
                        check_source_shape(
                            self.parse(), record=record, snapshot=snapshot
                        )
                    self.assertEqual(
                        str(error.exception), "Invalid controlled command shape"
                    )
                    self.assertIsNone(error.exception.__cause__)
        for record, snapshot in ((None, self.snapshot), (self.record, None)):
            with self.assertRaises(CommandShapeError):
                check_source_shape(self.parse(), record=record, snapshot=snapshot)

    def test_source_uuid_fields_reject_equality_spoofing(self):
        class EqualToAnything:
            def __eq__(self, other):
                return True

        for target, fields in (
            ("record", ("pk", "organization_id")),
            ("snapshot", ("pk", "record_id")),
        ):
            for field in fields:
                for invalid in (EqualToAnything(), "sensitive-canary", True, None):
                    # Matching UUIDs for all other fields isolate each check.
                    record = SimpleNamespace(**vars(self.record))
                    snapshot = SimpleNamespace(**vars(self.snapshot))
                    setattr(record if target == "record" else snapshot, field, invalid)
                    with self.subTest(
                        target=target, field=field, kind=type(invalid).__name__
                    ):
                        with self.assertRaises(CommandShapeError):
                            check_source_shape(
                                self.parse(), record=record, snapshot=snapshot
                            )

    def test_unassigned_organization_source_is_valid_but_not_authority(self):
        self.record.organization_id = None
        shape = self.parse(organization_id=None)
        self.assertIsNone(
            check_source_shape(shape, record=self.record, snapshot=self.snapshot)
        )
        self.assertFalse(shape.executable)
        self.assertFalse(command_available(None, shape.command))
        self.assertEqual((self.record.state, self.record.revision), ("draft", 1))
