# Initial public-directory deployment — one operator procedure

This procedure applies the reviewed implementation on the already-prepared Contabo
host. It does not repeat installation, public certificate issuance, runtime secret
creation or source-host inventory. It never authorizes itself. Run only after the
owner supplies exact host/change authority. Docker access is root-equivalent.
No real NGO records, fixtures, accounts or grants are created. All personal/private
service flags and opportunity publication remain closed in the existing renderer.

This workflow is for **initial deployment**. An already-healthy exact private bootstrap is a no-op; any other existing
project/container/DB volume blocks bootstrap/restore rather than automatically
migrating or overwriting it.
Partial failures preserve files, containers and volumes for operator-led recovery;
there is deliberately no automatic teardown, volume deletion, rollback, firewall,
DNS, shared-proxy edit or destructive retry. Healthy exact-stack exposure is a no-op.
PKI/config updates are idempotent for a completed generation; interrupted generations
are retained and require a new versioned directory. Old keys/configs remain intact.

## 1. Apply reviewed release and select private operator state

On the trusted SSH terminal, use the reviewed PR/merge commit, not an unreviewed
branch or the old `15c277a` code. Preserve the existing checkout and workloads;
follow the release-directory policy in README. Commands run from that clean
reviewed repository as the authorized owner of the private external directories
(normally root on this host). Do not use shell tracing.

```bash
set -euo pipefail
umask 077
CONFIG=/srv/projects/pwc/staging/secrets/config.json
# Owner-selected NEW private directory outside Git; do not reuse another release.
: "${STATE:?Set the absolute operator state directory for this release}"
test -d "$STATE" || mkdir -m 700 "$STATE"
sha256sum "$CONFIG"
```

## 2. Resolve, review and apply immutable image references

Supply `IMAGE_CANDIDATES_JSON` outside Git with exactly `python`, `node`, `nginx`,
`postgres`, `haproxy` mapped to owner-selected registry tags. Start from current
reviewed distro/version requirements in README, not an unreviewed `latest` tag.
Resolution pulls images but cannot apply them automatically:

```bash
python3 -m infra.staging.provision resolve-images \
  --candidates "$IMAGE_CANDIDATES_JSON" --output "$STATE/image-proposal.json"
# Owner reviews provenance, architecture, versions and exact repository@sha256 refs.
python3 -m infra.staging.provision apply-images --config "$CONFIG" \
  --reviewed-images "$STATE/image-proposal.json" \
  --approve-config-sha256 "$OWNER_APPROVED_CURRENT_CONFIG_SHA256"
```

`apply-images` rejects mutable references and sets `release` to this reviewed
checkout's exact HEAD. Other configuration fields/secrets stay intact. Use the new
current config hash for each approved mutation, not the hash from a prior step.

Image approval comes **before** client certificate completion. Only `apply-images`
may load the exact documented initial image placeholders; it validates every other
metadata field and all replacement references strictly. It deliberately does not
require the not-yet-issued client certificates. The configuration SHA changes after
image approval: obtain a **new owner approval** for that updated SHA before signing.
Do not reuse the pre-image SHA. Rendering still requires complete valid files and
immutable images and must fail until client completion succeeds.

## 3. Complete the client identities

Choose **one** issuer path below. Do not regenerate public/app/DB keys or four
application secrets. CSR/key matching, >7-day validity, chain/purpose and full
renderer validation occur before configuration changes. Client certificates made
by this tool have clientAuth-only EKU and exact SANs `ngo_client.pwc.internal`,
`ops_client.pwc.internal`, `health.pwc.internal`. CSR-requested extensions are not
copied. The dedicated issuer is trusted to issue only approved client identities.

- **Preferred: original approved issuer is external.** Send the two existing public
  CSRs through its authorized process; receive public signed leaves, not its key.
  Store a private JSON mapping `ngo_client` and `ops_client` to their absolute
  certificate paths outside Git. The existing health certificate/CA remain unchanged:

  ```bash
  python3 -m infra.staging.provision import-clients --config "$CONFIG" \
    --certificates "$RETURNED_CLIENT_CERTIFICATES_JSON" \
    --approve-config-sha256 "$OWNER_APPROVED_CURRENT_CONFIG_SHA256"
  ```

