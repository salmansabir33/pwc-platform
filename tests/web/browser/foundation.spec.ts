import { test, expect } from "@playwright/test";
import { createRequire } from "node:module";
import type { AxeResults } from "axe-core";
const require = createRequire(import.meta.url);
async function accessibility(page: import("@playwright/test").Page) {
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  const result = await page.evaluate(async () => {
    const axe = (
      window as unknown as {
        axe: { run: (root: Element, options: unknown) => Promise<AxeResults> };
      }
    ).axe;
    return await axe.run(document.documentElement, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
      },
    });
  });
  expect(
    result.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => n.target),
    })),
  ).toEqual([]);
}
for (const [app, port] of [
  ["ngo", 5173],
  ["ops", 5174],
] as const) {
  const url = `http://127.0.0.1:${port}`;
  test(`${app}: desktop routes, no API calls and full browser axe checks in both locales`, async ({
    page,
  }) => {
    const apiRequests: string[] = [];
    const errors: string[] = [];
    page.on("request", (r) => {
      if (new URL(r.url()).pathname.startsWith("/api/"))
        apiRequests.push(r.url());
    });
    page.on("pageerror", (e) => errors.push(e.message));
    await page.setViewportSize({ width: 1440, height: 1000 });
    for (const path of [
      "/",
      "/foundation/accessibility",
      "/foundation/states",
    ]) {
      await page.goto(url + path);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
      await accessibility(page);
      await page.getByRole("combobox").selectOption("ur");
      await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
      await page.evaluate(() => document.fonts.ready);
      const sidebar = await page.locator(".sidebar").boundingBox();
      const workspace = await page.locator(".workspace").boundingBox();
      expect(sidebar!.x).toBeGreaterThan(workspace!.x);
      await accessibility(page);
    }
    expect(apiRequests).toEqual([]);
    expect(errors).toEqual([]);
    expect(
      await page.evaluate(() => ({
        local: localStorage.length,
        session: sessionStorage.length,
        cookies: document.cookie,
      })),
    ).toEqual({ local: 0, session: 0, cookies: "" });
  });
  test(`${app}: 320px reflow and accessible collapsed navigation in English and Urdu`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    await page.goto(url);
    const menu = page.getByRole("button", { name: "Toggle navigation" });
    await expect(menu).toHaveAttribute("aria-expanded", "false");
    await expect(page.getByRole("navigation")).toBeHidden();
    await menu.click();
    await expect(
      page.getByRole("button", { name: "Close navigation" }),
    ).toHaveAttribute("aria-expanded", "true");
    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Language & accessibility" })
      .click();
    await expect(page.getByRole("navigation")).toBeHidden();
    for (const locale of ["en", "ur"]) {
      await page.getByRole("combobox").selectOption(locale);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= window.innerWidth,
        ),
      ).toBe(true);
      await accessibility(page);
    }
  });
  test(`${app}: keyboard navigation, skip link, field errors and local feedback`, async ({
    page,
  }) => {
    await page.goto(url);
    await page.keyboard.press("Tab");
    await expect(
      page.getByRole("link", { name: "Skip to main content" }),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.getByRole("main")).toBeFocused();
    await page
      .getByRole("navigation")
      .getByRole("link", { name: "Language & accessibility" })
      .click();
    await expect(page.getByRole("heading", { level: 1 })).toBeFocused();
    const input = page.getByRole("textbox", { name: "Example display label" });
    await input.focus();
    await page.keyboard.press("Tab");
    await expect(
      page.getByRole("button", { name: "Test local feedback" }),
    ).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(input).toHaveAttribute("aria-invalid", "true");
    await input.fill("Synthetic specimen");
    await page.getByRole("button", { name: "Test local feedback" }).click();
    await expect(page.getByRole("status")).toContainText(
      "Nothing was submitted or saved",
    );
    await expect(input).toHaveAccessibleName("Example display label");
    await input.focus();
    await page.keyboard.press("Tab");
    const focus = await page
      .getByRole("button", { name: "Test local feedback" })
      .evaluate((element) => ({
        style: getComputedStyle(element).outlineStyle,
        width: getComputedStyle(element).outlineWidth,
      }));
    expect(focus).toEqual({ style: "solid", width: "3px" });
    await input.fill('<img src=x onerror="window.__injected=true">');
    await page.getByRole("button", { name: "Test local feedback" }).click();
    await expect(page.locator("main img")).toHaveCount(0);
    expect(await page.evaluate(() => Object.hasOwn(window, "__injected"))).toBe(
      false,
    );
  });
  test(`${app}: all foundation pages reflow at 320px in both directions`, async ({
    page,
  }) => {
    await page.setViewportSize({ width: 320, height: 800 });
    for (const path of [
      "/",
      "/foundation/accessibility",
      "/foundation/states",
    ]) {
      await page.goto(url + path);
      for (const locale of ["en", "ur"]) {
        await page.getByRole("combobox").selectOption(locale);
        await page.evaluate(() => document.fonts.ready);
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= window.innerWidth,
          ),
        ).toBe(true);
        await accessibility(page);
      }
    }
  });
  test(`${app}: unavailable auth/business routes have only safe not-found content`, async ({
    page,
  }) => {
    for (const path of [
      "/sign-in",
      "/register",
      "/workspaces",
      "/verification",
      "/operations",
      "/ngos/00000000-0000-4000-8000-00000000000a/finance",
    ]) {
      await page.goto(url + path);
      await expect(
        page.getByRole("heading", { name: "This route is not available" }),
      ).toBeVisible();
      await expect(page.getByRole("textbox")).toHaveCount(0);
      await expect(
        page.getByRole("link", { name: "Return to foundation" }),
      ).toBeVisible();
    }
  });
}
test("NGO and Operations keep independent origin, direction and navigation state", async ({
  browser,
}) => {
  const context = await browser.newContext();
  const ngo = await context.newPage();
  const ops = await context.newPage();
  try {
    await ngo.goto("http://127.0.0.1:5173/foundation/accessibility");
    await ngo.getByRole("combobox").selectOption("ur");
    await ops.goto("http://127.0.0.1:5174");
    await expect(ngo.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(ops.locator("html")).toHaveAttribute("dir", "ltr");
    await expect(ops.getByRole("rowheader", { name: "OPS-01" })).toBeVisible();
    await expect(ops.getByRole("rowheader", { name: "ORG-04" })).toHaveCount(0);
  } finally {
    await context.close();
  }
});
