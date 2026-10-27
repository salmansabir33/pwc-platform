import { useEffect, useRef, useState } from "react";
import type { components } from "../../../packages/api-contracts/generated/schema";
import { useLocale } from "@pwc/web-i18n";
import { Button, TextField } from "@pwc/web-ui";

type S = components["schemas"];
export type RegistryGateway = {
  search(
    q: string,
    city: string,
    cursor?: string,
  ): Promise<S["RegistrySearchPage"]>;
  history(kind: "draft" | "claim", id: string): Promise<S["RegistryEventPage"]>;
  edit(id: string, input: S["RegistryDraftEdit"]): Promise<S["RegistryDraft"]>;
  drafts(cursor?: string): Promise<S["RegistryDraftPage"]>;
  claims(cursor?: string): Promise<S["RegistryClaimPage"]>;
  create(
    input: S["RegistryDraftInput"],
    retryKey: string,
  ): Promise<S["RegistryDraft"]>;
  claim(id: string, retryKey: string): Promise<S["RegistryClaim"]>;
  change(
    id: string,
    command: "submit" | "withdraw",
    revision: number,
  ): Promise<S["RegistryDraft"]>;
  withdrawClaim(id: string, revision: number): Promise<S["RegistryClaim"]>;
};

// Dependency injection is for contract-tested components only. The mounted W1
// application NEVER supplies a gateway, adds fetch, credentials or live auth.
export function Registry({
  gateway,
  scope = "unavailable",
}: {
  gateway?: RegistryGateway;
  scope?: string;
}) {
  const { locale } = useLocale();
  const ur = locale === "ur";
  const t = (en: string, urdu: string) => (ur ? urdu : en);
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [name, setName] = useState("");
  const [editing, setEditing] = useState<S["RegistryDraft"] | null>(null);
  const [legal, setLegal] = useState("");
  const [aliases, setAliases] = useState("");
  const [jurisdiction, setJurisdiction] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [classification, setClassification] = useState<
    "registered" | "unregistered"
  >("unregistered");
  const [hits, setHits] = useState<S["PublicOrganization"][]>([]);
  const [draftCursor, setDraftCursor] = useState<string | null>(null);
  const [claimCursor, setClaimCursor] = useState<string | null>(null);
  const [history, setHistory] = useState<S["RegistryEvent"][]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<S["RegistryDraft"][]>([]);
  const [claims, setClaims] = useState<S["RegistryClaim"][]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const generation = useRef(0);
  useEffect(() => {
    generation.current++;
    setDraftCursor(null);
    setClaimCursor(null);
    setHistory([]);
    setEditing(null);
    setLegal("");
    setAliases("");
    setJurisdiction("");
    setEmail("");
    setPhone("");
    setQ("");
    setCity("");
    setName("");
    setHits([]);
    setDrafts([]);
    setClaims([]);
    setCursor(null);
    setMessage("");
    setBusy(false);
    return () => {
      generation.current++;
    };
  }, [scope, gateway, locale]);
  async function run(work: () => Promise<void>) {
    if (!gateway || busy) return;
    const current = generation.current;
    setBusy(true);
    setMessage("");
    try {
      await work();
    } catch {
      if (current === generation.current)
        setMessage(
          t(
            "Request unavailable or conflicting. Reload your status before retrying; no automatic replay.",
            "درخواست دستیاب نہیں یا متصادم ہے۔ دوبارہ کوشش سے پہلے حالت دیکھیں۔",
          ),
        );
    } finally {
      if (current === generation.current) setBusy(false);
    }
  }
  // Guard every resolved value against logout/scope/language/unmount races.
  function guarded<T>(promise: Promise<T>, apply: (value: T) => void) {
    const current = generation.current;
    return promise.then((value) => {
      if (current === generation.current) apply(value);
    });
  }
  const unavailable = !gateway || busy;
  return (
    <section className="stack" aria-busy={busy}>
      <p>
        Initial rollout: NGO and representative verification is external. Public
        NGO self-registration and existing-NGO claims are unavailable.
        Historical records confer no authority.
      </p>
      <h1 tabIndex={-1}>
        {t("ORG-01 · Find or claim an NGO", "ORG-01 · تنظیم تلاش کریں")}
      </h1>
      <p>
        {t(
          "A claim is a request, not ownership, verification or NGO access. Use synthetic data only in this review foundation.",
          "درخواست ملکیت، تصدیق یا تنظیم تک رسائی نہیں۔ صرف فرضی معلومات استعمال کریں۔",
        )}
      </p>
      {!gateway && (
        <p role="status">
          {t(
            "Unavailable: browser networking and live authentication remain blocked. Components are contract-tested, not connected.",
            "غیر دستیاب: براؤزر نیٹ ورک اور براہ راست شناخت بند ہیں۔",
          )}
        </p>
      )}
      {message && <p role="alert">{message}</p>}
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void run(() =>
            guarded(gateway!.search(q, city), (page) => {
              setHits(page.results);
              setCursor(page.next_cursor);
            }),
          );
        }}
      >
        <TextField
          label={t("Organization search", "تنظیم کی تلاش")}
          hint={t(
            "Public names only; matching does not establish authority.",
            "صرف عوامی نام؛ مماثلت اختیار ثابت نہیں کرتی۔",
          )}
          value={q}
          maxLength={250}
          minLength={2}
          required
          disabled={unavailable}
          onChange={(e) => {
            setQ(e.target.value);
            setHits([]);
            setCursor(null);
          }}
        />
        <TextField
          label={t("City", "شہر")}
          hint={t("Optional location filter", "اختیاری مقام")}
          value={city}
          maxLength={100}
          disabled={unavailable}
          onChange={(e) => {
            setCity(e.target.value);
            setHits([]);
            setCursor(null);
          }}
        />
        <Button type="submit" disabled={unavailable}>
          {t("Search", "تلاش")}
        </Button>
      </form>
      {hits.length > 0 && (
        <p>
          {t(
            "Potential duplicates only. No automatic merge or control transfer.",
            "ممکنہ مماثلت؛ خودکار انضمام یا اختیار کی منتقلی نہیں۔",
          )}
        </p>
      )}
      <ul>
        {hits.map((hit) => (
          <li key={hit.id}>
            <bdi>
              {hit.name} · {hit.city}
            </bdi>{" "}
            <Button
              disabled={unavailable}
              onClick={() => {
                void run(() =>
                  guarded(
                    gateway!.claim(hit.id, crypto.randomUUID()),
                    (value) =>
                      setClaims((old) => [
                        ...old.filter((c) => c.id !== value.id),
                        value,
                      ]),
                  ),
                );
              }}
            >
              {t("Request claim", "درخواست جمع کریں")}
            </Button>
          </li>
        ))}
      </ul>
      {cursor && (
        <Button
          disabled={unavailable}
          onClick={() => {
            void run(() =>
              guarded(gateway!.search(q, city, cursor), (page) => {
                setHits((old) => [...old, ...page.results]);
                setCursor(page.next_cursor);
              }),
            );
          }}
        >
          {t("More results", "مزید نتائج")}
        </Button>
      )}
      <h2>
        {t(
          "ORG-02 · Provisional organization draft",
          "ORG-02 · عارضی تنظیم کا مسودہ",
        )}
      </h2>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void run(() =>
            guarded(
              editing
                ? gateway!.edit(editing.id, {
                    name,
                    city,
                    classification,
                    legal_name: legal,
                    aliases: aliases
                      .split(",")
                      .map((v) => v.trim())
                      .filter(Boolean),
                    jurisdiction,
                    contact_email: email,
                    contact_phone: phone,
                    revision: editing.revision,
                  })
                : gateway!.create(
                    {
                      name,
                      city,
                      classification,
                      legal_name: legal,
                      aliases: aliases
                        .split(",")
                        .map((v) => v.trim())
                        .filter(Boolean),
                      jurisdiction,
                      contact_email: email,
                      contact_phone: phone,
                    },
                    crypto.randomUUID(),
                  ),
              (value) => {
                setDrafts((old) => [
                  ...old.filter((d) => d.id !== value.id),
                  value,
                ]);
                setName("");
                setEditing(null);
              },
            ),
          );
        }}
      >
        <TextField
          label={t("Display name", "نام")}
          hint={t(
            "Search first. This does not reserve ownership of an existing NGO.",
            "پہلے تلاش کریں؛ موجودہ تنظیم کی ملکیت حاصل نہیں ہوتی۔",
          )}
          value={name}
          maxLength={250}
          required
          disabled={unavailable}
          onChange={(e) => setName(e.target.value)}
        />
        {(
          [
            ["Legal name", "قانونی نام", legal, setLegal, 250],
            [
              "Aliases (comma separated, at most five)",
              "متبادل نام",
              aliases,
              setAliases,
              1254,
            ],
            [
              "Jurisdiction (self-declared)",
              "دائرہ اختیار",
              jurisdiction,
              setJurisdiction,
              100,
            ],
            [
              "Organization contact email",
              "تنظیم کا ای میل",
              email,
              setEmail,
              254,
            ],
            ["Organization contact phone", "تنظیم کا فون", phone, setPhone, 40],
          ] as const
        ).map(([label, urdu, value, update, max]) => (
          <TextField
            key={label}
            label={t(label, urdu)}
            hint={t(
              "Private draft metadata, not authority or evidence.",
              "نجی مسودہ، اختیار یا ثبوت نہیں۔",
            )}
            value={value}
            maxLength={max}
            disabled={unavailable}
            onChange={(e) => update(e.target.value)}
          />
        ))}
        <label>
          {t("Category", "قسم")}{" "}
          <select
            value={classification}
            disabled={unavailable}
            onChange={(e) =>
              setClassification(e.target.value as typeof classification)
            }
          >
            <option value="unregistered">
              {t("Informal welfare organization", "غیر رجسٹرڈ فلاحی تنظیم")}
            </option>
            <option value="registered">
              {t("Registered (self-declared)", "رجسٹرڈ (ذاتی دعویٰ)")}
            </option>
          </select>
        </label>
        <Button type="submit" disabled={unavailable}>
          {t("Save private draft", "نجی مسودہ محفوظ کریں")}
        </Button>
      </form>
      <Button
        disabled={unavailable}
        onClick={() => {
          void run(async () => {
            await guarded(gateway!.drafts(), (page) => {
              setDrafts(page.results);
              setDraftCursor(page.next_cursor);
            });
            await guarded(gateway!.claims(), (page) => {
              setClaims(page.results);
              setClaimCursor(page.next_cursor);
            });
          });
        }}
      >
        {t("Reload own status", "اپنی حالت دیکھیں")}
      </Button>
      <h2>{t("Own applications", "اپنی درخواستیں")}</h2>
      <ul>
        {drafts.map((draft) => (
          <li key={draft.id}>
            <bdi>
              {draft.name} · {draft.state} · v{draft.revision}
            </bdi>
            <Button
              disabled={unavailable}
              onClick={() => {
                void run(() =>
                  guarded(gateway!.history("draft", draft.id), (page) =>
                    setHistory(page.results),
                  ),
                );
              }}
            >
              {t("Draft history", "مسودے کی تاریخ")}
            </Button>
            {draft.state === "draft" && (
              <Button
                disabled={unavailable}
                onClick={() => {
                  setEditing(draft);
                  setName(draft.name);
                  setCity(draft.city);
                  setClassification(draft.classification);
                  setLegal(draft.legal_name);
                  setAliases(draft.aliases.join(", "));
                  setJurisdiction(draft.jurisdiction);
                  setEmail(draft.contact_email);
                  setPhone(draft.contact_phone);
                }}
              >
                {t("Edit own draft", "اپنا مسودہ بدلیں")}
              </Button>
            )}
            {draft.state === "draft" && (
              <Button
                disabled={unavailable}
                onClick={() => {
                  void run(() =>
                    guarded(
                      gateway!.change(draft.id, "submit", draft.revision),
                      (value) =>
                        setDrafts((old) =>
                          old.map((d) => (d.id === value.id ? value : d)),
                        ),
                    ),
                  );
                }}
              >
                {t(
                  "Submit for future review",
                  "مستقبل کے جائزے کے لیے جمع کریں",
                )}
              </Button>
            )}
            {draft.state !== "withdrawn" && (
              <Button
                disabled={unavailable}
                onClick={() => {
                  void run(() =>
                    guarded(
                      gateway!.change(draft.id, "withdraw", draft.revision),
                      (value) =>
                        setDrafts((old) =>
                          old.map((d) => (d.id === value.id ? value : d)),
                        ),
                    ),
                  );
                }}
              >
                {t("Withdraw draft", "مسودہ واپس لیں")}
              </Button>
            )}
          </li>
        ))}
      </ul>
      <ul>
        {claims.map((claim) => (
          <li key={claim.id}>
            <Button
              disabled={unavailable}
              onClick={() => {
                void run(() =>
                  guarded(gateway!.history("claim", claim.id), (page) =>
                    setHistory(page.results),
                  ),
                );
              }}
            >
              {t("Claim history", "درخواست کی تاریخ")}
            </Button>
            <bdi>
              {claim.id} · {claim.state}
            </bdi>
            {["pending", "needs_information"].includes(claim.state) && (
              <Button
                disabled={unavailable}
                onClick={() => {
                  void run(() =>
                    guarded(
                      gateway!.withdrawClaim(claim.id, claim.revision),
                      (value) =>
                        setClaims((old) =>
                          old.map((c) => (c.id === value.id ? value : c)),
                        ),
                    ),
                  );
                }}
              >
                {t("Withdraw claim", "درخواست واپس لیں")}
              </Button>
            )}
          </li>
        ))}
      </ul>
      {draftCursor && (
        <Button
          disabled={unavailable}
          onClick={() => {
            void run(() =>
              guarded(gateway!.drafts(draftCursor), (page) => {
                setDrafts((old) => [...old, ...page.results]);
                setDraftCursor(page.next_cursor);
              }),
            );
          }}
        >
          {t("More own drafts", "مزید مسودے")}
        </Button>
      )}
      {claimCursor && (
        <Button
          disabled={unavailable}
          onClick={() => {
            void run(() =>
              guarded(gateway!.claims(claimCursor), (page) => {
                setClaims((old) => [...old, ...page.results]);
                setClaimCursor(page.next_cursor);
              }),
            );
          }}
        >
          {t("More own claims", "مزید درخواستیں")}
        </Button>
      )}
      <ul>
        {history.map((event) => (
          <li key={event.id}>
            {event.action} · v{event.revision}
          </li>
        ))}
      </ul>
      <p>
        {t(
          "Evidence upload, reviewer decisions, verification, administrators, rosters and finance are unavailable.",
          "ثبوت، جائزہ، تصدیق، انتظامیہ، فہرستیں اور مالیات دستیاب نہیں۔",
        )}
      </p>
    </section>
  );
}
