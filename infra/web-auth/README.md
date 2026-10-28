# Web authentication ingress acceptance — deployment handoff (NOT activated)

No actual NGO/Operations hostnames, DNS zone, edge/provider configuration, upstream
server, certificate ownership or independent acceptance evidence is recorded in
this repository. The deployment question in this assignment supplied no hosts.
Do not substitute `.invalid` fixtures, Arena preview URLs or invented domains.

**Current decision: production enablement BLOCKED.** ADR-0003 §4, WEB-02/03/09
and applicable AUTH/E/GM/REAL gates are unchanged. This is an executable validation
procedure, not a provider choice, deployment recipe, release approval or proxy-trust
extension. Existing staging/production environment parsing rejects enabled service
flags; historical workspace endpoints also remain development/test-only. Accepted
host observations alone cannot remove those runtime/independent approval gates.

## 1. Inputs required from deployment/security owners

Record in the approved restricted evidence system (not this public repository):

- The two **distinct exact HTTPS origins** and DNS ownership, SNI/Host/port mapping,
  environment and artifact SHAs; accountable deployment/security reviewers.
- Edge and application-server products/versions; complete network-hop diagram;
  genuine TLS at the WSGI/ASGI application boundary; verified upstream CA/name,
  backend peer restrictions/firewall and any mTLS decision; certificate rotation owner.
- Sanitized effective Django configuration: exact `ALLOWED_HOSTS`,
  `PWC_AUTH_PORTALS` (`ngo_web` / `pwc_ops`), no wildcard/trailing-path aliases,
  `SECURE_PROXY_SSL_HEADER=None`, `USE_X_FORWARDED_HOST=False`,
  `USE_X_FORWARDED_PORT=False`, `CSRF_TRUSTED_ORIGINS=[]`, secure cookie settings,
  DB TLS, debug disabled, secret/key rotation references (never actual keys).
- Approved source-IP contract and abuse budgets: backend `REMOTE_ADDR` origin,
  aggregate edge and shared-NAT/load results. No ad-hoc X-Forwarded-For middleware.
- Log/trace/analytics redaction, retention/incident access, rollback and restore
  ownership; provider/link-origin acceptance where account delivery is used.
- Independent approval of any required production-mode/backend service activation;
  no flag/transport switch is introduced by this PR.

## 2. Read-only external observations (no credentials)

In an operator environment with network access to the supplied real hosts:

```sh
# Set these to the independently supplied exact origins; no defaults are provided.
python scripts/web_host_preflight.py \
  --ngo-origin "$REVIEWED_NGO_ORIGIN" --ops-origin "$REVIEWED_OPS_ORIGIN" \
  > "$RESTRICTED_EVIDENCE_DIRECTORY/web-host-observations.json"
```

This standard-library tool requires separate named HTTPS hosts, checks public DNS
and system-CA TLS/hostname verification, then GETs health/anonymous CSRF/me without
credentials, cookie reuse or redirects. It records bounded status/security-property
observations, not response bodies, tokens, cookie values or raw exceptions. A
private/VPN-only deployment needs separately reviewed operator-side observations;
this tool deliberately refuses private DNS targets. Exit 0 means **observations
completed**, not that endpoints/security checks passed, and certainly not acceptance.
Review each status/property. `me` should deny anonymous access without redirects or
SPA HTML; 503 indicates a still-disabled service, not functional authentication.
The report always leaves production enablement blocked and lists unverified tests.

Record certificate chain/issuer/SAN/expiry and rotation evidence separately. The
observer is not a substitute for certificate expiry monitoring or ingress inspection.

## 3. Inspect every hop before testing credentials

Preferred boundary:

```text
Browser HTTPS -> controlled exact-Host edge -> certificate-verified private HTTPS
              -> TLS-capable application server -> genuinely secure Django request
```

- Serve each static build only at its own approved host. Preserve canonical Host.
  `/api/v1/*` must reach Django, never SPA fallback; never cache auth/private API
  responses. Keep separate portal deployments and host-only cookies.
- Edge strips client `Forwarded` / all `X-Forwarded-*`, rejects conflicting/duplicate
  authority/framing and unknown hosts. Application does not trust these headers.
- Wrong-name/untrusted/expired upstream certificates must fail closed; backend must
  not be an alternate public ingress. Prove peer restrictions, not just encryption.
