import { test, expect } from "@playwright/test";
test("controlled offline initial rollout has no privileged browser calls", async ({
  page,
}) => {
  const calls: string[] = [];
  page.on("request", (r) => {
    if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:5174/controlled-onboarding");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("PWC-01");
  await expect(
    page.getByRole("button", { name: "Approve record" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Send recipient-bound invitation" }),
  ).toBeDisabled();
  await expect(page.locator("input[type=file]")).toHaveCount(0);
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
