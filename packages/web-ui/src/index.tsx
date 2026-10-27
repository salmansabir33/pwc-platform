import { Component, useEffect, useId, useRef, useState } from "react";
import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
} from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useLocale } from "@pwc/web-i18n";
import { DesignSystemSpecimen } from "./components";

export {
  PageHeader,
  Badge,
  Banner,
  Card,
  SelectField,
  TextArea,
  Choice,
  DataTable,
  Pagination,
  Skeleton,
  ConfirmDialog,
} from "./components";

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
export function TextField({
  label,
  hint,
  error,
  id: providedId,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint: string;
  error?: string;
}) {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        {...props}
        id={id}
        aria-describedby={`${id}-hint${error ? ` ${id}-error` : ""}`}
        aria-invalid={!!error}
      />
      <p className="hint" id={`${id}-hint`}>
        {hint}
      </p>
      {error && (
        <p className="field-error" id={`${id}-error`} role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
export function Stack({ children }: { children: ReactNode }) {
  return <div className="stack">{children}</div>;
}
export function Panel({ children }: { children: ReactNode }) {
  return <section className="panel">{children}</section>;
}
export function StatePanel({
  title,
  children,
  kind,
}: {
  title: string;
  children: ReactNode;
  kind: "loading" | "empty" | "error" | "restricted" | "unavailable";
}) {
  return (
    <section className={`state-panel state-${kind}`}>
      <span className="state-mark" aria-hidden="true">
        {kind === "error" ? "!" : kind === "empty" ? "—" : "…"}
      </span>
      <div>
        <h2>{title}</h2>
        <p>{children}</p>
      </div>
    </section>
  );
}
export class AppBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <main className="fatal">
        <h1>Interface unavailable</h1>
        <p>
          The application could not render safely. No technical details or
          private data are displayed.
        </p>
        <a href="/">Return to foundation</a>
      </main>
    ) : (
      this.props.children
    );
  }
}

export function PortalShell({
  portal,
  children,
}: {
  portal: "ngo" | "ops";
  children: ReactNode;
}) {
  const { t, locale, direction, setLocale } = useLocale();
  const [menu, setMenu] = useState(false);
  const location = useLocation();
  const previousPath = useRef(location.pathname);
  const title = t(portal === "ngo" ? "ngoTitle" : "opsTitle");
  useEffect(() => {
    document.title = `${title} · ${t(location.pathname === "/" ? "overview" : location.pathname === "/foundation/accessibility" ? "accessibility" : location.pathname === "/foundation/states" ? "states" : "notFound")}`;
    if (previousPath.current !== location.pathname) {
      document.querySelector<HTMLElement>("main h1")?.focus();
      previousPath.current = location.pathname;
    }
    setMenu(false);
  }, [location.pathname, title, t]);
  return (
    <div className={`portal portal-${portal}`} dir={direction}>
      <a className="skip-link" href="#main">
        {t("skip")}
      </a>
      <aside className="sidebar">
        <Link
          className="brand"
          to="/"
          aria-label={`${title} — ${t("overview")}`}
        >
          <span className="brand-mark" aria-hidden="true">
            P
          </span>
          <span>
            <strong>PWC</strong>
            <small>{title}</small>
          </span>
        </Link>
        <Button
          aria-expanded={menu}
          aria-controls="foundation-nav"
          onClick={() => setMenu((v) => !v)}
        >
          {menu ? t("closeMenu") : t("menu")}
        </Button>
        <nav
          id="foundation-nav"
          aria-label={t("navigation")}
          className={menu ? "nav open" : "nav"}
        >
          <span className="nav-label">{t("foundation")}</span>
          <NavLink to="/" end>
            <span aria-hidden="true">01</span>
            {t("overview")}
          </NavLink>
          <NavLink to="/foundation/accessibility">
            <span aria-hidden="true">02</span>
            {t("accessibility")}
          </NavLink>
          <NavLink to="/foundation/states">
            <span aria-hidden="true">03</span>
            {t("states")}
          </NavLink>
        </nav>
        <div className="sidebar-note">
          <span className="small-label">{t("environment")}</span>
          <p>{t("disconnected")}</p>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className="environment">
            <span aria-hidden="true" />
            {t("environment")}
          </span>
          <div className="workspace-context">
            <span id="workspace-context-label">{t("contextTitle")}</span>
            <Button
              id="workspace-context"
              disabled
              aria-describedby="workspace-context-label"
            >
              {t("disconnected")}
            </Button>
          </div>
          <div className="language">
            <label htmlFor="display-language">{t("language")}</label>
            <select
              id="display-language"
              value={locale}
              onChange={(e) => setLocale(e.target.value === "ur" ? "ur" : "en")}
            >
              <option value="en" lang="en">
                English
              </option>
              <option value="ur" lang="ur">
                اردو · نمونہ
              </option>
            </select>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          <nav
            className="breadcrumbs"
            aria-label={direction === "rtl" ? "مقام" : "Breadcrumb"}
          >
            <Link to="/">{title}</Link>
            <span aria-hidden="true"> / </span>
            <span>{t("foundation")}</span>
          </nav>
          {children}
        </main>
        <footer>
          <span>{t("footer")}</span>
          <span>{t("target")}</span>
        </footer>
      </div>
    </div>
  );
}

