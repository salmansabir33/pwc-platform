import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests/web/browser",
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"], ["junit", { outputFile: "coverage/browser-junit.xml" }]],
  use: {
    browserName: "chromium",
    headless: true,
    trace: "retain-on-failure",
    launchOptions: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE
      ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE }
      : {},
  },
  webServer: [
    ...(process.env.PWC_PUBLIC_API_TARGET
      ? [
          {
            command: `${process.env.PWC_E2E_PYTHON ?? "python"} apps/backend/manage.py runserver 127.0.0.1:8000 --noreload`,
            url: "http://127.0.0.1:8000/api/v1/health/",
            reuseExistingServer: !process.env.CI,
          },
        ]
      : []),
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
