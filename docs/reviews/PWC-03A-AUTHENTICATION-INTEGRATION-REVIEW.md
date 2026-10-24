# PWC-03A — Comprehensive Authentication Integration Review

Date: **2026-10-24**. Repository: `salmansabir33/pwc-platform`.
Feature: `arena/7bcc0d8b-pwc-platform`; target: `main`.
Reviewed checkpoint: `fea49b95dd601918a5140a48045b60c2c19a4b24`.

## 1. Executive summary and review boundary

**Verdict: READY FOR PR — bounded backend authentication foundation.**
One High, three Medium and one Low finding were corrected. No unresolved
Critical/High finding was identified in this engineering review; this is not a
claim that no unknown vulnerability exists. Fresh actual-PostgreSQL acceptance:
**247 passed, 0 failed**, including all 226 checkpoint tests and all eight original
public-foundation tests. Twenty-five concurrency cases passed three further runs.
Human review and green checks on the final PR are still required before merging.
No merge, production activation, real messaging, client UI or NGO authorization
is authorized by this verdict.

This review covers the approved PWC-02A ADR and implementations 03A.1–03A.4,
including interactions rather than only isolated services. It does not claim the
ADR's entire future route catalog is implemented. Password change/contact change,
assisted recovery and private tenant integrations remain absent, explicitly below.

Source hierarchy and reconciliation:
- Root `AGENTS.md`; Roadmap v2.0 §§1–3, gates and task contract; Strategic/Product
  Foundation §§1–4, privacy/release gates; Identity/Multi-NGO Foundation §§1–4,
  §12, security/API boundaries; Django/PostgreSQL Foundation's modular-monolith,
  service/transaction, UUID, tenant and audit requirements.
- `docs/decisions/ADR-0001-authentication-and-recovery.md`, particularly §§4–8,
  migration/rollback contract, AUTH threat matrix and operational gates. Approved
  ADR SHA256 remains
  `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`.
- All five existing 03A runbooks (including the separate .2 recovery review),
  session/MFA JSON fixtures and README, auth models/migrations/services/adapters,
  middleware, worker/cleanup commands, settings, requirements, CI and tests.

Planning documents retain their draft/provisional/open/deferred statuses. Neither
this review nor implementation approves governance, legal, finance or data policy.
Plain Django JSON adapters are a documented narrow choice for explicit anonymous
CSRF/transport enforcement; DRF/public directory and future authentication adapter
remain, not a replacement framework or permission system.

### Preservation and ancestry

The restored checkout initially had older `fc7056f` HEAD and surviving auth work.
Before Git state changes, 84 relevant files were independently copied/archived
with original paths/status and SHA256, plus patches, refs and history bundle, to
`/home/user/pwc03a-review-preservation-20261024T102039Z/`. Copies and archive members
were checksum-verified. An include-untracked preservation stash is retained.
After fetching both branches and verifying ancestry/remote checkpoint, only a
fast-forward reconciliation was used. All 84 files matched the verified checkpoint
exactly; no old stash/bulk archive was reapplied. No reset, clean, force push,
history rewrite, branch switch or fabricated historical commit was used.

The explicit current-task branch supersedes AGENTS' original session-branch pin.
Fetched base `fc7056f0486ae4644d7143943874f0a1bd6a4204` to checkpoint initially
comprised 43 files, +12,404/-22 lines. Existing lineage is preserved:
`79a1bd2` ADR → `1182192` foundation → `af40ebe` registration/recovery →
`26b0ad3` sessions → `fea49b9` MFA. Review corrections are a subsequent commit,
not replacement implementations. Backups/stash remain outside the PR.

## 2. Architecture and security-boundary assessment

- **Identity:** existing UUID `accounts.User`, password hashes, usernames and NGO
  FKs remain. Only a verified active primary UserContact grants public email-login
  eligibility. Legacy `User.email`, staff/superuser, names and imports are not
  ownership verification or relationship transfer mechanisms. Canonicalization is
  bounded ASCII local-part plus explicit IDNA2008/UTS46 domain handling, without
  dot/plus stripping; ambiguous legacy reservations fail closed pending inventory.
