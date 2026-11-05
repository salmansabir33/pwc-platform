# Controlled personal enrollment and Contabo staging preparation

## Current boundary — 5 November 2026

The owner's current initial policy is **invitation-only**. This is product
scope, not authentication of an issuer or approval of a privacy/issuer contract.
Existing email/password/CSRF/session/MFA/recovery/audit and EN/UR React/Flutter
journeys are reused. No new invitation issuer, endpoint, token table, account,
grant, native networking permission or activation setting is introduced.

Public registration request/resend/confirmation now reject every non-`test`
profile before database or delivery I/O, even if flow flags are accidentally
set. Existing synthetic registration/expiry/replay/two-account tests continue in
explicit `test` profile. Reset remains the existing purpose-separated flow;
reset never removes MFA, clears a recovery hold or grants authority. The shipped
browser remains network-disabled. Staging still rejects every auth-enable flag.

**Invitation issuance/acceptance is not executable.** Exact personal-invitation
issuer and recipient/state/privacy contracts are not accepted in this baseline.
Reusing public registration as an invitation or a manually delivered database
proof would be a bootstrap shortcut, not completion. The read-only preflight:

```sh
cd apps/backend
python manage.py check_personal_enrollment_readiness
```

prints bounded JSON and exits nonzero. There is no `--approve`, issuer boolean,
email/name/GitHub ownership shortcut or staff/superuser bypass. It does not probe
a provider, inspect secrets, create accounts, send mail or query private data.

## Exact contract disposition needed before invitation implementation

| Gate        | Required bounded acceptance                                                                                                                                                                                                                                                                                                                | Current status                                                    |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------- |
| PE-ISSUER   | Actual accountable personal-enrollment issuer, authenticated person/account binding, charter/source/version, narrowly scoped invitation power and recipient bounds, expiry/revocation and review/conflict rules. No NGO/Founder/verifier privilege.                                                                                        | Unaccepted; no issuer installed                                   |
| PE-CONTRACT | Canonical recipient binding; single-use invitation digest and purpose separation; exact lifetime/reissue/revoke semantics; verified-email proof binding; transactional lock/consume/replay/rate-limit/audit/storage/API contract; duplicate-account behavior; account-creation versus MFA completion checkpoint and allowed pending state. | Unaccepted; no speculative table/writer/route                     |
| O1/O2       | Provider, region/terms, sender/domain authentication, deliverability trial, budgets/global spend cap, scheduling/alerts, queue ownership, abuse/shared-NAT limits and approved worker egress.                                                                                                                                              | Unaccepted; no real mail                                          |
| O4          | Eligibility and age rules; lawful basis including holding an invitee's address before acceptance; notice text/version and acknowledgement rule; enumerated fields/audiences; exact retention/start/hold/erasure for invites, contacts, security/IP/session/audit and backups.                                                              | Unaccepted; no invented legal conclusion or production TTL        |
| O3/W2       | Exact portal/link origins, independently checked actual-host HTTPS/cookie/CSRF/CSP/ingress; aggregate-proxy rate behavior/edge controls; reviewed browser/native composition and minimal authentication DB writer privileges.                                                                                                              | Disabled-service infrastructure only; live transport not accepted |
| IDENTITY    | Separate account/person bindings for Founder and AbuBakr, distinct natural persons and non-conflicted independent verification; authenticated responsibility/founding-source evidence.                                                                                                                                                     | Not established by accounts, nomination or GitHub access          |

Record exact accept/amend/reject dispositions against versioned text and actual
accountable charters/evidence; do not fabricate reviewers, signatures or dates.
Use existing Issue #42 for its exact institutional trust dependencies. Do not
reopen accepted C1 R01–R08 or conflate personal invitation permission with NGO
issuer/GM/04C authority. No identity evidence upload is added.

The future implementation must reuse PostgreSQL constraints/transactions,
existing canonical email/proof hashing/encrypted outbox, server-side ownership,
CSRF, TOTP, recovery restrictions and generation invalidation. Reuse does not
settle the currently missing invitation lifetime, consume checkpoint or issuer
source. Invitation expiry/replay tests cannot truthfully be reported as passed
until this contract is accepted and an actual invitation service exists. Existing
registration proof expiry/replay tests are not invitation acceptance evidence.

## Prepared SMTP adapter — intentionally unwired

`accounts.prepared_mail` supplies a replaceable, one-attempt SMTP adapter using
Django's existing SMTP backend. It supports verified implicit TLS or mandatory
STARTTLS, authenticates after TLS, uses a 20-second socket timeout, rejects expired
or malformed messages/header injection, and returns only bounded failures.
Provider exception text, addresses, message content and credentials are not
logged. There is no plaintext/certificate-verification fallback or automatic
adapter retry. Tests use a disposable local TLS SMTP server and ephemeral PKI,
not a provider or actual recipient.

Operator-only environment inventory (no values in chat/Git):

| Variable            | Handling                                                                           |
| ------------------- | ---------------------------------------------------------------------------------- |
| `PWC_MAIL_HOST`     | Exact approved provider DNS host; no URL or credentials                            |
| `PWC_MAIL_PORT`     | Approved SMTP port; integer 1–65535                                                |
| `PWC_MAIL_TLS_MODE` | Exactly `starttls` or `tls`; certificate/hostname validation mandatory             |
| `PWC_MAIL_USERNAME` | Deployment secret store; never diagnostics                                         |
| `PWC_MAIL_PASSWORD` | Deployment secret store, narrowly scoped credential and rotation owner             |
| `PWC_MAIL_FROM`     | Approved sender mailbox with verified domain/SPF/DKIM/DMARC and ownership evidence |

