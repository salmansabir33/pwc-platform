import { test, expect } from "@playwright/test";
import axe from "axe-core";
for (const [origin, path, title] of [
  ["http://127.0.0.1:5173", "/administration", "NGO administration boundary"],
  [
    "http://127.0.0.1:5174",
    "/operations-status",
    "Operations · Controlled rollout status",
  ],
  [
    "http://127.0.0.1:5174",
    "/personal-session",
    "Operations · Controlled rollout status",
  ],
] as const) {
  test(`${path}: default-gated boundary is responsive, localized and makes no API calls`, async ({
    page,
  }) => {
    const calls: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.startsWith("/api/"))
        calls.push(request.url());
    });
    await page.setViewportSize({ width: 320, height: 844 });
    await page.goto(origin + path);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    for (const locale of ["en", "ur"]) {
      await page
        .getByRole("combobox", {
          name: "Display language",
        })
        .selectOption(locale);
      await expect(page.locator("html")).toHaveAttribute(
        "dir",
        locale === "ur" ? "rtl" : "ltr",
      );
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      await page.addScriptTag({ content: axe.source });
      expect(
        await page.evaluate(async () =>
          (
            await (window as unknown as { axe: typeof axe }).axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21aa"],
              },
            })
          ).violations.map((v) => v.id),
        ),
      ).toEqual([]);
    }
    expect(calls).toEqual([]);
    expect(
      await page
        .getByRole("button", { name: /Approve|Accept invitation|Activate/ })
        .count(),
    ).toBe(0);
  });
}
