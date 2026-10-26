import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    environment: "jsdom",
    reporters: ["default", "junit"],
    outputFile: { junit: "coverage/web-junit.xml" },
    setupFiles: ["./tests/web/setup.ts"],
    include: ["tests/web/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    clearMocks: true,
  },
});