- **Services/transactions:** request adapters bound and validate JSON, explicitly
  select transport and call account services. Ownership is checked without relying
  on `full_clean()`. PostgreSQL constraints complement, not replace, cross-row
  checks. User serialization precedes contact/factor/session/flow/intent/credential
  mutation; delivery claims do not retain locks across external I/O. Shared abuse
  counters use their own bounded committed transactions before account mutations.
- **Web:** DB sessions, exact server-configured HTTPS portals, anonymous unsafe
  CSRF plus exact origin, Secure/HttpOnly/host-only cookies, no cookie/bearer fallback.
  Login rotates cookie/CSRF. Successful step-up/hold clearance now rotates them too,
  atomically updating registry mapping while keeping the logical session UUID.
  Failed rotation restores the request store as well as rolling back DB state.
- **Native:** opaque selector + 256-bit secrets; only digests persisted. Five-minute
  access; single-use rotating refresh families; replay revokes that family, not
  independent sessions. No cookie issuance or browser-provenance native login.
- **Online authority:** live active contact/account, epoch, session, expiry, factor
  revision and transport are rechecked. Original access/idle/absolute cutoffs bound
  sensitive MFA/device actions through their final savepoint gate. Suspension,
  reset, factor changes and global logout revoke as documented. GET/poll/refresh
  cannot manufacture interactive idle renewal.
- **MFA:** pinned PyOTP and cryptography; owner/factor/purpose-bound encrypted
  secrets and independent external HMAC keys. Monotonic locked timestep acceptance,
  ±1 step, bounded attempts. Correct password alone returns 202 preauth, never full
  credentials. Recovery codes are atomically consumed and preserve TOTP while
  advancing epoch/recovery generation and imposing `review_required`.
- **Assurance:** ≤5-minute single-use exact-user/session/epoch/generation/context/
  operation/target/command proofs. Ordinary same-session recent TOTP is allowed;
  hold clearance specifically requires a new code from the captured pre-hold
  revision. It never clears `review_required`, restores grants or enrolls around
  a lost factor. Only registered personal operations exist; unknown NGO/platform/
  finance operations fail closed, even for staff/superusers.
- **Delivery/evidence:** encrypted PostgreSQL outbox, bounded leases/retries,
  generation/attempt fencing and terminal payload erasure. Timeout can duplicate
  the same proof; delayed stale mail cannot resurrect proof authority. Adapter is
  hardwired synthetic locmem, not configurable live SMTP. Audit events contain
  bounded codes/snapshots, not secret request bodies. Application append-only
  guards are not database-level immutability or a complete retention program.

No new queue, identity store, permission shortcut, domain role registry, RLS,
production adapter or NGO-private endpoint was introduced. Future DRF consumers
must use online personal authentication **and independent transactional domain
permission checks**, not authorize writes solely from an earlier request.user.

## 3. Workflow and integration acceptance matrix

