import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import axe from "axe-core";
import { LocaleProvider, useLocale } from "@pwc/web-i18n";
import {
  ApiError,
  PersonalEnrollmentClient,
  ScopeState,
  consumeEnrollmentLink,
} from "@pwc/web-api";
import { PersonalEnrollment } from "../../apps/ngo-web/src/PersonalEnrollment";
const ID = "00000000-0000-4000-8000-000000000001";
const PROOF = "x".repeat(43),
  PASSWORD = "synthetic password fixture";
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status });
const accepted = {
  status: "accepted",
  flow_id: ID,
  flow_control: "control",
  expires_in: 1800,
};
const csrf = () => json({ csrf_token: "a".repeat(64) });
function setup(responses: Response[] = []) {
  const state = new ScopeState("ngo");
  const transport = vi.fn().mockImplementation(async (url: string) => {
    if (url.endsWith("csrf/")) return csrf();
    const next = responses.shift();
    if (!next) throw new Error("Unexpected request");
    return next;
  });
  return {
    state,
    transport,
    client: new PersonalEnrollmentClient(state, transport),
  };
}
function actor(state: ScopeState) {
  state.switchScope({
    principalId: ID,
    sessionId: ID,
    organizationId: null,
    registryVersion: "personal-history-v1",
    revision: "session",
  });
}
function Language() {
  const { setLocale } = useLocale();
  return <button onClick={() => setLocale("ur")}>Urdu</button>;
}
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});
describe("personal enrollment client", () => {
  it("does not use ambient fetch or expose secrets through serialization", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    const client = new PersonalEnrollmentClient(new ScopeState("ngo"));
    await expect(
      client.start("registration", "person@example.invalid"),
    ).rejects.toMatchObject({ kind: "disabled" });
    expect(fetch).not.toHaveBeenCalled();
    expect(JSON.stringify(client)).not.toContain("person@example.invalid");
  });
  it("registers without login, uses fixed CSRF-protected routes, resends, confirms explicitly and erases flow", async () => {
    const { client, state, transport } = setup([
      json(accepted, 202),
      json({ status: "accepted" }, 202),
      json({ status: "verified" }, 201),
    ]);
    await client.start("registration", "Person@bücher.invalid");
    await client.resend();
    await client.confirm(PROOF, PASSWORD);
    expect(state.currentScope).toBeNull();
    expect(
      transport.mock.calls
        .filter((c) => !c[0].endsWith("csrf/"))
        .map((c) => c[0]),
    ).toEqual([
      "/api/v1/auth/registration/request/",
      "/api/v1/auth/registration/resend/",
      "/api/v1/auth/registration/confirm/",
    ]);
    for (const [, init] of transport.mock.calls)
      expect(init).toMatchObject({
        credentials: "same-origin",
        cache: "no-store",
        referrerPolicy: "no-referrer",
        redirect: "error",
      });
    expect(transport.mock.calls.at(-1)?.[1]).toMatchObject({
      headers: { "X-CSRFToken": "a".repeat(64) },
      body: JSON.stringify({ flow_id: ID, proof: PROOF, password: PASSWORD }),
    });
    expect(JSON.stringify(client)).not.toContain(PROOF);
    await expect(client.confirm(PROOF, PASSWORD)).rejects.toMatchObject({
      code: "CHALLENGE_INVALID",
    });
  });
  it("keeps reset distinct, does not establish a session or weaken recovery hold", async () => {
    const { client, state, transport } = setup([
      json({ ...accepted, expires_in: 900 }, 202),
      new Response(null, { status: 204 }),
    ]);
    await client.start("password-reset", "person@example.invalid");
    await client.confirm(PROOF, PASSWORD);
    expect(state.currentScope).toBeNull();
    expect(transport.mock.calls.at(-1)?.[1].body).toBe(
      JSON.stringify({ flow_id: ID, proof: PROOF, new_password: PASSWORD }),
    );
  });
  it("bounds flow expiry, extra response fields and signed-out MFA; never auto retries", async () => {
    for (const value of [
      { ...accepted, expires_in: 1801 },
      { ...accepted, role: "Founder" },
    ]) {
      const { client, transport } = setup([json(value, 202)]);
      await expect(
        client.start("registration", "p@example.invalid"),
      ).rejects.toMatchObject({ kind: "contract" });
      await expect(client.resend()).rejects.toMatchObject({
        code: "CHALLENGE_INVALID",
      });
      expect(transport).toHaveBeenCalledTimes(2);
    }
    await expect(setup().client.requestMfa(PASSWORD)).rejects.toMatchObject({
      code: "SESSION_REQUIRED",
    });
  });
  it("expires resend without extending the original flow or disclosing duplicate eligibility", async () => {
    vi.useFakeTimers();
    const { client } = setup([json({ ...accepted, expires_in: 1 }, 202)]);
    await client.start("registration", "p@example.invalid");
    vi.advanceTimersByTime(1001);
    await expect(client.resend()).rejects.toMatchObject({
      code: "CHALLENGE_INVALID",
    });
  });
  it("rejects concurrent attempts and late registration responses after cancellation", async () => {
    let release!: (r: Response) => void;
    const state = new ScopeState("ngo");
    const transport = vi.fn(async (url: string) =>
      url.endsWith("csrf/")
        ? csrf()
        : await new Promise<Response>((resolve) => {
            release = resolve;
          }),
    );
    const client = new PersonalEnrollmentClient(state, transport);
    const first = client.start("registration", "p@example.invalid");
    await waitFor(() => expect(release).toBeDefined());
    await expect(
      client.start("registration", "other@example.invalid"),
    ).rejects.toMatchObject({ code: "ENROLLMENT_PENDING" });
    client.cancel();
    release(json(accepted, 202));
    await expect(first).rejects.toMatchObject({ name: "StaleResponseError" });
    expect(client.canResend).toBe(false);
  });
  it("enrolls an own first factor with exact intent, rotated CSRF and one-time recovery codes", async () => {
    const expires = new Date(Date.now() + 240000).toISOString();
    const codes = Array.from({ length: 10 }, (_, i) => `recovery-fixture-${i}`);
    const { state, client, transport } = setup([
      json(
        { intent_id: ID, expires_at: expires, required_methods: ["password"] },
        201,
      ),
      json({ assurance_proof: "one-use-proof", expires_at: expires }),
      json(
        {
          enrollment_id: ID,
          secret: "ABCDEFGHIJKLMNOP",
          otpauth_uri: "otpauth://totp/PWC:test",
          expires_at: expires,
        },
        201,
      ),
      json({ status: "active", recovery_codes: codes }),
    ]);
    actor(state);
    const value = await client.requestMfa(PASSWORD);
    expect(value.secret).toBe("ABCDEFGHIJKLMNOP");
    expect(await client.confirmMfa("123456")).toEqual(codes);
    expect(state.currentScope?.organizationId).toBeNull();
    const writes = transport.mock.calls.filter((c) => !c[0].endsWith("csrf/"));
    expect(writes.map((c) => c[0])).toEqual([
      "/api/v1/auth/assurance/intents/",
      "/api/v1/auth/step-up/",
      "/api/v1/auth/mfa/enrollment/request/",
      "/api/v1/auth/mfa/enrollment/confirm/",
    ]);
    expect(JSON.parse(writes[0]?.[1].body)).toEqual({
      operation: "mfa.enroll",
      context: { kind: "personal", id: ID },
      command: {},
    });
    expect(JSON.stringify(client)).not.toContain("ABCDEFGHIJKLMNOP");
    expect(JSON.stringify(client)).not.toContain("recovery-fixture");
    await expect(client.confirmMfa("123456")).rejects.toMatchObject({
      code: "CHALLENGE_INVALID",
    });
  });
  it("fails on network uncertainty, errors and malformed step-up without caching credentials", async () => {
    const { client, transport } = setup();
    await expect(
      client.start("registration", "p@example.invalid"),
    ).rejects.toMatchObject({ code: "ENROLLMENT_RESULT_UNCERTAIN" });
    expect(transport).toHaveBeenCalledTimes(2);
    const x = setup([
      json(
        {
          error: {
            code: "RATE_LIMITED",
            message: "private",
            field_errors: {},
            request_id: ID,
          },
        },
        429,
      ),
    ]);
    await expect(
      x.client.start("registration", "p@example.invalid"),
    ).rejects.toMatchObject({ kind: "rate-limit" });
    const expires = new Date(Date.now() + 240000).toISOString();
    const malformed = setup([
      json(
        { intent_id: ID, expires_at: expires, required_methods: ["password"] },
        201,
      ),
      json({ bad: "private" }),
    ]);
    actor(malformed.state);
    const before = malformed.state.generation;
    await expect(malformed.client.requestMfa(PASSWORD)).rejects.toBeInstanceOf(
      ApiError,
    );
    expect(malformed.state.generation).toBeGreaterThan(before);
  });
});
describe("email confirmation link handling", () => {
  it("scrubs fragment before returning proof, rejects duplicates, query credentials and unknown fields", () => {
    const replaceState = vi.fn();
    const hash = `#flow_id=${ID}&proof=${PROOF}&purpose=registration`;
    expect(
      consumeEnrollmentLink(
        { hash, pathname: "/account/confirm", search: "" },
        { replaceState },
      ),
    ).toEqual({ id: ID, proof: PROOF, purpose: "registration" });
    expect(replaceState).toHaveBeenCalledWith(null, "", "/account/confirm");
    for (const value of [
      hash + "&proof=x",
      hash + "&role=Founder",
      "#purpose=unknown",
    ])
      expect(
        consumeEnrollmentLink(
          { hash: value, pathname: "/account/confirm", search: "" },
          { replaceState },
        ),
      ).toBeNull();
    expect(
      consumeEnrollmentLink(
        { hash, pathname: "/account/confirm", search: "?proof=x" },
        { replaceState },
      ),
    ).toBeNull();
  });
});
describe("personal enrollment UI", () => {
  it("ships disabled without transport, remains accessible in EN/UR and cannot create privileged users", async () => {
    const fetch = vi.spyOn(globalThis, "fetch");
    for (const locale of ["en", "ur"] as const) {
      const view = render(
        <LocaleProvider>
          <Language />
          <PersonalEnrollment />
        </LocaleProvider>,
      );
      if (locale === "ur") {
        await userEvent
          .setup()
          .click(screen.getByRole("button", { name: "Urdu" }));
        expect(document.documentElement.dir).toBe("rtl");
        expect(
          screen.getByRole("button", { name: "ای میل تصدیق کی درخواست" }),
        ).toBeDisabled();
      }
      if (locale === "en") {
        expect(
          screen.getByRole("button", { name: "Request email verification" }),
        ).toBeDisabled();
        expect(
          screen.getByRole("button", { name: "Set up authenticator" }),
        ).toBeDisabled();
      }
      expect((await axe.run(view.container)).violations).toEqual([]);
      view.unmount();
    }
    expect(fetch).not.toHaveBeenCalled();
  });
  it("completes request/proof/password without automatic login or privileges and clears form secrets", async () => {
    const { client } = setup([
      json(accepted, 202),
      json({ status: "verified" }, 201),
    ]);
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <PersonalEnrollment client={client} />
      </LocaleProvider>,
    );
    await user.type(
      screen.getByLabelText("Enrollment email"),
      "p@example.invalid",
    );
    await user.click(
      screen.getByRole("button", { name: "Request email verification" }),
    );
    await user.type(
      await screen.findByLabelText("Email verification proof"),
      PROOF,
    );
    await user.type(screen.getByLabelText("Choose your password"), PASSWORD);
    await user.click(
      screen.getByRole("button", { name: "Confirm personal account" }),
    );
    expect(await screen.findByText(/Confirmation succeeded/)).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Set up authenticator" }),
    ).toBeDisabled();
    expect(document.body.innerHTML).not.toContain(PASSWORD);
  });
  it("consumes an emailed fragment in StrictMode but never confirms on link opening", async () => {
    window.history.replaceState(
      null,
      "",
      `/account/confirm#flow_id=${ID}&proof=${PROOF}&purpose=registration`,
    );
    const { client, transport } = setup([json({ status: "verified" }, 201)]);
    const user = userEvent.setup();
    render(
      <StrictMode>
        <LocaleProvider>
          <PersonalEnrollment client={client} />
        </LocaleProvider>
      </StrictMode>,
    );
    expect(window.location.hash).toBe("");
    expect(transport).not.toHaveBeenCalled();
    await user.type(screen.getByLabelText("Choose your password"), PASSWORD);
    await user.click(
      screen.getByRole("button", { name: "Confirm personal account" }),
    );
    expect(await screen.findByText(/Confirmation succeeded/)).toBeVisible();
  });
  it("renders first-factor setup, removes its secret after activation and hides one-time codes", async () => {
    const expires = new Date(Date.now() + 240000).toISOString();
    const codes = Array.from({ length: 10 }, (_, i) => `offline-code-${i}`);
    const { state, client } = setup([
      json(
        { intent_id: ID, expires_at: expires, required_methods: ["password"] },
        201,
      ),
      json({ assurance_proof: "only-proof", expires_at: expires }),
      json(
        {
          enrollment_id: ID,
          secret: "ABCDEFGHIJKLMNOP",
          otpauth_uri: "otpauth://totp/PWC:test",
          expires_at: expires,
        },
        201,
      ),
      json({ status: "active", recovery_codes: codes }),
    ]);
    actor(state);
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <PersonalEnrollment client={client} />
      </LocaleProvider>,
    );
    await user.type(
      screen.getByLabelText("Current password for MFA"),
      PASSWORD,
    );
    await user.click(
      screen.getByRole("button", { name: "Set up authenticator" }),
    );
    expect(await screen.findByText("ABCDEFGHIJKLMNOP")).toBeVisible();
    expect(
      (await axe.run(document.body, { rules: { region: { enabled: false } } }))
        .violations,
    ).toEqual([]);
    await user.type(screen.getByLabelText("New authenticator code"), "123456");
    await user.click(
      screen.getByRole("button", { name: "Activate personal MFA" }),
    );
    expect(await screen.findByText("offline-code-0")).toBeVisible();
    expect(screen.queryByText("ABCDEFGHIJKLMNOP")).toBeNull();
    await user.click(
      screen.getByRole("button", {
        name: "I saved my recovery codes; hide them",
      }),
    );
    expect(screen.queryByText("offline-code-0")).toBeNull();
  });
  it("removes an enrollment secret and credentials on visibility invalidation", async () => {
    const expires = new Date(Date.now() + 240000).toISOString();
    const { state, client } = setup([
      json(
        { intent_id: ID, expires_at: expires, required_methods: ["password"] },
        201,
      ),
      json({ assurance_proof: "proof", expires_at: expires }),
      json(
        {
          enrollment_id: ID,
          secret: "ABCDEFGHIJKLMNOP",
          otpauth_uri: "otpauth://totp/PWC:test",
          expires_at: expires,
        },
        201,
      ),
    ]);
    actor(state);
    const user = userEvent.setup();
    render(
      <LocaleProvider>
        <PersonalEnrollment client={client} />
      </LocaleProvider>,
    );
    await user.type(
      screen.getByLabelText("Current password for MFA"),
      PASSWORD,
    );
    await user.click(
      screen.getByRole("button", { name: "Set up authenticator" }),
    );
    await screen.findByText("ABCDEFGHIJKLMNOP");
    state.invalidate("visibility");
    await waitFor(() =>
      expect(screen.queryByText("ABCDEFGHIJKLMNOP")).toBeNull(),
    );
    await expect(client.confirmMfa("123456")).rejects.toMatchObject({
      code: "CHALLENGE_INVALID",
    });
  });
});
