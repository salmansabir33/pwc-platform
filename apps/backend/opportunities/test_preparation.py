"""Nonwriting domain exercises against fictional PostgreSQL records only."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone as dt_timezone
from uuid import uuid4
from django.db import connection, transaction, IntegrityError
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from .models import Opportunity
from .preparation import PreparationError, prepare_draft, propose_transition
from .tests import organization, opportunity, ROOT, FIELDS


class PreparationTests(TestCase):
    def setUp(self):
        self.a = organization()
        self.b = organization("Fictional B")
        self.draft = opportunity(self.a, "DRAFT")
        self.published = opportunity(self.a)
        self.withdrawn = opportunity(self.a, "WITHDRAWN")
        self.now = timezone.now()
        self.fields = {"type": "JOB", "title": "Fictional role"}

    def assertRejected(self, code, callback):
        with self.assertRaises(PreparationError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(str(caught.exception), "Opportunity preparation rejected")

    def transition(self, row, action, **kwargs):
        return propose_transition(
            self.a.pk, row.pk, action, effective_at=kwargs.get("effective_at", self.now)
        )

    def test_new_draft_normalizes_bounded_text_without_creating_record(self):
        self.assertEqual(connection.vendor, "postgresql")
        count = Opportunity.objects.count()
        value = prepare_draft(
            self.a.pk,
            {
                "type": "INTERNSHIP",
                "title": "  Ｗｅｌｆａｒｅ   اردو  ",
                "summary": "  Fictional   summary ",
            },
        )
        self.assertEqual(value.title, "Welfare اردو")
        self.assertEqual(value.lookup_title, "welfare اردو")
        self.assertEqual(value.summary, "Fictional summary")
        self.assertEqual(value.proposed_state, "DRAFT")
        self.assertIsNone(value.opportunity_id)
        self.assertIsNone(value.published_at)
        self.assertEqual(Opportunity.objects.count(), count)
        self.assertFalse(value.live_execution_available)

    def test_partial_draft_keeps_owner_and_unspecified_fields(self):
        value = prepare_draft(
            self.a.pk,
            {"title": "Updated fictional title"},
            opportunity_id=self.draft.pk,
        )
        self.assertEqual(value.opportunity_id, self.draft.pk)
        self.assertEqual(value.organization_id, self.a.pk)
        self.assertEqual(value.summary, self.draft.summary)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.title, "Fictional Welfare Role")

    def test_required_fields_types_lengths_and_control_characters(self):
        invalid = [
            None,
            [],
            {},
            {"type": "JOB"},
            {"title": "Fictional"},
            dict(self.fields, type="STAFF"),
            dict(self.fields, title=True),
            dict(self.fields, title="   "),
            dict(self.fields, title="x" * 201),
            dict(self.fields, title="\x00private"),
            dict(self.fields, title="\u202eprivate"),
            dict(self.fields, summary=[]),
            dict(self.fields, summary="x" * 1001),
            dict(self.fields, summary="private\x00"),
            dict(self.fields, title=" " * 801),
        ]
        for payload in invalid:
            with self.subTest(payload_type=type(payload).__name__):
                self.assertRejected(
                    "INVALID_FIELDS", lambda: prepare_draft(self.a.pk, payload)
                )
        for kind in Opportunity.Type.values:
            self.assertEqual(
                prepare_draft(self.a.pk, dict(self.fields, type=kind)).type, kind
            )

    def test_unknown_fields_cannot_set_state_owner_ids_timestamps_or_authority(self):
        for key in (
            "id",
            "organization",
            "organization_id",
            "state",
            "lookup_title",
            "published_at",
            "withdrawn_at",
            "created_at",
            "grant",
            "is_staff",
            "notes",
            "contact_email",
        ):
            self.assertRejected(
                "INVALID_FIELDS",
                lambda: prepare_draft(
                    self.a.pk, dict(self.fields, **{key: "private-value"})
                ),
            )

    def test_cross_ngo_and_missing_snapshots_are_indistinguishable(self):
        for row in (self.draft, self.published, self.withdrawn):
            self.assertRejected(
                "SOURCE_UNAVAILABLE",
                lambda: prepare_draft(
                    self.b.pk, {"title": "Changed"}, opportunity_id=row.pk
                ),
            )
            self.assertRejected(
                "SOURCE_UNAVAILABLE",
                lambda: propose_transition(
                    self.b.pk, row.pk, "withdraw", effective_at=self.now
                ),
            )
        self.assertRejected(
            "SOURCE_UNAVAILABLE",
            lambda: prepare_draft(self.a.pk, self.fields, opportunity_id=uuid4()),
        )

    def test_invalid_identifiers_and_nonexistent_ngo_are_rejected(self):
        for value in (None, "invalid", str(self.a.pk), 1):
            self.assertRejected(
                "INVALID_IDENTIFIER", lambda: prepare_draft(value, self.fields)
            )
        self.assertRejected(
            "INVALID_FIELDS", lambda: prepare_draft(uuid4(), self.fields)
        )

    def test_publication_request_is_only_a_proposal(self):
        value = self.transition(self.draft, "request_publication")
        self.assertEqual(
            (value.source_state, value.proposed_state), ("DRAFT", "PUBLISHED")
        )
        self.assertEqual(value.published_at, self.now)
        self.assertIsNone(value.withdrawn_at)
        self.assertFalse(value.live_execution_available)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.state, "DRAFT")
        self.assertIsNone(self.draft.published_at)

    def test_withdrawal_proposal_preserves_publication_and_source_content(self):
        value = self.transition(self.published, "withdraw")
        self.assertEqual(value.proposed_state, "WITHDRAWN")
        self.assertEqual(value.published_at, self.published.published_at)
        self.assertEqual(value.withdrawn_at, self.now)
        self.assertEqual(value.title, self.published.title)
        self.published.refresh_from_db()
        self.assertEqual(self.published.state, "PUBLISHED")

    def test_invalid_transition_matrix_and_published_edits(self):
        for row, action in [
            (self.published, "request_publication"),
            (self.withdrawn, "request_publication"),
            (self.draft, "withdraw"),
            (self.withdrawn, "withdraw"),
        ]:
            self.assertRejected(
                "INVALID_TRANSITION", lambda: self.transition(row, action)
            )
        for row in (self.published, self.withdrawn):
            self.assertRejected(
                "INVALID_TRANSITION",
                lambda: prepare_draft(
                    self.a.pk, {"title": "Changed"}, opportunity_id=row.pk
                ),
            )
        for action in (
            "publish",
            "approve",
            "reopen",
            "republish",
            "delete",
            "grant",
            None,
            [],
        ):
            self.assertRejected(
                "INVALID_OPERATION", lambda: self.transition(self.draft, action)
            )

    def test_simulation_clock_is_aware_and_withdrawal_cannot_precede_publication(self):
        for clock in (None, "now", datetime(2026, 1, 1)):
            self.assertRejected(
                "INVALID_EFFECTIVE_TIME",
                lambda: self.transition(
                    self.draft, "request_publication", effective_at=clock
                ),
            )
        self.assertRejected(
            "INVALID_FIELDS",
            lambda: self.transition(
                self.published,
                "withdraw",
                effective_at=self.published.published_at - timedelta(seconds=1),
            ),
        )
        clock = self.now.astimezone(dt_timezone(timedelta(hours=5)))
        self.assertEqual(
            self.transition(
                self.draft, "request_publication", effective_at=clock
            ).published_at.tzinfo,
            dt_timezone.utc,
        )

    def test_deleted_or_changed_source_is_reloaded_on_every_call(self):
        self.transition(self.draft, "request_publication")
        Opportunity.objects.filter(pk=self.draft.pk).update(
            state="PUBLISHED", published_at=self.now
        )
        self.assertRejected(
            "INVALID_TRANSITION",
            lambda: self.transition(self.draft, "request_publication"),
        )
        Opportunity.objects.filter(pk=self.draft.pk).delete()
        self.assertRejected(
            "SOURCE_UNAVAILABLE", lambda: self.transition(self.draft, "withdraw")
        )

    def test_proposals_are_immutable_redacted_and_not_models_or_receipts(self):
        value = prepare_draft(
            self.a.pk, dict(self.fields, summary="private simulation content")
        )
        self.assertNotIn("private", repr(value))
        self.assertNotIn("Fictional role", repr(value))
        self.assertFalse(hasattr(value, "save"))
        self.assertFalse(hasattr(value, "apply"))
        with self.assertRaises(FrozenInstanceError):
            value.title = "Changed"

    def test_domain_validation_uses_no_writing_queries(self):
        before = list(Opportunity.objects.values())
        with CaptureQueriesContext(connection) as queries:
            prepare_draft(self.a.pk, self.fields)
            prepare_draft(
                self.a.pk, {"summary": "Changed"}, opportunity_id=self.draft.pk
            )
            self.transition(self.draft, "request_publication")
            self.transition(self.published, "withdraw")
        self.assertTrue(queries)
        self.assertTrue(
            all(
                item["sql"]
                .lstrip()
                .upper()
                .startswith(
                    (
                        "SELECT",
                        "SAVEPOINT",
                        "RELEASE SAVEPOINT",
                        "ROLLBACK TO SAVEPOINT",
                    )
                )
                for item in queries
            )
        )
        self.assertEqual(list(Opportunity.objects.values()), before)

    def test_proposal_matches_existing_postgresql_transition_and_owner_guards(self):
        # Fixture-only SQL exercise, not an installed writer or apply method.
        for row, action in [
            (self.draft, "request_publication"),
            (self.published, "withdraw"),
        ]:
            value = self.transition(row, action)
            Opportunity.objects.filter(pk=row.pk).update(
                state=value.proposed_state,
                published_at=value.published_at,
                withdrawn_at=value.withdrawn_at,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Opportunity.objects.filter(pk=self.draft.pk).update(organization=self.b)

    def test_existing_model_field_and_constraint_validation_is_reused(self):
        # Bypass save normalization to emulate a malformed legacy snapshot.
        Opportunity.objects.filter(pk=self.draft.pk).update(title="x" * 200)
        value = prepare_draft(self.a.pk, {"summary": ""}, opportunity_id=self.draft.pk)
        self.assertEqual(len(value.title), 200)
        self.assertRejected(
            "INVALID_FIELDS",
            lambda: prepare_draft(self.a.pk, dict(self.fields, summary="x" * 1001)),
        )

    @override_settings(PWC_ENVIRONMENT="test", PWC_OPPORTUNITIES_TEST_EXERCISE=True)
    def test_preparation_never_changes_public_disclosure(self):
        before = self.client.get(ROOT).json()
        prepare_draft(self.a.pk, self.fields)
        self.transition(self.draft, "request_publication")
        self.transition(self.published, "withdraw")
        after = self.client.get(ROOT).json()
        self.assertEqual(after, before)
        self.assertEqual(set(after["results"][0]), FIELDS)
        self.assertEqual(self.client.get(f"{ROOT}{self.draft.pk}/").status_code, 404)
        self.assertEqual(
            self.client.get(f"{ROOT}{self.withdrawn.pk}/").status_code, 404
        )

    def test_live_read_gate_remains_closed_after_preparation(self):
        self.transition(self.draft, "request_publication")
        for profile in ("development", "staging", "production"):
            with override_settings(
                PWC_ENVIRONMENT=profile, PWC_OPPORTUNITIES_TEST_EXERCISE=True
            ):
                response = self.client.get(ROOT)
                self.assertEqual(response.status_code, 503)
                self.assertEqual(
                    response.json()["error"]["code"], "OPPORTUNITIES_UNAVAILABLE"
                )
