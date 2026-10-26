"""Narrow wire annotations for function views; public fields derive from DRF.

No runtime imports by authentication/authorization code. Schemas describe existing
behavior, not authority or availability. See the 03C runbook before updating.
"""
from copy import deepcopy
from django.conf import settings
from rest_framework import serializers
from organizations.views import PublicOrganizationSerializer

VERSION = "1.0.0"
S = {"type": "string"}
UUID = {"type": "string", "format": "uuid"}
DATE = {"type": "string", "format": "date-time"}
SECRET = {"type": "string", "minLength": 1, "x-sensitive": True}
BOOL = {"type": "boolean"}
INT = {"type": "integer", "minimum": 0}


def ref(name):
    return {"$ref": "#/components/schemas/" + name}


def obj(properties, optional=()):
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional],
            "additionalProperties": False}


def arr(item):
    return {"type": "array", "items": item}


def enum(*values):
    return {"type": "string", "enum": list(values)}


def schemas():
    hold = enum("clear", "restricted", "review_required")
    session = obj({"id": UUID, "absolute_expires_at": DATE, "idle_expires_at": DATE,
                   "assurance": obj({"method": S, "last_mfa_at": {"anyOf": [DATE, {"type": "null"}]}})})
    base = {"user": obj({"id": UUID, "preferred_language": S}),
            "session": session, "recovery_hold_state": hold}
    result = {
        "Empty": obj({}),
        "Health": obj({"status": enum("ok"), "service": enum("pwc-api")}),
        "AuthError": obj({"error": obj({"code": S, "message": S,
            "field_errors": {"type": "object", "additionalProperties": arr(S)}, "request_id": UUID})}),
        "ContextError": obj({"error": obj({"code": S, "correlation_id": UUID})}),
        "PublicError": obj({"detail": S}),
        "Csrf": obj({"csrf_token": {"type": "string", "pattern": "^[a-zA-Z0-9]{64}$", "x-sensitive": True}}),
        "FlowRequest": obj({"email": S}),
        "FlowResend": obj({"flow_id": UUID, "flow_control": SECRET}),
        "RegistrationConfirm": obj({"flow_id": UUID, "proof": SECRET, "password": SECRET}),
        "ResetConfirm": obj({"flow_id": UUID, "proof": SECRET, "new_password": SECRET}),
        "FlowAccepted": obj({"status": enum("accepted"), "flow_id": UUID, "flow_control": SECRET, "expires_in": INT}),
        "ResendAccepted": obj({"status": enum("accepted")}),
        "Verified": obj({"status": enum("verified")}),
        "Login": obj({"email": S, "password": SECRET,
                      "device_label": {"type": "string", "maxLength": 100}}, ("device_label",)),
        "Refresh": obj({"refresh_token": SECRET}),
        "SessionEnvelope": obj(base),
        "Me": obj(dict(base, email_verified=BOOL)),
        "MobileSession": obj(dict(base, access_token=SECRET, token_type=enum("Bearer"),
                                   expires_in=INT, refresh_token=SECRET, refresh_expires_at=DATE)),
        "Preauth": obj({"status": enum("mfa_required"), "challenge_id": UUID,
                        "preauth_control": SECRET, "expires_in": INT}),
        "MfaLogin": obj({"challenge_id": UUID, "preauth_control": SECRET,
                         "method": enum("totp", "recovery_code"), "code": SECRET}),
        "Sessions": obj({"results": arr(obj({"id": UUID, "device_label": S,
            "transport": enum("web", "mobile"), "created_at": DATE,
            "last_interactive_at": DATE, "is_current": BOOL}))}),
        "ProofCommand": obj({"assurance_proof": SECRET}),
        "MfaStatus": obj({"enabled": BOOL, "pending": BOOL, "recovery_hold_state": hold}),
        "IntentRequest": {"oneOf": [
            obj({"operation": enum("mfa.enroll", "mfa.remove", "mfa.recovery_codes.rotate", "sessions.logout_all", "recovery_hold.clear"),
                 "context": obj({"kind": enum("personal"), "id": UUID}), "command": obj({})}),
            obj({"operation": enum("sessions.revoke"), "context": obj({"kind": enum("personal"), "id": UUID}),
                 "command": obj({"session_id": UUID}), "object_id": UUID}, ("object_id",))]},
        "Intent": obj({"intent_id": UUID, "expires_at": DATE, "required_methods": arr(enum("password", "totp"))}),
        "StepUp": obj({"intent_id": UUID, "password": SECRET, "totp_code": S}, ("totp_code",)),
        "ClearHold": obj({"intent_id": UUID, "password": SECRET, "totp_code": S}),
        "Assurance": obj({"assurance_proof": SECRET, "expires_at": DATE}),
        "Enrollment": obj({"enrollment_id": UUID, "secret": SECRET, "otpauth_uri": SECRET, "expires_at": DATE}),
        "EnrollmentConfirm": obj({"enrollment_id": UUID, "code": S}),
        "RecoveryCodes": obj({"recovery_codes": arr(SECRET)}),
        "Activation": obj({"status": enum("active"), "recovery_codes": arr(SECRET)}),
        "Context": obj({"kind": enum("ngo"), "organization_id": UUID}),
        "Discovery": obj({"results": arr(obj({"kind": enum("ngo"), "organization_id": UUID, "context_revision": INT})),
                          "next_cursor": {"type": ["string", "null"]}}),
        "Capabilities": obj({"context": ref("Context"), "registry_version": enum("ngo_kernel_v1"),
            "context_revision": INT, "actions": arr(enum("ngo.context.enter", "ngo.kernel_settings.read", "ngo.private_stub.read")),
            "earliest_grant_expires_at": DATE}),
        "SyntheticResource": obj({"organization_id": UUID, "probe_code": S, "label": S, "context_revision": INT}),
    }
    # Do not maintain a second public projection field list.
    public = {}
    for name, field in PublicOrganizationSerializer().fields.items():
        if isinstance(field, serializers.UUIDField):
            public[name] = UUID
        elif isinstance(field, serializers.ChoiceField):
            public[name] = enum(*field.choices)
        elif isinstance(field, serializers.CharField):
            public[name] = dict(S, **({"maxLength": field.max_length} if field.max_length else {}))
        else:
            raise ValueError("Unsupported public field; review its contract: " + name)
    result["PublicOrganization"] = obj(public)
    return result


