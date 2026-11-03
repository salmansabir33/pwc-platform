import { describe, it, expect, vi } from "vitest";
import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider, useLocale } from "@pwc/web-i18n";
import type { DirectoryGateway } from "@pwc/web-api";
import { Directory } from "../../apps/ngo-web/src/PublicDirectory";
const a = {
  id: "00000000-0000-4000-8000-000000000001",
  name: "NGO A",
  city: "Faisalabad",
  classification: "registered" as const,
};
const b = {
  ...a,
  id: "00000000-0000-4000-8000-000000000002",
  name: "NGO B",
  city: "Lahore",
};
function mount(
  search = vi.fn().mockResolvedValue({ results: [a, b], next_cursor: null }),
) {
  const gateway: DirectoryGateway = { search };
  const result = render(
    <LocaleProvider>
      <Directory gateway={gateway} />
    </LocaleProvider>,
  );
  return { ...result, search, user: userEvent.setup() };
}
async function searchAndSelect(
  user: ReturnType<typeof userEvent.setup>,
  name = "NGO A",
) {
  await user.click(screen.getByRole("button", { name: "Search registry" }));
  await user.click(
    await screen.findByRole("button", {
      name: `View public summary for ${name}`,
    }),
  );
}
describe("04D public-only summary", () => {
  it("selects exact NGO, focuses heading and restores focus without extra networking", async () => {
    const { user, search } = mount();
    await searchAndSelect(user);
    let region = screen.getByRole("region", { name: "NGO public summary" });
    expect(within(region).getByText("NGO A")).toBeVisible();
    expect(within(region).queryByText("Lahore")).toBeNull();
    expect(
      screen.getByRole("heading", { name: "NGO public summary" }),
    ).toHaveFocus();
    await user.click(
      screen.getByRole("button", { name: "View public summary for NGO B" }),
    );
    region = screen.getByRole("region", { name: "NGO public summary" });
    expect(within(region).getByText("Lahore")).toBeVisible();
    expect(within(region).queryByText("NGO A")).toBeNull();
    expect(
      within(region).queryByRole("button", { name: /edit|publish|approve/i }),
    ).toBeNull();
    await user.click(
      screen.getByRole("button", { name: "Close public summary" }),
    );
    expect(
      screen.getByRole("button", { name: "View public summary for NGO B" }),
    ).toHaveFocus();
    expect(search).toHaveBeenCalledTimes(1);
  });
  it("clears summary when filters change and shows empty/error states", async () => {
    const search = vi
      .fn()
      .mockResolvedValueOnce({ results: [a], next_cursor: null })
      .mockResolvedValueOnce({ results: [], next_cursor: null })
      .mockRejectedValueOnce(new Error("private-canary"));
    const { user } = mount(search);
    await searchAndSelect(user);
    await user.type(screen.getByLabelText("NGO name"), "other");
    expect(
      screen.queryByRole("region", { name: "NGO public summary" }),
    ).toBeNull();
    await user.click(screen.getByRole("button", { name: "Search registry" }));
    expect(
      await screen.findByText("No public organizations match these filters."),
    ).toBeVisible();
    await user.click(screen.getByRole("button", { name: "Search registry" }));
    expect(await screen.findByText(/Registry unavailable/)).toBeVisible();
    expect(screen.queryByText("private-canary")).toBeNull();
  });
  it.each([
    { ...a, id: "../private" },
    { ...a, private_notes: "unpublished-canary" },
    { ...a, contact: "unpublished-canary" },
    { ...a, history: "unpublished-canary" },
    { ...a, verification: "unpublished-canary" },
    { ...a, memberships: "unpublished-canary" },
  ])(
    "fails closed on malformed IDs or additional private fields",
    async (row) => {
      const { user } = mount(
        vi.fn().mockResolvedValue({ results: [row], next_cursor: null }),
      );
      await user.click(screen.getByRole("button", { name: "Search registry" }));
      expect(await screen.findByText(/Registry unavailable/)).toBeVisible();
      expect(
        screen.queryByRole("button", { name: /View public summary/ }),
      ).toBeNull();
      expect(screen.queryByText("unpublished-canary")).toBeNull();
    },
  );
  it("renders untrusted names as text and handles absent public city", async () => {
    const row = { ...a, name: '<img src=x onerror="alert(1)">', city: "" };
    const { user, container } = mount(
      vi.fn().mockResolvedValue({ results: [row], next_cursor: null }),
    );
    await searchAndSelect(user, row.name);
    expect(
      within(
        screen.getByRole("region", { name: "NGO public summary" }),
      ).getByText("Not provided"),
    ).toBeVisible();
    expect(container.querySelector("img")).toBeNull();
  });
  it("shows loading and ignores a late result after filter reset", async () => {
    let resolve!: (v: unknown) => void;
    const { user } = mount(
      vi.fn().mockReturnValue(
        new Promise((r) => {
          resolve = r;
        }),
      ),
    );
    await user.click(screen.getByRole("button", { name: "Search registry" }));
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    await user.type(screen.getByLabelText("City"), "new");
    await act(async () => {
      resolve({ results: [a], next_cursor: null });
    });
    expect(
      screen.queryByRole("button", { name: /View public summary/ }),
    ).toBeNull();
  });
});

