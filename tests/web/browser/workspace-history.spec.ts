import { test, expect } from "@playwright/test";
import axe from "axe-core";
test("owner history default transport remains gated, accessible and isolated in EN/UR", async ({
  page,
}) => {
  const calls: string[] = [];
  page.on("request", (r) => {
    if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
  });
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto("http://127.0.0.1:5173/application-history");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "My application history",
  );
  await expect(
    page.getByRole("button", { name: "Refresh history" }),
  ).toBeDisabled();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "Personal networking remains disabled" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("status")
      .filter({ hasText: "No checked personal session." }),
  ).toBeVisible();
  await page
    .getByRole("combobox", { name: "Display language" })
    .selectOption("ur");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    page.getByRole("button", { name: "تاریخ دوبارہ دیکھیں" }),
  ).toBeDisabled();
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
          runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
        })
      ).violations.map((v) => v.id),
    ),
  ).toEqual([]);
  expect(calls).toEqual([]);
});
