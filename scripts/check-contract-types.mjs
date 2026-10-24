// Regenerate in a disposable directory; never update checked files in check mode.
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
const directory = mkdtempSync(join(tmpdir(), "pwc-contract-types-"));
try {
  const path = join(directory, "schema.ts");
  execFileSync(
    process.execPath,
    [
      "node_modules/openapi-typescript/bin/cli.js",
      "packages/api-contracts/openapi-v1.json",
      "-o",
      path,
    ],
    { stdio: "inherit" },
  );
  if (
    !readFileSync(path).equals(
      readFileSync("packages/api-contracts/generated/schema.ts"),
    )
  )
    throw new Error(
      "Generated TypeScript contract drift; run npm run contracts:types and review the diff",
    );
} finally {
  rmSync(directory, { recursive: true, force: true });
}
