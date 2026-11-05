"""Real in-memory OOXML packages; no mocked parser, intake or authority claims."""

import csv
from io import BytesIO, StringIO
from pathlib import Path
from unittest.mock import patch
from uuid import UUID
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from django.test import SimpleTestCase, TestCase
from .member_import_preview import (
    HEADERS,
    ImportPreviewError,
    PreviewCatalog,
    preview_csv,
)
from .member_import_xlsx import (
    CONTENT,
    MAIN,
    OFFICE,
    REL,
    MAX_PART_BYTES,
    MAX_XLSX_BYTES,
    XlsxPreviewError,
    preview_xlsx,
)

TENANT = UUID("11111111-1111-4111-8111-111111111111")
OTHER = UUID("22222222-2222-4222-8222-222222222222")
CATALOG = PreviewCatalog(TENANT, frozenset({"ORDINARY"}), frozenset({"OLD"}))


def package(rows, *, shared=False):
    sheet = ET.Element(f"{{{MAIN}}}worksheet")
    data = ET.SubElement(sheet, f"{{{MAIN}}}sheetData")
    strings = ET.Element(f"{{{MAIN}}}sst")
    for number, values in enumerate(rows, 1):
        row = ET.SubElement(data, f"{{{MAIN}}}row", r=str(number))
        for index, value in enumerate(values):
            cell = ET.SubElement(
                row,
                f"{{{MAIN}}}c",
                r=f"{chr(65 + index)}{number}",
                t="s" if shared else "inlineStr",
            )
            if shared:
                ET.SubElement(cell, f"{{{MAIN}}}v").text = str(len(strings))
                ET.SubElement(
                    ET.SubElement(strings, f"{{{MAIN}}}si"), f"{{{MAIN}}}t"
                ).text = value
            else:
                ET.SubElement(
                    ET.SubElement(cell, f"{{{MAIN}}}is"), f"{{{MAIN}}}t"
                ).text = value
    workbook = ET.Element(f"{{{MAIN}}}workbook")
    ET.SubElement(
        ET.SubElement(workbook, f"{{{MAIN}}}sheets"),
        f"{{{MAIN}}}sheet",
        {"name": "Private canary", "sheetId": "1", f"{{{OFFICE}}}id": "rId1"},
    )
    rels = ET.Element(f"{{{REL}}}Relationships")
    ET.SubElement(
        rels,
        f"{{{REL}}}Relationship",
        Id="rId1",
        Type=OFFICE + "/worksheet",
        Target="worksheets/sheet1.xml",
    )
    rootrels = ET.Element(f"{{{REL}}}Relationships")
    ET.SubElement(
        rootrels,
        f"{{{REL}}}Relationship",
        Id="rId1",
        Type=OFFICE + "/officeDocument",
        Target="xl/workbook.xml",
    )
    types = ET.Element(f"{{{CONTENT}}}Types")
    ET.SubElement(
        types,
        f"{{{CONTENT}}}Override",
        PartName="/xl/workbook.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
    )
    parts = {
        "[Content_Types].xml": types,
        "_rels/.rels": rootrels,
        "xl/workbook.xml": workbook,
        "xl/_rels/workbook.xml.rels": rels,
        "xl/worksheets/sheet1.xml": sheet,
    }
    if shared:
        ET.SubElement(
            rels,
            f"{{{REL}}}Relationship",
            Id="rId2",
            Type=OFFICE + "/sharedStrings",
            Target="sharedStrings.xml",
        )
        parts["xl/sharedStrings.xml"] = strings
    return parts


def archive(parts):
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as zipped:
        for name, root in parts.items():
            zipped.writestr(
                name,
                root
                if isinstance(root, bytes)
                else ET.tostring(root, encoding="utf-8", xml_declaration=True),
            )
    return stream.getvalue()


def sheet_data(parts):
    return parts["xl/worksheets/sheet1.xml"].find(f"{{{MAIN}}}sheetData")


