# PWC-03C — API Contract Integration Review

Date: 24 October 2026. Scope: completed PWC-03C shared-contract slice and bounded review corrections only. No PWC-03D, W2, live web authentication, Flutter application, business API or deployment work.

## Verdict and merge gate

**Suitable for human review once final validation and exact-head GitHub checks pass.** All reproduced findings below are corrected. No unresolved Critical or High finding was identified in this bounded review. This is not a full penetration test, native integration acceptance or production security certification. Require owner review of the complete PR and green checks on its final head/merge candidate before merging; do not auto-merge.

## 1. Repository integrity and baseline recovery

Assigned active branch: `arena/44f76f8d-pwc-platform`. The checkout unexpectedly started at `cf82dec7adfc6f57e1152cabc6d1f0491d09a5b7`, with the PWC-03C implementation as modified/untracked files. Fetched main and the feature branch; remote feature HEAD was the required `18445ac512fe143f68fadf781cade9a5a59e7c6a`. Every local implementation file was compared byte-for-byte to that checkpoint and matched.

Before reconciling, saved an external preservation archive (`/home/user/03c-review-preservation.tar.gz`) and an include-untracked Git stash. Fast-forwarded the same assigned branch to the existing required checkpoint. No files were discarded, commit recreated, branch switched, stash dropped or history rewritten. Review changes are descendants of that checkpoint. Existing stash/archive are retained rather than reapplied over identical committed files.

Fetched main is `cf82dec7adfc6f57e1152cabc6d1f0491d09a5b7`. Unshallowed the existing checkout to verify ancestry of the merged PRs: #3 `889fc2f`, #4 `cb4ae6c`, #5 `cf82dec`. The whole PWC-03C diff against main was examined: 23 implementation files originally, dominated by generated OpenAPI/type artifacts, plus these review-only tests/checks/docs. Re-fetch and verify current main before PR creation.

Protected comparisons against main show **no changes** to approved ADRs, production backend accounts/access/config/organization code, migrations, production Python dependencies, application flags, either web application, mobile scaffold or product specifications. Auth ADR SHA256 is `bb2969e5c59fd2889fec83192000590274da2b0570770ae122f43ebe2aecc294`; authorization `93d30e1169c2ac0654803348ae4a01450b2fa4902b414a517b050692376a834f`; web ADR `734b9323dd35bde5fe67b1b0e7b4d4746231206c62b78b2f6d76e551a96a2496`.

References: [AGENTS](../../AGENTS.md), [Roadmap v2.0](../development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md), [auth ADR](../decisions/ADR-0001-authentication-and-recovery.md), [authorization ADR](../decisions/ADR-0002-multi-ngo-authorization-and-tenant-isolation.md), [web ADR](../decisions/ADR-0003-web-frontend-architecture.md), [contract runbook](../runbooks/PWC-03C-SHARED-API-CONTRACTS.md), [Flutter architecture](../product/PWC_Flutter_Frontend_Architecture_v1.0_Draft.md).

## 2. Architecture and canonical contract accuracy

Implementation behavior remains authoritative; annotations are reviewed descriptions, not new endpoint promises. OpenAPI 3.1 generation is offline and does not register a schema route or import tools into the production security services. Public organization properties derive from the existing DRF serializer. Plain Django auth closures still require explicit annotations; this is not a claim that all schemas are inferred automatically.

Final counts remain **32 paths, 47 operations, 39 schemas**. Canonical JSON, generated TypeScript/browser metadata, checked examples, existing fixture files and source-lock bytes are unchanged by this review. No published wire shape, endpoint or existing frozen operation/schema/security fingerprint was amended. Only two new global guard fingerprints were appended to the compatibility manifest; original values were checked for equality before adding them.

### All path/operation families

