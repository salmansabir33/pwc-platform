# PWC-03A.2 — Registration and password recovery

## Engineering prerequisites resolved for this slice (not production approval)

- **B1 profile:** ASCII dot-atom local parts (no quoted/SMTPUTF8 mailbox), ASCII
  lowercase comparison, preserving dots and plus-tags. Domains use pinned
  `idna==3.20`, IDNA2008 with UTS #46 non-transitional mapping and STD3 rules,
  then ASCII lowercase. Trim outer whitespace only; reject internal whitespace,
  multiple @, empty labels/trailing dot, invalid syntax and >254 canonical chars.
  Unicode domains work; Unicode local parts are rejected, never transliterated.
  `User.Name+Tag@EXAMPLE.invalid` -> `user.name+tag@example.invalid`;
  `User@BÜCHER.invalid` -> `user@xn--bcher-kva.invalid`;
  `User@faß.invalid` -> `user@xn--fa-hia.invalid` (not `fass`). Executable vectors
  cover these, composed/decomposed domains and rejection cases. Broader mailbox
  internationalization needs separate review, not silent account equivalences.
- **B2 challenge mechanisms:** `secrets.token_urlsafe(32)` (256-bit randomness),
  SHA-256 digests for these high-entropy secrets, Django constant_time_compare,
  and purpose-separated Django salted_hmac for abuse keys. Passwords continue
  to use Django hashers/validators. No OTP/MFA implementation is selected here.
- **B2 delayed mail:** PostgreSQL DeliveryIntent outbox using the maintained
  `cryptography` Fernet implementation, with an external environment key ring
  and active key ID, separate abuse HMAC key, and no production default keys.
  Library/version compatibility and tamper/wrong-key tests are required; this
  is not a claim of independent library audit. Ciphertext contains the minimum
  recipient/proof/link data. Plain proofs are never in challenge digests,
  SecurityEvent, normal logs or API responses. Key loss/tampering fails closed.
- **One delivery mechanism:** a scheduled management command leases due intents
  without holding DB locks across mail I/O. Only Django in-memory synthetic
  delivery is enabled in this assignment; real providers remain gated. Public
  flows are disabled by default. No Redis/Celery/SMS/identity SaaS introduced.

The approved ADR is preserved unchanged. These decisions finalize the scoped B1
and challenge-delivery portion of B2 under this implementation assignment; MFA
components and B3 privileged-action policy are not resolved by this work.

## Compatibility contract

Reuse PWC-03A.1 models and constraints, without changing initial migrations.
A public request creates an eligible challenge or inert placeholder with the
same response shape and encrypted outbox path; no mail provider is called in a
request. Eligibility is never returned. Legacy User.email alone never authorizes
reset. Known legacy email matches block duplicate registration and require a
separately reviewed legacy enrollment. A verified primary UserContact is the
only reset target. Prior mixed-Unicode legacy values require inventory before
live rollout; this slice does not auto-link or backfill legacy contacts.

Registration verifies proof before setting a password and atomically creates a
single personal User/contact with no grants. Reset locks User, active contact,
active factor, sessions and challenge in ADR order, rechecks ownership/epoch,
replaces password, consumes proof, advances epochs, preserves higher recovery
holds/MFA and revokes sessions/intents. Future session authentication MUST check
live auth_epoch/revoked_at; opaque access expiry alone is insufficient. Django's
legacy session auth hash also changes on reset. No login or token issuance here.

Reset notification uses a reset-family DeliveryIntent at generation N+1 after
proof generation N is consumed; it contains no proof. This reserves a separate
outbox slot without changing the challenge generation or existing schema.
Notices expire 15 minutes after consumption; proof mail retains original flow
expiry. Dispatcher recognizes notice vs proof only from authenticated ciphertext
and rechecks consumed state and generation; stale proof mail cannot be revived.
This is a delivery-family implementation detail, not a new account-recovery path.

## Engineering review, defaults and limitations

This slice's engineering review accepts R4/R5/R11/R12 for **synthetic tests**:
PostgreSQL outbox, 60-second leases, attempt-count fencing, 1/2/4/8-minute
backoff and at most five attempts, fixed UTC windows (not rolling limits),
1 send/target/minute, 5/target/hour, 30/IP/route/15 minutes, and five wrong
proofs/flow. The global synthetic delivery-request cap is 100/hour, including
placeholders. A fixed-window boundary can allow a burst; shared-NAT fairness,
distributed ingress, operational alerts and actual spend tuning remain O2/O3.
IP counters commit before workflow validation, and exhausted budgets stop new
bucket allocation. Rate-limit events are emitted once per crossed bucket, not
on every subsequent rejection. IPs use canonical IPv6/IPv4-mapped spelling;
X-Forwarded-For is not trusted. There is no automatic deadlock retry: a DB error
fails closed, and callers must not assume whether a timed-out response committed.