- **Approved original issuer key is available locally to its authorized custodian.**
  Supply its existing private path in a separate caller-owned 0700 issuer directory
  (key mode 0600); never copy it into runtime mounts or Git:

  ```bash
  python3 -m infra.staging.provision clients --config "$CONFIG" \
    --output "$STATE/client-generation" --ngo-csr "$NGO_CSR" --ops-csr "$OPS_CSR" \
    --issuer-key "$APPROVED_EXISTING_CLIENT_ISSUER_KEY" \
    --approve-config-sha256 "$OWNER_APPROVED_CURRENT_CONFIG_SHA256"
  ```

- **Original issuer unavailable: separately authorize replacement of client trust.**
  Record owner approval of new dedicated client CA custody/retention and reissuance
  of **all three** client leaves, including health. Set `APPROVED_NEW_CLIENT_ISSUER_KEY`
  to a nonexistent path in a separate existing private issuer directory. Then use
  the preceding command with that key and `--replace-client-ca`. This creates a
  3072-bit dedicated CA and stages three leaves using the existing private leaf
  keys. The new issuer key remains outside runtime mount sources. The config
  switches only after validation; public/app/DB CAs and original client files stay
  untouched. This is initial offline provisioning, **not live CA-rotation automation**.

Each mutation requires the exact current config hash approved by the operator,
uses a private advisory lock/CAS, and retains `config.json.before-<original-hash>`.
Do not auto-pipe a displayed digest into an approval argument. Hash confirmation
binds a change; it does not establish the operator's organizational authority.
On failure there is no config switch; preserve the generation for private diagnosis.
Existing configuration backups can contain sensitive paths: never upload them.

## 4. Render, approve build, build and scan

```bash
RENDER="$STATE/rendered"
python3 -m infra.staging.operate render --config "$CONFIG" --render "$RENDER"
python3 -m infra.staging.operate plan-build --config "$CONFIG" --render "$RENDER"
# Owner approves the displayed plan for building these images on this host.
python3 -m infra.staging.operate build --config "$CONFIG" --render "$RENDER" \
  --approve-plan-sha256 "$APPROVED_BUILD_PLAN"
python3 -m infra.staging.operate scan --config "$CONFIG" --render "$RENDER" \
  --reports "$STATE/scans" --scanner "$REVIEWED_TRIVY_REPOSITORY_AT_DIGEST"
python3 -m infra.staging.operate plan-bootstrap --config "$CONFIG" --render "$RENDER" \
  --reports "$STATE/scans"
```

The scanner mounts the Docker socket, so its exact digest needs approval too. The
existing staging CI pins a scanner reference; do not interpret that as host risk
acceptance. Five complete reports must identify the exact built image IDs. Any
fixable HIGH/CRITICAL finding blocks bootstrap/exposure; no override exists.
Every remaining unfixed HIGH/CRITICAL ID needs owner disposition in a private JSON
file with `plan_sha256`, named `reviewer`, and exact `accepted_unfixed_ids` list.
The CLI plan prints these IDs and their binding hash. `--risk-disposition` is needed
only if findings remain. For a later expose plan, obtain its own matching disposition.
Raw scanner reports/configs stay private; report sanitized IDs/counts only.

Approvals bind action, host machine ID, release, source cleanliness, config, all
mounted file hashes, rendered ingress and actual image IDs/scan reports. Drift
invalidates approval. Another operator must not mutate Docker tags/files during
these operations; host/root administrators remain a trust boundary. No tool here
creates independent legal/security acceptance by generating a receipt.

## 5. Approve private bootstrap; encrypted off-host backup

After explicit owner approval to initialize this **fresh** PWC project (no ingress):

```bash
python3 -m infra.staging.operate bootstrap --config "$CONFIG" --render "$RENDER" \
  --reports "$STATE/scans" --approve-plan-sha256 "$APPROVED_BOOTSTRAP_PLAN" \
  --risk-disposition "$BOOTSTRAP_RISK_DISPOSITION"
```

For no findings, omit `--risk-disposition`. This starts only private PostgreSQL,
uses the existing owner-only migration/grant service, then starts the app with its
bounded runtime role. DB TLS, migrations and application mTLS are checked by the
existing health commands. No portal/gateway/host port is started. No root development
Compose file or environment-file override is used. Docker explicitly selects the
local default context (never changes the saved context), and inherited COMPOSE_*
project/profile overrides cannot retarget another workload. A remote/rootless
Docker context is intentionally unsupported by this local-host workflow. An existing volume or unhealthy/different project is a hard stop, not permission
to drop it; an already-healthy exact private bootstrap is a no-op. Preserve partial state on error.

