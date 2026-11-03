"""PWC-05B nonwriting CSV preview. No authorization, intake adapter or commit.

The template is internal preparation vocabulary, not an accepted membership API.
Supplied reference catalogs are caller data, never authenticated NGO authority.
No matching name creates a person/User, and no report is an executable import.
"""

import csv
from dataclasses import dataclass, field
from io import StringIO
import re
import unicodedata
from uuid import UUID

MAX_BYTES = 65536
MAX_ROWS = 200
HEADERS = ("record_reference", "display_name", "category_reference")
REFERENCE = re.compile(r"[A-Z][A-Z0-9_-]{0,63}", re.ASCII)


FILE_CODES = frozenset(
    {
        "INVALID_INPUT",
        "BYTE_LIMIT",
        "CATALOG_TENANT_MISMATCH",
        "INVALID_ENCODING",
        "CONTROL_CHARACTER",
        "INVALID_HEADER",
        "EMPTY_FILE",
        "COLUMN_COUNT",
        "ROW_LIMIT",
        "MALFORMED_CSV",
    }
)
ERROR_CODES = (
    "FORMULA_CELL",
    "INVALID_REFERENCE",
    "INVALID_NAME",
    "UNKNOWN_CATEGORY",
    "EXISTING_REFERENCE",
    "DUPLICATE_REFERENCE",
)
WARNING_CODES = ("POSSIBLE_NAME_DUPLICATE",)
REPORT_VERSION = "pwc.member-import-preview.internal.v1"


class ImportPreviewError(ValueError):
    def __init__(self, code="INVALID_INPUT", *, record=None, column=None):
        if type(code) is not str or code not in FILE_CODES:
            raise ValueError("Unknown preview diagnostic code")
        if (
            record is not None
            and (type(record) is not int or record < 1)
            or column is not None
            and (type(column) is not int or column not in (1, 2, 3))
        ):
            raise ValueError("Invalid preview diagnostic position")
        super().__init__("Invalid member import preview input")
        self.code, self.record, self.column = code, record, column

    def to_diagnostic(self):
        return {"code": self.code, "record": self.record, "column": self.column}


def _invalid(code="INVALID_INPUT", *, record=None, column=None):
    raise ImportPreviewError(code, record=record, column=column) from None


def _reference(value):
    return type(value) is str and REFERENCE.fullmatch(value) is not None


def _valid_name(value):
    return (
        bool(value)
        and len(value) <= 250
        and not any(unicodedata.category(c).startswith("C") for c in value)
    )


@dataclass(frozen=True, slots=True)
class TemplateColumn:
    name: str
    required: bool
    max_characters: int

    def __post_init__(self):
        expected = dict(zip(HEADERS, (64, 250, 64)))
        if (
            type(self.name) is not str
            or self.name not in expected
            or self.required is not True
            or type(self.max_characters) is not int
            or self.max_characters != expected[self.name]
        ):
            _invalid()


@dataclass(frozen=True, slots=True)
class CsvTemplate:
    version: str
    columns: tuple[TemplateColumn, ...]
    encoding: str
    max_bytes: int
    max_rows: int
    sample_records: tuple[tuple[str, str, str], ...]

    def __post_init__(self):
        if (
            type(self.version) is not str
            or type(self.encoding) is not str
            or self.version != "pwc.member-import.csv.internal.v1"
            or self.encoding != "utf-8-sig"
            or type(self.max_bytes) is not int
            or self.max_bytes != MAX_BYTES
            or type(self.max_rows) is not int
            or self.max_rows != MAX_ROWS
            or type(self.columns) is not tuple
            or any(type(c) is not TemplateColumn for c in self.columns)
            or tuple(c.name for c in self.columns) != HEADERS
            or type(self.sample_records) is not tuple
            or not 1 <= len(self.sample_records) <= MAX_ROWS
        ):
            _invalid()
        for row in self.sample_records:
            if (
                type(row) is not tuple
                or len(row) != 3
                or any(type(v) is not str for v in row)
                or not _reference(row[0])
                or not _valid_name(row[1])
                or row[1] != unicodedata.normalize("NFC", row[1].strip())
                or row[1].startswith(("=", "+", "-", "@"))
                or not _reference(row[2])
            ):
                _invalid()
        if (
            len({row[0] for row in self.sample_records}) != len(self.sample_records)
            or len(self.sample_csv()) > self.max_bytes
        ):
            _invalid()

    def sample_csv(self):
        stream = StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(tuple(c.name for c in self.columns))
        writer.writerows(self.sample_records)
        return stream.getvalue().encode("utf-8")


