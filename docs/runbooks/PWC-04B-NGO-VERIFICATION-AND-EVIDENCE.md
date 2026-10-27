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
components, source-bound initiation, requirements/history and non-file marker
changes, with unavailable file/review states; no live gateway is wired.
History/preparation displays are bounded first pages in both clients, not full
audit exports; web case lists additionally support cursor continuation.
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

## Revised offline controlled onboarding — superseding initial rollout

**27 October 2026, later product-owner instruction; ADR-0004 §7 / PWC-02E §9.**
Earlier sections describe the merged PR12 preparation checkpoint, not the new
rollout policy. For initial rollout there is **no public NGO self-registration,
existing-NGO claim or applicant-driven evidence submission**. Personal identity
registration/recovery is a different domain and supplies no operator powers.

### Executable boundary

- Old URLs/schemas/data/migrations are preserved. New draft/claim/case creation,
  editing, preparation addition/replacement and submission return 503
  `SELF_SERVICE_UNAVAILABLE` after current personal authentication/hold checks,
  before parsing request data. Existing own reads/history and withdrawal remain
  scoped. Raw evidence adapters stay unavailable. A withdrawn record never
  grants NGO access.
- A non-environment-configurable `PWC_LEGACY_ONBOARDING_TEST_EXERCISE` defaults
  false. It is consulted **only when environment is exactly test** to exercise
  frozen historical success contracts in isolated regression fixtures. It cannot
  enable rollout in development/staging/production, never affects controlled
  commands, and has no HTTP/header/token bypass. Do not enable in deployed code.
- New `/api/v1/controlled-onboarding/requirements/` returns generic policy after
  personal-session checks in the existing default-off dev/test API boundary.
  It is **not a capabilities response**. Twelve implemented operations total,
  ten paths: requirements plus unavailable list/create/read/edit, submit,
  approve/reject/return/withdraw, invitation creation and recipient acceptance.
- All controlled private readers/commands return 503
  `CONTROLLED_ONBOARDING_UNAVAILABLE` for every actor, including Django
  superuser/staff, Board, legacy NGO admin and synthetic grant holders. No
  object lookup/body parse/contact/evidence persistence or enumeration occurs.
  No setting activates them. Cookie CSRF/origin, native transport separation,
  current auth/holds, quotas and lock/statement bounds remain enforced.

### Domain preparation, not a live privileged writer

Additive migrations 0007/0008 introduce ControlledOnboardingRecord (initiator,
reviewer, state/revision, optional existing organization), immutable
ControlledOnboardingRevision (minimized identity/nomination snapshot), separate
OfflineVerificationAttestation eligibility/mandate lanes, and immutable
ControlledOnboardingEvent (actor/session/revision provenance). All references
are protected from cascade deletion. Snapshot revisions are unique; review
states require a different reviewer account and provenance; the initiator
cannot be replaced to bypass independence. History updates/deletes are blocked
by PostgreSQL triggers; reversing used records is refused. DB-owner power is
not treated as domain authority.

Snapshots contain NGO display name/city/classification, optional existing
nominee User and opaque nominee/official-nomination custody handles. Attestations
contain a separate purpose, opaque external evidence/method handles, examination
date and attestor. No document number, raw scan, URL, free narrative, case
contents, evidence sufficiency or PWC-alliance requirement is added. Handle
syntax is a technical bound, **not an approved privacy/retention/reference
classification or a guarantee that arbitrary identifiers are harmless**. No
real data may be entered until those contracts are accepted.

Non-writing `preflight` validates the proposed draft/returned → submitted →
approved/rejected/returned graph, withdrawal, expected revision, different
reviewer account and presence of both attestation lanes. It performs no queries,
permission checks or persistence. A returned correction requires a new immutable
snapshot/revision; approval of an old revision cannot be carried forward.
A successful preflight **never authorizes** a command or asserts distinct-human
verification, documentary authenticity or NGO authority. Approved/rejected are
preparation schema states only; no live transition writer is implemented.

### Operator/reviewer and invitation integration contract

Required capabilities are separate appointment-backed, operation-specific
platform permissions: record/edit/submit by the nominated initiating operator;
read/review/approve/reject/return by an independently appointed officer. These
are architecture requirements, **not approved permission atoms or an issuer
matrix**. Before implementing a writer, independently accept:

1. Legitimate initial appointing authority; narrow provisioning writer,
   appointment scope/expiry/revocation/recovery and distinct-human provenance.
2. Exact issuer/command/target and conflict matrix, current-session operation-bound
   assurance/intent, hold/factor/recovery behavior, locks/revision/idempotency and
   restricted-role database writer/API/private-reader/notice contracts.
3. External evidence custody/legal basis and minimized reference/privacy/retention
   classification. No arbitrary document sufficiency or duration is invented.
4. Exact recipient binding, identity activation, invitation token lifecycle,
   delivery/expiry/replay/revocation and version-specific nonfinance acceptance.
5. Separate 04C/03B.3 grant activation. No invitation, accepted record or reviewer
   status automatically becomes an NGO grant; finance/signatory/governance,
   collaboration and private support stay separately gated.

No email/token delivery, assurance-proof reuse, grant mapping or live operator
appointment exists. Model-level different-account checks are not proof of two
independently vetted human individuals. Denied/unavailable commands have no
approval audit success, invite token or synthetic-to-real provenance path.

### Operations UI

PWC-01 `/controlled-onboarding` presents the external-examination → operator
record → independent approval → nominee invitation/acceptance → separate grant
stages and exact unavailable boundaries. The form is disabled when mounted;
synthetic component tests can preview at most 20 local immutable revisions.
Nothing is sent, persisted in browser storage, approved or invited. State clears
on scope/mode/locale change. References are bounded opaque handles, not uploads.
Review/return/reject/invite/accept/activate controls always stay disabled.
Legacy ORG screens explain the revised policy while preserving historical
components; mounted browser/native gateways remain disconnected.
