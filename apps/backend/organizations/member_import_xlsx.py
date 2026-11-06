"""Bounded internal XLSX -> existing CSV preview, never an intake/authority API.

Supports one visible sheet and text cells only (shared, inline or rich text).
No formula evaluation/cached values, type guessing, external resources, uploads,
DB calls or writes. Limits are engineering bounds, not approved NGO quotas.
"""

import csv
from io import BytesIO, StringIO
import posixpath
import re
from xml.etree import ElementTree as ET
from zipfile import BadZipFile, ZIP_DEFLATED, ZIP_STORED, ZipFile
import zlib

from .member_import_preview import MAX_BYTES, MAX_ROWS, ImportPreviewError, preview_csv

MAX_XLSX_BYTES = 262144
MAX_EXPANDED_BYTES = 1048576
MAX_PART_BYTES = 524288
MAX_PARTS = 32
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT = "http://schemas.openxmlformats.org/package/2006/content-types"
PART = re.compile(
    r"(?:\[Content_Types\]\.xml|_rels/\.rels|docProps/(?:app|core)\.xml|"
    r"xl/(?:workbook\.xml|_rels/workbook\.xml\.rels|sharedStrings\.xml|styles\.xml|"
    r"theme/theme1\.xml|worksheets/[A-Za-z0-9_-]+\.xml))"
)
CODES = frozenset(
    {
        "INVALID_INPUT",
        "BYTE_LIMIT",
        "UNSAFE_PACKAGE",
        "EXPANSION_LIMIT",
        "INVALID_XML",
        "UNSUPPORTED_WORKBOOK",
        "UNSUPPORTED_SHEET",
        "UNSUPPORTED_CELL",
        "FORMULA_CELL",
        "ROW_LIMIT",
        "COLUMN_COUNT",
    }
)


class XlsxPreviewError(ValueError):
    def __init__(self, code, *, record=None, column=None):
        if type(code) is not str or code not in CODES:
            raise ValueError("Unknown XLSX preview diagnostic")
        if (
            record is not None
            and (type(record) is not int or record < 1)
            or column is not None
            and (type(column) is not int or column not in (1, 2, 3))
        ):
            raise ValueError("Invalid XLSX preview diagnostic position")
        super().__init__("Invalid member XLSX preview input")
        self.code, self.record, self.column = code, record, column

    def to_diagnostic(self):
        return {"code": self.code, "record": self.record, "column": self.column}


def _invalid(code, *, record=None, column=None):
    raise XlsxPreviewError(code, record=record, column=column) from None


def _xml(raw):
    try:
        text = raw.decode("utf-8-sig")
        if "\x00" in text or re.search(r"<!\s*(?:DOCTYPE|ENTITY)", text, re.I):
            _invalid("INVALID_XML")
        return ET.fromstring(text)
    except (UnicodeError, ET.ParseError):
        _invalid("INVALID_XML")


def _package(raw):
    if type(raw) is not bytes:
        _invalid("INVALID_INPUT")
    if len(raw) > MAX_XLSX_BYTES:
        _invalid("BYTE_LIMIT")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            entries = archive.infolist()
            if (
                not entries
                or len(entries) > MAX_PARTS
                or len({p.filename for p in entries}) != len(entries)
                or any(
                    not PART.fullmatch(p.filename)
                    or p.flag_bits & 1
                    or p.compress_type not in (ZIP_STORED, ZIP_DEFLATED)
                    for p in entries
                )
            ):
                _invalid("UNSAFE_PACKAGE")
            if sum(p.file_size for p in entries) > MAX_EXPANDED_BYTES or any(
                p.file_size > MAX_PART_BYTES for p in entries
            ):
                _invalid("EXPANSION_LIMIT")
            parts = {}
            for entry in entries:
                with archive.open(entry) as stream:
                    content = stream.read(MAX_PART_BYTES + 1)
                if len(content) > MAX_PART_BYTES:
                    _invalid("EXPANSION_LIMIT")
                parts[entry.filename] = _xml(content)
            return parts
    except (BadZipFile, OSError, RuntimeError, NotImplementedError, zlib.error):
        _invalid("UNSAFE_PACKAGE")


