import {
  ApiClient,
  ApiError,
  ScopeState,
  StaleResponseError,
  normalizeError,
} from "./index";
import type { SyntheticTransport } from "./index";

type Purpose = "registration" | "password-reset";
type Flow = {
  id: string;
  control?: string;
  purpose: Purpose;
  deadline: number;
};
export type EnrollmentSecret = {
  secret: string;
  otpauth_uri: string;
  expires_at: string;
};
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const secret = (v: unknown): v is string =>
  typeof v === "string" && v.length > 0 && v.length <= 4096;
function record(v: unknown, keys: string[]): Record<string, unknown> {
  if (
    !v ||
    typeof v !== "object" ||
    Array.isArray(v) ||
    Object.keys(v).sort().join() !== keys.sort().join()
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return v as Record<string, unknown>;
}
function deadline(v: unknown): number {
  const time = typeof v === "string" ? Date.parse(v) : NaN;
  if (
    !Number.isFinite(time) ||
    time <= Date.now() ||
    time > Date.now() + 301_000
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return performance.now() + time - Date.now();
}
/** Existing personal wire contracts only. Explicit injection is test-only; no
 * ambient fetch/provider override, registration invitation or domain grant path. */
export class PersonalEnrollmentClient {
  #flow: Flow | null = null;
  #factor: { id: string; deadline: number } | null = null;
  #pending = false;
  #api: ApiClient;
  constructor(
    readonly state: ScopeState,
    private transport?: SyntheticTransport,
  ) {
    this.#api = new ApiClient(
      state,
      transport ? { mode: "synthetic-test", transport } : { mode: "disabled" },
    );
    state.subscribe(() => {
      this.#flow = null;
      this.#factor = null;
    });
  }
  subscribe(listener: (reason: string) => void) {
    return this.state.subscribe(listener);
  }
  get signedIn() {
    return this.state.currentScope !== null;
  }
  get canResend() {
    return !!this.#flow?.control;
  }
  cancel() {
    this.state.invalidate("unmount", true);
  }
  toJSON() {
    return "PersonalEnrollmentClient(<redacted>)";
  }
  toString() {
    return this.toJSON();
  }
  async #serial<T>(run: () => Promise<T>): Promise<T> {
    if (this.#pending) throw new ApiError("conflict", 0, "ENROLLMENT_PENDING");
    this.#pending = true;
    try {
      return await run();
    } finally {
      this.#pending = false;
    }
  }
  #assertEpoch(epoch: number) {
    if (epoch !== this.state.generation) throw new StaleResponseError();
  }
  async #post(
    path: string,
    body: object,
    status: number,
    epoch: number,
  ): Promise<unknown> {
    if (!this.transport)
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (epoch !== this.state.generation) throw new StaleResponseError();
    const ticket = this.state.begin();
    try {
      const csrf = await this.#api.bootstrapCsrf();
      ticket.assertCurrent();
      const response = await this.transport("/api/v1/auth/" + path, {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
        signal: ticket.signal,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify(body),
      });
      const value: unknown =
        response.status === 204
          ? undefined
          : await response.json().catch(() => undefined);
      ticket.assertCurrent();
      if (!response.ok) {
        if ([401, 403].includes(response.status))
          this.state.invalidate("session-invalid");
        throw normalizeError(
          response.status,
          value,
          response.headers.get("Retry-After"),
        );
      }
      if (response.status !== status)
        throw new ApiError("contract", response.status, "INVALID_RESPONSE");
      return value;
    } catch (e) {
      if (e instanceof ApiError || e instanceof StaleResponseError) throw e;
      ticket.assertCurrent();
      throw new ApiError("network", 0, "ENROLLMENT_RESULT_UNCERTAIN");
    } finally {
      ticket.finish();
    }
  }
  start(purpose: Purpose, email: string): Promise<void> {
    return this.#serial(async () => {
      this.#flow = null;
      if (
        !["registration", "password-reset"].includes(purpose) ||
        !email ||
        [...email].length > 1024
      )
        throw new ApiError("validation", 0, "INVALID_INPUT");
      const epoch = this.state.generation;
      const v = record(
        await this.#post(purpose + "/request/", { email }, 202, epoch),
        ["status", "flow_id", "flow_control", "expires_in"],
      );
      this.#assertEpoch(epoch);
      const max = purpose === "registration" ? 1800 : 900;
      if (
        v.status !== "accepted" ||
        typeof v.flow_id !== "string" ||
        !uuid.test(v.flow_id) ||
        !secret(v.flow_control) ||
        !Number.isSafeInteger(v.expires_in) ||
        (v.expires_in as number) <= 0 ||
        (v.expires_in as number) > max
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      this.#flow = {
        purpose,
        id: v.flow_id,
        control: v.flow_control,
        deadline: performance.now() + (v.expires_in as number) * 1000,
      };
    });
  }
  /** Fragment parsed/scrubbed by the caller; never fetched or auto-confirmed. */
  resume(id: string, purpose: Purpose) {
    if (
      this.#pending ||
      !uuid.test(id) ||
      !["registration", "password-reset"].includes(purpose)
    )
      throw new ApiError("validation", 0, "INVALID_INPUT");
    // Actual link expiry is server-owned. No resend control is recovered from a link.
    this.#flow = {
      id,
      purpose,
      deadline:
        performance.now() + (purpose === "registration" ? 1800 : 900) * 1000,
    };
  }
  #currentFlow() {
    if (!this.#flow || performance.now() >= this.#flow.deadline) {
      this.#flow = null;
      throw new ApiError("validation", 0, "CHALLENGE_INVALID");
    }
    return this.#flow;
  }
  resend(): Promise<void> {
    return this.#serial(async () => {
      const flow = this.#currentFlow();
      if (!flow.control)
        throw new ApiError("validation", 0, "CHALLENGE_INVALID");
      const v = record(
        await this.#post(
          flow.purpose + "/resend/",
          { flow_id: flow.id, flow_control: flow.control },
          202,
          this.state.generation,
        ),
        ["status"],
      );
      if (v.status !== "accepted")
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
    });
  }
  confirm(proof: string, password: string): Promise<void> {
    return this.#serial(async () => {
      const flow = this.#currentFlow();
      if (
        !/^[A-Za-z0-9_-]{43}$/.test(proof) ||
        !password ||
        [...password].length > 128
      )
        throw new ApiError("validation", 0, "INVALID_INPUT");
      // Uncertain responses are not replayed with retained secrets.
      this.#flow = null;
      const epoch = this.state.generation;
      const v = await this.#post(
        flow.purpose + "/confirm/",
        {
          flow_id: flow.id,
          proof,
          ...(flow.purpose === "registration"
            ? { password }
            : { new_password: password }),
        },
        flow.purpose === "registration" ? 201 : 204,
        epoch,
      );
      this.#assertEpoch(epoch);
      if (
        flow.purpose === "registration" &&
        record(v, ["status"]).status !== "verified"
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      this.state.invalidate("security-rotation");
    });
  }
  requestMfa(password: string): Promise<EnrollmentSecret> {
    return this.#serial(async () => {
      const actor = this.state.currentScope;
      if (
        !actor ||
        actor.organizationId !== null ||
        !password ||
        [...password].length > 128
      )
        throw new ApiError("session", 401, "SESSION_REQUIRED");
      let epoch = this.state.generation;
      this.#factor = null;
      const intent = record(
        await this.#post(
          "assurance/intents/",
          {
            operation: "mfa.enroll",
            context: { kind: "personal", id: actor.principalId },
            command: {},
          },
          201,
          epoch,
        ),
        ["intent_id", "expires_at", "required_methods"],
      );
      if (
        typeof intent.intent_id !== "string" ||
        !uuid.test(intent.intent_id) ||
        !Array.isArray(intent.required_methods) ||
        intent.required_methods.join() !== "password"
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      const expires = deadline(intent.expires_at);
      const rawStep = await this.#post(
        "step-up/",
        { intent_id: intent.intent_id, password },
        200,
        epoch,
      );
      this.#assertEpoch(epoch);
      // Successful step-up rotates browser CSRF, including a malformed response.
      this.state.invalidate("security-rotation", true);
      epoch = this.state.generation;
      const step = record(rawStep, ["assurance_proof", "expires_at"]);
      if (
        this.state.currentScope !== actor ||
        !secret(step.assurance_proof) ||
        performance.now() >= expires
      )
        throw new StaleResponseError();
      const proofDeadline = deadline(step.expires_at);
      const value = record(
        await this.#post(
          "mfa/enrollment/request/",
          { assurance_proof: step.assurance_proof },
          201,
          epoch,
        ),
        ["enrollment_id", "secret", "otpauth_uri", "expires_at"],
      );
      if (
        typeof value.enrollment_id !== "string" ||
        !uuid.test(value.enrollment_id) ||
        typeof value.secret !== "string" ||
        !/^[A-Z2-7]{16,128}$/.test(value.secret) ||
        typeof value.otpauth_uri !== "string" ||
        !value.otpauth_uri.startsWith("otpauth://totp/") ||
        value.otpauth_uri.length > 4096 ||
        performance.now() >= proofDeadline
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      this.#assertEpoch(epoch);
      const enrollmentDeadline = deadline(value.expires_at);
      this.#factor = { id: value.enrollment_id, deadline: enrollmentDeadline };
      return {
        secret: value.secret,
        otpauth_uri: value.otpauth_uri,
        expires_at: value.expires_at as string,
      };
    });
  }
  confirmMfa(code: string): Promise<string[]> {
    return this.#serial(async () => {
      const factor = this.#factor;
      this.#factor = null;
      if (
        !factor ||
        performance.now() >= factor.deadline ||
        !/^\d{6}$/.test(code)
      )
        throw new ApiError("validation", 0, "CHALLENGE_INVALID");
      const epoch = this.state.generation;
      const rawValue = await this.#post(
        "mfa/enrollment/confirm/",
        { enrollment_id: factor.id, code },
        200,
        epoch,
      );
      this.#assertEpoch(epoch);
      this.state.invalidate("security-rotation", true);
      const value = record(rawValue, ["status", "recovery_codes"]);
      if (
        value.status !== "active" ||
        !Array.isArray(value.recovery_codes) ||
        value.recovery_codes.length !== 10 ||
        !value.recovery_codes.every(secret) ||
        new Set(value.recovery_codes).size !== 10
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      return value.recovery_codes as string[];
    });
  }
}

/** Consume only existing mail-link vocabulary; strip fragment BEFORE processing.
 * Query-string credentials and arbitrary extra/duplicate fragment fields reject. */
export function consumeEnrollmentLink(
  location: Pick<Location, "hash" | "pathname" | "search">,
  history: Pick<History, "replaceState">,
) {
  const fragment = location.hash;
  if (fragment || location.search)
    history.replaceState(null, "", location.pathname);
  if (!fragment || location.search || fragment.length > 1024) return null;
  const p = new URLSearchParams(fragment.slice(1));
  if ([...p.keys()].sort().join() !== "flow_id,proof,purpose") return null;
  const id = p.get("flow_id"),
    proof = p.get("proof"),
    purpose = p.get("purpose");
  if (
    !id ||
    !uuid.test(id) ||
    !proof ||
    !/^[A-Za-z0-9_-]{43}$/.test(proof) ||
    !["registration", "reset"].includes(purpose ?? "")
  )
    return null;
  return {
    id,
    proof,
    purpose: (purpose === "reset"
      ? "password-reset"
      : "registration") as Purpose,
  };
}
