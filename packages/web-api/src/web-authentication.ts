import {
  ApiError,
  ScopeState,
  StaleResponseError,
  classifyLogin,
  normalizeError,
} from "./index";
import type { ContractSchemas, SyntheticTransport } from "./index";

type Preauth = ContractSchemas["Preauth"];
export type WebLoginResult =
  { kind: "session" } | { kind: "mfa"; preauth: Preauth };
/** Fixed browser issuance only. Not an extension to the original six-operation
 * foundation client, native allowlists, or a production transport enable switch. */
export class WebAuthenticationClient {
  constructor(
    private state: ScopeState,
    private transport?: SyntheticTransport,
  ) {}
  async issue(
    body: ContractSchemas["Login"],
    csrf: string,
  ): Promise<WebLoginResult> {
    const { status, payload } = await this.post("web/login/", body, csrf);
    const classified = classifyLogin(status, payload);
    if (classified.kind === "session") return { kind: "session" };
    const raw = payload as Preauth;
    if (
      Object.keys(raw).sort().join(",") !==
        "challenge_id,expires_in,preauth_control,status" ||
      !Number.isSafeInteger(raw.expires_in) ||
      raw.expires_in <= 0 ||
      raw.expires_in > 300 ||
      raw.preauth_control.length > 1024
    )
      throw new ApiError("contract", 0, "INVALID_RESPONSE");
    return { kind: "mfa", preauth: { ...raw } };
  }
  async confirm(
    body: ContractSchemas["MfaLogin"],
    csrf: string,
  ): Promise<void> {
    const { status, payload } = await this.post("web/mfa/confirm/", body, csrf);
    if (classifyLogin(status, payload).kind !== "session")
      throw new ApiError("contract", status, "INVALID_RESPONSE");
  }
  private async post(
    path: "web/login/" | "web/mfa/confirm/",
    body: ContractSchemas["Login"] | ContractSchemas["MfaLogin"],
    csrf: string,
  ) {
    if (!this.transport)
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (!/^[a-zA-Z0-9]{64}$/.test(csrf))
      throw new ApiError("csrf", 0, "CSRF_REQUIRED");
    const active = this.state.begin();
    try {
      const response = await this.transport("/api/v1/auth/" + path, {
        method: "POST",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
        signal: active.signal,
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "X-CSRFToken": csrf,
        },
        body: JSON.stringify(body),
      });
      const payload: unknown = await response.json().catch(() => undefined);
      active.assertCurrent();
      if (!response.ok)
        throw normalizeError(
          response.status,
          payload,
          response.headers.get("Retry-After"),
        );
      if (![200, 202].includes(response.status))
        throw new ApiError("contract", response.status, "INVALID_RESPONSE");
      return { status: response.status, payload };
    } catch (error) {
      if (error instanceof ApiError || error instanceof StaleResponseError)
        throw error;
      active.assertCurrent();
      throw new ApiError("network", 0, "AUTH_RESULT_UNCERTAIN");
    } finally {
      active.finish();
    }
  }
}
