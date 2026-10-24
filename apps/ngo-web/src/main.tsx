import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { LocaleProvider } from "@pwc/web-i18n";
import { AppBoundary } from "@pwc/web-ui";
import { App } from "./App";
import "@pwc/design-tokens";
import "@pwc/web-ui/styles.css";
createRoot(document.getElementById("root")!, {
  onCaughtError: () => {
    /* No raw exception telemetry. */
  },
}).render(
  <StrictMode>
    <AppBoundary>
      <LocaleProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </LocaleProvider>
    </AppBoundary>
  </StrictMode>,
);
