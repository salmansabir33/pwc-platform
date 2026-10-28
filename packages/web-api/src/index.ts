import {
  browserOperations,
  contractVersion,
} from "../../api-contracts/generated/browser-operations";
import type {
  components,
  operations as WireOperations,
} from "../../api-contracts/generated/schema";
export { contractVersion };
export type ContractSchemas = components["schemas"];
/** Check checked-artifact compatibility, not a fictitious HTTP version header. */
export function assertContractVersion(version: string): void {
  if (version !== contractVersion)
    throw new ApiError("contract", 0, "CONTRACT_VERSION_MISMATCH");
}

/** W1 transport infrastructure only: applications cannot enable live network access. */
export type Portal = "ngo" | "ops";
export type Scope = Readonly<{
  principalId: string;
  sessionId: string;
  organizationId: string | null;
  registryVersion: string;
  revision: string;
}>;
export type Invalidation =
  | "logout"
  | "session-invalid"
  | "access-denied"
  | "context-switch"
  | "security-rotation"
  | "remote"
  | "visibility"
  | "unmount";
export class StaleResponseError extends Error {
  constructor() {
    super("Request is no longer current.");
    this.name = "StaleResponseError";
  }
}

/** Memory-only active-context cache. Scope IDs are partition keys, NEVER authority. */
export class ScopeState {
  private epoch = 0;
  private scope: Scope | null = null;
  private cache = new Map<string, unknown>();
  private controllers = new Set<AbortController>();
  private listeners = new Set<(reason: Invalidation) => void>();
  constructor(readonly portal: Portal) {}
  get currentScope(): Scope | null {
    return this.scope;
  }
  get generation(): number {
    return this.epoch;
  }
  subscribe(fn: (reason: Invalidation) => void): () => void {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }
  invalidate(reason: Invalidation, preserveIdentity = false): void {
    this.epoch++;
    this.controllers.forEach((c) => c.abort());
    this.controllers.clear();
    this.cache.clear();
    if (!preserveIdentity) this.scope = null;
    this.listeners.forEach((fn) => fn(reason));
  }
  switchScope(next: Scope): void {
    this.invalidate("context-switch");
    this.scope = Object.freeze({ ...next });
  }
  begin() {
    const epoch = this.epoch;
    const controller = new AbortController();
    this.controllers.add(controller);
    return {
      owner: this,
      signal: controller.signal,
      assertCurrent: () => {
        if (epoch !== this.epoch || controller.signal.aborted)
          throw new StaleResponseError();
      },
      finish: () => {
        this.controllers.delete(controller);
      },
    };
  }
  private key(operation: string): string {
    return JSON.stringify([
      this.portal,
      this.scope?.principalId,
      this.scope?.sessionId,
      this.scope?.organizationId,
      this.scope?.registryVersion,
      this.scope?.revision,
      this.epoch,
      operation,
    ]);
  }
  set<T>(key: string, value: T, ticket: ReturnType<ScopeState["begin"]>): void {
    if (ticket.owner !== this) throw new StaleResponseError();
    ticket.assertCurrent();
    if (!this.scope) throw new StaleResponseError();
    this.cache.set(this.key(key), structuredClone(value));
  }
  get<T>(key: string): T | undefined {
    const value = this.cache.get(this.key(key));
    return value === undefined ? undefined : (structuredClone(value) as T);
  }
}

export type ErrorKind =
  | "disabled"
  | "csrf"
  | "session"
  | "forbidden"
  | "not-found"
  | "conflict"
  | "rate-limit"
  | "server"
  | "validation"
  | "network"
  | "contract";
export class ApiError extends Error {
  constructor(
    readonly kind: ErrorKind,
    readonly status: number,
    readonly code: string,
    readonly reference?: string,
    readonly retryAfterSeconds?: number,
  ) {
    // Never render/log raw response messages or bodies (they may contain PII).
    super(`Request could not be completed (${kind}).`);
    this.name = "ApiError";
  }
}
const record = (v: unknown): v is Record<string, unknown> =>
  v !== null && typeof v === "object" && !Array.isArray(v);
const safeCode = (v: unknown): string =>
  typeof v === "string" && /^[A-Za-z][A-Za-z0-9_]{0,63}$/.test(v)
    ? v
    : "REQUEST_FAILED";
const safeReference = (v: unknown): string | undefined =>
  typeof v === "string" && /^[a-zA-Z0-9-]{1,64}$/.test(v) ? v : undefined;
