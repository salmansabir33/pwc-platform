import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { LocaleProvider, useLocale } from "@pwc/web-i18n";
import {
  InvitationEnrollmentClient,
  ScopeState,
  consumeInvitationLink,
} from "@pwc/web-api";
import { InvitationEnrollment } from "../../apps/ngo-web/src/InvitationEnrollment";

const ID = "00000000-0000-4000-8000-000000000001";
const TOKEN = "t".repeat(43),
  CONTROL = "c".repeat(43),
  SECRET = "A".repeat(32);
const CODES = Array.from({ length: 10 }, (_, n) => String(n).repeat(43));
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status });
const verified = () =>
  json({
    status: "email_verified",
    enrollment_control: CONTROL,
    expires_at: new Date(Date.now() + 3600_000).toISOString(),
  });
const setup = () =>
  json({
    status: "mfa_required",
    secret: SECRET,
    otpauth_uri: `otpauth://totp/PWC:person?secret=${SECRET}&issuer=PWC`,
    expires_at: new Date(Date.now() + 300_000).toISOString(),
  });
function fixture(responses: Response[] = []) {
  const transport = vi.fn(async (url: string) => {
    if (url.endsWith("csrf/")) return json({ csrf_token: "a".repeat(64) });
    const next = responses.shift();
    if (!next) throw new Error("Unexpected request");
    return next;
  });
  const client = new InvitationEnrollmentClient(
    new ScopeState("ngo"),
    transport,
  );
  client.adopt({ id: ID, token: TOKEN });
  return { client, transport };
}
function link() {
  window.history.replaceState(
    null,
    "",
    `/account/invite#invitation_id=${ID}&token=${TOKEN}`,
  );
}
function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("ur")}>Urdu</button>;
}
afterEach(() => {
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});

describe("invitation security client", () => {
  it("scrubs valid, duplicate, extra and query-string credentials before parsing", () => {
    for (const [hash, search, valid] of [
      [`#invitation_id=${ID}&token=${TOKEN}`, "", true],
      [`#invitation_id=${ID}&token=${TOKEN}&token=${TOKEN}`, "", false],
      [`#invitation_id=${ID}&token=${TOKEN}&next=external`, "", false],
      [`#invitation_id=${ID}&token=${TOKEN}`, `?token=${TOKEN}`, false],
      ["#invalid", "", false],
    ] as const) {
      const history = { replaceState: vi.fn() };
      const parsed = consumeInvitationLink(
        { hash, search, pathname: "/account/invite" },
        history,
      );
      expect(!!parsed).toBe(valid);
      expect(history.replaceState).toHaveBeenCalledWith(
        null,
        "",
        "/account/invite",
      );
    }
  });
  it("does not fetch by default and redacts serialization", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const client = new InvitationEnrollmentClient(new ScopeState("ngo"));
    client.adopt({ id: ID, token: TOKEN });
    await expect(
      client.requestProof("person@example.invalid"),
    ).rejects.toMatchObject({ kind: "disabled" });
    expect(fetch).not.toHaveBeenCalled();
    expect(JSON.stringify(client)).not.toContain(TOKEN);
  });
  it("runs fixed routes with CSRF and no bearer/storage, clears capabilities after atomic completion", async () => {
    const { client, transport } = fixture([
      json({ status: "accepted" }, 202),
      verified(),
      setup(),
      json({ status: "complete", recovery_codes: CODES }, 201),
    ]);
    await client.requestProof("person@example.invalid");
    await client.confirmEmail("p".repeat(43));
    await client.setPassword("a private long passphrase");
    expect(await client.activate("123456")).toEqual(CODES);
    expect(client.phase).toBe("complete");
    await expect(client.activate("123456")).rejects.toMatchObject({
      code: "CHALLENGE_INVALID",
    });
    for (const [url, init] of transport.mock.calls as unknown as [
      string,
      RequestInit,
    ][]) {
      if (url.endsWith("csrf/")) continue;
      expect(url).toMatch(/^\/api\/v1\/auth\/web\/invitations\//);
      expect(init).toMatchObject({
        credentials: "same-origin",
        cache: "no-store",
        redirect: "error",
        referrerPolicy: "no-referrer",
      });
      expect(init.headers).toHaveProperty("X-CSRFToken");
      expect(init.headers).not.toHaveProperty("Authorization");
    }
  });
  it("rejects malformed setup and duplicate recovery codes without claiming completion", async () => {
    const { client } = fixture([
      json({ status: "accepted" }, 202),
      verified(),
      setup(),
      json({ status: "complete", recovery_codes: Array(10).fill(TOKEN) }, 201),
    ]);
    await client.requestProof("person@example.invalid");
    await client.confirmEmail("proof");
    await client.setPassword("long private passphrase");
    await expect(client.activate("123456")).rejects.toMatchObject({
      kind: "contract",
    });
    expect(client.phase).toBe("link");
  });
  it("drops late confirmation results after invalidation", async () => {
    let release!: (response: Response) => void;
    const state = new ScopeState("ngo");
    const transport = vi.fn(async (url: string) =>
      url.endsWith("csrf/")
        ? json({ csrf_token: "a".repeat(64) })
        : new Promise<Response>((resolve) => {
            release = resolve;
          }),
    );
    const client = new InvitationEnrollmentClient(state, transport);
    client.adopt({ id: ID, token: TOKEN });
    const request = client.requestProof("person@example.invalid");
    await waitFor(() => expect(release).toBeTypeOf("function"));
    client.cancel();
    release(json({ status: "accepted" }, 202));
    await expect(request).rejects.toHaveProperty("name", "StaleResponseError");
    expect(client.phase).toBe("link");
  });
});

