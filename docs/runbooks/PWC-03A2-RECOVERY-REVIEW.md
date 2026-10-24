# PWC-03A.2 — Safe recovery and engineering security review

Date: 2026-10-24. Scope: recover/stabilize registration, email verification and
password recovery only. This is an engineering review, not independent external
security certification, production approval, or PWC-03A.3 implementation.

## Recovery and provenance

The checkout began on the correct active branch `arena/7bcc0d8b-pwc-platform`,
HEAD `fc7056f`, with surviving implementation files modified/untracked. The
product owner explicitly authorized a NEW implementation recovery commit based
on remote foundation `1182192`; missing `cf857005` is not recreated or claimed
preserved. No reset, clean, force checkout, rebase, force push or new branch.

Before changing branch position:

1. Enumerated unstaged/staged paths and recursively enumerated non-ignored
   untracked project files; recorded status and branch refs, plus both binary
   patches. There were no staged changes.
2. Archived all **25** surviving changed/untracked files to an independent
   workspace location outside the repository, including both migrations,
   authentication services/adapters, models, tests, validators and runbooks/ADR.
3. Wrote a per-file SHA-256 manifest. Independently reread every archive entry
   and verified its digest, and asserted the critical migrations/tests/docs were
   present before proceeding.
4. Created and retained an additional Git stash including untracked files.
5. Fetched the remote feature branch and fast-forwarded the SAME branch to
   `1182192`. Existing `79a1bd2` and `1182192` are real ancestors, not new copies.
6. Stash apply restored tracked edits/new files but reported collisions where
   previously untracked foundation files had become tracked after fast-forward.
   Nothing was discarded: restored original bytes from the verified archive for
   every manifest path, then rehashed all 25 working files successfully. Thus
   03A.2 extensions to the foundation tests/models were not lost to collisions.

Backup location (local workspace only, deliberately not committed):
`/home/user/pwc-recovery-backup-20261024T061242Z/`
contains `project-files.tar`, `manifest.json`, status/refs and staged/unstaged
patches. The retained stash is labeled
`PWC-03A.2 independently backed-up recovery snapshot`.
All 25 original paths exist after reconciliation; none missing. A second archive
verification passed after review. No environments/databases or credentials were
added to Git. A newly installed ignored audit venv is not part of the recovery.