export function normalizeError(
  status: number,
  body: unknown,
  retry: string | null = null,
): ApiError {
  const envelope =
    record(body) && record(body.error) ? body.error : record(body) ? body : {};
  const kind: ErrorKind =
    status === 401
      ? "session"
      : status === 403
        ? "forbidden"
        : status === 404
          ? "not-found"
          : status === 409
            ? "conflict"
            : status === 429
              ? "rate-limit"
              : status >= 500
                ? "server"
                : "validation";
  const seconds = retry && /^\d{1,6}$/.test(retry) ? Number(retry) : undefined;
  return new ApiError(
    kind,
    status,
    safeCode(envelope.code),
    safeReference(envelope.request_id ?? envelope.correlation_id),
    seconds,
  );
}

export type HoldState = "clear" | "restricted" | "review_required";
export type SessionView = Readonly<{
  userId: string;
  sessionId: string;
  hold: HoldState;
  emailVerified: boolean;
}>;
export type LoginView =
  | { kind: "preauth"; expiresIn: number }
  | { kind: "session"; userId: string; sessionId: string; hold: HoldState };
const uuid = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
function sessionEnvelope(v: unknown) {
  if (
    !record(v) ||
    !record(v.user) ||
    !record(v.session) ||
    !uuid(v.user.id) ||
    !uuid(v.session.id) ||
    typeof v.recovery_hold_state !== "string" ||
    !["clear", "restricted", "review_required"].includes(v.recovery_hold_state)
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return {
    userId: v.user.id,
    sessionId: v.session.id,
    hold: v.recovery_hold_state as HoldState,
  };
}
export function parseMe(v: unknown): SessionView {
  const envelope = sessionEnvelope(v);
  if (!record(v) || typeof v.email_verified !== "boolean")
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return { ...envelope, emailVerified: v.email_verified };
}
/** Redacted flow classification for synthetic tests; contains no preauth controls/proofs. */
export function classifyLogin(status: number, v: unknown): LoginView {
  if (
    status === 202 &&
    record(v) &&
    v.status === "mfa_required" &&
    uuid(v.challenge_id) &&
    typeof v.preauth_control === "string" &&
    v.preauth_control.length > 0 &&
    typeof v.expires_in === "number" &&
    v.expires_in > 0
  )
    return { kind: "preauth", expiresIn: v.expires_in };
  if (status !== 200)
    throw new ApiError("contract", status, "INVALID_RESPONSE");
  return { kind: "session", ...sessionEnvelope(v) };
}
export function recoveryDisposition(
  hold: HoldState,
): "none" | "fresh-pre-hold-factor" | "review-required" {
  return hold === "clear"
    ? "none"
    : hold === "restricted"
      ? "fresh-pre-hold-factor"
      : "review-required";
}
export function parseCsrf(v: unknown): string {
  if (
    !record(v) ||
    typeof v.csrf_token !== "string" ||
    !/^[a-zA-Z0-9]{64}$/.test(v.csrf_token)
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return v.csrf_token;
}
// Generated from canonical backend contracts; deliberately retains only W1's six
// operations. No synthetic NGO or mobile issuance/refresh command is enabled.
const operations = browserOperations;
export type Operation = keyof typeof operations;
type RequestBody<O extends keyof WireOperations> = [
  NonNullable<WireOperations[O]["requestBody"]>,
] extends [never]
  ? never
  : NonNullable<WireOperations[O]["requestBody"]> extends {
        content: { "application/json": infer Body };
      }
    ? Body
    : never;
type Bodies = { [O in Operation]: RequestBody<O> };
export type SyntheticTransport = (
  input: string,
  init: RequestInit,
) => Promise<Response>;
// Explicit injection for synthetic tests only; no ambient fetch fallback or env switch.
type TransportConfig =
  | { mode: "disabled" }
  | { mode: "synthetic-test"; transport: SyntheticTransport };
export class ApiClient {
  private csrf: string | null = null;
  private unsafePending = false;
  constructor(
    readonly state: ScopeState,
    private config: TransportConfig = { mode: "disabled" },
  ) {
    state.subscribe(() => {
      this.csrf = null;
    });
  }
  async bootstrapCsrf(signal?: AbortSignal): Promise<string> {
    const generation = this.state.generation;
    const token = await this.request("csrf", parseCsrf, undefined, signal);
    if (generation !== this.state.generation || signal?.aborted)
      throw new StaleResponseError();
    this.csrf = token;
    return token;
  }
  async request<O extends Operation, T>(
    operation: O,
    decode: (v: unknown) => T,
    body?: Bodies[O],
    signal?: AbortSignal,
  ): Promise<T> {
    // Logout must purge local data even when a request cannot be issued.
    // Retain only the pre-purge CSRF value long enough to send an eligible logout.
    const csrf = this.csrf;
    if (operation === "logout") this.state.invalidate("logout");
    if (this.config.mode === "disabled")
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (!Object.hasOwn(operations, operation))
      throw new ApiError("contract", 0, "UNKNOWN_OPERATION");
    const endpoint = operations[operation];
    const unsafe = endpoint.method !== "GET";
    if (unsafe && !csrf) throw new ApiError("csrf", 0, "CSRF_REQUIRED");
    if (unsafe && this.unsafePending)
      throw new ApiError("conflict", 0, "SECURITY_COMMAND_PENDING");
    if (!unsafe && body !== undefined)
      throw new ApiError("contract", 0, "UNEXPECTED_BODY");
    const headers: Record<string, string> = { Accept: "application/json" };
    if (unsafe) {
      headers["Content-Type"] = "application/json";
      headers["X-CSRFToken"] = csrf!;
      this.unsafePending = true;
    }
    const active = this.state.begin();
    try {
      const combinedSignal = signal
        ? AbortSignal.any([active.signal, signal])
        : active.signal;
      if (combinedSignal.aborted) throw new StaleResponseError();
      const response = await this.config.transport(
        "/api/v1/auth/" + endpoint.path,
        {
          method: endpoint.method,
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          referrerPolicy: "no-referrer",
          headers,
          signal: combinedSignal,
          ...(unsafe ? { body: JSON.stringify(body ?? {}) } : {}),
        },
      );
      active.assertCurrent();
      if (combinedSignal.aborted) throw new StaleResponseError();
      let payload: unknown;
      if (response.status !== 204) {
        try {
          payload = await response.json();
        } catch {
          payload = undefined;
        }
      }
      active.assertCurrent();
      if (combinedSignal.aborted) throw new StaleResponseError();
      if (!response.ok) {
        const error = normalizeError(
          response.status,
          payload,
          response.headers.get("Retry-After"),
        );
        if (response.status === 401) this.state.invalidate("session-invalid");
        else if (response.status === 403 || response.status === 409)
          this.state.invalidate("access-denied");
        throw error;
      }
      if (operation === "logout" && response.status !== 204)
        throw new ApiError("contract", response.status, "INVALID_RESPONSE");
      let result: T;
      try {
        result = decode(payload);
      } catch {
        throw new ApiError("contract", response.status, "INVALID_RESPONSE");
      } finally {
        // The backend already reported success. Rotation is not conditional on
        // a well-formed payload or a successful decoder. Never invalidate a
        // different/newer identity if the decoder itself changes scope.
        active.assertCurrent();
        if (operation === "stepUp" || operation === "clearHold")
          this.state.invalidate("security-rotation", true);
      }
      return result;
    } catch (error) {
      if (error instanceof ApiError || error instanceof StaleResponseError)
        throw error;
      active.assertCurrent();
      if (signal?.aborted) throw new StaleResponseError();
      throw new ApiError("network", 0, "NETWORK_UNAVAILABLE");
    } finally {
      active.finish();
      if (unsafe) this.unsafePending = false;
    }
  }
}
export function createFoundationRuntime(portal: Portal) {
  const state = new ScopeState(portal);
  return Object.freeze({ state, api: new ApiClient(state) });
}

export function connectInvalidationChannel(state: ScopeState): () => void {
  if (typeof BroadcastChannel === "undefined") return () => {};
  let channel: BroadcastChannel;
  try {
    channel = new BroadcastChannel("pwc-session-invalidation");
  } catch {
    return () => {};
  }
  channel.onmessage = (event: MessageEvent<unknown>) => {
    if (event.data === "session-invalidated") state.invalidate("remote");
  };
  const unsubscribe = state.subscribe((reason) => {
    if (reason === "logout" || reason === "session-invalid")
      channel.postMessage("session-invalidated");
  });
  return () => {
    unsubscribe();
    channel.close();
  };
}

export {
  PublicDirectoryClient,
  HistoricalWorkspaceClient,
  parseDirectory,
  parseWorkspace,
  parseWorkspaceDetail,
} from "./workspace";
export type {
  DirectoryGateway,
  DirectoryFilter,
  DirectoryPage,
  WorkspaceGateway,
  WorkspacePage,
  WorkspaceDetail,
  WorkspaceApplication,
} from "./workspace";

export { PersonalWorkspaceSession } from "./personal-session";
export { OperationsPolicyClient } from "./operations-policy";
