import {
  ApiError,
  ScopeState,
  StaleResponseError,
  normalizeError,
} from "./index";
import type { ContractSchemas, SyntheticTransport } from "./index";
import spec from "../../api-contracts/openapi-v1.json";
type Policy = ContractSchemas["ControlledOnboardingRequirements"];
export class OperationsPolicyClient {
  constructor(
    readonly state: ScopeState,
    private transport?: SyntheticTransport,
  ) {}
  async read(): Promise<Policy> {
    if (!this.transport)
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (!this.state.currentScope)
      throw new ApiError("session", 401, "SESSION_REQUIRED");
    const active = this.state.begin();
    try {
      const response = await this.transport(
        "/api/v1/controlled-onboarding/requirements/",
        {
          method: "GET",
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          referrerPolicy: "no-referrer",
          signal: active.signal,
          headers: { Accept: "application/json" },
        },
      );
      const body: unknown = await response.json().catch(() => undefined);
      active.assertCurrent();
      if (!response.ok) {
        const error = normalizeError(
          response.status,
          body,
          response.headers.get("Retry-After"),
        );
        if ([401, 403, 409].includes(response.status))
          this.state.invalidate("access-denied");
        throw error;
      }
      // The approved requirements projection is entirely constants. Validate
      // all fields, including blocked flags; future capability success needs review.
      const schema = spec.components.schemas.ControlledOnboardingRequirements;
      if (
        !body ||
        typeof body !== "object" ||
        Array.isArray(body) ||
        Object.keys(body).length !== Object.keys(schema.properties).length
      )
        throw new ApiError("contract", 0, "INVALID_RESPONSE");
      for (const [key, property] of Object.entries(schema.properties)) {
        const expected =
          "const" in property
            ? property.const
            : "enum" in property
              ? property.enum[0]
              : undefined;
        if (
          JSON.stringify((body as Record<string, unknown>)[key]) !==
          JSON.stringify(expected)
        )
          throw new ApiError("contract", 0, "INVALID_RESPONSE");
      }
      return structuredClone(body) as Policy;
    } catch (error) {
      if (error instanceof ApiError || error instanceof StaleResponseError)
        throw error;
      active.assertCurrent();
      throw new ApiError("network", 0, "NETWORK_UNAVAILABLE");
    } finally {
      active.finish();
    }
  }
}
