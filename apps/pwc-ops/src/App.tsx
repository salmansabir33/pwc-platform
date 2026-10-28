import { OperationsStatus } from "./OperationsStatus";
import { Directory } from "../../ngo-web/src/PublicDirectory";
import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import {
  createFoundationRuntime,
  connectInvalidationChannel,
  PublicDirectoryClient,
} from "@pwc/web-api";
import {
  PortalShell,
  Overview,
  AccessibilitySpecimen,
  StateSpecimens,
  NotFound,
} from "@pwc/web-ui";
import { Verification } from "../../ngo-web/src/Verification";
import { ControlledOnboarding } from "./ControlledOnboarding";
import { config } from "./config";

export function App() {
  const [directory] = useState(
    () => new PublicDirectoryClient((url, init) => fetch(url, init)),
  );
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
              <Link to="/operations-status">Controlled rollout status</Link>
              <Link to="/ngo-registry">NGO registry · public read-only</Link>
              <Link to="/controlled-onboarding">
                PWC-01 · Controlled onboarding (unavailable)
              </Link>
            </>
          }
        />
        <Route
          path="/foundation/accessibility"
          element={<AccessibilitySpecimen />}
        />
        <Route path="/foundation/states" element={<StateSpecimens />} />
        <Route
          path="/controlled-onboarding"
          element={<ControlledOnboarding />}
        />
        <Route path="/operations-status" element={<OperationsStatus />} />
        <Route path="/verification" element={<Verification review />} />
        <Route
          path="/ngo-registry"
          element={<Directory gateway={directory} />}
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </PortalShell>
  );
}