- TLS must reach the application-serving layer. Do not set Django's proxy SSL tuple
  to repair a plaintext application hop: existing explicit gates reject it. A trusted
  termination alternative requires a separate accepted security implementation.
- Unsafe HTTP must fail, not redirect already-submitted secrets. Test redirects with
  no credentials first; no redirect may carry proof/password/query credentials.
- Review effective HSTS/CSP, anti-framing, no-sniff/referrer headers and no credentialed
  CORS; no remote runtime assets, auth caching, sensitive telemetry or exception dumps.

## 4. Real-browser acceptance at BOTH actual hosts (synthetic test users only)

Use an isolated review environment with approved infrastructure, synthetic identities
and historical test records. Do not enable real public intake or officer powers to
prepare tests. Record artifact/config SHAs, timestamps, reviewer and sanitized results:

1. Anonymous history and `me` denied; password sign-in establishes the host-only
   `__Host-pwc_session` (Secure, HttpOnly, Path=/, SameSite=Lax); CSRF cookie is Secure,
   host-only, Path=/, SameSite=Lax. Verify fixation prevention and fresh CSRF after login.
2. Enrolled account returns 202 preauth only; TOTP completion needs ephemeral control
   plus rotated CSRF. Expired/replayed/cancelled challenges fail. Recovery code gives
   restricted—not officer/NGO/finance—authority. `review_required` has no self-clear bypass.
3. Owner history, verification/source revisions and stale indications; foreign/missing
   object IDs indistinguishable. No private target projection or prohibited new intake.
4. Exact-revision withdrawal through confirmation; success reload; stale/duplicate
   conflicts cause no duplicate events. Deliberately lose an actual response and point
   reconcile independently of list filters. An unchanged read is not proof of noncommit;
   no automatic unsafe retries or fabricated withdrawal receipts.
5. Missing/stale CSRF, sibling Origin, null Origin/invalid Referer, cookie+bearer and
   browser native issuance rejected. Explicit session/CSRF recheck does not replay a write.
6. Replay NGO cookie on OPS and vice versa; reject mismatched portal/Host/port, unknown
   Host, forwarded-header spoofing including duplicate/comma values and direct ingress.
   Spoofing must not change scheme/portal/source-IP budget identity.
7. Idle and absolute expiry, inactive/revoked account/session, logout and cross-tab
   invalidation purge private UI. Failed logout says server outcome unconfirmed; only
   explicit retry. No heartbeat extends idle life. Normal read/refresh is not activity.
8. Inspect browser storage, URL/history, network, sanitized logs and artifacts: no
   passwords/cookies/CSRF/preauth/recovery proofs in app persistence or telemetry.
   Password-manager support is not permission for application-side credential storage.
9. Test source-IP/NAT/concurrency budgets without relaxing backend limits. Verify
   backend unavailable/redirect/error behavior and rollback at both independent portals.
10. EN/UR, narrow viewport, keyboard/screen-reader and actual supported browser review;
    automated axe/Chromium is not manual accessibility or native-device acceptance.

Do not store unredacted HARs/traces/session-cookie exports in Git or CI artifacts.
A passing synthetic direct-TLS test in this repo is **local integration evidence only**.

## 5. Acceptance record

| Category | Current state |
| --- | --- |
| Locally integrated/verified | Browser password/TOTP/recovery + session/workspace flow tested against actual Django/PostgreSQL with ephemeral synthetic TLS |
| Production-host verified | **None**: hosts/configuration/credentials/evidence not supplied; no external success claimed |
| Implemented but disabled pending acceptance | NGO browser login/session/history and compatible OPS personal-session/policy composition; no shipped adapter or environment enable switch |
| Privileged separately blocked | Officer/reviewer provisioning, private queues/decisions, invitation/grant activation, finance/signatory/support, new intake |

Reviewers must attach exact-host results and explicitly accept the applicable version/
environment with exclusions. Merging code/documents or running the observer does not
change any pending security/operations/release status.

## Disabled-service staging foundation

[PWC-04C staging infrastructure](../staging/README.md) supplies a separate
Compose/PKI/build/migration/backup foundation with genuine application TLS and
all service gates off. Its synthetic infrastructure tests are category **A only**;
actual deployment (B), independent exact-host acceptance against this baseline
(C), and explicit credential-transport/runtime authorization (D) remain separate.
It does not enable this authentication handoff or replace any requirement above.