| Workflow | Combined evidence / observed result | Scope limit |
|---|---|---|
| Email request → worker → explicit confirmation | New journeys start via API, synthetic mail fragment and confirmation; no User before proof, no login/grants after confirmation | No real provider/client link handling |
| Normalization, duplicates, unverified/retired contact | Existing profile/legacy/contact-binding/unique-race tests pass; duplicate losing User creation rolls back | Real legacy inventory/enrollment not approved |
| Password policy/reset | 15–128 code points, common/similarity validation, old hashes preserved; API reset changes hash, advances epoch and revokes web/access/refresh | Password-change route absent |
| Browser login/session/logout/CSRF | Existing browser, middleware/async bridge and transport tests; new rotated-cookie/proof/CSRF checks and failure rollback | No physical browser/TLS ingress acceptance |
| Native login/refresh/device families | Actual API journey rotates pair; consumed refresh replay invalidates descendant but not another family | Strict lost-response re-login, no grace |
| Enrollment → activation → MFA login | Existing activation/key/replay tests and journey: other sessions revoked, confirming session promoted; valid password yields preauth only | Domain retention/action matrix pending |
| Recovery-code login → password reset | New journey retains factor and `review_required`, revokes recovered session; code not a hold-clear credential | No lost-all-factors assisted recovery |
| Reset with MFA → fresh login | Valid web MFA session and promoted mobile session exist before reset; both then fail, old refresh fails, new password still requires MFA | Non-MFA reset cannot self-clear without pre-hold factor |
| Restricted hold clearance | New regressions reject empty code on both paths, even after MFA login; new timestep clears eligible hold and rotates web cookie | Only same pre-hold revision; no review-required clearance |
| Step-up → exact personal mutation | New web proof survives logical-session-preserving rotation; old cookie fails; existing cross-user/session/action/scope/replay tests pass | Authentication/assurance is not domain authorization |
| Epoch/suspension/revocation | New registration-to-suspension journey rejects web, bearer, refresh and login; existing reset/login/refresh races pass | No private endpoint revocation claim |
| Worker failures/cleanup/rate controls | Existing stale-worker, concurrent claim, retry/tamper/key-loss, TTL and shared-budget tests pass | Production observability/retention absent |
| Method/envelope contract | New test covers all 25 registered auth patterns: 405, explicit Allow, no-store and error code | Framework/ingress failures outside adapters can differ |
| Tenant/import independence | Auth journeys create no OrganizationAccess; nonpersonal/staff shortcuts denied; original eight directory tests unchanged | No import/claim/private finance endpoints exist to exercise |

## 4. Classified findings and corrections

Severity is assessed within the disabled-by-default synthetic foundation; latent
credential confidentiality defects are still treated seriously.

| ID / severity | Confirmed defect and impact | Fix and regression |
|---|---|---|
| H1 — High, resolved | Public registration/reset POSTs lacked the TLS gate present on session/MFA routes. With activation and reachable HTTP ingress they could process password/proof/control bodies in plaintext. This was not a claim that public deployment was enabled. | Reject HTTP before body/workflow/counter processing; ignore spoofed forwarded-proto as shipped; reject unapproved proxy-trust configuration. New tests cover six routes, valid request shape, no side effects and three proxy settings. Existing helpers/parser regression explicitly use HTTPS. Edge TLS remains mandatory: the server cannot undo a secret already sent over HTTP. |
| M1 — Medium, resolved | Successful web step-up retained the cookie key, contrary to ADR §5, allowing copied prior cookies to remain mapped across assurance elevation. | Rotate Django key/registry mapping and CSRF on successful web step-up/clearance; stable logical session preserves exact proof. Tests cover old-cookie denial, proof usability, failed-password no-rotation, expiry rollback, DB-failure request-store restoration, clear-hold rotation and competing/reset races. |
| M2 — Medium, resolved | Hold-clear called generic step-up, which accepted an empty totp_code using recent TOTP. It could issue a clearance proof or clear the hold without the fresh single-use code required by ADR §8. | Hold-clear intents reject empty codes with audited 403; step-up omission also returns 403, while a missing required clearance field is schema-invalid 400. Generic recent-TOTP behavior elsewhere is unchanged. Reproduced 200/204 before correction; tests now require 403 and successful clearance only with a later valid code. |
| M3 — Medium, resolved | Reversing 0005 alone dropped used preauth client/factor/device metadata, bypassing the older broader rollback guards in 0004/0003. | New additive 0006 refuses reverse when preauth rows or 0005 metadata exist, before columns drop. Historical five-migration reversal reproduced this loss on disposable PostgreSQL. Used/unused guard and full-chain legacy-preservation regressions pass. Existing migrations remain byte-identical. |
| L1 — Low, resolved | Public/bootstrap 405 responses lacked required Allow headers, unlike session/MFA adapters. | Explicit POST/GET Allow; all 25 auth route patterns tested. No methods enabled. |

The first pre-fix six-case regression run had five failures and one pass, covering
H1/M1/M2 and the missing rotation path. Later implementation checks caught and
corrected the rolled-back-request-store edge. One intermediate full run was
242/243: the old deep-JSON test still used HTTP and hit the new TLS gate. Its
request now uses HTTPS, preserving its original parser/error/no-state assertions;
final acceptance below supersedes that run. No tests were removed or skipped.

## 5. Executed validation and evidence