The approved ADR, custom User source, foundation migration 0003 and initial
migrations 0001/0002 remain byte-identical to `1182192`. ADR SHA-256:
`bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
The new commit contains the delta from that foundation, not duplicate foundation
work. The original 03A.2 runbook's 85-test result is labeled historical.

## Findings and scoped fixes

No Critical or High exploit was confirmed in this review. This is not evidence
that none can exist. Regression tests were added BEFORE correction and reproduced
failures/errors on the recovered code, then passed after fixes.

| Severity / ID | Finding | Correction and evidence |
|---|---|---|
| Medium M1 | Cleanup/removal between initial selector lookup and lock could raise DoesNotExist, producing 500 instead of uniform invalid/accepted responses. Reset request could also fail if its candidate contact disappeared. | Lock/re-read with optional selectors; missing confirm is CHALLENGE_INVALID, resend remains accepted, and missing/ineligible reset ownership is inert/null. Tests simulate removal at lock boundary for registration/reset/resend/contact lookup. |
| Medium M2 | Abuse bucket get_or_create read was separated from its locking read, leaving a deletion gap against expired-window cleanup. | select_for_update().get_or_create performs the initial read under lock in the same counter transaction; existing concurrency tests plus an assertion on the lookup's actual ORM lock flag cover this contract. |
| Medium M3 | Resend checked cooldown only before acquiring its flow lock. A delayed request could rotate again using a stale snapshot after another resend. | Recheck purpose, control, cooldown, terminal state and expiry on the locked flow. A lock-boundary competing-resend simulation asserts no new generation or intent. |
| Medium M4 | Notification retention could fill every cleanup batch slot with rows deliberately retained until a later deadline, starving expired secret payloads behind them. | Exclude reset-notice rows still within their own retention window from the due batch. Proof ciphertext was already erased atomically by confirmation. A limit=1 test retains the notification but disposes another expired flow/payload. |
| Medium M5 | Deeply nested JSON below the byte cap raised uncaught RecursionError and generated server errors. | Treat parser recursion as sanitized VALIDATION_ERROR with no state writes. A 4001-byte nested payload regression passes. This does not authorize accepting deep structures. |
| Medium M6 | Unsupported anomalous legacy addresses were skipped. For example, a trailing-dot legacy domain could cease reserving an ambiguous existing mailbox spelling, permitting duplicate personal identity creation (not takeover of its grants). | An unsupported anomaly now fails closed to an inert registration until reviewed inventory. Normal canonical alias checks and the 100-anomaly bound remain. No provider-equivalence mapping, merge or auto-verification was introduced. Regression asserts no eligible send for the trailing-dot case. |
| Low L1 | Link configuration accepted invalid ports, control characters, backslashes or invalid host syntax; malformed global budget types could give 500/429 rather than unavailable. | Validate exact ASCII HTTPS origin syntax/port with Django URLValidator plus path/credential/query/fragment checks; require a positive integer cap (not bool). Configuration-negative tests return 503 before counters/challenges. |

Eight new test methods (including multiple security-negative subcases) cover
these corrections in `accounts/test_recovery_review.py`. Deterministic
lock-boundary simulations are not mislabeled as real simultaneous executions;
the separate PostgreSQL concurrency suite does use independent connections.
No additional migration was needed for the corrections. Recovered migration
0004 remains the additive cooldown/audit-evidence migration, with its unused-only
reverse guard, unchanged by this review.

## Controls reviewed and retained

- **Enumeration:** uniform accepted envelopes and opaque independent secrets;
  inert placeholders follow the encrypted outbox path; no provider calls in
  HTTP. Invalid resends do not spend victim target budgets or change proofs.
  Eligibility is not returned. Timing paths still differ; see residual risks.
- **Challenges/atomicity:** original 30/15-minute deadlines, constant-time digest
  comparison, purpose/generation/ownership/epoch rechecks, five-failure flow
  retirement, proof-before-password validation and single-use consumption.
  PostgreSQL verified-contact uniqueness rolls back a losing registration User.
- **Reset:** User/contact/factor/session/flow lock order; one password mutation,
  epoch/recovery increment, challenge/assurance invalidation and session
  revocation in the same transaction. No automatic login, grant restoration,
  MFA removal or weakening review_required. Existing factor ownership, including
  enrollment session ownership, is checked without relying on full_clean().
- **Transport:** early cookie+Authorization rejection, no incidental-cookie
  subject selection, explicit anonymous browser CSRF and exact origin/HTTPS
  Referer, JSON-only native public proof ingress, no CORS enablement. This is NOT
  a native login/session ingress implementation.
- **Abuse:** PostgreSQL shared counters, stable lock order, canonical IPv6 and
  IPv4-mapped addresses, no trust in forwarded headers, bounded counts and no
  new target/flow bucket allocation after upstream limit denial. Global cap
  includes placeholders and failed target attempts; conservative availability
  tradeoffs require operational tuning, not a billing/deliverability promise.
- **Cryptography/outbox:** independent 256-bit random proof/control secrets,
  SHA-256 digests of high-entropy secrets and constant-time comparison;
  purpose-separated Django HMAC abuse keys; pinned Fernet with independent
  environment key ring/active ID, no plaintext fallback or DB key. Existing
  tamper, key-loss/rotation, timeout, retry, expiry and terminal erasure tests
  remain. No arbitrary SMTP selection through EMAIL_BACKEND.
- **Worker:** short skip-locked lease claim, no locks across I/O, current
  generation/expiry check, same-proof bounded retry, attempt fencing and stale
  acknowledgement rejection. Duplicate delivery remains possible and safe;
  there is no exactly-once email claim. A consumed reset's notification has no
  proof and cannot restore/reopen a challenge.
- **Exposure/ORM:** errors are bounded codes, adapter exceptions are not logged
  with secret-bearing bodies, and events have typed metadata, not arbitrary
  JSON. No raw proof/password goes into digests/events. Secret-bearing service
  locals are marked sensitive. Mail necessarily contains the proof, in fragment
  at configured HTTPS origin. Privileged raw SQL/unsafe internal ORM can bypass
  cross-row/append-only hygiene; neither DB tamper-proofing nor APM redaction
  outside this code is claimed.
- **Migration/legacy:** original UUIDs/passwords/relationships retained. Legacy
  email never authorizes reset or auto-merging. Fresh/upgrade/unused-reverse and
  used-schema refusal tests pass; 0004 refuses before dropping audit evidence.
  Recovery, review and routing do not add private NGO APIs or authority.

### Documented implementation variances / complexity

Small Django JSON adapters intentionally avoid implicit DRF SessionAuthentication
on public proof commands; they do not replace the Django/DRF stack. The original
runbook documents this choice and explicit CSRF tests cover it.

The ADR schema sketch calls flow controls "keyed", while its detailed §6 calls
for established digests and constant-time comparison of independent >=256-bit
secrets. This implementation uses SHA-256 for these random secrets, NOT for
passwords or low-entropy factors. No feasible offline guessing weakness was
confirmed for these entropy levels. This wording discrepancy should be clarified
in human slice review, not silently described as keyed hashing or resolved by
editing the approved ADR. Keyed abuse digests are separate.

The reset-family notification occupies generation N+1 of DeliveryIntent without
changing the proof generation. This avoids another table, but is an implicit
contract: keep the purpose/consumed/generation checks and dedicated tests when
future outbox changes occur. `DeliveryIntent.state` is authoritative for mail;
`AuthChallenge.delivery_state` is only a partial status mirror (sent/pending),
not a basis for ownership, proof validity, authentication or production alerting.
A full mail monitoring/status projection is low-priority operational debt.

## Current validation — not the historical report

Environment: **Python 3.11.2, PostgreSQL 16.2** (real disposable cluster via
`pgserver==0.1.4`, not SQLite). Application pins were installed from
`apps/backend/requirements.txt`; Black/pgserver are environment-only audit tools.
No real personal/NGO data or external email used.

| Execution | Result |
|---|---|
| Recovered code before fixes: full checks/migrations/tests | 85/85 tests passed in 26.652s |
| New regressions before fixes | 8 methods failed with 14 assertion failures and 6 errors across subcases; confirms defects, not a recovery success claim |
| New regressions after fixes | 8/8 passed in 1.058s |
| Final complete Django suite | **93/93 passed, 0 failures/errors**, 26.920s |
| Additional repeat of real PostgreSQL race suite | **8/8 passed**, 3.488s (subset of the 93, not 8 more unique tests) |
| Django system checks | zero issues |
| makemigrations --check --dry-run | no changes detected |
| migrate --plan / migrate --noinput / migrate --check | passed on a fresh PostgreSQL database |
| pip check | no broken requirements |
| git diff --check | passed |

Commands: `python manage.py check`, `makemigrations --check --dry-run`,
`migrate --plan`, `migrate --noinput`, `migrate --check`, `test --verbosity 2`.
The race repeat selected `AdditionalPostgresRaces`, `ConcurrentFlowTests`,
`ResendConfirmationRace` and foundation `ConcurrentConstraintTests`. The complete
suite includes migration compatibility/reversal and all existing org projection
tests. The existing CI discovers the new tests; no remote CI result is claimed.

Final synthetic HTTP samples (8/group), ms min/median/max: registration new
9.93/11.33/13.10; existing 9.02/10.36/12.42; reset eligible 12.32/14.79/18.48;
unknown 12.14/12.71/15.02. These small, local samples are NOT a statistical
non-enumeration certification; there is no claim of identical distributions.

Not performed: Python 3.12, Docker, live email, Flutter/web app runtime,
production infrastructure/load, external penetration test or dependency-CVE
audit. Full authentication/tenant isolation acceptance is not claimed.

## Remaining gates / readiness

- **Medium residual risk before live use:** account-dependent DB paths/locks can
  differ in timing. Target budgets and no synchronous provider calls mitigate
  but do not eliminate statistical enumeration. Production-distribution review
  and ingress/abuse tuning remain necessary; no cosmetic sleep was added as a
  false constant-time guarantee.
- **Availability/operations:** fixed-window bursts, shared-NAT fairness,
  attacker exhaustion of the conservative global cap, distributed source IPs,
  scheduler/cleanup monitoring and lease-timeout tuning require O2/O3 review.
  Unsupported/large legacy anomaly inventories intentionally keep registration
  inert; resolve through reviewed enrollment, not an unsafe first-match merge.
- **Unchanged O1–O6:** provider/sender, spend/scheduling, TLS/proxies/cookies/keys/
  backups, privacy/retention/notices, assisted recovery and deployment/real-data
  authorization remain open. SMTP and real-user collection are not enabled.
- **Later engineering:** MFA B2/B3, contact changes and hold clearance remain
  03A.4. Session issuance, online epoch/revocation validation, refresh, idle
  semantics, portal separation and client secure storage remain 03A.3/later.

Recommendation: recovered/stabilized 03A.2 is ready for human review and a
separately authorized 03A.3 assignment, contingent on its trusted synthetic portal
configuration and transport/session policy review. Never issue sessions that
ignore live reset epoch/revocation; MFA-enabled login must remain denied until
its required MFA implementation, not temporarily bypassed. This recovery task
stops without implementing 03A.3, MFA, authorization or UI. No PR or merge.
