import { useMemo } from "react";
import { Banner, PersonalSessionPanel } from "@pwc/web-ui";
import { useLocale } from "@pwc/web-i18n";
import type {
  PersonalWorkspaceSession,
  OperationsPolicyClient,
} from "@pwc/web-api";
import { OperationsStatus } from "./OperationsStatus";
/** Separate Operations portal context. Personal login cannot appoint an officer.
 * No production adapter is supplied by App. */
export function OperationsWorkspace({
  session,
  policy,
}: {
  session?: PersonalWorkspaceSession;
  policy?: OperationsPolicyClient;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  // Immutable object keeps presentation port identity stable during renders.
  const port = useMemo(() => session, [session]);
  return (
    <section className="stack">
      <Banner
        title={t("Operations personal session", "آپریشنز کی ذاتی نشست")}
        tone="restricted"
      >
        {t(
          "Personal authentication is not PWC officer authority. Reviewer queues and privileged commands remain unavailable.",
          "ذاتی شناخت پی ڈبلیو سی افسر کا اختیار نہیں۔ جائزے کی قطاریں اور خصوصی احکامات غیر دستیاب ہیں۔",
        )}
      </Banner>
      <PersonalSessionPanel {...(port ? { session: port } : {})}>
        {(view) => (
          <OperationsStatus
            {...(view && port?.state.currentScope && policy
              ? { gateway: policy }
              : {})}
          />
        )}
      </PersonalSessionPanel>
    </section>
  );
}
