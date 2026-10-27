import { useEffect, useId, useRef } from "react";
import type {
  ReactNode,
  HTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
  InputHTMLAttributes,
} from "react";
import { Button } from "./index";

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
  return (
    <dialog
      ref={ref}
      aria-labelledby={id}
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
