import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/api-contracts/generated/schema";
import { Button } from "@pwc/web-ui";
import { useLocale } from "@pwc/web-i18n";
type S = components["schemas"];
export type VerificationGateway = {
  list(cursor?: string): Promise<S["VerificationCasePage"]>;
  create(
    input: S["VerificationCaseInput"],
    key: string,
  ): Promise<S["VerificationCase"]>;
  change(
    id: string,
    command: "submit" | "withdraw",
    revision: number,
  ): Promise<S["VerificationCase"]>;
  requirements(id: string): Promise<S["VerificationRequirements"]>;
  history(id: string): Promise<S["VerificationHistoryPage"]>;
  preparation(id: string): Promise<S["EvidencePreparationPage"]>;
  prepare(
    id: string,
    input: S["EvidencePreparationInput"],
    key: string,
  ): Promise<S["EvidencePreparation"]>;
  replace(
    id: string,
    item: string,
    input: S["EvidencePreparationEdit"],
    withdraw: boolean,
  ): Promise<S["EvidencePreparation"]>;
};
// Synthetic DI only. No mounted gateway, upload input, reviewer mutation or transport.
export function Verification({
  gateway,
  source,
  scope = "unavailable",
  review = false,
}: {
  gateway?: VerificationGateway;
  source?: Omit<S["VerificationCaseInput"], "purpose">;
  scope?: string;
  review?: boolean;
}) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const [cases, setCases] = useState<S["VerificationCase"][]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const [detail, setDetail] = useState<{
    id: string;
    requirements: S["VerificationRequirements"];
    preparation: S["EvidencePreparation"][];
    history: S["VerificationHistory"][];
  } | null>(null);
  const generation = useRef(0);
  useEffect(() => {
    generation.current++;
    setCases([]);
    setCursor(null);
    setBusy(false);
    setError(false);
    setDetail(null);
    return () => {
      generation.current++;
    };
  }, [scope, gateway, locale, source, review]);
  async function run(work: () => Promise<void>) {
    if (!gateway || busy || review) return;
    const g = generation.current;
    setBusy(true);
    setError(false);
    try {
      await work();
    } catch {
      if (g === generation.current) setError(true);
    } finally {
      if (g === generation.current) setBusy(false);
    }
  }
  function guarded<T>(promise: Promise<T>, apply: (v: T) => void) {
    const g = generation.current;
    return promise.then((v) => {
      if (g === generation.current) apply(v);
    });
  }
  function update(v: S["VerificationCase"]) {
    setCases((old) => [v, ...old.filter((c) => c.id !== v.id)]);
    setDetail(null);
  }
  const disabled = !gateway || busy || review;
  return (
    <section className="stack" aria-busy={busy}>
      <p>
        Initial rollout: NGO and representative verification is external. Public
        NGO self-registration and existing-NGO claims are unavailable.
        Historical records confer no authority.
      </p>
      <h1 tabIndex={-1}>
        {review
          ? "PWC-01 · Verification review"
          : "ORG-03 · Verification preparation"}
      </h1>
      <p>
        {t(
          "Eligibility and representative mandate are separate. Submission records synthetic preparation only: not evidence acceptance, verification, authority or NGO access.",
          "اہلیت اور نمائندگی الگ ہیں۔ جمع کرنا صرف فرضی تیاری ہے، تصدیق یا تنظیم کا اختیار نہیں۔",
        )}
      </p>
      <p role="status" className="ds-banner tone-restricted">
        {t(
          "Files unavailable: no approved evidence classes, storage, scanning or retention contract. Reviewer IAM and adjudication unavailable. Browser networking remains blocked.",
          "فائل، جائزہ اور براؤزر نیٹ ورک غیر دستیاب ہیں۔",
        )}
      </p>
      {error && (
        <p role="alert" className="ds-banner tone-danger">
          {t(
            "Unavailable or conflicting. Reload current status; no automatic replay.",
            "غیر دستیاب یا متصادم؛ موجودہ حالت دوبارہ دیکھیں۔",
          )}
        </p>
      )}
      {!review && (
        <>
          <Button
            disabled={disabled}
            onClick={() =>
              void run(() =>
                guarded(gateway!.list(), (p) => {
                  setCases(p.results);
                  setCursor(p.next_cursor);
                  setDetail(null);
                }),
              )
            }
          >
            {t("Load own cases", "اپنے مقدمات دیکھیں")}
          </Button>
          {(
            ["organization_eligibility", "representative_mandate"] as const
          ).map((purpose) => (
            <Button
              key={purpose}
              disabled={disabled || !source}
              onClick={() =>
                void run(() =>
                  guarded(
                    gateway!.create(
                      { ...source!, purpose },
                      crypto.randomUUID(),
                    ),
                    update,
                  ),
                )
              }
            >
              {purpose}
            </Button>
          ))}
          {cases.map((c) => (
            <article key={c.id} className="stack">
              <h2>
                {c.purpose} · {c.track} · {c.state}
              </h2>
              <p>Revision {c.revision}</p>
              <Button
                disabled={disabled}
                onClick={() =>
                  void run(() =>
                    guarded(
                      Promise.all([
                        gateway!.requirements(c.id),
                        gateway!.preparation(c.id),
                        gateway!.history(c.id),
                      ]),
                      ([requirements, preparation, history]) =>
                        setDetail({
                          id: c.id,
                          requirements,
                          preparation: preparation.results,
                          history: history.results,
                        }),
                    ),
                  )
                }
              >
                {t("Requirements and history", "شرائط اور تاریخ")}
              </Button>
              <Button
                disabled={disabled || c.state !== "draft"}
                onClick={() =>
                  void run(() =>
                    guarded(
                      gateway!.prepare(
                        c.id,
                        { case_revision: c.revision, prepared_offline: false },
                        crypto.randomUUID(),
                      ),
                      () => {
                        setDetail(null);
                        setCases([]);
                      },
                    ),
                  )
                }
              >
                {t(
                  "Add non-file preparation marker",
                  "غیر فائل تیاری شامل کریں",
                )}
              </Button>
              <Button
                disabled={disabled || c.state !== "draft"}
                onClick={() =>
                  void run(() =>
                    guarded(
                      gateway!.change(c.id, "submit", c.revision),
                      update,
                    ),
                  )
                }
              >
                {t("Submit preparation only", "صرف تیاری جمع کریں")}
              </Button>
              <Button
                disabled={disabled || c.state === "withdrawn"}
                onClick={() =>
                  void run(() =>
                    guarded(
                      gateway!.change(c.id, "withdraw", c.revision),
                      update,
                    ),
                  )
                }
              >
                {t("Withdraw case", "مقدمہ واپس لیں")}
              </Button>
              {detail?.id === c.id && (
                <div>
                  <p>
                    {detail.requirements.rubric_status} ·{" "}
                    {detail.requirements.submission_effect}
                  </p>
                  {detail.preparation.map((m) => (
                    <div key={m.id}>
                      <p>
                        {m.state} · {String(m.prepared_offline)}
                      </p>
                      {[false, true].map((withdraw) => (
                        <Button
                          key={String(withdraw)}
                          disabled={
                            disabled ||
                            c.state !== "draft" ||
                            m.state !== "planned"
                          }
                          onClick={() =>
                            void run(() =>
                              guarded(
                                gateway!.replace(
                                  c.id,
                                  m.id,
                                  {
                                    case_revision: c.revision,
                                    revision: m.revision,
                                    prepared_offline: !m.prepared_offline,
                                  },
                                  withdraw,
                                ),
                                () => {
                                  setCases([]);
                                  setDetail(null);
                                },
                              ),
                            )
                          }
                        >
                          {withdraw ? "Withdraw marker" : "Replace marker"}
                        </Button>
                      ))}
                    </div>
                  ))}
                  <ul>
                    {detail.history.map((h) => (
                      <li key={h.id}>
                        {h.reason_code} · {h.revision}
                      </li>
                    ))}
                  </ul>
                  <p>
                    Bounded first page only; reload current cases before
                    changing preparation.
                  </p>
                </div>
              )}
            </article>
          ))}
          {cursor && (
            <Button
              disabled={disabled}
              onClick={() =>
                void run(() =>
                  guarded(gateway!.list(cursor), (p) => {
                    setCases((old) => [...old, ...p.results]);
                    setCursor(p.next_cursor);
                  }),
                )
              }
            >
              More cases
            </Button>
          )}
        </>
      )}
    </section>
  );
}
