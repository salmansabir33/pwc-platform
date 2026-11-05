import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Banner, Button, Card, TextField } from "@pwc/web-ui";
import { useLocale } from "@pwc/web-i18n";
import { consumeEnrollmentLink } from "@pwc/web-api";
import type { PersonalEnrollmentClient, EnrollmentSecret } from "@pwc/web-api";

/** Existing proof/first-factor journey, not nomination, invitations or authority.
 * Only the existing injected composition can issue requests; default stays inert. */
export function PersonalEnrollment({
  client,
}: {
  client?: PersonalEnrollmentClient;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [purpose, setPurpose] = useState<"registration" | "password-reset">(
    "registration",
  );
  const [phase, setPhase] = useState<"request" | "confirm">("request");
  const [factor, setFactor] = useState<EnrollmentSecret | null>(null);
  const [codes, setCodes] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [, render] = useState(0);
  const generation = useRef(0);
  const pending = useRef(false);
  const root = useRef<HTMLDivElement>(null);
  const linkProof = useRef("");
  const linkConsumed = useRef(false);
  const lifecycle = useRef(0);
  const priorLocale = useRef(locale);
  const currentClient = useRef(client);
  const priorClient = useRef(client);
  currentClient.current = client;
  function erase() {
    root.current?.querySelectorAll("form").forEach((form) => form.reset());
    linkProof.current = "";
    setFactor(null);
    setCodes([]);
  }
  useLayoutEffect(() => {
    if (linkConsumed.current) return;
    linkConsumed.current = true;
    const link = consumeEnrollmentLink(window.location, window.history);
    if (link && client) {
      client.resume(link.id, link.purpose);
      linkProof.current = link.proof;
      setPurpose(link.purpose);
      setPhase("confirm");
    }
    // The client does not survive a route remount in the shipped, disabled app.
  }, [client]);
  useEffect(() => {
    const lease = ++lifecycle.current;
    if (priorClient.current !== client) {
      erase();
      setPhase("request");
      setMessage("");
      priorClient.current = client;
    }
    const clear = (reason: string) => {
      erase();
      render((n) => n + 1);
      if (reason !== "security-rotation") {
        generation.current++;
        pending.current = false;
        setBusy(false);
        setPhase("request");
        setMessage("");
      }
    };
    const unsubscribe = client?.subscribe(clear);
    const hide = () => {
      if (document.hidden) client?.cancel();
    };
    const pagehide = () => client?.cancel();
    document.addEventListener("visibilitychange", hide);
    window.addEventListener("pagehide", pagehide);
    return () => {
      generation.current++;
      unsubscribe?.();
      queueMicrotask(() => {
        if (lifecycle.current === lease || currentClient.current !== client) {
          client?.cancel();
          linkProof.current = "";
        }
      });
      document.removeEventListener("visibilitychange", hide);
      window.removeEventListener("pagehide", pagehide);
    };
  }, [client]);
  useEffect(() => {
    if (priorLocale.current !== locale) {
      erase();
      client?.cancel();
      priorLocale.current = locale;
    }
  }, [client, locale]);
  useEffect(() => {
    if (!factor) return;
    const timer = setTimeout(
      () => {
        erase();
        client?.cancel();
      },
      Math.min(
        300_000,
        Math.max(0, Date.parse(factor.expires_at) - Date.now()),
      ),
    );
    return () => clearTimeout(timer);
  }, [factor, client]);
  useEffect(() => {
    if (!codes.length) return;
    const timer = setTimeout(() => {
      erase();
      client?.cancel();
    }, 300_000);
    return () => clearTimeout(timer);
  }, [codes, client]);
  useEffect(() => {
    if (!cooldown) return;
    const timer = setTimeout(
      () => setCooldown(0),
      Math.max(0, cooldown - performance.now()),
    );
    return () => clearTimeout(timer);
  }, [cooldown]);
  async function run(
    kind: "request" | "confirm" | "resend" | "factor" | "activate",
    data: FormData,
  ) {
    if (!client || pending.current || cooldown) return;
    pending.current = true;
    setBusy(true);
    setMessage("");
    const ticket = generation.current;
    try {
      if (kind === "request") {
        await client.start(purpose, String(data.get("email") ?? ""));
        if (ticket === generation.current) {
          setPhase("confirm");
          setMessage(
            t(
              "Request accepted. This does not confirm an account exists or that email was delivered.",
              "درخواست موصول ہوئی۔ اس سے اکاؤنٹ یا ای میل کی ترسیل کی تصدیق نہیں ہوتی۔",
            ),
          );
        }
      } else if (kind === "confirm") {
        const proof = String(data.get("proof") || linkProof.current);
        linkProof.current = "";
        await client.confirm(proof, String(data.get("password") ?? ""));
        if (ticket === generation.current) {
          setPhase("request");
          setMessage(
            t(
              "Confirmation succeeded. Sign in explicitly with your own credentials. No authority was granted.",
              "تصدیق مکمل ہوئی۔ اپنی معلومات سے شناخت کریں۔ کوئی انتظامی اختیار نہیں ملا۔",
            ),
          );
        }
      } else if (kind === "resend") {
        await client.resend();
        if (ticket === generation.current)
          setMessage(
            t(
              "Resend accepted; delivery is not guaranteed and expiry is unchanged.",
              "دوبارہ ارسال کی درخواست موصول ہوئی؛ ترسیل یقینی نہیں اور مدت تبدیل نہیں ہوئی۔",
            ),
          );
      } else if (kind === "factor") {
        const value = await client.requestMfa(
          String(data.get("password") ?? ""),
        );
        if (ticket === generation.current) setFactor(value);
      } else {
        const value = await client.confirmMfa(String(data.get("code") ?? ""));
        if (ticket === generation.current) {
          setFactor(null);
          setCodes(value);
          setMessage(
            t(
              "MFA is active. Save your own recovery codes once, offline. They confer no administrative authority.",
              "اضافی تصدیق فعال ہے۔ اپنے بازیابی کوڈ صرف ایک بار آف لائن محفوظ کریں۔ ان سے انتظامی اختیار نہیں ملتا۔",
            ),
          );
        }
      }
    } catch (e) {
      if (ticket === generation.current) {
        erase();
        setPhase("request");
        const retry = (e as { retryAfterSeconds?: number }).retryAfterSeconds;
        if (typeof retry === "number" && retry > 0)
          setCooldown(performance.now() + Math.min(retry, 3600) * 1000);
        setMessage(
          t(
            "Request unavailable, expired, rejected or uncertain. No automatic retry. Check your session or start a fresh request; never share proofs or codes.",
            "درخواست دستیاب نہیں، ختم، مسترد یا غیر مصدقہ ہے۔ خودکار کوشش نہیں ہوگی۔ نشست چیک کریں یا نئی درخواست دیں؛ کوڈ کسی کو نہ دیں۔",
          ),
        );
      }
    } finally {
      if (ticket === generation.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }
  const disabled = !client || busy || !!cooldown;
  const submit =
    (kind: Parameters<typeof run>[0]) =>
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const form = event.currentTarget;
      const data = new FormData(form);
      form.reset();
      void run(kind, data);
    };
  return (
    <div className="stack" ref={root}>
      <Banner
        tone="restricted"
        title={t("Personal enrollment only", "صرف ذاتی اندراج")}
      >
        {t(
          "Use separate accounts, passwords and authenticators. Founder and verifier nominations never grant access. Real mail delivery and credentialed web activation remain gated.",
          "الگ اکاؤنٹ، پاس ورڈ اور تصدیقی ایپ استعمال کریں۔ بانی یا تصدیق کنندہ کی نامزدگی سے اختیار نہیں ملتا۔ حقیقی ای میل اور ویب رابطہ منظوری تک بند ہیں۔",
        )}
      </Banner>
      <Card
        title={t(
          "Invitation-only enrollment or account recovery",
          "دعوت کے ذریعے اندراج یا اکاؤنٹ کی بازیابی",
        )}
      >
        <p>
          {t(
            "Initial enrollment is invitation-only. Issuing and accepting invitations is unavailable until the issuer and privacy contracts are accepted. Public registration is test-only.",
            "ابتدائی اندراج صرف دعوت سے ہے۔ دعوت دینے والے اور رازداری کے معاہدوں کی منظوری تک دعوت دینا اور قبول کرنا دستیاب نہیں۔ عام اندراج صرف آزمائش کے لیے ہے۔",
          )}
        </p>
        {!client && (
          <p>
            {t(
              "Enrollment unavailable: no approved transport is connected.",
              "اندراج دستیاب نہیں: منظور شدہ رابطہ موجود نہیں۔",
            )}
          </p>
        )}
        {message && <p role="status">{message}</p>}
        {cooldown > 0 && (
          <p role="alert">
            {t(
              "Rate limited. Wait before another request.",
              "درخواستوں کی حد مکمل ہے۔ اگلی کوشش سے پہلے انتظار کریں۔",
            )}
          </p>
        )}
        <form
          className="stack"
          onSubmit={submit(phase === "request" ? "request" : "confirm")}
        >
          {phase === "request" ? (
            <>
              <label>
                {t("Account action", "اکاؤنٹ کا عمل")}
                <select
                  disabled={disabled}
                  value={purpose}
                  onChange={(e) => {
                    erase();
                    setPurpose(e.target.value as typeof purpose);
                  }}
                >
                  <option value="registration">
                    {t("Create personal account", "ذاتی اکاؤنٹ بنائیں")}
                  </option>
                  <option value="password-reset">
                    {t("Reset password", "پاس ورڈ بحال کریں")}
                  </option>
                </select>
              </label>
              <TextField
                label={t("Enrollment email", "اندراج کا ای میل")}
                hint={t(
                  "Your own address; no account eligibility is disclosed",
                  "آپ کا اپنا پتہ؛ اکاؤنٹ کی اہلیت ظاہر نہیں ہوتی",
                )}
                name="email"
                autoComplete="email"
                required
                disabled={disabled}
              />
            </>
          ) : (
            <>
              <TextField
                label={t("Email verification proof", "ای میل تصدیق کا ثبوت")}
                hint={t(
                  "From your own verification message; never a staff-supplied bypass",
                  "اپنے تصدیقی پیغام سے؛ انتظامی بائی پاس نہیں",
                )}
                name="proof"
                type="password"
                autoComplete="off"
                required={!linkProof.current}
                disabled={disabled}
              />
              <TextField
                label={t("Choose your password", "اپنا پاس ورڈ منتخب کریں")}
                hint={t(
                  "Use your own password manager; never share this password",
                  "اپنا پاس ورڈ مینیجر استعمال کریں؛ پاس ورڈ کسی کو نہ دیں",
                )}
                name="password"
                type="password"
                autoComplete="new-password"
                required
                disabled={disabled}
              />
            </>
          )}
          <Button type="submit" disabled={disabled} busy={busy}>
            {phase === "request"
              ? t("Request email verification", "ای میل تصدیق کی درخواست")
              : t("Confirm personal account", "ذاتی اکاؤنٹ کی تصدیق")}
          </Button>
        </form>
        {phase === "confirm" && (
          <Button
            variant="secondary"
            disabled={disabled || !client?.canResend}
            onClick={() => void run("resend", new FormData())}
          >
            {t("Resend verification", "تصدیق دوبارہ بھیجیں")}
          </Button>
        )}
        <Button
          variant="tertiary"
          disabled={busy}
          onClick={() => {
            erase();
            client?.cancel();
            setPhase("request");
          }}
        >
          {t("Clear enrollment secrets", "اندراج کے راز ہٹائیں")}
        </Button>
      </Card>
      <Card
        title={t("Enroll your own authenticator", "اپنی تصدیقی ایپ شامل کریں")}
      >
        <p>
          {t(
            "First sign in and check your personal session below. This enrolls a first factor only, not privileged command assurance.",
            "پہلے شناخت کریں اور نیچے ذاتی نشست چیک کریں۔ یہ پہلی تصدیقی ایپ ہے، انتظامی حکم کی اجازت نہیں۔",
          )}
        </p>
        {!factor && codes.length === 0 && (
          <form className="stack" onSubmit={submit("factor")}>
            <TextField
              label={t(
                "Current password for MFA",
                "اضافی تصدیق کے لیے موجودہ پاس ورڈ",
              )}
              hint={t(
                "Required again for the exact personal enrollment intent",
                "اسی ذاتی اندراج کے لیے دوبارہ درکار ہے",
              )}
              name="password"
              type="password"
              autoComplete="current-password"
              required
              disabled={disabled || !client?.signedIn}
            />
            <Button
              type="submit"
              disabled={disabled || !client?.signedIn}
              busy={busy}
            >
              {t("Set up authenticator", "تصدیقی ایپ ترتیب دیں")}
            </Button>
          </form>
        )}
        {factor && (
          <div className="stack">
            <p>
              {t(
                "Enter this secret into your own authenticator: time-based TOTP, six digits, 30 seconds. No third-party QR service is used.",
                "یہ راز اپنی تصدیقی ایپ میں درج کریں: وقت پر مبنی چھ ہندسوں کا کوڈ، ۳۰ سیکنڈ۔ بیرونی کیو آر خدمت استعمال نہیں ہوتی۔",
              )}
            </p>
            <code className="personal-secret">{factor.secret}</code>
            <form className="stack" onSubmit={submit("activate")}>
              <TextField
                label={t("New authenticator code", "نئی تصدیقی ایپ کا کوڈ")}
                hint={t(
                  "Six digits from your own authenticator",
                  "اپنی تصدیقی ایپ کے چھ ہندسے",
                )}
                name="code"
                type="password"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                pattern="[0-9]{6}"
                disabled={disabled}
              />
              <Button type="submit" disabled={disabled} busy={busy}>
                {t("Activate personal MFA", "ذاتی اضافی تصدیق فعال کریں")}
              </Button>
            </form>
          </div>
        )}
        {codes.length > 0 && (
          <div>
            <p>
              {t("Recovery codes — shown once", "بازیابی کوڈ — صرف ایک بار")}
            </p>
            <ul>
              {codes.map((code) => (
                <li key={code}>
                  <code className="personal-secret">{code}</code>
                </li>
              ))}
            </ul>
            <Button onClick={erase}>
              {t(
                "I saved my recovery codes; hide them",
                "کوڈ محفوظ کر لیے ہیں؛ اب چھپائیں",
              )}
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
