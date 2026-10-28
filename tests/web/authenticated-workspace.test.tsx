import { beforeEach, describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider } from "@pwc/web-i18n";
import { PersonalWorkspaceSession, OperationsPolicyClient } from "@pwc/web-api";
import { PersonalWorkspace } from "../../apps/ngo-web/src/PersonalWorkspace";
import { OperationsStatus } from "../../apps/pwc-ops/src/OperationsStatus";
import { AdministrationBoundary } from "../../apps/ngo-web/src/AdministrationBoundary";
import spec from "../../packages/api-contracts/openapi-v1.json";
const ID = "00000000-0000-4000-8000-000000000001";
const me = {
  user: { id: ID },
  session: { id: ID },
  recovery_hold_state: "clear",
  email_verified: true,
};
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status });
const policy = Object.fromEntries(
  Object.entries(
    spec.components.schemas.ControlledOnboardingRequirements.properties,
  ).map(([key, p]) => [
    key,
    "const" in p ? p.const : "enum" in p ? p.enum[0] : null,
  ]),
);
beforeEach(() => {
  vi.restoreAllMocks();
});
describe("personal session and permitted policy composition", () => {
  it("has no ambient fetch or production enable default", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const session = new PersonalWorkspaceSession("ngo");
    await expect(session.refresh()).rejects.toMatchObject({ kind: "disabled" });
    await expect(
      new OperationsPolicyClient(session.state).read(),
    ).rejects.toMatchObject({ kind: "disabled" });
    expect(fetch).not.toHaveBeenCalled();
  });
  it("activates only a personal scope, retains CSRF in memory and purges it on invalidation", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(json(me))
      .mockResolvedValueOnce(json({ csrf_token: "a".repeat(64) }))
      .mockResolvedValueOnce(json({ id: ID, revision: 2, state: "withdrawn" }));
    const session = new PersonalWorkspaceSession("ngo", transport);
    await session.refresh();
    expect(session.state.currentScope?.organizationId).toBeNull();
    const item = {
      id: ID,
      revision: 1,
      kind: "draft" as const,
      organization_id: ID,
      state: "draft" as const,
      name: "Synthetic",
      city: "City",
      classification: "registered" as const,
      can_withdraw: true,
      verification: [],
    };
    await session.history.withdraw(item);
    expect(transport.mock.calls[2]?.[1].headers["X-CSRFToken"]).toBe(
      "a".repeat(64),
    );
    session.state.invalidate("remote");
    await expect(session.history.withdraw(item)).rejects.toMatchObject({
      status: 401,
    });
    expect(transport).toHaveBeenCalledTimes(3);
  });
  it.each(["restricted", "review_required"])(
    "does not establish history scope for %s recovery hold",
    async (hold) => {
      const transport = vi
        .fn()
        .mockResolvedValue(json({ ...me, recovery_hold_state: hold }));
      const session = new PersonalWorkspaceSession("ngo", transport);
      expect((await session.refresh()).hold).toBe(hold);
      expect(session.state.currentScope).toBeNull();
      expect(transport).toHaveBeenCalledTimes(1);
    },
  );
  it("does not establish scope for unverified contact", async () => {
    const session = new PersonalWorkspaceSession(
      "ngo",
      vi.fn().mockResolvedValue(json({ ...me, email_verified: false })),
    );
    await session.refresh();
    expect(session.state.currentScope).toBeNull();
  });
  it("rejects false policy capability claims and reads only the fixed authenticated path", async () => {
    const session = new PersonalWorkspaceSession(
      "ops",
      vi
        .fn()
        .mockResolvedValueOnce(json(me))
        .mockResolvedValueOnce(json({ csrf_token: "a".repeat(64) })),
    );
    await session.refresh();
    const transport = vi
      .fn()
      .mockResolvedValueOnce(json(policy))
      .mockResolvedValueOnce(
        json({ ...policy, operator_commands_available: true }),
      );
    const gateway = new OperationsPolicyClient(session.state, transport);
    expect(await gateway.read()).toEqual(policy);
    expect(transport.mock.calls[0]?.[0]).toBe(
      "/api/v1/controlled-onboarding/requirements/",
    );
    expect(transport.mock.calls[0]?.[1]).toMatchObject({
      method: "GET",
      credentials: "same-origin",
      redirect: "error",
    });
    await expect(gateway.read()).rejects.toMatchObject({ kind: "contract" });
  });
  it("policy UI clears current server data on scope invalidation", async () => {
    const session = new PersonalWorkspaceSession(
      "ops",
      vi
        .fn()
        .mockResolvedValueOnce(json(me))
        .mockResolvedValueOnce(json({ csrf_token: "a".repeat(64) })),
    );
    await session.refresh();
    const gateway = new OperationsPolicyClient(
      session.state,
      vi.fn().mockResolvedValue(json(policy)),
    );
    const u = userEvent.setup();
    render(
      <LocaleProvider>
        <OperationsStatus gateway={gateway} />
      </LocaleProvider>,
    );
    await u.click(
      screen.getByRole("button", { name: "Refresh rollout policy" }),
    );
    expect(await screen.findByText("offline_initial_2026_10_27")).toBeVisible();
    session.state.invalidate("remote");
    await waitFor(() =>
      expect(screen.queryByText("offline_initial_2026_10_27")).toBeNull(),
    );
  });
  it("expired session UI does not offer domain actions or disclose server errors", async () => {
    const session = new PersonalWorkspaceSession(
      "ngo",
      vi
        .fn()
        .mockResolvedValue(
          json(
            { error: { code: "SESSION_INVALID", message: "private secret" } },
            401,
          ),
        ),
    );
    render(
      <LocaleProvider>
        <PersonalWorkspace session={session} />
      </LocaleProvider>,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Check personal session" }),
    );
    expect(
      await screen.findByText(/Session unavailable or expired/),
    ).toBeVisible();
    expect(screen.queryByText("private secret")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Refresh history" }),
    ).toBeDisabled();
  });
  it.each(["unavailable", "no-context", "restricted", "expired"] as const)(
    "admin %s is a state boundary, never authority",
    (state) => {
      render(
        <LocaleProvider>
          <AdministrationBoundary state={state} />
        </LocaleProvider>,
      );
      expect(
        screen.getByText("UI-state preparation · no active authority"),
      ).toBeVisible();
      expect(screen.queryByRole("button")).toBeNull();
      expect(
        screen.getByText(/acceptance is distinct from grant activation/),
      ).toBeVisible();
    },
  );
});
