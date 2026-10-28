import {
  ApiError,
  ScopeState,
  StaleResponseError,
  normalizeError,
} from "./index";
import type { ContractSchemas, SyntheticTransport } from "./index";
export type WorkspacePage = ContractSchemas["WorkspacePage"];
export type WorkspaceDetail = ContractSchemas["WorkspaceDetail"];
export type WorkspaceApplication = ContractSchemas["WorkspaceApplication"];
export type DirectoryPage = ContractSchemas["RegistrySearchPage"];
export type DirectoryFilter = Readonly<{
  q: string;
  city: string;
  classification: "" | "registered" | "unregistered";
}>;
const object = (v: unknown): v is Record<string, unknown> =>
  !!v && typeof v === "object" && !Array.isArray(v);
const id = (v: unknown): v is string =>
  typeof v === "string" &&
  /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(v);
const revision = (v: unknown) => Number.isSafeInteger(v) && Number(v) > 0;
const text = (v: unknown, max: number) =>
  typeof v === "string" && v.length <= max && !/[\u0000-\u001f\u007f]/.test(v);
const closed = (v: Record<string, unknown>, keys: string[]) =>
  keys.length === Object.keys(v).length &&
  keys.every((k) => Object.hasOwn(v, k));
function bad(): never {
  throw new ApiError("contract", 0, "INVALID_RESPONSE");
}
function page(v: unknown): asserts v is Record<string, unknown> & {
  results: unknown[];
  next_cursor: string | null;
} {
  if (
    !object(v) ||
    !Array.isArray(v.results) ||
    v.results.length > 20 ||
    !(v.next_cursor === null || text(v.next_cursor, 1024))
  )
    bad();
}
export function parseDirectory(v: unknown): DirectoryPage {
  page(v);
  if (!closed(v, ["results", "next_cursor"])) bad();
  const seen = new Set<string>();
  for (const row of v.results) {
    if (
      !object(row) ||
      !closed(row, ["id", "name", "city", "classification"]) ||
      !id(row.id) ||
      seen.has(row.id) ||
      !text(row.name, 250) ||
      !text(row.city, 100) ||
      !["registered", "unregistered"].includes(String(row.classification))
    )
      bad();
    seen.add(row.id);
  }
  return structuredClone(v) as DirectoryPage;
}
export function parseWorkspace(v: unknown): WorkspacePage {
  page(v);
  if (
    !closed(v, [
      "results",
      "next_cursor",
      "administration_available",
      "intake_available",
      "verification_available",
    ]) ||
    v.administration_available !== false ||
    v.intake_available !== false ||
    typeof v.verification_available !== "boolean"
  )
    bad();
  const seen = new Set<string>();
  for (const row of v.results) {
    if (
      !object(row) ||
      !closed(row, [
        "id",
        "kind",
        "organization_id",
        "revision",
        "state",
        "name",
        "city",
        "classification",
        "can_withdraw",
        "verification",
      ]) ||
      !id(row.id) ||
      seen.has(row.id) ||
      !id(row.organization_id) ||
      !revision(row.revision) ||
      !["draft", "claim"].includes(String(row.kind)) ||
      ![
        "draft",
        "submitted",
        "pending",
        "needs_information",
        "rejected",
        "withdrawn",
      ].includes(String(row.state)) ||
      typeof row.can_withdraw !== "boolean" ||
      !Array.isArray(row.verification) ||
      row.verification.length > 2
    )
      bad();
    seen.add(row.id);
    if (
      row.kind === "claim"
        ? row.name !== null || row.city !== null || row.classification !== null
        : !text(row.name, 250) ||
          !text(row.city, 100) ||
          !["registered", "unregistered"].includes(String(row.classification))
    )
      bad();
    if (!v.verification_available && row.verification.length) bad();
    for (const c of row.verification) {
      if (
        !object(c) ||
        !closed(c, [
          "id",
          "purpose",
          "state",
          "revision",
          "source_revision",
          "stale",
        ]) ||
        !id(c.id) ||
        !revision(c.revision) ||
        !revision(c.source_revision) ||
        !["organization_eligibility", "representative_mandate"].includes(
          String(c.purpose),
        ) ||
        !["draft", "submitted", "withdrawn"].includes(String(c.state)) ||
        c.stale !== (c.source_revision !== row.revision)
      )
        bad();
    }
  }
  return structuredClone(v) as WorkspacePage;
}
/** Reuse the exact closed page projection validator; no receipt semantics. */
export function parseWorkspaceDetail(v: unknown): WorkspaceDetail {
  if (
    !object(v) ||
    !closed(v, [
      "application",
      "administration_available",
      "intake_available",
      "verification_available",
    ])
  )
    bad();
  const parsed = parseWorkspace({
    results: [v.application],
    next_cursor: null,
    administration_available: v.administration_available,
    intake_available: v.intake_available,
    verification_available: v.verification_available,
  });
  return {
    application: parsed.results[0]!,
    administration_available: false,
    intake_available: false,
    verification_available: parsed.verification_available,
  };
}
export interface DirectoryGateway {
  search(
    filters: DirectoryFilter,
    cursor?: string,
    signal?: AbortSignal,
  ): Promise<DirectoryPage>;
}
/** Explicit public-only exception: no cookies, bearer tokens, private paths or writes.
 * Existing W1 personal/domain ApiClient remains disabled; no generic fetch API.
 */