Install/review the age CLI on the authorized hosts. Owner provides a public native
age recipient, separate backup-host SSH account, pinned known_hosts file, private
remote directory, retention/access policy, RPO/RTO and recovery key custody. The
backup host must have Python >=3.11. Its destination directory must already be owned
by that account with mode 0700. No private age identity belongs in this repository.

```bash
python3 -m infra.staging.recovery export --config "$CONFIG" --render "$RENDER" \
  --recipient "$APPROVED_AGE_RECIPIENT" --backup "$STATE/initial.age" \
  --offhost "$APPROVED_BACKUP_USER_AT_HOST" --known-hosts "$PINNED_BACKUP_KNOWN_HOSTS" \
  --remote-path "$APPROVED_NEW_REMOTE_BACKUP_PATH" --receipt "$STATE/offhost.json"
```

The dump streams directly to age; only ciphertext reaches disk/SSH. Export enforces
host-key verification, exclusive creation, hash readback/fsync and a different
machine ID. It never overwrites a remote file. An interrupted copy can leave partial
ciphertext: preserve it and select a new approved remote path; do not overwrite it.
If SSH fails after encryption, `export-existing` with the same arguments except
`--recipient` exports the exact saved file using its source sidecar, never relabels
an older dump with a new release/config. Files and receipts must be retained together.
A successful SSH/fsync receipt is not proof of provider independence, retention,
backup scheduling or independent disaster acceptance. Record these separately.
Schedule the existing encrypted backup/export operation to the approved RPO after
initial deployment; scheduling credentials/retention settings are provider inputs,
not defaults supplied by this code. Do not auto-delete older backups.

## 6. Rehearse on a separate isolated restore host

Use a **third authorized machine**, distinct from source and backup storage. Supply
the same reviewed checkout and **exact five built image IDs** through the approved
registry/image transport (rebuilding apt layers may change IDs and is not equivalent).
The project tag names must still resolve to those IDs. Provision matching approved
private configuration/PKI there, render using `operate render`, and copy only the
encrypted backup and source receipt via approved transport. Never copy data/secrets
into CI artifacts. The restore host must have no existing project containers/volume.

```bash
# On that isolated host, with its own CONFIG/RENDER/private STATE paths:
python3 -m infra.staging.recovery plan-restore --config "$CONFIG" --render "$RENDER" \
  --backup "$RESTORE_CIPHERTEXT" --source-receipt "$SOURCE_OFFHOST_RECEIPT" \
  --receipt "$STATE/restore.json"
# Owner approves exact fresh-host restore; private identity supplied locally:
python3 -m infra.staging.recovery restore --config "$CONFIG" --render "$RENDER" \
  --backup "$RESTORE_CIPHERTEXT" --source-receipt "$SOURCE_OFFHOST_RECEIPT" \
  --identity "$APPROVED_PRIVATE_AGE_IDENTITY" --receipt "$STATE/restore.json" \
  --approve-plan-sha256 "$APPROVED_RESTORE_PLAN"
```

No ingress is started. It creates a fresh DB, pipes decryption into the existing
controlled restore service, checks both exits/timeouts, applies migration/grants
and verifies DB/app health. Plaintext is never a file. Copy the resulting nonsensitive
operational receipt back to source's private STATE using approved transport.
Record measured recovery time and owner RPO/RTO acceptance. No automated teardown is
performed: isolate/preserve the rehearsal until its owner authorizes cleanup.

## 7. Approve exposure, then independently verify

Back on Contabo, supply the genuine off-host/rehearsal receipts. The binding rejects
same-machine rehearsal, mismatched backups/config/source image IDs and stale scans.
Receipts are operator-controlled evidence, not digitally authenticated independent
acceptance: the owner must verify their origin before approving the plan.

```bash
python3 -m infra.staging.operate plan-expose --config "$CONFIG" --render "$RENDER" \
  --reports "$STATE/scans" --backup-receipt "$STATE/offhost.json" \
  --restore-receipt "$RESTORE_RECEIPT_ON_SOURCE"
# Owner approves exactly this PWC stack and public 443 publication/change window:
python3 -m infra.staging.operate expose --config "$CONFIG" --render "$RENDER" \
  --reports "$STATE/scans" --backup-receipt "$STATE/offhost.json" \
  --restore-receipt "$RESTORE_RECEIPT_ON_SOURCE" \
  --approve-plan-sha256 "$APPROVED_EXPOSE_PLAN" \
  --risk-disposition "$EXPOSE_RISK_DISPOSITION"
```

