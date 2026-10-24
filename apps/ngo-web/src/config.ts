// Public, non-secret configuration. W1 has no live-network enable switch.
export const config = Object.freeze({
  appId: "ngo",
  title: "NGO Web Portal",
  stage: "W1",
  network: "disabled",
} as const);
