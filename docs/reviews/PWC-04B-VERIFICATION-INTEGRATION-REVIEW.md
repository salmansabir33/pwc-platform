# PWC-04B verification integration review

Status: engineering validation in progress; no independent approval, production
activation or complete 04B roadmap sign-off. Baseline main c8a1637 (merged PR11).
Assigned branch: arena/1778b1f4-pwc-platform; consolidated PR #12, no auto-merge.

## Delivered safe slice

Four additive models: revision-bound personal VerificationCase with mutually
exclusive 04A draft/claim source; EvidencePreparation non-file boolean marker;
immutable VerificationEvent and VerificationReceipt. Separate eligibility and
representative-mandate purposes and registered/unregistered category snapshots.
Draft/submitted/withdrawn only. No accepted document metadata, reviewer IAM,
review decision, government attestation, public-state or grant writer. See the
[runbook](../runbooks/PWC-04B-NGO-VERIFICATION-AND-EVIDENCE.md) for exact states,
API, minimization and migration/incident boundaries.

## Authority, privacy and dependency review

Case ownership is personal, not NGO membership/administration. Authentication,
current account/session/hold checks, source ownership and revision checks occur
inside the durable transaction with the existing User-first prefix. Atomic
history/receipts have PostgreSQL update/delete guards. Source withdrawal blocks
submission/marker mutations, not applicant withdrawal. Same-key replay returns
current state; no resurrection. One active case per own source/purpose and one
active marker/case are database constrained. Application validation establishes
source/claimant/organization consistency; this is not a restricted DB-writer
architecture or defense against DB owners.

Staff/superuser/legacy NGO admin/Board confer no case-review entitlement. No
reviewer model, provisioning flag, assignment, assessment or approval exists.
Queue adapter always 503 without enumeration. Self/conflict/independence and
reviewer-revocation races cannot be claimed tested for a nonexistent decision
writer; forbidden routes/unavailable adapters are tested instead.

No file bytes are parsed or stored. Filename, URL, hash, notes, reviewer and
asserted approval inputs are rejected. Disabled own upload/download adapters
have no success response, and foreign/missing case/marker stays 404. No media,
public URL, scanner, retention schedule or authenticity automation is supplied.
Synthetic boolean preparation has no evidentiary weight.

All thirty E/GM dispositions remain scoped. E01–E04 rubric/namespace/governance/
reviewer IAM; E06/E07 privacy/storage/retention/scanning; E10 assurance;
E12–E14 disputes/exception/command protocols and E17/E18 reader/activation
contracts still gate their affected implementations. E05 bounds are not new
settings. E08 public consent remains separate. E09/E11 and GM01–GM12 do not
permit grant commands or synthetic-to-real migration. E15/E16 delegation,
finance/alliance and support remain excluded. OPEN-DECISIONS is unchanged: no
new product choice or independent sign-off is fabricated.

## API and clients

15 implemented operations, 12 success contracts plus permanently unavailable
file/reviewer adapters. Frozen 03C/04A contracts unchanged; source hashes, checked
synthetic examples, TS types and Dart DTOs/verification-only manifest refreshed.
Personal native 22-operation allowlist unchanged. No endpoint proposal for
approval is advertised.

React ORG-03 source-bound initiation, own list/status, requirements/history,
preparation add/replace/withdraw, revision-bound submit/withdraw and safe errors;
PWC-01 unavailable view. Flutter parallel preparation/status components and
unavailable review. Both are synthetic-DI tests, not client/server integration.
Mounted W1 networking remains blocked; native credential transport/storage is
unchanged. Private state clears on context/gateway/language changes and ignores
late responses. History/marker views are bounded first pages, not complete
exports; web additionally continues case lists. Unavailable future
needs-information/appeal/decision workflows are explicit rather than mocked
verified success.

## Findings and limits

- Native DTO validation initially did not enforce JSON Schema const/maxItems/
  maximum: corrected with closed unavailable-requirements regression tests.
- Old web route tests expected /verification to be absent: updated only that
  expectation now an explicit unavailable canonical view is mounted; other
  unfinished routes remain absent.
- Pinned Flutter formatting must be verified by CI; local WASM dart_style
  formatting matches existing pinned-formatted source but is not Flutter SDK
  execution.
- No known unresolved Critical/High finding in this bounded slice from the
  agent's review; independent security/privacy/database review is outstanding.
- No physical device/emulator test, real document/NGO authenticity check,
  production load/restore/retention/operational acceptance or external audit is
  implied by synthetic tests or Android compile jobs.

## Executed validation

Pending final exact-head evidence. Initial focused PostgreSQL run: 30 tests
passed on PostgreSQL 16.2. Local web check (typecheck, Prettier, Vitest, two
production bundles) passed after route expectation correction. Full
contract-instrumented PostgreSQL suite and CI are still running. No final green
claim is made at this checkpoint.

## Readiness and human handoff

Reviewable only as the bounded preparation foundation after exact-head gates
pass. Not complete policy-dependent verification or production readiness.
Independent policy/IAM/privacy/legal/security/operations gates and REAL01–04
remain. Stop before 04C/04D, privileged grants, finance or deployment. Human PR
review and explicit merge decision required; do not auto-merge.