export class PublicDirectoryClient implements DirectoryGateway {
  constructor(private readonly transport: SyntheticTransport) {}
  async search(
    filters: DirectoryFilter,
    cursor?: string,
    signal?: AbortSignal,
  ): Promise<DirectoryPage> {
    if (
      !text(filters.q, 250) ||
      !text(filters.city, 250) ||
      !["", "registered", "unregistered"].includes(filters.classification) ||
      (cursor !== undefined && !text(cursor, 1024))
    )
      throw new ApiError("validation", 0, "INVALID_FILTER");
    const params = new URLSearchParams({
      q: filters.q,
      city: filters.city,
      classification: filters.classification,
    });
    if (cursor) params.set("cursor", cursor);
    try {
      const response = await this.transport("/api/v1/directory/?" + params, {
        method: "GET",
        credentials: "omit",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
        headers: { Accept: "application/json" },
        ...(signal ? { signal } : {}),
      });
      const body: unknown = await response.json().catch(() => undefined);
      if (!response.ok)
        throw normalizeError(
          response.status,
          body,
          response.headers.get("Retry-After"),
        );
      return parseDirectory(body);
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (signal?.aborted) throw new StaleResponseError();
      throw new ApiError("network", 0, "NETWORK_UNAVAILABLE");
    }
  }
}
export interface WorkspaceGateway {
  readonly state: ScopeState;
  list(
    kind: "draft" | "claim",
    state?: string,
    cursor?: string,
  ): Promise<WorkspacePage>;
  detail?(kind: "draft" | "claim", id: string): Promise<WorkspaceDetail>;
  withdraw(item: WorkspaceApplication): Promise<void>;
}
/** Owner history port only; NO production networking escape for W1 or domain commands. */
export class HistoricalWorkspaceClient implements WorkspaceGateway {
  constructor(
    readonly state: ScopeState,
    private transport?: SyntheticTransport,
    private csrf?: () => string | null,
  ) {}
  private async request(
    path: string,
    body?: { revision: number },
  ): Promise<unknown> {
    if (!this.transport)
      throw new ApiError("disabled", 0, "W1_NETWORK_DISABLED");
    if (!this.state.currentScope)
      throw new ApiError("session", 401, "SESSION_REQUIRED");
    const token = body ? this.csrf?.() : null;
    if (body && !token) throw new ApiError("csrf", 0, "CSRF_REQUIRED");
    const active = this.state.begin();
    try {
      const response = await this.transport(path, {
        method: body ? "POST" : "GET",
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
        signal: active.signal,
        headers: {
          Accept: "application/json",
          ...(body
            ? { "Content-Type": "application/json", "X-CSRFToken": token! }
            : {}),
        },
        ...(body ? { body: JSON.stringify(body) } : {}),
      });
      const payload: unknown = await response.json().catch(() => undefined);
      active.assertCurrent();
      if (!response.ok) {
        const error = normalizeError(
          response.status,
          payload,
          response.headers.get("Retry-After"),
        );
        if ([401, 403, 409].includes(response.status))
          this.state.invalidate(
            response.status === 401 ? "session-invalid" : "access-denied",
          );
        throw error;
      }
      return payload;
    } catch (e) {
      if (e instanceof ApiError || e instanceof StaleResponseError) throw e;
      active.assertCurrent();
      throw new ApiError("network", 0, "NETWORK_UNCERTAIN");
    } finally {
      active.finish();
    }
  }
  async list(
    kind: "draft" | "claim",
    state = "",
    cursor?: string,
  ): Promise<WorkspacePage> {
    if (
      !["draft", "claim"].includes(kind) ||
      ![
        "",
        "draft",
        "submitted",
        "pending",
        "needs_information",
        "rejected",
        "withdrawn",
      ].includes(state) ||
      (cursor !== undefined && !text(cursor, 1024))
    )
      bad();
    const params = new URLSearchParams({ kind, state });
    if (cursor) params.set("cursor", cursor);
    return parseWorkspace(
      await this.request("/api/v1/registry/workspace/?" + params),
    );
  }
  async detail(
    kind: "draft" | "claim",
    value: string,
  ): Promise<WorkspaceDetail> {
    if (!["draft", "claim"].includes(kind) || !id(value)) bad();
    const result = parseWorkspaceDetail(
      await this.request(
        `/api/v1/registry/workspace/${kind === "draft" ? "drafts" : "claims"}/${value}/`,
      ),
    );
    if (result.application.id !== value || result.application.kind !== kind)
      bad();
    return result;
  }
  async withdraw(item: WorkspaceApplication): Promise<void> {
    if (
      !id(item.id) ||
      !revision(item.revision) ||
      !["draft", "claim"].includes(item.kind) ||
      !item.can_withdraw
    )
      bad();
    const result = await this.request(
      `/api/v1/registry/${item.kind === "draft" ? "drafts" : "claims"}/${item.id}/withdraw/`,
      { revision: item.revision },
    );
    if (
      !object(result) ||
      result.id !== item.id ||
      result.state !== "withdrawn" ||
      result.revision !== item.revision + 1
    )
      bad();
  }
}
