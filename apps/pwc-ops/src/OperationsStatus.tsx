import { useEffect, useRef, useState } from "react";
import { useLocale } from "@pwc/web-i18n";
import { Banner, Button, Card } from "@pwc/web-ui";
import type { ContractSchemas, OperationsPolicyClient } from "@pwc/web-api";

/** Actual permitted policy read, NOT a reviewer queue or session capabilities. */
export function OperationsStatus({
  gateway,
}: {
  gateway?: OperationsPolicyClient;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [policy, setPolicy] = useState<
    ContractSchemas["ControlledOnboardingRequirements"] | null
  >(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const generation = useRef(0);
  const pending = useRef(false);
  useEffect(() => {
    const clear = () => {
      generation.current++;
      pending.current = false;
      setPolicy(null);
      setBusy(false);
      setFailed(false);
    };
    clear();
    const disconnect = gateway?.state.subscribe(clear);
    return () => {
      generation.current++;
      disconnect?.();
    };
  }, [gateway, locale]);
  async function read() {
    if (!gateway || pending.current) return;
    pending.current = true;
    setBusy(true);
    setPolicy(null);
    setFailed(false);
    const ticket = ++generation.current;
    try {
      const result = await gateway.read();
      if (ticket === generation.current) setPolicy(result);
    } catch {
      if (ticket === generation.current) setFailed(true);
    } finally {
      if (ticket === generation.current) {
        setBusy(false);
        pending.current = false;
      }
    }
  }
  return (
    <section className="stack">
      <h1>
        {t(
          "Operations · Controlled rollout status",
          "آپریشنز · محدود اجرا کی حالت",
        )}
      </h1>
      <Banner
        title={t("Policy, not capabilities", "پالیسی، اختیارات نہیں")}
        tone="restricted"
      >
        {t(
          "No private queue, verification decisions, operator appointment, invitations or grant activation. Public registry browsing is separate. Personal authentication is not reviewer authorization.",
          "نجی قطار، تصدیق کے فیصلے، تقرری، دعوت یا اختیارات کی فعالیت دستیاب نہیں۔ عوامی فہرست الگ ہے۔ ذاتی شناخت جائزہ لینے کا اختیار نہیں۔",
        )}
      </Banner>
      <Button disabled={!gateway || busy} onClick={() => void read()}>
        {t("Refresh rollout policy", "اجرا کی پالیسی دوبارہ دیکھیں")}
      </Button>
      <p role="status">
        {busy
          ? t("Loading…", "لوڈ ہو رہا ہے…")
          : failed
            ? t(
                "Policy unavailable or access changed. No private data retained.",
                "پالیسی دستیاب نہیں یا رسائی تبدیل ہو گئی۔ نجی معلومات محفوظ نہیں رکھی گئیں۔",
              )
            : !gateway
              ? t(
                  "Authenticated policy transport disabled pending integration acceptance.",
                  "منظوری تک ذاتی پالیسی رابطہ بند ہے۔",
                )
              : !policy
                ? t(
                    "Refresh to read current server policy.",
                    "سرور کی موجودہ پالیسی دوبارہ دیکھیں۔",
                  )
                : t(
                    "Source: authenticated Django policy read. No individual capability or authority is asserted.",
                    "ماخذ: شناخت شدہ جنگو پالیسی۔ کسی فرد کے اختیار کی تصدیق نہیں ہوتی۔",
                  )}
      </p>
      {policy && (
        <Card title={t("Current rollout policy", "اجرا کی موجودہ پالیسی")}>
          <p>
            {t("Policy version", "پالیسی کا ورژن")}:{" "}
            <bdi>{policy.policy_version}</bdi>
          </p>
          <p>
            {t(
              "Self-service, raw documents, operator commands, invitations and grant activation: unavailable.",
              "خودکار شمولیت، اصل دستاویزات، منتظم احکامات، دعوتیں اور اختیارات کی فعالیت: غیر دستیاب۔",
            )}
          </p>
          <p>
            {t(
              "Independent, distinct authorized individuals are required. Pending blockers:",
              "الگ اور آزاد مجاز افراد درکار ہیں۔ زیر التوا رکاوٹیں:",
            )}
          </p>
          <ul>
            {policy.blockers.map((code) => (
              <li key={code}>
                <bdi>{code}</bdi>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </section>
  );
}
