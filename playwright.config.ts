import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/web/browser",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: "list",
  use: {
    browserName: "chromium",
    headless: true,
    trace: "retain-on-failure",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE }
      : {},
  },
  webServer: [
    {
      command: "npm run preview -w @pwc/ngo-web",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run preview -w @pwc/pwc-ops",
      url: "http://127.0.0.1:5174",
      reuseExistingServer: !process.env.CI,
    },
  ],
});
