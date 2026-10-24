import { describe, it, expect } from "vitest";
import {
  assertContractVersion,
  contractVersion,
  normalizeError,
  createFoundationRuntime,
} from "../../packages/web-api/src";
import type { ContractSchemas } from "../../packages/web-api/src";
import { browserOperations } from "../../packages/api-contracts/generated/browser-operations";
import spec from "../../packages/api-contracts/openapi-v1.json";

describe("canonical cross-platform contract compatibility", () => {
  it("checks contract release without inventing HTTP negotiation", () => {
    expect(contractVersion).toBe(spec.info.version);
    expect(() => assertContractVersion(contractVersion)).not.toThrow();
    expect(() => assertContractVersion("0.0.0")).toThrow(
      "Request could not be completed",
    );
  });
  it("uses exactly the existing closed browser allowlist and canonical paths/methods", () => {
    expect(Object.keys(browserOperations).sort()).toEqual(
      ["csrf", "me", "mfaStatus", "logout", "stepUp", "clearHold"].sort(),
    );
    const operations = Object.entries(spec.paths).flatMap(([path, methods]) =>
      Object.entries(methods).map(([method, op]) => ({ path, method, op })),
    );
    for (const [id, endpoint] of Object.entries(browserOperations)) {
      const canonical = operations.find(({ op }) => op.operationId === id)!;
      expect(canonical.path).toBe("/api/v1/auth/" + endpoint.path);
      expect(canonical.method.toUpperCase()).toBe(endpoint.method);
      expect(endpoint.transport).toBe("same-origin-cookie");
    }
  });
  it("preserves unavailable/hidden errors without claiming feature availability", () => {
    expect(
      normalizeError(503, { error: { code: "AUTH_UNAVAILABLE" } }).kind,
    ).toBe("server");
    expect(normalizeError(404, { error: { code: "not_found" } }).kind).toBe(
      "not-found",
    );
  });
  it("does not enable either portal when shared types become available", async () => {
    for (const portal of ["ngo", "ops"] as const)
      await expect(
        createFoundationRuntime(portal).api.request("me", (value) => value),
      ).rejects.toMatchObject({ code: "W1_NETWORK_DISABLED" });
  });
  it("types hold clearance separately from optional ordinary step-up assurance", () => {
    const step: ContractSchemas["StepUp"] = {
      intent_id: "synthetic",
      password: "synthetic",
    };
    const clear: ContractSchemas["ClearHold"] = {
      ...step,
      totp_code: "000000",
    };
    expect(clear.totp_code).toBe("000000");
    // @ts-expect-error A fresh factor is mandatory for hold-clear, not just ordinary step-up.
    const invalid: ContractSchemas["ClearHold"] = step;
    void invalid;
  });
});