# id, suffix, method, transport, request schema, success status/schema, gate
AUTH = [
    ("csrf", "csrf/", "get", "bootstrap", None, 200, "Csrf", None),
    ("registrationRequest", "registration/request/", "post", "public-proof", "FlowRequest", 202, "FlowAccepted", "flows"),
    ("registrationConfirm", "registration/confirm/", "post", "public-proof", "RegistrationConfirm", 201, "Verified", "flows"),
    ("registrationResend", "registration/resend/", "post", "public-proof", "FlowResend", 202, "ResendAccepted", "flows"),
    ("resetRequest", "password-reset/request/", "post", "public-proof", "FlowRequest", 202, "FlowAccepted", "flows"),
    ("resetConfirm", "password-reset/confirm/", "post", "public-proof", "ResetConfirm", 204, None, "flows"),
    ("resetResend", "password-reset/resend/", "post", "public-proof", "FlowResend", 202, "ResendAccepted", "flows"),
    ("webLogin", "web/login/", "post", "browser-issuance", "Login", 200, "SessionEnvelope", "sessions"),
    ("mobileLogin", "mobile/login/", "post", "native-issuance", "Login", 200, "MobileSession", "sessions"),
    ("mobileRefresh", "mobile/refresh/", "post", "native-refresh", "Refresh", 200, "MobileSession", "sessions"),
    ("me", "me/", "get", "personal", None, 200, "Me", "sessions"),
    ("logout", "logout/", "post", "personal", "Empty", 204, None, "sessions"),
    ("logoutAll", "logout-all/", "post", "personal", "ProofCommand", 204, None, "sessions"),
    ("revokeSession", "sessions/{session_id}/", "delete", "personal", "ProofCommand", 204, None, "sessions"),
    ("sessions", "sessions/", "get", "personal", None, 200, "Sessions", "sessions"),
    ("webMfaConfirm", "web/mfa/confirm/", "post", "browser-preauth", "MfaLogin", 200, "SessionEnvelope", "mfa"),
    ("mobileMfaConfirm", "mobile/mfa/confirm/", "post", "native-preauth", "MfaLogin", 200, "MobileSession", "mfa"),
    ("mfaStatus", "mfa/status/", "get", "personal", None, 200, "MfaStatus", "mfa"),
    ("enrollMfa", "mfa/enrollment/request/", "post", "personal", "ProofCommand", 201, "Enrollment", "mfa"),
    ("confirmMfa", "mfa/enrollment/confirm/", "post", "personal", "EnrollmentConfirm", 200, "Activation", "mfa"),
    ("removeMfa", "mfa/remove/", "post", "personal", "ProofCommand", 204, None, "mfa"),
    ("rotateRecovery", "mfa/recovery-codes/rotate/", "post", "personal", "ProofCommand", 200, "RecoveryCodes", "mfa"),
    ("createIntent", "assurance/intents/", "post", "personal", "IntentRequest", 201, "Intent", "mfa"),
    ("stepUp", "step-up/", "post", "personal", "StepUp", 200, "Assurance", "mfa"),
    ("clearHold", "recovery-hold/clear/", "post", "personal", "ClearHold", 204, None, "mfa"),
]
GATES = {
    "registry": ["PWC_REGISTRY_ENABLED", "PWC_AUTH_SESSIONS_ENABLED"],
    "flows": ["PWC_AUTH_FLOWS_ENABLED"],
    "sessions": ["PWC_AUTH_SESSIONS_ENABLED"],
    "mfa": ["PWC_AUTH_SESSIONS_ENABLED", "PWC_AUTH_MFA_ENABLED"],
    "synthetic": ["PWC_SYNTHETIC_CONTEXT_HTTP_ENABLED", "PWC_SYNTHETIC_AUTHORIZATION_ENABLED"],
}


