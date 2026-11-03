# Member CSV preview — nonwriting preparation

This is the independently safe part of PWC-05B/ORG-10, not a live membership
service. It makes no database query/write and performs no authority lookup.
`commit_available` is always false. No upload/API/client gateway is installed.

## Run a complete synthetic example

With the existing test environment configured:

```sh
python apps/backend/manage.py preview_member_import_fixture --scenario valid
python apps/backend/manage.py preview_member_import_fixture --scenario duplicate
python apps/backend/manage.py preview_member_import_fixture --scenario invalid
```

Only these built-in fictional scenarios are accepted; there is no file/data input
option. Valid exits 0. Invalid/duplicate scenarios emit row numbers and issue codes,
then exit nonzero. The command prints no names, raw CSV, private identifiers or
credentials and does not provision people or grant anything.

## Internal preview engine

`organizations.member_import_preview.preview_csv` accepts UTF-8 bytes, an exact
organization UUID and an immutable same-organization `PreviewCatalog`. Catalog
contents are supplied by the caller, **not authenticated source authority**.
The provisional closed template is:

```csv
record_reference,display_name,category_reference
MEMBER_A,Synthetic Person A,ORDINARY
```

It is not an approved membership API, identity schema or canonical import format.
Limits: 64 KiB, 200 data records, three columns; reference/category handles use
bounded uppercase ASCII identifiers, names at most 250 characters. UTF-8 BOM,
CRLF, quoted commas and Unicode names are supported. Names trim/NFC-normalize;
case-folding only finds warning candidates, never identities. Malformed/empty
files fail with a value-free error. Invalid rows retain only record position and
issue codes; valid values are available in the in-memory report only. Reprs omit
cell values. Nothing persists, logs, exports, merges or links to a User.

Within-file duplicate references invalidate **all** occurrences; known reference
conflicts and unknown categories are row errors. Same names only warn. Categories,
existing records and identity evidence must eventually come from an authorized,
locked, tenant-scoped source, never this caller catalog alone. Do not log valid-row
values or attach reports to general telemetry. XLSX, file intake, persistent staging,
commit/undo/idempotency, roster reading, user claims and clients remain unbuilt.

## Exact remaining dependency

Existing synthetic bundles contain only context/private-stub/settings reads, not
member or import rights. Live 05A/05B needs accepted admission/category semantics,
explicit member/import capability and issuer/source contracts, privacy/intake/
retention and duplicate-resolution rules, then atomic revision/audit/idempotency
and separate verified claim/link design. This preview closes none of those gates.
04D additional public fields and privileged profile writers remain excluded too.

## Structured template and report contracts (internal v1)

`TEMPLATE` is a frozen, validated `CsvTemplate`; its ordered frozen columns are:

| Column (one-based) | Name | Required | Maximum characters |
| --- | --- | --- | --- |
| 1 | `record_reference` | yes | 64 |
| 2 | `display_name` | yes | 250 |
| 3 | `category_reference` | yes | 64 |

There are **no optional columns**. The descriptor rejects reordered/extra columns,
changed limits/encoding/version, mutable definitions, noncanonical/unsafe sample
cells and duplicate sample references. `TEMPLATE.sample_csv()` emits only its
fictional examples. The template version is `pwc.member-import.csv.internal.v1`:
UTF-8 with optional BOM (`utf-8-sig` decoding), 65,536 bytes including header/BOM,
200 data records. Sample output is UTF-8 without BOM. The fictional `ORDINARY`
category is not an approved admission rule or a promise about any real catalog.

`preview_csv` remains the **only parser**. Reports, rows, diagnostics and their
nested tuples are immutable. Constructor validation rejects mutable report
metadata, unsupported codes and inconsistent record positions. In-memory valid
row values remain intentionally private; **never export `dataclasses.asdict`**.
Use `report.to_summary()` for a fresh JSON-compatible, value-free projection:

- `format`: `pwc.member-import-preview.internal.v1`; `template`: the above version.
- `organization_id`: the supplied catalog-bound UUID, not source authentication.
- `non_authoritative: true`, `commit_available: false` unconditionally.
- `row_count`, `accepted_count`, `rejected_count`, `warning_count`. Accepted means
  no structural row error, **not admitted membership**. Accepted + rejected equals
  total. Warnings count warning diagnostics, including those on rejected rows;
  a warning alone never rejects a row. Fatal file errors yield no partial report.