Cooldown uses the new `AuthChallenge.last_issued_at`, not the mutable retry due
time. Resend never extends expiry and never invalidates a different flow.
Missing required configuration/DB produces sanitized 503, never unlimited
bypass. No provider call occurs inside HTTP or an identity transaction. Latency
is not mathematically constant. The measured synthetic distributions below are
small regression samples, not a production timing-side-channel certification.

Legacy ASCII matches and up to 100 anomalous legacy email values are checked
without granting ownership. IDNA/decomposed-domain/outer-whitespace aliases are
reserved as well. More than 100 anomalies conservatively makes registration
inert until reviewed inventory/enrollment; no unbounded Python scan, silent
merge, or picking the first legacy duplicate. An unsupported legacy anomaly
also makes registration inert until reviewed inventory, rather than silently
releasing an ambiguous reservation. This intentionally affects availability,
never assigns ownership. Live inventory and legacy enrollment remain required.

Only the seven approved auth paths below are routed. Adapters use small Django
JSON views rather than implicit DRF SessionAuthentication: public commands must
not select an account from an incidental authenticated cookie, and anonymous
browser CSRF cannot depend on DRF's authenticated-session check. This keeps the
existing Django/DRF stack; existing DRF defaults/public projections are unchanged.
Cookie+Authorization is rejected first, even if either value is invalid.
Authorization alone is rejected on public commands. Browser provenance/session
cookie requires exact same/trusted Origin (or exact HTTPS Referer) AND Django
CSRF validation; wildcard origins are not accepted. Cookie-less native JSON has
no ambient login authority. JSON-only ingress/no CORS prevents cross-site simple
forms from being treated as native commands. These are public proof endpoints,
not permission to use this native classification for future login/session APIs.

There is no client confirmation page/app-link implementation here. Mail points
only at the configured HTTPS origin, with proof in fragment, never query string;
the eventual client must scrub fragment state and explicitly POST without
analytics/referrer leakage. No client-supplied redirect URL is accepted.
Notification success means synthetic handoff, not deliverability. Timeout/crash
may duplicate the SAME link. Lease attempt fencing prevents a stale worker from
changing a reclaimed/cancelled row; server generation/expiry prevents old links
from becoming authority. New email providers need separate O1/O2 review and an
adapter change; changing EMAIL_BACKEND cannot silently turn on SMTP.

## API v1 contract (relative to `/api/v1/auth/`)

| Method/path | Request | Successful response |
|---|---|---|
| GET `csrf/` | none | 200 `{csrf_token}` with masked Django CSRF token |
| POST `registration/request/` | `{email}` | 202 `{status:"accepted",flow_id,flow_control,expires_in:1800}` |
| POST `registration/resend/` | `{flow_id,flow_control}` | 202 `{status:"accepted"}` |
| POST `registration/confirm/` | `{flow_id,proof,password}` | 201 `{status:"verified"}` |
| POST `password-reset/request/` | `{email}` | same opaque 202 envelope, `expires_in:900` |
| POST `password-reset/resend/` | `{flow_id,flow_control}` | 202 `{status:"accepted"}` |
| POST `password-reset/confirm/` | `{flow_id,proof,new_password}` | 204, empty body |

Commands require an exact JSON object schema; extra fields and oversized bodies
(>8192 bytes) are rejected. No password policy details before valid possession
proof. Valid-proof policy errors do not consume it. Password policy stays 15–128
characters plus Django similarity/common-password checks, with no composition
rule. All endpoint responses use no-store/no-referrer. Errors use
`{error:{code,message,field_errors:{},request_id}}`; wrong-purpose, expiry,
consumption, collision, retired contact, inactive user and epoch mismatch share
400 CHALLENGE_INVALID. Syntax/policy 400 VALIDATION_ERROR; browser failure 403
CSRF_FAILED; throttling 429 RATE_LIMITED with Retry-After; unavailable 503
AUTH_UNAVAILABLE. Method/transport errors have the same envelope. GET confirmation
is 405 and has no effect; login/refresh/MFA/private APIs remain 404.

