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

describe.each(["ngo", "ops"] as const)("%s bounded public proxy", (app) => {
  it("proxies only the exact public directory path", async () => {
    vi.stubEnv("PWC_PUBLIC_API_TARGET", "http://127.0.0.1:8000");
    const proxy = (await config(app)).server?.proxy ?? {};
    const pattern = new RegExp(Object.keys(proxy)[0]!);
    expect(pattern.test("/api/v1/directory/?q=ngo")).toBe(true);
    expect(pattern.test("/api/v1/auth/me/")).toBe(false);
    expect(pattern.test("/api/v1/directory/../auth/me/")).toBe(false);
    expect(pattern.test("/api/v1/controlled-onboarding/records/")).toBe(false);
  });
  it.each([
    "https://outside.invalid",
    "http://127.0.0.1:0",
    "http://127.0.0.1:99999",
    "http://user:secret@127.0.0.1:8000",
    "http://127.0.0.1:8000/path",
  ])("rejects unsafe target %s", async (target) => {
    vi.stubEnv("PWC_PUBLIC_API_TARGET", target);
    await expect(config(app)).rejects.toThrow("Invalid public API target");
  });
});
