import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/web/setup.ts"],
    include: ["tests/web/**/*.test.{ts,tsx}"],
    restoreMocks: true,
    clearMocks: true,
  },
});