Fixed API/status/header/error examples are exercised directly by
`accounts/test_registration.py`; no generated SDK or frontend is claimed.

## Configuration and running synthetic delivery

The test suite supplies ephemeral random keys via `override_settings`; **no
private configuration is needed to run it**. Do not reuse test keys outside tests.
For an isolated native synthetic exercise, set these environment variables in
an ignored, permission-restricted configuration file/secret store shared with
the dispatcher. Native Django does not load `.env` automatically.

| Variable | Meaning |
|---|---|
| PWC_AUTH_FLOWS_ENABLED | `1` explicitly enables synthetic commands; default `0` |
| PWC_AUTH_ABUSE_KEY | independent CSPRNG secret, at least 32 characters |
| PWC_AUTH_DELIVERY_ACTIVE_KEY | non-secret active key ID, max 100 chars |
| PWC_AUTH_DELIVERY_KEYS | JSON object mapping IDs to Fernet-generated URL-safe keys |
| PWC_AUTH_LINK_ORIGIN | exact configured HTTPS origin, no path/credentials/query/fragment; default `https://pwc.invalid` |

Generate secret material with Python `secrets` and `Fernet.generate_key()`;
never commit or print the values in logs. Retain old decrypt keys while their
intents can be active (up to 30-minute proof expiry, or notice expiry 15 minutes
after reset). Rotate active ID for new intents; do not overwrite an old ID with
new material. Missing/wrong old keys cause bounded retry/terminal disposal, not
a plaintext fallback. Fernet is authenticated encryption; no home-grown cipher.

With the PostgreSQL environment configured per LOCAL-SETUP:

```sh
cd apps/backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --verbosity 2
python manage.py dispatch_auth_mail --limit 100
python manage.py cleanup_auth_flows --limit 100
```

A scheduler may invoke bounded batches in an isolated synthetic environment.
Locmem mail exists only in that worker's memory, not a real inbox; tests capture
it in-process. No secret-bearing console email backend is enabled. Cleanup works
with endpoints disabled or keys lost. It prunes expired abuse windows/flows and
outbox rows only, preserving consumed challenge metadata through original
expiry and reset-notice retention through its own deadline. It does not delete
Users, sessions, contacts, grants or SecurityEvents. Run cleanup regularly:
expiry is checked on every use, but physical deletion requires dispatch/cleanup,
not a magic wall-clock database trigger. Production retention is O4, not this
synthetic TTL policy. Infinite adversarial source IPs still require ingress
protection; the application does not claim an absolute database-growth bound.

## Schema, compatibility and rollback

`0004_flow_cooldown_and_transition_evidence` is additive: challenge cooldown
issue time; six nullable/blank typed SecurityEvent transition fields and four
constraints. Reset completion records old/new hold, resulting epoch/recovery
generation, reason, captured factor UUID/revision and existing correlation/time.
No arbitrary body/PII metadata field was added. Foundation/initial migrations,
User UUID/password/organization relations and custom User class are unchanged.
Migrations 0003 and 0004 both refuse destructive reversal after security state
is used; 0004 checks BEFORE dropping audit columns. Unused synthetic upgrade and
reverse are tested. Once used, disable commands, drain workers, preserve evidence
and use a reviewed forward fix/backup restore. Do not reset epochs or drop the
security tables to make rollback appear successful.

## Historical validation evidence (2026-10-23)

For current recovery validation and review findings see
[PWC-03A2-RECOVERY-REVIEW.md](PWC-03A2-RECOVERY-REVIEW.md).

- Before implementation: 35/35 existing tests passed on real PostgreSQL 16.2.
- Final scoped suite: **85/85 passed**, 30.196 seconds, Python 3.11/PostgreSQL
  16.2 disposable pgserver cluster, independent connections for race tests.
  This is 50 additional tests; the foundation route-absence assertion now
  excludes newly authorized registration, retaining deferred route coverage.
- `check`: zero issues; migration drift: none; fresh migrations and
  `migrate --check`: passed; `pip check`: passed; whitespace check: passed.
- No SQLite substitute. Python 3.12/Docker, live provider, frontend/runtime,
  production timing/load and full authentication acceptance were **not** run.