Local environment: **Python 3.11.2, PostgreSQL 16.2**, disposable real clusters
via environment-only `pgserver==0.1.4`; no SQLite substitute. App requirements:
Django 5.2.18, DRF 3.18.3, psycopg 3.3.6, cryptography 50.0.2, PyOTP 2.10.0,
IDNA 3.20 and the committed transitive pins. No runtime dependency changed here.

| Check | Result |
|---|---|
| Fresh checkpoint baseline | 226/226, 193.241s |
| Final whole backend suite | **247/247, 229.497s**, 0 failures/errors/skips |
| Additional concurrency acceptance | **25/25 × 3**, 26.512s / 26.866s / 26.642s |
| `pip check` | No broken requirements |
| `manage.py check` | No issues |
| `makemigrations --check --dry-run` | No changes detected |
| `migrate --plan`, `migrate --noinput`, `migrate --check` | Ordered full-chain apply and applied-state checks passed |
| Migration/ADR/original-test integrity | 0001–0005 and original eight tests unchanged; ADR SHA256 unchanged |

Commands from an environment configured per LOCAL-SETUP, in `apps/backend`:
`python manage.py check`; `python manage.py makemigrations --check --dry-run`;
`python manage.py migrate --plan`; `python manage.py migrate --noinput`;
`python manage.py migrate --check`; `python manage.py test --verbosity 2`.
Scoped Black checks are a local development check, not a newly claimed CI lint
policy. Git diff/JSON/static secret-pattern inspection supplements tests; it is
not a secret-scanner certification or CVE audit.

Sandbox-only evidence (not required for reviewers to reproduce from the repo):
`/home/user/pwc03a-review-baseline.log`, `pwc03a-review-final.log`,
`pwc03a-review-races-{1,2,3}.log`, `pwc03a-review-reproductions.log`,
`pwc03a-review-historical-rollback.log`; fresh harness
`/home/user/pwc03a-review-validate.py`. Reproducible test cases are committed.
Remote final-head Python 3.11/3.12 CI is a separate PR gate; the PR's live checks,
not these local timings or earlier checkpoint green runs, are authoritative.
No local Python 3.12, Docker, physical browser/device, live SMTP, production,
external penetration test or vulnerability-database audit result is claimed.

## 6. Migration and legacy-data review

0001 custom User → 0002 compatibility options → 0003 security tables/defaults/
constraints → 0004 cooldown/transition evidence → 0005 preauth binding → new
**0006 reverse guard**. New 0006 is a reversible-on-unused-state RunPython guard,
not a schema/data backfill or secret migration. It depends on 0005 and writes no
application rows on forward application. Apply the entire chain before activation.

Fresh apply passes. Existing constraint/index/foreign-key tests and migration
suite pass. New full-chain tests seed blank, duplicate/case-variant, IDNA,
whitespace and trailing-dot legacy emails, old short password hash and NGO grant;
upgrade to 0006, unused reverse to 0002 and reapply preserve exact UUID/hash/email/
NGO FK values and do not manufacture verified contacts, sessions or grants.
There is no automatic legacy normalization, verification, user merge or bulk
suspension. Inventory anomalies and reviewed ownership enrollment before cutover.

0003/0004 refuse destructive rollback of used security schema/evidence or changed
epochs. 0006 protects used 0005 metadata, including consumed/expired preauth rows.
Do not delete evidence to bypass guards. Real rollback requires endpoint disable,
worker drain, revocation, evidence preservation, tested backup/restore or reviewed
forward fix; app rollback must not resurrect username/unverified-email fallback.
This explicit limited reversibility is not a promise of safe production downgrade.

## 7. API contract and frontend readiness

Actual prefix `/api/v1/auth/`; exactly 25 registered patterns. P = public proof,
W = browser issuance, M = native issuance, X = exactly one protected cookie/Bearer.
All mutations require HTTPS; W and unsafe cookie X require explicit CSRF/origin.
P ignores incidental cookie identity, but still enforces browser CSRF and rejects
Authorization/mixed credentials. Native issuance rejects cookies/browser provenance.

