import { test, expect } from "@playwright/test";
for (const [port, screen] of [
  [5173, "ORG-03"],
  [5174, "PWC-01"],
] as const) {
  test(`04B ${screen} unavailable in production bundle without API calls`, async ({
    page,
  }) => {
    const calls: string[] = [];
    page.on("request", (r) => {
      if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`http://127.0.0.1:${port}/verification`);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(screen);
    await expect(page.getByRole("status")).toContainText("Files unavailable");
    expect(await page.locator("input[type=file]").count()).toBe(0);
    if (port === 5173)
      await expect(
        page.getByRole("button", { name: "Load own cases" }),
      ).toBeDisabled();
    await page
      .getByRole("combobox", { name: "Display language" })
      .selectOption("ur");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(calls).toEqual([]);
  });
}
