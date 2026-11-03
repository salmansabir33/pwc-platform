"""Synthetic import preparation, not a claim of member-management authority."""

from dataclasses import FrozenInstanceError
from io import StringIO
import json
from uuid import uuid4
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase
from .member_import_preview import (
    HEADERS,
    MAX_BYTES,
    MAX_ROWS,
    ImportPreviewError,
    PreviewCatalog,
    preview_csv,
)
from .models import Organization, OrganizationAccess

HEADER = (",".join(HEADERS) + "\n").encode()


class MemberImportPreviewTests(SimpleTestCase):
    def setUp(self):
        self.organization = uuid4()
        self.catalog = PreviewCatalog(
            self.organization, frozenset({"ORDINARY"}), frozenset({"EXISTING"})
        )

    def parse(self, rows, **kwargs):
        return preview_csv(
            HEADER + rows,
            organization_id=self.organization,
            catalog=kwargs.get("catalog", self.catalog),
        )

    def test_valid_unicode_csv_preview_is_nonwriting_and_immutable(self):
        report = self.parse(
            'A,  فرضی نام  ,ORDINARY\nB,"Synthetic, Person",ORDINARY\n'.encode()
        )
        self.assertEqual(report.rows[0].values, ("A", "فرضی نام", "ORDINARY"))
        self.assertEqual(report.rows[1].values[1], "Synthetic, Person")
        self.assertFalse(report.commit_available)
        self.assertNotIn("Synthetic", repr(report))
        self.assertNotIn("فرضی", repr(report.rows[0]))
        with self.assertRaises(FrozenInstanceError):
            report.commit_available = True

    def test_duplicate_reference_invalidates_every_occurrence(self):
        report = self.parse(b"A,Synthetic One,ORDINARY\nA,Synthetic Two,ORDINARY\n")
        for row in report.rows:
            self.assertIn("DUPLICATE_REFERENCE", row.errors)
            self.assertIsNone(row.values)

    def test_same_name_warns_but_never_merges_or_links(self):
        report = self.parse(
            b"A,Synthetic Person,ORDINARY\nB,synthetic person,ORDINARY\n"
        )
        self.assertEqual(len(report.rows), 2)
        for row in report.rows:
            self.assertEqual(row.errors, ())
            self.assertEqual(row.warnings, ("POSSIBLE_NAME_DUPLICATE",))
            self.assertFalse(hasattr(row, "user_id"))

    def test_existing_reference_and_unknown_category_are_row_errors(self):
        report = self.parse(b"EXISTING,Canary Name,UNKNOWN\n")
        self.assertEqual(
            report.rows[0].errors, ("UNKNOWN_CATEGORY", "EXISTING_REFERENCE")
        )
        self.assertIsNone(report.rows[0].values)

    def test_formula_and_control_cells_are_not_retained(self):
        for name in ("=DDE", "+SUM", "-1", "@CANARY", "\t=CANARY", "Hidden\u202eName"):
            with self.subTest(name=name):
                row = self.parse(f"A,{name},ORDINARY\n".encode()).rows[0]
                self.assertTrue(row.errors)
                self.assertIsNone(row.values)

    def test_header_encoding_structure_and_empty_input_fail_redacted(self):
        cases = (
            b"",
            HEADER,
            b"name,phone\nA,B\n",
            HEADER + b'A,"unterminated',
            HEADER + b"A,B,C,extra\n",
            HEADER + b"A,\xff,ORDINARY\n",
            HEADER + b"A,N\x00ame,ORDINARY\n",
            HEADER + b"\n",
        )
        for raw in cases:
            with self.subTest(raw=raw), self.assertRaises(ImportPreviewError) as error:
                preview_csv(
                    raw, organization_id=self.organization, catalog=self.catalog
                )
            self.assertEqual(
                str(error.exception), "Invalid member import preview input"
            )

    def test_authority_and_identity_columns_are_not_importable(self):
        for extra in ("user_id", "role", "status", "organization_id", "grant"):
            raw = (
                ",".join(HEADERS) + "," + extra + "\nA,Synthetic,ORDINARY,PRIVILEGED\n"
            ).encode()
            with self.subTest(column=extra), self.assertRaises(ImportPreviewError):
                preview_csv(
                    raw, organization_id=self.organization, catalog=self.catalog
                )

    def test_utf8_bom_and_crlf_supported(self):
        report = preview_csv(
            b"\xef\xbb\xbf" + HEADER + b"A,Synthetic,ORDINARY\r\n",
            organization_id=self.organization,
            catalog=self.catalog,
        )
        self.assertEqual(report.rows[0].errors, ())

    def test_byte_row_and_name_bounds(self):
        with self.assertRaises(ImportPreviewError):
            self.parse(b"x" * MAX_BYTES)
        rows = b"".join(
            f"R{i},Synthetic {i},ORDINARY\n".encode() for i in range(MAX_ROWS)
        )
        self.assertEqual(len(self.parse(rows).rows), MAX_ROWS)
        with self.assertRaises(ImportPreviewError):
            self.parse(rows + b"OVER,Synthetic,ORDINARY\n")
        self.assertIn(
            "INVALID_NAME",
            self.parse(b"A," + b"x" * 251 + b",ORDINARY\n").rows[0].errors,
        )

    def test_catalog_tenant_mismatch_and_mutable_inputs_deny(self):
        with self.assertRaises(ImportPreviewError):
            self.parse(
                b"A,Synthetic,ORDINARY\n",
                catalog=PreviewCatalog(uuid4(), frozenset({"ORDINARY"})),
            )
        with self.assertRaises(ImportPreviewError):
            PreviewCatalog(self.organization, {"ORDINARY"})
        with self.assertRaises(ImportPreviewError):
            preview_csv(
                "not bytes", organization_id=self.organization, catalog=self.catalog
            )

    def test_command_has_only_synthetic_cases_and_nonsecret_reports(self):
        output = StringIO()
        call_command("preview_member_import_fixture", scenario="valid", stdout=output)
        data = json.loads(output.getvalue())
        self.assertFalse(data["commit_available"])
        self.assertTrue(data["synthetic_only"])
        self.assertNotIn("Synthetic Person", output.getvalue())
        with self.assertRaises(CommandError):
            call_command(
                "preview_member_import_fixture", scenario="duplicate", stdout=StringIO()
            )

    def test_all_cli_paths_remain_database_free_including_system_checks(self):
        # SimpleTestCase forbids DB queries. Unlike call_command defaults, do
        # not skip Django checks: exercise the CLI's ordinary execution path.
        for scenario in ("valid", "duplicate", "invalid"):
            output = StringIO()
            with self.subTest(scenario=scenario):
                if scenario == "valid":
                    call_command(
                        "preview_member_import_fixture",
                        scenario=scenario,
                        stdout=output,
                        skip_checks=False,
                    )
                else:
                    with self.assertRaises(CommandError):
                        call_command(
                            "preview_member_import_fixture",
                            scenario=scenario,
                            stdout=output,
                            skip_checks=False,
                        )
                report = json.loads(output.getvalue())
                self.assertEqual(
                    set(report),
                    {
                        "synthetic_only",
                        "commit_available",
                        "rows",
                        "format",
                        "template",
                        "organization_id",
                        "non_authoritative",
                        "row_count",
                        "accepted_count",
                        "rejected_count",
                        "warning_count",
                    },
                )
                self.assertTrue(report["synthetic_only"])
                self.assertIs(report["commit_available"], False)
                for row in report["rows"]:
                    self.assertEqual(
                        set(row), {"record", "errors", "warnings", "diagnostics"}
                    )
                self.assertNotIn("Synthetic Person", output.getvalue())
                self.assertNotIn("=FORMULA", output.getvalue())

    def test_programmatic_scenario_validation_cannot_bypass_fixture_allowlist(self):
        for scenario in ("private-canary.csv", "../private", "", None, []):
            output = StringIO()
            with self.subTest(kind=type(scenario).__name__):
                with self.assertRaises(CommandError) as error:
                    call_command(
                        "preview_member_import_fixture",
                        scenario=scenario,
                        stdout=output,
                    )
                self.assertEqual(
                    str(error.exception), "Unknown synthetic preview scenario"
                )
                self.assertEqual(output.getvalue(), "")


