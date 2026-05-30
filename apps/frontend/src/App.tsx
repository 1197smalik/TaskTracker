import { useEffect, useState } from "react";
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
import {
  createReadyWorkspaceProjectNavigation,
  fetchProjectNavigation,
  fetchWorkspaceNavigation,
  updateSelectedProject,
  updateSelectedWorkspace,
  updateWorkspaceProjects,
} from "./projects/navigation";
import { AppShell } from "./routes/AppShell";
import {
  WorkItemBoardPage,
  WorkItemDetailPage,
  WorkItemListPage,
} from "./work-items";

export function App() {
  const [session] = useState<AuthSession>(() => createAnonymousSession());
  const [projectNavigation, setProjectNavigation] =
    useState<WorkspaceProjectNavigationState>(() =>
    createEmptyWorkspaceProjectNavigation()
  );

  useEffect(() => {
    let cancelled = false;

    void fetchWorkspaceNavigation()
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
  }, []);

  useEffect(() => {
    if (
      projectNavigation.status !== "ready" ||
      projectNavigation.selectedWorkspaceId === null
    ) {
      return;
    }

    let cancelled = false;

    void fetchProjectNavigation(projectNavigation.selectedWorkspaceId)
      .then((projects) => {
        if (cancelled) {
          return;
        }

        setProjectNavigation((currentNavigation) =>
          updateWorkspaceProjects(currentNavigation, projects)
        );
      })
      .catch(() => {
        if (!cancelled) {
          setProjectNavigation((currentNavigation) =>
            updateWorkspaceProjects(currentNavigation, [])
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectNavigation.status, projectNavigation.selectedWorkspaceId]);

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

  return (
    <Routes>
      <Route
        element={
          <AppShell
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
          element={<WorkItemBoardPage />}
        />
        <Route
          path="/workspace/:workspaceId/projects/:projectId/work-items/:workItemId"
          element={<WorkItemDetailPage />}
        />
      </Route>
    </Routes>
  );
}
