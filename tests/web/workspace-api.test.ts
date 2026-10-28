import { describe, it, expect, vi } from "vitest";
import {
  PublicDirectoryClient,
  HistoricalWorkspaceClient,
  parseDirectory,
  parseWorkspace,
  ScopeState,
} from "@pwc/web-api";
import type { WorkspacePage } from "@pwc/web-api";
const ID = "00000000-0000-4000-8000-000000000001";
export const historyPage = (): WorkspacePage => ({
  results: [
    {
      id: ID,
      organization_id: ID,
      kind: "draft",
      revision: 1,
      state: "submitted",
      name: "Synthetic Welfare",
      city: "City",
      classification: "unregistered",
      can_withdraw: true,
      verification: [
        {
          id: ID,
          purpose: "organization_eligibility",
          state: "submitted",
          revision: 1,
          source_revision: 1,
          stale: false,
        },
      ],
    },
  ],
  next_cursor: null,
  administration_available: false,
  intake_available: false,
  verification_available: true,
});
export function state() {
  const s = new ScopeState("ngo");
  s.switchScope({
    principalId: ID,
    sessionId: ID,
    organizationId: null,
    registryVersion: "v1",
    revision: "1",
  });
  return s;
}
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
describe("bounded public and owner-history clients", () => {
  it("can ONLY send fixed public GET, with no cookies, tokens or arbitrary routes", async () => {
    const transport = vi
      .fn()
      .mockResolvedValue(json({ results: [], next_cursor: null }));
    await new PublicDirectoryClient(transport).search({
      q: "خدمت",
      city: "City",
      classification: "",
    });
    const [url, init] = transport.mock.calls[0]!;
    expect(url).toMatch(/^\/api\/v1\/directory\/\?/);
    expect(init).toMatchObject({
      method: "GET",
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    expect(init.headers).not.toHaveProperty("Authorization");
    expect(init.headers).not.toHaveProperty("X-CSRFToken");
  });
  it("rejects extra/private fields, oversized pages and malformed public responses", () => {
    const row = {
      id: ID,
      name: "Synthetic",
      city: "City",
      classification: "registered",
    };
    for (const value of [
      { results: [{ ...row, email: "private" }], next_cursor: null },
      { results: Array(21).fill(row), next_cursor: null },
      { results: [row, row], next_cursor: null },
      { results: [], next_cursor: 7 },
    ])
      expect(() => parseDirectory(value)).toThrow();
  });
  it("fails safely for HTML, errors and redirects without echoing bodies", async () => {
    const api = new PublicDirectoryClient(
      vi.fn().mockResolvedValue(new Response("private html", { status: 503 })),
    );
    await expect(
      api.search({ q: "", city: "", classification: "" }),
    ).rejects.toMatchObject({
      status: 503,
      message: "Request could not be completed (server).",
    });
  });
  it("owner transport stays disabled by default and requires explicit current scope", async () => {
    await expect(
      new HistoricalWorkspaceClient(state()).list("draft"),
    ).rejects.toMatchObject({ kind: "disabled" });
    const transport = vi.fn();
    await expect(
      new HistoricalWorkspaceClient(new ScopeState("ngo"), transport).list(
        "draft",
      ),
    ).rejects.toMatchObject({ kind: "session" });
    expect(transport).not.toHaveBeenCalled();
  });
  it("uses canonical owner DTO and exact revision for actual withdrawal, with CSRF", async () => {
    const transport = vi
      .fn()
      .mockResolvedValueOnce(json(historyPage()))
      .mockResolvedValueOnce(json({ id: ID, revision: 2, state: "withdrawn" }));
    const api = new HistoricalWorkspaceClient(
      state(),
      transport,
      () => "masked-token",
    );
    const page = await api.list("draft");
    await api.withdraw(page.results[0]!);
    expect(transport.mock.calls[0]![0]).toBe(
      "/api/v1/registry/workspace/?kind=draft&state=",
    );
    expect(transport.mock.calls[1]![1]).toMatchObject({
      method: "POST",
      body: '{"revision":1}',
      headers: { "X-CSRFToken": "masked-token" },
    });
  });
  it("denies unsafe requests without CSRF and never retries lost responses", async () => {
    const transport = vi
      .fn()
      .mockRejectedValue(new Error("private connection note"));
    await expect(
      new HistoricalWorkspaceClient(state(), transport).withdraw(
        historyPage().results[0]!,
      ),
    ).rejects.toMatchObject({ kind: "csrf" });
    expect(transport).not.toHaveBeenCalled();
    await expect(
      new HistoricalWorkspaceClient(state(), transport, () => "token").withdraw(
        historyPage().results[0]!,
      ),
    ).rejects.toMatchObject({ code: "NETWORK_UNCERTAIN" });
    expect(transport).toHaveBeenCalledTimes(1);
  });
  it.each([401, 403, 409])("purges scope and cache on %s", async (status) => {
    const s = state();
    const transport = vi
      .fn()
      .mockResolvedValue(
        json({ error: { code: "DENIED", message: "private" } }, status),
      );
    await expect(
      new HistoricalWorkspaceClient(s, transport).list("draft"),
    ).rejects.toMatchObject({ status });
    expect(s.currentScope).toBeNull();
  });
  it("drops a late response after logout even when transport ignores cancellation", async () => {
    let complete!: (v: Response) => void;
    const transport = vi.fn(
      () =>
        new Promise<Response>((r) => {
          complete = r;
        }),
    );
    const s = state();
    const request = new HistoricalWorkspaceClient(s, transport).list("draft");
    s.invalidate("logout");
    complete(json(historyPage()));
    await expect(request).rejects.toMatchObject({ name: "StaleResponseError" });
  });
  it("rejects authority flags and inconsistent stale-source metadata", () => {
    const p = historyPage();
    p.administration_available = true as false;
    expect(() => parseWorkspace(p)).toThrow();
    const inconsistent = historyPage();
    inconsistent.results[0]!.verification[0]!.stale = true;
    expect(() => parseWorkspace(inconsistent)).toThrow();
  });
});
