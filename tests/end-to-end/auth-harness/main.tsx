// NONSHIPPED synthetic test entry. Never imported by either application build.
import { createRoot } from "react-dom/client";
import { LocaleProvider, useLocale } from "@pwc/web-i18n";
import {
  PersonalWorkspaceSession,
  OperationsPolicyClient,
  PublicDirectoryClient,
} from "@pwc/web-api";
import { PersonalWorkspace } from "../../../apps/ngo-web/src/PersonalWorkspace";
import { OperationsWorkspace } from "../../../apps/pwc-ops/src/OperationsWorkspace";
import { OperationsStatus } from "../../../apps/pwc-ops/src/OperationsStatus";
import { Directory } from "../../../apps/ngo-web/src/PublicDirectory";
import "../../../packages/design-tokens/tokens.css";
import "@pwc/web-ui/styles.css";
let lose = false;
let csrfFault = false;
const transport: typeof fetch = async (path, init) => {
  if (csrfFault && init?.method === "POST") {
    csrfFault = false;
    const headers = new Headers(init.headers);
    headers.set("X-CSRFToken", "x".repeat(64));
    init = { ...init, headers };
  }
  const response = await fetch(path, init);
  if (lose && String(path).endsWith("/withdraw/") && response.ok) {
    lose = false;
    // Actual Django commit happened. Discard response, not mock server success.
    throw new TypeError(
      "Synthetic response discarded after actual server response",
    );
  }
  return response;
};
const session = new PersonalWorkspaceSession(
  location.hostname.startsWith("ops.") ? "ops" : "ngo",
  transport,
);
const policy = new OperationsPolicyClient(session.state, transport);
const directory = new PublicDirectoryClient(transport);
function Harness() {
  const { locale, setLocale } = useLocale();
  return (
    <main>
      <p>SYNTHETIC TEST ONLY · not W2 acceptance</p>
      <button onClick={() => setLocale(locale === "en" ? "ur" : "en")}>
        Toggle locale
      </button>
      <button
        onClick={() => {
          lose = true;
        }}
      >
        Discard next withdrawal response (test only)
      </button>
      <button
        onClick={() => {
          csrfFault = true;
        }}
      >
        Corrupt next CSRF (test only)
      </button>
      {location.hostname.startsWith("ops.") ? (
        <OperationsWorkspace session={session} policy={policy} />
      ) : (
        <>
          <PersonalWorkspace session={session} />
          <OperationsStatus gateway={policy} />
        </>
      )}
      <Directory gateway={directory} />
    </main>
  );
}
createRoot(document.getElementById("root")!).render(
  <LocaleProvider>
    <Harness />
  </LocaleProvider>,
);
