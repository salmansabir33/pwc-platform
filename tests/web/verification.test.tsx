import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider } from "@pwc/web-i18n";
import {
  Verification,
  type VerificationGateway,
} from "../../apps/ngo-web/src/Verification";
import examples from "../../packages/api-contracts/examples-v1.json";
const fixture = (id: string) =>
  examples.cases.find(
    (c) =>
      c.operationId === id && c.kind === "response" && (c.status ?? 999) < 300,
  )!.body;
function gateway(): VerificationGateway {
  return {
    list: vi.fn().mockResolvedValue({
      results: [
        fixture("verificationCreateCase") as Awaited<
          ReturnType<VerificationGateway["list"]>
        >["results"][number],
      ],
      next_cursor: null,
    }),
    create: vi.fn().mockResolvedValue(fixture("verificationCreateCase")),
    change: vi.fn().mockResolvedValue(fixture("verificationSubmit")),
    requirements: vi
      .fn()
      .mockResolvedValue(fixture("verificationRequirements")),
    history: vi.fn().mockResolvedValue({ results: [], next_cursor: null }),
    preparation: vi.fn().mockResolvedValue({ results: [], next_cursor: null }),
    prepare: vi.fn(),
    replace: vi.fn(),
  };
}
describe("04B disconnected verification components", () => {
  it("keeps W1 blocked and exposes no file chooser or review success", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const { container } = render(
      <LocaleProvider>
        <Verification />
      </LocaleProvider>,
    );
    expect(screen.getByRole("status")).toHaveTextContent("Files unavailable");
    expect(
      screen.getByRole("button", { name: "Load own cases" }),
    ).toBeDisabled();
    expect(container.querySelector('input[type="file"]')).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("uses contract revisions and never represents submission as verification", async () => {
    const api = gateway();
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Verification gateway={api} scope="synthetic" />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Load own cases" }));
    await user.click(
      screen.getByRole("button", { name: "Requirements and history" }),
    );
    expect(
      screen.getByText(/unapproved · preparation_record_only/),
    ).toBeVisible();
    await user.click(
      screen.getByRole("button", { name: "Submit preparation only" }),
    );
    expect(api.change).toHaveBeenCalledWith(
      "00000000-0000-4000-8000-000000000001",
      "submit",
      1,
    );
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(
      "submitted",
    );
    expect(
      screen.getByRole("button", { name: "Submit preparation only" }),
    ).toBeDisabled();
  });
  it("does not infer reviewer entitlement even with an injected gateway", () => {
    const api = gateway();
    render(
      <LocaleProvider>
        <Verification gateway={api} review />
      </LocaleProvider>,
    );
    expect(screen.queryByRole("button")).toBeNull();
    expect(api.list).not.toHaveBeenCalled();
  });
  it("clears private cases on scope invalidation and discards late results", async () => {
    const api = gateway();
    let resolve!: (v: Awaited<ReturnType<VerificationGateway["list"]>>) => void;
    vi.mocked(api.list).mockImplementation(
      () =>
        new Promise((r) => {
          resolve = r;
        }),
    );
    const user = userEvent.setup();
    const { rerender } = render(
      <LocaleProvider>
        <Verification gateway={api} scope="a" />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Load own cases" }));
    rerender(
      <LocaleProvider>
        <Verification gateway={api} scope="b" />
      </LocaleProvider>,
    );
    resolve({
      results: [
        fixture("verificationCreateCase") as Awaited<
          ReturnType<VerificationGateway["list"]>
        >["results"][number],
      ],
      next_cursor: null,
    });
    expect(screen.queryByRole("heading", { level: 2 })).toBeNull();
  });
  it("shows a safe conflict without replay or success", async () => {
    const api = gateway();
    vi.mocked(api.list).mockRejectedValue(new Error("private"));
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <Verification gateway={api} />
      </LocaleProvider>,
    );
    await user.click(screen.getByRole("button", { name: "Load own cases" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Reload");
    expect(screen.getByRole("alert")).not.toHaveTextContent("private");
    expect(api.list).toHaveBeenCalledTimes(1);
  });
});
