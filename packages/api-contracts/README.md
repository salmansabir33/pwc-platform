OpenAPI contract is to be generated/approved from backend implementation; no fabricated endpoint promises.

PWC-03A.3: `auth-sessions-v1.fixtures.json` is the synthetic session wire-key/transport fixture, checked against actual responses by the PostgreSQL suite. It is not a generated OpenAPI schema, live credentials or an approved production client. See `docs/runbooks/PWC-03A3-SESSIONS.md` for methods, error precedence, storage and strict refresh/lost-response requirements.
