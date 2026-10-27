import { useEffect, useState } from "react";
import { Button, TextField } from "@pwc/web-ui";
import { useLocale } from "@pwc/web-i18n";

type Draft = {
  organization: string;
  city: string;
  classification: "registered" | "unregistered";
  nominee: string;
  nomination: string;
  eligibility: string;
  mandate: string;
  method: string;
  examined: string;
};
const empty = (): Draft => ({
  organization: "",
  city: "",
  classification: "unregistered",
  nominee: "",
  nomination: "",
  eligibility: "",
  mandate: "",
  method: "",
  examined: "",
});
// Local synthetic preparation only. No transport, credentials, storage, operator
// appointment, invitation token, approval success or NGO authority is supplied.
export function ControlledOnboarding({
  synthetic = false,
  scope = "unavailable",
}: {
  synthetic?: boolean;
  scope?: string;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [draft, setDraft] = useState<Draft>(empty);
  const [history, setHistory] = useState<Readonly<Draft>[]>([]);
  useEffect(() => {
    setDraft(empty());
    setHistory([]);
  }, [scope, synthetic, locale]);
  const fields: [keyof Draft, string, number][] = [
    ["organization", "NGO display name", 250],
    ["city", "City", 100],
    ["nominee", "External nominee reference", 64],
    ["nomination", "Official nomination reference", 64],
    ["eligibility", "External eligibility evidence reference", 64],
    ["mandate", "External mandate evidence reference", 64],
    ["method", "External examination method reference", 64],
  ];
  return (
    <section className="stack">
      <h1>
        PWC-01 · {t("Controlled NGO onboarding", "کنٹرول شدہ تنظیم کی شمولیت")}
      </h1>
      <p role="status">
        {t(
          "Unavailable: operator/reviewer provisioning, command assurance and invitation contracts require independent acceptance. No live onboarding or browser networking.",
          "غیر دستیاب: منتظم، جائزہ اور دعوت کے معاہدوں کی آزاد منظوری درکار ہے۔",
        )}
      </p>
      <p>
        {t(
          "Initial rollout: external verification only. Public NGO self-registration and existing-NGO claims are unavailable. Do not enter real evidence or personal identity-document numbers.",
          "ابتدائی اجرا میں تصدیق بیرون ایپ ہوگی۔ عوامی تنظیم رجسٹریشن اور دعوے دستیاب نہیں۔ اصل دستاویزات درج نہ کریں۔",
        )}
      </p>
      <ol>
        <li>External eligibility and representative-mandate examination</li>
        <li>
          Specifically authorized operator records NGO and official nomination
        </li>
        <li>
          Distinct, independently authorized individual approves the precise
          revision
        </li>
        <li>
          Recipient-bound invitation: nominee activates own identity and accepts
          precise nonfinance authority
        </li>
        <li>Separate 04C / 03B.3 grant activation</li>
      </ol>
      <p>
        Platform Super Admin / verification-officer capabilities do not imply
        NGO-private data access. Staff, Board, MFA and recovery are not
        provisioning. Software access is independent of alliance membership.
      </p>
      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault();
          if (synthetic && history.length < 20) {
            setHistory((old) =>
              old.length < 20 ? [Object.freeze({ ...draft }), ...old] : old,
            );
          }
        }}
      >
        {fields.map(([key, label, max]) => (
          <TextField
            key={key}
            label={label}
            hint="Synthetic local preparation only; opaque custody handles are not document numbers, URLs or case contents."
            value={draft[key]}
            required
            maxLength={max}
            pattern={
              key === "organization" || key === "city"
                ? undefined
                : String.raw`[A-Z][A-Z0-9_\-]{0,63}`
            }
            disabled={!synthetic}
            onChange={(e) =>
              setDraft((old) => ({ ...old, [key]: e.target.value }))
            }
          />
        ))}
        <label>
          External examination date
          <input
            type="date"
            required
            disabled={!synthetic}
            value={draft.examined}
            onChange={(e) =>
              setDraft((old) => ({ ...old, examined: e.target.value }))
            }
          />
        </label>
        <label>
          Externally examined status
          <select
            value={draft.classification}
            disabled={!synthetic}
            onChange={(e) =>
              setDraft((old) => ({
                ...old,
                classification: e.target.value as Draft["classification"],
              }))
            }
          >
            <option value="registered">Registered</option>
            <option value="unregistered">Informal / unregistered</option>
          </select>
        </label>
        <Button type="submit" disabled={!synthetic || history.length >= 20}>
          Preview synthetic revision
        </Button>
      </form>
      {history.map((snapshot, i) => (
        <article key={history.length - i}>
          <h2>Synthetic revision {history.length - i} · not submitted</h2>
          <p>
            <bdi>
              {snapshot.organization} · {snapshot.city}
            </bdi>
          </p>
          <p>
            {snapshot.classification} · {snapshot.examined}
          </p>
          <p>
            No server record, attestation approval, invitation or authority was
            created.
          </p>
        </article>
      ))}
      <h2>Independent officer review</h2>
      <p>
        No private queue or reviewer assignment is available. Different account
        IDs alone do not prove distinct individuals. No self-approval or
        alternative staff route.
      </p>
      {[
        "Submit record",
        "Approve record",
        "Return for correction",
        "Reject record",
        "Send recipient-bound invitation",
        "Accept nonfinance authority",
        "Activate NGO grant",
      ].map((label) => (
        <Button key={label} disabled>
          {label}
        </Button>
      ))}
      <p>
        Raw documents are not uploaded. Evidence custody and reference
        privacy/retention require separate contracts. Finance, signatory,
        governance, collaboration and exceptional private support remain
        separately gated.
      </p>
    </section>
  );
}
