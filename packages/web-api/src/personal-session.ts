import { ApiClient, ApiError, ScopeState, parseMe } from "./index";
import type { Portal, SessionView, SyntheticTransport } from "./index";
import { HistoricalWorkspaceClient } from "./workspace";

/** Explicit injected test composition only. No ambient fetch, storage, login,
 * domain context, permission claims or production enable switch. */
export class PersonalWorkspaceSession {
  readonly state: ScopeState;
  readonly api: ApiClient;
  readonly history: HistoricalWorkspaceClient;
  private csrf: string | null = null;
  private pending = false;
  constructor(portal: Portal, transport?: SyntheticTransport) {
    this.state = new ScopeState(portal);
    this.api = new ApiClient(
      this.state,
      transport ? { mode: "synthetic-test", transport } : { mode: "disabled" },
    );
    this.history = new HistoricalWorkspaceClient(
      this.state,
      transport,
      () => this.csrf,
    );
    this.state.subscribe(() => {
      this.csrf = null;
    });
  }
  async refresh(): Promise<SessionView> {
    if (this.pending)
      throw new ApiError("conflict", 0, "SESSION_CHECK_PENDING");
    this.pending = true;
    this.state.invalidate("session-invalid");
    try {
      const view = await this.api.request("me", parseMe);
      // Hold and unverified identity are NOT an authenticated domain context.
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
    } catch (error) {
      this.state.invalidate("session-invalid");
      throw error;
    } finally {
      this.pending = false;
    }
  }
  async logout(): Promise<void> {
    // ApiClient purges immediately, even if logout fails. No command replay.
    await this.api.request("logout", () => undefined);
  }
  clear(): void {
    this.state.invalidate("unmount");
  }
}