| Surface                         | Paths / operations | Accuracy and availability assessment                                                                                                                                                                                                                                                                                  |
| ------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Registration and password reset | 6 / 6              | Request/resend POST 202; registration confirm 201; reset confirm 204. Exact JSON field sets and anti-enumeration replies match closures/services. Public proof inputs still require direct HTTPS, browser provenance/CSRF checks when applicable, and default-off flow configuration. Delivery remains synthetic-only |
| Sessions/authentication         | 9 / 9              | CSRF GET 200; distinct web/mobile login POST 200 or enabled/enrolled-MFA 202; native refresh POST 200; personal me/list GET 200; logout/logout-all POST 204; own-session DELETE 204. Logout body optional, other commands require their declared body; ownership/assurance stays backend-side                         |
| MFA and personal assurance      | 10 / 10            | Browser/native preauth confirmation POST 200, status GET 200, enrollment/intent POST 201, confirmation/recovery-code rotation/step-up POST 200, removal/hold-clear POST 204. Default-disabled personal security, not NGO grants                                                                                       |
| Synthetic NGO context           | 4 / 8              | GET/HEAD only: discovery, capabilities, private probe, kernel-settings. Outer HTTP flag off hides even unsupported methods with 404; kernel/isolation/dependency failures can instead be 503. Never production workspace APIs                                                                                         |
| Public organizations            | 2 / 6              | GET/HEAD/OPTIONS, verified-workspace public projection only; unpaginated collection. Detail UUID path converter and four serializer fields (`id`, `name`, `city`, `classification`) preserved                                                                                                                         |
| Health                          | 1 / 8              | Actual method-agnostic Django handler, with GET recommended; unsafe methods can fail Django CSRF middleware. No liveness-to-authentication or database-readiness claim                                                                                                                                                |

Unregistered password/contact change, real NGO discovery/grants/workspaces, finance, governance, files/exports and future product routes remain absent. Canonical screen/authority statuses are not changed by contract metadata.

### All 39 schema families

- Common (6): Empty, Health, AuthError, ContextError, PublicError, Csrf.
- Verification/reset (7): FlowRequest, FlowResend, RegistrationConfirm, ResetConfirm, FlowAccepted, ResendAccepted, Verified.
- Login/session (8): Login, Refresh, SessionEnvelope, Me, MobileSession, Preauth, MfaLogin, Sessions.
- Personal MFA/assurance (11): ProofCommand, MfaStatus, IntentRequest, Intent, StepUp, ClearHold, Assurance, Enrollment, EnrollmentConfirm, RecoveryCodes, Activation.
- Context (4): Context, Discovery, Capabilities, SyntheticResource.
- Public projection/framework metadata (3): PublicOrganization, PublicOrganizations, PublicMetadata.

Required/optional/nullable checks: optional device label and ordinary step-up TOTP stay optional; hold-clear TOTP is mandatory. Own-session revoke intent may additionally name the target object; arbitrary version/domain commands remain rejected. `last_mfa_at` and discovery `next_cursor` are nullable, not silently mandatory non-null strings. Schemas intentionally describe usable wire shapes, not every invalid input accepted into anti-enumeration/error handling. Email normalization, password strength, ownership, proof freshness and state/deadline conditions cannot be proven by structural types.

**Precision limits disclosed, not promoted to guarantees:** error responses use conservative shared status families; they are not an exact reachability matrix for every method/state. Error-code/status semantics are checked by existing endpoint assertions, not fully constrained enums in every JSON schema. PublicMetadata is intentionally a loose framework object, not a typed capability response. Generic non-JSON framework/proxy errors remain fallback failures, not validated successful adapter envelopes. These constraints do not expose a new route or enable authority, but future consumed W2 operations still need exact decoder/scenario acceptance.

## 3. Findings and corrected regressions

Severity reflects contract/CI reliability in a disconnected foundation, not an active exploitation of live NGO data. No production security code was changed to accommodate validators.

| ID  | Severity / status | Confirmed finding                                                                                                                          | Correction                                                                                                                                                                                                                                                       |
| --- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | Medium — resolved | An undocumented 204 bypassed response schema/status checks; `application/jsonp` was accepted as JSON due to prefix matching                | Reject undeclared success/redirect statuses before empty-body shortcuts; parse the exact case-insensitive media type separately from parameters. A legitimate JSON charset response still passes                                                                 |
| C2  | Medium — resolved | Synthetic `Vary` was declared but ignored by the validator unless a const header existed; missing Authorization partition was not detected | Require both Cookie and Authorization tokens on validated synthetic adapter responses, including bodyless declared responses; tolerate token case/order and additional safe tokens                                                                               |
| C3  | Medium — resolved | Golden coverage accepted an error example as evidence of a success and did not require request examples                                    | Require every declared JSON success status and every request-body operation to have a checked example. This checks coverage, not whether inert credentials could authenticate                                                                                    |
| C4  | Medium — resolved | Compatibility fingerprints omitted global security/lifecycle metadata, relative server and OpenAPI dialect                                 | Add global-security and protocol fingerprints without changing any existing frozen entry. Mutation tests now reject those changes                                                                                                                                |
| C5  | Low — resolved    | Generation overwrote checked artifacts before rejecting an incompatible change                                                             | Check compatibility before any output write; a regression verifies all three checked artifacts remain unchanged after an incompatible generation attempt. This is failure-before-write for compatibility errors, not a general multi-file filesystem transaction |

