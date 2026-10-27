import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import axe from "axe-core";
import { LocaleProvider } from "@pwc/web-i18n";
import { AppBoundary, Button, TextField } from "@pwc/web-ui";
import { App as Ngo } from "../../apps/ngo-web/src/App";
import { App as Ops } from "../../apps/pwc-ops/src/App";

function portal(app: "ngo" | "ops", path = "/") {
  return render(
    <LocaleProvider>
      <MemoryRouter initialEntries={[path]}>
        {app === "ngo" ? <Ngo /> : <Ops />}
      </MemoryRouter>
    </LocaleProvider>,
  );
}
describe.each(["ngo", "ops"] as const)("%s independent route tree", (app) => {
  it("renders only the foundation, with no live requests, sign-in controls or business menu", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    portal(app);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      app === "ngo" ? "independent impact" : "responsible operations",
    );
    const nav = screen.getByRole("navigation", {
      name: "Foundation navigation",
    });
    expect(within(nav).getAllByRole("link")).toHaveLength(3);
    expect(
      screen.queryByRole("button", { name: /sign in|verify|approve|finance/i }),
    ).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
    expect(
      screen.getByRole("rowheader", {
        name: app === "ngo" ? "ORG-04" : "OPS-01",
      }),
    ).toBeVisible();
    expect(
      screen.queryByRole("rowheader", {
        name: app === "ngo" ? "OPS-01" : "ORG-04",
      }),
    ).not.toBeInTheDocument();
  });
  it.each([
    "/sign-in",
    "/register",
    "/account/security",
    "/ngos/00000000-0000-4000-8000-00000000000a/finance",
    "/operations",
    "/api/v1/ngo-contexts/test/private-probe/",
  ])("does not register unfinished route %s", (path) => {
    portal(app, path);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "This route is not available",
    );
    expect(
      screen.getByRole("link", { name: "Return to foundation" }),
    ).toHaveAttribute("href", "/");
  });
  it("navigates foundation routes, moves heading focus and updates the title", async () => {
    portal(app);
    const user = userEvent.setup();
    await user.click(
      within(
        screen.getByRole("navigation", { name: "Foundation navigation" }),
      ).getByRole("link", {
        name: "Language & accessibility",
      }),
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Language & accessibility",
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveFocus();
    expect(document.title).toContain("Language & accessibility");
    await user.click(
      within(
        screen.getByRole("navigation", { name: "Foundation navigation" }),
      ).getByRole("link", {
        name: "Interface states",
      }),
    );
    expect(
      screen.getByRole("heading", { name: "Loading specimen" }),
    ).toBeInTheDocument();
  });
  it("switches English/Urdu direction and clears local specimen drafts on language changes", async () => {
    portal(app, "/foundation/accessibility");
    const user = userEvent.setup();
    await user.type(
      screen.getByRole("textbox", { name: "Example display label" }),
      "synthetic text",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: /Display language|نمائش کی زبان/ }),
      "ur",
    );
    expect(document.documentElement).toHaveAttribute("lang", "ur");
    expect(document.documentElement).toHaveAttribute("dir", "rtl");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "زبان اور رسائی",
    );
    expect(screen.getByRole("textbox", { name: "مثالی نام" })).toHaveValue("");
    expect(screen.getByText("PWC-W1 / example@pwc.invalid").tagName).toBe(
      "BDI",
    );
    await user.selectOptions(
      screen.getByRole("combobox", { name: /Display language|نمائش کی زبان/ }),
      "en",
    );
    expect(document.documentElement).toHaveAttribute("dir", "ltr");
  });
  it("provides label/hint/error and local-only feedback for the specimen", async () => {
    portal(app, "/foundation/accessibility");
    const user = userEvent.setup();
    const fetch = vi.spyOn(globalThis, "fetch");
    const field = screen.getByRole("textbox", {
      name: "Example display label",
    });
    expect(field).toHaveAccessibleDescription(
      "Use synthetic text only. Nothing is sent or saved.",
    );
    await user.click(
      screen.getByRole("button", { name: "Test local feedback" }),
    );
    expect(field).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Enter an example label",
    );
    await user.type(field, "Synthetic");
    await user.click(
      screen.getByRole("button", { name: "Test local feedback" }),
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Nothing was submitted or saved",
    );
    expect(fetch).not.toHaveBeenCalled();
  });
  it.each([
    "/",
    "/foundation/accessibility",
    "/foundation/states",
    "/not-found",
  ])(
    "has no detectable DOM accessibility violations at %s (visual/manual checks remain)",
    async (path) => {
      const { container } = portal(app, path);
      const result = await axe.run(container, {
        rules: { "color-contrast": { enabled: false } },
      });
      expect(result.violations).toEqual([]);
    },
  );
});
it("has native keyboard-operable buttons and preserves explicit button types", async () => {
  const click = vi.fn();
  render(
    <>
      <Button onClick={click}>Example</Button>
      <TextField label="Label" hint="Hint" />
    </>,
  );
  const user = userEvent.setup();
  await user.tab();
  expect(screen.getByRole("button")).toHaveFocus();
  await user.keyboard("{Enter}");
  expect(click).toHaveBeenCalledOnce();
  expect(screen.getByRole("button")).toHaveAttribute("type", "button");
  await user.tab();
  expect(screen.getByRole("textbox")).toHaveFocus();
});
it("catches rendering failures without displaying raw exception secrets", () => {
  const error = vi.spyOn(console, "error").mockImplementation(() => {});
  const Crash = (): never => {
    throw new Error("private synthetic secret");
  };
  render(
    <AppBoundary>
      <Crash />
    </AppBoundary>,
  );
  expect(
    screen.getByRole("heading", { name: "Interface unavailable" }),
  ).toBeVisible();
  expect(
    screen.queryByText("private synthetic secret"),
  ).not.toBeInTheDocument();
  error.mockRestore();
});
