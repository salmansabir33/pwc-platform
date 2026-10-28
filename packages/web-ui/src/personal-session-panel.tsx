import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useLocale } from "@pwc/web-i18n";
import { Button } from "./button";
import { TextField } from "./index";
import { SelectField } from "./components";

type View = {
  hold: "clear" | "restricted" | "review_required";
  emailVerified: boolean;
};
/** Presentation port only; no web-api dependency or grant inference. */
export interface PersonalSessionPort {
  subscribe(listener: () => void): () => void;
  refresh(): Promise<View>;
  login(
    email: string,
    password: string,
  ): Promise<
    { kind: "mfa"; expiresIn: number } | { kind: "session"; view: View }
  >;
  confirmMfa(method: "totp" | "recovery_code", code: string): Promise<View>;
  logout(): Promise<void>;
  clear(): void;
}
export function PersonalSessionPanel({
  session,
  children,
}: {
  session?: PersonalSessionPort;
  children: (view: View | null) => ReactNode;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [view, setView] = useState<View | null>(null);
  const [mfa, setMfa] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [retryAt, setRetryAt] = useState<number | null>(null);
  const [retryLogout, setRetryLogout] = useState(false);
  const generation = useRef(0);
  const pending = useRef(false);
  const forms = useRef<HTMLDivElement>(null);
  useEffect(() => {
    generation.current++;
    pending.current = false;
    setView(null);
    setMfa(null);
    setBusy(false);
    setMessage("");
    setRetryLogout(false);
    const disconnect = session?.subscribe(() => {
      setView(null);
      setMfa(null);
      forms.current?.querySelectorAll("form").forEach((form) => form.reset());
    });
    return () => {
      generation.current++;
      disconnect?.();
      session?.clear();
    };
  }, [session, locale]);
  useEffect(() => {
    if (!mfa) return;
    const timer = setTimeout(() => {
      session?.clear();
      setMfa(null);
      setMessage(
        t(
          "Sign-in challenge expired. Start again.",
          "شناخت کی درخواست ختم ہو گئی۔ دوبارہ شروع کریں۔",
        ),
      );
    }, mfa * 1000);
    return () => clearTimeout(timer);
  }, [mfa, session, locale]);
  useEffect(() => {
    if (retryAt === null) return;
    const timer = setTimeout(
      () => setRetryAt(null),
      Math.max(0, retryAt - performance.now()),
    );
    return () => clearTimeout(timer);
  }, [retryAt]);
  async function action(
    kind: "login" | "confirm" | "check" | "logout",
    email = "",
    password = "",
    method: "totp" | "recovery_code" = "totp",
    code = "",
  ) {
    if (!session || pending.current || retryAt !== null) return;
    pending.current = true;
    setBusy(true);
    setMessage("");
    const ticket = ++generation.current;
    try {
      if (kind === "logout") {
        setView(null);
        setMfa(null);
        await session.logout();
        if (ticket === generation.current) {
          setRetryLogout(false);
          setMessage(
            t(
              "Signed out on the server. Private data cleared.",
              "سرور سے نشست ختم ہو گئی۔ ذاتی معلومات ہٹا دی گئیں۔",
            ),
          );
        }
      } else if (kind === "login") {
        const result = await session.login(email, password);
        if (ticket !== generation.current) return;
        setRetryLogout(false);
        if (result.kind === "mfa") setMfa(result.expiresIn);
        else setView(result.view);
      } else {
        const result =
          kind === "check"
            ? await session.refresh()
            : await session.confirmMfa(method, code);
        if (ticket === generation.current) {
          setMfa(null);
          setView(result);
          setRetryLogout(false);
        }
      }
    } catch (error) {
      if (ticket === generation.current) {
        setView(null);
        setMfa(null);
        setRetryLogout(kind === "logout");
        if (
          error &&
          typeof error === "object" &&
          "status" in error &&
          error.status === 429
        ) {
          const seconds =
            "retryAfterSeconds" in error &&
            typeof error.retryAfterSeconds === "number" &&
            Number.isFinite(error.retryAfterSeconds)
              ? Math.max(1, Math.min(999999, error.retryAfterSeconds))
              : 60;
          setRetryAt(performance.now() + seconds * 1000);
          setMessage(
            t(
              "Too many attempts. Wait before explicitly trying again; no automatic retry.",
              "کوششیں زیادہ ہو گئی ہیں۔ دوبارہ کوشش سے پہلے انتظار کریں؛ خودکار کوشش نہیں ہوگی۔",
            ),
          );
          return;
        }
        setMessage(
          kind === "logout"
            ? t(
                "Local data cleared; server logout unconfirmed. Check the session or explicitly retry logout.",
                "مقامی معلومات ہٹا دی گئیں؛ سرور پر نشست ختم ہونے کی تصدیق نہیں۔ نشست چیک کریں یا دوبارہ خروج کریں۔",
              )
            : t(
                "Session unavailable or expired, credentials rejected, or access restricted. No command retried. Check the session after an uncertain response or start sign-in again.",
                "نشست دستیاب نہیں، ختم ہو گئی، معلومات درست نہیں یا رسائی محدود ہے۔ کوئی حکم دوبارہ نہیں بھیجا گیا۔ جواب غیر مصدقہ ہو تو نشست چیک کریں یا دوبارہ شناخت کریں۔",
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
  return (
    <div className="stack" ref={forms}>
      {session && (
        <>
          {!view && !mfa && (
            <form
              className="stack"
              onSubmit={(event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const data = new FormData(form);
                const email = String(data.get("email") ?? ""),
                  password = String(data.get("password") ?? "");
                form.reset();
                void action("login", email, password);
              }}
            >
              <TextField
                label={t("Email", "ای میل")}
                hint={t(
                  "Your verified email address",
                  "آپ کا تصدیق شدہ ای میل پتہ",
                )}
                type="text"
                inputMode="email"
                name="email"
                autoComplete="username"
                maxLength={2048}
                required
                disabled={busy || retryAt !== null}
              />
              <TextField
                label={t("Password", "پاس ورڈ")}
                hint={t(
                  "Paste and password managers are supported",
                  "پیسٹ اور پاس ورڈ مینیجر استعمال کر سکتے ہیں",
                )}
                type="password"
                name="password"
                autoComplete="current-password"
                maxLength={256}
                required
                disabled={busy || retryAt !== null}
              />
              <Button type="submit" disabled={busy || retryAt !== null}>
                {t("Sign in", "داخل ہوں")}
              </Button>
            </form>
          )}
          {mfa && (
            <form
              className="stack"
              onSubmit={(event) => {
                event.preventDefault();
                const form = event.currentTarget;
                const data = new FormData(form);
                const method =
                  data.get("method") === "recovery_code"
                    ? "recovery_code"
                    : "totp";
                const code = String(data.get("code") ?? "");
                form.reset();
                void action("confirm", "", "", method, code);
              }}
            >
              <p role="status">
                {t(
                  "Second factor required. This is not an authenticated session.",
                  "دوسری تصدیق درکار ہے۔ یہ شناخت شدہ نشست نہیں ہے۔",
                )}
              </p>
              <SelectField
                label={t("Second factor method", "دوسری تصدیق کا طریقہ")}
                name="method"
                disabled={busy || retryAt !== null}
              >
                <option value="totp">
                  {t("Authenticator code", "تصدیقی ایپ کا کوڈ")}
                </option>
                <option value="recovery_code">
                  {t(
                    "Recovery code (restricted session)",
                    "بحالی کا کوڈ (محدود نشست)",
                  )}
                </option>
              </SelectField>
              <TextField
                label={t("Second factor code", "دوسری تصدیق کا کوڈ")}
                hint={t(
                  "Used only for this sign-in attempt",
                  "صرف اس شناخت کی کوشش کے لیے استعمال ہوگا",
                )}
                type="password"
                name="code"
                autoComplete="one-time-code"
                maxLength={1024}
                required
                disabled={busy || retryAt !== null}
              />
              <Button type="submit" disabled={busy || retryAt !== null}>
                {t("Confirm second factor", "دوسری تصدیق کریں")}
              </Button>
              <Button
                type="button"
                disabled={busy || retryAt !== null}
                onClick={() => {
                  session.clear();
                  setMfa(null);
                }}
              >
                {t("Cancel sign-in", "شناخت منسوخ کریں")}
              </Button>
            </form>
          )}
          <div className="action-row">
            <Button
              disabled={busy || retryAt !== null}
              onClick={() => void action("check")}
            >
              {t("Check personal session", "ذاتی نشست چیک کریں")}
            </Button>
            {(view || retryLogout) && (
              <Button
                disabled={busy || retryAt !== null}
                onClick={() => void action("logout")}
              >
                {t("Sign out", "نشست ختم کریں")}
              </Button>
            )}
          </div>
        </>
      )}
      <p role="status">
        {busy
          ? t("Checking session…", "نشست چیک ہو رہی ہے…")
          : message ||
            (view?.hold !== undefined && view.hold !== "clear"
              ? t(
                  "Recovery-restricted session. Private history cleared; recovery is not a grant.",
                  "بحالی کی وجہ سے نشست محدود ہے۔ ذاتی تاریخ ہٹا دی گئی؛ بحالی اختیار نہیں ہے۔",
                )
              : view && !view.emailVerified
                ? t(
                    "Verified contact required. History remains restricted.",
                    "تصدیق شدہ رابطہ درکار ہے۔ تاریخ محدود ہے۔",
                  )
                : view
                  ? t(
                      "Personal session checked. No active NGO authority.",
                      "ذاتی نشست چیک ہو گئی۔ تنظیم کا فعال اختیار نہیں۔",
                    )
                  : t(
                      "No checked personal session.",
                      "چیک شدہ ذاتی نشست موجود نہیں۔",
                    ))}
      </p>
      {children(view)}
    </div>
  );
}
