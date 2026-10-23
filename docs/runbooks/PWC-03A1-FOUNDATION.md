# PWC-03A.1 — Identity and security data foundation

## Scope

Additive schema only, following the finalized authentication ADR. The UUID custom
User, username, password hashes, legacy emails, active status and NGO FKs remain
unchanged. No existing contact is auto-verified and no existing account is merged.

`accounts.models` exports UserContact, AuthChallenge, AuthSession,
MobileCredential, MfaFactor, MfaRecoveryCode, AssuranceIntent, DeliveryIntent,
SecurityEvent and AuthAbuseBucket. Their definitions are in `security_models.py`
to keep the custom User readable. These are **inert records**, not functional
authentication, encryption, issuance, MFA, queue dispatch or rate-limit services.
No public auth URLs, new auth backend, Admin registration or DRF configuration
changes are included. Existing DRF session defaults remain scaffold only.

## Invariants and boundaries

- PostgreSQL enforces active verified-contact and primary-contact uniqueness,
  primary eligibility, closed state values, lifetimes, terminal-state pairs,
  current credential/factor uniqueness, digest shape and transport binding.
- Digest fields store 64-character hexadecimal placeholders for future reviewed
  digest services, not raw tokens. Ciphertext columns/key identifiers are schema
  only: they do not encrypt, decrypt or certify that arbitrary supplied bytes
  are genuine ciphertext. Synthetic tests deliberately use fake ciphertext.
- `full_clean()` validates cross-record ownership (contact, session, factor and
  hold evidence) and mobile-session ownership of bearer records. **Django does
  not call full_clean on save/create/bulk writes.** Future transactional services
  must validate and recheck ownership under the ADR lock order; ordinary FKs
  and CHECKs cannot enforce joins across rows. No private data API exists here.
- Verified-contact uniqueness assumes approved canonical input. No lowercasing,
  IDNA or Unicode normalization is performed while B1 remains unresolved. Do
  not expose writes or rely on this schema alone for case-insensitive login.
- SecurityEvent's supported instance/QuerySet write paths reject updates/deletes
  and conflicting inserts cannot overwrite an event. There is deliberately no
  arbitrary request-body/JSON metadata field. This is application-level hygiene,
  **not database tamper-proofing**: raw SQL, internal managers and privileged DB
  users remain outside that guard. Reviewed retention requires a separate path.
- Password policy uses Django validators with minimum 15 and the ADR's R1
  engineering ceiling of 128 code points. Paste, spaces and lowercase-only
  passphrases work. Numeric-only rejection was removed to avoid a composition
  rule; common-password and similarity checks remain. Existing passwords are
  never rehashed/invalidated by this migration. As in Django generally,
  set_password/create_user do not invoke password validators: future workflow
  services must explicitly call validate_password before changing a password.
- No schema record grants NGO authority or finance access. One User can still
  have independent OrganizationAccess relationships in multiple NGOs.

## Setup and checks

Use `LOCAL-SETUP.md` to provide Python 3.11/3.12, PostgreSQL 16 and the required
environment. Then, with the venv active, from `apps/backend`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py migrate --noinput
python manage.py migrate --check
python manage.py test --verbosity 2
```

Tests cover the original public API, database constraints (including ORM writes
that bypass validation), explicit ownership validation, append-only event paths,
password bounds, competing verified-contact inserts on separate PostgreSQL
connections, legacy upgrade/unused reversal and refusal to drop used security
state. These are not tests of token rotation/reset/MFA workflows; those follow
in later slices. No real data or external delivery is used.

The sandbox validation used Python 3.11 and disposable real PostgreSQL 16.2
provided by `pgserver==0.1.4` installed in the ignored audit venv. pgserver is not
an application dependency. Docker and Python 3.12 execution are not claimed.
CI's existing backend workflow discovers the new tests automatically.

## Rollback safety

Migration `accounts.0003_usercontact_user_auth_epoch_and_more` adds fields/tables;
0001/0002 are untouched. It can reverse only when all new tables are unused and
all users retain default epoch/recovery/hold state. A reverse guard runs before
dropping anything and raises IrreversibleError if the foundation has been used.
It does not delete rows to make a reversal succeed. After use, disable/drain auth,
preserve evidence, and plan a reviewed forward fix or tested backup/restore.
Do not fake migrations or restore a legacy unverified-login bypass.

## Follow-on gates

B1 normalization profile/test vectors precede canonical contact workflows.
B2 vetted TOTP/encryption/key configuration precedes secret-bearing services.
B3 action/assurance policy precedes protected NGO/platform integration.
Operational provider, privacy/retention, assisted recovery and deployment gates
are unchanged. PWC-03A.2 is a separate assignment, not started here.

## Validation evidence — 23 October 2026

- `pip check`: no broken requirements.
- Django `check`: zero issues.
- `makemigrations --check --dry-run`: no changes detected.
- Fresh PostgreSQL migrations and `migrate --check`: passed.
- `manage.py test --verbosity 2`: **35/35 passed**, including all 8 existing
  organization/public API tests and 27 foundation/compatibility tests.
- Concurrent verified-contact insert used separate connections/transactions;
  one insert committed, the conflicting insert failed, and both users remained.
- Synthetic legacy upgrade and unused-schema reversal preserved UUIDs, hashes,
  emails and organization relationships. Used records or changed epochs blocked
  destructive reversal without removing data.
- Targeted Python files were formatted with Black as an environment-only tool;
  no formatter/runtime dependency or CI/lint policy was added.
- Initial standalone migration generation warned about absent localhost PG;
  subsequent checks and full application/tests ran against real PostgreSQL.
- No token issuance, rotation, MFA/recovery, delivery or private tenant-API test
  is claimed complete by these data-foundation tests.

Checkout note: the supplied finalized ADR was present but untracked at baseline
`fc7056f`; the previously reported `39fddf9` object was not in this checkout.
The existing ADR was preserved byte-for-byte in a separate documentation commit
before implementation. No history reset/replacement or architecture rewrite was
performed. The active session branch remains `arena/7bcc0d8b-pwc-platform`.
