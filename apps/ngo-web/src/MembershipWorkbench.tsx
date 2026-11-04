import { useState } from "react";
import { useLocale } from "@pwc/web-i18n";
import { Banner, Button, Card, PageHeader } from "@pwc/web-ui";
import examples from "../../../packages/api-contracts/fixtures/membership-demonstrations.json";

type Step = {
  policy_revision?: number;
  category_count?: number;
  active_category_count?: number;
  pending_review_count?: number;
  policy_history?: {
    revision: number;
    operation: string;
    mode: string;
    active_category_count: number;
  }[];
  revision?: number;
  member_count?: number;
  row_count?: number;
  candidate_count?: number;
  code?: string;
  rows?: { record: number; errors: string[]; warnings: string[] }[];
  history?: {
    revision: number;
    kind: string;
    from_state: string;
    to_state: string;
    category_changed: boolean;
  }[];
};
const scenarios: { id: string; steps: Step[] }[] = examples.scenarios;
const titles: Record<string, [string, string]> = {
  "category-policy": [
    "Category and policy versions",
    "زمرے اور پالیسی کی ترامیم",
  ],
  admission: ["Admission requests", "رکنیت کی درخواستیں"],
  category: ["Category assignment", "زمرے کی تبدیلی"],
  status: ["Member status and history", "رکن کی حالت اور تاریخ"],
  stale: ["Source revision conflict", "ماخذ کی ترمیم میں تضاد"],
  import: ["Import preparation", "درآمد کی تیاری"],
};
const words: Record<string, [string, string]> = {
  initial: ["Initial policy", "ابتدائی پالیسی"],
  category_created: ["Category created", "زمرہ بنایا گیا"],
  category_updated: ["Category renamed", "زمرے کا نام بدلا گیا"],
  category_deactivated: ["Category deactivated", "زمرہ غیر فعال کیا گیا"],
  mode_changed: ["Admission mode changed", "داخلے کا طریقہ بدلا گیا"],
  open: ["Open", "کھلا"],
  approval: ["Approval", "منظوری"],
  invitation: ["Invitation", "دعوت"],
  draft: ["Draft", "مسودہ"],
  pending: ["Pending", "زیر التوا"],
  accepted: ["Proposed acceptance", "قبولیت کی تجویز"],
  declined: ["Declined", "مسترد"],
  cancelled: ["Cancelled", "منسوخ"],
  active: ["Active", "فعال"],
  suspended: ["Suspended", "معطل"],
  ended: ["Ended", "ختم شدہ"],
};
/** Fixed redacted fixture viewer only. No gateway, file input, member data or writer. */
export function MembershipWorkbench() {
  const { locale } = useLocale();
  const [selected, setSelected] = useState("admission");
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const label = (key: string, dict = words) => {
    const pair = dict[key];
    return pair ? t(...pair) : key;
  };
  const scenario = scenarios.find((s) => s.id === selected)!;
  return (
    <section className="stack">
      <PageHeader
        title={t("Membership preparation", "رکنیت کی تیاری")}
        description={t(
          "P4 · Internal synthetic demonstration, not a live NGO workspace.",
          "پی ۴ · اندرونی فرضی نمونہ، حقیقی تنظیم کا شعبہ نہیں۔",
        )}
      />
      <Banner
        tone="restricted"
        title={t("Live membership unavailable", "حقیقی رکنیت دستیاب نہیں")}
      >
        <p>
          {t(
            "Fictional counts and validation only. Nothing is sent, saved, admitted or linked. A valid proposal grants no authority.",
            "صرف فرضی شمار اور جانچ۔ کچھ بھیجا، محفوظ، منظور یا منسلک نہیں ہوتا۔ درست تجویز کوئی اختیار نہیں دیتی۔",
          )}
        </p>
      </Banner>
      <label className="field-label" htmlFor="membership-example">
        {t("Read-only example", "صرف مطالعے کا نمونہ")}
      </label>
      <select
        id="membership-example"
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
      >
        {scenarios.map((s) => (
          <option key={s.id} value={s.id}>
            {label(s.id, titles)}
          </option>
        ))}
      </select>
      <div role="status" aria-live="polite">
        {t("Viewing fictional example:", "فرضی نمونہ:")}{" "}
        {label(selected, titles)}
      </div>
      <Card title={label(selected, titles)}>
        {scenario.steps.map((step, index) => (
          <section key={`${selected}-${index}`} className="stack">
            <h3>
              {t("Proposed step", "مجوزہ مرحلہ")} {index + 1}
            </h3>
            {step.policy_revision !== undefined && (
              <>
                <p>
                  {t("Policy revision", "پالیسی کی ترمیم")}:{" "}
                  {step.policy_revision} · {t("Categories", "زمرے")}:{" "}
                  {step.category_count} · {t("Active categories", "فعال زمرے")}:{" "}
                  {step.active_category_count}
                </p>
                <p>
                  {t(
                    "Pending fixtures requiring explicit re-review",
                    "دوبارہ جائزے کے منتظر فرضی اندراجات",
                  )}
                  : {step.pending_review_count}
                </p>
              </>
            )}
            {step.policy_history && (
              <ol
                aria-label={t(
                  "Proposed policy history",
                  "پالیسی کی مجوزہ تاریخ",
                )}
              >
                {step.policy_history.map((h) => (
                  <li key={h.revision}>
                    {h.revision}: {label(h.operation)} · {label(h.mode)} ·{" "}
                    {t("Active categories", "فعال زمرے")}:{" "}
                    {h.active_category_count}
                  </li>
                ))}
              </ol>
            )}
            {step.revision !== undefined && (
              <p>
                {t("Fixture revision", "فرضی ترمیم")}: {step.revision} ·{" "}
                {t("Fictional members", "فرضی ارکان")}: {step.member_count}
              </p>
            )}
            {step.code && (
              <p role="alert">
                {t(
                  "Validation rejected stale source. Refresh the fixture before proposing another change.",
                  "پرانا ماخذ مسترد ہوا۔ نئی تجویز سے پہلے فرضی ماخذ تازہ کریں۔",
                )}{" "}
                <code>{step.code}</code>
              </p>
            )}
            {step.history && (
              <ol
                aria-label={t(
                  "Redacted proposed history",
                  "مجوزہ تاریخ کا محدود خلاصہ",
                )}
              >
                {step.history.map((h) => (
                  <li key={h.revision}>
                    {h.revision}: {label(h.from_state)} → {label(h.to_state)}
                    {h.category_changed
                      ? t(" · category changed", " · زمرہ تبدیل")
                      : ""}
                  </li>
                ))}
              </ol>
            )}
            {step.row_count !== undefined && (
              <p>
                {t("CSV records", "سی ایس وی ریکارڈ")}: {step.row_count} ·{" "}
                {t("Admission candidates only", "صرف داخلے کے امیدوار")}:{" "}
                {step.candidate_count}
              </p>
            )}
            {step.rows && (
              <ul>
                {step.rows.map((r) => (
                  <li key={r.record}>
                    {t("Record", "ریکارڈ")} {r.record}:{" "}
                    {r.errors.length ? (
                      <>
                        {t("Validation rejected", "جانچ میں مسترد")}{" "}
                        <code>{r.errors.join(", ")}</code>
                      </>
                    ) : (
                      t(
                        "Candidate only; no import or admission",
                        "صرف امیدوار؛ درآمد یا داخلہ نہیں",
                      )
                    )}
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </Card>
      <fieldset disabled className="stack">
        <legend>
          {t("Protected workflows — unavailable", "محفوظ عمل — غیر دستیاب")}
        </legend>
        <div className="action-row">
          {[
            ["Save category", "زمرہ محفوظ کریں"],
            ["Approve admission", "داخلہ منظور کریں"],
            ["Change member status", "رکن کی حالت بدلیں"],
            ["Upload or commit import", "درآمد اپ لوڈ یا نافذ کریں"],
            ["Claim or link account", "اکاؤنٹ کا دعویٰ یا ربط"],
          ].map(([en, ur]) => (
            <Button key={en} disabled>
              {t(en!, ur!)}
            </Button>
          ))}
        </div>
      </fieldset>
      <Card title={t("Separate approval boundaries", "الگ منظوری کی حدود")}>
        <p>
          {t(
            "CSV preview → authorized staging → import approval → atomic creation → separately verified claim. None is enabled here. No names or contact matching can link an account.",
            "سی ایس وی جائزہ ← مجاز تیاری ← درآمد کی منظوری ← یکجا تخلیق ← الگ تصدیق شدہ دعویٰ۔ یہاں کوئی مرحلہ فعال نہیں۔ نام یا رابطے کا ملاپ اکاؤنٹ منسلک نہیں کر سکتا۔",
          )}
        </p>
      </Card>
    </section>
  );
}
