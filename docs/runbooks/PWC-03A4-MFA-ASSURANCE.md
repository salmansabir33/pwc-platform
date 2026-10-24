# PWC-03A.4 — MFA and operation-bound assurance

## Pre-implementation policy (2026-10-24)

Clean branch `arena/7bcc0d8b-pwc-platform`, local and fetched remote exactly
`26b0ad31f0fc41b71ee2f95e8950923fa9162144`; ADR SHA256
`bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
Source integrity checked; fresh PostgreSQL baseline **153/153 in 71.109s**.
Existing User/security schema, migrations and transport services are retained.

Engineering acceptance for this synthetic assignment: R3/R8/R9/R11 and B2's
factor component use pinned PyOTP 2.10.0 (RFC6238 implementation; installed on
Python 3.11), existing cryptography 50.0.2 Fernet, independent external factor
key ring/key ID and Django purpose-separated HMAC-SHA256. No handwritten OTP or
encryption algorithm. This is scoped component selection/testing, not external
cryptographic audit, product approval or production key-management certification.
TOTP: six digits, SHA1 interoperability, 30-second step, ±1 step skew, monotonically
increasing accepted step under User/factor locks, five attempts per flow/window.
Pending enrollment and preauth expire after five minutes. A separate default-off
MFA flag preserves existing disabled posture and safe denials when not enabled.

Enrollment requires a same-session operation intent and reentered current
password; an existing factor additionally requires live/recent TOTP. Hold must be
clear. New secret shown only in initiation; confirmation proves possession before
activation. Only one pending/active factor; replacement requires existing-factor
assurance and confirmation of new secret. Initial activation preserves/promotes
the enrolling session and revokes others; replacement/removal revokes all,
requires fresh login. Neither enrollment nor factor changes clear a hold.

Password-correct MFA login returns only 202 preauth challenge/control, bound to
user/epoch/password/factor revision/transport/portal. Browser additionally binds
to an anonymous session cookie and enforces CSRF; native control is an independent
256-bit capability held by the initiating client. Completion single-use, no
partial authentication or native token issuance. Recovery codes: ten independent
256-bit codes, only keyed owner/factor/revision-bound verifiers persisted, displayed
once; atomic consumption, old set revoked at rotation. Password+code login retains
TOTP, advances epoch/recovery generation, revokes existing sessions and creates a
restricted personal session with `review_required`. No automated review clearance.

Intents are server-generated UUID/nonces, exact validated command/context/target
bound and <=5 minutes, never beyond session idle/absolute. Confirmation reenters
password and requires active TOTP where enrolled; same-session TOTP within five
minutes at the still-active revision can be reused as an observation, not as a
reusable operation proof. Recovery-code assurance cannot qualify. Final consumption
rechecks ownership, session/epoch/hold/generation/revision, operation/command and
permission in the same transaction as mutation. Cross-user/session/NGO/operation
proofs cannot confer access. Unmapped operations deny before issuing intents.

`restricted` hold clearance requires a specific hold-clear intent, password and
same pre-hold active factor/revision; `review_required` and absent/lost pre-hold
factor stay blocked (O5). Reset retains MFA and persistent hold. No matching-name,
staff/superuser, email, elapsed-time or new-factor recovery shortcut.

## Privileged-action assurance matrix

| Category | Mechanism in this slice | Authorization / remaining decision |
|---|---|---|
| Own enrollment | Password; existing TOTP if enrolled; clear hold | Personal owner/session only |
| Own factor remove/replace/code rotation | Password + live/recent existing TOTP; clear hold | Personal only; unmapped privileged actions remain denied after removal |
| Logout-all / own-device revoke | Password + TOTP if enrolled; no recovery-code assurance | Own target checked before intent/proof consumption; holds do not bypass factors |
| Restricted hold clearance | Password + pre-hold existing TOTP | Only restricted→clear; no grants restored |
| Platform/support elevation | No public intent or grant | B3/PWC-02C and operational approval; deny |
| NGO role delegation / sensitive export | No public intent or grant | Independent tenant permission and approved B3 matrix required; deny |
| NGO financial approval / posting | No public intent or grant | Separate finance grants/versioned domain transaction; deny |
| NGO commitments / governance | No public intent or grant | NGO-specific approved representative/version policy; deny |
| Assisted/lost-all-factor recovery / review-required clearance | Disabled | O5 independently reviewed human procedure; no staff override |

No finance/tenant demonstration endpoints. Generic context IDs are not authority.
The personal allowlist does not approve B3 domain policies. Contact replacement
and other unassigned account workflows remain unmapped rather than piggybacking
on generic assurance. Operational gates O1–O6 and all 03A.3 deployment limitations
remain. Final evidence, API fixtures and limitations will be appended after tests.

## Implemented API and integration contract

All paths below are `/api/v1/auth/`, trailing slash required. Reuse 03A.3 direct
HTTPS, mixed-credential rejection before lookup, same-origin CSRF for cookie
writes (including anonymous browser MFA), native public-client separation, strict
JSON <=8192 bytes, no-store/no-referrer and existing error envelopes. No client
secret, username fallback, permissive CORS or unreviewed proxy trust introduced.

| Method/path | Exact JSON / response |
|---|---|
| POST `web/login/`, `mobile/login/` | Existing email/password request; with active MFA and enabled flag: 202 `{status:"mfa_required",challenge_id,preauth_control,expires_in:300}`; no native credentials |
| POST `web/mfa/confirm/`, `mobile/mfa/confirm/` | `{challenge_id,preauth_control,method:"totp"|"recovery_code",code}` → normal corresponding 03A.3 session envelope, only after verification |
| GET `mfa/status/` | Cookie OR Bearer → `{enabled,pending,recovery_hold_state}`; never a secret/verifier |
| POST `assurance/intents/` | `{operation,context:{kind:"personal",id:<own UUID>},command,object_id?}` → 201 `{intent_id,expires_at,required_methods}`; `version`/domain operations not supported |
| POST `step-up/` | `{intent_id,password,totp_code?}` → `{assurance_proof,expires_at}` once |
| POST `mfa/enrollment/request/` | `{assurance_proof}` for `mfa.enroll` → 201 `{enrollment_id,secret,otpauth_uri,expires_at}` once |
| POST `mfa/enrollment/confirm/` | `{enrollment_id,code}` → `{status:"active",recovery_codes:[10 codes]}` once |
| POST `mfa/recovery-codes/rotate/` | `{assurance_proof}` for `mfa.recovery_codes.rotate` → `{recovery_codes:[10 new codes]}` once |
| POST `mfa/remove/` | `{assurance_proof}` for `mfa.remove` → 204; all sessions/codes revoked |
| POST `recovery-hold/clear/` | `{intent_id,password,totp_code}` for pending `recovery_hold.clear` intent → 204 atomically confirm+consume; no separate prior step-up call needed |
| POST `logout-all/` | `{assurance_proof}` for `sessions.logout_all` → 204; epoch advance, all sessions/preauth/intents revoked |
| DELETE `sessions/{id}/` | `{assurance_proof}` for `sessions.revoke`, command `{session_id:<same own target UUID>}` → 204; own target checked first, foreign/missing 404 without consuming proof |

Every command is `{}` except `sessions.revoke`. Target IDs are normalized and
derived by the server; client digests, extra commands, arbitrary versions,
`mfa=true`, platform/NGO contexts and unmapped operations cannot authorize. The
server's random intent UUID is the operation-challenge nonce/selector, not a
credential; after authentication a separate independent 256-bit proof is issued.
Proof format uses the existing UUIDhex.secret parser, not a new bearer transport.
No proof is accepted on ordinary profile endpoints as authentication.

Browser preauth flushes old authenticated/anonymous cookie state, creates a new
five-minute anonymous session with a server preauth marker and rotates CSRF.
This prevents an incomplete flow preserving a prior principal. Completion needs
that same persisted anonymous cookie AND control AND CSRF AND exact portal;
copying only an ID/control or changing host is insufficient. On completion Django
cookie/CSRF rotation and normal registry creation still apply. Fetch a fresh
masked `csrf/` value after each rotation. Use relative same-origin URLs, no
browser localhost backend calls. Native login/confirm must have no auth cookie,
Authorization or browser provenance headers; retain the flow control only on the
initiating client. It is not full authentication or an embedded app secret.

TOTP is 32 Base32 characters (160 random bits), six digits, 30 seconds, SHA1,
±1 step; PyOTP performs verification. Last accepted timestep advances strictly
under the User/factor lock. A freshly accepted timestep cannot log in another
session or confirm a second challenge. Within the same session, eligible recent
TOTP can be reused as an observation by omitting `totp_code` in step-up; supplying
a code always verifies it (invalid/decryption failure is not ignored just because
there is recent assurance). Reusing an observation does not update `last_mfa_at`.
Successful explicit password/factor reauthentication can renew idle, never
absolute expiry; passive requests/refresh still cannot. Expired sessions cannot
be resurrected by step-up. Proof expiry is capped by intent/session and the
five-minute factor-observation deadline.

Counters: shared 30/IP/15-minute public-route budget, five lifetime attempts per
preauth/enrollment/intent and an additional five TOTP attempts (including valid
attempts) per active factor/fixed five-minute window. Pending/intent counters are
anchored to creation, not reset by a wall-clock boundary. These conservative
synthetic limits require NAT/load/abuse review; they are not production tuning.

Response/error examples and keys are checked against executable behavior in
`packages/api-contracts/auth-mfa-v1.fixtures.json`. The 03A.3 fixture still covers
MFA-disabled behavior. Invalid challenges: generic CHALLENGE_INVALID 400; invalid
operation proof: STEP_UP_REQUIRED 403; authenticated owned proof replay: STATE_CONFLICT 409; held policy: RECOVERY_RESTRICTED 403;
expired/revoked sessions: SESSION_INVALID 401; infrastructure/key errors:
AUTH_UNAVAILABLE 503. No secret exists in ordinary me/status/list responses.

Clients must serialize completion/refresh and use secure native storage. Never
capture QR/otpauth URI, password, code, preauth control, recovery codes, proof or
API bodies in logs, analytics, crash reports, URLs to servers or backups. The
local otpauth URI is solely for authenticator provisioning, not a redirect/link
to a server. Response loss does not permit fetching old secrets/proofs/codes:
start a new authorized intent/enrollment/code rotation. Lost MFA login response
requires fresh login/possibly the next timestep. The existing mobile refresh
lost-response/replay policy remains strict; do not retry consumed refresh.

## Transactions, storage and lifecycle

Reuse User -> contact/factor -> registry -> challenge/credential/intent locking;
all same-owner transitions serialize on User with PostgreSQL, no local mutex.
Re-read challenge purpose/owner/epoch/password/factor revision/client/portal,
terminal state and deadlines after locks. Final preauth deadline is rechecked
after potentially blocking verification. A raw FK reassignment cannot give
another owner's factor, recovery code or session authority. Factor ciphertext
binds its purpose/User/factor UUID; active factor's enrollment session ownership
is checked. Assurance HMAC binds User/session, intent, operation/context/target,
validated command digest, epoch/generation, methods/revision and expiry. Changing
scope or extending expiry via unsafe ORM cannot repurpose an issued proof.

Initial activation advances epoch, invalidates preauth/intents and revokes other
sessions, then explicitly preserves/promotes only the confirming session.
Replacement confirms new factor first, retires old factor/codes, advances epoch,
invalidates preauth/intents and revokes **all** sessions. Removal likewise revokes
all; relogin required. Code rotation retires old code rows using consumed_at (no
plaintext retrieval); audit distinguishes issuance/rotation from code-login use.
Active factor's epoch fields are enrollment snapshots, not an instruction to
remove MFA on password reset. Existing reset service and hashes are unchanged.

Recovery-code login consumes once, advances epoch/recovery generation, retains
factor and old relationships, sets review_required and issues only a restricted
personal session. Valid TOTP later can establish TOTP assurance on that session
for permitted personal logout-all/device actions; it still cannot clear review
hold, enroll/remove/rotate factors or restore any grant. Restricted hold clearance
requires the exact active factor/revision confirmed before hold; it atomically
consumes intent, advances recovery generation, invalidates other pending intents
and records a typed clearance event. No automatic clearing for absence of factor,
new enrollment, reset, recovery code, elapsed time, identity match or staff flag.

No permission callback for an unapproved domain is registered. Future PWC-02C
integrations must authorize actor/tenant/object/version, canonicalize exact
command, and recheck grants plus consume proof in the **domain mutation's own
transaction**, under compatible lock order. The current personal allowlist is
not a generic finance/grant authorization API or transferable MFA capability.

## Keys, schema and deployment prerequisites

New settings (all empty/off in `.env.example`):
- `PWC_AUTH_MFA_ENABLED=0`; requires existing session flag/configuration too.
- `PWC_AUTH_MFA_ACTIVE_KEY`: <=100-character active key ID.
- `PWC_AUTH_MFA_KEYS`: external JSON key-ID → Fernet-key ring; generated via
  `Fernet.generate_key()`, never database/Git-derived; separate from delivery keys.
- `PWC_AUTH_MFA_PROOF_KEY`: independent >=43-character >=256-bit random HMAC key
  (`secrets.token_urlsafe(32)`); do not reuse encryption/session/abuse keys.

Encryption uses pinned existing cryptography/Fernet; authenticated ciphertext
contains only purpose, owner, factor and secret. Retain old ring entries while
factors use them; adding a new active key doesn't silently decrypt with another
key or rewrite factors. Missing/wrong/tampered keys fail closed, not password
fallback (including explicit recovery-code completion if factor decrypt fails).
Recent already-verified TOTP is an allowed observation, not a new decryption
attempt. HMAC key rotation invalidates outstanding preauth/assurance and recovery
verifiers; plan authorized TOTP-based code reissuance. No fallback HMAC keys or
key-loss identity-matching bypass. Vault/KMS, rotation/backup/incident procedures,
body/APM redaction, TLS and synchronized clocks remain O3 operational work.

**Additive migration 0005_mfa_preauth_binding** adds only client_digest,
factor_revision and device_label to AuthChallenge. No backfill, new identity,
initial-migration rewrite or hash/relationship mutation. User unchanged;
0001–0004 and ADR byte-preserved. This is not a destructive production rollback
procedure; disable endpoints and use reviewed forward fixes/backup procedures.
The old deferred-route test now tests only still-unimplemented contact change;
new authorized endpoints are tested as disabled-by-default rather than absent.

Factor/preauth/intent evidence and ciphertext retention/disposal needs approved
bounded cleanup and scheduling before real deployment. Existing cleanup only
prunes old registration/reset/counters, not the new MFA lifecycle records. This
slice does not invent privacy retention terms or claim production row-growth
limits. Do not deploy with debug, body logging or synthetic keys.

## Validation evidence (2026-10-24)

Python **3.11.2**, real PostgreSQL **16.2** via pgserver 0.1.4; temporary empty
clusters and actual Django test databases. Pinned PyOTP **2.10.0** installed and
its verification implementation reviewed; existing dependency versions retained.

- Fresh exact-checkpoint baseline **153/153 in 67.318s**; historical preflight logs were missing and were not relied upon.
- Recovery complete suite **226/226 in 155.583s**, no skips: all prior 153 plus
  **73** MFA/assurance/ownership/contract/concurrency tests.
- **27/27** concurrency/security-negative subset passed on each of three additional
  runs: **21.544s, 22.490s, 23.814s** (seven MFA races, four recovered regressions plus existing 16).
- `check`, `makemigrations --check --dry-run` (no drift), migration plan,
  migration apply and applied-state check passed; pip check, scoped Black and
  diff whitespace checks passed. Historical formatter debt outside edited files
  is not silently reformatted or claimed fixed.
- ADR SHA256 unchanged; User and migrations 0001–0004 source compared with
  required start. Existing reset/session/registration/tenant public projection
  regressions passed; no NGO financial end-to-end acceptance claim.

New races: competing activation, same-step TOTP, simultaneous recovery-code use,
proof double consumption, reset/suspension versus MFA completion, replacement
versus independent-family refresh. Exactly one activation/code/action succeeds;
revocation winning the lock prevents issuance, or revokes a preceding winner.
A same-family refresh may legitimately supersede a concurrent command's access
proof before it locks (401); it is not permission to finish that command using
stale access. Replacement/refresh race uses independent families to exercise
all-session revocation rather than assuming the superseded access stays valid.

Coverage also includes skew/expiry/replay, wrong owner/session/control/portal,
partial authentication, secret tamper/key loss/rotation, recovery holds and old
factor clearance, password reset retention, proof scope/expiry tampering, epochs,
revoked sessions, unmapped/cross-NGO denial, no plaintext in normal responses,
security-event values or handled-error log messages, and fixture wire keys.

Reproduce using LOCAL-SETUP with a PostgreSQL CREATEDB test role:
`cd apps/backend && python manage.py check`, migration commands above, then
`python manage.py test --verbosity 2`. Race subset labels:
`accounts.test_mfa.MfaRaces`, `accounts.test_sessions.SessionConcurrencyTests`,
`accounts.test_sessions.AdditionalSessionRaces`,
`accounts.test_registration.ConcurrentFlowTests`,
`accounts.test_registration.AdditionalPostgresRaces`,
`accounts.test_registration.ResendConfirmationRace`,
`accounts.tests.ConcurrentConstraintTests`.
Logs outside Git: `/home/user/pwc03a4-recovered-baseline.log`,
`pwc03a4-recovered-full.log`, `pwc03a4-recovered-races-{1,2,3}.log`,
`pwc03a4-regressions.log` and the two reproduced-failure logs.
Reproduction harness `/home/user/pwc03a4-validate.py` uses pgserver; the exact
checkpoint test source was a plain `git archive` outside the working repository,
not another branch or worktree.

## Readiness and explicit remaining blockers

Ready for final **backend authentication integration/security review**, not
production or G1a certification. B2 factor components have scoped engineering
selection/evidence here; independent dependency/security audit, Python 3.12,
Docker, remote CI, physical-browser TLS, actual authenticator/Flutter/web storage
and UX testing have not been performed. No real users/provider/live deployment.

B3 domain permission/retention matrix and PWC-02C integration remain blocked;
platform/NGO/finance/commitment operations deny. O5 assisted recovery and
review_required clearance stay disabled, even if a legitimate user loses all
factors. O1–O6 remain. Contact replacement/password-change endpoints are not
added merely as assurance demonstrations; they require their own bounded assigned
integration review. Historical runbooks describe their slice checkpoints, not
activation approval. No next work package, UI, business endpoint, PR or merge
is automatically started.


## Authorized preservation-first recovery and review

The interrupted environment restored local HEAD to `fc7056f` while 03A.1–4
files survived. Work stopped and explicit preservation-first authorization was
obtained. No prior uncommitted MFA commit or missing validation log is fabricated.
GitHub API and fetched feature ref both verified exact `26b0ad31` before recovery.

Backup retained outside Git:
`/home/user/pwc03a4-preservation-20261024T093502Z/`.
All **84** non-.git project files (962,520 bytes) were independently copied and
archived before changing Git state, then SHA256-verified from both copies and tar
members. Git status (including staged/untracked/ignored), binary patches, refs,
history and original Git bundle were preserved. There were no ignored project
files at that point; the runtime/venv/logs had not survived. Both checksum
manifests remain, including `manifest-with-status.json`; original SHA256SUMS
reverified after reconciliation. No Git authentication configuration was copied.

A retained include-untracked stash provided a second safeguard. The SAME branch
was fast-forwarded from fc7056f to the existing 26b0ad31 checkpoint; no reset,
force operation, branch switch, old-commit reconstruction or history rewrite.
Archive comparison found **68** files exactly equal to that checkpoint and
**16** unfinished MFA paths (ten modified integration files and six new files).
Only those MFA paths were copied back and hash-verified; no remote-only/missing
files, unrelated changes or duplicate foundation services were found.
`reconciliation.json` lists every classification. Stash and independent bundles
are retained, not reapplied wholesale or deleted after the push.

Confirmed review findings and fixes:
1. **Late credential expiry:** a token expiring during OTP/password verification
   could previously commit activation or mint an operation proof. Assured
   logout-all could likewise consume a proof/revoke after access expiry. A
   captured original credential+idle+absolute cutoff and a nested savepoint now
   guard sensitive MFA/personal mutations at final authorization, before commit.
   On expiry, provisional factor/code/proof/epoch/activity/audit writes roll back
   and response is SESSION_INVALID 401. Deliberate session revocation or initial
   promotion is not mistaken for authentication failure after mutation. Cookie
   logout occurs only after this gate. IP ingress counters remain independent.
2. **Historical migration stability:** new 0005 used the mutable model digest
   helper. Its field/validator definition is now frozen in the migration, so a
   future helper change cannot silently reinterpret historical schema. Same
   effective field state; no changes to applied 0001–0004.
3. **Stale evidence:** surviving runbook counts were older than the interrupted
   report. Fresh baseline/full/race/check evidence above supersedes them; no
   missing historical logs are treated as current validation.

Two initial regressions reproduced activation-after-expiry and live migration
helper dependence; a separate test reproduced logout-all-after-expiry. All four
final regression tests pass, including late step-up rollback and successful
subsequent enrollment with fresh credentials. Full suite has no skips. Existing
MFA replay, cipher/owner/contact binding, preauth client separation, persistent
holds, and personal-only scope checks were reviewed and retained, not rebuilt.

Remaining policy/operational gates in the preceding section are unchanged.
This recovery ends at the validated MFA checkpoint, not a PR, next work package,
production deployment or domain financial acceptance.