- Timing sample (8 requests/group), milliseconds min/median/max:
  registration new 16.18/16.51/18.17; existing 15.45/15.56/24.17;
  reset eligible 13.07/13.28/15.35; unknown 11.65/12.00/12.91.
  No eligible-only provider calls; no claim these distributions are identical.

| AUTH ID | Evidence/remaining scope |
|---|---|
| 01–03 | Canonical collision, atomic no-orphan identity, proof-before-password, purpose/control/generation/expiry/replay/GET, independent flow and concurrent resend/confirm tests pass. |
| 04 | Registration/reset validators and retained Django hashes pass; general login/change/inactive transport tests await 03A.3/4. |
| 05 | Generic request/resend envelopes, placeholders, no HTTP mail calls and synthetic timing samples pass; login/production timing deferred. |
| 06–07 | Scoped anonymous/incidental-cookie CSRF/bootstrap/exact origin/mixed credential tests pass; cookie rotation/portal/native session issuance deferred. |
| 08–09 | No refresh/login/idle/logout implementation claimed; future online session checks must enforce reset epoch/revocation. |
| 10 | Same/different reset proof races, epoch increment, hold capture/preservation, session/intent invalidation, request no-effect and retired/inactive/stale target tests pass. |
| 11 | Retired reset target rejection only; contact-change flow deferred. |
| 12 | Atomic cross-connection budgets, shared target/global limits, cooldown, failure counts, forwarded-IP rejection and IPv6 equivalence pass; distributed/NAT operational tuning deferred. |
| 13 | No TOTP/factor operations implemented; existing factor retained and ownership checked on reset. |
| 14–15 | Registration creates no grants; reset preserves inactive grants and User identity; existing public org isolation tests pass. No import/private tenant/finance implementation claimed. |
| 16 | Reset preserves restricted/review_required state and pre-hold factor; login persistence/hold-clear/role integration deferred. |
| 17 | No browser/mobile client runtime evidence. |
| 18 | Existing migration compatibility plus typed audit reverse guard pass. |
| 19 | No raw secrets in challenge/event records, ciphertext tamper/key-loss/rotation and terminal erasure tested; only synthetic mail contains emailed proof. Client/APM/production logging review remains. |
| 20 | Synthetic send failure/retry/expiry/reclaim/concurrent dispatcher/stale acknowledgement/notification and configured fragment links pass; live provider/app handoff remains gated. |

## Integrity and handoff

Active branch stayed `arena/7bcc0d8b-pwc-platform`. `79a1bd2` and `1182192`
were verified before edits and successfully pushed as a remote preservation
checkpoint. No reset/rebase/history replacement, PR or merge. `39fddf9` is not
available locally, and GitHub's commit lookup returned HTTP 422 "No commit found";
the reflog begins with the fc7056f clone, then preservation/foundation commits.
This is consistent with the ADR's recorded untracked-input handoff, not proof
of the missing object's full provenance; no restored commit was fabricated.
Approved ADR SHA-256 remains
`bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.

PWC-03A.2 is ready for scoped human review, not production acceptance. B1 and
challenge-delivery B2 are implemented/tested for the documented restricted
profile; MFA B2/B3 and O1–O6 remain open. PWC-03A.3 needs an explicit new assignment,
trusted test topology and its own transport/session review. Stop here: no
login/logout, mobile issuance/refresh, MFA enrollment, NGO authority or UI added.


## Integration-review corrections (2026-10-24)

All six registration/reset POST commands now require HTTPS **before** body
processing, abuse spending or workflow calls. Plain HTTP (including a spoofed
forwarded-proto header) returns 400 `TRANSPORT_NOT_ALLOWED`; it is not redirected
with secret-bearing bodies. Unreviewed `USE_X_FORWARDED_HOST`,
`USE_X_FORWARDED_PORT` or `SECURE_PROXY_SSL_HEADER` configurations fail closed in
flow configuration, matching session topology restrictions. Direct TLS is the
synthetic request contract, not approval of a proxy deployment. GET `csrf/`
is only a CSRF bootstrap, never login authority. Unsupported methods now include
an explicit `Allow` header (`POST` on commands, `GET` on bootstrap).

The earlier HTTP-default test helper is now explicitly secure, retaining every
existing test and its assertions; the direct deep-JSON regression likewise uses
HTTPS so it continues to exercise the parser, not just the transport gate.
See `../reviews/PWC-03A-AUTHENTICATION-INTEGRATION-REVIEW.md` for current combined
acceptance; earlier counts in this runbook remain historical slice evidence.
