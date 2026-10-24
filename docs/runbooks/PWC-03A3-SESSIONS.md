# PWC-03A.3 — Browser/mobile sessions

**2026-10-24; implemented synthetic backend slice, default disabled.** Not MFA,
frontend, NGO authorization, production deployment or governance acceptance.
The next slice is 03A.4; do not activate unfinished assurance operations.

## Integrity and engineering contract

Preflight was clean on `arena/7bcc0d8b-pwc-platform`; local and fetched remote
HEAD were exactly `af40ebe3fc5178c6296cc4c8b651fefde0954cb4`. Fresh baseline:
93/93 tests passed. Custom User, security models, migrations 0001–0004,
registration/recovery services and ADR are unchanged. No new migration.
ADR SHA256: `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
Historical recovery provenance/limitations remain in the 03A.2 recovery review;
this work does not manufacture missing historical commits.

Pre-implementation engineering acceptance recorded R2/R3/R6/R7: exact HTTPS
portals, 5-minute access, strict single-use refresh/no grace, no passive renewal.
This implementation also uses R11's five failed passwords/target/15 minutes,
30 login attempts/IP/15 minutes and 30 refreshes/session/minute. Success neither
spends nor resets the target failure counter. Browser and mobile share it.
An additional conservative shared public budget limits refresh attempts to
30/IP/15 minutes, including invalid attempts. IP/target counter windows are
fixed, not sliding. No permanent anonymous lockout. All budgets need O2/NAT
review before operation; they are not production-tuned guarantees.

## Configuration and topology (fail closed)

- `PWC_AUTH_SESSIONS_ENABLED=0` by default; independent of registration/reset's
  `PWC_AUTH_FLOWS_ENABLED`. Disabled session API returns `AUTH_UNAVAILABLE` 503.
- `PWC_AUTH_SESSION_KEY`: separate externally generated >=256-bit secret
  (`secrets.token_urlsafe(32)`, >=43 characters); no fallback to SECRET_KEY or
  database data. `PWC_AUTH_ABUSE_KEY` is also required (>=32 characters).
  Delivery encryption keys are not needed to authenticate an existing verified
  account. Do not print any generated keys or commit them.
- `PWC_AUTH_PORTALS={}` by default. Synthetic example only:
  `{"https://ngo.pwc.invalid":"ngo_web","https://ops.pwc.invalid":"pwc_ops"}`.
  Use exact canonical HTTPS origins, no trailing slash, credentials, path,
  query, wildcard or fragment; one origin per portal type. Explicitly configure
  matching `DJANGO_ALLOWED_HOSTS`. Empty/invalid map blocks browser issuance.
  Portal is never chosen by a request body or a user's alliance/NGO role.
- Direct TLS is the tested request topology. Forwarded host/port trust or a
  `SECURE_PROXY_SSL_HEADER` configuration disables session operations pending O3
  review. Spoofed forwarded headers are not used; IP budgets use REMOTE_ADDR.
  No permissive CORS or guessed deployment origins are added. Ordinary HTTP
  Compose/runserver and a TLS-terminating preview proxy are **not** a reviewed
  browser-login deployment. Tests use Django's explicit secure-request adapter,
  not a live TLS/browser acceptance environment.
- Browser requires Django DB sessions, `__Host-pwc_session`, Secure, HttpOnly,
  host-only (Domain=None), path `/`, SameSite=Lax (Strict also accepted by the
  gate). Other cookie names must retain `__Host-`. CSRF cookie must be Secure.
  Distinct portal hosts isolate cookies; registry also checks portal binding.
- Session HMAC key replacement invalidates existing browser registry bindings
  and mobile proofs: deliberate global re-login, no old-key fallback. Normal
  password/reset/suspension services must advance epoch/revoke. Django SECRET_KEY
  rotation has its own cookie implications, not a replacement for this policy.

Both `.env.example` flags remain off and keys/maps empty. No real users,
provider, secret, role grants or operational activation were introduced.

## Transport rules and API

Prefix `/api/v1/auth/`; trailing slash required. JSON commands: object of string
values, exact declared fields, <=8192 bytes; label optional, <=100 characters,
no control characters. No embedded mobile client secret. Responses use
`Cache-Control: no-store`, `Referrer-Policy: no-referrer` and the existing error
shape `{error:{code,message,field_errors,request_id}}`. Rate-limit responses
include Retry-After. Business API errors do not replace upstream routing/TLS
errors. Method mismatch is 405 with Allow.

**Mixed credentials:** presence of the configured authentication cookie AND any
Authorization header gives `AMBIGUOUS_CREDENTIALS` 400 before identity lookup,
CSRF, flag checks or mutation. An invalid credential is not permission to fall
back to the other mode. A CSRF cookie alone is not an authentication cookie.

| Method/path | Transport and body | Current result |
|---|---|---|
| GET `csrf/` | Existing same-origin bootstrap, no Authorization | Masked `csrf_token` and CSRF cookie; no authentication |
| POST `web/login/` | Exact mapped HTTPS portal, anonymous CSRF required; `email,password`, optional `device_label`; no Authorization | 200 minimal browser envelope + rotated cookie; never bearer/refresh |
| POST `mobile/login/` | Native only; same fields | 200 envelope + opaque access/refresh pair |
| POST `mobile/refresh/` | Native only; `refresh_token` only, no access header | 200 replacement pair + envelope |
| GET `me/` | Exactly one cookie OR Bearer | 200 personal envelope + `email_verified:true` |
| POST `logout/` | Same; browser CSRF; empty body or `{}` | 204; revoke current family; clear web cookie |
| POST `logout-all/` | Same; browser CSRF; `assurance_proof` | Valid-shaped request: `STEP_UP_REQUIRED` 403; no revocation |
| GET `sessions/` | Exactly one cookie OR Bearer | 200 `{results:[...]}` own unrevoked/current-epoch/unexpired sessions |
| DELETE `sessions/{id}/` | Same; browser CSRF; `assurance_proof` | Missing/malformed/foreign target 404 first; own target then safe 403 |

Browser writes require matching Origin, or matching HTTPS Referer if Origin
absent, AND Django CSRF cookie/header proof. Anonymous login is not exempt.
Native issuance/refresh reject authentication cookies, any Authorization header
and presence of Origin, Referer or Sec-Fetch-Site. This is transport separation,
not device attestation. Shared Bearer endpoints require direct HTTPS and exact
`Bearer <opaque-access>`; cookie unsafe commands require CSRF. Browser response
never includes bearer/refresh credentials. Registration/reset's stricter
transport/ownership rules remain unchanged; their tests use the configured new
cookie name rather than a hard-coded legacy name.

Generic `INVALID_CREDENTIALS` 401 covers unknown, inactive, unverified,
retired/nonprimary contact and wrong password. Canonical verified primary email
only; no public username fallback. Usable legacy short passwords can log in;
new/reset passwords retain the existing 15–128 policy. Invalid sessions return
`SESSION_INVALID` 401. Correct-password MFA-enabled login returns `MFA_REQUIRED`
403 with no session or preauth credentials. An existing session is invalidated
if an active factor appears; 03A.4 must implement verified-factor continuation,
not remove checks without replacement. Assurance method `password` is not a
recent step-up proof. No password-only shortcut for logout-all/device DELETE.

## Envelopes and client fixture

`packages/api-contracts/auth-sessions-v1.fixtures.json` is checked against actual
responses; not a generated OpenAPI schema or working credentials.

Base envelope:
- `user:{id,preferred_language}`; no username, password hash, role, NGO data.
- `session:{id,absolute_expires_at,idle_expires_at,assurance:{method:"password",last_mfa_at:null}}`.
- `recovery_hold_state` is live state, not a restored grant or authorization.

Mobile additionally returns `access_token`, `token_type:"Bearer"`, `expires_in`
(up to 300), `refresh_token`, `refresh_expires_at` (absolute ISO8601). Me adds
`email_verified:true`. List items: `id,device_label,transport,created_at,
last_interactive_at,is_current`; no credentials or network/private NGO data.
Labels are untrusted display text, not trusted device identity: render as text.

Browser integration: fetch relative `csrf/` on the chosen same-origin portal,
retain cookies, send X-CSRFToken and JSON login, then refresh the masked CSRF
value after login rotation. Use relative URLs; no browser calls to sandbox
localhost or cross-origin credential forwarding. No frontend is built here.
Legacy Django-only cookies are not upgraded into registered authority. The
configured verified-email backend and online registry middleware replace that
compatibility path; no claim of Django Admin/username-login compatibility.

Native integration: serialize refresh per family; securely replace access AND
refresh together after a successful response, before making further calls.
Use OS protected credential storage, never ordinary preferences, URL/query,
analytics, crash reports or app logs. Public client has no secret embedded.
On failed/ambiguous refresh, storage failure or lost response, clear local
credentials and re-login; **do not retry consumed refresh**. Another valid
request might briefly use a winning response before a replay transaction
commits, but no descendant survives committed family revocation. Flutter UI,
network retries, secure storage and real client runtime remain untested gates.

## Lifecycles, concurrency and authority boundary

| Session | Idle | Absolute | Access |
|---|---:|---:|---:|
| Mobile | 7 days | 30 days | min(5 minutes, remaining absolute) |
| NGO web | 30 minutes | 12 hours | Cookie + live registry |
| Operations web | 15 minutes | 8 hours | Cookie + live registry |

Deadlines deny at equality. Refresh/status/list/reads do not renew inactivity
or absolute expiry. There is no heartbeat, client-selected "active" flag or
ordinary interactive command in this slice that renews idle. Re-login creates
a new session. Same-user/browser reauthentication retires its old registry row;
independent successful submissions create independent families, one per committed
login, not an idempotent login replay API.

Opaque proofs contain UUID selector + independent 256-bit CSPRNG secret (76
characters total). Only purpose-separated Django HMAC-SHA256 digests persist.
Digest binds selector, secret, User UUID, family UUID and live encoded password.
Consumed-refresh foreign-key reassignment cannot revoke another family, even
with identical legacy password hashes. Browser registry stores a keyed session
key digest and verifies Django owner/backend/password auth hash and registry ID.
Session/token UUIDs are selectors, never sufficient credentials.

Transition lock order: User -> contact/factor where applicable -> registry ->
credential. Refresh re-reads ownership/kind after acquiring the User lock;
missing/stale rows deny, never trust the initial selector snapshot. Successful
refresh consumes once, replaces old access immediately, increments generation
and issues one pair, with no grace period. A correct consumed refresh revokes
its family atomically; wrong-secret/guessed selectors cannot cause revocation.
Replay denial is returned normally so revocation commits (not rolled back by an
exception). Independent families are unaffected. Deadlines rechecked after
potentially blocking budget work; logout rechecks proof expiry at mutation.
Bounded command bodies are buffered before acquiring owner locks.

Login password check is serialized by the target failure bucket; release it
before User/domain locks. Under User lock recheck password/epoch/active/contact
before issuance. Reset/suspension winning the lock race cannot mint credentials
from an earlier password check. Reset uses existing all-session/epoch revocation;
trusted internal suspension/revoke-all hooks serialize with refresh. No public
operator/NGO suspension or ungated logout-all API is exposed. Reactivation never
revives old families. Direct password hash replacement invalidates proofs too,
but is not a substitute for approved security services/epoch transitions.

Every authenticated command checks live account, verified primary contact,
revocation, epoch, password binding and deadlines. Online cookie middleware also
overrides Django's async `auser`; default DRF cookie authentication cannot accept
unregistered legacy sessions. Bearer is not implicitly selected by middleware;
`PersonalAuthentication` is the explicit future DRF adapter. Adapter reads may
finish after a later revocation commit; it is **not** a transaction/permission
wrapper for future privileged mutations. Those must revalidate under owner locks
with domain authorization in the action transaction. No identity envelope grants
membership, finance, Board/PWC operations or NGO-private access. Recovery hold
continues; authentication cannot restore those grants.

## Performed validation and limits

Environment: Python **3.11.2**, actual **PostgreSQL 16.2** via pgserver 0.1.4,
pinned project dependencies. Fresh temporary cluster and Django test database;
no SQLite substitution, live users, provider or production data.

- Prechange 93/93 in 27.167s; initial implementation preserved 93/93 in 27.228s.
- Final combined **153/153 in 75.009s**, no skips: existing 93 + **60** session
  tests. Full `check`, migration drift, plan, apply and applied-state checks pass.
- Repeated PostgreSQL concurrency subset **16/16** on each of three additional
  runs: **9.685s, 9.809s, 9.628s**. Includes registration/recovery/ownership races
  plus duplicate refresh, independent login, reset/suspension/internal revoke
  versus refresh, and suspension/reset between password check and issuance.
- Browser CSRF/fixation/cookie+CSRF rotation, portal/proxy rejection; native/mixed
  transport; live state/expiry/password/epoch/reset; replay/lost response/foreign
  family and unsafe ORM ownership; assurance safe denial; adapters/async bridge;
  error/no-secret envelopes; response fixtures; distributed-IP refresh budget;
  cleanup preserves replay floor and cannot resurrect revoked/expired families.
- `pip check`, scoped Black check and `git diff --check` pass. Repository-wide
  Black also reports pre-existing formatting in apps.py, config urls/wsgi and
  migrations 0001/0002; those historical files are intentionally untouched.
- ADR/User/security models/migration source integrity checked against starting
  commit. Existing foundation deferred-route assertion updated only for newly
  authorized paths; old cookie assertions now use configured cookie name.

Local raw logs (outside Git): `/home/user/pwc03a3-baseline.log`,
`pwc03a3-full.log`, `pwc03a3-races-{1,2,3}.log`. Reproduce with configured
PostgreSQL using the LOCAL-SETUP commands and `python manage.py test`; subset:
`accounts.test_sessions.SessionConcurrencyTests`,
`accounts.test_sessions.AdditionalSessionRaces`,
`accounts.test_registration.ConcurrentFlowTests`,
`accounts.test_registration.AdditionalPostgresRaces`,
`accounts.test_registration.ResendConfirmationRace`,
`accounts.tests.ConcurrentConstraintTests`.

No Python 3.12/Docker/remote CI acceptance, external pentest/CVE audit, physical
browser TLS test, timing side-channel certification, Flutter/web UI or production
load claim. Timing output from old registration tests is not a login timing
certification. Consumed refresh evidence is retained through absolute family
expiry; existing flow cleanup does not delete session/credential rows. No new
session purge policy is invented. Bounded session/event retention and cleanup
scheduling (including expired credential disposal) remain explicit O2/O4 gates;
list pagination/session-volume caps also require review before real deployment.

## Remaining gates / next slice

03A.4 may build actual factor/preauth/recovery-code/operation-bound assurance on
this locked live-state contract. Until then, syntactically valid logout-all and
own-device DELETE deny, and MFA-enabled users cannot log in. Default-disable is
intentional, not a completed account-management product.

O1–O6 remain: selected public domains and separate web hosts/frameworks; reviewed
TLS/proxy/ingress/CSRF/CORS/cookie deployment; secret generation/rotation/loss and
backup controls; synchronized clocks/DB health; NAT and global abuse/load limits,
retention/disposal and safe logging/APM; device storage/retry UX and frontend
acceptance; real-user/provider/security/governance/privacy/operational approvals.
Do not enable on an inferred preview topology or claim production readiness.
