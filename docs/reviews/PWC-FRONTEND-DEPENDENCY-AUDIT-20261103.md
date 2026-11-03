# Frontend dependency audit — verified compatibility blocker

**3 November 2026; baseline main `e0cb68ad73cb2cdcb8eab907e56b898a4b867c53`.**
**Status: NOT REMEDIATED. Security gate remains failing; no acceptance/suppression.**

This records the assignment's explicit fallback when no safe compatible fix is
available. There is no verified dependency remediation to apply and therefore no
justified root manifest or lockfile change. This is not a security sign-off or an
application/governance readiness review.

## Observed failure and installed graph

[Main workflow run 41595290672](https://github.com/salmansabir33/pwc-platform/actions/runs/41595290672)
failed at `Run npm audit --audit-level=low`, job 125781106955. Reproduced with
Node 22.22.3/npm 10.9.8, `npm ci --ignore-scripts`, then the exact audit command.
Before **and after** validation: exit 1, **3 moderate**, 0 low/high/critical findings.

```text
openapi-typescript@7.13.0 (direct development tool)
└── @redocly/openapi-core@1.34.22
    └── minimatch@5.1.9
```

The three package findings are one propagated advisory chain:
[GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249), globparts
amplification denial of service. Audit reports minimatch `<11.0.1`, propagating
through Redocly `<=2.6.0` to openapi-typescript `>=7.0.0-next.0`. These are build/
contract-generation tools, not new application imports; that does **not** exempt
them from the repository's audit policy.

Exact before/after findings, counts, lockfile SHA-256 and probe results are in
[evidence/frontend-audit-20261103.json](evidence/frontend-audit-20261103.json).

## Candidate verification — no speculative override retained

| Candidate | Verified result | Disposition |
|---|---|---|
| Latest openapi-typescript 7.13.0 | Still declares Redocly `^1.34.6`; current direct tool already latest. | No patched compatible direct release found. |
| Redocly 1.34.23 | Published tarball comparison against 1.34.22: only package version/changelog changed, no runtime/dependency change. Still pins minimatch 5.1.9. | Cosmetic update would not remediate; not applied. |
| Redocly 2.7.0 (first audit-unaffected line) | Isolated install with generator 7.13.0; generation of this repository's OpenAPI exits 1: `ERR_PACKAGE_PATH_NOT_EXPORTED` for `./lib/ref-utils.js`. | Incompatible; no root override. |
| minimatch 11.0.1 | Actual CommonJS export is an object with named `minimatch`; locked Redocly 1.x does `const minimatch = require("minimatch")` then calls it as a function. | Not a drop-in dependency override. No shim/private-path patch. |
| Audit's suggested openapi-typescript 6.7.6 | Audit labels the suggestion a semver-major change (a downgrade across the generator's major boundary), not an in-range patch. | Not applied or claimed compatible; requires separate generator/semantic compatibility evaluation, not `audit fix --force`. |

Candidate probes were isolated under ignored `.cache`; they did not modify root
package files. No fork, patched tarball, lockfile edit, force fix, advisory exception,
threshold change, generated-type replacement or runtime shim was retained.

## Executed regression evidence

- `npm run contracts:types:check`: unchanged generated TypeScript **passes**.
- `npm run check`: **202 React tests pass**, typecheck, formatting, design-token
  parity and both NGO/Operations production builds pass.
- `contracts.check --check`: OpenAPI, source inventory, frozen compatibility,
  examples and security metadata pass.
- Django contract/shape/preparation tests: **22 pass** (database-free suites).
- Tooling tests: **15 pass**; repository Ruff and Python dependency consistency pass.
- Locked PWC-04C contract byte check passes. No contract, source, access-control,
  public-data, transport or CI-workflow changes.
- Browser/PostgreSQL end-to-end tests not rerun: no application/API changes and
  Chromium is unavailable. These are not claimed as passing integration evidence.

## Exact next blocker

A supported generator release must use a patched dependency graph **and** preserve
this project's OpenAPI 3.1-to-TypeScript semantics without importing removed Redocly
private paths. Alternatively, a deliberately reviewed generator replacement/major
migration needs full schema-semantic and client regression evidence; it is not a
safe automatic fix for this narrow assignment. Rerun install/audit, byte-for-byte
type generation, frontend checks and browser/backend contract integration against
the candidate. Until then the gate stays red; do not merge on a claim of remediation.

No product feature, privileged transition, deployment or infrastructure action was
performed. This evidence PR deliberately does not invent a lockfile change when no
independently verified compatible security fix exists.
