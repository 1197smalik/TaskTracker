import { useEffect, useRef, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { createAuthenticatedApiClient } from "./identity/apiClient";
import {
  type AuthSession,
  createCheckingSession,
  createAnonymousSession,
  clearStoredRefreshToken,
  getRefreshDelay,
  isAuthenticatedSession,
  login,
  logout,
  readStoredRefreshToken,
  refreshSession,
} from "./identity/session";
import { LoginPage } from "./identity/LoginPage";
import { OrganizationCreatePage } from "./organizations";
import {
  ProjectCreatePage,
  ProjectShellPage,
  WorkspaceHomePage,
  createEmptyWorkspaceProjectNavigation,
  type WorkspaceProjectNavigationState,
} from "./projects";
import {
  clearSelectedWorkspace,
  createReadyWorkspaceProjectNavigation,
  fetchProjectNavigation,
  fetchWorkspaceNavigation,
  updateSelectedProject,
  updateSelectedWorkspace,
  updateWorkspaceProjects,
} from "./projects/navigation";
import { AppShell } from "./routes/AppShell";
import { WorkspaceCreatePage } from "./workspaces";
import {
  WorkItemBoardPage,
  WorkItemDetailPage,
  WorkItemListPage,
} from "./work-items";

export function App() {
  const restoreAttemptedRef = useRef(false);
  const sessionRef = useRef<AuthSession>(createCheckingSession());
  const apiClientRef = useRef<ReturnType<typeof createAuthenticatedApiClient> | null>(
    null
  );
  const [authNotice, setAuthNotice] = useState<string | null>(null);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [session, setSession] = useState<AuthSession>(() => createCheckingSession());
  const [projectNavigation, setProjectNavigation] =
    useState<WorkspaceProjectNavigationState>(() =>
    createEmptyWorkspaceProjectNavigation()
  );
  sessionRef.current = session;

  if (apiClientRef.current === null) {
    apiClientRef.current = createAuthenticatedApiClient({
      getSession: () => sessionRef.current,
      onSessionInvalidated: (error) => {
        clearStoredRefreshToken();
        setAuthNotice(resolveAuthNotice(error));
        setSession(createAnonymousSession());
      },
      onSessionRenewed: (nextSession) => {
        setAuthNotice(null);
        setSession(nextSession);
      },
    });
  }

  const apiClient = apiClientRef.current;

  useEffect(() => {
    if (restoreAttemptedRef.current) {
      return;
    }
    restoreAttemptedRef.current = true;

    let cancelled = false;
    const storedRefreshToken = readStoredRefreshToken();

    if (storedRefreshToken === null) {
      setSession(createAnonymousSession());
      return;
    }

    void refreshSession(storedRefreshToken)
      .then((nextSession) => {
        if (!cancelled) {
          setAuthNotice(null);
          setSession(nextSession);
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          clearStoredRefreshToken();
          setAuthNotice(resolveAuthNotice(error));
          setSession(createAnonymousSession());
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    void fetchWorkspaceNavigation(apiClient)
      .then((workspaces) => {
        if (cancelled) {
          return;
        }

        setProjectNavigation(createReadyWorkspaceProjectNavigation(workspaces));
      })
      .catch(() => {
        if (!cancelled) {
          setProjectNavigation(createEmptyWorkspaceProjectNavigation());
        }
      });

    return () => {
      cancelled = true;
    };
  }, [apiClient]);

  useEffect(() => {
    if (
      projectNavigation.status !== "ready" ||
      projectNavigation.selectedWorkspaceId === null
    ) {
      return;
    }

    let cancelled = false;

    void fetchProjectNavigation(apiClient, projectNavigation.selectedWorkspaceId)
      .then((projects) => {
        if (cancelled) {
          return;
        }

        setProjectNavigation((currentNavigation) =>
          updateWorkspaceProjects(currentNavigation, projects)
        );
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setProjectNavigation((currentNavigation) => {
            if (
              error instanceof Error &&
              (error.message === "project_navigation_request_failed:403" ||
                error.message === "project_navigation_request_failed:404")
            ) {
              return clearSelectedWorkspace(currentNavigation);
            }

            return updateWorkspaceProjects(currentNavigation, []);
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [apiClient, projectNavigation.status, projectNavigation.selectedWorkspaceId]);

  useEffect(() => {
    const refreshDelay = getRefreshDelay(session);
    if (refreshDelay === null) {
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(() => {
      void refreshSession()
        .then((nextSession) => {
          if (!cancelled) {
            setAuthNotice(null);
            setSession(nextSession);
          }
        })
        .catch((error: unknown) => {
          if (!cancelled) {
            clearStoredRefreshToken();
            setAuthNotice(resolveAuthNotice(error));
            setSession(createAnonymousSession());
          }
        });
    }, refreshDelay);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [session]);

  const handleWorkspaceSelect = (workspaceId: string | null) => {
    setProjectNavigation((currentNavigation) =>
      updateSelectedWorkspace(currentNavigation, workspaceId)
    );
  };

  const handleProjectSelect = (projectId: string | null) => {
    setProjectNavigation((currentNavigation) =>
      updateSelectedProject(currentNavigation, projectId)
    );
  };

  const handleWorkspaceCreated = async (workspace: {
    id: string;
    organizationId: string;
    name: string;
  }) => {
    try {
      const workspaces = await fetchWorkspaceNavigation(apiClient);
      setProjectNavigation({
        status: "ready",
        selectedWorkspaceId: workspace.id,
        selectedProjectId: null,
        workspaces,
        projects: [],
      });
    } catch {
      setProjectNavigation((currentNavigation) => ({
        status: "ready",
        selectedWorkspaceId: workspace.id,
        selectedProjectId: null,
        workspaces:
          currentNavigation.status === "ready"
            ? [
                ...currentNavigation.workspaces.filter(
                  (currentWorkspace) => currentWorkspace.id !== workspace.id
                ),
                workspace,
              ].sort((left, right) => left.name.localeCompare(right.name))
            : [workspace],
        projects: [],
      }));
    }
  };

  const handleProjectCreated = async (project: {
    id: string;
    workspaceId: string;
    key: string;
    name: string;
  }) => {
    try {
      const projects = await fetchProjectNavigation(apiClient, project.workspaceId);
      setProjectNavigation((currentNavigation) => ({
        status: "ready",
        selectedWorkspaceId: project.workspaceId,
        selectedProjectId: project.id,
        workspaces:
          currentNavigation.status === "ready" ? currentNavigation.workspaces : [],
        projects,
      }));
    } catch {
      setProjectNavigation((currentNavigation) => ({
        status: "ready",
        selectedWorkspaceId: project.workspaceId,
        selectedProjectId: project.id,
        workspaces:
          currentNavigation.status === "ready" ? currentNavigation.workspaces : [],
        projects:
          currentNavigation.status === "ready" &&
          currentNavigation.selectedWorkspaceId === project.workspaceId
            ? [
                ...currentNavigation.projects.filter(
                  (currentProject) => currentProject.id !== project.id
                ),
                project,
              ].sort((left, right) => left.key.localeCompare(right.key))
            : [project],
      }));
    }
  };

  const handleLogin = async (email: string, password: string) => {
    setIsLoggingIn(true);
    try {
      const nextSession = await login(email, password);
      setAuthNotice(null);
      setSession(nextSession);
    } finally {
      setIsLoggingIn(false);
    }
  };

  const handleLogout = () => {
    setIsLoggingOut(true);
    void logout()
      .catch((error: unknown) => {
        setAuthNotice(resolveAuthNotice(error));
      })
      .finally(() => {
        setSession(createAnonymousSession());
        setIsLoggingOut(false);
      });
  };

  return (
    <Routes>
      <Route
        element={
          <AppShell
            authNotice={authNotice}
            logoutPending={isLoggingOut}
            onLogout={handleLogout}
            onProjectSelect={handleProjectSelect}
            onWorkspaceSelect={handleWorkspaceSelect}
            projectNavigation={projectNavigation}
            session={session}
          />
        }
      >
        <Route index element={<Navigate replace to="/workspace" />} />
        <Route
          path="/login"
          element={
            <LoginPage
              authNotice={authNotice}
              isSubmitting={isLoggingIn}
              onLogin={handleLogin}
              session={session}
            />
          }
        />
        <Route
          path="/organizations/new"
          element={
            <OrganizationCreatePage
              apiClient={apiClient}
              isAuthenticated={isAuthenticatedSession(session)}
            />
          }
        />
        <Route
          path="/organizations/:organizationId/workspaces/new"
          element={
            <WorkspaceCreatePage
              apiClient={apiClient}
              isAuthenticated={isAuthenticatedSession(session)}
              onWorkspaceCreated={handleWorkspaceCreated}
            />
          }
        />
        <Route
          path="/workspaces/:workspaceId/projects/new"
          element={
            <ProjectCreatePage
              apiClient={apiClient}
              isAuthenticated={isAuthenticatedSession(session)}
              onProjectCreated={handleProjectCreated}
            />
          }
        />
        <Route
          path="/workspace"
          element={
            <WorkspaceHomePage
              navigation={projectNavigation}
              onProjectSelect={handleProjectSelect}
              onWorkspaceSelect={handleWorkspaceSelect}
            />
          }
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId"
          element={
            <ProjectShellPage
              navigation={projectNavigation}
              onProjectSelect={handleProjectSelect}
              onWorkspaceSelect={handleWorkspaceSelect}
            />
          }
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId/work-items"
          element={<WorkItemListPage />}
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId/board"
          element={<WorkItemBoardPage apiClient={apiClient} />}
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId/work-items/:workItemId"
          element={<WorkItemDetailPage apiClient={apiClient} />}
        />
      </Route>
    </Routes>
  );
}

function resolveAuthNotice(error: unknown): string {
  if (!(error instanceof Error) || !("code" in error)) {
    return "Authentication failed. Try again.";
  }

  switch (error.code) {
    case "expired_session":
      return "Your session expired. Sign in again.";
    case "invalid_session":
      return "Your session is invalid. Sign in again.";
    case "revoked_session":
      return "Your session was revoked. Sign in again.";
    case "network_error":
      return "TaskMaster could not reach the authentication service.";
    default:
      return "Authentication failed. Try again.";
  }
}