| Method / path | Mode; request summary | Success |
|---|---|---|
| GET csrf/ | Bootstrap, no bearer | 200 masked csrf_token, no personal data |
| POST registration/request/, password-reset/request/ | P; email | 202 accepted + flow_id/control/expires_in |
| POST registration/resend/, password-reset/resend/ | P; flow_id/control | Generic 202 accepted |
| POST registration/confirm/ | P; flow_id/proof/password | 201 verified; no login |
| POST password-reset/confirm/ | P; flow_id/proof/new_password | 204, no login |
| POST web/login/, mobile/login/ | W/M; email/password, optional device_label | 200 session or 202 MFA preauth |
| POST web/mfa/confirm/, mobile/mfa/confirm/ | Matching web/native preauth; challenge_id/control/method/code | 200 corresponding session |
| POST mobile/refresh/ | M body refresh_token only | 200 rotated pair/session |
| GET me/, sessions/ | X | 200 minimal own profile/session or own list |
| POST logout/ | X; empty body/object | 204 current session revoked |
| POST logout-all/ | X; exact-operation assurance_proof | 204 all sessions revoked |
| DELETE sessions/{id}/ | X; target-bound assurance_proof | 204 owned target only |
| GET mfa/status/ | X | 200 enabled/pending/hold state |
| POST mfa/enrollment/request/ | X; enrollment assurance_proof | 201 one-time secret/URI/id/expiry |
| POST mfa/enrollment/confirm/ | X; enrollment_id/code | 200 active + one-time recovery_codes |
| POST mfa/remove/ | X; removal assurance_proof | 204; sessions revoked |
| POST mfa/recovery-codes/rotate/ | X; rotation assurance_proof | 200 one-time codes |
| POST assurance/intents/ | X; registered operation/personal context/exact command; limited optional target | 201 id/expiry/required_methods |
| POST step-up/ | X; intent_id/password/totp_code when required | 200 proof/expiry, rotated web cookie/CSRF |
| POST recovery-hold/clear/ | X; clear intent_id/password/new pre-hold totp_code | 204, rotated web cookie/CSRF |

Handled errors use `{error:{code,message,field_errors,request_id}}`, no-store and
no-referrer. Checked statuses include 400 validation/challenge/transport/mixed,
401 generic credentials/session, 403 CSRF/MFA/step-up/hold, owned 409 replay,
foreign target 404, bounded 429 + Retry-After and unavailable 503. Method/mixed/
syntax checks can precede configuration checks: disabled does not mean every
malformed request returns 503. Framework/host/proxy-wide failures and unregistered
routes are not promised this adapter envelope. Ordinary payloads expose no grants,
precise IP/location, contact lists, factor ciphertext or private NGO/finance data.

**Not frontend-complete:** session/MFA fixtures check wire keys but are not a
full generated/approved OpenAPI contract. Registration/reset lack a JSON fixture;
there is no generated client, secure-store implementation, verified app-link/
fragment-scrub flow, recovery UX, cookie-rotation/concurrent-command acceptance,
real-browser CSRF/CORS deployment acceptance or supported-runtime UI validation.
The historical .3 fixture describes MFA-disabled denials; enabled accounts use
.4 preauth/assurance behavior. The updated MFA fixture makes fresh-code clearance
and web rotation explicit. Serialize browser security commands/re-bootstrap CSRF;
lost refresh response means clear local secrets and log in again, never replay.

ADR target `password/change/` and `contact-change/{request,confirm}/` are absent
(404), not stubbed enabled workflows. Public assisted/lost-all-factor recovery,
SSO, passkeys, phone OTP, user-import/claim and NGO representative/finance routes
are absent. Do not advertise complete ADR/client readiness or build screens from
illustrative target routes. These omissions are follow-on work, not permission to
silently add product features in this review.

## 8. Residual risks and limitations

- Rate budgets, database rows/locks and password hashing still need adversarial
  load testing, global ingress/CPU controls and monitored tuning. REMOTE_ADDR is
  authoritative; deployed proxy topology is unapproved. Shared-IP availability,
  target-budget denial and bounded legacy quarantine are deliberate conservative
  tradeoffs, not solved distributed-DoS protection.
