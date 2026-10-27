# PWC-04B — NGO verification preparation and evidence boundary

## Scope and operation

This is an additive **synthetic personal preparation foundation**, based on merged
04A (`c8a1637`). It is not document intake, an evidence rubric, reviewer IAM,
adjudication, NGO verification, an administrator grant, or production acceptance.
The authoritative roadmap, ADR-0001–0004 and scoped E01–E18 / GM01–GM12
register dispositions continue to apply. Implementation does not close their
independent legal/privacy/security/IAM/operations gates.

`PWC_VERIFICATION_ENABLED` defaults false, additionally requiring the existing
registry and personal-session gates and development/test environment. No flag
activates file acceptance or reviewer entitlement. Mounted web/native clients
remain disconnected. Never enable against real documents or real applicants.

## Data and state contracts

- `VerificationCase`: personal claimant, organization, exactly one own 04A
  draft/claim, source revision, eligibility **or** representative-mandate purpose,
  registered/unregistered track snapshot, revision and timestamps. One active
  case per source/purpose; separate cases do not satisfy one another.
- States: `draft -> submitted -> withdrawn`, or `draft -> withdrawn`.
  Submission means **preparation_record_only**, not accepted evidence or review.
  Source must remain live/current to mutate; withdrawal remains possible after
  source withdrawal. Historical own reads remain available.
- `EvidencePreparation`: not evidence or file metadata. One active marker/case,
  a strict boolean `prepared_offline`, planned/withdrawn state and revision.
  Replace/withdraw uses both case and marker revision; changes advance parent.
  The boolean is self-declared synthetic preparation, not authenticity assurance.
- `VerificationEvent`: immutable actor/session provenance, reason code, case
  revision and bounded marker snapshot. `VerificationReceipt`: immutable
  claimant-scoped UUID retry key, operation/input digest and object references.
  Exact retries return current state, never resurrect withdrawn records.
- Additive migrations 0005/0006 provide constraints and PostgreSQL immutable
  triggers. Reversing used data is refused; use a reviewed forward correction.
  These are application/history guards, not protection against database owners.

No contact, organization/public state, access or grant writer is added.

## API and client contracts

15 actual operations under `/api/v1/verification/`, in canonical OpenAPI v1,
checked synthetic examples, generated TypeScript and separate Dart verification
manifest. Existing frozen 03C/04A operations and native personal allowlist remain
unchanged. Case list/create/detail/requirements/history/submit/withdraw;
preparation list/create/detail/replace/withdraw; disabled upload/download/queue.
Requirements return empty accepted classes, unapproved rubric, false file/review
availability. No proposed reviewer mutation or approval API is advertised.

Personal sessions, current holds/revocation, cookie CSRF/origin/transport rules,
owner-before-object lookup, bounded signed pagination (20), strict closed inputs,
8 KiB JSON body bound for preparation, quotas and PostgreSQL lock/statement
limits apply. Errors omit request data and database details; responses no-store.
Mutations/audits/receipts commit atomically, with authentication rechecked before
completion. User-first locking serializes same-user source/case/hold mutations.

Upload/download always return 503 **after authentication and ownership**;
foreign/missing case or marker returns 404. Upload bytes are not parsed or stored.
No media model, public URL, filename, content hash, quarantine storage, scanner,
encryption key or retention job exists. A download adapter's item identifier is
only an existing preparation marker; no real evidence identifier exists.

ORG-03 React provides typed synthetic DI initiation from an existing source,
own cases, requirements/history, marker changes and preparation submission/
withdrawal. PWC-01 review is explicitly unavailable, with no private queue.
Flutter provides separate typed DTOs/manifest, own-status/submission/withdrawal
components and unavailable file/review states; no live gateway is wired.
Flutter initiation/marker editing/history interaction is **not implemented**;
those approved-preparation UI extensions remain follow-up work, not live parity.
Private component state is invalidated on scope/gateway/language changes and
late responses discarded. W1 network blockade and native-backed credential
handling are unchanged. Components do not authorize backend operations.

## Unimplemented policy-dependent workflows

No case needs-information/reopening, actual evidence replacement, assignment,
assessment, recommendation, decision, appeal/dispute, re-verification,
suspension/revocation or reviewer provisioning exists. These require approved
rubric/state/IAM/assurance/notice/retention contracts, not just flipping a flag.
No automated test can establish real-document authenticity.

E01–E03 track direction does not approve document sufficiency. E04 reviewer
issuer/root and conflicts remain prerequisites. E06/E07/E10/E12/E13/E14/E17
privacy, storage, scanning, encryption, retention, assurance, disputes and
technical notice/reader contracts remain blocking for their affected commands.
E05/E09/E11/E18 and **all GM01–GM12 command implementation gates** remain for
mandate/authority/activation. E08/E15/E16 public consent, delegation,
finance/alliance/support remain outside this slice. No mixed-owner decision is
closed wholesale. No new decision is self-approved in OPEN-DECISIONS.

## Validation and incident handling

See the integration review for executed evidence and limitations. Use only
synthetic fixtures and actual PostgreSQL. Full runner:

```sh
cd apps/backend
python -m contracts.check --check
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --testrunner contracts.testing.ContractRunner
```

Do not run concurrent suites against the same test database. On unexpected
sensitive intake, stop the affected flow and escalate to privacy/security owners;
do not log documents, infer a retention period or turn on an uploader. Flags off
are not a substitute for incident response or approved cleanup procedures.

## Next-phase gates

04C/04D, privileged grant management, finance and deployment are not started.
Human review of this safe slice cannot authorize those phases. Real intake needs
independent privacy/legal/security/storage/operations approval, scoped reviewer
IAM, evidence and state rubrics, and approved retention/notice contracts, followed
by implementation and adversarial tests of those actual paths. No production
readiness or real-organization/device acceptance is asserted here.
