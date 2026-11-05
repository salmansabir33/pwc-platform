import { test, expect } from "@playwright/test";
import axe from "axe-core";

test("shipped invitation route scrubs credentials, remains disconnected and accessible in EN/UR at 320px", async ({
  page,
}) => {
  const api: string[] = [];
  page.on("request", (request) => {
    if (new URL(request.url()).pathname.startsWith("/api/"))
      api.push(request.url());
  });
  await page.setViewportSize({ width: 320, height: 844 });
  await page.goto(
    "http://127.0.0.1:5173/account/invite#invitation_id=00000000-0000-4000-8000-000000000001&token=" +
      "t".repeat(43),
  );
  await expect(page).toHaveURL("http://127.0.0.1:5173/account/invite");
  await expect(
    page.getByRole("button", { name: "Request email proof", exact: true }),
  ).toBeDisabled();
  for (const locale of ["en", "ur"]) {
    if (locale === "ur")
      await page
        .getByRole("combobox", { name: "Display language" })
        .selectOption("ur");
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
            runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"] },
          })
        ).violations.map((violation) => violation.id),
      ),
    ).toEqual([]);
  }
  expect(api).toEqual([]);
});
