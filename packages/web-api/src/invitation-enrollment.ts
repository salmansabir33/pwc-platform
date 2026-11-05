import {
  ApiClient,
  ApiError,
  ScopeState,
  StaleResponseError,
  normalizeError,
} from "./index";
import type { SyntheticTransport } from "./index";

const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const capability = (v: unknown): v is string =>
  typeof v === "string" && /^[A-Za-z0-9_-]{43}$/.test(v);
function record(value: unknown, keys: string[]): Record<string, unknown> {
  if (
    !value ||
    typeof value !== "object" ||
    Array.isArray(value) ||
    Object.keys(value).sort().join() !== keys.sort().join()
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return value as Record<string, unknown>;
}
function expiry(value: unknown, maximum: number) {
  const time = typeof value === "string" ? Date.parse(value) : NaN;
  if (
    !Number.isFinite(time) ||
    time <= Date.now() ||
    time > Date.now() + maximum + 1000
  )
    throw new ApiError("contract", 0, "INVALID_RESPONSE");
  return performance.now() + time - Date.now();
}
/** Scrub before parsing, including invalid/duplicate/query-string credentials. */
export function consumeInvitationLink(
  location: Pick<Location, "hash" | "pathname" | "search">,
  history: Pick<History, "replaceState">,
) {
  const { hash, search, pathname } = location;
  if (hash || search) history.replaceState(null, "", pathname);
  if (!hash || search || hash.length > 256) return null;
  const fields = new URLSearchParams(hash.slice(1));
  if ([...fields.keys()].sort().join() !== "invitation_id,token") return null;
  const id = fields.get("invitation_id"),
    token = fields.get("token");
  return id && uuid.test(id) && capability(token) ? { id, token } : null;
}
export type InvitationSetup = {
  secret: string;
  otpauth_uri: string;
  expires_at: string;
};
/** Explicit composition only. No ambient fetch/storage or live-enable flag. */
export class InvitationEnrollmentClient {
  #link: { id: string; token: string } | null = null;
  #recipient = "";
  #control = "";
  #deadline = Infinity;
  #pending = false;
  #phase: "link" | "proof" | "password" | "mfa" | "complete" = "link";
  #api: ApiClient;
  constructor(
    readonly state: ScopeState,
    private transport?: SyntheticTransport,
  ) {
    this.#api = new ApiClient(
      state,
      transport ? { mode: "synthetic-test", transport } : { mode: "disabled" },
    );
    state.subscribe(() => this.#erase());
  }
  #erase() {
    this.#link = null;
    this.#recipient = "";
    this.#control = "";
    this.#deadline = Infinity;
    this.#phase = "link";
  }
  cancel() {
    this.state.invalidate("unmount", true);
  }
  subscribe(listener: () => void) {
    return this.state.subscribe(listener);
  }
  get phase() {
    return this.#phase;
  }
  get connected() {
    return !!this.transport;
  }
  toJSON() {
    return "InvitationEnrollmentClient(<redacted>)";
  }
  toString() {
    return this.toJSON();
  }
  adopt(link: { id: string; token: string }) {
    this.cancel();
    if (!uuid.test(link.id) || !capability(link.token))
      throw new ApiError("validation", 0, "CHALLENGE_INVALID");
    this.#link = { ...link };
  }
  async #command(
    operation: "request-proof" | "confirm-email" | "password" | "activate",
    extra: object,
    status: number,
    decode: (value: unknown) => void,
  ) {
    if (!this.transport)
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (!this.#link || performance.now() >= this.#deadline) {
      this.cancel();
      throw new ApiError("validation", 0, "CHALLENGE_INVALID");
    }
    if (this.#pending) throw new ApiError("conflict", 0, "ENROLLMENT_PENDING");
    this.#pending = true;
    const ticket = this.state.begin();
    try {
      const csrf = await this.#api.bootstrapCsrf(ticket.signal);
      ticket.assertCurrent();
      const response = await this.transport(
        "/api/v1/auth/web/invitations/" + operation + "/",
        {
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
          body: JSON.stringify({
            invitation_id: this.#link.id,
            token: this.#link.token,
            recipient: this.#recipient,
            ...extra,
          }),
        },
      );
      const value: unknown = await response.json().catch(() => undefined);
      ticket.assertCurrent();
      if (!response.ok) {
        if ([401, 403].includes(response.status)) this.cancel();
        throw normalizeError(
          response.status,
          value,
          response.headers.get("Retry-After"),
        );
      }
      if (response.status !== status)
        throw new ApiError("contract", response.status, "INVALID_RESPONSE");
      decode(value);
    } catch (error) {
      if (
        operation === "activate" &&
        !(error instanceof ApiError && error.status >= 400)
      )
        this.cancel();
      if (error instanceof ApiError || error instanceof StaleResponseError)
        throw error;
      ticket.assertCurrent();
      throw new ApiError("network", 0, "ENROLLMENT_RESULT_UNCERTAIN");
    } finally {
      ticket.finish();
      this.#pending = false;
    }
  }
  requestProof(recipient: string) {
    if (this.#pending)
      return Promise.reject(new ApiError("conflict", 0, "ENROLLMENT_PENDING"));
    if (!recipient.trim() || recipient.length > 254)
      return Promise.reject(new ApiError("validation", 0, "VALIDATION_ERROR"));
    this.#recipient = recipient;
    return this.#command("request-proof", {}, 202, (value) => {
      if (record(value, ["status"]).status !== "accepted")
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      this.#phase = "proof";
    });
  }
  confirmEmail(proof: string) {
    return this.#command("confirm-email", { proof }, 200, (value) => {
      const row = record(value, ["status", "enrollment_control", "expires_at"]);
      if (
        row.status !== "email_verified" ||
        !capability(row.enrollment_control)
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      this.#deadline = expiry(row.expires_at, 86_400_000);
      this.#control = row.enrollment_control;
      this.#phase = "password";
    });
  }
  async setPassword(password: string): Promise<InvitationSetup> {
    if (this.#phase !== "password" || !this.#control)
      throw new ApiError("validation", 0, "CHALLENGE_INVALID");
    let result!: InvitationSetup;
    await this.#command(
      "password",
      { enrollment_control: this.#control, password },
      200,
      (value) => {
        const row = record(value, [
          "status",
          "secret",
          "otpauth_uri",
          "expires_at",
        ]);
        if (
          row.status !== "mfa_required" ||
          typeof row.secret !== "string" ||
          !/^[A-Z2-7]{32}$/.test(row.secret) ||
          typeof row.otpauth_uri !== "string"
        )
          throw new ApiError("contract", 0, "INVALID_RESPONSE");
        const uri = new URL(row.otpauth_uri);
        if (
          uri.protocol !== "otpauth:" ||
          uri.hostname !== "totp" ||
          uri.searchParams.get("secret") !== row.secret ||
          uri.searchParams.get("issuer") !== "PWC"
        )
          throw new ApiError("contract", 0, "INVALID_RESPONSE");
        this.#deadline = Math.min(
          this.#deadline,
          expiry(row.expires_at, 300_000),
        );
        this.#phase = "mfa";
        result = {
          secret: row.secret,
          otpauth_uri: row.otpauth_uri,
          expires_at: row.expires_at as string,
        };
      },
    );
    return result;
  }
  async activate(code: string): Promise<string[]> {
    if (this.#phase !== "mfa" || !this.#control)
      throw new ApiError("validation", 0, "CHALLENGE_INVALID");
    let codes: string[] = [];
    await this.#command(
      "activate",
      { enrollment_control: this.#control, code },
      201,
      (value) => {
        const row = record(value, ["status", "recovery_codes"]);
        if (
          row.status !== "complete" ||
          !Array.isArray(row.recovery_codes) ||
          row.recovery_codes.length !== 10 ||
          !row.recovery_codes.every(capability) ||
          new Set(row.recovery_codes).size !== 10
        )
          throw new ApiError("contract", 0, "INVALID_RESPONSE");
        codes = [...row.recovery_codes];
        this.#erase();
        this.#phase = "complete";
      },
    );
    return codes;
  }
}
