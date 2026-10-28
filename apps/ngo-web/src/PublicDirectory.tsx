import { useEffect, useRef, useState } from "react";
import type {
  DirectoryGateway,
  DirectoryFilter,
  DirectoryPage,
} from "@pwc/web-api";
import { useLocale } from "@pwc/web-i18n";
import { Button, TextField, SelectField, Card, Badge } from "@pwc/web-ui";

export function Directory({ gateway }: { gateway: DirectoryGateway }) {
  const { locale } = useLocale();
  const t = (en: string, ur: string) => (locale === "ur" ? ur : en);
  const empty: DirectoryFilter = { q: "", city: "", classification: "" };
  const [filters, setFilters] = useState<DirectoryFilter>(empty);
  const [page, setPage] = useState<DirectoryPage | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const generation = useRef(0);
  const pending = useRef<AbortController | null>(null);
  const reset = () => {
    generation.current++;
    pending.current?.abort();
    pending.current = null;
    setPage(null);
    setBusy(false);
    setError(false);
  };
  useEffect(() => {
    reset();
    return () => {
      generation.current++;
      pending.current?.abort();
    };
  }, [gateway, locale]);
  async function load(cursor?: string) {
    pending.current?.abort();
    const ticket = ++generation.current;
    const controller = new AbortController();
    pending.current = controller;
    setPage(null);
    setError(false);
    setBusy(true);
    try {
      const next = await gateway.search(filters, cursor, controller.signal);
      if (ticket === generation.current && !controller.signal.aborted)
        setPage(next);
    } catch {
      if (ticket === generation.current && !controller.signal.aborted)
        setError(true);
    } finally {
      if (ticket === generation.current) setBusy(false);
    }
  }
  return (
    <section className="stack">
      <h1 tabIndex={-1}>
        {t(
          "NGO registry · public information",
          "تنظیموں کی فہرست · عوامی معلومات",
        )}
      </h1>
      <p>
        {t(
          "Read-only existing public projection. This is not verification consent, a membership list or administrator access. Self-service registration and claims remain unavailable.",
          "صرف موجودہ عوامی معلومات۔ یہ رکنیت، منتظم رسائی یا تصدیق کی منظوری نہیں۔ نئی رجسٹریشن دستیاب نہیں۔",
        )}
      </p>
      <form
        className="stack"
        onSubmit={(e) => {
          e.preventDefault();
          void load();
        }}
      >
        <TextField
          label={t("NGO name", "تنظیم کا نام")}
          hint={t("Search public names only", "صرف عوامی نام تلاش کریں")}
          value={filters.q}
          maxLength={250}
          onChange={(e) => {
            reset();
            setFilters({ ...filters, q: e.target.value });
          }}
        />
        <TextField
          label={t("City", "شہر")}
          hint={t("Optional city filter", "شہر کا اختیاری فلٹر")}
          value={filters.city}
          maxLength={250}
          onChange={(e) => {
            reset();
            setFilters({ ...filters, city: e.target.value });
          }}
        />
        <SelectField
          label={t("Classification", "درجہ بندی")}
          value={filters.classification}
          onChange={(e) => {
            reset();
            setFilters({
              ...filters,
              classification: e.target
                .value as DirectoryFilter["classification"],
            });
          }}
        >
          <option value="">{t("All classifications", "تمام اقسام")}</option>
          <option value="registered">{t("Registered", "رجسٹرڈ")}</option>
          <option value="unregistered">
            {t("Unregistered", "غیر رجسٹرڈ")}
          </option>
        </SelectField>
        <Button type="submit" disabled={busy}>
          {t("Search registry", "فہرست تلاش کریں")}
        </Button>
      </form>
      <p role="status">
        {busy
          ? t("Loading public information…", "عوامی معلومات لوڈ ہو رہی ہیں…")
          : error
            ? t(
                "Registry unavailable. Check connection or retry; no changes were made.",
                "فہرست دستیاب نہیں۔ دوبارہ کوشش کریں؛ کوئی تبدیلی نہیں ہوئی۔",
              )
            : page
              ? t(
                  `${page.results.length} results on this page`,
                  `اس صفحے پر ${page.results.length} نتائج`,
                )
              : t("Choose filters and search.", "فلٹر منتخب کر کے تلاش کریں۔")}
      </p>
      {page?.results.length === 0 && (
        <p>
          {t(
            "No public organizations match these filters.",
            "ان فلٹرز کے مطابق کوئی عوامی تنظیم نہیں۔",
          )}
        </p>
      )}
      {page?.results.map((row) => (
        <Card key={row.id} title={row.name}>
          <p>{row.city}</p>
          <Badge>
            {row.classification === "registered"
              ? t("Registered", "رجسٹرڈ")
              : t("Unregistered", "غیر رجسٹرڈ")}
          </Badge>
        </Card>
      ))}
      {page?.next_cursor && (
        <Button onClick={() => void load(page.next_cursor!)} disabled={busy}>
          {t("Next page", "اگلا صفحہ")}
        </Button>
      )}
    </section>
  );
}