class ImportPreviewPostgreSQLTests(TestCase):
    def test_reference_catalogs_remain_separate_and_preview_creates_no_identity_or_access(
        self,
    ):
        a = Organization.objects.create(name="Synthetic A")
        b = Organization.objects.create(name="Synthetic B")
        user_count = get_user_model().objects.count()
        access_count = OrganizationAccess.objects.count()
        raw = HEADER + b"EXISTING,Synthetic Same Person,ORDINARY\n"
        with self.assertNumQueries(0):
            first = preview_csv(
                raw,
                organization_id=a.pk,
                catalog=PreviewCatalog(
                    a.pk, frozenset({"ORDINARY"}), frozenset({"EXISTING"})
                ),
            )
            second = preview_csv(
                raw,
                organization_id=b.pk,
                catalog=PreviewCatalog(b.pk, frozenset({"ORDINARY"})),
            )
            summaries = (first.to_summary(), second.to_summary())
        self.assertEqual(tuple(s["accepted_count"] for s in summaries), (0, 1))
        self.assertEqual(
            tuple(s["organization_id"] for s in summaries), (str(a.pk), str(b.pk))
        )
        self.assertIn("EXISTING_REFERENCE", first.rows[0].errors)
        self.assertEqual(second.rows[0].errors, ())
        self.assertEqual(second.organization_id, b.pk)
        self.assertFalse(first.commit_available or second.commit_available)
        self.assertEqual(get_user_model().objects.count(), user_count)
        self.assertEqual(OrganizationAccess.objects.count(), access_count)
