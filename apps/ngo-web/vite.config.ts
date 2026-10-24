import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Exact optional preview host only; no blanket host allowlist or API proxy.
const previewHost = process.env.PWC_PREVIEW_HOST;
// A leading dot has wildcard/suffix semantics in Vite. Permit DNS labels only.
const exactHostname =
  /^(?=.{1,253}$)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
if (
  previewHost &&
  (previewHost.trim() !== previewHost || !exactHostname.test(previewHost))
)
  throw new Error("Invalid preview hostname");
export default defineConfig({
  plugins: [react()],
  publicDir: "../../packages/design-tokens/public",
  server: { host: "0.0.0.0", allowedHosts: previewHost ? [previewHost] : [] },
  build: { sourcemap: false, target: "es2022" },
});