TEMPLATE = CsvTemplate(
    "pwc.member-import.csv.internal.v1",
    tuple(
        TemplateColumn(name, True, limit) for name, limit in zip(HEADERS, (64, 250, 64))
    ),
    "utf-8-sig",
    MAX_BYTES,
    MAX_ROWS,
    (
        ("MEMBER_A", "Synthetic Person A", "ORDINARY"),
        ("MEMBER_B", "Synthetic Person B", "ORDINARY"),
    ),
)


@dataclass(frozen=True, slots=True)
class PreviewDiagnostic:
    code: str
    record: int
    column: int
    related_records: tuple[int, ...] = ()

    def __post_init__(self):
        if (
            type(self.code) is not str
            or self.code not in ERROR_CODES + WARNING_CODES
            or type(self.record) is not int
            or self.record < 2
            or type(self.column) is not int
            or self.column not in (1, 2, 3)
            or type(self.related_records) is not tuple
            or any(
                type(n) is not int or n < 2 or n == self.record
                for n in self.related_records
            )
            or tuple(sorted(set(self.related_records))) != self.related_records
        ):
            _invalid()
        expected = {
            "INVALID_REFERENCE": 1,
            "INVALID_NAME": 2,
            "UNKNOWN_CATEGORY": 3,
            "EXISTING_REFERENCE": 1,
            "DUPLICATE_REFERENCE": 1,
            "POSSIBLE_NAME_DUPLICATE": 2,
        }
        if self.code in expected and self.column != expected[self.code]:
            _invalid()

    @property
    def severity(self):
        return "warning" if self.code in WARNING_CODES else "error"

    def to_summary(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "record": self.record,
            "column": self.column,
            "column_name": HEADERS[self.column - 1],
            "related_records": list(self.related_records),
        }


@dataclass(frozen=True, slots=True, repr=False)
class PreviewCatalog:
    organization_id: UUID
    categories: frozenset[str]
    existing_references: frozenset[str] = frozenset()

    def __post_init__(self):
        if type(self.organization_id) is not UUID or not self.organization_id.int:
            _invalid()
        for values in (self.categories, self.existing_references):
            if type(values) is not frozenset or any(not _reference(v) for v in values):
                _invalid()


@dataclass(frozen=True, slots=True, repr=False)
class PreviewRow:
    number: int
    # Invalid rows carry positions/codes only, never raw rejected cell content.
    values: tuple[str, str, str] | None
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    diagnostics: tuple[PreviewDiagnostic, ...] = ()

    def __post_init__(self):
        if (
            type(self.number) is not int
            or not 2 <= self.number <= MAX_ROWS + 1
            or type(self.errors) is not tuple
            or type(self.warnings) is not tuple
            or any(type(c) is not str or c not in ERROR_CODES for c in self.errors)
            or any(type(c) is not str or c not in WARNING_CODES for c in self.warnings)
            or len(set(self.errors)) != len(self.errors)
            or len(set(self.warnings)) != len(self.warnings)
            or bool(self.errors) != (self.values is None)
            or self.values is not None
            and (
                type(self.values) is not tuple
                or len(self.values) != 3
                or any(type(v) is not str for v in self.values)
            )
            or type(self.diagnostics) is not tuple
            or any(
                type(d) is not PreviewDiagnostic or d.record != self.number
                for d in self.diagnostics
            )
        ):
            _invalid()
        if {d.code for d in self.diagnostics} != set(self.errors + self.warnings):
            _invalid()


@dataclass(frozen=True, slots=True, repr=False)
class ImportPreview:
    organization_id: UUID
    rows: tuple[PreviewRow, ...]
    commit_available: bool = field(default=False, init=False)

    def __post_init__(self):
        if (
            type(self.organization_id) is not UUID
            or not self.organization_id.int
            or type(self.rows) is not tuple
            or not 1 <= len(self.rows) <= MAX_ROWS
            or any(
                type(r) is not PreviewRow or r.number != number
                for number, r in enumerate(self.rows, 2)
            )
        ):
            _invalid()
        if any(
            n > len(self.rows) + 1
            for row in self.rows
            for d in row.diagnostics
            for n in d.related_records
        ):
            _invalid()

    @property
    def accepted_count(self):
        # Structural acceptance only, never membership admission/authority.
        return sum(not row.errors for row in self.rows)

    @property
    def rejected_count(self):
        return len(self.rows) - self.accepted_count

    @property
    def warning_count(self):
        return sum(len(row.warnings) for row in self.rows)

    def to_summary(self):
        """Fresh value-free internal JSON projection, NOT an accepted wire API.

        Never serialize this object with dataclasses.asdict: valid row values
        intentionally remain available only to the in-memory preparation caller.
        """
        return {
            "format": REPORT_VERSION,
            "template": TEMPLATE.version,
            "organization_id": str(self.organization_id),
            "non_authoritative": True,
            "commit_available": False,
            "row_count": len(self.rows),
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "warning_count": self.warning_count,
            "rows": [
                {
                    "record": row.number,
                    "errors": list(row.errors),
                    "warnings": list(row.warnings),
                    "diagnostics": [d.to_summary() for d in row.diagnostics],
                }
                for row in self.rows
            ],
        }

    def __repr__(self):
        return f"<ImportPreview rows={len(self.rows)} non-authoritative>"