it("renders a complete keyboard-usable ceremony in StrictMode, clears setup, displays recovery codes once", async () => {
  link();
  const user = userEvent.setup();
  const { client } = fixture([
    json({ status: "accepted" }, 202),
    verified(),
    setup(),
    json({ status: "complete", recovery_codes: CODES }, 201),
  ]);
  render(
    <StrictMode>
      <LocaleProvider>
        <main>
          <InvitationEnrollment client={client} />
        </main>
      </LocaleProvider>
    </StrictMode>,
  );
  expect(window.location.hash).toBe("");
  await user.type(
    screen.getByLabelText(/Your invitation email/),
    "person@example.invalid",
  );
  await user.click(screen.getByRole("button", { name: "Request email proof" }));
  await user.type(
    await screen.findByLabelText(/Email confirmation proof/),
    "proof",
  );
  await user.click(screen.getByRole("button", { name: "Confirm email" }));
  await user.type(
    await screen.findByLabelText(/Choose your password/),
    "a private long passphrase",
  );
  await user.type(
    screen.getByLabelText(/Repeat your password/),
    "a private long passphrase",
  );
  await user.click(
    screen.getByRole("button", { name: "Set up authenticator" }),
  );
  expect(await screen.findByLabelText("Authenticator setup key")).toHaveValue(
    SECRET,
  );
  expect((await axe.run(document.body)).violations).toEqual([]);
  await user.type(screen.getByLabelText(/Authenticator code/), "123456");
  await user.click(
    screen.getByRole("button", { name: "Activate and complete enrollment" }),
  );
  expect(
    await screen.findByText("Personal account and MFA are ready"),
  ).toBeVisible();
  expect(screen.queryByDisplayValue(SECRET)).not.toBeInTheDocument();
  expect(screen.getByText(CODES[0]!)).toBeVisible();
  await user.click(
    screen.getByRole("button", { name: "Clear recovery codes" }),
  );
  expect(screen.queryByText(CODES[0]!)).not.toBeInTheDocument();
});

it("clears secrets on locale switch and keeps default EN/UR route inert and accessible", async () => {
  link();
  const user = userEvent.setup();
  render(
    <LocaleProvider>
      <main>
        <Language />
        <InvitationEnrollment />
      </main>
    </LocaleProvider>,
  );
  expect(window.location.hash).toBe("");
  expect(
    screen.getByRole("button", { name: "Request email proof" }),
  ).toBeDisabled();
  await user.click(screen.getByRole("button", { name: "Urdu" }));
  expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
    "اپنی ذاتی دعوت قبول کریں",
  );
  expect((await axe.run(document.body)).violations).toEqual([]);
});
