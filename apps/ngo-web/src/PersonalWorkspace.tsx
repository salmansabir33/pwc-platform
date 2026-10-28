import { useLocale } from "@pwc/web-i18n";
import { Banner, PersonalSessionPanel } from "@pwc/web-ui";
import type { PersonalWorkspaceSession } from "@pwc/web-api";
import { WorkspaceHistory } from "./WorkspaceHistory";

export function PersonalWorkspace({
  session,
}: {
  session?: PersonalWorkspaceSession;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
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
      <PersonalSessionPanel {...(session ? { session } : {})}>
        {(view) => (
          <WorkspaceHistory
            {...(view && session?.state.currentScope
              ? { gateway: session.history }
              : {})}
          />
        )}
      </PersonalSessionPanel>
    </section>
  );
}
