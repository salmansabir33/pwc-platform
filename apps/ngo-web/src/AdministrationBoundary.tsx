import { useLocale } from "@pwc/web-i18n";
import { Banner, Card } from "@pwc/web-ui";
export type AdministrationState =
  "unavailable" | "no-context" | "restricted" | "expired";
/** UI-state preparation only. No recipient token, roster or grants supplied. */
export function AdministrationBoundary({
  state = "unavailable",
}: {
  state?: AdministrationState;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const reason = {
    unavailable: t(
      "Administration integrations are unavailable.",
      "انتظامی رابطے دستیاب نہیں۔",
    ),
    "no-context": t(
      "No authorized NGO context. A personal session is not an NGO role.",
      "تنظیم کا مجاز سیاق موجود نہیں۔ ذاتی نشست تنظیم کا کردار نہیں۔",
    ),
    restricted: t(
      "Access restricted. Private information and pending actions cleared.",
      "رسائی محدود ہے۔ نجی معلومات اور زیر التوا اقدامات ہٹا دیے گئے ہیں۔",
    ),
    expired: t(
      "Session or invitation expired. Reauthentication does not activate authority.",
      "نشست یا دعوت ختم ہو چکی ہے۔ دوبارہ شناخت اختیار فعال نہیں کرتی۔",
    ),
  }[state];
  return (
    <section className="stack">
      <h1>{t("NGO administration boundary", "تنظیم کی انتظامی حد")}</h1>
      <Banner
        title={t(
          "UI-state preparation · no active authority",
          "حالتوں کی تیاری · کوئی فعال اختیار نہیں",
        )}
        tone="restricted"
      >
        <p role="status">{reason}</p>
      </Banner>
      <Card
        title={t("NGO overview and information", "تنظیم کا جائزہ اور معلومات")}
      >
        {t(
          "Only the separate public registry exposes approved name, city and classification. No private profile is loaded here.",
          "صرف الگ عوامی فہرست میں منظور شدہ نام، شہر اور درجہ بندی دستیاب ہیں۔ یہاں نجی پروفائل لوڈ نہیں ہوتا۔",
        )}
      </Card>
      <Card
        title={t("Administrators and representatives", "منتظمین اور نمائندے")}
      >
        {t(
          "No private roster or appointment writer is available. Primary and ordinary administrators are distinct; neither implies finance, signatory, alliance or support powers.",
          "نجی فہرست یا تقرری کا عمل دستیاب نہیں۔ بنیادی اور عام منتظم الگ ہیں؛ مالی، دستخطی، اتحاد یا معاونت کے اختیارات خودکار نہیں ملتے۔",
        )}
      </Card>
      <Card title={t("Nonfinance permissions", "غیر مالی اختیارات")}>
        {t(
          "No permission editor or grant activation. A historical claim or verification preparation does not confer authority.",
          "اختیار میں تبدیلی یا فعالیت دستیاب نہیں۔ سابقہ دعویٰ یا تصدیق کی تیاری اختیار نہیں دیتی۔",
        )}
      </Card>
      <Card
        title={t(
          "Invitations and appointment requests",
          "دعوتیں اور تقرری کی درخواستیں",
        )}
      >
        {t(
          "Unavailable pending recipient-bound contracts and independent approvals. An invitation lasts at most 72 hours; acceptance is distinct from grant activation. No invitation acceptance or appointment success is claimed.",
          "وصول کنندہ سے منسلک معاہدوں اور آزاد منظوری تک غیر دستیاب۔ دعوت زیادہ سے زیادہ ۷۲ گھنٹے کی ہے؛ قبولیت اختیار کی فعالیت سے الگ ہے۔ کامیابی کا دعویٰ نہیں کیا جاتا۔",
        )}
      </Card>
    </section>
  );
}
