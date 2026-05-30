export const WORKSPACE_PROJECT_NAVIGATION_UNAVAILABLE_REASON =
  "workspace_project_api_not_available";

export const WORKSPACE_PROJECT_NAVIGATION_LOCAL_ONLY_NOTICE =
  "local_manual_navigation_only";

export type WorkspaceNavigationItem = {
  id: string;
  organizationId: string;
  name: string;
};

export type ProjectNavigationItem = {
  id: string;
  workspaceId: string;
  key: string;
  name: string;
};

export type WorkspaceProjectNavigationState =
  | {
      status: "unavailable";
      reason: typeof WORKSPACE_PROJECT_NAVIGATION_UNAVAILABLE_REASON;
      selectedWorkspaceId: null;
      selectedProjectId: null;
      workspaces: [];
      projects: [];
    }
  | {
      status: "ready";
      selectedWorkspaceId: string | null;
      selectedProjectId: string | null;
      workspaces: WorkspaceNavigationItem[];
      projects: ProjectNavigationItem[];
    };

type WorkspaceNavigationListResponse = {
  items: WorkspaceNavigationItem[];
};

type ProjectNavigationListResponse = {
  items: ProjectNavigationItem[];
};

export function createEmptyWorkspaceProjectNavigation(): WorkspaceProjectNavigationState {
  return {
    status: "unavailable",
    reason: WORKSPACE_PROJECT_NAVIGATION_UNAVAILABLE_REASON,
    selectedWorkspaceId: null,
    selectedProjectId: null,
    workspaces: [],
    projects: [],
  };
}

export function createReadyWorkspaceProjectNavigation(
  workspaces: WorkspaceNavigationItem[]
): WorkspaceProjectNavigationState {
  return {
    status: "ready",
    selectedWorkspaceId: null,
    selectedProjectId: null,
    workspaces,
    projects: [],
  };
}

export function updateSelectedWorkspace(
  navigation: WorkspaceProjectNavigationState,
  workspaceId: string | null
): WorkspaceProjectNavigationState {
  return {
    status: "ready",
    selectedWorkspaceId: workspaceId,
    selectedProjectId: null,
    workspaces: navigation.workspaces,
    projects: [],
  };
}

export function updateWorkspaceProjects(
  navigation: WorkspaceProjectNavigationState,
  projects: ProjectNavigationItem[]
): WorkspaceProjectNavigationState {
  return {
    status: "ready",
    selectedWorkspaceId: navigation.selectedWorkspaceId,
    selectedProjectId: null,
    workspaces: navigation.workspaces,
    projects,
  };
}

export function updateSelectedProject(
  navigation: WorkspaceProjectNavigationState,
  projectId: string | null
): WorkspaceProjectNavigationState {
  return {
    status: "ready",
    selectedWorkspaceId: navigation.selectedWorkspaceId,
    selectedProjectId: projectId,
    workspaces: navigation.workspaces,
    projects: navigation.projects,
  };
}

export async function fetchWorkspaceNavigation(): Promise<WorkspaceNavigationItem[]> {
  const response = await fetch("/api/v1/projects/workspaces");

  if (!response.ok) {
    throw new Error("workspace_navigation_request_failed");
  }

  const data = (await response.json()) as WorkspaceNavigationListResponse;
  return data.items;
}

export async function fetchProjectNavigation(
  workspaceId: string
): Promise<ProjectNavigationItem[]> {
  const response = await fetch(`/api/v1/projects/workspaces/${workspaceId}/projects`);

  if (!response.ok) {
    throw new Error("project_navigation_request_failed");
  }

  const data = (await response.json()) as ProjectNavigationListResponse;
  return data.items;
}

export function getSelectedWorkspace(
  navigation: WorkspaceProjectNavigationState
): WorkspaceNavigationItem | null {
  if (navigation.selectedWorkspaceId === null) {
    return null;
  }

  return (
    navigation.workspaces.find(
      (workspace) => workspace.id === navigation.selectedWorkspaceId
    ) ?? null
  );
}

export function getSelectedProject(
  navigation: WorkspaceProjectNavigationState
): ProjectNavigationItem | null {
  if (navigation.selectedProjectId === null) {
    return null;
  }

  return (
    navigation.projects.find((project) => project.id === navigation.selectedProjectId) ??
    null
  );
}
