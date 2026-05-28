import { Link, useParams } from "react-router-dom";

import {
  type WorkspaceProjectNavigationState,
  getSelectedProject,
  getSelectedWorkspace,
} from "./navigation";

type WorkspaceProjectNavigationProps = {
  navigation: WorkspaceProjectNavigationState;
};

export function WorkspaceProjectNavigation({
  navigation,
}: WorkspaceProjectNavigationProps) {
  const selectedWorkspace = getSelectedWorkspace(navigation);
  const selectedProject = getSelectedProject(navigation);

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
      {navigation.workspaces.length > 0 ? (
        <nav aria-label="Workspace list">
          {navigation.workspaces.map((workspace) => (
            <Link key={workspace.id} to="/workspace">
              {workspace.name}
            </Link>
          ))}
        </nav>
      ) : null}
      {navigation.projects.length > 0 ? (
        <nav aria-label="Project list">
          {navigation.projects.map((project) => (
            <Link
              key={project.id}
              to={`/workspace/${project.workspaceId}/projects/${project.id}`}
            >
              {project.key} {project.name}
            </Link>
          ))}
        </nav>
      ) : null}
    </aside>
  );
}

export function WorkspaceHomePage({ navigation }: WorkspaceProjectNavigationProps) {
  return (
    <section aria-labelledby="workspace-heading">
      <p>Workspace</p>
      <h1 id="workspace-heading">Workspace home</h1>
      <WorkspaceProjectNavigation navigation={navigation} />
      <p>
        Recent projects, assigned work, sprint health, and activity will render
        here after backend workspace/project list APIs exist.
      </p>
    </section>
  );
}

export function ProjectShellPage({ navigation }: WorkspaceProjectNavigationProps) {
  const { projectId, workspaceId } = useParams();

  return (
    <section aria-labelledby="project-heading">
      <p>Project</p>
      <h1 id="project-heading">Project shell</h1>
      <WorkspaceProjectNavigation navigation={navigation} />
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
