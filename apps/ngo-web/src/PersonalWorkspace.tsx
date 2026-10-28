import { useEffect, useRef, useState } from "react";
import { useLocale } from "@pwc/web-i18n";
import { Banner, Button } from "@pwc/web-ui";
import type { PersonalWorkspaceSession, SessionView } from "@pwc/web-api";
import { WorkspaceHistory } from "./WorkspaceHistory";

export function PersonalWorkspace({
  session,
}: {
  session?: PersonalWorkspaceSession;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const generation = useRef(0);
  const [view, setView] = useState<SessionView | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  useEffect(() => {
    generation.current++;
    setView(null);
    setBusy(false);
    setError(false);
    const disconnect = session?.state.subscribe(() => setView(null));
    return () => {
      generation.current++;
      disconnect?.();
      session?.clear();
    };
  }, [session, locale]);
  async function check() {
    if (!session || busy) return;
    const ticket = ++generation.current;
    setBusy(true);
    setError(false);
    try {
      const next = await session.refresh();
      if (ticket === generation.current) setView(next);
    } catch {
      if (ticket === generation.current) {
        setView(null);
        setError(true);
      }
    } finally {
      if (ticket === generation.current) setBusy(false);
    }
  }
  return (
    <section className="stack">
      <Banner
        title={t("Personal session boundary", "ذاتی نشست کی حد")}
        tone="restricted"
      >
        {t(
          "No NGO context or administrative authority is inferred from a personal session. Credentialed web integration remains gated.",
          "ذاتی نشست سے تنظیم کا سیاق یا انتظامی اختیار نہیں ملتا۔ ذاتی ویب رابطہ منظوری تک بند ہے۔",
        )}
      </Banner>
      {session && (
        <Button disabled={busy} onClick={() => void check()}>
          {t("Check personal session", "ذاتی نشست چیک کریں")}
        </Button>
      )}
      <p role="status">
        {busy
          ? t("Checking session…", "نشست چیک ہو رہی ہے…")
          : error
            ? t(
                "Session unavailable or expired. Reauthenticate separately, then check again. No withdrawal retried.",
                "نشست دستیاب نہیں یا ختم ہو گئی۔ دوبارہ شناخت کے بعد چیک کریں۔ واپسی دوبارہ نہیں بھیجی گئی۔",
              )
            : view?.hold !== undefined && view.hold !== "clear"
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
                    )}
      </p>
      <WorkspaceHistory
        {...(view && session?.state.currentScope
          ? { gateway: session.history }
          : {})}
      />
    </section>
  );
}