function SwitchLanguage() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("ur")}>Urdu</button>;
}
it("clears selected data on language/gateway change and renders Urdu RTL", async () => {
  const gateway = {
    search: vi.fn().mockResolvedValue({ results: [a], next_cursor: null }),
  };
  const user = userEvent.setup();
  const { rerender } = render(
    <LocaleProvider>
      <SwitchLanguage />
      <Directory gateway={gateway} />
    </LocaleProvider>,
  );
  await searchAndSelect(user);
  const replacement = {
    search: vi.fn().mockResolvedValue({ results: [b], next_cursor: null }),
  };
  rerender(
    <LocaleProvider>
      <SwitchLanguage />
      <Directory gateway={replacement} />
    </LocaleProvider>,
  );
  expect(
    screen.queryByRole("region", { name: "NGO public summary" }),
  ).toBeNull();
  await searchAndSelect(user, "NGO B");
  await user.click(screen.getByRole("button", { name: "Urdu" }));
  expect(
    screen.queryByRole("region", { name: "تنظیم کا عوامی خلاصہ" }),
  ).toBeNull();
  await user.click(screen.getByRole("button", { name: "فہرست تلاش کریں" }));
  await user.click(
    await screen.findByRole("button", { name: "NGO B کا عوامی خلاصہ دیکھیں" }),
  );
  expect(
    screen.getByRole("region", { name: "تنظیم کا عوامی خلاصہ" }),
  ).toBeVisible();
  expect(
    screen.getByRole("navigation", { name: "عوامی خلاصے کی سمت یابی" }),
  ).toBeVisible();
  expect(screen.getByRole("button", { name: "پچھلی تنظیم" })).toBeDisabled();
  expect(screen.getByRole("button", { name: "اگلی تنظیم" })).toBeDisabled();
  expect(screen.getByText("اس صفحے پر 1 میں سے عوامی نتیجہ 1")).toBeVisible();
  expect(document.documentElement).toHaveAttribute("dir", "rtl");
});
it("drops the old summary before fetching the next public page", async () => {
  const search = vi
    .fn()
    .mockResolvedValueOnce({ results: [a], next_cursor: "synthetic-cursor" })
    .mockResolvedValueOnce({ results: [b], next_cursor: null });
  const { user } = mount(search);
  await searchAndSelect(user);
  await user.click(screen.getByRole("button", { name: "Next page" }));
  expect(
    screen.queryByRole("region", { name: "NGO public summary" }),
  ).toBeNull();
  expect(
    screen.queryByRole("button", { name: "View public summary for NGO A" }),
  ).toBeNull();
  await user.click(
    await screen.findByRole("button", {
      name: "View public summary for NGO B",
    }),
  );
  expect(
    within(
      screen.getByRole("region", { name: "NGO public summary" }),
    ).getByText("NGO B"),
  ).toBeVisible();
  expect(search).toHaveBeenLastCalledWith(
    expect.any(Object),
    "synthetic-cursor",
    expect.any(AbortSignal),
  );
});

it("browses only current-page NGOs with keyboard, announces position and closes to the current result", async () => {
  const { user, search } = mount();
  await searchAndSelect(user);
  let region = screen.getByRole("region", { name: "NGO public summary" });
  const title = within(region).getByRole("heading", {
    name: "NGO public summary",
  });
  expect(title).toHaveAccessibleDescription(
    "Public result 1 of 2 on this page",
  );
  expect(
    within(region).getByRole("button", { name: "Previous NGO" }),
  ).toBeDisabled();
  // Heading is focused; disabled Previous is skipped by keyboard navigation.
  await user.tab();
  expect(
    within(region).getByRole("button", { name: "Next NGO" }),
  ).toHaveFocus();
  await user.keyboard("{Enter}");
  region = screen.getByRole("region", { name: "NGO public summary" });
  expect(within(region).getByText("NGO B")).toBeVisible();
  expect(within(region).queryByText("NGO A")).toBeNull();
  expect(
    within(region).getByRole("heading", { name: "NGO public summary" }),
  ).toHaveFocus();
  expect(
    within(region).getByRole("heading", { name: "NGO public summary" }),
  ).toHaveAccessibleDescription("Public result 2 of 2 on this page");
  expect(
    within(region).getByRole("button", { name: "Next NGO" }),
  ).toBeDisabled();
  await user.keyboard("{Escape}");
  expect(
    screen.queryByRole("region", { name: "NGO public summary" }),
  ).toBeNull();
  expect(
    screen.getByRole("button", { name: "View public summary for NGO B" }),
  ).toHaveFocus();
  expect(search).toHaveBeenCalledTimes(1);
});

it("Previous returns to A and Close restores A, without moving between result pages", async () => {
  const { user, search } = mount();
  await searchAndSelect(user, "NGO B");
  await user.click(screen.getByRole("button", { name: "Previous NGO" }));
  expect(
    within(
      screen.getByRole("region", { name: "NGO public summary" }),
    ).getByText("NGO A"),
  ).toBeVisible();
  await user.click(
    screen.getByRole("button", { name: "Close public summary" }),
  );
  expect(
    screen.getByRole("button", { name: "View public summary for NGO A" }),
  ).toHaveFocus();
  expect(search).toHaveBeenCalledTimes(1);
});

it("cannot navigate beyond a single visible result or expose an unpublished row", async () => {
  const { user, search } = mount(
    vi
      .fn()
      .mockResolvedValue({ results: [a], next_cursor: "next-public-page" }),
  );
  await searchAndSelect(user);
  const region = screen.getByRole("region", { name: "NGO public summary" });
  expect(
    within(region).getByRole("button", { name: "Previous NGO" }),
  ).toBeDisabled();
  expect(
    within(region).getByRole("button", { name: "Next NGO" }),
  ).toBeDisabled();
  expect(
    within(region).getByText("Public result 1 of 1 on this page"),
  ).toBeVisible();
  expect(within(region).queryByText("NGO B")).toBeNull();
  expect(search).toHaveBeenCalledTimes(1);
});
