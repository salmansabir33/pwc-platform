import { test, expect } from "@playwright/test";
import axe from "axe-core";
for (const port of [5173, 5174]) {
  test(`public registry on ${port}: actual Django/PostgreSQL, pagination, EN/UR and restricted exclusion`, async ({
    page,
  }) => {
    test.skip(
      !process.env.PWC_PUBLIC_API_TARGET,
      "Requires actual disposable PostgreSQL-backed API, never a mocked response",
    );
    const calls: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.startsWith("/api/"))
        calls.push(new URL(request.url()).pathname);
    });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(`http://127.0.0.1:${port}/ngo-registry`);
    expect(calls).toEqual([]);
    await page.getByLabel("NGO name").fill("Synthetic Directory NGO");
    await page.getByRole("button", { name: "Search registry" }).click();
    await expect(page.getByRole("status")).toContainText("20 results");
    await expect(
      page.getByRole("heading", {
        name: "Synthetic Directory NGO 00",
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", {
        name: "Synthetic Directory NGO 23",
        exact: true,
      }),
    ).toHaveCount(0);
    await page.getByRole("button", { name: "Next page", exact: true }).click();
    await expect(page.getByRole("status")).toContainText("3 results");
    await expect(
      page.getByRole("heading", {
        name: "Synthetic Directory NGO 22",
        exact: true,
      }),
    ).toBeVisible();
    await page.getByLabel("NGO name").fill("Synthetic Directory NGO 23");
    await page.getByRole("button", { name: "Search registry" }).click();
    await expect(
      page.getByText("No public organizations match these filters."),
    ).toBeVisible();
    await page
      .getByRole("combobox", { name: "Display language" })
      .selectOption("ur");
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await page.getByRole("button", { name: "فہرست تلاش کریں" }).click();
    await expect(page.getByRole("status")).toContainText("0");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.addScriptTag({ content: axe.source });
    const violations = await page.evaluate(async () =>
      (
        await (window as typeof window & { axe: typeof axe }).axe.run(
          document,
          {
            runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
          },
        )
      ).violations.map((v) => v.id),
    );
    expect(violations).toEqual([]);
    expect(calls.every((path) => path === "/api/v1/directory/")).toBe(true);
    expect(calls.length).toBe(4);
  });
}
