OpenAPI contract is to be generated/approved from backend implementation; no fabricated endpoint promises.

PWC-03A.3: `auth-sessions-v1.fixtures.json` is the synthetic session wire-key/transport fixture, checked against actual responses by the PostgreSQL suite. It is not a generated OpenAPI schema, live credentials or an approved production client. See `docs/runbooks/PWC-03A3-SESSIONS.md` for methods, error precedence, storage and strict refresh/lost-response requirements.

PWC-03A.4: `auth-mfa-v1.fixtures.json` covers the separately enabled MFA preauth/enrollment/assurance wire keys. The 03A.3 fixtures still describe MFA-disabled behavior; when MFA is enabled an enrolled account returns 202 preauth, not a session or a bypass. Neither fixture approves domain authorization.
