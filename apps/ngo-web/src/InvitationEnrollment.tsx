import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Banner, Button, Card, TextField } from "@pwc/web-ui";
import { useLocale } from "@pwc/web-i18n";
import {
  ApiError,
  consumeInvitationLink,
  connectInvalidationChannel,
} from "@pwc/web-api";
import type { InvitationEnrollmentClient, InvitationSetup } from "@pwc/web-api";

/** No ambient transport. Shipped route stays inert pending actual live contracts. */
export function InvitationEnrollment({
  client,
}: {
  client?: InvitationEnrollmentClient;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [, render] = useState(0);
  const [setup, setSetup] = useState<InvitationSetup | null>(null);
  const [codes, setCodes] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [cooldown, setCooldown] = useState(0);
  const form = useRef<HTMLFormElement>(null);
  const pending = useRef(false);
  const generation = useRef(0);
  const consumed = useRef(false);
  const lifecycle = useRef(0);
  const currentClient = useRef(client);
  currentClient.current = client;
  const priorLocale = useRef(locale);
  const heading = useRef<HTMLHeadingElement>(null);
  const enabled = !!client?.connected;
  const phase = client?.phase ?? "link";
  function erase() {
    form.current?.reset();
    setSetup(null);
    setCodes([]);
  }
  useLayoutEffect(() => {
    if (consumed.current) return;
    consumed.current = true;
    const link = consumeInvitationLink(window.location, window.history);
    if (enabled && link) client?.adopt(link);
    if (!link)
      setMessage(
        t(
          "Open your own invitation email link. Invalid link material has been removed.",
          "اپنی دعوتی ای میل کا لنک کھولیں۔ غلط لنک کی معلومات ہٹا دی گئی ہیں۔",
        ),
      );
  }, [client, enabled]);
  useEffect(() => {
    const lease = ++lifecycle.current;
    const clear = () => {
      generation.current++;
      pending.current = false;
      erase();
      setBusy(false);
      setCooldown(0);
      setMessage(
        t(
          "Enrollment data cleared. Reopen your invitation if unfinished; sign in explicitly if completion may have succeeded.",
          "اندراج کی معلومات ہٹا دی گئیں۔ نامکمل ہو تو دعوت دوبارہ کھولیں؛ ممکنہ تکمیل پر خود سائن ان کریں۔",
        ),
      );
      render((n) => n + 1);
    };
    const unsubscribe = client?.subscribe(clear);
    const disconnect = client
      ? connectInvalidationChannel(client.state)
      : undefined;
    const hide = () => {
      if (document.hidden) {
        client?.cancel();
        clear();
      }
    };
    const leave = () => {
      client?.cancel();
      clear();
    };
    document.addEventListener("visibilitychange", hide);
    window.addEventListener("pagehide", leave);
    return () => {
      generation.current++;
      unsubscribe?.();
      disconnect?.();
      queueMicrotask(() => {
        if (lifecycle.current === lease || currentClient.current !== client)
          client?.cancel();
      });
      form.current?.reset();
      document.removeEventListener("visibilitychange", hide);
      window.removeEventListener("pagehide", leave);
    };
  }, [client]);
  useEffect(() => {
    if (priorLocale.current !== locale) {
      generation.current++;
      client?.cancel();
      erase();
      setMessage("");
      priorLocale.current = locale;
    }
  }, [client, locale]);
  useEffect(() => {
    if (!setup && !codes.length) return;
    const timer = setTimeout(
      () => {
        client?.cancel();
        erase();
        setMessage(
          t(
            "Setup expired or recovery codes were cleared. Reopen your own invitation if unfinished; sign in explicitly if completed.",
            "سیٹ اپ کی مدت ختم یا بحالی کوڈ ہٹا دیے گئے۔ اگر نامکمل ہے تو اپنی دعوت دوبارہ کھولیں؛ مکمل ہو تو خود سائن ان کریں۔",
          ),
        );
      },
      setup
        ? Math.min(
            300_000,
            Math.max(0, Date.parse(setup.expires_at) - Date.now()),
          )
        : 300_000,
    );
    return () => clearTimeout(timer);
  }, [setup, codes, client, locale]);
  useEffect(() => {
    if (!cooldown) return;
    const timer = setTimeout(
      () => setCooldown(0),
      Math.max(0, cooldown - performance.now()),
    );
    return () => clearTimeout(timer);
  }, [cooldown]);
  async function submit(event: React.SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client || !enabled || pending.current || cooldown) return;
    const data = new FormData(event.currentTarget);
    const ticket = generation.current;
    pending.current = true;
    setBusy(true);
    setMessage("");
    event.currentTarget.reset();
    try {
      if (phase === "link")
        await client.requestProof(String(data.get("recipient") ?? ""));
      else if (phase === "proof")
        await client.confirmEmail(String(data.get("proof") ?? ""));
      else if (phase === "password") {
        const password = String(data.get("password") ?? "");
        if (password !== data.get("repeat_password"))
          throw new ApiError("validation", 400, "VALIDATION_ERROR");
        const next = await client.setPassword(password);
        if (ticket === generation.current) setSetup(next);
      } else if (phase === "mfa") {
        const next = await client.activate(String(data.get("code") ?? ""));
        if (ticket === generation.current) {
          setSetup(null);
          setCodes(next);
        }
      }
      if (ticket === generation.current) {
        render((n) => n + 1);
        setMessage(
          phase === "link"
            ? t(
                "Request accepted, not a delivery guarantee. Check your own inbox; wait before resending.",
                "درخواست موصول ہوئی، ترسیل کی ضمانت نہیں۔ اپنا ان باکس دیکھیں؛ دوبارہ بھیجنے سے پہلے انتظار کریں۔",
              )
            : "",
        );
        heading.current?.focus();
      }
    } catch (error) {
      if (ticket !== generation.current) return;
      if (error instanceof ApiError && error.kind === "rate-limit")
        setCooldown(
          performance.now() + Math.max(1, error.retryAfterSeconds ?? 60) * 1000,
        );
      if (phase === "mfa" && client.phase !== "mfa") erase();
      setMessage(
        error instanceof ApiError && error.kind === "network"
          ? t(
              "Result uncertain. Do not retry automatically. If completion may have succeeded, sign in explicitly; otherwise reopen your invitation.",
              "نتیجہ غیر یقینی ہے۔ خودکار دوبارہ کوشش نہ کریں۔ ممکنہ تکمیل پر خود سائن ان کریں؛ ورنہ دعوت دوبارہ کھولیں۔",
            )
          : t(
              "Could not complete this step. Check your details, expiry and service availability. No authority was granted.",
              "یہ مرحلہ مکمل نہیں ہوا۔ معلومات، مدت اور سروس دیکھیں۔ کوئی اختیار نہیں دیا گیا۔",
            ),
      );
      render((n) => n + 1);
    } finally {
      if (ticket === generation.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }
  const disabled = !enabled || busy || !!cooldown;
  return (
    <section className="stack">
      <h1 ref={heading} tabIndex={-1}>
        {t("Accept your personal invitation", "اپنی ذاتی دعوت قبول کریں")}
      </h1>
      <Card title={t("Private personal enrollment", "نجی ذاتی اندراج")}>
        <p>
          {t(
            "Confirm your own email, choose your password and activate your authenticator within 24 hours. No account exists until every step succeeds. No Founder, verifier or NGO authority is granted.",
            "۲۴ گھنٹوں میں اپنی ای میل کی تصدیق، پاس ورڈ اور آتھنٹیکیٹر فعال کریں۔ تمام مراحل کی کامیابی سے پہلے اکاؤنٹ نہیں بنتا۔ بانی، تصدیق کنندہ یا این جی او کا اختیار نہیں ملتا۔",
          )}
        </p>
        {!enabled && (
          <Banner tone="warning" title={t("Not connected", "رابطہ موجود نہیں")}>
            {t(
              "Live invitation enrollment is unavailable. Issuer, privacy, mail and transport acceptance remain required.",
              "حقیقی دعوتی اندراج دستیاب نہیں۔ مجاز جاری کنندہ، رازداری، ای میل اور رابطے کی منظوری درکار ہے۔",
            )}
          </Banner>
        )}
        {message && <p role="status">{message}</p>}
        {!!cooldown && (
          <p role="alert">
            {t(
              "Rate limited. Wait before trying again.",
              "درخواستوں کی حد مکمل ہے۔ دوبارہ کوشش سے پہلے انتظار کریں۔",
            )}
          </p>
        )}
        {phase !== "complete" && (
          <form ref={form} className="stack" onSubmit={submit}>
            {phase === "link" && (
              <TextField
                hint={t(
                  "Use only the address bound to your invitation.",
                  "صرف دعوت سے منسلک اپنا پتہ استعمال کریں۔",
                )}
                name="recipient"
                label={t("Your invitation email", "آپ کی دعوتی ای میل")}
                autoComplete="email"
                type="email"
                required
                disabled={disabled}
              />
            )}
            {phase === "proof" && (
              <TextField
                hint={t(
                  "Copy the separate proof from your own inbox.",
                  "الگ تصدیقی کوڈ اپنے ان باکس سے لیں۔",
                )}
                name="proof"
                label={t("Email confirmation proof", "ای میل تصدیقی کوڈ")}
                autoComplete="off"
                type="password"
                required
                disabled={disabled}
              />
            )}
            {phase === "password" && (
              <>
                <TextField
                  name="password"
                  label={t("Choose your password", "اپنا پاس ورڈ منتخب کریں")}
                  hint={t(
                    "At least 15 characters. Use your own password manager; never share it.",
                    "کم از کم ۱۵ حروف۔ اپنا پاس ورڈ مینیجر استعمال کریں؛ کسی کو نہ دیں۔",
                  )}
                  autoComplete="new-password"
                  type="password"
                  minLength={15}
                  maxLength={128}
                  required
                  disabled={disabled}
                />
                <TextField
                  hint={t(
                    "Enter the same private password again.",
                    "وہی نجی پاس ورڈ دوبارہ درج کریں۔",
                  )}
                  name="repeat_password"
                  label={t("Repeat your password", "پاس ورڈ دوبارہ درج کریں")}
                  autoComplete="new-password"
                  type="password"
                  minLength={15}
                  maxLength={128}
                  required
                  disabled={disabled}
                />
              </>
            )}
            {phase === "mfa" && (
              <>
                <p>
                  {t(
                    "Add this key to your own authenticator. It expires in five minutes or at the invitation deadline, whichever is earlier. Never share the key or codes.",
                    "یہ کلید اپنے آتھنٹیکیٹر میں شامل کریں۔ پانچ منٹ یا دعوت کی مدت، جو پہلے ہو، تک درست ہے۔ کلید یا کوڈ کسی کو نہ دیں۔",
                  )}
                </p>
                {setup && (
                  <>
                    <TextField
                      label={t("Authenticator setup key", "آتھنٹیکیٹر کی کلید")}
                      hint={t(
                        "Private setup key; do not share it.",
                        "نجی کلید؛ کسی کو نہ دیں۔",
                      )}
                      value={setup.secret}
                      readOnly
                      autoComplete="off"
                      dir="ltr"
                    />
                    <a href={setup.otpauth_uri}>
                      {t("Open authenticator app", "آتھنٹیکیٹر ایپ کھولیں")}
                    </a>
                  </>
                )}
                <TextField
                  hint={t(
                    "Enter six digits from your authenticator.",
                    "اپنے آتھنٹیکیٹر سے چھ ہندسے درج کریں۔",
                  )}
                  name="code"
                  label={t("Authenticator code", "آتھنٹیکیٹر کوڈ")}
                  autoComplete="one-time-code"
                  inputMode="numeric"
                  pattern="[0-9]{6}"
                  maxLength={6}
                  required
                  disabled={disabled}
                />
              </>
            )}
            <Button type="submit" disabled={disabled} busy={busy}>
              {phase === "link"
                ? t("Request email proof", "ای میل کوڈ کی درخواست")
                : phase === "proof"
                  ? t("Confirm email", "ای میل کی تصدیق")
                  : phase === "password"
                    ? t("Set up authenticator", "آتھنٹیکیٹر ترتیب دیں")
                    : t(
                        "Activate and complete enrollment",
                        "فعال کریں اور اندراج مکمل کریں",
                      )}
            </Button>
          </form>
        )}
        {phase === "proof" && (
          <Button
            variant="secondary"
            disabled={disabled}
            onClick={() => {
              client?.cancel();
              erase();
              setMessage(
                t(
                  "Reopen your invitation link to request a fresh proof after the delivery cooldown. No account has been created.",
                  "انتظار کے بعد نیا کوڈ لینے کے لیے دعوت کا لنک دوبارہ کھولیں۔ اکاؤنٹ نہیں بنایا گیا۔",
                ),
              );
            }}
          >
            {t(
              "Restart from invitation email",
              "دعوتی ای میل سے دوبارہ شروع کریں",
            )}
          </Button>
        )}
        {phase === "complete" && (
          <section aria-label={t("Enrollment complete", "اندراج مکمل")}>
            <h2>
              {t(
                "Personal account and MFA are ready",
                "ذاتی اکاؤنٹ اور ایم ایف اے تیار ہیں",
              )}
            </h2>
            <p>
              {t(
                "Save these recovery codes privately now. They are shown once. Sign in explicitly with your own password and authenticator; no session or institutional authority was granted here.",
                "بحالی کوڈ ابھی نجی طور پر محفوظ کریں۔ یہ صرف ایک بار دکھائے جاتے ہیں۔ اپنے پاس ورڈ اور آتھنٹیکیٹر سے خود سائن ان کریں؛ یہاں کوئی سیشن یا انتظامی اختیار نہیں ملا۔",
              )}
            </p>
            <ul dir="ltr">
              {codes.map((code) => (
                <li key={code}>
                  <code>{code}</code>
                </li>
              ))}
            </ul>
            <Button
              onClick={() => {
                erase();
                client?.cancel();
              }}
            >
              {t("Clear recovery codes", "بحالی کوڈ ہٹا دیں")}
            </Button>
            <a href="/account">{t("Sign in explicitly", "خود سائن ان کریں")}</a>
          </section>
        )}
        {phase !== "complete" && (
          <Button
            variant="secondary"
            onClick={() => {
              generation.current++;
              client?.cancel();
              erase();
              setBusy(false);
              setMessage(
                t(
                  "Enrollment cleared on this device. Reopen your own invitation to restart before expiry.",
                  "اس آلے سے اندراج ہٹا دیا گیا۔ مدت ختم ہونے سے پہلے اپنی دعوت دوبارہ کھولیں۔",
                ),
              );
            }}
          >
            {t("Clear and leave enrollment", "اندراج ہٹائیں اور چھوڑیں")}
          </Button>
        )}
      </Card>
    </section>
  );
}
