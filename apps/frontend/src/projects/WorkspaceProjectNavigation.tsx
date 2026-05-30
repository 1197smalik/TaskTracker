import { ChangeEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  WORKSPACE_PROJECT_NAVIGATION_LOCAL_ONLY_NOTICE,
  type WorkspaceProjectNavigationState,
  getSelectedProject,
  getSelectedWorkspace,
} from "./navigation";

type WorkspaceProjectNavigationProps = {
  navigation: WorkspaceProjectNavigationState;
  onProjectSelect: (projectId: string | null) => void;
  onWorkspaceSelect: (workspaceId: string | null) => void;
};

export function WorkspaceProjectNavigation({
  navigation,
  onProjectSelect,
  onWorkspaceSelect,
}: WorkspaceProjectNavigationProps) {
  const navigate = useNavigate();
  const selectedWorkspace = getSelectedWorkspace(navigation);
  const selectedProject = getSelectedProject(navigation);

  const handleWorkspaceChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const workspaceId = event.target.value || null;
    onWorkspaceSelect(workspaceId);
    navigate("/workspace");
  };

  const handleProjectChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const projectId = event.target.value || null;
    onProjectSelect(projectId);

    if (projectId !== null && selectedWorkspace !== null) {
      navigate(`/workspace/${selectedWorkspace.id}/projects/${projectId}`);
    }
  };

  return (
    <aside aria-label="Workspace and project navigation">
      <p>Workspace context</p>
      <h2>{selectedWorkspace?.name ?? "No workspace selected"}</h2>
      <p>Project context: {selectedProject?.name ?? "No project selected"}</p>
      {navigation.status === "unavailable" ? (
        <p>
          Workspace and project lists are waiting for backend list contracts.
          No frontend authorization or membership lookup is inferred.
        </p>
      ) : null}
      {navigation.status === "ready" ? (
        <>
          <p>
            Lists are {WORKSPACE_PROJECT_NAVIGATION_LOCAL_ONLY_NOTICE.replaceAll("_", " ")}.
            No membership lookup or authorization inference is applied.
          </p>
          <label>
            Workspace selector
            <select
              aria-label="Workspace selector"
              onChange={handleWorkspaceChange}
              value={navigation.selectedWorkspaceId ?? ""}
            >
              <option value="">Select a workspace</option>
              {navigation.workspaces.map((workspace) => (
                <option key={workspace.id} value={workspace.id}>
                  {workspace.name}
                </option>
              ))}
            </select>
          </label>
          {navigation.workspaces.length === 0 ? (
            <p>No workspaces are available for local manual navigation.</p>
          ) : null}
          <label>
            Project selector
            <select
              aria-label="Project selector"
              disabled={navigation.selectedWorkspaceId === null}
              onChange={handleProjectChange}
              value={navigation.selectedProjectId ?? ""}
            >
              <option value="">Select a project</option>
              {navigation.projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.key} {project.name}
                </option>
              ))}
            </select>
          </label>
          {navigation.selectedWorkspaceId === null ? (
            <p>Select a workspace before choosing a project.</p>
          ) : null}
          {navigation.selectedWorkspaceId !== null && navigation.projects.length === 0 ? (
            <p>No projects are available for the selected workspace.</p>
          ) : null}
        </>
      ) : null}
    </aside>
  );
}

export function WorkspaceHomePage({
  navigation,
  onProjectSelect,
  onWorkspaceSelect,
}: WorkspaceProjectNavigationProps) {
  return (
    <section aria-labelledby="workspace-heading">
      <p>Workspace</p>
      <h1 id="workspace-heading">Workspace home</h1>
      <WorkspaceProjectNavigation
        navigation={navigation}
        onProjectSelect={onProjectSelect}
        onWorkspaceSelect={onWorkspaceSelect}
      />
      <p>
        Recent projects, assigned work, sprint health, and activity will render
        here after backend workspace/project list APIs exist.
      </p>
    </section>
  );
}

export function ProjectShellPage({
  navigation,
  onProjectSelect,
  onWorkspaceSelect,
}: WorkspaceProjectNavigationProps) {
  const { projectId, workspaceId } = useParams();

  return (
    <section aria-labelledby="project-heading">
      <p>Project</p>
      <h1 id="project-heading">Project shell</h1>
      <WorkspaceProjectNavigation
        navigation={navigation}
        onProjectSelect={onProjectSelect}
        onWorkspaceSelect={onWorkspaceSelect}
      />
      <p>
        Route context: workspace {workspaceId ?? "unselected"}, project{" "}
        {projectId ?? "unselected"}.
      </p>
      {workspaceId !== undefined && projectId !== undefined ? (
        <nav aria-label="Project views">
          <Link to={`/workspace/${workspaceId}/projects/${projectId}/work-items`}>
            View work items
          </Link>
          <Link to={`/workspace/${workspaceId}/projects/${projectId}/board`}>
            View board
          </Link>
        </nav>
      ) : null}
      <p>
        Board, backlog, sprint, epic, milestone, and settings pages are not
        implemented in this navigation shell.
      </p>
    </section>
  );
}
