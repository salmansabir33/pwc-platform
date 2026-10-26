# PWC-04A — Registry integration and internal security review

Date: 27 October 2026. Scope: [runbook](../runbooks/PWC-04A-NGO-REGISTRY-AND-CLAIMS.md), ORG-01/02 only. Main baseline `5c3c6d0294d63e8b5719df865ea40da9e6d8be90`, merged PR #10 owner disposition. Assigned writable branch: `arena/9ab3f8ef-pwc-platform`. No independent human security/legal/governance approval is claimed.

## Authority and inspected foundations

AGENTS/roadmap P3, Strategic and Identity foundations, approved ADR-0001/0002/0003, ADR-0004, E01–E18/GM01–GM12 owner dispositions and REAL gates constrain this slice. Existing Django organization/public projection, live personal sessions and recovery holds, synthetic authorization/DB guards, audit primitives, PWC-03C generation/compatibility/runner, React W1 blockade, Flutter native allowlists and PWC-02F CI/configuration were inspected. Historical AGENTS branch/scaffold descriptions do not override the current assignment or merged executable foundations.

This assignment supplies authority to implement the **safe claimant foundation**, not missing evidence/quorum/assurance/publication standards or grant commands. Default-off synthetic exercise is deliberate: real data/authority intake remains gated. Canonical current public fields are unchanged. No policy matrix/ADR approval status is edited.

## Threat review / corrected defects

| Threat / defect | Control and evidence |
| --- | --- |
| Existing NGO takeover / forged representation / contact coincidence | Applications never create grants, legacy roles, mandates or verified state; repeated and rival requests cannot transfer a workspace; direct DB counts and target fields tested |
| Cross-tenant enumeration / hidden target discovery | Every own lookup filters locked claimant before UUID lookup; hidden/nonexistent/provisional targets have same 404; search reads only existing four public fields; no count or global collision oracle |
| Board/staff/synthetic/legacy privilege shortcut | Staff/superuser and legacy admin still get other-owner 404; no access-model writer in registry; existing authorization denial suite remains applicable |
| Recovery restriction / suspension / stale identity | Current User-first session locks and completion reauthentication in same transaction; all registry reads/writes denied on holds; revoked/inactive/missing sessions tested; no MFA/hold bypass |
| Duplicate / lost-response / concurrent mutation | Owner-scoped receipts and conditional DB uniqueness, User serialization, revision conflicts, independent PostgreSQL connections and barrier-start races |
| Audit failure / incomplete transition | Transactional identity/application/event/receipt rollback; injected history failure on create and submit; immutable DB event/receipt updates/deletes rejected |
| History loss on rollback | Used-record reversal guard requires forward correction; migration compatibility test preserves UUID, Unicode keys and unpublished state |
| Unicode/case/whitespace / alias collision | NFKC/casefold/collapsed whitespace keys; no global name/contact uniqueness, no alias publication/authority; exact registration namespaces remain unresolved |
| Request ambiguity / error/log disclosure | Closed bounded DTOs, duplicate JSON rejection, redacted generic errors, forbidden browser-Bearer provenance, no-store/no-referrer and Vary; no raw payload audit or logging |
| Stale client state / implicit workspace | Synthetic gateway components only; scope/language/unmount guards discard late values, default controls unavailable; no browser/live registry transport or private UI |
| Initial adapter defect | Read-only kernel negotiator had no request parser; replaced with registry-specific fixed JSON negotiation/parser before acceptance |
| Initial serializer defect | Incorrect claim model tuple corrected and claimed workflow tests rerun |
| Full-suite migration regression | Historical auth tests left organizations at old migration target; teardown now restores all current leaf migrations. Isolated and combined migration/concurrency tests rerun; full suite required at final head |

No confirmed Critical/High finding is intentionally left open in the bounded slice. This is engineering review, not adversarial certification or production performance/abuse assurance. Production DB-owner tampering, privacy/retention, provider/HTTPS ingress and actual native-device acceptance remain external gates.

## Validation ledger

Results here distinguish executed local evidence from final-head CI; the final PR report/comment records exact SHA and workflow conclusions without claiming source tests against their own future commit.

- Local Python 3.11.2 / **actual PostgreSQL 16.2**: 31 registry tests passed, including real DB constraints, immutable history, rollback, upgrade and four concurrent connection tests. Temporary `pgserver` supplied the disposable local PostgreSQL binary; it is not an app dependency or committed tool.
- Migration regression selection: 32 tests passed before the additional migration/deadline/JSON cases (registry plus historical authentication migration tests plus repeated concurrency selection).
- Full initial contract-runner execution: 394 tests, four errors due to old-test schema restoration, **not accepted as passing**. Teardown defect corrected; final full rerun/CI must pass.
- Local OpenAPI generation/inventory/source/frozen-compatibility and specification/checked examples passed; Django checks/drift and migration plan/application/check passed. Final regeneration follows any source changes.
- Local React TypeScript, formatter, unit/component suite: 118 tests passed; both production builds passed. New ORG-01/02 component cases cover gate, search/claim, create/transitions, redacted conflict and stale-scope result denial.
- Local production-browser Playwright: **12 passed**, including both portal foundations and disconnected ORG-01/02 in English/Urdu at mobile width. First attempt could not start Chromium because sandbox system libraries were missing; temporary npm Chromium runtime libraries resolved that tool limitation without repository/dependency changes. Not a live-auth browser test.
- Local scoped Ruff, tracked-file secret/config/workflow scanner, six tooling tests, dependency consistency and diff whitespace checks passed. No runtime dependency version changed.
- Flutter/Dart/Android unavailable locally. Added canonical registry DTO/example and widget tests; pinned real CI analysis/tests/Android build and formatting evidence are required. No local mobile pass is claimed.

## Remaining acceptance

Read the runbook's per-subphase and REAL gate list. In particular exact evidence rubric/registration namespace, reviewer IAM, real privacy/storage/retention, held-account case-read rules, review transitions, all privileged commands, public consent/badges and production/native deployment remain unavailable. Receipt/history retention is not silently invented. Legal terms, operations/restore and independent human reviews are not replaced by CI.

**Human review focus:** additive migration/backfill/reverse guard; claimant-only querysets/locks/final expiry; whether the synthetic-only minimized boundary is acceptable while policy gates remain; frozen compatibility plus generated client artifacts; W1 and native transport non-activation; final-head CI and source/diff hygiene. Do not merge automatically, start 04B/C/D or enable real intake as part of this PR.