Reproduction before fixes: **7 failures / 1 pass** across eight new regression tests. After fixes: all **15 focused contract tests** pass. Added tests are isolated and use inert HttpResponse objects or temporary files, not operational credentials. No existing test was removed/skipped or weakened. Original operation/schema/credential fingerprint values and current wire artifacts remain unchanged.

## 4. Drift prevention: guarantees and limits

- Recursive Django URL inventory covers all current registered paths. Actual production adapters/services/registry/models/settings in the source lock are hashed; serializer field changes also alter the generated document. Exact generated-file and TypeScript-byte comparison catches stale checked output.
- The complete opt-in regression runner validates actual Django test-client results, not fixture-generated successes. It checks schema/known JSON statuses, no-store/no-referrer, bodyless HEAD/204 semantics, and now synthetic Vary. It hides potentially sensitive validation instances from failure messages.
- Compatibility fingerprints sort object keys, so object key ordering is not itself a change. Array order, documentation strings, annotation changes and source whitespace still cause conservative false positives. This is deliberate review friction, not a semantic backward-compatibility engine.
- Source hashes are not inference: updating a hash without reconciling annotations can hide a mistake. Existing source-lock coverage is finite (current app-root modules/config, not every future nested package/migration). New API apps/nested runtime modules require expanding that coverage. Existing PostgreSQL/migration tests remain necessary.
- Positive response validation does not validate every request or prove every endpoint/state combination. Stateful ownership, concurrency, anti-enumeration, refresh replay, grants and expiry are supplied by the existing regression assertions, not inferred from OpenAPI or example counts.
- Frozen manifest edits still need human review. No checksum can approve a policy change, prove a deployed server's version, prevent a malicious code change approved together with its tests, or replace actual browser/native ingress acceptance. Top-level descriptive text and compatible release evolution are not full behavioral equivalence proofs.
- Examples are structural, synthetic and inert. They cannot establish email delivery, OTP correctness, secure storage, actual NGO authority or successful requests with placeholder proofs. Existing historical MFA-disabled fixtures must not override enabled-MFA implementation behavior.

## 5. Transport, tenancy and confidentiality

Browser issuance/preauth completion uses exact configured HTTPS portal and CSRF; unsafe personal cookie requests require CSRF. Native issuance/refresh/preauth rejects ambient browser provenance/cookie/Authorization as implemented, with body proofs. Authenticated personal reads/commands choose exactly one cookie or native opaque Bearer; refresh never accepts access Authorization as a fallback. No browser bearer storage, JWT decoding, permissive CORS/proxy or live networking switch was added.

MFA 202 is preauth, not a logged-in principal. Recovery holds stay clear/restricted/review_required; only eligible restricted hold clearance uses a NEW captured pre-hold factor code. Successful web assurance/clearance rotates cookie+CSRF while preserving logical session. Native refresh is single-use and a lost response is not permission to replay; idle/absolute expiry and no GET/status/list/refresh idle renewal remain unchanged.

NGO requests require explicit Organization UUID paths; no selection headers, first-NGO fallback or client role hierarchy. Signed discovery cursors are principal/session-bound scan positions, not encryption, stable snapshots or authority; at most 50 results and 3600-second age remain documented. Cache partitions include portal/principal/logical session/NGO/registry/revision/generation, with cancellation and stale-completion fencing.

Backend grant checks remain authoritative. NGO admin does not imply finance; PWC Board/platform/staff does not imply NGO-private access. Personal assurance does not create domain authority. Synthetic probes remain independently gated and isolated. Current public projections are minimized, not membership/finance/evidence export. Adapter no-store/no-referrer and synthetic Cookie/Authorization Vary requirements are verified; global ingress failures are not claimed to have adapter headers.

