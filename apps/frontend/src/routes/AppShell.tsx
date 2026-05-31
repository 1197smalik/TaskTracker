import { Link, Outlet, useLocation } from "react-router-dom";

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
  authNotice: string | null;
  logoutPending: boolean;
  onLogout: () => void;
  onProjectSelect: (projectId: string | null) => void;
  onWorkspaceSelect: (workspaceId: string | null) => void;
  session: AuthSession;
  projectNavigation: WorkspaceProjectNavigationState;
};

export function AppShell({
  authNotice,
  logoutPending,
  onLogout,
  onProjectSelect,
  onWorkspaceSelect,
  projectNavigation,
  session,
}: AppShellProps) {
  const location = useLocation();
  const sessionLabel = describeSessionStatus(session);
  const shouldShowAuthNotice =
    authNotice !== null &&
    (isAuthenticatedSession(session) || location.pathname !== "/login");

  return (
    <div>
      <header>
        <Link to="/workspace">TaskMaster</Link>
        <nav aria-label="Primary navigation">
          <Link to="/workspace">Workspace</Link>
          {isAuthenticatedSession(session) ? (
            <Link to="/organizations/new">Create organization</Link>
          ) : null}
          {!isAuthenticatedSession(session) ? <Link to="/login">Sign in</Link> : null}
        </nav>
        <section aria-label="Authentication session">
          <p>{sessionLabel}</p>
          <p>
            Access tokens are {AUTH_SESSION_STORAGE_POLICY.accessToken}; refresh
            tokens are {AUTH_SESSION_STORAGE_POLICY.refreshToken}.
          </p>
          {shouldShowAuthNotice ? (
            <p role="status">{authNotice}</p>
          ) : null}
          {isAuthenticatedSession(session) ? (
            <button disabled={logoutPending} onClick={onLogout} type="button">
              {logoutPending ? "Signing out..." : "Sign out"}
            </button>
          ) : null}
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
