import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider } from "@pwc/web-i18n";
import { Directory } from "../../apps/ngo-web/src/PublicDirectory";
import { WorkspaceHistory } from "../../apps/ngo-web/src/WorkspaceHistory";
import { ScopeState } from "@pwc/web-api";
import type { WorkspacePage } from "@pwc/web-api";
const ID = "00000000-0000-4000-8000-000000000001";
const page = (): WorkspacePage => ({
  results: [
    {
      id: ID,
      organization_id: ID,
      kind: "draft",
      revision: 1,
      state: "submitted",
      name: "Synthetic Welfare",
      city: "City",
      classification: "unregistered",
      can_withdraw: true,
      verification: [],
    },
  ],
  next_cursor: null,
  administration_available: false,
  intake_available: false,
  verification_available: true,
});
describe("permission-aware public and personal history screens", () => {
  it("does not fetch public data until user searches and clears old results on filter edits", async () => {
    const search = vi.fn().mockResolvedValue({
      results: [
        {
          id: ID,
          name: "Synthetic NGO",
          city: "City",
          classification: "registered",
        },
      ],
      next_cursor: "next",
    });
    const u = userEvent.setup();
    render(
      <LocaleProvider>
        <Directory gateway={{ search }} />
      </LocaleProvider>,
    );
    expect(search).not.toHaveBeenCalled();
    await u.click(screen.getByRole("button", { name: "Search registry" }));
    expect(await screen.findByText("Synthetic NGO")).toBeVisible();
    await u.type(screen.getByLabelText("NGO name"), "new");
    expect(screen.queryByText("Synthetic NGO")).toBeNull();
  });
  it("renders safe errors and empty states without fake success", async () => {
    const search = vi
      .fn()
      .mockRejectedValueOnce(new Error("private case"))
      .mockResolvedValueOnce({ results: [], next_cursor: null });
    const u = userEvent.setup();
    render(
      <LocaleProvider>
        <Directory gateway={{ search }} />
      </LocaleProvider>,
    );
    await u.click(screen.getByRole("button", { name: "Search registry" }));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("unavailable"),
    );
    expect(screen.queryByText("private case")).toBeNull();
    await u.click(screen.getByRole("button", { name: "Search registry" }));
    expect(
      await screen.findByText("No public organizations match these filters."),
    ).toBeVisible();
  });
  it("personal screen stays unavailable without gateway and never fetches", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    render(
      <LocaleProvider>
        <WorkspaceHistory />
      </LocaleProvider>,
    );
    expect(
      screen.getByRole("button", { name: "Refresh history" }),
    ).toBeDisabled();
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.queryByRole("button", { name: /Approve/ })).toBeNull();
  });
  it("withdraws exact owner application then reloads server state, never optimistically", async () => {
    const current = page();
    const list = vi
      .fn()
      .mockResolvedValueOnce(current)
      .mockResolvedValueOnce({
        ...current,
        results: [
          {
            ...current.results[0],
            state: "withdrawn",
            revision: 2,
            can_withdraw: false,
          },
        ],
      });
    const withdraw = vi.fn().mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const u = userEvent.setup();
    render(
      <LocaleProvider>
        <WorkspaceHistory
          gateway={{ state: new ScopeState("ngo"), list, withdraw }}
        />
      </LocaleProvider>,
    );
    await u.click(screen.getByRole("button", { name: "Refresh history" }));
    expect(await screen.findByText("Synthetic Welfare")).toBeVisible();
    await u.click(screen.getByRole("button", { name: "Withdraw application" }));
    expect(
      await screen.findByText("Withdrawn", { selector: "span" }),
    ).toBeVisible();
    expect(withdraw).toHaveBeenCalledWith(current.results[0]);
    expect(list).toHaveBeenCalledTimes(2);
    expect(
      screen.queryByRole("button", { name: "Withdraw application" }),
    ).toBeNull();
  });
  it("purges private rows on remote logout and discards late success", async () => {
    let resolve!: (value: WorkspacePage) => void;
    const list = vi.fn(
      () =>
        new Promise<WorkspacePage>((r) => {
          resolve = r;
        }),
    );
    const state = new ScopeState("ngo");
    const u = userEvent.setup();
    render(
      <LocaleProvider>
        <WorkspaceHistory gateway={{ state, list, withdraw: vi.fn() }} />
      </LocaleProvider>,
    );
    await u.click(screen.getByRole("button", { name: "Refresh history" }));
    state.invalidate("remote");
    resolve(page());
    await waitFor(() =>
      expect(screen.queryByText("Synthetic Welfare")).toBeNull(),
    );
    expect(
      screen.getByRole("button", { name: "Refresh history" }),
    ).not.toBeDisabled();
  });
});