export function Overview({ portal }: { portal: "ngo" | "ops" }) {
  const { t } = useLocale();
  const references = [
    ["ID-01", t("id01"), "W2"],
    ["ID-02", t("id02"), "W2 · subset"],
    ["ID-03", t("id03"), "W3"],
    ["ID-04", t("id04"), "W3"],
    ["ID-05", t("id05"), "W2 · subset"],
    [
      portal === "ngo" ? "ORG-04" : "OPS-01",
      t(portal === "ngo" ? "org04" : "ops01"),
      t("later"),
    ],
  ];
  return (
    <Stack>
      <div className="page-heading">
        <p className="eyebrow">{t("eyebrow")} / W1</p>
        <h1 tabIndex={-1}>{t(portal === "ngo" ? "heading" : "opsHeading")}</h1>
        <p className="lede">{t(portal === "ngo" ? "intro" : "opsIntro")}</p>
      </div>
      <div className="status-grid">
        {(["shell", "auth", "context"] as const).map((item, index) => (
          <section className="status-card" key={item}>
            <div className="card-top">
              <span className="card-number" aria-hidden="true">
                0{index + 1}
              </span>
              <span className={index === 0 ? "badge ready" : "badge"}>
                {t(index === 0 ? "available" : "gated")}
              </span>
            </div>
            <h2>
              {t(
                item === "shell"
                  ? "shellTitle"
                  : item === "auth"
                    ? "authTitle"
                    : "contextTitle",
              )}
            </h2>
            <p>
              {t(
                item === "shell"
                  ? "shellBody"
                  : item === "auth"
                    ? "authBody"
                    : "contextBody",
              )}
            </p>
          </section>
        ))}
      </div>
      <section className="boundary-note">
        <span aria-hidden="true" className="boundary-symbol">
          ↳
        </span>
        <div>
          <h2>{t("boundaryTitle")}</h2>
          <p>{t("boundaryBody")}</p>
        </div>
      </section>
      <div className="detail-grid">
        <Panel>
          <p className="eyebrow">W1 / {t("foundation")}</p>
          <h2>{t("nextTitle")}</h2>
          <p>{t("nextBody")}</p>
          <Link className="text-link" to="/foundation/accessibility">
            {t("accessibility")} <span aria-hidden="true">↗</span>
          </Link>
        </Panel>
        <Panel>
          <h2>{t("screensTitle")}</h2>
          <p>{t("screensBody")}</p>
          <div
            className="table-scroll"
            role="region"
            aria-label={t("screensTitle")}
            tabIndex={0}
          >
            <table>
              <caption className="sr-only">{t("screensTitle")}</caption>
              <thead>
                <tr>
                  <th scope="col">{t("screen")}</th>
                  <th scope="col">{t("meaning")}</th>
                  <th scope="col">{t("readiness")}</th>
                </tr>
              </thead>
              <tbody>
                {references.map(([id, label, gate]) => (
                  <tr key={id}>
                    <th scope="row">
                      <bdi>{id}</bdi>
                    </th>
                    <td>{label}</td>
                    <td>
                      <bdi>{gate}</bdi>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </Stack>
  );
}
export function AccessibilitySpecimen() {
  const { t, locale } = useLocale();
  const [value, setValue] = useState("");
  const [invalid, setInvalid] = useState(false);
  const [complete, setComplete] = useState(false);
  useEffect(() => {
    setValue("");
    setInvalid(false);
    setComplete(false);
  }, [locale]);
  return (
    <Stack>
      <div className="page-heading">
        <p className="eyebrow">W1 / UI</p>
        <h1 tabIndex={-1}>{t("specimenTitle")}</h1>
        <p className="lede">{t("specimenIntro")}</p>
      </div>
      <div className="detail-grid">
        <Panel>
          <h2>{t("sampleTitle")}</h2>
          <form
            noValidate
            onSubmit={(e) => {
              e.preventDefault();
              setInvalid(!value.trim());
              setComplete(!!value.trim());
            }}
          >
            <TextField
              label={t("sampleLabel")}
              hint={t("sampleHint")}
              value={value}
              maxLength={80}
              autoComplete="off"
              onChange={(e) => {
                setValue(e.target.value);
                setInvalid(false);
                setComplete(false);
              }}
              {...(invalid ? { error: t("sampleError") } : {})}
            />
            <Button type="submit">{t("sampleAction")}</Button>
            <p role="status" className="success-message">
              {complete ? t("sampleResult") : ""}
            </p>
          </form>
        </Panel>
        <Panel>
          <h2>{t("directionTitle")}</h2>
          <p>{t("directionBody")}</p>
          <p>
            {t("mixed")}: <bdi dir="ltr">PWC-W1 / example@pwc.invalid</bdi>
          </p>
          <p className="hint">{t("focusNote")}</p>
        </Panel>
      </div>
      <DesignSystemSpecimen urdu={locale === "ur"} />
    </Stack>
  );
}
export function StateSpecimens() {
  const { t } = useLocale();
  return (
    <Stack>
      <div className="page-heading">
        <p className="eyebrow">W1 / UI</p>
        <h1 tabIndex={-1}>{t("statesTitle")}</h1>
        <p className="lede">{t("statesIntro")}</p>
      </div>
      <StatePanel kind="loading" title={t("loadingTitle")}>
        {t("loadingBody")}
      </StatePanel>
      <StatePanel kind="empty" title={t("emptyTitle")}>
        {t("emptyBody")}
      </StatePanel>
      <StatePanel kind="error" title={t("errorTitle")}>
        {t("errorBody")}
      </StatePanel>
    </Stack>
  );
}
export function NotFound() {
  const { t } = useLocale();
  return (
    <div className="page-heading">
      <p className="eyebrow">404 / W1</p>
      <h1 tabIndex={-1}>{t("notFound")}</h1>
      <p className="lede">{t("notFoundBody")}</p>
      <Link className="text-link" to="/">
        {t("back")}
      </Link>
    </div>
  );
}
