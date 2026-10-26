import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider } from "@pwc/web-i18n";
import { Registry } from "../../apps/ngo-web/src/Registry";
import type { RegistryGateway } from "../../apps/ngo-web/src/Registry";
import type { components } from "../../packages/api-contracts/generated/schema";
import examples from "../../packages/api-contracts/examples-v1.json";
type S = components["schemas"];
const fixture = <T,>(id: string): T =>
  examples.cases.find((c) => c.operationId === id && c.kind === "response")!
    .body as T;
function gateway(): RegistryGateway {
  return {
    search: vi.fn().mockResolvedValue({
      results: [
        {
          id: "00000000-0000-4000-8000-000000000001",
          name: "Synthetic Welfare",
          city: "Faisalabad",
          classification: "registered",
        },
      ],
      next_cursor: null,
    }),
    drafts: vi.fn().mockResolvedValue({
      results: [fixture<S["RegistryDraft"]>("registryCreateDraft")],
      next_cursor: null,
    }),
    claims: vi.fn().mockResolvedValue({
      results: [fixture<S["RegistryClaim"]>("registryCreateClaim")],
      next_cursor: null,
    }),
    history: vi.fn().mockResolvedValue({ results: [], next_cursor: null }),
    edit: vi.fn().mockResolvedValue(fixture("registryCreateDraft")),
    create: vi.fn().mockResolvedValue(fixture("registryCreateDraft")),
    claim: vi.fn().mockResolvedValue(fixture("registryCreateClaim")),
    change: vi.fn().mockResolvedValue(fixture("registrySubmitDraft")),
    withdrawClaim: vi.fn().mockResolvedValue(fixture("registryWithdrawClaim")),
  };
}
describe("04A claimant components without W1 networking", () => {
  it("mounts unavailable with disabled actions and no network", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(
      <LocaleProvider>
        <Registry />
      </LocaleProvider>,
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "ORG-01",
    );
    expect(
      screen.getByRole("button", { name: "Save private draft" }),
    ).toBeDisabled();
    expect(screen.getByRole("status")).toHaveTextContent("networking");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("searches minimized candidates, warns and submits segregated claim", async () => {
    const api = gateway();
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Registry gateway={api} scope="synthetic" />
      </LocaleProvider>,
    );
    await user.type(screen.getByLabelText("Organization search"), "Welfare");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(api.search).toHaveBeenCalledWith("Welfare", "");
    expect(screen.getByText(/Potential duplicates/)).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Request claim" }));
    expect(api.claim).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("button", { name: "Withdraw claim" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /approve|verify|admin|finance/i }),
    ).toBeNull();
  });
  it("creates, submits and withdraws current revisions without granting authority", async () => {
    const api = gateway();
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Registry gateway={api} scope="synthetic" />
      </LocaleProvider>,
    );
    await user.type(screen.getByLabelText("Display name"), "Synthetic Welfare");
    await user.click(
      screen.getByRole("button", { name: "Save private draft" }),
    );
    expect(api.create).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "Synthetic Welfare",
        city: "",
        classification: "unregistered",
      }),
      expect.stringMatching(/^[0-9a-f-]{36}$/),
    );
    await user.click(
      screen.getByRole("button", { name: "Submit for future review" }),
    );
    expect(api.change).toHaveBeenCalledWith(expect.any(String), "submit", 1);
    expect(
      screen.queryByRole("button", { name: "Submit for future review" }),
    ).toBeNull();
    await user.click(screen.getByRole("button", { name: "Withdraw draft" }));
    expect(api.change).toHaveBeenLastCalledWith(
      expect.any(String),
      "withdraw",
      2,
    );
  });
  it("redacts raw errors and does not replay conflicting requests", async () => {
    const api = gateway();
    vi.mocked(api.search).mockRejectedValue(new Error("private database note"));
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Registry gateway={api} />
      </LocaleProvider>,
    );
    await user.type(screen.getByLabelText("Organization search"), "Welfare");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(screen.getByRole("alert")).toHaveTextContent("conflicting");
    expect(screen.queryByText(/private database/)).toBeNull();
    expect(api.search).toHaveBeenCalledTimes(1);
  });
  it("discards late data after identity/scope invalidation", async () => {
    const api = gateway();
    let resolve!: (value: S["RegistrySearchPage"]) => void;
    vi.mocked(api.search).mockReturnValue(
      new Promise((r) => {
        resolve = r;
      }),
    );
    const user = userEvent.setup();
    const view = render(
      <LocaleProvider>
        <Registry gateway={api} scope="A" />
      </LocaleProvider>,
    );
    await user.type(screen.getByLabelText("Organization search"), "Welfare");
    await user.click(screen.getByRole("button", { name: "Search" }));
    view.rerender(
      <LocaleProvider>
        <Registry scope="signed-out" />
      </LocaleProvider>,
    );
    resolve({
      results: [
        {
          id: "00000000-0000-4000-8000-000000000001",
          name: "Private stale data",
          city: "",
          classification: "registered",
        },
      ],
      next_cursor: null,
    });
    expect(screen.queryByText(/Private stale/)).toBeNull();
    expect(screen.getByLabelText("Organization search")).toHaveValue("");
  });
});
