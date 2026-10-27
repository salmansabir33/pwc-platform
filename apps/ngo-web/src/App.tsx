import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import {
  createFoundationRuntime,
  connectInvalidationChannel,
} from "@pwc/web-api";
import {
  PortalShell,
  Overview,
  AccessibilitySpecimen,
  StateSpecimens,
  NotFound,
} from "@pwc/web-ui";
import { Verification } from "./Verification";
import { Registry } from "./Registry";
import { config } from "./config";

export function App() {
  // Factory per mounted application, never a shared session/cache singleton.
  const [runtime] = useState(() => createFoundationRuntime(config.appId));
  useEffect(() => {
    const disconnect = connectInvalidationChannel(runtime.state);
    const hide = () => {
      if (document.hidden) runtime.state.invalidate("visibility");
    };
    document.addEventListener("visibilitychange", hide);
    return () => {
      disconnect();
      document.removeEventListener("visibilitychange", hide);
      runtime.state.invalidate("unmount");
    };
  }, [runtime]);
  return (
    <PortalShell portal={config.appId}>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <Overview portal={config.appId} />
              <Link to="/verification">
                ORG-03 · Verification (unavailable)
              </Link>
              <Link to="/registry">
                ORG-01 / ORG-02 · Registry review (not connected)
              </Link>
            </>
          }
        />
        <Route
          path="/foundation/accessibility"
          element={<AccessibilitySpecimen />}
        />
        <Route path="/foundation/states" element={<StateSpecimens />} />
        <Route path="/verification" element={<Verification />} />
        <Route path="/registry" element={<Registry />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </PortalShell>
  );
}