class XlsxPreviewTests(SimpleTestCase):
    def test_independent_xlsxwriter_file_matches_csv_without_writer_dependency(self):
        raw = (
            Path(__file__).resolve().parents[3]
            / "tests/fixtures/member-import-preview/text-cells.xlsx"
        ).read_bytes()
        expected = preview_csv(
            (
                ",".join(HEADERS)
                + "\nA,Synthetic Person A,ORDINARY\nB,فرضی رکن,ORDINARY\nA,Synthetic Person A,ORDINARY\n"
            ).encode(),
            organization_id=TENANT,
            catalog=CATALOG,
        )
        result = preview_xlsx(raw, organization_id=TENANT, catalog=CATALOG)
        self.assertEqual(result, expected)
        self.assertEqual(result.accepted_count, 1)
        self.assertEqual(result.rejected_count, 2)

    def parse(self, parts, tenant=TENANT):
        return preview_xlsx(archive(parts), organization_id=tenant, catalog=CATALOG)

    def rejected(self, parts, code):
        with self.assertRaises(XlsxPreviewError) as error:
            self.parse(parts)
        self.assertEqual(error.exception.code, code)
        self.assertEqual(str(error.exception), "Invalid member XLSX preview input")
        self.assertNotIn("Private", repr(error.exception))
        return error.exception.to_diagnostic()

    def test_shared_and_inline_match_csv_exactly_including_diagnostics_and_unicode(
        self,
    ):
        rows = [
            HEADERS,
            ("A", "فرضی رکن", "ORDINARY"),
            ("A", "فرضی رکن", "ORDINARY"),
            ("OLD", "Other", "MISSING"),
            ("C", "=SUM(1,2)", "ORDINARY"),
            ("D", " e\u0301 ", "ORDINARY"),
        ]
        stream = StringIO(newline="")
        csv.writer(stream, lineterminator="\n").writerows(rows)
        expected = preview_csv(
            stream.getvalue().encode(), organization_id=TENANT, catalog=CATALOG
        )
        for shared in (True, False):
            result = self.parse(package(rows, shared=shared))
            self.assertEqual(result, expected)
            summary = str(result.to_summary())
            for private in ("فرضی رکن", "SUM", "ORDINARY", "MISSING", "Private canary"):
                self.assertNotIn(private, summary)
            self.assertFalse(result.commit_available)

    def test_rich_text_and_absolute_opc_targets(self):
        parts = package([HEADERS, ("A", "", "ORDINARY")])
        inline = sheet_data(parts)[1][1][0]
        inline.clear()
        for value in ("Synthetic ", "Person"):
            ET.SubElement(
                ET.SubElement(inline, f"{{{MAIN}}}r"), f"{{{MAIN}}}t"
            ).text = value
        parts["xl/_rels/workbook.xml.rels"][0].set(
            "Target", "/xl/worksheets/sheet1.xml"
        )
        self.assertEqual(self.parse(parts).rows[0].values[1], "Synthetic Person")

    def test_missing_cells_and_sparse_rows_remain_visible_validation_errors(self):
        parts = package(
            [HEADERS, ("A", "Synthetic", "ORDINARY"), ("B", "Other", "ORDINARY")]
        )
        data = sheet_data(parts)
        del data[1][1]
        data[2].set("r", "4")
        for cell in data[2]:
            cell.set("r", cell.get("r")[0] + "4")
        result = self.parse(parts)
        self.assertEqual([r.number for r in result.rows], [2, 3, 4])
        self.assertIn("INVALID_NAME", result.rows[0].errors)
        self.assertIn("INVALID_REFERENCE", result.rows[1].errors)
        self.assertEqual(result.accepted_count, 1)

    def test_wrong_tenant_and_invalid_catalog_never_return_report(self):
        parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")])
        with self.assertRaises(ImportPreviewError) as error:
            self.parse(parts, OTHER)
        self.assertEqual(error.exception.code, "CATALOG_TENANT_MISMATCH")
        with self.assertRaises(ImportPreviewError):
            preview_xlsx(archive(parts), organization_id=TENANT, catalog={})

    def test_formulas_fail_with_position_without_trusting_cached_values(self):
        for shared in (True, False):
            parts = package(
                [HEADERS, ("A", "Cached private name", "ORDINARY")], shared=shared
            )
            cell = sheet_data(parts)[1][1]
            ET.SubElement(
                cell, f"{{{MAIN}}}f"
            ).text = 'WEBSERVICE("https://private.invalid")'
            self.assertEqual(
                self.rejected(parts, "FORMULA_CELL"),
                {"code": "FORMULA_CELL", "record": 2, "column": 2},
            )

    def test_no_numeric_boolean_error_date_or_cached_string_coercion(self):
        for kind in ("n", "b", "e", "d", "str", None):
            parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")])
            cell = sheet_data(parts)[1][1]
            cell.clear()
            cell.set("r", "B2")
            if kind:
                cell.set("t", kind)
            ET.SubElement(cell, f"{{{MAIN}}}v").text = "123"
            self.rejected(parts, "UNSUPPORTED_CELL")

    def test_invalid_shared_index_or_duplicate_cell_value_rejected(self):
        for index in ("-1", "9999", "1.0", "private-value"):
            parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")], shared=True)
            sheet_data(parts)[1][1][0].text = index
            self.rejected(parts, "UNSUPPORTED_CELL")
        parts = package([HEADERS], shared=True)
        ET.SubElement(sheet_data(parts)[0][0], f"{{{MAIN}}}v").text = "0"
        self.rejected(parts, "UNSUPPORTED_CELL")

    def test_second_hidden_or_orphan_sheet_rejected(self):
        for state in ("hidden", "veryHidden"):
            parts = package([HEADERS])
            parts["xl/workbook.xml"][0][0].set("state", state)
            self.rejected(parts, "UNSUPPORTED_WORKBOOK")
        parts = package([HEADERS])
        parts["xl/worksheets/sheet2.xml"] = parts["xl/worksheets/sheet1.xml"]
        self.rejected(parts, "UNSUPPORTED_WORKBOOK")

    def test_external_or_unsafe_relationships_never_fetch_or_resolve_files(self):
        for mode, target in (
            ("External", "https://private.invalid"),
            ("Internal", "../sheet.xml"),
            ("Internal", "file:///private"),
            ("Internal", "%2e%2e/sheet.xml"),
        ):
            parts = package([HEADERS])
            relation = parts["xl/_rels/workbook.xml.rels"][0]
            relation.set("TargetMode", mode)
            relation.set("Target", target)
            self.rejected(parts, "UNSAFE_PACKAGE")

    def test_macros_path_traversals_unexpected_parts_and_duplicate_zip_members(self):
        for path in (
            "xl/vbaProject.bin",
            "../private",
            "xl/worksheets/../sheet.xml",
            "xl/externalLinks/externalLink1.xml",
        ):
            parts = package([HEADERS])
            parts[path] = b"private"
            self.rejected(parts, "UNSAFE_PACKAGE")
        raw = archive(package([HEADERS]))
        stream = BytesIO(raw)
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with ZipFile(stream, "a") as zipped:
                zipped.writestr("xl/workbook.xml", b"private")
        with self.assertRaises(XlsxPreviewError) as error:
            preview_xlsx(stream.getvalue(), organization_id=TENANT, catalog=CATALOG)
        self.assertEqual(error.exception.code, "UNSAFE_PACKAGE")

    def test_xml_entities_doctype_invalid_utf8_and_malformed_xml_rejected(self):
        for raw in (
            b'<!DOCTYPE foo [<!ENTITY value "private">]><foo>&value;</foo>',
            b'<!DOCTYPE foo SYSTEM "file:///private"><foo/>',
            b"\xff",
            b"<broken",
            b"<x>\0</x>",
        ):
            parts = package([HEADERS])
            parts["docProps/core.xml"] = raw
            self.rejected(parts, "INVALID_XML")

    def test_compressed_expansion_and_input_byte_bounds(self):
        parts = package([HEADERS])
        parts["docProps/core.xml"] = b" " * (MAX_PART_BYTES + 1)
        self.rejected(parts, "EXPANSION_LIMIT")
        for value, code in (
            (b"bad-zip", "UNSAFE_PACKAGE"),
            ("not bytes", "INVALID_INPUT"),
            (b"0" * (MAX_XLSX_BYTES + 1), "BYTE_LIMIT"),
        ):
            with self.assertRaises(XlsxPreviewError) as error:
                preview_xlsx(value, organization_id=TENANT, catalog=CATALOG)
            self.assertEqual(error.exception.code, code)

    def test_rows_columns_and_order_are_bounded_and_not_silently_discarded(self):
        parts = package([HEADERS, ("A", "Synthetic", "ORDINARY", "Private")])
        self.rejected(parts, "COLUMN_COUNT")
        for number, code in (
            ("202", "ROW_LIMIT"),
            ("1", "UNSUPPORTED_SHEET"),
            ("-1", "UNSUPPORTED_SHEET"),
        ):
            parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")])
            sheet_data(parts)[1].set("r", number)
            self.rejected(parts, code)
        parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")])
        sheet_data(parts)[1][1].set("r", "B3")
        self.rejected(parts, "UNSUPPORTED_CELL")

    def test_merge_hyperlink_and_hidden_rows_rejected_not_partially_imported(self):
        for tag in ("mergeCells", "hyperlinks", "conditionalFormatting"):
            parts = package([HEADERS])
            ET.SubElement(parts["xl/worksheets/sheet1.xml"], f"{{{MAIN}}}{tag}")
            self.rejected(parts, "UNSUPPORTED_SHEET")
        parts = package([HEADERS])
        sheet_data(parts)[0].set("hidden", "1")
        self.rejected(parts, "UNSUPPORTED_SHEET")

    def test_header_empty_sheet_and_csv_byte_limit_reuse_original_errors(self):
        for rows, code in (
            ([], "EMPTY_FILE"),
            ([HEADERS], "EMPTY_FILE"),
            ([("wrong", "header", "values")], "INVALID_HEADER"),
            (
                [HEADERS] + [(f"R{i}", "A" * 250, "ORDINARY") for i in range(200)],
                "BYTE_LIMIT",
            ),
        ):
            # 250 ASCII chars are below CSV byte bound; Unicode makes the last case exceed it.
            if code == "BYTE_LIMIT":
                rows = [HEADERS] + [
                    (f"R{i}", "ر" * 250, "ORDINARY") for i in range(200)
                ]
            with self.assertRaises(ImportPreviewError) as error:
                self.parse(package(rows))
            self.assertEqual(error.exception.code, code)

    def test_ooxml_escapes_are_decoded_once_with_surrogate_pair_handling(self):
        cases = (("_x005F_x0041_", "_x0041_"), ("_xD83D__xDE00_", "😀"))
        for encoded, expected in cases:
            result = self.parse(package([HEADERS, ("A", encoded, "ORDINARY")]))
            self.assertEqual(result.rows[0].values[1], expected)
        result = self.parse(package([HEADERS, ("A", "a_x000A_b", "ORDINARY")]))
        self.assertIn("INVALID_NAME", result.rows[0].errors)
        self.assertIsNone(result.rows[0].values)
        self.rejected(
            package([HEADERS, ("A", "_xD83D_", "ORDINARY")]), "UNSUPPORTED_CELL"
        )

    def test_repeated_shared_strings_cannot_expand_past_converted_csv_budget(self):
        parts = package([HEADERS, ("A", "private" * 20000, "ORDINARY")], shared=True)
        # Repeat the same large shared-string reference without duplicating XML.
        data = sheet_data(parts)
        import copy

        for number in range(3, 202):
            row = copy.deepcopy(data[1])
            row.set("r", str(number))
            for cell in row:
                cell.set("r", cell.get("r")[0] + str(number))
            data.append(row)
        with self.assertRaises(ImportPreviewError) as error:
            self.parse(parts)
        self.assertEqual(error.exception.code, "BYTE_LIMIT")

    def test_total_expansion_part_count_and_truncated_zip_are_bounded(self):
        parts = package([HEADERS])
        for name in ("docProps/core.xml", "docProps/app.xml", "xl/styles.xml"):
            parts[name] = b" " * 400000
        self.rejected(parts, "EXPANSION_LIMIT")
        parts = package([HEADERS])
        for number in range(32):
            parts[f"xl/worksheets/extra{number}.xml"] = b"<x/>"
        self.rejected(parts, "UNSAFE_PACKAGE")
        with self.assertRaises(XlsxPreviewError) as error:
            preview_xlsx(
                archive(package([HEADERS]))[:-40],
                organization_id=TENANT,
                catalog=CATALOG,
            )
        self.assertEqual(error.exception.code, "UNSAFE_PACKAGE")

    def test_parse_does_not_use_files_network_models_or_identity_linkage(self):
        parts = package([HEADERS, ("A", "Synthetic", "ORDINARY")])
        with (
            patch("builtins.open", side_effect=AssertionError("No filesystem")),
            patch("socket.socket", side_effect=AssertionError("No network")),
        ):
            self.assertEqual(self.parse(parts).accepted_count, 1)


class XlsxDatabaseBoundaryTests(TestCase):
    def test_same_reference_other_ngo_is_not_authority_and_evaluation_has_zero_queries(
        self,
    ):
        from accounts.models import User
        from organizations.models import Organization

        before = (User.objects.count(), Organization.objects.count())
        raw = archive(package([HEADERS, ("A", "Synthetic", "ORDINARY")]))
        with self.assertNumQueries(0):
            result = preview_xlsx(raw, organization_id=TENANT, catalog=CATALOG)
            self.assertFalse(result.commit_available)
            with self.assertRaises(ImportPreviewError):
                preview_xlsx(raw, organization_id=OTHER, catalog=CATALOG)
        self.assertEqual(before, (User.objects.count(), Organization.objects.count()))
