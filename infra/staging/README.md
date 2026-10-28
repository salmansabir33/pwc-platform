# PWC-04C — disabled-service staging infrastructure

This is an **implementation foundation, not a deployed or accepted environment**.
The root `compose.yaml` remains local-development-only. Never use its runserver,
published PostgreSQL or plaintext ingress for staging/authentication.

## Acceptance and non-goals

| Category | What this change can establish | Authorization |
| --- | --- | --- |
| **A — built/tested infrastructure** | Offline configuration tests and hosted disposable Compose/TLS/PostgreSQL smoke + image scans, on the exact reviewed commit. Consult the PR checks/artifact, not this document, for execution results. | Synthetic automated evidence only |
| **B — actual staging deployment** | Owner applies reviewed artifacts on an identified staging host, records DNS, image/config SHAs, migrations, backup and restore rehearsal. | **Not performed by this change** |
| **C — independent actual-host acceptance** | Independent reviewer accepts both real portal hosts against [web-auth baseline](../web-auth/README.md) and ADR-0003 §4, including real browsers and negative ingress/PKI tests. | **Not established by A or B** |
| **D — credential transport authorization** | Explicit separate owner/security authorization for an exact environment/version with independently accepted actual-host evidence and all independent runtime gates satisfied. | **Not authorized**; C alone is insufficient |

No email/provider integration, public intake, officer/reviewer provisioning,
synthetic authority, invitation activation, finance/support privileges or native
networking is introduced. No ordinary personal, staff/superuser, recovery or MFA
state confers NGO/officer authority. There is no activation option in this stack.
Do not modify the fail-closed staging parser or enable flags to perform acceptance.
The complete future live-auth exercise remains blocked pending its separately
reviewed runtime/enablement prerequisites; this stack can test disabled-service
transport and public projections without those powers.

## Architecture and trust boundaries

```
443 only -> HAProxy TCP/SNI gateway (no TLS termination)
            -> NGO Nginx TLS + NGO-only static build
            -> OPS Nginx TLS + OPS-only static build
                 -> verified, client-authenticated TLS :8443
                      -> Gunicorn TLS socket -> Django secure WSGI
                            -> verify-full TLS -> private PostgreSQL 16
```

* Exact distinct lowercase DNS names, canonical Host **without explicit port**,
  same SNI, HTTPS origins on 443, separate portal chains/keys/builds. Unknown SNI
  has no backend; Nginx rejects unknown/default SNI and sibling/port Host. HTTP/1.1
  only; duplicate Host and conflicting framing fail. Port 80 is not published:
  unsafe plaintext fails rather than redirecting submitted secrets.
* No forwarded-header trust. Nginx copies only explicitly listed browser headers
  (Origin/Referer/CSRF/Cookie/Authorization/Accept/Content-Type/Sec-Fetch-Site).
  `Forwarded` and all `X-Forwarded-*` are absent upstream. Gunicorn ignores
  forwarded metadata. Django retains `SECURE_PROXY_SSL_HEADER=None` and no
  forwarded Host/port. TLS is genuine at the application-serving socket.
* `routing`, `application`, `database` are internal Compose networks; only the
  TCP gateway joins the external-capable `public` network and publishes a port.
  DB and WSGI have no host port. Application ingress requires client CA-verified
  certificates; NGO/OPS/health use separate client keys. The host/Docker daemon
  and CA issuer remain trusted administrators, not isolated adversaries.
* Only DB has a persistent named volume. Processes are non-root except the
  official PostgreSQL initialization wrapper, which copies keys to a private
  tmpfs owned by postgres then drops privileges. All filesystems are read-only,
  capabilities dropped (minimal initialization exceptions only for DB), bounded
  processes/memory/log rotation, no Docker socket or host network in the stack.
* WSGI uses `pwc_app`: public organization/workspace + migration SELECT, abuse
  counter SELECT/INSERT/UPDATE, security-event INSERT/ID-return only. No account,
  session or authority writer. Separate owner role is mounted **only** in DB and
  maintenance services. No default privileges grant future tables. Migration
  profile must complete before app start; app restarts only check migrations.
* Host-only `__Host-pwc_session`, Secure/HttpOnly/Lax/Path=/ and Secure host-only
  CSRF/Lax/Path=/ stay unchanged; CSRF trusted origins remain empty. No credentialed
  CORS, remote assets or API caching. App/static responses get no-store/referrer,
  anti-framing/no-sniff/CSP and a deliberately short 300-second staging HSTS.
  No includeSubDomains/preload claim is made. Static fonts ship under existing
  self-hosted licenses. Actual enabled auth cookie/CSRF behavior needs C.

### Source address / abuse budgets (explicit limitation)

