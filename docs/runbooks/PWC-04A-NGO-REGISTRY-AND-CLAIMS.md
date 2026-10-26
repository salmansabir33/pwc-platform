# PWC-04A — NGO registry, provisional drafts and secure claims

Date: 27 October 2026. Baseline: `5c3c6d0294d63e8b5719df865ea40da9e6d8be90` (main including merged owner-policy PR #10). Canonical screens: **ORG-01 / ORG-02**. This assignment authorizes the bounded implementation below, not the real-authority branch of PWC-04B/C/D or any GM command.

## Availability and scope

`PWC_REGISTRY_ENABLED=0` by default. Opt-in requires the existing configured personal-session foundation and direct HTTPS, **development/test only, synthetic data only**. Strict environment parsing rejects activation in staging/production; the adapter independently denies those profiles. No real organization/contact/evidence intake, production deployment or authority is approved. Do not enable synthetic NGO context HTTP or authorization flags for registry use.

This is a claimant-owned application service in **personal context**, not an NGO workspace context. Its only permissions are:

| Capability | Rule |
| --- | --- |
| Search | Current personal session; existing verified-only public four-field projection only |
| Create/list/read/edit draft | Current personal session; `claimant_id` equals locked live user; edit only `draft` |
| Submit/withdraw | Own draft; exact current revision and allowed transition |
| Create/list/read/withdraw claim | Own request; target must already be publicly eligible; never resolves authority |
| History | Own application events, no other claimant identity or private evidence |
| Recovery hold, inactive/revoked/expired/suspended personal session | Deny all registry reads and writes; held-account case access remains a policy dependency |
| Legacy admin, synthetic grant, Board/staff/superuser | No shortcut, no inherited provisional permission |

No access to members, volunteers, private projects, administrator controls, finance, signatories, alliance governance, evidence or rival cases is implemented. No `OrganizationAccess`, `NGOGrant`, `NGOKernelState`, mandate, reviewer or public-verification transition is written.

## Model and migrations

- `Organization` retains its UUID, original names/city/classification/history. New derived `lookup_name` / `lookup_city` text keys support Unicode matching without changing the public serializer. `save()` maintains keys; registry draft edits update both scalar and derived fields. Future writers must use this invariant rather than raw/bulk name updates.
- `OrganizationDraft`: its own UUID, reserved organization UUID and provisional workspace, protected claimant FK, self-declared category, display/legal names, up to five aliases, city/jurisdiction, optional organization contacts, state/revision/timestamps and private dedup key. Contacts/aliases/jurisdiction are **private draft metadata**, not publicly discoverable fields or registration/mandate evidence.
- `OrganizationClaim`: independent UUID, protected applicant and public target FKs, state/revision/timestamps. No free-text allegation, identity document or representative assertion dossier is collected.
- `RegistryReceipt`: owner/key unique, operation, normalized payload digest and result ID. No credentials or raw payload. No invented expiry/purge policy; real retention is gated.
- `RegistryEvent`: protected actor/session/source links, action, source revision and timestamp. One source per event, unique event per source/revision; no contact/name/evidence payload.
- Additive **0003** creates those columns/tables, indexes, valid-state/revision constraints and conditional uniqueness. **0004** backfills only derived keys and installs PostgreSQL UPDATE/DELETE rejection triggers for event/receipt history. It refuses reversal once registry records exist; use a reviewed forward fix. Original migrations are untouched. Historical authentication migration-test teardown now restores *all* leaf migrations, preventing later-app schema regressions.

Fresh database and legacy-upgrade tests preserve stable organization identities and create no grants/publication. Triggers are not protection against a database owner disabling triggers, nor immutable external archival. Production DB privileges/retention/backup handling remain unaccepted.

## State machines

- Draft: `draft --edit--> draft` (revision increments); `draft --submit--> submitted`; `draft|submitted --withdraw--> withdrawn`.
- Claim: creation enters `pending`; `pending|needs_information --withdraw--> withdrawn`.
- `rejected` / `needs_information` claim values are readable schema states for a future approved reviewer contract. **No route produces them.** No approve/reject/needs-information, resubmit, evidence, verification, merge, appointment or grant command exists. Submission is stored pending future review, not a working reviewer queue or a promised SLA.
- Stale revision, duplicate active own application or invalid transition: **409**, no mutation/audit advancement. Separate rival applicants can submit segregated requests; no first-claim ownership or global name reservation.

All mutation work reauthenticates and locks the current user/contact/session/credential inside the same durable transaction as own resource, transition, history and receipt. Same-user creates/claims serialize on User; DB uniqueness is a second guard. Shared persisted IP abuse spend commits before workflow rollback. The existing budget (30 requests / 900 seconds) is reused for the registry route; it is not a production abuse-assurance decision. Locks/statements are bounded to 2s/5s. Authentication is rechecked at completion, including access-token expiry; GET never renews idle time. Audit/receipt failure rolls back the identity, application and state change.

## API — `/api/v1/registry/`

| Suffix | Methods / result |
| --- | --- |
| `search/?q=...&city=...&cursor=...` | GET, minimized public candidate page |
| `drafts/` | GET own page; POST private draft (201) |
| `drafts/{pk}/` | GET own detail; PATCH full replacement of editable fields plus revision |
| `drafts/{pk}/submit/` | POST revision; stores submitted application |
| `drafts/{pk}/withdraw/` | POST revision |
| `drafts/{pk}/history/` | GET own immutable metadata page |
| `claims/` | GET own page; POST public `organization_id` (201) |
| `claims/{pk}/` | GET own minimal detail |
| `claims/{pk}/withdraw/` | POST revision |
| `claims/{pk}/history/` | GET own metadata page |

13 operations / 10 new paths. No existing path changes. UUID path converters; malformed UUID routes get framework 404. JSON only, bounded 8192-byte commands, closed fields and duplicate-JSON-key rejection. PATCH is replacement, **not** JSON Merge Patch: omitted optional fields reset to defaults. Never send state/claimant/role/grant fields. Revision is an integer, not a string/bool.

POST collection operations require a UUID **Idempotency-Key**. Exact normalized retries return the same resource's **current** state with 201, without duplicate history. Changed payload or operation under the same owner/key conflicts; another owner has a separate key namespace. On uncertain response, reload own state; do not blindly replay. Transition commands use current revision rather than an idempotency receipt, so an already-used revision conflicts.

Cookie requests require exact configured direct-HTTPS portal and Origin/CSRF for unsafe methods; native Bearer forbids browser provenance and mixed cookies. Registry responses/errors have no-store/no-referrer and credential Vary. Errors use the existing AuthError envelope with redacted generic messages: 400 validation/transport, 401 invalid session, 403 hold/CSRF, 404 missing-or-not-own/hidden target, 405 method, 409 state conflict, 415 media type, 429 abuse, 503 configuration/dependency. Database details and submitted contacts are never returned in errors.

## Discovery and duplicate policy

NFKC → collapse Unicode whitespace → casefold, deterministic independent of DB locale. Inputs reject control/format characters and excessive lengths. Name substring and optional city matching consider **all eligible public organizations** through a bounded page query, not a first-500 scan. `%`/`_` are literal ORM-escaped text. No total count. UUID-keyset pages return at most 20 records and an opaque signed cursor bound to applicant, purpose and normalized search filters; no snapshot promise. Cursors are not encrypted, not authority, expire after one hour, and contain no hidden-record IDs.

Own open-draft collision key uses normalized name/city/jurisdiction (not contacts, aliases or registration category); same-applicant pending claims are unique by target. A warning establishes only a potential match, never identity, leadership, exclusivity or mandate. Private drafts/claims, hidden organizations, private contacts, aliases and registration/evidence notes are never a matching oracle. Alias storage does not approve alias publication; search cannot yet match another institution's private alias. Exact jurisdiction/registration-number namespace, branch/shared-number rules, fuzzy thresholds and real evidence sufficiency remain E01/E02 gates. No registration-number namespace or automatic merge is invented.

## Contracts and clients

Canonical OpenAPI, checked synthetic examples, source hashes and generated TypeScript include only implemented routes. Existing frozen v1 operations/schemas/security stay byte-fingerprint compatible. Flutter generation adds typed registry DTOs and a **separate non-callable registry manifest**; `PersonalApi`/`NativeApi` allowlists are unchanged. New API examples are validated by the contract runner and mobile tests.

- React NGO route `/registry`, linked from foundation overview: ORG-01/02 search/create/claim/status/edit/submit/withdraw/history presentation, conflict/loading/unavailable states, bounded pages, private optional metadata and English/Urdu direction-aware labels. No operations-portal registry route. The mounted application supplies **no gateway**: controls stay disabled, no fetch or browser auth is activated. Contract-component tests inject a synthetic gateway only. Scope/locale/unmount invalidates local data and late responses.
- Flutter `/registry`, linked from personal profile: corresponding claimant presentation with typed DTOs, guarded asynchronous results and a test-only gateway port. Default mounted route has **no registry transport**. Native personal authentication is unchanged; this is not live mobile registry integration or production native acceptance. Real intake/transport needs an explicitly accepted environment and security/hold/privacy contract, not a build-time bypass.
- Neither UI fabricates verification success, administrators or private lists. Localization is a foundation, not a completed Urdu translation/manual accessibility acceptance.

## Validation and operations

See [integration review](../reviews/PWC-04A-NGO-REGISTRY-INTEGRATION-REVIEW.md) for exact results, corrected findings and final-head CI evidence. Reproduce against disposable PostgreSQL 16 with existing hash-locked requirements:

```sh
cd apps/backend
python -m contracts.check --check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --testrunner contracts.testing.ContractRunner --verbosity 2
# root: npm run check; npm run contracts:types:check; npm run test:browser
# pinned Flutter/Dart: python3 scripts/mobile_contracts.py --check
# apps/mobile: flutter analyze; flutter test; existing CI Android build gates
```

Do not use real NGO/person data or run destructive rollback against used records. No extra runtime dependencies, data seeding, production flags, grants or deployment changes accompany this slice.

## Later gates — stop after 04A

- **04B:** E01–E04 eligibility/namespace/evidence/reviewer IAM, E06/07 storage/retention, E10 assurance, E12/13 dispute/safety, E14/17 wire/notice/abuse contracts. No files, reviewer appointment or adjudication exists here.
- **04C:** E03/05/09/10/11/18 and **all GM01–GM12** exact command, source, recipient, assurance, conflict/quorum, locks/writer/schema and failure contracts. No admin/grant activation or synthetic promotion.
- **04D:** E08 public consent/allowlist/badges/withdrawal. Existing public projection is preserved, not newly certified for production. Private draft fields are never auto-published.
- **REAL01–04:** independent NGO-governance/security/legal/privacy/operations approvals, real intake, regrant/cutover, least-privilege deployment/HTTPS, storage/retention, monitoring/restore/load and actual device/browser acceptance. E15 delegation, E16 finance/signatory/alliance/support and operational merges remain excluded.

The consolidated owner-disposition register remains authoritative; this task neither reclassifies its P/C decisions nor closes mixed-owner gates. Foundation merge-readiness is distinct from real onboarding/release readiness.
