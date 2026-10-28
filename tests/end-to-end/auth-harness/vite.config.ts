import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  root: "tests/end-to-end/auth-harness",
  plugins: [react()],
  publicDir: "../../../packages/design-tokens/public",
  build: {
    outDir: "../../../.cache/auth-harness",
    emptyOutDir: true,
    target: "es2022",
  },
});