def preview_csv(raw, *, organization_id, catalog):
    """Validate an in-memory bounded template; no DB, logs, lookup or side effect.

    CSV record numbers (header=1) are used, not physical line numbers. Duplicate
    references invalidate ALL occurrences. Duplicate names only warn: never merge.
    Empty files/header-only files are invalid, not successful empty imports.
    """
    if (
        type(raw) is not bytes
        or type(catalog) is not PreviewCatalog
        or type(organization_id) is not UUID
        or not organization_id.int
    ):
        _invalid()
    if len(raw) > TEMPLATE.max_bytes:
        _invalid("BYTE_LIMIT")
    if organization_id != catalog.organization_id:
        _invalid("CATALOG_TENANT_MISMATCH")
    next_record = 1
    try:
        text = raw.decode(TEMPLATE.encoding)
        if any(ord(c) < 32 and c not in "\r\n\t" for c in text):
            _invalid("CONTROL_CHARACTER")
        reader = csv.reader(StringIO(text, newline=""), strict=True)
        if tuple(next(reader)) != tuple(c.name for c in TEMPLATE.columns):
            _invalid("INVALID_HEADER", record=1)
        next_record = 2
        rows = []
        for number, cells in enumerate(reader, 2):
            if number > TEMPLATE.max_rows + 1:
                _invalid("ROW_LIMIT", record=number)
            if len(cells) != len(TEMPLATE.columns):
                _invalid("COLUMN_COUNT", record=number)
            values = tuple(unicodedata.normalize("NFC", c.strip()) for c in cells)
            errors = []
            diagnostics = []

            def issue(code, column):
                if code not in errors:
                    errors.append(code)
                diagnostics.append(PreviewDiagnostic(code, number, column))

            for column, value in enumerate(values, 1):
                if value.startswith(("=", "+", "-", "@")):
                    issue("FORMULA_CELL", column)
            reference, name, category = values
            if not _reference(reference):
                issue("INVALID_REFERENCE", 1)
            if not _valid_name(name):
                issue("INVALID_NAME", 2)
            if not _reference(category) or category not in catalog.categories:
                issue("UNKNOWN_CATEGORY", 3)
            if reference in catalog.existing_references:
                issue("EXISTING_REFERENCE", 1)
            rows.append((number, values, errors, diagnostics))
            next_record = number + 1
        if not rows:
            _invalid("EMPTY_FILE")
    except UnicodeError:
        _invalid("INVALID_ENCODING")
    except csv.Error:
        _invalid("MALFORMED_CSV", record=next_record)
    except StopIteration:
        _invalid("EMPTY_FILE")
    references = {}
    names = {}
    for number, (reference, name, _), _, _ in rows:
        references.setdefault(reference, []).append(number)
        names.setdefault(name.casefold(), []).append(number)
    result = []
    for number, values, errors, diagnostics in rows:
        if len(references[values[0]]) > 1:
            errors.append("DUPLICATE_REFERENCE")
            diagnostics.append(
                PreviewDiagnostic(
                    "DUPLICATE_REFERENCE",
                    number,
                    1,
                    tuple(n for n in references[values[0]] if n != number),
                )
            )
        warnings = (
            ("POSSIBLE_NAME_DUPLICATE",) if len(names[values[1].casefold()]) > 1 else ()
        )
        if warnings:
            diagnostics.append(
                PreviewDiagnostic(
                    "POSSIBLE_NAME_DUPLICATE",
                    number,
                    2,
                    tuple(n for n in names[values[1].casefold()] if n != number),
                )
            )
        diagnostics.sort(
            key=lambda d: (d.column, (ERROR_CODES + WARNING_CODES).index(d.code))
        )
        result.append(
            PreviewRow(
                number,
                None if errors else values,
                tuple(errors),
                warnings,
                tuple(diagnostics),
            )
        )
    return ImportPreview(organization_id, tuple(result))
