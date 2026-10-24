# PWC shared API contracts

PWC-03C establishes `openapi-v1.json` (OpenAPI 3.1, contract release 1.0.0), generated from the implemented route inventory, narrow Django annotations and the existing DRF public serializer. It does not activate any API or approve production use. See [the shared-contract runbook](../../docs/runbooks/PWC-03C-SHARED-API-CONTRACTS.md) for generation, validation, TypeScript/Flutter consumption and remaining gates.

The existing three fixture files below are retained historical behavioral profiles. `examples-v1.json` adds checked synthetic structural request/success/error examples, including registration/reset. `generated/schema.ts` is type-only; `generated/browser-operations.ts` retains only W1's six disabled-runtime operations. Do not hand-edit generated artifacts or use fixtures as credentials.

## Historical fixtures and boundaries

PWC-03A.3: `auth-sessions-v1.fixtures.json` is the synthetic session wire-key/transport fixture, checked against actual responses by the PostgreSQL suite. It is not a generated OpenAPI schema, live credentials or an approved production client. See `docs/runbooks/PWC-03A3-SESSIONS.md` for methods, error precedence, storage and strict refresh/lost-response requirements.

PWC-03A.4: `auth-mfa-v1.fixtures.json` covers the separately enabled MFA preauth/enrollment/assurance wire keys. The 03A.3 fixtures still describe MFA-disabled behavior; when MFA is enabled an enrolled account returns 202 preauth, not a session or a bypass. Neither fixture approves domain authorization.

PWC-03A integration review: registration/reset mutations now require direct
HTTPS too; unreviewed forwarded-host/port/protocol trust fails closed. Successful
web step-up/hold clearance rotates both the cookie and CSRF token, preserving the
logical session/proof binding; bootstrap a new CSRF token before the next unsafe
request. Hold-clear intents require a **new single-use** code from the captured
pre-hold factor, even when the session has recent TOTP. Ordinary non-clearance
step-up can still reuse eligible recent TOTP. The MFA fixture records this
verified distinction. The session fixture's deferred denials are the historical
MFA-disabled profile, not the enabled-MFA behavior of this combined branch.

These historical wire-key examples alone are not a complete client contract.
PWC-03C's canonical schema and additional examples now cover the implemented
registration/reset and personal-security routes, but no live-browser/native
storage/app-link acceptance or password-change/contact-change route is added.
Do not generate clients from the ADR's entire target route catalog. Actual
integration still needs separate approval and operational acceptance.

PWC-03B.2: `ngo-contexts-v1.fixtures.json` is checked against actual synthetic HTTP
responses for discovery, capabilities, private probe and kernel settings. It records
only the approved read surface, strict path/input grammar, minimized keys, no-store
headers and error/cursor semantics. These endpoints are independently default-off;
all existing synthetic eligibility and current-session/grant checks still apply.
It is not generated OpenAPI, a client implementation, grant-management authority or
real NGO/finance approval. See `docs/runbooks/PWC-03B2-CONTEXT-ENFORCEMENT.md`.
