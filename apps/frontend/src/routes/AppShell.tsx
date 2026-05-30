import { Link, Outlet } from "react-router-dom";

import {
  AUTH_SESSION_STORAGE_POLICY,
  type AuthSession,
  describeSessionStatus,
  isAuthenticatedSession,
} from "../identity/session";
import {
  WorkspaceProjectNavigation,
  type WorkspaceProjectNavigationState,
} from "../projects";

type AppShellProps = {
  onProjectSelect: (projectId: string | null) => void;
  onWorkspaceSelect: (workspaceId: string | null) => void;
  session: AuthSession;
  projectNavigation: WorkspaceProjectNavigationState;
};

export function AppShell({
  onProjectSelect,
  onWorkspaceSelect,
  projectNavigation,
  session,
}: AppShellProps) {
  const sessionLabel = describeSessionStatus(session);

  return (
    <div>
      <header>
        <Link to="/workspace">TaskMaster</Link>
        <nav aria-label="Primary navigation">
          <Link to="/workspace">Workspace</Link>
          {!isAuthenticatedSession(session) ? <Link to="/login">Sign in</Link> : null}
        </nav>
        <section aria-label="Authentication session">
          <p>{sessionLabel}</p>
          <p>
            Access tokens are {AUTH_SESSION_STORAGE_POLICY.accessToken}; refresh
            tokens are {AUTH_SESSION_STORAGE_POLICY.refreshToken}.
          </p>
        </section>
      </header>
      <WorkspaceProjectNavigation
        navigation={projectNavigation}
        onProjectSelect={onProjectSelect}
        onWorkspaceSelect={onWorkspaceSelect}
      />
      <main>
        <Outlet />
      </main>
    </div>
  );
}
