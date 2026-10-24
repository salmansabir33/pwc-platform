import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

function sources(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory()
      ? sources(path)
      : /\.(ts|tsx)$/.test(path)
        ? [path]
        : [];
  });
}
const json = (path: string) =>
  JSON.parse(readFileSync(path, "utf8")) as {
    private: boolean;
    dependencies?: Record<string, string>;
    peerDependencies?: Record<string, string>;
  };

describe("W1 package and runtime boundaries", () => {
  it("keeps shared source independent of either application and UI independent of API state", () => {
    for (const pkg of ["web-api", "web-ui", "web-i18n"]) {
      for (const path of sources(`packages/${pkg}/src`)) {
        const text = readFileSync(path, "utf8");
        expect(text, path).not.toMatch(
          /(?:from\s*|import\s*\()["'][^"']*(?:apps\/|@pwc\/(?:ngo-web|pwc-ops))/,
        );
        if (pkg === "web-ui") expect(text, path).not.toContain("@pwc/web-api");
      }
    }
  });
  it("keeps both apps private, independently rooted and incapable of env-based live enablement", () => {
    for (const app of ["ngo-web", "pwc-ops"]) {
      expect(json(`apps/${app}/package.json`).private).toBe(true);
      const config = readFileSync(`apps/${app}/src/config.ts`, "utf8");
      expect(config).toContain('network: "disabled"');
      expect(config).not.toContain("import.meta.env");
      const appSource = readFileSync(`apps/${app}/src/App.tsx`, "utf8");
      expect(appSource).toContain("createFoundationRuntime(config.appId)");
      expect(appSource).toContain("<Routes>");
      expect(readFileSync(`apps/${app}/src/main.tsx`, "utf8")).toContain(
        "createRoot(",
      );
    }
    for (const pkg of ["design-tokens", "web-api", "web-ui", "web-i18n"])
      expect(json(`packages/${pkg}/package.json`).private).toBe(true);
  });
});
