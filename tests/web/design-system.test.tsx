import { describe, it, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {
  Button,
  TextField,
  TextArea,
  SelectField,
  Choice,
  Badge,
  Banner,
  DataTable,
  Pagination,
} from "@pwc/web-ui";
import tokens from "../../packages/design-tokens/tokens.v1.json";
function luminance(hex: string) {
  const rgb = hex
    .slice(1)
    .match(/../g)!
    .map((x) => parseInt(x, 16) / 255)
    .map((x) => (x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4));
  return rgb[0]! * 0.2126 + rgb[1]! * 0.7152 + rgb[2]! * 0.0722;
}
function contrast(a: string, b: string) {
  const x = luminance(a),
    y = luminance(b);
  return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
}
describe("Design system v1.0 contracts", () => {
  it("maps every color and scale to both generated adapters", () => {
    const css = readFileSync("packages/design-tokens/generated.css", "utf8");
    const dart = readFileSync("apps/mobile/lib/design/tokens.g.dart", "utf8");
    for (const [name, value] of Object.entries(tokens.colors)) {
      expect(css).toContain(value.toLowerCase());
      expect(dart).toContain(
        `static const ${name} = Color(0xff${value.slice(1).toLowerCase()})`,
      );
    }
    for (const n of tokens.typeSizes)
      expect(css).toContain(`--ds-type-${n}: ${n / 16}rem`);
    expect(dart).toContain("'Noto Sans Arabic Variable'");
  });
  it("passes normal-text AA across all intended semantic pairings", () => {
    const c = tokens.colors;
    for (const fg of [
      c.textPrimary,
      c.textSecondary,
      c.ngoPrimary,
      c.opsPrimary,
      c.success,
      c.warning,
      c.danger,
      c.info,
      c.focus,
    ])
      for (const bg of [c.surface, c.canvas])
        expect(contrast(fg, bg), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
    for (const tone of ["success", "warning", "danger", "info"] as const)
      expect(contrast(c[tone], c[`${tone}Background`])).toBeGreaterThanOrEqual(
        4.5,
      );
    for (const state of [
      "ngoPrimary",
      "ngoHover",
      "ngoPressed",
      "opsPrimary",
      "opsHover",
      "opsPressed",
      "danger",
    ] as const)
      expect(contrast(c.surface, c[state])).toBeGreaterThanOrEqual(4.5);
    expect(
      contrast(c.disabledForeground, c.disabledBackground),
    ).toBeGreaterThanOrEqual(4.5);
    expect(contrast(c.controlBorder, c.surface)).toBeGreaterThanOrEqual(3);
    expect(contrast(c.controlBorder, c.canvas)).toBeGreaterThanOrEqual(3);
    expect(contrast(c.focus, c.surface)).toBeGreaterThanOrEqual(3);
  });
  it("keeps button names, variant classes, caller classes and blocks busy commands", async () => {
    const action = vi.fn();
    render(
      <Button variant="destructive" busy className="caller" onClick={action}>
        Withdraw
      </Button>,
    );
    const b = screen.getByRole("button", { name: /Withdraw/ });
    expect(b).toHaveClass("button", "button-destructive", "caller");
    expect(b).toHaveAttribute("aria-busy", "true");
    expect(b).toBeDisabled();
    await userEvent.click(b);
    expect(action).not.toHaveBeenCalled();
  });
  it("associates labels, hints and errors and honors caller IDs", () => {
    render(
      <>
        <TextField
          label="Search"
          hint="Public registry only"
          id="search"
          type="search"
          error="Try another name"
        />
        <TextArea label="Notes" hint="No private documents" error="Required" />
        <SelectField label="State" error="Choose" defaultValue="">
          <option value="">Select</option>
        </SelectField>
        <Choice label="Acknowledge" />
      </>,
    );
    expect(screen.getByRole("searchbox")).toHaveAttribute("id", "search");
    expect(screen.getByRole("searchbox")).toHaveAccessibleDescription(
      "Public registry only Try another name",
    );
    expect(screen.getByRole("textbox")).toHaveAccessibleDescription(
      "No private documents Required",
    );
    expect(screen.getByRole("combobox")).toHaveAccessibleDescription("Choose");
    expect(screen.getByRole("checkbox")).toHaveAccessibleName("Acknowledge");
  });
  it("uses text for status, real empty rows and absent-pagination denial", () => {
    render(
      <>
        <Badge tone="restricted">Restricted</Badge>
        <Banner tone="danger" title="Unavailable" urgent>
          No command ran.
        </Banner>
        <DataTable
          caption="Registry"
          headers={["Name"]}
          rows={[]}
          empty="No results"
        />
        <Pagination
          label="Registry pages"
          previousLabel="Previous"
          nextLabel="Next"
        />
      </>,
    );
    expect(screen.getByText("Restricted")).toHaveClass("tone-restricted");
    expect(screen.getByRole("alert")).toHaveTextContent("No command ran.");
    expect(screen.getByRole("table")).toHaveAccessibleName("Registry");
    expect(screen.getByRole("cell")).toHaveTextContent("No results");
    expect(screen.getByRole("button", { name: "Next" })).toBeDisabled();
  });
});
