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
