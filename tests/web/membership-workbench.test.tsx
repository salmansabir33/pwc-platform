import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import axe from "axe-core";
import { LocaleProvider, useLocale } from "@pwc/web-i18n";
import { MembershipWorkbench } from "../../apps/ngo-web/src/MembershipWorkbench";
import manifest from "../../packages/api-contracts/fixtures/membership-demonstrations.json";

function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("ur")}>Urdu</button>;
}
function mount() {
  render(
    <LocaleProvider>
      <Language />
      <MembershipWorkbench />
    </LocaleProvider>,
  );
  return userEvent.setup();
}
afterEach(() => vi.unstubAllGlobals());
describe("P4 fixed synthetic workbench", () => {
  it("reads every generated journey without fetching, editing, importing or linking", async () => {
    const fetch = vi.fn();
    vi.stubGlobal("fetch", fetch);
    const user = mount();
    const selector = screen.getByRole("combobox", {
      name: "Read-only example",
    });
    for (const scenario of manifest.scenarios) {
      await user.selectOptions(selector, scenario.id);
      expect(screen.getByRole("status")).toHaveTextContent(
        "Viewing fictional example",
      );
      for (const button of screen
        .getAllByRole("button")
        .filter((b) => b.textContent !== "Urdu")) {
        expect(button).toBeDisabled();
      }
    }
    await user.selectOptions(selector, "import");
    expect(screen.getByText("EXISTING_REFERENCE")).toBeVisible();
    expect(
      screen.getByText(/Candidate only; no import or admission/),
    ).toBeVisible();
    expect(document.querySelector('input[type="file"]')).toBeNull();
    expect(document.querySelector("form")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
    expect(document.body).not.toHaveTextContent("MEMBER_A");
    expect(document.body).not.toHaveTextContent("Synthetic Person");
  });
  it("shows C1 policy history and stale pending bindings without adding writers", async () => {
    const user = mount();
    await user.selectOptions(screen.getByRole("combobox"), "category-policy");
    expect(screen.getByText(/Policy revision: 3/)).toBeVisible();
    expect(
      screen.getByText(/Pending fixtures requiring explicit re-review: 1/),
    ).toBeVisible();
    const histories = screen.getAllByRole("list", {
      name: "Proposed policy history",
    });
    expect(within(histories[1]!).getAllByRole("listitem")).toHaveLength(3);
    expect(
      within(histories[1]!).getByText(/Category deactivated/),
    ).toBeVisible();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Save category" }),
    ).toBeDisabled();
  });
  it("presents revisions, preserved history and an actionable stale validation explanation", async () => {
    const user = mount();
    await user.selectOptions(screen.getByRole("combobox"), "category");
    const history = screen.getByRole("list", {
      name: "Redacted proposed history",
    });
    expect(within(history).getAllByRole("listitem")).toHaveLength(3);
    expect(within(history).getByText(/category changed/)).toBeVisible();
    await user.selectOptions(screen.getByRole("combobox"), "stale");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "SOURCE_REVISION_CONFLICT",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Refresh the fixture");
    expect(screen.queryByRole("list")).toBeNull();
  });
  it("has keyboard-accessible navigation, bilingual labels and no enabled protected actions", async () => {
    const user = mount();
    await user.tab();
    expect(screen.getByRole("button", { name: "Urdu" })).toHaveFocus();
    await user.tab();
    expect(screen.getByRole("combobox")).toHaveFocus();
    await user.click(screen.getByRole("button", { name: "Urdu" }));
    expect(document.documentElement.dir).toBe("rtl");
    expect(
      screen.getByRole("heading", { name: "رکنیت کی تیاری" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "داخلہ منظور کریں" }),
    ).toBeDisabled();
    await user.selectOptions(
      screen.getByRole("combobox", { name: "صرف مطالعے کا نمونہ" }),
      "import",
    );
    expect(screen.getByText(/سی ایس وی ریکارڈ/)).toBeVisible();
  });
  it("passes automated accessibility in both languages and every specimen", async () => {
    const user = mount();
    for (const language of ["en", "ur"]) {
      if (language === "ur")
        await user.click(screen.getByRole("button", { name: "Urdu" }));
      for (const scenario of manifest.scenarios) {
        await user.selectOptions(screen.getByRole("combobox"), scenario.id);
        const result = await axe.run(document.body, {
          rules: { region: { enabled: false } },
        });
        expect(result.violations).toEqual([]);
      }
    }
  });
});