- `rows`: ordered logical CSV records (header = 1, first data record = 2), with
  legacy `errors`/`warnings` code lists and structured `diagnostics`. A diagnostic
  has `code`, `severity` (`error`/`warning`), `record`, one-based `column`,
  `column_name`, and sorted `related_records` excluding itself. Records are not
  physical line numbers for quoted multiline fields.

Stable row codes:

| Code | Severity | Column | Meaning |
| --- | --- | --- | --- |
| `FORMULA_CELL` | error | each offending column | leading formula marker after trimming |
| `INVALID_REFERENCE` | error | 1 | invalid bounded reference syntax |
| `INVALID_NAME` | error | 2 | missing, oversized or control/format-bearing name |
| `UNKNOWN_CATEGORY` | error | 3 | invalid category syntax or absent from caller catalog |
| `EXISTING_REFERENCE` | error | 1 | present in same-tenant caller reference catalog |
| `DUPLICATE_REFERENCE` | error | 1 | every within-file occurrence rejected; all other positions listed |
| `POSSIBLE_NAME_DUPLICATE` | warning | 2 | case-folded normalized name candidate; all other positions listed |

Rows preserve input order. Diagnostics sort by column, then the table's code
order; legacy error ordering is retained for compatibility. A formula in multiple
cells gets one diagnostic per cell but only one legacy error code. Existing
reference conflicts have no related imported record unless also duplicated in
this CSV. Same-name candidates are never identity evidence or link targets.

Fatal `ImportPreviewError` retains its constant value-free message and exposes
`to_diagnostic()` (`code`, nullable `record`, nullable `column`). Codes are
`INVALID_INPUT`, `BYTE_LIMIT`, `CATALOG_TENANT_MISMATCH`, `INVALID_ENCODING`,
`CONTROL_CHARACTER`, `INVALID_HEADER`, `EMPTY_FILE`, `COLUMN_COUNT`, `ROW_LIMIT`,
`MALFORMED_CSV`. Position is populated only when the logical record is known;
file-wide encoding/control/size failures and empty input have null positions.
Header mismatch uses record 1; excess records use the first out-of-bound record.
No header text, cell, name, contact, raw reference or catalog content is serialized.

`member_import_fixtures` centralizes the immutable built-in synthetic scenarios;
the existing CLI adds only `synthetic_only: true` to the same summary. Checked
CSV/JSON pairs live in `tests/fixtures/member-import-preview/`. Tests compare
both parser and CLI to these deterministic reports, independently assert counts,
ordering, redaction, fatal errors and conflict positions, forbid database access
on every CLI path (including system checks), and assert zero queries for
same-tenant parsing/projection under PostgreSQL with unchanged identity/access
counts. Unsupported programmatic scenario values fail with a constant message.

This JSON is suitable for **future** React/Flutter preparation, not a registered
public API, transport adapter, client screen, accepted wire contract or upload
permission. No OpenAPI/TypeScript/Dart interface, disclosure, schema, authority or
locked 04C §12/F1–F9/E05 acceptance is changed by this internal contract.

### Local validation evidence — 3 November 2026

Python 3.11.2 / PostgreSQL 16.2: the complete contract-instrumented backend suite
passed 527 tests and checked 310 distinct HTTP route/method/status combinations.
The preview subset includes 27 database-forbidden tests plus the PostgreSQL
zero-query parser/projection regression. Contracts/source inventory, migration
checks, locked 04C bytes, 15 offline tooling tests, Python hash locks, pip consistency
and scoped Ruff checks passed. Web checks also passed: generated TypeScript drift,
design tokens, types, formatting, 202 tests and both builds. No Dart/shared wire
interface changed, so no local Flutter rerun is claimed.

Security limits are unchanged: `npm audit --audit-level=low` exits 1 with the
existing three moderate findings (unchanged package-lock; prior audit evidence
retained). Python advisory review exits 1 because OSV is unreachable (`URLError`),
not a zero-finding result. Neither gate is suppressed or waived; remote CI status
must be checked separately. These results confer no member/import or 04C authority.