Example/fixture review found only reserved domains, synthetic identifiers and inert placeholders, not live account/session/OTP/refresh secrets or real NGO/member data. Generated TypeScript is type-only; complete schemas are not shipped as a new executable client.

## 6. Web and Flutter readiness

W1 keeps exactly its existing six operations, generated metadata and request-body types, safe normalized errors and redacted runtime views. Both app factories remain default-disabled, separately scoped and without fetch fallback; browser tests still record zero API calls. Local `assertContractVersion` checks checked-artifact consistency only; no fictitious HTTP version negotiation was introduced. Schema types do not replace future runtime decoders.

Flutter guidance covers one personal identity, separate native transport, 300-second access credentials, reviewed OS-secure refresh storage, atomic serialized refresh/re-login on ambiguous consumption, login/logout/MFA/holds, request cancellation versus unknown server commit, bounded retries, error taxonomy, context cache purging and evolution. Review adds explicit logout/cancellation/retry clarification to the runbook. No Flutter SDK/model/client/screen is generated or compiled; those remain separate approved work.

## 7. Validation evidence

Environment: Python 3.11, disposable PostgreSQL 16.2, Node 22.22.3/npm 10.9.8; sandbox Chromium 153 with external runtime libraries. CI uses supported Python 3.11/3.12, PostgreSQL 16 and managed Playwright Chromium. Dependency manifests/locks and CI workflows are unchanged by the review itself; initial PWC-03C additions remain in the full PR.

| Check                                                                       | Actual result                                                                                                                                                      |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Fresh locked npm install / Python dependency consistency                    | Passed                                                                                                                                                             |
| OpenAPI 3.1/schema/source/inventory/compatibility/examples/type-byte checks | Passed; 32 paths, 47 operations, 39 schemas, 70 examples                                                                                                           |
| Defect reproductions                                                        | 7 failed / 1 passed before correction, expected failures                                                                                                           |
| Focused contract tests                                                      | 15 passed                                                                                                                                                          |
| Full PostgreSQL/Django regression suite and actual HTTP validator           | 351 passed on PostgreSQL 16.2; 168 distinct route/method/status combinations validated; dependency, Django and migration plan/application/drift/check gates passed |
| Strict TypeScript, scoped Prettier, both web production builds              | Passed                                                                                                                                                             |
| Web unit/component/config/contract tests                                    | 113 passed across 5 files                                                                                                                                          |
| Fresh production Chromium                                                   | 11 passed; axe/keyboard/RTL/320px/portal isolation/zero API traffic                                                                                                |
| npm dependency audit                                                        | 0 reported vulnerabilities; not a certification                                                                                                                    |
| Protected decisions/runtime/migrations/apps/fixtures/type/wire artifacts    | Unchanged as described above; source and decision comparisons passed                                                                                               |

A separate release-advisory metadata lookup checked all **31 distinct pinned Python releases** across production and contract-tool requirements against PyPI: no advisories returned. This is a point-in-time PyPI lookup, not a full pip-audit/OSV scan or security certification.

No native Dart compilation, real mobile secure storage/deep-link test, live cookie/CSRF/TLS ingress, real email delivery, physical screen-reader/native Urdu or Firefox/WebKit acceptance was performed. Existing GitHub checkpoint results must not be substituted for final-review commit results. Final task report/PR records current exact-head CI; require green checks after the final push. Logs, test DB, browser binaries and environments stay outside Git.

## 8. Deferred scope and recommendation

The broader roadmap's shared audit/event infrastructure and private-file/storage/scanning/download/export primitives remain explicit follow-on tasks; existing auth/authorization events are preserved, not replaced. No claim that every PWC-03C roadmap item is completed.

After human review of this bounded PR: select a separate approved Flutter foundation or W2 contract/HTTPS readiness work package. Neither begins automatically here. W2 still needs exact consumed schemas/scenarios, real email delivery approval, TLS/Host/Origin/CSRF/cookie/source-IP/abuse acceptance and recovery/rotation/lost-response ceremonies. W3 requires NGO eligibility/representative verification, REAL01–REAL04 authority activation and real workspace/capability contracts. Production privacy/legal/retention/support/security-header/operational/deployment approval is separate.

**Merge recommendation:** accept only the bounded shared-contract foundation after owner review and green exact-head/PR CI. No unresolved Critical/High finding was identified; these corrections do not approve real users, NGO authority or deployment. Stop after the single PR is prepared, without merging.
