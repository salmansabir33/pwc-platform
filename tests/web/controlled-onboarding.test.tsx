import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LocaleProvider } from "@pwc/web-i18n";
import { ControlledOnboarding } from "../../apps/pwc-ops/src/ControlledOnboarding";

describe("revised offline controlled onboarding", () => {
  it("is unavailable without a reviewer/bootstrap/network shortcut", () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const { container } = render(
      <LocaleProvider>
        <ControlledOnboarding />
      </LocaleProvider>,
    );
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "PWC-01",
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "independent acceptance",
    );
    expect(
      screen.getByRole("button", { name: "Approve record" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Preview synthetic revision" }),
    ).toBeDisabled();
    expect(container.querySelector("input[type=file]")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("prepares only local synthetic revisions and never claims approval", async () => {
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <ControlledOnboarding synthetic scope="synthetic" />
      </LocaleProvider>,
    );
    for (const [label, value] of [
      ["NGO display name", "Synthetic Welfare"],
      ["City", "Faisalabad"],
      ["External nominee reference", "NOM_TEST"],
      ["Official nomination reference", "APPOINT_TEST"],
      ["External eligibility evidence reference", "EVIDENCE_TEST"],
      ["External mandate evidence reference", "MANDATE_TEST"],
      ["External examination method reference", "METHOD_TEST"],
    ] as const)
      await user.type(screen.getByLabelText(label), value);
    fireEvent.change(screen.getByLabelText("External examination date"), {
      target: { value: "2026-10-27" },
    });
    await user.click(
      screen.getByRole("button", { name: "Preview synthetic revision" }),
    );
    expect(
      screen.getByRole("heading", {
        name: "Synthetic revision 1 · not submitted",
      }),
    ).toBeVisible();
    await user.clear(screen.getByLabelText("NGO display name"));
    await user.type(
      screen.getByLabelText("NGO display name"),
      "Changed Synthetic",
    );
    await user.click(
      screen.getByRole("button", { name: "Preview synthetic revision" }),
    );
    expect(screen.getByText("Synthetic Welfare · Faisalabad")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Send recipient-bound invitation" }),
    ).toBeDisabled();
    expect(screen.getAllByText(/No server record/)).toHaveLength(2);
  });
  it("rejects URLs and numeric-only strings as opaque reference handles", () => {
    render(
      <LocaleProvider>
        <ControlledOnboarding synthetic />
      </LocaleProvider>,
    );
    const field = screen.getByLabelText(
      "External eligibility evidence reference",
    );
    fireEvent.change(field, {
      target: { value: "https://private.invalid/document" },
    });
    expect(field).toBeInvalid();
    fireEvent.change(field, { target: { value: "12345678" } });
    expect(field).toBeInvalid();
    fireEvent.change(field, { target: { value: "CUSTODY_TEST" } });
    expect(field).toBeValid();
  });
  it("clears private preparation on context invalidation", async () => {
    const user = userEvent.setup();
    const { rerender } = render(
      <LocaleProvider>
        <ControlledOnboarding synthetic scope="a" />
      </LocaleProvider>,
    );
    await user.type(screen.getByLabelText("NGO display name"), "Synthetic A");
    rerender(
      <LocaleProvider>
        <ControlledOnboarding synthetic scope="b" />
      </LocaleProvider>,
    );
    expect(screen.getByLabelText("NGO display name")).toHaveValue("");
  });
});
