import { test, expect } from "@playwright/test";
test("04A production NGO bundle keeps registry disconnected in English and Urdu", async ({
  page,
}) => {
  const calls: string[] = [];
  page.on("request", (r) => {
    if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5173/registry");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("ORG-01");
  await expect(
    page.getByRole("button", { name: "Save private draft" }),
  ).toBeDisabled();
  await expect(page.getByRole("status")).toContainText("not connected");
  await page
    .getByRole("combobox", { name: "Display language" })
    .selectOption("ur");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("ORG-01");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect(calls).toEqual([]);
});
