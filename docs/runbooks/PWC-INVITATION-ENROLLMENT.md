# Invitation-to-personal-account and MFA — PR46

## Implementation and live boundary

The existing PR46 slice is extended, not replaced. Product decisions and scoped
permission remain in [the decision record](../decisions/PWC-PERSONAL-INVITATION-BOUNDED-DEVELOPMENT.md).
Founder and AbuBakr are intended initial recipients; no real recipient address or
authenticated officer/source was supplied. No identity, signature or independent
review is inferred from this implementation or repository ownership.

**Complete bounded implementation, not live activation:** recipient email proof,
Django password validation/hash, authenticator provisioning and existing MFA
activation/recovery codes, transactional account creation/consumption, encrypted
outbox worker and accessible EN/UR React. Every service/view/worker rejects every
non-test profile. The real issuer resolver always denies. Neither portal injects
a credentialed invitation transport. No SMTP mode/approval boolean or institutional
grant is installed. Flutter's existing 22-operation personal allowlist is unchanged;
new browser-only routes are excluded from it. Staging still rejects auth flags.

## State, deadline and abandoned enrollment

1. Explicitly authorized issuance binds the canonical recipient and opaque source
   digest. A 256-bit invitation token is queued encrypted; only its purpose/UUID-
   separated HMAC digest is stored for verification. API/service issuance returns
   no raw token. No public issuer route exists.
2. Opening `/account/invite#invitation_id=…&token=…` scrubs the fragment immediately
   and performs no acceptance. Query, duplicate and extra link fields are rejected.
3. Recipient explicitly requests a separate mailbox proof. The worker sends only
   to the stored canonical address. Shared IP/target/global budgets are reused;
   initial invitation and proof delivery share the existing email cooldown.
4. Proof confirmation is explicit, recipient-bound, purpose-separated and
   single-use (at most 30 minutes, capped by the original invitation deadline).
   Only its submitter receives a fresh memory-only enrollment continuation
   capability. The invitation token alone cannot choose credentials after someone
   else confirms email. Fresh mailbox proof rotates that capability.
5. Password validation uses Django's existing minimum-length/common-password/
   similarity rules and hashers. Only an encrypted hash and a random authenticator
   secret/ephemeral UUIDs are staged, for at most five minutes and never beyond
   the invitation deadline. **No User, contact, session, factor or recovery code
   exists yet.** Password plaintext is never persisted.
6. TOTP confirmation creates User/contact and uses existing `mfa.enrollment_confirm`
   to verify/replay-fence the code, activate the encrypted factor and hash recovery
   codes. An internal enrollment-session record supports the existing factor
   ownership invariant; no cookie/bearer is issued, and that record is revoked
   before commit. It is not a logged-in recipient session.
7. Account, verified contact, factor, recovery codes, audit and invitation
   consumption share one transaction/savepoint. Expiry/source are rechecked after
   expensive work and at the final audit fence. Failure rolls everything back;
   denial counters commit separately. A canonical contact unique constraint
   rejects a racing duplicate rather than linking an existing account.
8. **All steps, including MFA activation/consumption, must succeed strictly before
   `created_at + 24 hours`.** Password or email success does not extend it.
   Successful completion returns recovery codes once and clears staged secrets.
   No auto-login or Founder/verifier/NGO/finance power follows. The recipient must
   explicitly sign in using the existing password + MFA ceremony.

Cancellation erases pending secrets and blocks all further steps; it cannot
cancel a consumed invitation or disable the resulting personal account. Five bad
proof/continuation/OTP attempts close an invitation without locking a real user.
Expired setup can be re-staged while the original invitation remains valid.
Worker expiry erases expired setup/proof and closes expired invitations. No real
account deletion or ambiguous partial-account recovery is needed. Metadata is
not automatically deleted: O4 retention/hold/erasure remains unaccepted.

Browser hiding, leaving, locale switch, invalidation and setup/recovery display
timeouts erase client material. Reopen one's original invitation, re-prove the
inbox and re-enter the same password to resume a still-valid five-minute setup;
this retains the authenticator key without extending its deadline. A different
password or expired setup replaces it. Never fetch real proofs from the database,
logs or an operator as an enrollment workaround.

## HTTP, locking, audit and delivery contract (implemented development scope)

