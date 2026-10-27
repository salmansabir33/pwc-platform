import { useEffect, useId, useRef, useState } from "react";
import type {
  ReactNode,
  HTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
  InputHTMLAttributes,
} from "react";
import { Button } from "./button";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  return (
    <header className="page-heading">
      <h1 tabIndex={-1}>{title}</h1>
      <p className="lede">{description}</p>
      {actions && <div className="action-row">{actions}</div>}
    </header>
  );
}
export function Badge({
  children,
  tone = "info",
}: {
  children: ReactNode;
  tone?: "info" | "success" | "warning" | "danger" | "restricted";
}) {
  return <span className={`ds-badge tone-${tone}`}>{children}</span>;
}
export function Banner({
  title,
  children,
  tone = "info",
  urgent = false,
}: {
  title: string;
  children: ReactNode;
  tone?: "info" | "success" | "warning" | "danger" | "restricted";
  urgent?: boolean;
}) {
  return (
    <section
      className={`ds-banner tone-${tone}`}
      {...(urgent ? { role: "alert" } : {})}
    >
      <h2>{title}</h2>
      <div>{children}</div>
    </section>
  );
}
export function Card({
  title,
  children,
  ...props
}: HTMLAttributes<HTMLElement> & { title: string }) {
  return (
    <section {...props} className={`panel ${props.className ?? ""}`}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
export function SelectField({
  label,
  hint,
  error,
  id: provided,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const generated = useId();
  const id = provided ?? generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={
          `${hint ? id + "-hint " : ""}${error ? id + "-error" : ""}`.trim() ||
          undefined
        }
      />
      {hint && (
        <p className="hint" id={id + "-hint"}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field-error" role="alert" id={id + "-error"}>
          {error}
        </p>
      )}
    </div>
  );
}
export function TextArea({
  label,
  hint,
  error,
  id: provided,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const generated = useId();
  const id = provided ?? generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <textarea
        {...props}
        id={id}
        aria-invalid={!!error}
        aria-describedby={
          `${hint ? id + "-hint " : ""}${error ? id + "-error" : ""}`.trim() ||
          undefined
        }
      />
      {hint && (
        <p className="hint" id={id + "-hint"}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field-error" role="alert" id={id + "-error"}>
          {error}
        </p>
      )}
    </div>
  );
}
export function Choice({
  label,
  type = "checkbox",
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: string;
  type?: "checkbox" | "radio";
}) {
  const generated = useId();
  const id = props.id ?? generated;
  return (
    <label className="choice" htmlFor={id}>
      <input {...props} id={id} type={type} />
      <span>{label}</span>
    </label>
  );
}
export function DataTable({
  caption,
  headers,
  rows,
  empty,
}: {
  caption: string;
  headers: string[];
  rows: ReactNode[][];
  empty: string;
}) {
  return (
    <div
      className="table-scroll"
      role="region"
      aria-label={caption}
      tabIndex={0}
    >
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {headers.map((h, i) => (
              <th key={i} scope="col">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j}>{cell}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={headers.length}>{empty}</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
export function Pagination({
  label,
  previousLabel,
  nextLabel,
  onPrevious,
  onNext,
  busy = false,
}: {
  label: string;
  previousLabel: string;
  nextLabel: string;
  onPrevious?: () => void;
  onNext?: () => void;
  busy?: boolean;
}) {
  return (
    <nav className="action-row" aria-label={label}>
      <Button
        variant="secondary"
        disabled={busy || !onPrevious}
        onClick={onPrevious}
      >
        {previousLabel}
      </Button>
      <Button variant="secondary" disabled={busy || !onNext} onClick={onNext}>
        {nextLabel}
      </Button>
    </nav>
  );
}
export function Skeleton({ label }: { label: string }) {
  return (
    <div role="status" aria-label={label} className="skeleton">
      <span className="sr-only">{label}</span>
    </div>
  );
}
// Native dialog supplies modal focus containment/inert backdrop. Never executes a
// business command, owns proof state, or treats dismissal as acknowledgement.
export function ConfirmDialog({
  open,
  title,
  children,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onClose,
  busy = false,
}: {
  open: boolean;
  title: string;
  children: ReactNode;
  confirmLabel: string;
  cancelLabel: string;
  onConfirm: () => void;
  onClose: () => void;
  busy?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  const closeHandler = useRef(onClose);
  closeHandler.current = onClose;
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    const opener = document.activeElement as HTMLElement | null;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
    return () => {
      if (d.open) d.close();
      if (open && opener?.isConnected) opener.focus();
    };
  }, [open]);
  useEffect(() => {
    if (open && busy) ref.current?.focus();
  }, [open, busy]);
  return (
    <dialog
      ref={ref}
      aria-labelledby={id}
      tabIndex={-1}
      onKeyDown={(e) => {
        if (e.key !== "Tab") return;
        const nodes = Array.from(
          e.currentTarget.querySelectorAll<HTMLElement>(
            'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        ).filter((el) => el.getClientRects().length > 0);
        const first = nodes[0];
        const last = nodes[nodes.length - 1];
        if (!first || !last) {
          e.preventDefault();
          e.currentTarget.focus();
          return;
        }
        if (
          e.shiftKey &&
          (document.activeElement === first ||
            document.activeElement === e.currentTarget)
        ) {
          e.preventDefault();
          last.focus();
        }
        if (
          !e.shiftKey &&
          (document.activeElement === last ||
            document.activeElement === e.currentTarget)
        ) {
          e.preventDefault();
          first.focus();
        }
      }}
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) closeHandler.current();
      }}
    >
      <h2 id={id}>{title}</h2>
      <div>{children}</div>
      <div className="action-row">
        <Button variant="secondary" autoFocus disabled={busy} onClick={onClose}>
          {cancelLabel}
        </Button>
        <Button variant="destructive" busy={busy} onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </dialog>
  );
}

/** Rendered only on the existing, explicitly UI-only foundation specimen route. */
export function DesignSystemSpecimen({ urdu = false }: { urdu?: boolean }) {
  const [open, setOpen] = useState(false);
  const [result, setResult] = useState(false);
  const t = (en: string, ur: string) => (urdu ? ur : en);
  useEffect(() => {
    setOpen(false);
    setResult(false);
  }, [urdu]);
  return (
    <section
      className="stack"
      aria-label={t("Design system examples", "ڈیزائن کی مثالیں")}
      key={String(urdu)}
    >
      <Card
        title={t(
          "Design system v1.0 · UI examples only",
          "ڈیزائن سسٹم · صرف انٹرفیس کی مثالیں",
        )}
      >
        <p>
          {t(
            "These controls do not create records, send requests or grant authority.",
            "یہ مثالیں ریکارڈ، درخواست یا اختیار نہیں بناتیں۔",
          )}
        </p>
        <div className="action-row">
          <Button onClick={() => setOpen(true)}>
            {t("Preview confirmation", "تصدیق کی مثال")}
          </Button>
          <Button variant="secondary">
            {t("Secondary example", "ثانوی مثال")}
          </Button>
          <Button variant="tertiary">
            {t("Tertiary example", "تیسری مثال")}
          </Button>
          <Button variant="destructive" disabled>
            {t("Destructive unavailable", "حذف دستیاب نہیں")}
          </Button>
          <Button busy>{t("Loading example", "انتظار کی مثال")}</Button>
        </div>
        <p aria-live="polite">
          {result
            ? t(
                "Local confirmation dismissed; no command ran.",
                "مقامی مثال بند ہوئی؛ کوئی کارروائی نہیں ہوئی۔",
              )
            : ""}
        </p>
        <ConfirmDialog
          open={open}
          title={t("UI-only confirmation", "صرف انٹرفیس کی تصدیق")}
          confirmLabel={t("Confirm example", "مثال کی تصدیق")}
          cancelLabel={t("Cancel", "منسوخ")}
          onClose={() => setOpen(false)}
          onConfirm={() => {
            setOpen(false);
            setResult(true);
          }}
        >
          <p>
            {t(
              "This is a presentation example, not a business action.",
              "یہ صرف انٹرفیس کی مثال ہے، کاروباری کارروائی نہیں۔",
            )}
          </p>
        </ConfirmDialog>
      </Card>
      <Card title={t("Labeled controls", "نام والے خانے")}>
        <TextArea
          label={t("Example notes", "مثالی نوٹس")}
          hint={t(
            "Synthetic text only; no private evidence.",
            "صرف فرضی متن؛ کوئی نجی ثبوت نہیں۔",
          )}
          rows={3}
        />
        <SelectField
          label={t("Example selection", "مثالی انتخاب")}
          defaultValue="one"
        >
          <option value="one">{t("First example", "پہلی مثال")}</option>
          <option value="two">{t("Second example", "دوسری مثال")}</option>
        </SelectField>
        <fieldset>
          <legend>{t("Example choices", "مثالی انتخاب")}</legend>
          <Choice label={t("Optional example", "اختیاری مثال")} />
          <Choice
            type="radio"
            name="specimen-choice"
            label={t("Option one", "پہلا اختیار")}
            value="one"
          />
          <Choice
            type="radio"
            name="specimen-choice"
            label={t("Option two", "دوسرا اختیار")}
            value="two"
          />
        </fieldset>
      </Card>
      <Banner tone="restricted" title={t("Restricted example", "محدود مثال")}>
        {t(
          "A status label never grants permission.",
          "حالت کا نام اختیار نہیں دیتا۔",
        )}
      </Banner>
      <div className="action-row">
        {(["success", "warning", "danger", "info", "restricted"] as const).map(
          (tone, i) => (
            <Badge key={tone} tone={tone}>
              {urdu
                ? ["کامیابی", "انتباہ", "خرابی", "معلومات", "محدود"][i]
                : tone}
            </Badge>
          ),
        )}
      </div>
      <DataTable
        caption={t(
          "Technical token examples (not organizational records)",
          "تکنیکی ٹوکن کی مثالیں، تنظیمی ریکارڈ نہیں",
        )}
        headers={[t("Token", "ٹوکن"), t("Value", "قیمت")]}
        rows={[
          [
            <bdi key="id" dir="ltr">
              text.primary
            </bdi>,
            <bdi key="hex" dir="ltr">
              #192F37
            </bdi>,
          ],
        ]}
        empty={t("No examples", "کوئی مثال نہیں")}
      />
      <Pagination
        label={t("Example pages", "مثالی صفحات")}
        previousLabel={t("Previous", "پچھلا")}
        nextLabel={t("Next", "اگلا")}
      />
    </section>
  );
}
