import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";
// jsdom has no canvas renderer; full contrast/visual checks run in Chromium.
HTMLCanvasElement.prototype.getContext = vi.fn(() => null);
afterEach(() => {
  cleanup();
});