def response(schema=None, private=True, description="Implemented response"):
    value = {"description": description}
    if schema:
        value["content"] = {"application/json": {"schema": ref(schema)}}
    if private:
        value["headers"] = {
            "Cache-Control": {"schema": {"const": "no-store", "type": "string"}},
            "Referrer-Policy": {"schema": {"const": "no-referrer", "type": "string"}},
        }
    return value


def operation(identifier, transport, request_schema, status, result, gate=None, synthetic=False):
    private = gate is not None or identifier == "csrf"
    errors = "ContextError" if synthetic else "AuthError" if private else "PublicError"
    responses = {str(status): response(result, private)}
    if private:
        for code in (400, 401, 403, 404, 405, 409, 429, 503):
            responses[str(code)] = response(errors)
        responses["429"]["headers"]["Retry-After"] = {"schema": {"type": "string", "pattern": "^[0-9]+$"}, "description": "Optional retry hint, never automatic command replay"}
    else:
        for code in (403, 404, 405):
            responses[str(code)] = response(errors, False)
    responses["default"] = {"description": "Framework/proxy failures can be non-JSON; clients must fail closed without rendering raw bodies",
                            "content": {"text/html": {"schema": S}}}
    return {"operationId": identifier, "summary": identifier,
        "description": "Implemented, not a promise of deployment or authority. " + (
            "Synthetic-only; isolated fixtures and current eligible grants required. Never production NGO functionality." if synthetic else
            "Default-disabled; configuration, direct HTTPS and operational acceptance remain required." if gate else
            "Public projection/liveness or CSRF bootstrap, not private authority."),
        "security": [{"browserCookie": []}, {"mobileBearer": []}] if transport == "personal" else [],
        "x-pwc": {"availability": "synthetic-only" if synthetic else "default-disabled" if gate else "public-implemented",
            "transport": transport, "gates": GATES.get(gate, []),
            "disabled": {"status": 404 if synthetic else 503, "code": "not_found" if synthetic else "AUTH_UNAVAILABLE"} if gate else None,
            "csrf": "required-for-cookie-unsafe" if transport == "personal" else "required" if transport.startswith("browser-") else "conditional-browser" if transport == "public-proof" else "bootstrap" if transport == "bootstrap" else "none",
            "direct_https": identifier != "csrf" if private else False,
            "error_precedence": "transport, method, parsing and configuration guards can precede the nominal disabled response; synthetic HTTP gate hides unsupported methods too",
            "authorization": "backend-only; no role/MFA escalation or NGO/finance inheritance"},
        **({"requestBody": {"required": identifier != "logout", "content": {"application/json": {"schema": ref(request_schema)}}}} if request_schema else {}),
        "responses": responses}


