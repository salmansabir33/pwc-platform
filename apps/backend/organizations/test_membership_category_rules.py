"""Value validation only; no DB, synthetic journey or authorization assertions."""

from django.test import SimpleTestCase
from .membership_category_rules import (
    ADMISSION_MODES,
    category_label_key,
    valid_category_label,
)
from .membership_preview import CategoryFixture, MembershipPreviewError, MODES
from uuid import UUID


class MembershipCategoryValueTests(SimpleTestCase):
    def test_shared_admission_modes_are_exact_and_immutable(self):
        self.assertIs(MODES, ADMISSION_MODES)
        self.assertEqual(ADMISSION_MODES, ("open", "approval", "invitation"))

    def test_key_collisions_preserve_supplied_display_labels(self):
        for left, right in (
            (" Ordinary  Member ", "ordinary member"),
            ("ＯＲＤＩＮＡＲＹ", "ordinary"),
            ("Straße", "STRASSE"),
            ("Café", "Cafe\u0301"),
            ("مصنوعی\u00a0 زمرہ", "مصنوعی زمرہ"),
        ):
            with self.subTest(left=left):
                self.assertEqual(category_label_key(left), category_label_key(right))
                fixture = CategoryFixture(UUID(int=1), "LOCAL", left)
                self.assertEqual(fixture.label, left)
                self.assertEqual(fixture.normalized_label, category_label_key(left))

    def test_code_point_limit_not_bytes_and_no_normalized_key_truncation(self):
        label = "\ufb03" * 250  # Compatibility expansion: 750 characters, not 250.
        self.assertTrue(valid_category_label(label))
        self.assertEqual(category_label_key(label), "ffi" * 250)
        self.assertTrue(valid_category_label("ر" * 250))
        self.assertFalse(valid_category_label("ر" * 251))

    def test_all_unicode_control_classes_and_invalid_types_are_rejected(self):
        for value in (
            None,
            True,
            1,
            [],
            {},
            b"label",
            "",
            " \u00a0 ",
            "A\nB",
            "A\x7fB",
            "A\u202eB",
            "A\ud800B",
            "A\ue000B",
            "A\u0378B",
        ):
            with self.subTest(value_type=type(value).__name__):
                self.assertFalse(valid_category_label(value))
                with self.assertRaisesMessage(ValueError, "Invalid category label"):
                    category_label_key(value)
                with self.assertRaises(MembershipPreviewError):
                    CategoryFixture(UUID(int=1), "LOCAL", value)

    def test_rejected_label_not_in_error(self):
        private = "Private category\nlabel"
        try:
            category_label_key(private)
        except ValueError as error:
            self.assertNotIn(private, str(error))
        else:
            self.fail("Invalid label was accepted")