def _target(value, base):
    # Closed subset: no parent traversals, encoded paths, URLs or backslashes.
    if (
        not value
        or any(c in value for c in ("%", ":", "\\", "?", "#"))
        or ".." in value.split("/")
    ):
        _invalid("UNSAFE_PACKAGE")
    return value.lstrip("/") if value.startswith("/") else posixpath.join(base, value)


def _relationships(root, base):
    if root is None or root.tag != f"{{{REL}}}Relationships":
        _invalid("UNSUPPORTED_WORKBOOK")
    result = {}
    for item in root:
        key = item.get("Id")
        if (
            item.tag != f"{{{REL}}}Relationship"
            or not key
            or key in result
            or item.get("TargetMode", "Internal") != "Internal"
        ):
            _invalid("UNSAFE_PACKAGE")
        result[key] = (item.get("Type"), _target(item.get("Target"), base))
    return result


def _text(node):
    """Join displayed rich-text runs only; never phonetic/extension payloads."""
    pieces = []
    for child in node:
        if child.tag == f"{{{MAIN}}}t" and not len(child):
            pieces.append(child.text or "")
        elif child.tag == f"{{{MAIN}}}r":
            for run in child:
                if run.tag == f"{{{MAIN}}}t" and not len(run):
                    pieces.append(run.text or "")
                elif run.tag != f"{{{MAIN}}}rPr":
                    _invalid("UNSUPPORTED_CELL")
        else:
            _invalid("UNSUPPORTED_CELL")
    # OOXML encodes XML-forbidden characters and literal escape prefixes this
    # way. One pass preserves _x005F_x0041_ as literal _x0041_, not "A".
    text = re.sub(
        r"_x([0-9A-Fa-f]{4})_", lambda match: chr(int(match[1], 16)), "".join(pieces)
    )
    try:
        return text.encode("utf-16", "surrogatepass").decode("utf-16")
    except UnicodeError:
        _invalid("UNSUPPORTED_CELL")


