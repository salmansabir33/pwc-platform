"""Internal preview contracts, never wire approval or member-management authority."""

from dataclasses import FrozenInstanceError, replace
from io import StringIO
import json
from pathlib import Path
from uuid import uuid4
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from .member_import_preview import (
    HEADERS,
    TEMPLATE,
    REPORT_VERSION,
    ImportPreviewError,
    PreviewCatalog,
    PreviewDiagnostic,
    PreviewRow,
    ImportPreview,
    TemplateColumn,
    preview_csv,
)
from .member_import_fixtures import (
    FIXTURE_CSV,
    SCENARIOS,
    UnknownFixtureScenario,
    preview_fixture,
)

FIXTURES = Path(__file__).resolve().parents[3] / "tests/fixtures/member-import-preview"
HEADER = (",".join(HEADERS) + "\n").encode()


class MemberImportContractTests(SimpleTestCase):
    def setUp(self):
        self.organization = uuid4()
        self.catalog = PreviewCatalog(
            self.organization, frozenset({"ORDINARY"}), frozenset({"B"})
        )

    def parse(self, rows):
        return preview_csv(
            HEADER + rows, organization_id=self.organization, catalog=self.catalog
        )

    def test_template_is_exact_required_immutable_and_sample_validates(self):
        self.assertEqual(tuple(c.name for c in TEMPLATE.columns), HEADERS)
        self.assertTrue(all(c.required for c in TEMPLATE.columns))
        self.assertEqual(
            tuple(c.max_characters for c in TEMPLATE.columns), (64, 250, 64)
        )
        self.assertEqual(
            (TEMPLATE.encoding, TEMPLATE.max_bytes, TEMPLATE.max_rows),
            ("utf-8-sig", 65536, 200),
        )
        report = preview_csv(
            TEMPLATE.sample_csv(),
            organization_id=self.organization,
            catalog=self.catalog,
        )
        self.assertEqual((report.accepted_count, report.rejected_count), (2, 0))
        with self.assertRaises(FrozenInstanceError):
            TEMPLATE.columns = ()
        with self.assertRaises(FrozenInstanceError):
            TEMPLATE.columns[0].required = False

    def test_descriptor_rejects_drift_and_unsafe_samples(self):
        for changes in (
            {"columns": TEMPLATE.columns[::-1]},
            {"columns": list(TEMPLATE.columns)},
            {"version": "public-api-v1"},
            {"encoding": "latin1"},
            {"max_bytes": True},
            {"max_rows": 201},
            {"sample_records": ()},
            {"sample_records": TEMPLATE.sample_records * 2},
            {"sample_records": (("A", "=FORMULA", "ORDINARY"),)},
            {"sample_records": (("A", "  Synthetic  ", "ORDINARY"),)},
        ):
            with self.subTest(changes=changes), self.assertRaises(ImportPreviewError):
                replace(TEMPLATE, **changes)
        for args in (
            ("user_id", True, 64),
            (HEADERS[0], False, 64),
            (HEADERS[0], True, 65),
        ):
            with self.assertRaises(ImportPreviewError):
                TemplateColumn(*args)

    def test_counts_include_warnings_on_rejected_rows_but_not_membership_acceptance(
        self,
    ):
        report = self.parse(
            b"A,Secret Name,ORDINARY\nB,Same Name,UNKNOWN\nA,Other Name,ORDINARY\nC,same name,ORDINARY\n"
        )
        summary = report.to_summary()
        self.assertEqual(
            (
                summary["row_count"],
                summary["accepted_count"],
                summary["rejected_count"],
                summary["warning_count"],
            ),
            (4, 1, 3, 2),
        )
        self.assertTrue(summary["non_authoritative"])
        self.assertIs(summary["commit_available"], False)
        self.assertEqual(summary["organization_id"], str(self.organization))
        self.assertEqual(summary["format"], REPORT_VERSION)
        self.assertEqual(
            report.rows[1].errors, ("UNKNOWN_CATEGORY", "EXISTING_REFERENCE")
        )
        self.assertNotIn("Secret Name", json.dumps(summary))
        self.assertNotIn("Same Name", json.dumps(summary))
        self.assertNotIn('UNKNOWN"', json.dumps(summary))

    def test_duplicate_conflicts_list_all_other_records_deterministically(self):
        raw = b"A,One,ORDINARY\nC,Two,ORDINARY\nA,Three,ORDINARY\nA,Four,ORDINARY\n"
        report = self.parse(raw)
        self.assertEqual(tuple(r.number for r in report.rows), (2, 3, 4, 5))
        for row in (report.rows[0], report.rows[2], report.rows[3]):
            diagnostic = next(
                d for d in row.diagnostics if d.code == "DUPLICATE_REFERENCE"
            )
            self.assertEqual(
                diagnostic.related_records,
                tuple(n for n in (2, 4, 5) if n != row.number),
            )
            self.assertEqual(
                (diagnostic.column, diagnostic.to_summary()["column_name"]),
                (1, HEADERS[0]),
            )
        self.assertEqual(report.to_summary(), self.parse(raw).to_summary())

    def test_logical_records_not_physical_lines_and_no_multiline_values_serialized(
        self,
    ):
        report = self.parse(
            b'A,"Secret\nName",ORDINARY\nC,Two,ORDINARY\nA,Three,ORDINARY\n'
        )
        self.assertEqual(tuple(r.number for r in report.rows), (2, 3, 4))
        self.assertIn("INVALID_NAME", report.rows[0].errors)
        self.assertEqual(report.rows[0].diagnostics[-1].code, "INVALID_NAME")
        self.assertEqual(report.rows[0].diagnostics[0].related_records, (4,))
        self.assertNotIn("Secret", json.dumps(report.to_summary()))

    def test_formula_diagnostics_locate_each_cell_without_repeating_legacy_codes(self):
        report = self.parse(b"=CANARY,+CANARY,@CANARY\n")
        row = report.rows[0]
        self.assertEqual(row.errors.count("FORMULA_CELL"), 1)
        self.assertEqual(
            tuple(d.column for d in row.diagnostics if d.code == "FORMULA_CELL"),
            (1, 2, 3),
        )
        self.assertEqual(
            tuple(d.column for d in row.diagnostics),
            tuple(sorted(d.column for d in row.diagnostics)),
        )
        self.assertNotIn("CANARY", json.dumps(report.to_summary()))

    def test_value_free_file_errors_have_stable_codes_and_record_positions(self):
        cases = (
            (b"", "EMPTY_FILE", None),
            (HEADER, "EMPTY_FILE", None),
            (b"secret,headers\n", "INVALID_HEADER", 1),
            (HEADER + b"A,Name,ORDINARY,private\n", "COLUMN_COUNT", 2),
            (HEADER + b'A,"secret', "MALFORMED_CSV", 2),
            (HEADER + b'A,"one\ntwo",ORDINARY\nC,"secret', "MALFORMED_CSV", 3),
            (HEADER + b"A,\xff,ORDINARY\n", "INVALID_ENCODING", None),
            (b"x" * 65537, "BYTE_LIMIT", None),
            (HEADER + b"A,private\x00,ORDINARY\n", "CONTROL_CHARACTER", None),
        )
        for raw, code, record in cases:
            with (
                self.subTest(code=code),
                self.assertRaises(ImportPreviewError) as error,
            ):
                preview_csv(
                    raw, organization_id=self.organization, catalog=self.catalog
                )
            self.assertEqual(
                error.exception.to_diagnostic(),
                {"code": code, "record": record, "column": None},
            )
            self.assertEqual(
                str(error.exception), "Invalid member import preview input"
            )
            self.assertNotIn("secret", json.dumps(error.exception.to_diagnostic()))

    def test_row_limit_error_reports_logical_record_202(self):
        with self.assertRaises(ImportPreviewError) as error:
            self.parse(b"A,Synthetic,ORDINARY\n" * 201)
        self.assertEqual(
            error.exception.to_diagnostic(),
            {"code": "ROW_LIMIT", "record": 202, "column": None},
        )

    def test_tenant_mismatch_error_and_summary_remain_bound_without_database_lookup(
        self,
    ):
        with self.assertRaises(ImportPreviewError) as error:
            preview_csv(
                TEMPLATE.sample_csv(), organization_id=uuid4(), catalog=self.catalog
            )
        self.assertEqual(error.exception.code, "CATALOG_TENANT_MISMATCH")
        report = self.parse(b"A,Private Person,ORDINARY\n")
        self.assertEqual(report.to_summary()["organization_id"], str(self.organization))
        self.assertNotIn("Private Person", json.dumps(report.to_summary()))

    def test_summary_is_a_defensive_value_free_projection_not_dataclass_export(self):
        report = self.parse(
            b"A,secret@example.invalid,ORDINARY\nA,Private Person,ORDINARY\n"
        )
        first = report.to_summary()
        self.assertNotIn("secret@example.invalid", json.dumps(first))
        first["rows"][0]["diagnostics"][0]["related_records"].append(999)
        first["rows"][0]["errors"].append("NOT_A_CODE")
        self.assertNotIn("999", json.dumps(report.to_summary()))
        self.assertNotIn("NOT_A_CODE", json.dumps(report.to_summary()))
        with self.assertRaises(FrozenInstanceError):
            report.rows[0].diagnostics[0].column = 2

    def test_diagnostic_objects_reject_unknown_codes_and_bad_positions(self):
        for args in (
            ("PRIVATE", 2, 1, ()),
            ("UNKNOWN_CATEGORY", 2, 1, ()),
            ("DUPLICATE_REFERENCE", True, 1, ()),
            ("DUPLICATE_REFERENCE", 2, 1, (4, 3)),
            ("DUPLICATE_REFERENCE", 2, 1, (2,)),
        ):
            with self.subTest(args=args), self.assertRaises(ImportPreviewError):
                PreviewDiagnostic(*args)

    def test_checked_fictional_inputs_and_cli_reports_match_golden_files(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                self.assertEqual(
                    (FIXTURES / f"{scenario}.csv").read_bytes(), FIXTURE_CSV[scenario]
                )
                expected = json.loads((FIXTURES / f"{scenario}.json").read_text())
                self.assertEqual(
                    dict(preview_fixture(scenario).to_summary(), synthetic_only=True),
                    expected,
                )
                output = StringIO()
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
                self.assertEqual(json.loads(output.getvalue()), expected)

    def test_fixture_inputs_are_immutable_and_unsupported_scenarios_redacted(self):
        with self.assertRaises(TypeError):
            FIXTURE_CSV["valid"] = b"private"
        for value in ("../private.csv", None, [], "", True):
            with self.assertRaises(UnknownFixtureScenario) as error:
                preview_fixture(value)
            self.assertEqual(str(error.exception), "Unknown synthetic preview scenario")

    def test_report_constructors_reject_mutable_or_unredactable_metadata(self):
        for args in (
            (2, ("A", "Name", "ORDINARY"), [], ()),
            (2, None, ("private-canary@example.invalid",), ()),
            (2, ["A", "Name", "ORDINARY"], (), ()),
        ):
            with self.assertRaises(ImportPreviewError):
                PreviewRow(*args)
        report = self.parse(b"A,Private Name,ORDINARY\n")
        for rows in (list(report.rows), (), report.rows * 2):
            with self.assertRaises(ImportPreviewError):
                ImportPreview(self.organization, rows)
        with self.assertRaises(ImportPreviewError):
            ImportPreview("private-canary", report.rows)
