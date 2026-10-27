import type { ButtonHTMLAttributes } from "react";

export function Button({
  type = "button",
  variant = "primary",
  busy = false,
  disabled,
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "tertiary" | "destructive";
  busy?: boolean;
}) {
  return (
    <button
      {...props}
      type={type}
      disabled={disabled || busy}
      aria-busy={busy || undefined}
      className={`button button-${variant} ${className}`}
    >
      {busy && <span aria-hidden="true">… </span>}
      {children}
    </button>
  );
}