HAProxy TCP does **not** send PROXY protocol; Nginx sees gateway address. Django
sees the corresponding Nginx application's internal address. No client IP is
accepted from HTTP headers. Existing 30/900s public-directory counters therefore
apply to the **aggregate portal proxy**, not individual visitors. Hosted tests
exercise both thresholds and redacted audit insertion. No budget is relaxed.
Before C/D, the owner must accept measured aggregate/NAT/concurrency behavior and
review appropriate edge controls, or obtain a separate reviewed peer-authenticated
source propagation implementation. This foundation is not ready for public load.

## Owner inputs — required, never guess these

1. Identified staging host, Linux distribution/patch owner, Docker Engine + Compose
   V2 versions, CPU/RAM/disk capacity, firewall/network/IPv4/IPv6 rules, maintenance
   window, restricted SSH/admin access, approved image registry/architecture.
2. Two exact separately approved DNS names (NGO and OPS), DNS ownership/A/AAAA and
   externally reachable 443 validation. No default public domains are supplied.
   Firewall permits 443 only for application ingress, restricted admin as approved;
   explicitly deny DB/WSGI/HTTP ports, including Docker-published-port bypasses of
   host firewall tooling. Do not expose Docker daemon remotely.
3. Approved digest-pinned base images: Python 3.12 slim Debian, Node 22.22.3
   bookworm-slim (npm 10), maintained stable Nginx/HAProxy 3.2 Debian Trixie,
   PostgreSQL **16 Trixie**. Retired Bookworm portal/gateway tags must not be used. Digest pinning does not prove an image is safe:
   record provenance/SBOM, scan every resulting image and approve findings.
   Renderer checks immutable reference syntax, not publisher trust/version.
4. Deployment-owned external secret/PKI directory, issuance/renewal/rotation owner,
   public certificate issuer, separate application/database server CAs and proxy
   client CA, off-host encrypted backup destination/encryption keys, RPO/RTO and
   restore reviewer. Do not share secrets or private evidence through chat/Git.
5. Exact release Git SHA, release/review owners, independently accepted host
   evidence and separate transport/runtime authorization decisions (C/D). No real
   NGO/member/beneficiary data or real user credentials are permitted for A/B.

## Host prerequisites and reproducible build/install

Commands below run **only on the owner-approved staging host**, not an arbitrary
machine. Shell variables name local paths; values must be supplied by its owner.
Use an immutable reviewed checkout, not a writable development worktree.

1. Install the vendor-supported Docker Engine and Compose V2 plugin for the
   approved OS, Git, Python 3.11+ and OpenSSL. Record package versions and security
   patch level; do not use an unaudited curl-to-shell installer. Docker access is
   root-equivalent. Container images supply Python/Node/PG dependencies. No host
   pip/npm install is required by the standard-library renderer.
2. Fetch and check out the reviewed release on the deployment machine; verify its
   signature/review/provenance. For this coding session the Arena branch is fixed;
   these are **host deployment** instructions, not branch-switching instructions
   for the agent. Retain prior checked-out release directories for rollback.
3. Copy `config.example.json` outside the checkout. Every placeholder deliberately
   fails validation. Supply fields exactly; unknown/duplicate JSON keys fail.
   `release` must be the checkout's 40-hex commit; `project` is a stable staging
   project name. Keep project/network/volume identity stable across releases.
4. Populate each `files` entry with an absolute path **outside Git/build context**.
   No `$`, colon or newline path interpolation. Password/key mounts must be mode
   0600 owned by UID10001, or 0640 owned by root/UID10001 and group10001. Files must
   not be symlinks. Parent directories must be deployment-admin controlled and
   traversable by the Docker daemon, never a public shared folder. Named Compose
   secrets use bind files: Compose does NOT fix host file UID/GID/mode for you.
   Certs/CA files contain no private keys and may be 0644; all CA private keys
   remain with the issuer, never mounted into any service.
5. Generate unique high-entropy values with the approved secret manager: Django
   secret >=50 characters; owner/app DB passwords and `abuse_key` >=32 printable
   non-space characters, each >=12 distinct characters. Example local entropy
   source is `openssl rand -hex 48 > "$managed_file"` under `umask 077`, followed
   by controlled ownership/mode assignment. Never echo/read them into terminal,
   command arguments or `.env`. Renderer rejects known development placeholders,
   weak shapes, duplicates and unsuitable permissions; this is not entropy proof.

```sh
# Set these locally to owner-chosen absolute paths, outside the checkout.
export STAGING_CONFIG=/absolute/managed/config.json
export STAGING_RENDER=/absolute/managed/rendered-release
python3 infra/staging/deploy.py --config "$STAGING_CONFIG" --check
python3 infra/staging/deploy.py --config "$STAGING_CONFIG" --output "$STAGING_RENDER"
# Generated compose contains paths/origins but no secret values. Keep it private.
docker compose --env-file /dev/null -f "$STAGING_RENDER/compose.json" config --quiet
infra/staging/stack.sh "$STAGING_RENDER/compose.json" build
# Scan/approve built app/NGO/OPS images AND gateway/PG digests before starting.
infra/staging/stack.sh "$STAGING_RENDER/compose.json" up
infra/staging/stack.sh "$STAGING_RENDER/compose.json" status
```

