import { useEffect, useRef, useState } from "react";
import { useLocale } from "@pwc/web-i18n";
import { Button, Card, Badge, SelectField, Banner } from "@pwc/web-ui";
import type {
  WorkspaceApplication,
  WorkspaceGateway,
  WorkspacePage,
} from "@pwc/web-api";

/** Claimant-owned history, never a roster or active NGO workspace. */
export function WorkspaceHistory({ gateway }: { gateway?: WorkspaceGateway }) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const stateName = (value: string) =>
    ({
      draft: t("Draft", "مسودہ"),
      submitted: t("Submitted", "جمع شدہ"),
      pending: t("Pending", "زیر التوا"),
      needs_information: t("Information required", "مزید معلومات درکار"),
      rejected: t("Rejected", "مسترد"),
      withdrawn: t("Withdrawn", "واپس لی گئی"),
    })[value] ?? t("Unavailable", "غیر دستیاب");
  const purposeName = (value: string) =>
    value === "organization_eligibility"
      ? t("NGO eligibility", "تنظیم کی اہلیت")
      : t("Representative mandate", "نمائندے کا اختیار");
  const [kind, setKind] = useState<"draft" | "claim">("draft");
  const [filter, setFilter] = useState("");
  const [page, setPage] = useState<WorkspacePage | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const generation = useRef(0);
  const active = useRef(false);
  const clear = () => {
    generation.current++;
    active.current = false;
    setPage(null);
    setBusy(false);
    setMessage("");
  };
  useEffect(() => {
    clear();
    const disconnect = gateway?.state.subscribe(() => {
      clear();
      setMessage(
        t(
          "Access changed. Private history cleared; reauthenticate or refresh before proceeding.",
          "رسائی تبدیل ہو گئی۔ ذاتی تاریخ ہٹا دی گئی ہے۔",
        ),
      );
    });
    return () => {
      generation.current++;
      disconnect?.();
    };
  }, [gateway, locale]);
  async function load(cursor?: string, withdrawal?: WorkspaceApplication) {
    if (!gateway || active.current) return;
    active.current = true;
    setBusy(true);
    setMessage("");
    const ticket = ++generation.current;
    setPage(null);
    try {
      if (withdrawal) await gateway.withdraw(withdrawal);
      if (ticket !== generation.current) return;
      const next = await gateway.list(kind, filter, cursor);
      if (ticket === generation.current) setPage(next);
    } catch {
      if (ticket === generation.current)
        setMessage(
          t(
            "Request unavailable or access changed. Refresh after reauthentication. A withdrawal response may be lost; check current history before trying again.",
            "درخواست دستیاب نہیں یا رسائی تبدیل ہو گئی۔ موجودہ تاریخ دوبارہ دیکھیں؛ واپسی کی درخواست خودکار طور پر نہیں دہرائی جائے گی۔",
          ),
        );
    } finally {
      if (ticket === generation.current) {
        active.current = false;
        setBusy(false);
      }
    }
  }
  return (
    <section className="stack">
      <h1 tabIndex={-1}>
        {t(
          "ORG-01 / ORG-02 · My application history",
          "میری درخواستوں کی تاریخ",
        )}
      </h1>
      <Banner
        title={t("Personal history only", "صرف ذاتی تاریخ")}
        tone="restricted"
      >
        {t(
          "No NGO administration, members, invitations, verification decisions or nonfinance grants are available. Primary and ordinary administrator roles require separate authority. New applications remain unavailable.",
          "تنظیم کی انتظامیہ، اراکین، دعوتیں اور اختیارات دستیاب نہیں۔ نئی درخواستیں بند ہیں۔",
        )}
      </Banner>
      {!gateway && (
        <p role="status">
          {t(
            "Personal networking remains disabled pending W2 integration acceptance. Public registry browsing is separate.",
            "ذاتی نیٹ ورکنگ منظوری تک بند ہے۔ عوامی فہرست الگ ہے۔",
          )}
        </p>
      )}
      <SelectField
        label={t("Application type", "درخواست کی قسم")}
        value={kind}
        disabled={busy}
        onChange={(e) => {
          clear();
          setKind(e.target.value as "draft" | "claim");
        }}
      >
        <option value="draft">
          {t("Historical NGO drafts", "سابقہ تنظیم مسودے")}
        </option>
        <option value="claim">
          {t("Historical representation claims", "سابقہ نمائندگی کے دعوے")}
        </option>
      </SelectField>
      <SelectField
        label={t("Application state", "درخواست کی حالت")}
        value={filter}
        disabled={busy}
        onChange={(e) => {
          clear();
          setFilter(e.target.value);
        }}
      >
        <option value="">{t("All states", "تمام حالتیں")}</option>
        {[
          "draft",
          "submitted",
          "pending",
          "needs_information",
          "rejected",
          "withdrawn",
        ].map((value) => (
          <option key={value} value={value}>
            {stateName(value)}
          </option>
        ))}
      </SelectField>
      <Button disabled={!gateway || busy} onClick={() => void load()}>
        {t("Refresh history", "تاریخ دوبارہ دیکھیں")}
      </Button>
      {gateway && (
        <p role="status">
          {busy
            ? t("Loading…", "لوڈ ہو رہا ہے…")
            : message ||
              (page
                ? t(
                    `${page.results.length} applications on this page`,
                    `اس صفحے پر ${page.results.length} درخواستیں`,
                  )
                : t(
                    "Refresh to load current history.",
                    "موجودہ تاریخ لوڈ کریں۔",
                  ))}
        </p>
      )}
      {page?.results.length === 0 && (
        <p>
          {t(
            "No matching historical applications.",
            "کوئی مماثل سابقہ درخواست نہیں۔",
          )}
        </p>
      )}
      {page && !page.verification_available && (
        <p>
          {t(
            "Verification history is unavailable.",
            "تصدیق کی تاریخ دستیاب نہیں۔",
          )}
        </p>
      )}
      {page?.results.map((item) => (
        <Card
          key={item.id}
          title={
            item.name ??
            t(
              "Claim target details are restricted",
              "دعوے کی تنظیم کی تفصیل محدود ہے",
            )
          }
        >
          {item.city && <p>{item.city}</p>}
          <Badge
            tone={
              item.state === "withdrawn" || item.state === "rejected"
                ? "restricted"
                : "info"
            }
          >
            {stateName(item.state)}
          </Badge>
          <p>
            {t("Revision", "نظر ثانی")}: {item.revision}
          </p>
          {item.verification.map((c) => (
            <p key={c.id}>
              {purposeName(c.purpose)} · {stateName(c.state)} ·{" "}
              {t("Source revision", "ماخذ کی نظر ثانی")}: {c.source_revision}{" "}
              {c.stale &&
                t(
                  "· Stale source — not current approval",
                  "· پرانا ماخذ — موجودہ منظوری نہیں",
                )}
            </p>
          ))}
          {item.can_withdraw && (
            <Button
              disabled={busy}
              onClick={() => {
                if (
                  window.confirm(
                    t(
                      "Withdraw this historical application? This does not revoke or create NGO authority.",
                      "اس سابقہ درخواست کو واپس لیں؟ اس سے تنظیم کے اختیارات تبدیل نہیں ہوتے۔",
                    ),
                  )
                )
                  void load(undefined, item);
              }}
            >
              {t("Withdraw application", "درخواست واپس لیں")}
            </Button>
          )}
        </Card>
      ))}
      {page?.next_cursor && (
        <Button disabled={busy} onClick={() => void load(page.next_cursor!)}>
          {t("Next history page", "تاریخ کا اگلا صفحہ")}
        </Button>
      )}
    </section>
  );
}
