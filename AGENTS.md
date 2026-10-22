# Agent instructions — Pakistan Welfare Club

## Purpose and existing architecture
PWC is a Faisalabad-first ecosystem for independent welfare NGOs, citizens/volunteers and voluntary alliance projects. PWC operates the platform, not the internal affairs of every NGO. Preserve the existing monorepo and modular Django/DRF + PostgreSQL foundation; do not rebuild it or introduce microservices. The technology foundation is adopted provisionally by ADR-0001, not production approval.

Implemented: `accounts.User` (UUID `AbstractUser`), organization/workspace/access skeleton, minimal health check and read-only public verified-organization projections. Session authentication is configured as a DRF default, not a completed login system. No private tenant APIs, granular authorization engine, finance, membership workflows or production deployment exist yet. Do not represent scaffold role labels or tests as proof of these capabilities.

## Planning authority and conflict handling

### Documentation hierarchy and master execution plan
- **Requirements authority:** The Strategic & Product Foundation (`docs/product/PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md`) remains the authoritative source for product requirements and provisional decisions. Its decision statuses must be preserved; provisional does not mean approved.
- **Implementation design references:** The technical architecture, identity/authorization, information architecture and detailed screen specifications listed below guide implementation design and canonical screen/flow mapping. They do not independently approve or redefine product requirements.
- **Master engineering execution plan:** Read [AI-Agent Implementation Roadmap v2.0](docs/development/PWC_AI_Agent_Implementation_Roadmap_v2.0.md) before planning or executing a task. It defines engineering phases, dependencies, task sequencing, acceptance gates, agent workflows and execution standards. It refines the earlier Development Execution Plan and M1 backlog for engineering sequencing, without replacing requirements authority or approving unresolved decisions. Apply its task contract, prerequisite checks, scoped execution, evidence-based reporting and human PR review standards alongside the instructions here.
- **Repository-wide agent instructions:** Root `AGENTS.md` contains the development instructions agents must follow throughout this repository. Task prompts supplement these instructions rather than replacing them; the roadmap does not waive the repository's security, quality or scope constraints.

Unresolved decisions cannot be treated as approved requirements. Only an explicitly human-reviewed and accepted ADR or product decision establishes approval within its recorded scope; a roadmap entry, AI recommendation or implementation commit alone does not. If requirements, design references, execution sequencing or repository instructions conflict, use the conflict-handling process below rather than silently selecting an interpretation.

Read `README.md`, `docs/decisions/`, the local setup runbook and relevant documents in `docs/product/` before changing code. All eight product documents remain drafts. Their roles (see Development Execution Plan §2) are:

1. `PWC_Strategic_and_Product_Foundation_v1.0_Draft_for_Review.md`: product scope, NGO independence, provisional governance and selected requirements.
2. `PWC_Identity_Authorization_and_Multi_NGO_Data_Model_Foundation_v1.0_Draft.md`: identity distinctions and security/domain invariants.
3. `PWC_App_Information_Architecture_and_Navigation_v1.0_Draft.md` and `PWC_Detailed_Mobile_and_Web_Screen_Specification_v1.0_Draft_for_Review.md`: canonical navigation, screen IDs, flows and screen acceptance.
4. `PWC_Django_Backend_and_PostgreSQL_Schema_Foundation_v1.0_Draft.md` and `PWC_Flutter_Frontend_Architecture_v1.0_Draft.md`: implementation recommendations, not permission to redesign product policy.
5. `PWC_Development_Execution_Plan_v1.0_Draft_for_Review.md` and `PWC_M1_Implementation_Readiness_and_Engineering_Backlog_v1.0.md`: dependencies, milestone sequencing and quality gates, not approval of unresolved decisions.

This is a responsibility/precedence guide, not a new policy approval. Explicit reviewed decisions in `docs/decisions/` govern their recorded implementation scope; README describes executable reality, not a replacement product specification. Source IA/screen IDs override illustrative alternate prefixes or paths in companion drafts. Preserve all planning documents; do not silently reconcile contradictions. Stop affected work, explain the conflict, propose an ADR and request owner review. Coventure is technical precedent only, never a source of PWC business requirements.

Respect labels: [S] selected provisionally, [R] recommended, [O] open, [D] deferred. Neither S nor R means formally approved. Record unresolved questions in `docs/decisions/OPEN-DECISIONS.md`; do not invent authentication channels, finance policy, verification evidence, retention terms or legal authority. Unrelated decisions may remain open; security-sensitive blocking decisions cannot be waived. PWC-01 does not authorize M1 authentication implementation.

## Repository organization and coding conventions
- `apps/backend/`: `config/` settings, URLs, WSGI; `accounts/` shared identity; `organizations/` organization registry scaffold; app-local migrations and Django tests.
- `apps/mobile/`: Flutter reserved path. Do not rename it to illustrative planning paths or generate a project until SDK/platform decisions are approved.
- `apps/ngo-web/`, `apps/pwc-ops/`: separate reserved interfaces; web frameworks remain open.
- `packages/api-contracts/`, `packages/design-tokens/`: reserved shared contracts/tokens, not implemented packages.
- `tests/end-to-end/`: future multi-surface security scenarios; `infra/`: infrastructure guidance; root Compose is local development only.