Four POST-only `/api/v1/auth/web/invitations/` operations: `request-proof/`,
`confirm-email/`, `password/`, `activate/`. Exact request/response/error schemas
are in OpenAPI/generated TypeScript and checked structural examples. Direct TLS,
exact accepted browser portal/Origin and explicit anonymous CSRF are mandatory;
bearer credentials/native transport are rejected. Responses are no-store and
no-referrer. There is no invitation list/status/issuer endpoint disclosing people.
New operations are additive; frozen v1 operations/security are not weakened.

Every mutator locks issuer User, then invitation. Completion creates a *new*
User and its factor/session records inside the held transaction; no existing
recipient row is adopted. The partial unique pending-recipient constraint and
unique verified-contact key arbitrate races. The eventual trusted-source adapter
must acquire and hold authoritative source/revocation locks consistently with
this order through commit; the deliberately denying seam is not evidence of
accepted live revocation semantics. Tests patch it only in nonshipped fixtures.
Minimal typed SecurityEvents use invitation UUID correlation, not raw recipients,
proofs, passwords, seeds or provider errors. Audit failures roll back writes.

`dispatch_personal_invitations --limit 20` processes bounded expiry and mail work
in test profile only. Encrypted generations, 60-second leases, five attempts,
1/2/4/8-minute retry delays, expiry checks and terminal erasure are implemented.
No locks span I/O. Stale generation/attempt acknowledgements cannot erase newer
mail. Delivery is at-least-once: uncertain SMTP acceptance may duplicate a message,
never account creation. Already in-flight mail cannot be retracted on cancellation;
server-side cancellation/expiry/replay checks remain authoritative.

The worker accepts the existing `PreparedSmtpAdapter.send(..., expires_at=...)`
interface; disposable certificate-verified TLS and STARTTLS integration tests run
through it. The command/default composition still uses locmem. SMTP environment
values alone cannot activate a live worker; O1/O2/O4 and a reviewed non-test
composition/guard change are required first. Redacted failures contain no provider
exception text. No real provider deliverability claim follows from local TLS.

## Verification and activation checklist

Use actual PostgreSQL, never SQLite. Full backend runs from `apps/backend`:
`python manage.py test --testrunner contracts.testing.ContractRunner`.
Focused suites: `accounts.test_personal_invitations`,
`accounts.test_invitation_completion`, `accounts.test_invitation_delivery`.
Run migration drift/check, `python -m contracts.check --check`, generated browser
and mobile contract checks, Ruff, lock/security/advisory gates, `npm run check`,
and browser CI. Existing nonshipped direct-TLS auth harness now runs the actual
EN/UR invitation UI against Django/PostgreSQL in addition to session regressions.
Its mocked source, temporary mailbox IPC and synthetic accounts are tests only;
none is imported into either shipped portal or an actual issuer adapter.

Exact outstanding live dispositions, not a request to reopen product decisions:

- **PE-ISSUER:** actual officer person/account binding and accountable charter;
  authenticated versioned trusted source; initial recipient bounds; revocation,
  expiry and conflict rules; transaction-held source locks. Issue42 institutional
  grants and distinct-human independent verification remain separate.
- **PE-CONTRACT live review:** accepted writer/source lock order and clock/failure/
  revocation semantics, minimal DB/runtime principals, audit/read audiences and
  browser security review. This document records implementation, not self-signoff.
- **O4:** recipient eligibility/age, lawful pre-acceptance address processing,
  notice/version/acknowledgement; invite/contact/session/audit/backups audiences;
  exact retention start/hold/erasure, including encrypted pending material.
- **O1/O2:** provider/region/terms, verified sender/domain, delivery trial and budget,
  worker owner/schedule/alerts/egress, retry and shared-NAT abuse acceptance.
- **O3/W2:** exact HTTPS portal/link hosts, actual ingress/source-IP/cookie/CSRF/CSP
  acceptance and reviewed credentialed browser composition. Native networking
  permissions are not expanded by a browser feature.
- **Deployment:** explicit separate Contabo authorization, secure configuration and
  independent actual-host acceptance. Do not provide secrets in repository/chat.

For a separate staging decision, use existing `infra/staging/README.md` and
controlled-enrollment coexistence/preflight checklists; do not replace another
project's proxy/listener. Supply approved host/origin inventory, scoped issuer
and recipients through secure channels, approved notices/retention/provider/worker
parameters, and secret references—not credential values in chat. CI Compose/TLS/
restore is disposable infrastructure evidence, not Contabo access or acceptance.
Do not deploy, send invitations or create real accounts from this runbook.

## Initial operating disposition — after merged PR46