def build():
    paths = {}
    for identifier, suffix, method, transport, request_schema, status, result, gate in AUTH:
        op = operation(identifier, transport, request_schema, status, result, gate)
        if identifier in ("webLogin", "mobileLogin"):
            op["responses"]["202"] = response("Preauth", description="MFA-enabled enrolled account: preauth only, no authenticated session")
        if method != "get" and transport == "personal":
            op["security"][0]["csrfHeader"] = []
        if transport.startswith("browser-"):
            op["security"] = [{"csrfHeader": []}]
        if "{session_id}" in suffix:
            op["parameters"] = [{"in": "path", "name": "session_id", "required": True, "schema": UUID}]
        paths["/api/v1/auth/" + suffix] = {method: op}
    for identifier, suffix, result in [
        ("discoverSyntheticContexts", "me/ngo-contexts/", "Discovery"),
        ("syntheticCapabilities", "ngo-contexts/{organization_uuid}/capabilities/", "Capabilities"),
        ("syntheticPrivateProbe", "ngo-contexts/{organization_uuid}/private-probe/", "SyntheticResource"),
        ("syntheticKernelSettings", "ngo-contexts/{organization_uuid}/kernel-settings/", "SyntheticResource"),
    ]:
        op = operation(identifier, "personal", None, 200, result, "synthetic", True)
        op["parameters"] = ([{"in": "path", "name": "organization_uuid", "required": True, "schema": UUID,
            "description": "Explicit Organization UUID, never a grant. No context headers, selected session tenant, or GET body."}] if "{" in suffix else [
            {"in": "query", "name": "cursor", "schema": S, "description": "Opaque signed scan cursor bound to principal/session; <=50 rows, max age 3600s; not encrypted, not authority, no snapshot guarantee"}])
        op["x-pwc"]["unknown_query"] = "reject"
        for item in op["responses"].values():
            if "headers" in item:
                item["headers"]["Vary"] = {"schema": S, "description": "Cookie, Authorization"}
        head = deepcopy(op)
        head["operationId"] += "Head"
        for item in head["responses"].values():
            item.pop("content", None)
        paths["/api/v1/" + suffix] = {"get": op, "head": head}
    paths["/api/v1/health/"] = {"get": operation("health", "public", None, 200, "Health")}
    for identifier, suffix, result in [("publicOrganizations", "organizations/", "PublicOrganizations"),
                                        ("publicOrganization", "organizations/{pk}/", "PublicOrganization")]:
        op = operation(identifier, "public-drf", None, 200, result)
        op["description"] = "Verified-workspace public projection only; no private records. Unpaginated list; no directory/search/publishing policy approval. DRF session auth may still reject an inactive authenticated principal. HEAD/OPTIONS are framework-supported."
        if "{" in suffix:
            op["parameters"] = [{"in": "path", "name": "pk", "required": True, "schema": UUID}]
        paths["/api/v1/" + suffix] = {"get": op}
    # DRF exposes HEAD/OPTIONS; health is a plain Django method-agnostic view.
    for path, methods in list(paths.items()):
        if path.startswith("/api/v1/organizations/") or path == "/api/v1/health/":
            head = deepcopy(methods["get"])
            head["operationId"] += "Head"
            for item in head["responses"].values(): item.pop("content", None)
            methods["head"] = head
            if "organizations" in path:
                options = operation(methods["get"]["operationId"] + "Options", "public-drf", None, 200, "PublicMetadata")
                if "parameters" in methods["get"]: options["parameters"] = deepcopy(methods["get"]["parameters"])
                methods["options"] = options
            else:
                for verb in ("post", "put", "patch", "delete", "options", "trace"):
                    other = deepcopy(methods["get"])
                    other["operationId"] += verb.title()
                    other["description"] += " Health is method-agnostic; Django CSRF middleware still protects unsafe methods. Use GET for liveness."
                    other["responses"]["403"] = {"description": "Django middleware CSRF rejection may be HTML", "content": {"text/html": {"schema": S}}}
                    methods[verb] = other
    definitions = schemas()
    definitions["PublicMetadata"] = {"type": "object", "description": "DRF SimpleMetadata; not capabilities or authority"}
    definitions["PublicOrganizations"] = arr(ref("PublicOrganization"))
    assert settings.SESSION_COOKIE_NAME == "__Host-pwc_session"
    from organizations.registry_contract import paths as registry_paths, definitions as registry_definitions
    paths.update(registry_paths())
    definitions.update(registry_definitions())
    return {"openapi": "3.1.0", "info": {"title": "PWC implemented API contracts", "version": VERSION,
        "description": "Versioned offline contract of existing Django APIs. No planned routes included. /api/v1 is the API major; info.version is the contract release. No runtime version-header negotiation exists."},
        "servers": [{"url": "/"}], "paths": paths,
        "components": {"securitySchemes": {
            "csrfHeader": {"type": "apiKey", "in": "header", "name": "X-CSRFToken", "description": "Masked CSRF token from bootstrap. Browser unsafe requests only; never a substitute for session or permission."},
            "browserCookie": {"type": "apiKey", "in": "cookie", "name": settings.SESSION_COOKIE_NAME,
                "description": "Host-only Secure HttpOnly Path=/ SameSite=Lax. Exact HTTPS portal, CSRF bootstrap+header for unsafe cookie requests. Never combine with Authorization."},
            "mobileBearer": {"type": "http", "scheme": "bearer", "bearerFormat": "opaque selector.secret (not JWT)",
                "description": "Native only; never browser storage. Exactly one credential transport. Refresh proof is body-only, no browser provenance/cookie/Authorization; single-use rotation, replay revokes family."}}, "schemas": definitions},
        "x-pwc-security": {"web_network": "disabled", "identity": "one personal identity; independent NGO relationships",
            "tenant": "explicit Organization UUID; backend current grants on every request; no finance/admin or Board/staff shortcut",
            "assurance": "personal operation-bound proof, never domain authority; clear restricted hold needs a NEW single-use captured pre-hold factor code; review_required is not self-clearable",
            "rotation": "web successful step-up/hold-clear rotates cookie+CSRF, preserve logical session; bootstrap again",
            "mobile_access_seconds": 300, "refresh": "single-use; uncertain response clears local credentials and requires login; no replay grace",
            "expiry": "mobile 7d idle/30d absolute; NGO web 30m/12h; OPS 15m/8h; GET/status/list/refresh never renew idle",
            "delivery": "registration/reset delivery synthetic-only; no live provider approved",
            "error_codes": {
                "400": ["VALIDATION_ERROR", "CHALLENGE_INVALID", "AMBIGUOUS_CREDENTIALS", "TRANSPORT_NOT_ALLOWED", "invalid_context"],
                "401": ["INVALID_CREDENTIALS", "SESSION_INVALID", "authentication_required"],
                "403": ["CSRF_FAILED", "MFA_REQUIRED", "STEP_UP_REQUIRED", "RECOVERY_RESTRICTED", "recovery_hold", "permission_denied"],
                "404": ["NOT_FOUND", "not_found"], "405": ["METHOD_NOT_ALLOWED", "method_not_allowed"],
                "409": ["STATE_CONFLICT", "state_conflict"], "429": ["RATE_LIMITED"],
                "503": ["AUTH_UNAVAILABLE", "authorization_unavailable"]}}}
