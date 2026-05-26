import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import {
  type AuthSession,
  createAnonymousSession,
} from "./identity/session";
import { AppShell } from "./routes/AppShell";

export function App() {
  const [session] = useState<AuthSession>(() => createAnonymousSession());

  return (
    <Routes>
      <Route element={<AppShell session={session} />}>
        <Route index element={<Navigate replace to="/workspace" />} />
        <Route
          path="/login"
          element={
            <section aria-labelledby="login-heading">
              <p>Identity</p>
              <h1 id="login-heading">Sign in to TaskMaster</h1>
              <p>
                Authentication endpoints are defined, but credential
                verification is not implemented yet.
              </p>
            </section>
          }
        />
        <Route
          path="/workspace"
          element={
            <section aria-labelledby="workspace-heading">
              <p>Workspace</p>
              <h1 id="workspace-heading">Workspace shell</h1>
              <p>
                Project navigation will attach here after backend workspace
                contracts are available.
              </p>
            </section>
          }
        />
      </Route>
    </Routes>
  );
}