def preview_xlsx(raw, *, organization_id, catalog):
    """Return the exact existing ImportPreview; fatal errors yield no partial report.

    The caller-supplied catalog still supplies no authority. CSV enforces tenant,
    header, normalized values, formulas, duplicates and final byte/row bounds.
    XLSX-specific errors are constant codes/positions, never XML or cell content.
    """
    parts = _package(raw)
    types = parts.get("[Content_Types].xml")
    workbook = parts.get("xl/workbook.xml")
    if (
        types is None
        or types.tag != f"{{{CONTENT}}}Types"
        or workbook is None
        or workbook.tag != f"{{{MAIN}}}workbook"
    ):
        _invalid("UNSUPPORTED_WORKBOOK")
    main_type = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"
    )
    overrides = [p for p in types if p.get("PartName") == "/xl/workbook.xml"]
    if len(overrides) != 1 or overrides[0].get("ContentType") != main_type:
        _invalid("UNSUPPORTED_WORKBOOK")
    package_rels = _relationships(parts.get("_rels/.rels"), "")
    if [v for v in package_rels.values() if v[0] == OFFICE + "/officeDocument"] != [
        (OFFICE + "/officeDocument", "xl/workbook.xml")
    ]:
        _invalid("UNSUPPORTED_WORKBOOK")
    relationships = _relationships(parts.get("xl/_rels/workbook.xml.rels"), "xl")
    sheets = workbook.findall(f"{{{MAIN}}}sheets/{{{MAIN}}}sheet")
    if len(sheets) != 1 or sheets[0].get("state", "visible") != "visible":
        _invalid("UNSUPPORTED_WORKBOOK")
    selected = relationships.get(sheets[0].get(f"{{{OFFICE}}}id"))
    if (
        selected is None
        or selected[0] != OFFICE + "/worksheet"
        or selected[1] not in parts
        or len([p for p in parts if p.startswith("xl/worksheets/")]) != 1
    ):
        _invalid("UNSUPPORTED_WORKBOOK")
    shared = []
    if "xl/sharedStrings.xml" in parts:
        if (
            OFFICE + "/sharedStrings",
            "xl/sharedStrings.xml",
        ) not in relationships.values():
            _invalid("UNSUPPORTED_WORKBOOK")
        strings = parts["xl/sharedStrings.xml"]
        if strings.tag != f"{{{MAIN}}}sst" or len(strings) > (MAX_ROWS + 1) * 3:
            _invalid("UNSUPPORTED_CELL")
        for node in strings:
            if node.tag != f"{{{MAIN}}}si":
                _invalid("UNSUPPORTED_CELL")
            shared.append(_text(node))
    worksheet = parts[selected[1]]
    allowed = {
        "sheetPr",
        "dimension",
        "sheetViews",
        "sheetFormatPr",
        "cols",
        "sheetData",
        "autoFilter",
        "printOptions",
        "pageMargins",
        "pageSetup",
        "headerFooter",
    }
    if (
        worksheet.tag != f"{{{MAIN}}}worksheet"
        or any(c.tag not in {f"{{{MAIN}}}{n}" for n in allowed} for c in worksheet)
        or len(worksheet.findall(f"{{{MAIN}}}sheetData")) != 1
    ):
        _invalid("UNSUPPORTED_SHEET")
    for col in worksheet.findall(f"{{{MAIN}}}cols/{{{MAIN}}}col"):
        if col.get("hidden", "0") not in ("0", "false"):
            _invalid("UNSUPPORTED_SHEET")
    rows = []
    for row in worksheet.find(f"{{{MAIN}}}sheetData"):
        number = row.get("r", "")
        if row.tag != f"{{{MAIN}}}row" or not re.fullmatch(r"[1-9][0-9]{0,6}", number):
            _invalid("UNSUPPORTED_SHEET")
        number = int(number)
        if number > MAX_ROWS + 1:
            _invalid("ROW_LIMIT", record=number)
        if number <= len(rows) or row.get("hidden", "0") not in ("0", "false"):
            _invalid("UNSUPPORTED_SHEET", record=number)
        while len(rows) < number:
            rows.append(["", "", ""])
        previous = 0
        for cell in row:
            address = re.fullmatch(r"([A-Z]+)([1-9][0-9]{0,6})", cell.get("r", ""))
            if (
                cell.tag != f"{{{MAIN}}}c"
                or address is None
                or int(address[2]) != number
            ):
                _invalid("UNSUPPORTED_CELL", record=number)
            if address[1] not in ("A", "B", "C"):
                _invalid("COLUMN_COUNT", record=number)
            column = ord(address[1]) - ord("A") + 1
            if column <= previous:
                _invalid("UNSUPPORTED_CELL", record=number, column=column)
            previous = column
            if cell.find(f"{{{MAIN}}}f") is not None:
                _invalid("FORMULA_CELL", record=number, column=column)
            if any(c.tag not in (f"{{{MAIN}}}is", f"{{{MAIN}}}v") for c in cell):
                _invalid("UNSUPPORTED_CELL", record=number, column=column)
            kind = cell.get("t")
            value = cell.find(f"{{{MAIN}}}v")
            inline = cell.find(f"{{{MAIN}}}is")
            if (
                kind == "inlineStr"
                and inline is not None
                and value is None
                and len(cell) == 1
            ):
                text = _text(inline)
            elif (
                kind == "s" and value is not None and not len(value) and len(cell) == 1
            ):
                index = value.text or ""
                if not re.fullmatch(r"[0-9]{1,4}", index) or int(index) >= len(shared):
                    _invalid("UNSUPPORTED_CELL", record=number, column=column)
                text = shared[int(index)]
            elif kind in (None, "n") and not len(cell):
                text = ""
            else:
                _invalid("UNSUPPORTED_CELL", record=number, column=column)
            rows[-1][column - 1] = text
    # Shared strings may be referenced hundreds of times: cap converted output
    # incrementally, before a small ZIP can multiply into a large CSV allocation.
    chunks = []
    size = 0
    for row in rows:
        if sum(len(value) for value in row) > MAX_BYTES:
            raise ImportPreviewError("BYTE_LIMIT")
        stream = StringIO(newline="")
        csv.writer(stream, lineterminator="\n").writerow(row)
        chunk = stream.getvalue().encode("utf-8")
        size += len(chunk)
        if size > MAX_BYTES:
            raise ImportPreviewError("BYTE_LIMIT")
        chunks.append(chunk)
    return preview_csv(
        b"".join(chunks), organization_id=organization_id, catalog=catalog
    )