These variables do **not** activate delivery. They are not forwarded into staging
Compose or read by `dispatch_auth_mail`. `delivery.deliver_message` remains
hardcoded locmem; `flow_security.configured()` and the strict environment parser
still reject non-synthetic delivery. `EMAIL_BACKEND` cannot turn on real mail.
After O1/O2/O4 acceptance, a separately reviewed wiring change must bind approved
message templates/recipient/expiry to this adapter, preserve leased encrypted
outbox fencing and its five-attempt 1/2/4/8-minute retry schedule, terminal expiry,
shared rate budgets and secret deletion, and approve SMTP worker egress. Do not
open an existing internal application network merely to try SMTP.

Existing registration confirmation, reset and password-change notices have
outbox coverage. Invitation and additional security templates/recipient rules
remain subject to their accepted contracts; this generic transport does not
invent them. Lost-all-factor/assisted recovery remains O5-blocked, without an
operator password/MFA bypass. Production retention is O4, not synthetic TTLs.

## Staging reuse and server coexistence

Use [the existing staging runbook](../../infra/staging/README.md), renderer,
Compose wrapper, migrations, PKI, private PostgreSQL, encrypted off-host backup /
fresh restore rehearsal, host observer and rollback procedure. Do not create a
second stack or use root development Compose for auth. Existing readiness has:

- Only gateway 443 published; distinct NGO/OPS builds/hosts and genuine end-to-end
  TLS/mTLS through Nginx/Gunicorn/PostgreSQL, no forwarded-proto trust or CORS.
- Project-scoped internal networks/volume, no DB/WSGI host ports, read-only
  non-root application processes, bounded resource/log settings and no Docker
  socket. DB owner is maintenance-only; app cannot write account/session/authority
  tables. Live auth needs a reviewed least-privilege extension, not blanket grants.
- Migration-before-ready, health probes, no startup account provisioning, and
  rollback which retains data and never destructively reverses used auth schema.
- Null request/payload logging, status-only diagnostics and sanitized CI evidence.
  Real-user observability/audit retention needs O4; do not collect raw SMTP, HTTP,
  cookie/token or database logs to debug enrollment.

New **offline** coexistence assessment, from repository root:

```sh
python -m infra.staging.readiness --config /owner-private/config.json --inventory /owner-private/host-inventory.json
```

An owner-supplied, current local inventory has exactly `inventory_complete`
(boolean true), `compose_projects` (project-name list) and `tcp_ports` (occupied
TCP-port numbers). It is not checked into Git. Missing/incomplete data, an
existing intended project or occupied 443 fails closed. Other projects and their
DB/HTTP ports are not stopped or changed. If another project owns 443, approve a
separate address/host or a separately reviewed coexistence design; do not replace
its proxy, alter DNS or silently change the accepted TLS topology. Renderer also
refuses an existing output directory. A passing self-reported inventory is not
actual-host acceptance or deployment authorization.

Supply through the approved operational channel: VPS identity/OS/patch owner,
Docker/Compose versions, capacity/firewall/SSH and occupied ports/projects; exact
two DNS names; image registry/architecture and reviewed immutable release/image
SHAs; externally managed secret/PKI paths and renewal/rotation owners; encrypted
off-host backup destination/RPO/RTO and restore reviewer; and approved rollback
window. The existing config's Django/DB/abuse secrets, separate server/client CA
certificates and keys remain external. No server, DNS or production changes are
performed here.

## Security evidence and activation sequence

See [actual image advisory matrix](../reviews/PWC-IMAGE-REMEDIATION-20261105.md).
Only fixable findings were remediated; unfixed HIGH/CRITICAL findings remain
visible and require review, not a fabricated clean-bill-of-health. The original
scanner digest, severity threshold and fixable gate are unchanged. New CI records
installed apt versions and allowlisted package details from all five final images.
Issue #40 remains open; each current npm audit is time-specific evidence, not
permanent remediation or an audit waiver.

1. Complete CI/review of the exact preparation revision and residual findings.
2. Accept the narrowly scoped issuer/invitation/privacy/delivery contracts above;
   implement and test actual invitation expiry/replay/concurrency/recipient/MFA
   checkpoints without privilege activation. Approve no secrets in Git/chat.
3. Only after explicit staging-deployment authorization, have the operator apply
   reviewed artifacts to the identified isolated host, rehearse restore/rollback,
   and obtain independent actual-host acceptance. No action in step 3 was run.
4. Obtain separate credential transport/email/real-user enrollment activation for
   that environment/version, then have each person accept their own invitation,
   choose their own password/MFA and retain their own recovery codes privately.
5. Keep institutional verification/independence and all Founder/verifier/NGO
   authority separate, with no automatic grants or self-verification.

**Next milestone:** close the exact acceptance/contract gaps and finish the
invitation slice. Contabo disabled-service rehearsal can then be an explicitly
authorized infrastructure milestone; real enrollment is not yet ready to enable.
