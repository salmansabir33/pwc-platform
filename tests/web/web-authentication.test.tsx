import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ApiError, PersonalWorkspaceSession } from "@pwc/web-api";
import { PersonalSessionPanel } from "@pwc/web-ui";
import type { PersonalSessionPort } from "@pwc/web-ui";
import { LocaleProvider } from "@pwc/web-i18n";
import { PersonalWorkspace } from "../../apps/ngo-web/src/PersonalWorkspace";
const ID = "00000000-0000-4000-8000-000000000001";
const csrf = () => json({ csrf_token: "a".repeat(64) });
const me = {
  user: { id: ID },
  session: { id: ID },
  recovery_hold_state: "clear",
  email_verified: true,
};
const envelope = {
  user: { id: ID },
  session: { id: ID },
  recovery_hold_state: "clear",
};
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status });
const challenge = {
  status: "mfa_required",
  challenge_id: ID,
  preauth_control: "ephemeral-secret-only",
  expires_in: 300,
};
const EMAIL = "synthetic@example.invalid",
  PASSWORD = "synthetic-test-password";
afterEach(() => vi.useRealTimers());
describe("bounded password/MFA browser integration", () => {
  it("default login/confirmation remain network disabled", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const session = new PersonalWorkspaceSession("ngo");
    await expect(session.login(EMAIL, PASSWORD)).rejects.toMatchObject({
      kind: "disabled",
    });
    await expect(session.confirmMfa("totp", "123456")).rejects.toMatchObject({
      code: "PREAUTH_EXPIRED",
    });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("password sign-in uses fixed cookie/CSRF routes, rereads me and renews rotated CSRF", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(envelope))
      .mockResolvedValueOnce(json(me))
      .mockResolvedValueOnce(csrf());
    const session = new PersonalWorkspaceSession("ngo", transport);
    expect((await session.login(EMAIL, PASSWORD)).kind).toBe("session");
    expect(transport.mock.calls.map((c) => c[0])).toEqual([
      "/api/v1/auth/csrf/",
      "/api/v1/auth/web/login/",
      "/api/v1/auth/me/",
      "/api/v1/auth/csrf/",
    ]);
    expect(transport.mock.calls[1]?.[1]).toMatchObject({
      method: "POST",
      credentials: "same-origin",
      redirect: "error",
      cache: "no-store",
      referrerPolicy: "no-referrer",
      headers: { "X-CSRFToken": "a".repeat(64) },
      body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
    });
    expect(session.state.currentScope?.organizationId).toBeNull();
    expect(JSON.stringify(session)).not.toContain(EMAIL);
    expect(JSON.stringify(session)).not.toContain("a".repeat(64));
  });
  it("does not narrow backend Unicode password or IDNA-input semantics", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(envelope))
      .mockResolvedValueOnce(json(me))
      .mockResolvedValueOnce(csrf());
    const session = new PersonalWorkspaceSession("ngo", transport);
    await session.login("member@مثال.پاکستان", "🧪".repeat(100));
    expect(JSON.parse(transport.mock.calls[1]?.[1].body).password).toBe(
      "🧪".repeat(100),
    );
    expect(JSON.parse(transport.mock.calls[1]?.[1].body).email).toBe(
      "member@مثال.پاکستان",
    );
  });
  it("202 never creates a scope; preauth stays private and needs fresh CSRF plus explicit confirmation", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(challenge, 202))
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(envelope))
      .mockResolvedValueOnce(json(me))
      .mockResolvedValueOnce(csrf());
    const session = new PersonalWorkspaceSession("ngo", transport);
    const result = await session.login(EMAIL, PASSWORD);
    expect(result.kind).toBe("mfa");
    expect(JSON.stringify(result)).not.toContain("ephemeral-secret");
    expect(JSON.stringify(session)).not.toContain("ephemeral-secret");
    expect(session.state.currentScope).toBeNull();
    await session.confirmMfa("totp", "123456");
    expect(transport.mock.calls[3]?.[0]).toBe("/api/v1/auth/web/mfa/confirm/");
    expect(JSON.parse(transport.mock.calls[3]?.[1].body)).toEqual({
      challenge_id: ID,
      preauth_control: challenge.preauth_control,
      method: "totp",
      code: "123456",
    });
    expect(transport.mock.calls[4]?.[0]).toBe("/api/v1/auth/me/");
  });
  it.each(["remote", "logout", "visibility"] as const)(
    "%s clears preauth before any confirmation can leave",
    async (reason) => {
      const transport = vi
        .fn()
        .mockResolvedValueOnce(csrf())
        .mockResolvedValueOnce(json(challenge, 202))
        .mockResolvedValueOnce(csrf());
      const session = new PersonalWorkspaceSession("ngo", transport);
      await session.login(EMAIL, PASSWORD);
      session.state.invalidate(reason);
      await expect(session.confirmMfa("totp", "123456")).rejects.toMatchObject({
        code: "PREAUTH_EXPIRED",
      });
      expect(transport).toHaveBeenCalledTimes(3);
    },
  );
  it("expired challenge is not sent and clock delay does not renew it", async () => {
    const clock = vi.spyOn(performance, "now").mockReturnValue(0);
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(challenge, 202))
      .mockResolvedValueOnce(csrf());
    const session = new PersonalWorkspaceSession("ngo", transport);
    await session.login(EMAIL, PASSWORD);
    clock.mockReturnValue(301000);
    await expect(session.confirmMfa("totp", "123456")).rejects.toMatchObject({
      code: "PREAUTH_EXPIRED",
    });
    expect(transport).toHaveBeenCalledTimes(3);
  });
  it("confirmation of recovery login renders a hold, not history authority", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(challenge, 202))
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(
        json({ ...envelope, recovery_hold_state: "restricted" }),
      )
      .mockResolvedValueOnce(
        json({ ...me, recovery_hold_state: "restricted" }),
      );
    const session = new PersonalWorkspaceSession("ngo", transport);
    await session.login(EMAIL, PASSWORD);
    expect(
      (await session.confirmMfa("recovery_code", "synthetic-recovery")).hold,
    ).toBe("restricted");
    expect(session.state.currentScope).toBeNull();
    expect(transport).toHaveBeenCalledTimes(5);
  });
  it("uncertain login is never retried or assumed authenticated", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockRejectedValueOnce(new TypeError("private transport detail"));
    const session = new PersonalWorkspaceSession("ngo", transport);
    await expect(session.login(EMAIL, PASSWORD)).rejects.toMatchObject({
      kind: "network",
    });
    expect(transport).toHaveBeenCalledTimes(2);
    expect(session.state.currentScope).toBeNull();
  });
  it("serializes sign-in and drops a late response after remote invalidation", async () => {
    let resolve!: (r: Response) => void;
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockImplementationOnce(
        () =>
          new Promise<Response>((r) => {
            resolve = r;
          }),
      );
    const session = new PersonalWorkspaceSession("ngo", transport);
    const pending = session.login(EMAIL, PASSWORD);
    await waitFor(() => expect(transport).toHaveBeenCalledTimes(2));
    await expect(session.login(EMAIL, PASSWORD)).rejects.toMatchObject({
      kind: "conflict",
    });
    session.state.invalidate("remote");
    resolve(json(envelope));
    await expect(pending).rejects.toThrow();
    expect(session.state.currentScope).toBeNull();
  });
  it("clears form passwords immediately, keeps 202 restricted, cancels without storing controls", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json(challenge, 202))
      .mockResolvedValueOnce(csrf());
    const session = new PersonalWorkspaceSession("ngo", transport);
    render(
      <LocaleProvider>
        <PersonalWorkspace session={session} />
      </LocaleProvider>,
    );
    const u = userEvent.setup();
    await u.type(screen.getByLabelText("Email", { exact: true }), EMAIL);
    await u.type(screen.getByLabelText("Password", { exact: true }), PASSWORD);
    await u.click(screen.getByRole("button", { name: "Sign in" }));
    expect(
      await screen.findByText(
        "Second factor required. This is not an authenticated session.",
      ),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Refresh history" }),
    ).toBeDisabled();
    expect(document.body.textContent).not.toContain(challenge.preauth_control);
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
    await u.click(screen.getByRole("button", { name: "Cancel sign-in" }));
    expect(screen.getByLabelText("Password", { exact: true })).toHaveValue("");
    await expect(session.confirmMfa("totp", "123456")).rejects.toMatchObject({
      code: "PREAUTH_EXPIRED",
    });
  });
  it("failed logout explicitly reports uncertainty and allows user retry, never claims revocation", async () => {
    const session: PersonalSessionPort = {
      subscribe: () => () => {},
      refresh: vi
        .fn()
        .mockResolvedValue({ hold: "clear", emailVerified: true }),
      login: vi.fn(),
      confirmMfa: vi.fn(),
      logout: vi
        .fn()
        .mockRejectedValueOnce(new Error("private failure"))
        .mockResolvedValueOnce(undefined),
      clear: vi.fn(),
    };
    render(
      <LocaleProvider>
        <PersonalSessionPanel session={session}>
          {() => null}
        </PersonalSessionPanel>
      </LocaleProvider>,
    );
    const u = userEvent.setup();
    await u.click(
      screen.getByRole("button", { name: "Check personal session" }),
    );
    await u.click(await screen.findByRole("button", { name: "Sign out" }));
    expect(
      await screen.findByText(/Local data cleared; server logout unconfirmed/),
    ).toBeVisible();
    expect(screen.queryByText(/Signed out on the server/)).toBeNull();
    await u.click(screen.getByRole("button", { name: "Sign out" }));
    expect(await screen.findByText(/Signed out on the server/)).toBeVisible();
    expect(session.logout).toHaveBeenCalledTimes(2);
  });
  it("holds retry controls after throttling and never makes a timed request", async () => {
    const login = vi
      .fn()
      .mockRejectedValue(
        new ApiError("rate-limit", 429, "RATE_LIMITED", undefined, 1),
      );
    const session: PersonalSessionPort = {
      subscribe: () => () => {},
      login,
      refresh: vi.fn(),
      confirmMfa: vi.fn(),
      logout: vi.fn(),
      clear: vi.fn(),
    };
    render(
      <LocaleProvider>
        <PersonalSessionPanel session={session}>
          {() => null}
        </PersonalSessionPanel>
      </LocaleProvider>,
    );
    const u = userEvent.setup();
    await u.type(screen.getByLabelText("Email", { exact: true }), EMAIL);
    await u.type(screen.getByLabelText("Password", { exact: true }), PASSWORD);
    await u.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText(/Too many attempts/)).toBeVisible();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeDisabled();
    await waitFor(
      () =>
        expect(
          screen.getByRole("button", { name: "Sign in" }),
        ).not.toBeDisabled(),
      { timeout: 2000 },
    );
    expect(login).toHaveBeenCalledTimes(1);
  });
  it("logout with unexpected success status cannot claim revocation", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(csrf())
      .mockResolvedValueOnce(json({}, 200));
    const session = new PersonalWorkspaceSession("ngo", transport);
    await expect(session.logout()).rejects.toMatchObject({ kind: "contract" });
    expect(session.state.currentScope).toBeNull();
  });
});