Use four-space Python indentation, snake_case functions/modules, PascalCase classes, explicit imports and descriptive tests. Match nearby Django patterns without broad reformatting. No formatter/linter is configured yet: do not claim a lint gate exists. Keep focused diffs; separate unrelated cleanup. Do not fabricate API contracts or generate clients from unapproved illustrative endpoints.

## Backend and database rules
Use Django ORM and PostgreSQL, not SQLite as a substitute for database acceptance tests. Retain the custom user model and existing migration history. Create additive, reviewed migrations; never edit applied initial migrations to hide drift. Run migration drift and application checks for every model change. Use UUIDs and timezone-aware UTC timestamps consistently with the foundation. Enforce uniqueness and ownership invariants in the database where applicable; protect historical records against accidental cascade deletion.

For future domain writes, use explicit services and transactions; side effects happen after commit or through an approved outbox. Money uses an approved fixed-precision representation, never float. Do not add queues, RLS or storage providers merely because they appear in a draft. RLS is not currently active. Pin tested dependency updates and rerun checks. Keep credentials environment-supplied; no silent production defaults.

## Mandatory isolation and authorization invariants
1. One personal identity can hold multiple independent NGO and PWC relationships. Do not create separate login identities per NGO.
2. NGO individual membership, standing volunteering, activity participation, administrative grants and PWC institutional membership are separate relationships.
3. Each NGO controls its private workspace/data. Future private queries must constrain tenant before returning lists, details, counts, search results, files, imports, exports or background-job output. Client-supplied organization IDs and UUIDs are not authority; validate actor, active context, object ownership and action permission on the backend.
4. PWC Board/alliance/committee roles grant no automatic access to private NGO information. Technical support authority is separate, scoped, justified, expiring and audited; do not expose an unrestricted Django Admin as a shortcut.
5. NGO finance read/write/approve/export/grant powers require separate explicit authorization. Even NGO primary-admin status does not imply finance access. Do not use Django superuser/staff flags as domain role shortcuts.
6. UI route guards and hidden buttons are presentation, never security. Every sensitive operation must be authorized server-side, including direct API calls and revocation checks.
7. A provisional workspace/claimant cannot access an existing NGO's private records before verification of organization eligibility and representative authority. Importing people cannot create authenticated users or auto-link them on name/contact matching alone.
8. PWC project approval never commits a member NGO. NGO acceptance requires its own authorized, version-specific approval workflow.

Public projections expose approved public fields only, never ordinary rosters, finance details or private evidence. Current verified-state publication is only a scaffold; consent/publication policy remains open. Do not widen it casually.

## Frontend rules
Flutter is planned, not generated. Pin a reviewed SDK before scaffolding; preserve canonical screen IDs. Both web surfaces share backend identity/contracts rather than independent identity stores. Display explicit workspace context and server-issued capabilities. Reset private state/caches on context switch, logout or revoked access. Never persist private rosters, finance data or tokens in ordinary caches/logs. Do not optimistically finalize finance postings or binding commitments. Use relative/proxied browser API URLs in remote development; browser localhost is not the backend. Frontend framework selection requires an ADR, not an agent guess.

## Quality and security
Follow `docs/runbooks/LOCAL-SETUP.md`. Minimum backend gate: dependency consistency, Django `check`, `makemigrations --check --dry-run`, migration plan/application, `migrate --check`, and tests on actual PostgreSQL. Keep CI green on supported Python versions. New private endpoints require positive and negative NGO A/B tests, claimant/verified/revoked grants, alliance-role denial and independent finance checks, including reads/writes/search/files/exports as applicable. Existing public projection tests do not prove private isolation or finance authorization. Document unexecuted checks honestly. No real NGO/member/beneficiary data in tests or staging.

Never commit `.env`, private keys, tokens, database dumps, user uploads, credentials or sensitive personal data. Use synthetic fixtures and development-only secrets. Do not print environment secrets in logs or reports. Placeholder/example/CI credentials are not production credentials. If a real credential is found, redact reports, notify the owner and rotate/revoke through the appropriate process; deleting a file alone does not remove Git history exposure. Check tracked files and diff before committing. Production HTTPS, secure cookies, backups, secret management and operational review are separate release gates.

## Git and handoff
Work in the assigned task branch from main; do not develop on or merge into main automatically. In Arena this session is fixed to `arena/9192ec62-pwc-platform`: do not switch/create/rename branches and push only that branch. Preserve pre-existing user changes. Use focused commits such as `chore(PWC-01): validate backend foundation and document agent workflow`; never commit generated environments/databases or bypass failing checks without disclosure.

Finish each task with changed files, exact commands/results, resolved and unresolved issues, security observations, branch/commit and next-task readiness. Approval blockers must be explicit; passing scaffold tests is not production or M1 sign-off.
