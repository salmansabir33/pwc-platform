"""Proposed C1 rules only. DB access forbidden; no transaction/authority claims."""

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
from uuid import UUID
from django.test import SimpleTestCase
from .category_policy_preview import (
    CategoryPolicyFixture,
    CategoryPolicyPreviewError,
    CategoryVersionFixture,
    PendingPolicyFixture,
    PolicyVersionFixture,
    preview_change_category,
    preview_change_mode,
    preview_create_category,
)
from .membership_preview import CategoryFixture
from .membership_workbench import SourceRevision

A, B, ID, SECOND = (UUID(int=i) for i in range(1, 5))
AT = datetime(2026, 11, 4, tzinfo=timezone.utc)
NEXT = AT + timedelta(seconds=1)


class CategoryPolicyPreparationTests(SimpleTestCase):
    def setUp(self):
        self.definition = CategoryFixture(A, "ORDINARY", "Synthetic Ordinary")
        self.source = CategoryPolicyFixture(
            (
                PolicyVersionFixture(
                    A, 1, "approval", (CategoryVersionFixture(ID, self.definition),), AT
                ),
            ),
            (PendingPolicyFixture(ID, 1),),
        )

    def change(self, source=None, **kwargs):
        source = self.source if source is None else source
        return preview_change_category(
            source,
            source.source_revision(),
            source.current.revision,
            ID,
            source.current.categories[0].revision,
            at=NEXT,
            **kwargs,
        )

    def assert_code(self, code, callback):
        with self.assertRaises(CategoryPolicyPreviewError) as caught:
            callback()
        self.assertEqual(caught.exception.to_diagnostic(), {"code": code})
        return caught.exception

    def test_create_keeps_server_identity_and_history_separate_from_reference(self):
        result = preview_create_category(
            self.source,
            self.source.source_revision(),
            1,
            replace(
                self.definition, reference="ASSOCIATE", label="Synthetic Associate"
            ),
            SECOND,
            at=NEXT,
        )
        self.assertEqual(
            (result.current.revision, len(result.current.categories)), (2, 2)
        )
        self.assertEqual(result.current.categories[1].revision, 1)
        self.assertEqual(result.versions[0], self.source.current)
        self.assertEqual(result.current.categories[1].id, SECOND)
        self.assertEqual(result.pending, self.source.pending)

    def test_tenant_mismatch_rejected_without_echo(self):
        error = self.assert_code(
            "TENANT_MISMATCH",
            lambda: preview_create_category(
                self.source,
                self.source.source_revision(),
                1,
                replace(self.definition, organization_id=B),
                SECOND,
                at=NEXT,
            ),
        )
        self.assertNotIn(str(B), str(error))
        self.assertNotIn(self.definition.label, str(error))

    def test_same_labels_and_references_allowed_in_another_ngo_fixture(self):
        other = PolicyVersionFixture(
            B,
            1,
            "approval",
            (
                CategoryVersionFixture(
                    SECOND, replace(self.definition, organization_id=B)
                ),
            ),
            AT,
        )
        self.assertNotEqual(
            CategoryPolicyFixture((other,)).source_revision(),
            self.source.source_revision(),
        )

    def test_empty_policy_can_create_first_category(self):
        empty = CategoryPolicyFixture((PolicyVersionFixture(A, 1, "approval", (), AT),))
        result = preview_create_category(
            empty, empty.source_revision(), 1, self.definition, ID, at=NEXT
        )
        self.assertEqual(result.to_summary()["category_count"], 1)

    def test_duplicate_ids_rejected(self):
        self.assert_code(
            "DUPLICATE_CATEGORY_ID",
            lambda: preview_create_category(
                self.source,
                self.source.source_revision(),
                1,
                replace(self.definition, reference="OTHER"),
                ID,
                at=NEXT,
            ),
        )

    def test_duplicate_references_rejected(self):
        self.assert_code(
            "DUPLICATE_CATEGORY_REFERENCE",
            lambda: preview_create_category(
                self.source,
                self.source.source_revision(),
                1,
                replace(self.definition, label="Another"),
                SECOND,
                at=NEXT,
            ),
        )

    def test_unicode_normalized_active_label_uniqueness(self):
        for label in (
            " synthetic   ordinary ",
            "Ｓｙｎｔｈｅｔｉｃ Ordinary",
            "SYNTHETIC ORDINARY",
        ):
            with self.subTest(label=label):
                self.assert_code(
                    "DUPLICATE_CATEGORY_LABEL",
                    lambda: preview_create_category(
                        self.source,
                        self.source.source_revision(),
                        1,
                        replace(self.definition, reference="OTHER", label=label),
                        SECOND,
                        at=NEXT,
                    ),
                )

    def test_rename_preserves_original_display_label_and_identity(self):
        result = self.change(label="مصنوعی زمرہ")
        self.assertEqual(
            result.versions[0].categories[0].definition.label, self.definition.label
        )
        current = result.current.categories[0]
        self.assertEqual(
            (current.id, current.definition.reference, current.revision),
            (ID, "ORDINARY", 2),
        )
        self.assertEqual(current.definition.label, "مصنوعی زمرہ")

    def test_rename_checks_other_active_label(self):
        source = preview_create_category(
            self.source,
            self.source.source_revision(),
            1,
            replace(self.definition, reference="OTHER", label="Associate"),
            SECOND,
            at=NEXT,
        )
        self.assert_code(
            "DUPLICATE_CATEGORY_LABEL", lambda: self.change(source, label="ASSOCIATE")
        )

    def test_noop_not_a_new_version(self):
        self.assert_code(
            "UNCHANGED_CATEGORY", lambda: self.change(label=self.definition.label)
        )
        self.assert_code(
            "UNCHANGED_POLICY",
            lambda: preview_change_mode(
                self.source, self.source.source_revision(), 1, "approval", at=NEXT
            ),
        )

    def test_deactivation_retains_history_and_pending_binding(self):
        result = self.change(deactivate=True)
        self.assertTrue(result.versions[0].categories[0].definition.active)
        self.assertFalse(result.current.categories[0].definition.active)
        self.assertEqual(result.to_summary()["pending_review_count"], 1)
        self.assertEqual(result.pending, self.source.pending)
        self.assertEqual(result.to_summary()["category_count"], 1)
        self.assertEqual(result.to_summary()["active_category_count"], 0)

    def test_deactivated_reference_cannot_be_reused(self):
        source = self.change(deactivate=True)
        self.assert_code(
            "DUPLICATE_CATEGORY_REFERENCE",
            lambda: preview_create_category(
                source,
                source.source_revision(),
                2,
                replace(self.definition, label="New display"),
                SECOND,
                at=NEXT,
            ),
        )

    def test_inactive_labels_do_not_reserve_active_names(self):
        source = self.change(deactivate=True)
        result = preview_create_category(
            source,
            source.source_revision(),
            2,
            replace(self.definition, reference="OTHER"),
            SECOND,
            at=NEXT,
        )
        self.assertEqual(result.to_summary()["active_category_count"], 1)

    def test_inactive_category_cannot_be_edited_or_reactivated(self):
        source = self.change(deactivate=True)
        self.assert_code(
            "INACTIVE_CATEGORY", lambda: self.change(source, label="Changed")
        )
        self.assert_code(
            "INACTIVE_CATEGORY", lambda: self.change(source, deactivate=True)
        )

    def test_policy_change_retains_pending_version_for_explicit_rereview(self):
        for mode in ("open", "invitation"):
            result = preview_change_mode(
                self.source, self.source.source_revision(), 1, mode, at=NEXT
            )
            self.assertEqual(result.current.mode, mode)
            self.assertEqual(result.pending[0].policy_revision, 1)
            self.assertEqual(result.to_summary()["pending_review_count"], 1)
            self.assertEqual(self.source.to_summary()["pending_review_count"], 0)

    def test_even_unrelated_category_change_requires_rereview_proposal(self):
        result = preview_create_category(
            self.source,
            self.source.source_revision(),
            1,
            replace(self.definition, reference="OTHER", label="Other"),
            SECOND,
            at=NEXT,
        )
        self.assertEqual(result.to_summary()["pending_review_count"], 1)

    def test_stale_whole_source_policy_and_category_revision(self):
        self.assert_code(
            "SOURCE_REVISION_CONFLICT",
            lambda: preview_change_mode(
                self.source, SourceRevision("0" * 64), 1, "open", at=NEXT
            ),
        )
        self.assert_code(
            "POLICY_REVISION_CONFLICT",
            lambda: preview_change_mode(
                self.source, self.source.source_revision(), 2, "open", at=NEXT
            ),
        )
        self.assert_code(
            "CATEGORY_REVISION_CONFLICT",
            lambda: preview_change_category(
                self.source,
                self.source.source_revision(),
                1,
                ID,
                2,
                label="Changed",
                at=NEXT,
            ),
        )

    def test_unknown_target_and_invalid_mode(self):
        self.assert_code(
            "UNKNOWN_CATEGORY",
            lambda: preview_change_category(
                self.source,
                self.source.source_revision(),
                1,
                SECOND,
                1,
                label="Changed",
                at=NEXT,
            ),
        )
        self.assert_code(
            "INVALID_INPUT",
            lambda: preview_change_mode(
                self.source, self.source.source_revision(), 1, "admin", at=NEXT
            ),
        )

    def test_future_revision_does_not_rebind_pending(self):
        self.assert_code(
            "INVALID_INPUT",
            lambda: replace(self.source, pending=(PendingPolicyFixture(ID, 2),)),
        )
        self.assert_code(
            "INVALID_INPUT",
            lambda: replace(self.source, pending=(PendingPolicyFixture(SECOND, 1),)),
        )

    def test_proposals_are_deterministic_not_commits_or_idempotency_receipts(self):
        before = self.source.source_revision()
        one, two = self.change(label="First"), self.change(label="Second")
        self.assertEqual(one.current.revision, two.current.revision)
        self.assertNotEqual(one.source_revision(), two.source_revision())
        self.assertEqual(self.change(label="First"), one)
        self.assertEqual(self.source.source_revision(), before)
        self.assert_code(
            "SOURCE_REVISION_CONFLICT",
            lambda: preview_change_mode(one, before, 2, "open", at=NEXT),
        )
        with self.assertRaises(FrozenInstanceError):
            one.pending = ()

    def test_effective_time_is_monotonic_utc_simulation_only(self):
        for at in (
            AT - timedelta(seconds=1),
            AT.replace(tzinfo=None),
            "2026-11-04",
            datetime(2026, 11, 4, tzinfo=timezone(timedelta(hours=5))),
        ):
            self.assert_code(
                "INVALID_EFFECTIVE_TIME",
                lambda: preview_change_mode(
                    self.source, self.source.source_revision(), 1, "open", at=at
                ),
            )
        # Same-time changes ordered by revision. No scheduled/backdated live writer exists.
        self.assertEqual(
            preview_change_mode(
                self.source, self.source.source_revision(), 1, "open", at=AT
            ).current.revision,
            2,
        )

    def test_immutable_history_cannot_drop_or_reidentify_categories(self):
        for categories in (
            (),
            (replace(self.source.current.categories[0], id=SECOND),),
            (
                replace(
                    self.source.current.categories[0],
                    definition=replace(self.definition, reference="REPLACED"),
                    revision=2,
                ),
            ),
        ):
            after = replace(
                self.source.current,
                revision=2,
                categories=categories,
                operation="category_updated",
            )
            self.assert_code(
                "INVALID_INPUT",
                lambda: CategoryPolicyFixture((self.source.current, after)),
            )

    def test_boolean_revisions_mutable_collections_and_non_uuid_ids_rejected(self):
        for callback in (
            lambda: replace(self.source.current, revision=True),
            lambda: replace(self.source, versions=list(self.source.versions)),
            lambda: CategoryVersionFixture(str(ID), self.definition),
            lambda: PendingPolicyFixture(ID, True),
            lambda: self.change(label="Changed", deactivate=True),
        ):
            self.assert_code("INVALID_INPUT", callback)

    def test_minimal_summary_has_no_identifiers_names_or_times(self):
        encoded = json.dumps(self.change(label="Private fixture label").to_summary())
        for private in (
            str(A),
            str(ID),
            self.definition.reference,
            self.definition.label,
            "Private fixture label",
            AT.isoformat(),
        ):
            self.assertNotIn(private, encoded)
        self.assertNotIn(
            "Private fixture label", repr(self.change(label="Private fixture label"))
        )
        self.assertFalse(self.source.to_summary()["commit_available"])
        self.assertTrue(self.source.to_summary()["non_authoritative"])