Omit risk option when no findings. Occupied ingress is not stopped/adopted; no
firewall/DNS edits happen. Closed provider/host firewall remains a separate exact
operator approval/action. Bootstrap does not rerun at exposure; no owner migrations
or unreviewed image build/pull occur. All five service health states and running
container image IDs are checked. The same healthy stack is a no-op on repetition.

On an authorized **outside-server** workstation with the reviewed repository and
Python standard library, no server secrets/config copy is needed:

```bash
python3 -m infra.staging.operate verify \
  --ngo-host ngo-staging.coventure.pk --ops-host ops-staging.coventure.pk
```

This verifies trusted TLS (no redirects/insecure fallback), both health endpoints,
empty credential-free directory envelope, nonexistent-detail 404 and opportunity
503. Unexpected populated data blocks this initial pilot; no records are seeded or
changed. An empty database cannot establish positive detail/filter/pagination/data
acceptance. The existing four-field serializer/contracts and automated isolation
suite remain unchanged. Run the independent host/browser ingress-negative suite
from README before recording host acceptance; the probe's output explicitly says
`acceptance: false`. Confirm existing unrelated applications remain healthy through
their owners, not by restarting/scanning them. No credential transport is authorized.

After verified reachability/owner approval, the Android public origin is
`https://ngo-staging.coventure.pk`, with `PWC_API_ORIGIN=`. Run pinned Flutter checks
and build/preserve a separately labeled live-directory APK per mobile runbook.
An empty live directory permits connectivity/navigation testing only; real NGO
publication and populated favorites tests require separate disclosure approval.

## Genuine remaining inputs

Authorized terminal/SSH execution; original issuer response or explicit replacement
client-CA authority/custody; exact image/scanner review and findings dispositions;
approved off-host SSH/storage recipient/retention and isolated restore host/private
recovery identity; approved deployment/443 change and external testing network.
These are not synthesized by CI and are the only reason to stop the corresponding
phase. No requirement to reinstall Docker, reissue valid public TLS or recreate
valid application secrets is introduced.

## Resume the reported initial bootstrap failure

No generation/key was created by the failed operation. Do not delete or recreate
existing secrets/certificates. Apply this reviewed fix to the source checkout first;
`apply-images` sets the config release to that exact new HEAD (not the old `15c277a`).
Use the authorized owner account and existing private STATE/CSR paths:

```bash
CONFIG=/srv/projects/pwc/staging/secrets/config.json
INITIAL_SHA=e949418b49b7b449077a32f9ccfb20cede79bf5a253cd97cd4f45c8fdd61d856
printf '%s  %s\n' "$INITIAL_SHA" "$CONFIG" | sha256sum --check -
# If this fails, stop: review the changed config rather than reusing old approval.
python3 -m infra.staging.provision resolve-images \
  --candidates "$IMAGE_CANDIDATES_JSON" --output "$NEW_IMAGE_PROPOSAL_JSON"
# Owner reviews these actual resolved references; no sample/fake digests on VPS.
python3 -m infra.staging.provision apply-images --config "$CONFIG" \
  --reviewed-images "$NEW_IMAGE_PROPOSAL_JSON" --approve-config-sha256 "$INITIAL_SHA"
sha256sum "$CONFIG"
# Obtain owner approval of THIS NEW hash for replacement client trust/custody.
python3 -m infra.staging.provision clients --config "$CONFIG" \
  --output "$STATE/client-generation" --ngo-csr "$NGO_CSR" --ops-csr "$OPS_CSR" \
  --issuer-key "$APPROVED_NEW_CLIENT_ISSUER_KEY" --replace-client-ca \
  --approve-config-sha256 "$OWNER_APPROVED_POST_IMAGE_CONFIG_SHA256"
python3 -m infra.staging.deploy --config "$CONFIG" --check
```

Set variables to the existing actual CSRs, an approved **new** issuer key path in
its separate private directory, a new generation path and reviewed image candidates.
Do not infer registry provenance/approval from a digest's shape. Original and
post-image configs remain in `config.json.before-<sha>`; do not overwrite or publish
these backups. Continue at step 4 only after strict renderer validation succeeds.
These commands provision configuration/PKI only; they do not deploy services.
