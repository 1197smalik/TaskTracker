import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import {
  type AuthSession,
  createAnonymousSession,
} from "./identity/session";
import {
  ProjectShellPage,
  WorkspaceHomePage,
  createEmptyWorkspaceProjectNavigation,
  type WorkspaceProjectNavigationState,
} from "./projects";
import { AppShell } from "./routes/AppShell";

export function App() {
  const [session] = useState<AuthSession>(() => createAnonymousSession());
  const [projectNavigation] = useState<WorkspaceProjectNavigationState>(() =>
    createEmptyWorkspaceProjectNavigation()
  );

  return (
    <Routes>
      <Route
        element={
          <AppShell session={session} projectNavigation={projectNavigation} />
        }
      >
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
          element={<WorkspaceHomePage navigation={projectNavigation} />}
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId"
          element={<ProjectShellPage navigation={projectNavigation} />}
        />
      </Route>
    </Routes>
  );
}