Render output must be a **new/empty directory**; existing nonempty output is
never overwritten. Use a new immutable render directory for every release/config
change, so Compose recreates services against changed bind mount sources. `--check`
validates without writing and can be repeated safely.

`up`: DB healthy -> one-shot owner migrations/grants -> app genuine mTLS/DB health
-> distinct portals -> gateway. Any error stops the script. It is idempotent but
not an atomic rolling deployment: stop request producers and back up before a
release with migrations. `restart` never applies migrations. Readiness failures
remain unhealthy (Docker restart policy handles **process exits**, not unhealthy
status); monitor and alert on both. A supervisor/operator may restart after cause
review, not loop away certificate or migration errors. `stop` retains the volume;
never use `down --volumes` on a deployed environment.

Do not run arbitrary Compose overrides, inherited `.env`, `runserver`, publish DB,
turn debug/service flags on, `--insecure`/`verify-ca` downgrade, or add proxy trust.
The helper uses `--env-file /dev/null`; no environment enables services. The
`--synthetic` renderer option permits reserved fixture hosts only for isolated A
work and confers **no** B/C/D acceptance. Never use it on an actual staging host.

## PKI provisioning, DNS validation and renewal

Use the approved issuer/secret manager, not the disposable test PKI generator.
All leaf certs/keys must match, use distinct keys and have >7 days remaining.
Server certificates require exactly their listed DNS SAN, not a wildcard/shared
SAN certificate. CA bundles must be distinct and public cert/CA files must not
contain private key material. Renderer uses OpenSSL
chain/purpose/hostname checks and rejects invalid/untrusted chains/keys.

| Files | Required identity / purpose |
| --- | --- |
| `ngo_cert`/`ngo_key`, `ops_cert`/`ops_key`, `public_ca` | Separate full leaf+intermediate chains and keys; exact respective DNS SAN; serverAuth; publicly trusted root bundle for independent clients |
| `app_cert`/`app_key`, `app_ca` | Private serverAuth SAN `app.pwc.internal`; Gunicorn presents full chain |
| `db_cert`/`db_key`, `db_ca` | Private serverAuth SAN `db.pwc.internal`; PostgreSQL presents full chain |
| `ngo_client_cert/key`, `ops_client_cert/key`, `health_cert/key`, `client_ca` | Three unique clientAuth leaf/key pairs; CA restricted to controlled proxies/health peer |

These two `.internal` names are **private network identities**, never invented
public DNS names. Use distinct leaf keys and CAs as listed; never mount issuer
private keys. Restrict CA issuance, file administration and Docker peer membership.
Certificate validity does not establish DNS ownership or reviewer acceptance.

Prefer automated **DNS-01** issuance under owner-controlled DNS: port 80 is closed.
Issuer adapter/credentials remain outside this repo; supply only resulting files.
Validate both public A/AAAA records from an independent network and confirm they
resolve only to the approved staging addresses; test all advertised addresses.
Then use the noncredentialed observer exactly as documented in
[web-auth](../web-auth/README.md), recording its sanitized output privately. It is
not the browser/reviewer acceptance suite and cannot authorize credential transport.

Alert at 30/14/7-day expiry thresholds; renew before 14 days. Stage new complete
chains and keys in a versioned external directory, validate renderer to a **new**
output directory, back up, then recreate affected services with the newly rendered
manifest. For public cert changes recreate NGO/OPS, then gateway if needed; app/
client CA or leaf changes recreate app/NGO/OPS (staged dual-CA overlap, then retire
old CA); database CA/key changes restart DB/app/maintenance consumers in a planned
window. Bind mounts do not reliably see atomic host-file replacement: **recreate**,
not just reload, after rotating source paths. DB wrapper recopy happens on start.
Verify old cert rejection and new real-host chains from outside, app readiness,
both portals, and absence of alternate ingress. Do not silently reload bad certs
or use plaintext as a recovery path. DB password-file replacement does **not**
rotate an existing role password: a separately controlled owner session must
`ALTER ROLE` via private stdin/secret-manager tooling (never argv/history/logs),
coordinate consuming mounts/recreation and verify old password rejection.

## Backup, fresh restore and disaster rehearsal

Backups include potentially sensitive database state; stdout is **intentional
backup data**, never logs/artifacts. Use approved encryption on the host before
writing/off-host transport, restrictive umask, `set -o pipefail` in Bash, and
check **both** dump/encrypt/upload exits. Do not run with shell tracing.