- Generic envelopes are tested; different eligible/inert database/mail paths still
  have timing differences. Synthetic eight-sample timing output is not production
  enumeration resistance certification. No guarantee against all side channels.
- Key stores, old-key retention/rotation, key loss, process memory, APM/body/email
  redaction, host hardening, mail deliverability and backup confidentiality are
  operational responsibilities. Missing keys fail closed, not assisted recovery.
- Auth flow cleanup is bounded synthetic TTL disposal. Preauth, factor history,
  sessions/credentials and append-only events do not have a complete approved
  lifecycle/purge implementation. Refresh replay evidence must survive its family
  lifetime. No cleanup cadence, immutable external audit or legal retention claim.
- An account reset without a pre-hold factor cannot enroll a new factor to clear
  its hold; review-required cannot self-clear. This is intentional safe denial,
  but requires honest UX and approved assisted-recovery procedures before pilot.
- PersonalAuthentication authenticates, not authorizes. Private query/object/file/
  export/job isolation and grant revocation are untested where endpoints do not
  exist. Original public-directory tests cannot establish full G1a tenant security.
- Dependency pins/install consistency pass; no external cryptographic audit,
  supply-chain attestation or live advisory-database assessment was performed.

These are explicit release/follow-on gates, not concealed claims that production
is ready or that all high-risk domain workflows exist.

## 9. Configuration, operational blockers and deployment steps

Default config and .env.example keep **flows, sessions and MFA off**, key material
empty and browser portal map empty. Flags are independent: disabling flows alone
is not an authentication-wide kill switch. CSRF bootstrap itself is public, not
a login credential. Active MFA accounts fail closed if its implementation flag is
off. Crypto is externally keyed with no SECRET_KEY/database/plaintext fallback.
No live provider can be enabled with EMAIL_BACKEND; delivery remains synthetic.

Before any controlled synthetic activation: isolated synthetic database/data,
apply through 0006, generate independent external keys without logging them,
configure exact HTTPS portals/hosts and reviewed direct-TLS test topology, run
checks/migrations/tests, exercise worker/cleanup within limits, plan lost-response
handling and disable/revoke/drain procedures. Ordinary runserver/Compose HTTP or
Arena's TLS-terminating preview is not an approved auth deployment; no insecure
proxy exception or bypass was added merely to display a preview.

Before a real-user pilot/production: ADR O2 delivery and sender/privacy decisions;
O3 TLS/proxy/origin/secret management, clock synchronization, monitoring/alerts,
incident response, redaction, backup/restore and key-loss drills; O4 consent/data
retention and cleanup ownership; O5 independently approved assisted recovery;
legacy inventory/enrollment; B3/02C independent privileged-action/tenant policy;
client contract/runtime/secure-store/app-link/browser acceptance; maintained
vulnerability/dependency review, load/security review and explicit operational/
privacy/legal/product approval. Test success is not authorization for those gates.
Never restore a legacy login backend or delete security state as rollback.

## 10. Readiness verdict and handoff

| Level | Decision |
|---|---|
| Review PR | **READY FOR PR**; resolved H1/M1/M2/M3/L1, full PostgreSQL/race evidence, migrations and limits documented |
| Human merge | Eligible for review of this bounded foundation; requires final-head CI green and human diff/security/migration acceptance; never automatic |
| Controlled synthetic development | Conditional on isolated data, explicit keys/flags, full migrations and supported secure request topology |
| Real-user pilot | **BLOCKED** pending operational/privacy/recovery/client approvals and applicable domain policy |
| Production | **BLOCKED**; no deployment/monitoring/legal/security certification or authorization |

Open one PR to main titled **PWC-03A — Backend Authentication Foundation
(Registration, Sessions, MFA)** from the fixed session branch; preserve the original
five commits and review corrections. The PR should carry final commit/check links
and deployment gates. Do not merge it automatically.

After human acceptance, recommend **PWC-02C tenant authorization ADR** before any
PWC-03B context/grant/capability implementation; coordinate PWC-03C contract work
and PWC-02D web decision before client delivery. Auth alone does not complete G1a
or authorize NGO-private/finance/commitment features. Stop at this review and PR.
