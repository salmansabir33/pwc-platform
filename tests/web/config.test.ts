import { afterEach, describe, expect, it, vi } from "vitest";

async function config(app: "ngo" | "ops") {
  vi.resetModules();
  return app === "ngo"
    ? (await import("../../apps/ngo-web/vite.config")).default
    : (await import("../../apps/pwc-ops/vite.config")).default;
}
afterEach(() => vi.unstubAllEnvs());

describe.each(["ngo", "ops"] as const)(
  "%s exact preview-host configuration",
  (app) => {
    it.each([
      ".example.invalid",
      "example..invalid",
      "-bad.invalid",
      "bad-.invalid",
      "host.invalid\n",
      "*.invalid",
      "https://host.invalid",
      "host.invalid:443",
      "host.invalid/path",
      "a".repeat(64) + ".invalid",
      "a.".repeat(127) + "invalid",
    ])("rejects non-canonical host %s", async (host) => {
      vi.stubEnv("PWC_PREVIEW_HOST", host);
      await expect(config(app)).rejects.toThrow("Invalid preview hostname");
    });
    it("accepts one explicit hostname rather than a wildcard or suffix", async () => {
      vi.stubEnv("PWC_PREVIEW_HOST", "5173-example.e2b.app");
      expect((await config(app)).server?.allowedHosts).toEqual([
        "5173-example.e2b.app",
      ]);
    });
  },
);