```bash
set -euo pipefail
umask 077
# AGE_RECIPIENT is the owner's approved public encryption recipient, not supplied here.
infra/staging/stack.sh "$STAGING_RENDER/compose.json" backup |
  age -r "$AGE_RECIPIENT" > "$ENCRYPTED_BACKUP"
# Upload encrypted file with approved tooling; validate hash, off-host durability,
# retention/access controls and recovery-key availability separately.
```

Use `pg_dump` custom/no-owner/no-ACL with owner via verify-full TLS. Back up prior
to migrations, scheduled to the owner's RPO and before patch/rotation. Separately
escrow encrypted config/PKI/secret-manager recovery references, exact image digests,
Git SHA, Compose project/volume identifiers and compatible release—**not in Git**.

Restore first on a separate approved isolated rehearsal host, **fresh** DB volume,
no real identity traffic, same project/config within that separate Docker host.
Start only DB (`docker compose ... up -d --wait db`), which initializes owner/app
roles. Do **not** run migrations before restoring the schema dump. Stop all app/
portal/gateway services. Have owner confirm DB is fresh, then:

```bash
set -euo pipefail
age --decrypt -i "$OFFLINE_IDENTITY_FILE" "$ENCRYPTED_BACKUP" |
  PWC_CONFIRM_FRESH_RESTORE=YES infra/staging/stack.sh "$STAGING_RENDER/compose.json" restore
infra/staging/stack.sh "$STAGING_RENDER/compose.json" up
```

`restore` enforces an explicit confirmation and stops producers, not automatic
freshness detection. Never use it against a populated/live DB. It restores in one
transaction, then `up` runs migrations/reapplies bounded grants. Verify migration
history/counts, public-only synthetic fixtures, restricted app privileges, both
TLS hosts, RPO/RTO and a new backup. Record reviewer/date/hash of the encrypted
backup and sanitized outcomes; not data or proof material. CI rehearses a fresh
schema restore on disposable data only; this does not prove off-host recovery.

## Health, diagnostics, rollback and patching

* `stack.sh ... status` and `docker compose ... ps --format json` expose readiness.
  App health checks DB TLS + actual authenticated TLS health request with allowed
  public Host. Public `/api/v1/health/` is a process/transport signal, **not** DB or
  service authorization; inspect container readiness too. Portal health checks
  config + process; independent HTTPS probes must test the full user path.
* `stack.sh ... logs` is bounded and payload-free: Nginx access/error and Gunicorn
  request/error logging are disabled; Django uses NullHandler; PostgreSQL disables
  statements/errors below panic. The trade-off is limited diagnosis. No request
  bodies, URLs, cookies, Authorization, SQL details, auth proofs or environment
  dumps. Obtain only status/exit/health/release evidence. Review a separate
  privacy-safe observability design before actual credential traffic. Do not
  enable verbose logs to troubleshoot real credentials; reproduce on synthetic
  disposable data. Never upload `docker inspect`/raw logs/PKI/config/DB backups.
* Rollback: stop gateway/portals/app, retain DB and encrypted backup, select prior
  immutable checkout/render directory/images. Assess migration compatibility
  **before** starting prior code. Do not blindly reverse migrations. If incompatible,
  restore the tested pre-release backup into a fresh isolated volume/host under
  maintenance, validate, then switch approved DNS/routing. Keep failed volume
  isolated for owner-led recovery, never delete the only copy.
* Patch: track Debian/Python/Node/Nginx/HAProxy/PostgreSQL advisories; update approved
  base digests and hashed Python/npm locks through review. Scan fixable HIGH/CRITICAL
  as a release gate; record all unfixed findings and require explicit owner risk
  decisions. Rebuild immutable artifacts, repeat A tests, rehearse backup/restore,
  deploy during window, repeat B/C evidence as applicable. PG major upgrade needs
  a separately rehearsed migration; do not point a different major at the volume.

## Automated evidence

```
python3 -m unittest discover -s tests/deployment -v
# Real containers only on a disposable CI runner, root permission for secret GID:
sudo env PWC_DISPOSABLE_CI=YES python3 tests/deployment/compose_smoke.py
```

`.github/workflows/staging.yml` builds app + separate portal images from immutable
resolved base digests; uses ephemeral CAs/secrets outside checkout; tests real
TLS/WSGI, disabled gates, effective cookies/settings, private TLS DB, bounded role,
exact Host/SNI, forwarded spoofing/framing rejection, no plaintext ingress,
aggregate abuse thresholds, failed upstream verification/recovery, migrations,
fresh backup/restore and secret-free logs. It tears down **only its disposable**
volume and retains only sanitized A evidence and vulnerability reports. Runtime
image scanning uses a resolved scanner digest and records it. Existing backend,
frontend/direct-TLS browser and Flutter regressions remain independent gates.
A failed or unexecuted CI check is not acceptance. Never upload traces/HARs/cookies.
