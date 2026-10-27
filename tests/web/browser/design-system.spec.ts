import { test, expect } from "@playwright/test";
import axe from "axe-core";
import { mkdirSync } from "node:fs";
const evidence = "coverage/design-system";
for (const [portal, url] of [
  ["ngo", "http://127.0.0.1:5173"],
  ["ops", "http://127.0.0.1:5174"],
] as const) {
  test(`${portal}: v1 component/modal keyboard, targets, font and screenshots`, async ({
    page,
  }) => {
    mkdirSync(evidence, { recursive: true });
    const calls: string[] = [];
    const external: string[] = [];
    page.on("request", (r) => {
      if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
      if (new URL(r.url()).origin !== url) external.push(r.url());
    });
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.goto(url);
    await page.evaluate(() => document.fonts.ready);
    await expect(page.locator(".workspace-context button")).toBeDisabled();
    await page.screenshot({
      path: `${evidence}/${portal}-overview-en-desktop.png`,
      fullPage: true,
    });
    await page.goto(url + "/foundation/accessibility");
    await page.evaluate(() => document.fonts.ready);
    const primary = page.getByRole("button", { name: "Preview confirmation" });
    await primary.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Cancel", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(
      page.getByRole("button", { name: "Confirm example", exact: true }),
    ).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(
      page.getByRole("button", { name: "Cancel", exact: true }),
    ).toBeFocused();
    await page.addScriptTag({ content: axe.source });
    expect(
      await page.evaluate(
        async () =>
          (
            await (window as unknown as { axe: typeof axe }).axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
              },
            })
          ).violations,
      ),
    ).toEqual([]);
    await page.screenshot({
      path: `${evidence}/${portal}-dialog-en-desktop.png`,
    });
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
    await expect(primary).toBeFocused();
    await primary.click();
    await page
      .getByRole("button", { name: "Confirm example", exact: true })
      .click();
    await expect(
      page.getByText("Local confirmation dismissed; no command ran."),
    ).toBeVisible();
    await expect(primary).toBeFocused();
    await expect(
      page.getByRole("button", { name: "Destructive unavailable" }),
    ).toBeDisabled();
    await expect(
      page.getByRole("button", { name: "Loading example" }),
    ).toHaveAttribute("aria-busy", "true");
    expect(
      await primary.evaluate((e) => e.getBoundingClientRect().height),
    ).toBeGreaterThanOrEqual(44);
    expect(
      await page
        .locator("table")
        .evaluate((e) => parseFloat(getComputedStyle(e).fontSize)),
    ).toBeGreaterThanOrEqual(14);
    expect(await page.evaluate(() => document.fonts.check("16px Inter"))).toBe(
      true,
    );
    await page
      .getByRole("textbox", { name: "Example notes" })
      .fill("Synthetic draft");
    await page
      .getByRole("combobox", { name: "Display language" })
      .selectOption("ur");
    await expect(page.getByRole("textbox", { name: "مثالی نوٹس" })).toHaveValue(
      "",
    );
    await page.setViewportSize({ width: 320, height: 900 });
    await page.evaluate(() => document.fonts.ready);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      await page.evaluate(() =>
        document.fonts.check('16px "Noto Sans Arabic Variable"', "اردو"),
      ),
    ).toBe(true);
    expect(
      await page.evaluate(
        async () =>
          (
            await (window as unknown as { axe: typeof axe }).axe.run(document, {
              runOnly: {
                type: "tag",
                values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
              },
            })
          ).violations,
      ),
    ).toEqual([]);
    await page.screenshot({
      path: `${evidence}/${portal}-components-ur-mobile.png`,
      fullPage: true,
    });
    await page
      .getByRole("button", { name: "تصدیق کی مثال", exact: true })
      .click();
    await expect(page.getByRole("dialog")).toBeVisible();
    expect(
      await page
        .getByRole("dialog")
        .evaluate((e) => e.getBoundingClientRect().right <= innerWidth),
    ).toBe(true);
    await page.keyboard.press("Escape");
    // 200% text scaling (not a substitute for a real browser zoom/device review).
    await page.evaluate(
      () => (document.documentElement.style.fontSize = "200%"),
    );
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(calls).toEqual([]);
    expect(external).toEqual([]);
  });
}

for (const [name, url, id] of [
  ["ngo-registry", "http://127.0.0.1:5173/registry", "ORG-01"],
  ["ngo-verification", "http://127.0.0.1:5173/verification", "ORG-03"],
  ["ops-controlled", "http://127.0.0.1:5174/controlled-onboarding", "PWC-01"],
  ["ops-review", "http://127.0.0.1:5174/verification", "PWC-01"],
] as const) {
  test(`${name}: gated screen AA, reflow, title and visual evidence`, async ({
    page,
  }) => {
    const calls: string[] = [];
    page.on("request", (r) => {
      if (new URL(r.url()).pathname.startsWith("/api/")) calls.push(r.url());
    });
    mkdirSync(evidence, { recursive: true });
    for (const locale of ["en", "ur"])
      for (const width of [1440, 320]) {
        await page.setViewportSize({ width, height: 1000 });
        await page.goto(url);
        await page
          .getByRole("combobox", { name: "Display language" })
          .selectOption(locale);
        await page.evaluate(() => document.fonts.ready);
        await expect(page.getByRole("heading", { level: 1 })).toContainText(id);
        await expect(page).not.toHaveTitle(/route is not available/i);
        expect(
          await page.evaluate(
            () => document.documentElement.scrollWidth <= innerWidth,
          ),
        ).toBe(true);
        await page.addScriptTag({ content: axe.source });
        expect(
          await page.evaluate(
            async () =>
              (
                await (window as unknown as { axe: typeof axe }).axe.run(
                  document,
                  {
                    runOnly: {
                      type: "tag",
                      values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
                    },
                  },
                )
              ).violations,
          ),
        ).toEqual([]);
        // Disabled operational controls stay disabled across language/layout changes.
        const commands = page.locator("main button");
        if (name === "ops-review") expect(await commands.count()).toBe(0);
        else expect(await commands.count()).toBeGreaterThan(0);
        for (const button of await commands.all())
          await expect(button).toBeDisabled();
        if (
          (locale === "en" && width === 1440) ||
          (locale === "ur" && width === 320)
        )
          await page.screenshot({
            path: `${evidence}/${name}-${locale}-${width}.png`,
            fullPage: true,
          });
      }
    expect(calls).toEqual([]);
  });
}
