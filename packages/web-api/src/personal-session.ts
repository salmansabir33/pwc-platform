import {
  ApiClient,
  ApiError,
  ScopeState,
  parseMe,
  connectInvalidationChannel,
} from "./index";
import type {
  ContractSchemas,
  Portal,
  SessionView,
  SyntheticTransport,
} from "./index";
import { HistoricalWorkspaceClient } from "./workspace";
import { WebAuthenticationClient } from "./web-authentication";

type SignIn =
  { kind: "mfa"; expiresIn: number } | { kind: "session"; view: SessionView };
/** Explicit injected composition only. Credentials and preauth stay ephemeral;
 * no ambient fetch/storage, domain context or production enable switch. */
export class PersonalWorkspaceSession {
  readonly state: ScopeState;
  readonly api: ApiClient;
  readonly history: HistoricalWorkspaceClient;
  private readonly authentication: WebAuthenticationClient;
  private csrf: string | null = null;
  private pending = false;
  private preauth: {
    value: ContractSchemas["Preauth"];
    deadline: number;
  } | null = null;
  constructor(portal: Portal, transport?: SyntheticTransport) {
    this.state = new ScopeState(portal);
    this.api = new ApiClient(
      this.state,
      transport ? { mode: "synthetic-test", transport } : { mode: "disabled" },
    );
    this.authentication = new WebAuthenticationClient(this.state, transport);
    this.history = new HistoricalWorkspaceClient(
      this.state,
      transport,
      () => this.csrf,
    );
    this.state.subscribe(() => {
      this.csrf = null;
      this.preauth = null;
    });
  }
  subscribe(listener: () => void): () => void {
    const disconnect = connectInvalidationChannel(this.state);
    const unsubscribe = this.state.subscribe(listener);
    const hide = () => {
      if (document.hidden) this.state.invalidate("visibility");
    };
    const pagehide = () => this.state.invalidate("unmount");
    if (typeof document !== "undefined")
      document.addEventListener("visibilitychange", hide);
    if (typeof window !== "undefined")
      window.addEventListener("pagehide", pagehide);
    return () => {
      disconnect();
      unsubscribe();
      if (typeof document !== "undefined")
        document.removeEventListener("visibilitychange", hide);
      if (typeof window !== "undefined")
        window.removeEventListener("pagehide", pagehide);
    };
  }
  private async serialized<T>(action: () => Promise<T>): Promise<T> {
    if (this.pending)
      throw new ApiError("conflict", 0, "SESSION_CHECK_PENDING");
    this.pending = true;
    try {
      return await action();
    } catch (error) {
      this.state.invalidate("session-invalid");
      throw error;
    } finally {
      this.pending = false;
    }
  }
  private async establish(): Promise<SessionView> {
    const view = await this.api.request("me", parseMe);
    if (view.hold !== "clear" || !view.emailVerified) return view;
    this.state.switchScope({
      principalId: view.userId,
      sessionId: view.sessionId,
      organizationId: null,
      registryVersion: "personal-history-v1",
      revision: "session",
    });
    this.csrf = await this.api.bootstrapCsrf();
    return view;
  }
  async refresh(): Promise<SessionView> {
    return this.serialized(async () => {
      this.state.invalidate("session-invalid");
      return this.establish();
    });
  }
  async login(email: string, password: string): Promise<SignIn> {
    return this.serialized(async () => {
      this.state.invalidate("session-invalid");
      if (
        !email ||
        [...email].length > 1024 ||
        !password ||
        [...password].length > 128
      )
        throw new ApiError("validation", 0, "INVALID_CREDENTIALS");
      const csrf = await this.api.bootstrapCsrf();
      const result = await this.authentication.issue({ email, password }, csrf);
      // Both login and MFA challenge rotate cookie + CSRF on the backend.
      this.state.invalidate("security-rotation");
      if (result.kind === "mfa") {
        const deadline = performance.now() + result.preauth.expires_in * 1000;
        // Rebootstrap against the newly rotated preauth cookie before confirmation.
        this.csrf = await this.api.bootstrapCsrf();
        if (performance.now() >= deadline)
          throw new ApiError("session", 401, "PREAUTH_EXPIRED");
        this.preauth = { value: result.preauth, deadline };
        return {
          kind: "mfa",
          expiresIn: Math.max(
            1,
            Math.floor((deadline - performance.now()) / 1000),
          ),
        };
      }
      return { kind: "session", view: await this.establish() };
    });
  }
  async confirmMfa(
    method: "totp" | "recovery_code",
    code: string,
  ): Promise<SessionView> {
    return this.serialized(async () => {
      const challenge = this.preauth;
      if (!challenge || performance.now() >= challenge.deadline || !this.csrf)
        throw new ApiError("session", 401, "PREAUTH_EXPIRED");
      if (
        !["totp", "recovery_code"].includes(method) ||
        !code ||
        code.length > 1024
      )
        throw new ApiError("validation", 0, "INVALID_PROOF");
      await this.authentication.confirm(
        {
          challenge_id: challenge.value.challenge_id,
          preauth_control: challenge.value.preauth_control,
          method,
          code,
        },
        this.csrf,
      );
      this.state.invalidate("security-rotation");
      return this.establish();
    });
  }
  async logout(): Promise<void> {
    // Purge now, even when the server cannot be reached. Fresh CSRF permits an
    // explicit retry after an uncertain failure; never claim server revocation.
    this.state.invalidate("logout");
    return this.serialized(async () => {
      await this.api.bootstrapCsrf();
      await this.api.request("logout", () => undefined);
    });
  }
  toJSON(): string {
    return "PersonalWorkspaceSession(<redacted>)";
  }
  toString(): string {
    return this.toJSON();
  }
  clear(): void {
    this.state.invalidate("unmount");
  }
}
