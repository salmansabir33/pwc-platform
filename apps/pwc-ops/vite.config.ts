import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// Exact optional preview host only; no blanket host allowlist or API proxy.
const previewHost = process.env.PWC_PREVIEW_HOST;
if (previewHost && !/^[a-zA-Z0-9.-]+$/.test(previewHost))
  throw new Error("Invalid preview hostname");
export default defineConfig({
  plugins: [react()],
  publicDir: "../../packages/design-tokens/public",
  server: { host: "0.0.0.0", allowedHosts: previewHost ? [previewHost] : [] },
  build: { sourcemap: false, target: "es2022" },
});
