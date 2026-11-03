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


class ImportPreviewError(ValueError):
    pass


def _invalid():
    raise ImportPreviewError("Invalid member import preview input") from None


def _reference(value):
    return type(value) is str and REFERENCE.fullmatch(value) is not None


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


@dataclass(frozen=True, slots=True, repr=False)
class ImportPreview:
    organization_id: UUID
    rows: tuple[PreviewRow, ...]
    commit_available: bool = field(default=False, init=False)

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
        or len(raw) > MAX_BYTES
        or type(catalog) is not PreviewCatalog
        or type(organization_id) is not UUID
        or not organization_id.int
        or organization_id != catalog.organization_id
    ):
        _invalid()
    try:
        text = raw.decode("utf-8-sig")
        if any(ord(c) < 32 and c not in "\r\n\t" for c in text):
            _invalid()
        reader = csv.reader(StringIO(text, newline=""), strict=True)
        if tuple(next(reader)) != HEADERS:
            _invalid()
        rows = []
        for number, cells in enumerate(reader, 2):
            if number > MAX_ROWS + 1 or len(cells) != 3:
                _invalid()
            values = tuple(unicodedata.normalize("NFC", c.strip()) for c in cells)
            errors = []
            if any(v.startswith(("=", "+", "-", "@")) for v in values):
                errors.append("FORMULA_CELL")
            reference, name, category = values
            if not _reference(reference):
                errors.append("INVALID_REFERENCE")
            if (
                not name
                or len(name) > 250
                or any(unicodedata.category(c).startswith("C") for c in name)
            ):
                errors.append("INVALID_NAME")
            if not _reference(category) or category not in catalog.categories:
                errors.append("UNKNOWN_CATEGORY")
            if reference in catalog.existing_references:
                errors.append("EXISTING_REFERENCE")
            rows.append((number, values, errors))
        if not rows:
            _invalid()
    except (UnicodeError, csv.Error, StopIteration, ValueError):
        _invalid()
    references = {}
    names = {}
    for _, (reference, name, _), _ in rows:
        references[reference] = references.get(reference, 0) + 1
        names[name.casefold()] = names.get(name.casefold(), 0) + 1
    result = []
    for number, values, errors in rows:
        if references[values[0]] > 1:
            errors.append("DUPLICATE_REFERENCE")
        warnings = (
            ("POSSIBLE_NAME_DUPLICATE",) if names[values[1].casefold()] > 1 else ()
        )
        result.append(
            PreviewRow(number, None if errors else values, tuple(errors), warnings)
        )
    return ImportPreview(organization_id, tuple(result))
