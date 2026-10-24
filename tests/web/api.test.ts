import { describe, expect, it, vi } from "vitest";
import {
  ApiClient,
  ApiError,
  ScopeState,
  StaleResponseError,
  classifyLogin,
  createFoundationRuntime,
  normalizeError,
  parseCsrf,
  parseMe,
  recoveryDisposition,
  connectInvalidationChannel,
} from "@pwc/web-api";
import type { Scope } from "@pwc/web-api";
import sessions from "../../packages/api-contracts/auth-sessions-v1.fixtures.json";
import mfa from "../../packages/api-contracts/auth-mfa-v1.fixtures.json";
import contexts from "../../packages/api-contracts/ngo-contexts-v1.fixtures.json";

const userId = "00000000-0000-4000-8000-000000000001";
const sessionId = "00000000-0000-4000-8000-000000000002";
const ngoA = "00000000-0000-4000-8000-00000000000a";
const ngoB = "00000000-0000-4000-8000-00000000000b";
const scope = (organizationId = ngoA): Scope => ({
  principalId: userId,
  sessionId,
  organizationId,
  registryVersion: contexts.registry_version,
  revision: "1",
});
const me = {
  user: { id: userId, preferred_language: "en" },
  session: {
    id: sessionId,
    absolute_expires_at: "2026-10-25T00:00:00Z",
    idle_expires_at: "2026-10-24T15:30:00Z",
    assurance: { method: "password", last_mfa_at: null },
  },
  recovery_hold_state: "clear",
  email_verified: true,
};
const token = "a".repeat(64);
const json = (v: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(v), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
function setup() {
  const state = new ScopeState("ngo");
  const transport =
    vi.fn<(input: string, init: RequestInit) => Promise<Response>>();
  const api = new ApiClient(state, { mode: "synthetic-test", transport });
  return { state, transport, api };
}
function deferred() {
  let resolve!: (r: Response) => void;
  const promise = new Promise<Response>((r) => {
    resolve = r;
  });
  return { promise, resolve };
}

describe("narrow fixture-backed contract parsing (synthetic only)", () => {
  it("tracks the actual me and error wire keys without inventing authority", () => {
    expect(Object.keys(me).sort()).toEqual(
      [...sessions.me_success_keys].sort(),
    );
    expect(parseMe(me)).toEqual({
      userId,
      sessionId,
      hold: "clear",
      emailVerified: true,
    });
    expect(parseMe(me)).not.toHaveProperty("roles");
    expect(sessions.cookie).toMatchObject({
      secure: true,
      httponly: true,
      domain: null,
      path: "/",
    });
    expect(contexts.context).toContain("Explicit path Organization UUID");
  });
  it("keeps enabled-MFA 202 preauth distinct from an established session", () => {
    const preauth = {
      status: "mfa_required",
      challenge_id: sessionId,
      preauth_control: "synthetic-control",
      expires_in: 300,
    };
    expect(Object.keys(preauth).sort()).toEqual([...mfa.preauth_keys].sort());
    expect(classifyLogin(mfa.preauth_status, preauth)).toEqual({
      kind: "preauth",
      expiresIn: 300,
    });
    expect(classifyLogin(200, me)).toMatchObject({ kind: "session", userId });
    expect(() => classifyLogin(202, me)).toThrow(ApiError);
    expect(() => parseMe(preauth)).toThrow(ApiError);
    expect(classifyLogin(202, preauth)).not.toHaveProperty("preauth_control");
  });
  it("never treats review-required as self-clearable, or MFA as NGO permission", () => {
    expect(recoveryDisposition("clear")).toBe("none");
    expect(recoveryDisposition("restricted")).toBe("fresh-pre-hold-factor");
    expect(recoveryDisposition("review_required")).toBe("review-required");
    expect(mfa.hold_clear_requires_new_single_use_totp).toBe(true);
    expect(
      parseMe({ ...me, recovery_hold_state: "review_required" }).hold,
    ).toBe("review_required");
  });
  it.each([
    {},
    { ...me, recovery_hold_state: "admin" },
    { ...me, user: { id: "invalid" } },
    { ...me, email_verified: "yes" },
  ])("fails closed on malformed session responses", (body) => {
    expect(() => parseMe(body)).toThrow(ApiError);
  });
  it.each([
    null,
    {},
    { csrf_token: "short" },
    { csrf_token: "<script>".repeat(8) },
  ])("rejects malformed CSRF responses", (body) =>
    expect(() => parseCsrf(body)).toThrow(ApiError),
  );
});

describe("transport boundaries", () => {
  it("is disabled in both shipped application runtimes and never falls back to fetch", async () => {
    const spy = vi.spyOn(globalThis, "fetch");
    for (const portal of ["ngo", "ops"] as const)
      await expect(
        createFoundationRuntime(portal).api.bootstrapCsrf(),
      ).rejects.toMatchObject({ kind: "disabled" });
    expect(spy).not.toHaveBeenCalled();
  });
  it("bootstraps memory-only CSRF and attaches it to unsafe same-origin JSON requests", async () => {
    const { api, transport } = setup();
    transport
      .mockResolvedValueOnce(json({ csrf_token: token }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    await api.bootstrapCsrf();
    await api.request("logout", () => undefined, {});
    expect(transport.mock.calls[0]?.[0]).toBe("/api/v1/auth/csrf/");
    expect(transport.mock.calls[1]).toEqual([
      "/api/v1/auth/logout/",
      expect.objectContaining({
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        body: "{}",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": token,
        },
      }),
    ]);
    for (const [url, init] of transport.mock.calls) {
      expect(url).toMatch(/^\/api\/v1\/auth\//);
      expect(init.headers).not.toHaveProperty("Authorization");
    }
  });
  it("refuses unsafe requests without CSRF and unknown endpoints without networking", async () => {
    const { api, transport } = setup();
    await expect(
      api.request("logout", () => undefined, {}),
    ).rejects.toMatchObject({ kind: "csrf" });
    // Runtime rejection as well as the closed TypeScript operation union.
    await expect(
      // @ts-expect-error Native/NGO business routes are not registered operations.
      api.request("https://example.invalid/mobile/refresh/", (v) => v),
    ).rejects.toMatchObject({ code: "UNKNOWN_OPERATION" });
    expect(transport).not.toHaveBeenCalled();
  });
  it("does not attach CSRF to GET or permit GET request bodies", async () => {
    const { api, transport } = setup();
    transport.mockResolvedValueOnce(json(me));
    await api.request("me", parseMe);
    expect(transport.mock.calls[0]?.[1].headers).toEqual({
      Accept: "application/json",
    });
    // @ts-expect-error GET operation bodies are forbidden.
    await expect(api.request("me", parseMe, {})).rejects.toMatchObject({
      code: "UNEXPECTED_BODY",
    });
  });
  it("fails safely on HTML success and network failures without echoing response data", async () => {
    const { api, transport } = setup();
    transport
      .mockResolvedValueOnce(new Response("<h1>private</h1>"))
      .mockRejectedValueOnce(new Error("secret internal URL"));
    await expect(api.request("me", parseMe)).rejects.toMatchObject({
      kind: "contract",
      code: "INVALID_RESPONSE",
    });
    await expect(api.request("me", parseMe)).rejects.toMatchObject({
      kind: "network",
      message: "Request could not be completed (network).",
    });
    expect(transport).toHaveBeenCalledTimes(2); // no automatic retry
  });
});

describe("safe API errors and invalidation", () => {
  it.each([
    [401, "session"],
    [403, "forbidden"],
    [404, "not-found"],
    [409, "conflict"],
    [429, "rate-limit"],
    [500, "server"],
    [503, "server"],
  ] as const)(
    "normalizes %i without returning raw messages or field values",
    async (status, kind) => {
      const { api, transport, state } = setup();
      state.switchScope(scope());
      const ticket = state.begin();
      state.set("private", { synthetic: "A" }, ticket);
      ticket.finish();
      transport.mockResolvedValueOnce(
        json(
          {
            error: {
              code: "SESSION_INVALID",
              message: "private email",
              field_errors: { password: "secret" },
              request_id: sessionId,
            },
          },
          status,
          { "Retry-After": "30" },
        ),
      );
      let caught: unknown;
      try {
        await api.request("me", parseMe);
      } catch (error) {
        caught = error;
      }
      expect(caught).toMatchObject({
        status,
        kind,
        reference: sessionId,
        retryAfterSeconds: 30,
      });
      expect(JSON.stringify(caught)).not.toContain("secret");
      expect(JSON.stringify(caught)).not.toContain("private email");
      if ([401, 403, 409].includes(status)) {
        expect(state.currentScope).toBeNull();
        expect(state.get("private")).toBeUndefined();
      }
      expect(transport).toHaveBeenCalledTimes(1);
    },
  );
  it("accepts the separate synthetic authorization envelope and ordinary non-JSON failures", () => {
    const envelope = { code: "permission_denied", correlation_id: sessionId };
    expect(Object.keys(envelope).sort()).toEqual(
      [...contexts.error_keys].sort(),
    );
    expect(normalizeError(403, envelope)).toMatchObject({
      kind: "forbidden",
      reference: sessionId,
    });
    expect(normalizeError(500, "<html>private stack</html>")).toMatchObject({
      kind: "server",
      code: "REQUEST_FAILED",
    });
    expect(
      normalizeError(400, {
        code: "<script>",
        correlation_id: "secret@example.invalid",
      }),
    ).toMatchObject({ code: "REQUEST_FAILED", reference: undefined });
  });
  it("clears state on logout initiation even when server revocation fails", async () => {
    const { api, transport, state } = setup();
    transport.mockResolvedValueOnce(json({ csrf_token: token }));
    await api.bootstrapCsrf();
    state.switchScope(scope()); // scope changes intentionally discard old CSRF
    transport.mockResolvedValueOnce(json({ csrf_token: token }));
    await api.bootstrapCsrf();
    const pending = deferred();
    transport.mockReturnValueOnce(pending.promise);
    const result = api.request("logout", () => undefined, {});
    expect(state.currentScope).toBeNull();
    pending.resolve(json({}, 503));
    await expect(result).rejects.toMatchObject({ kind: "server" });
    await expect(
      api.request("logout", () => undefined, {}),
    ).rejects.toMatchObject({ kind: "csrf" });
  });
});

describe("memory-only context isolation and late response fencing", () => {
  it("clears A on switching to B and rejects an A response even if transport ignores abort", async () => {
    const { api, transport, state } = setup();
    state.switchScope(scope());
    const a = state.begin();
    state.set("roster", { marker: "synthetic A" }, a);
    const pending = deferred();
    transport.mockReturnValueOnce(pending.promise);
    const request = api.request("me", parseMe);
    state.switchScope(scope(ngoB));
    expect(state.get("roster")).toBeUndefined();
    const b = state.begin();
    state.set("roster", { marker: "synthetic B" }, b);
    expect(() => state.set("roster", { marker: "late A" }, a)).toThrow(
      StaleResponseError,
    );
    pending.resolve(json(me));
    await expect(request).rejects.toBeInstanceOf(StaleResponseError);
    expect(state.get("roster")).toEqual({ marker: "synthetic B" });
    expect(a.signal.aborted).toBe(true);
    a.finish();
    b.finish();
  });
  it("rejects an old 401 instead of logging out a newly selected principal", async () => {
    const { api, transport, state } = setup();
    state.switchScope(scope());
    const pending = deferred();
    transport.mockReturnValueOnce(pending.promise);
    const request = api.request("me", parseMe);
    state.switchScope({ ...scope(), principalId: ngoB, sessionId: ngoA });
    pending.resolve(json({}, 401));
    await expect(request).rejects.toBeInstanceOf(StaleResponseError);
    expect(state.currentScope?.principalId).toBe(ngoB);
  });
  it.each(["logout", "session-invalid", "visibility", "remote"] as const)(
    "fences requests and purges private state after %s",
    async (reason) => {
      const { api, transport, state } = setup();
      state.switchScope(scope());
      const pending = deferred();
      transport.mockReturnValueOnce(pending.promise);
      const request = api.request("me", parseMe);
      state.invalidate(reason);
      pending.resolve(json(me));
      await expect(request).rejects.toBeInstanceOf(StaleResponseError);
      expect(state.currentScope).toBeNull();
    },
  );
  it("keeps app caches, identities and CSRF separate even for the same personal identity", () => {
    const ngo = createFoundationRuntime("ngo");
    const ops = createFoundationRuntime("ops");
    ngo.state.switchScope(scope());
    ops.state.switchScope(scope());
    const a = ngo.state.begin();
    ngo.state.set("value", { app: "ngo" }, a);
    expect(ops.state.get("value")).toBeUndefined();
    expect(() => ops.state.set("value", { app: "wrong" }, a)).toThrow(
      StaleResponseError,
    );
    ops.state.invalidate("logout");
    expect(ngo.state.currentScope).not.toBeNull();
    a.finish();
  });
  it("copies cached objects so callers cannot mutate another view by alias", () => {
    const state = new ScopeState("ngo");
    state.switchScope(scope());
    const ticket = state.begin();
    const input = { marker: "A" };
    state.set("x", input, ticket);
    input.marker = "mutated";
    const result = state.get<{ marker: string }>("x")!;
    result.marker = "changed";
    expect(state.get("x")).toEqual({ marker: "A" });
    ticket.finish();
  });
  it("rejects externally cancelled responses without automatic retries", async () => {
    const { api, transport } = setup();
    const pending = deferred();
    transport.mockReturnValueOnce(pending.promise);
    const controller = new AbortController();
    const request = api.request("me", parseMe, undefined, controller.signal);
    controller.abort();
    pending.resolve(json(me));
    await expect(request).rejects.toBeInstanceOf(StaleResponseError);
    expect(transport).toHaveBeenCalledTimes(1);
  });
  it("never restores CSRF after an invalidated bootstrap", async () => {
    const { api, transport, state } = setup();
    const pending = deferred();
    transport.mockReturnValueOnce(pending.promise);
    const bootstrap = api.bootstrapCsrf();
    state.invalidate("logout");
    pending.resolve(json({ csrf_token: token }));
    await expect(bootstrap).rejects.toBeInstanceOf(StaleResponseError);
    await expect(
      api.request("logout", () => undefined, {}),
    ).rejects.toMatchObject({ kind: "csrf" });
  });
  it.each(["stepUp", "clearHold"] as const)(
    "serializes security commands and discards CSRF after %s",
    async (operation) => {
      const { api, transport, state } = setup();
      state.switchScope(scope());
      transport.mockResolvedValueOnce(json({ csrf_token: token }));
      await api.bootstrapCsrf();
      const pending = deferred();
      transport.mockReturnValueOnce(pending.promise);
      const body = {
        intent_id: sessionId,
        password: "synthetic-only",
        totp_code: "000000",
      };
      const request = api.request(operation, (v) => v, body);
      await expect(
        api.request(operation, (v) => v, body),
      ).rejects.toMatchObject({ code: "SECURITY_COMMAND_PENDING" });
      pending.resolve(
        operation === "clearHold"
          ? new Response(null, { status: 204 })
          : json({
              assurance_proof: "synthetic-transient",
              expires_at: "2026-10-24T16:00:00Z",
            }),
      );
      await request;
      expect(state.currentScope?.sessionId).toBe(sessionId);
      await expect(
        api.request(operation, (v) => v, body),
      ).rejects.toMatchObject({ kind: "csrf" });
    },
  );
  it("broadcasts only a non-sensitive invalidation signal and never echoes remote events", () => {
    const posted: unknown[] = [];
    let listener: ((event: MessageEvent) => void) | null = null;
    class Channel {
      set onmessage(fn: (event: MessageEvent) => void) {
        listener = fn;
      }
      postMessage(data: unknown) {
        posted.push(data);
      }
      close = vi.fn();
    }
    vi.stubGlobal("BroadcastChannel", Channel);
    try {
      const state = new ScopeState("ngo");
      const close = connectInvalidationChannel(state);
      state.switchScope(scope());
      state.invalidate("logout");
      expect(posted).toEqual(["session-invalidated"]);
      state.switchScope(scope());
      const receive = listener as unknown as (event: MessageEvent) => void;
      receive(new MessageEvent("message", { data: "session-invalidated" }));
      expect(state.currentScope).toBeNull();
      expect(posted).toHaveLength(1);
      close();
    } finally {
      vi.unstubAllGlobals();
    }
  });
});

describe("additional race and authority boundaries", () => {
  it("fences asynchronous body parsing after a context switch", async () => {
    const { api, transport, state } = setup();
    state.switchScope(scope());
    let resolveBody!: (v: unknown) => void;
    const body = new Promise<unknown>((resolve) => {
      resolveBody = resolve;
    });
    transport.mockResolvedValue({
      ok: true,
      status: 200,
      json: () => body,
    } as Response);
    const request = api.request("me", parseMe);
    await Promise.resolve();
    state.switchScope(scope(ngoB));
    resolveBody(me);
    await expect(request).rejects.toBeInstanceOf(StaleResponseError);
  });
  it("does not invoke transport for an already-cancelled operation", async () => {
    const { api, transport } = setup();
    const controller = new AbortController();
    controller.abort();
    await expect(
      api.request("me", parseMe, undefined, controller.signal),
    ).rejects.toBeInstanceOf(StaleResponseError);
    expect(transport).not.toHaveBeenCalled();
  });
  it.each(["admin", "staff", "superuser", "Board"])(
    "does not turn an untrusted %s response label into authority",
    async (label) => {
      const { api, transport } = setup();
      transport.mockResolvedValueOnce(
        json({ ...me, roles: [label], capabilities: ["finance", "ngo-admin"] }),
      );
      const view = await api.request("me", parseMe);
      expect(Object.keys(view).sort()).toEqual(
        ["userId", "sessionId", "hold", "emailVerified"].sort(),
      );
      expect(view).not.toHaveProperty("capabilities");
      // @ts-expect-error No generic finance endpoint is exposed by the web adapter.
      await expect(api.request("finance", (v) => v)).rejects.toMatchObject({
        code: "UNKNOWN_OPERATION",
      });
      expect(transport).toHaveBeenCalledTimes(1);
    },
  );
  it("purges a cache when registry/context revision changes", () => {
    const state = new ScopeState("ngo");
    state.switchScope(scope());
    const ticket = state.begin();
    state.set("probe", { synthetic: true }, ticket);
    state.switchScope({
      ...scope(),
      registryVersion: "test-next",
      revision: "2",
    });
    expect(state.get("probe")).toBeUndefined();
    expect(() => ticket.assertCurrent()).toThrow(StaleResponseError);
    ticket.finish();
  });
  it("discards CSRF when principal or NGO scope changes", async () => {
    const { api, transport, state } = setup();
    transport.mockResolvedValueOnce(json({ csrf_token: token }));
    await api.bootstrapCsrf();
    state.switchScope(scope(ngoB));
    await expect(
      api.request("logout", () => undefined, {}),
    ).rejects.toMatchObject({ kind: "csrf" });
    expect(transport).toHaveBeenCalledTimes(1);
  });
});