No new product acceptance is inferred by the operational-preparation task.
Invitation-only, the intended Founder/AbuBakr recipients, ordinary permissions,
personal email/password/TOTP, single use, and the **entire 24-hour ceremony** are
accepted. Initial issuance is reserved to an explicitly authorized PWC officer;
that rule does not identify or authenticate an actual officer. PR46/CI/merge are
not officer appointment, legal/privacy approval or independent verification.

**Exact issuer today: none executable.** `authorize_source` always denies. The
staging `pwc_app` DB role has no invitation/account writer rights. Neither an
operator, Founder title, repository owner nor staff/superuser can fill this gap.
No new bootstrap credential, root installation command or privileged endpoint is
proposed here. There is no honest deployment-only switch that enables enrollment.

The first real issuance must follow this existing trust procedure, not a new
identity system:

1. The accountable PWC appointing/source owner supplies the *actual* officer's
   person/account binding, charter, source/version and authenticated evidence via
   the approved evidence channel. If no accepted source/credential ceremony yet
   exists for that officer, the issuer dependency remains blocked; do not create
   an officer account or grant as a circular enrollment workaround.
2. The existing trusted-source/IAM owner independently validates that source and
   its narrow personal-invitation action, exact canonical recipient bounds,
   assurance, expiry and revocation. Issue42 remains the routing point for its
   institutional source dependencies; no wholesale governance re-review is needed.
3. The separately accepted source adapter authenticates the issuer using existing
   live session/MFA primitives and transaction-held source/revocation checks.
   Recipient UUIDs/names/GitHub accounts are not authority. The initial recipient
   addresses are supplied securely and are not invented or committed here.
4. Recipient email possession, password and TOTP complete only ordinary personal
   enrollment. Independently confirm actual distinct-human bindings and conflicts
   before Founder/verifier appointments; the Founder cannot independently verify
   himself. Separate logins alone do not establish independence.
5. Record the actual confirmer/charter, source/version, decision and evidence
   reference. An agent cannot supply a signature or substitute a fixture for it.

The indispensable external confirmation is therefore the actual scoped issuer
appointment/source and its independent validation, not another vote on the
already accepted invitation policy. Live source/DB/transport composition still
requires reviewed implementation after that disposition, even if the VPS is ready.

### Enrollment privacy/security worksheet (reuse ADR-0001 O1–O4)

| Item | Existing minimum / technical boundary | Exact unresolved disposition before real data |
| --- | --- | --- |
| Personal data | Canonical email; password hash only; encrypted TOTP seed; hashed recovery codes; opaque invitation/source/user IDs, lifecycle times, keyed abuse counters and minimal typed security events. No ID scan, phone, NGO roster or legal-identity proof added to personal enrollment. | Actual age/eligibility rule and any guardian requirements; whether further fields are justified. Do not infer an adult-only rule. |
| Notice and basis | Invitations hold an address *before* the person accepts; enrollment never opts a person into membership, marketing or disclosure. | Accountable privacy owner identifies appropriate processing basis for pre-invitation and account/security processing, notice text/version and acknowledgement/withdrawal effects. Product permission is not consent or a legal finding. |
| Retention/deletion | Setup maximum five minutes; email proof maximum thirty minutes; invitation maximum twenty-four hours; expired/terminal encrypted material erased by the worker. No abandoned User exists. Typed audit is append-only. | Exact metadata/contact/IP/security/audit retention periods **and start events**, holds, access, deletion process and backup expiry. No statutory period or indefinite real-user retention is approved by the current implementation. |
| Delivery | Separate recipient-bound proof; mandatory verified TLS/STARTTLS adapter, bounded retries/leases, no raw provider-error logging, no live SMTP composition. | Provider/region/terms, authenticated sender/domain, deliverability, budget, shared-NAT limits and worker/alert owner. |
| Audit protection | No raw password/proof/seed/provider payload; opaque correlation; no public invitation list or audit reader; restricted staging DB principal; encrypted backup required. | Named audit readers, lawful purpose, retention/hold/erasure and privacy-safe incident access. |
| MFA/recovery | Personally held authenticator, one-time recovery codes, explicit login after completion; recovery never grants institutional authority or clears holds by nomination. No shared seeds/passwords or operator proof retrieval. | Secure recovery-code custody guidance and actual support/incident owner; no alternate lost-contact/factor recovery channel is authorized. |

Until these enumerated dispositions exist, use disposable non-personal fixtures
only. Do not gather real addresses/evidence/credentials in chat or the repository.
