import { useEffect, useId, useRef } from "react";
import type { ContractSchemas } from "@pwc/web-api";
import { useLocale } from "@pwc/web-i18n";
import { Button, Card } from "@pwc/web-ui";

/** Existing public projection only; not a publication, editing or authority API. */
export function PublicSummary({
  organization,
  onClose,
  navigation,
}: {
  organization: ContractSchemas["PublicOrganization"];
  onClose: () => void;
  navigation?: {
    position: number;
    total: number;
    previous?: (() => void) | undefined;
    next?: (() => void) | undefined;
  };
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const titleId = useId();
  const positionId = useId();
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    heading.current?.focus();
  }, [organization.id]);
  return (
    <section
      aria-labelledby={titleId}
      className="stack public-summary"
      onKeyDown={(event) => {
        if (event.key === "Escape" && !event.defaultPrevented) {
          event.preventDefault();
          event.stopPropagation();
          onClose();
        }
      }}
    >
      <h2
        id={titleId}
        tabIndex={-1}
        ref={heading}
        aria-describedby={navigation ? positionId : undefined}
      >
        {t("NGO public summary", "تنظیم کا عوامی خلاصہ")}
      </h2>
      {navigation && (
        <div className="stack">
          <p id={positionId}>
            {t(
              `Public result ${navigation.position} of ${navigation.total} on this page`,
              `اس صفحے پر ${navigation.total} میں سے عوامی نتیجہ ${navigation.position}`,
            )}
          </p>
          <nav
            aria-label={t(
              "Public summary navigation",
              "عوامی خلاصے کی سمت یابی",
            )}
            className="action-row"
          >
            <Button
              variant="secondary"
              disabled={!navigation.previous}
              onClick={navigation.previous}
            >
              {t("Previous NGO", "پچھلی تنظیم")}
            </Button>
            <Button
              variant="secondary"
              disabled={!navigation.next}
              onClick={navigation.next}
            >
              {t("Next NGO", "اگلی تنظیم")}
            </Button>
          </nav>
        </div>
      )}
      <Card title={organization.name}>
        <dl>
          <dt>{t("Registry reference", "فہرست کا حوالہ")}</dt>
          <dd>
            <bdi>{organization.id}</bdi>
          </dd>
          <dt>{t("City", "شہر")}</dt>
          <dd>
            {organization.city || t("Not provided", "فراہم نہیں کیا گیا")}
          </dd>
          <dt>{t("Classification", "درجہ بندی")}</dt>
          <dd>
            {organization.classification === "registered"
              ? t("Registered", "رجسٹرڈ")
              : t("Unregistered", "غیر رجسٹرڈ")}
          </dd>
        </dl>
      </Card>
      <p>
        {t(
          "Existing public registry information only. Classification is not a legal or financial endorsement. This summary does not provide administrator access, private records or permission to edit or publish.",
          "صرف موجودہ عوامی فہرست کی معلومات۔ درجہ بندی قانونی یا مالی توثیق نہیں۔ یہ خلاصہ منتظم رسائی، نجی ریکارڈ یا ترمیم اور اشاعت کی اجازت نہیں دیتا۔",
        )}
      </p>
      <Button onClick={onClose}>
        {t("Close public summary", "عوامی خلاصہ بند کریں")}
      </Button>
    </section>
  );
}
