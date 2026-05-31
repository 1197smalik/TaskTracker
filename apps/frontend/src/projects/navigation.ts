import {
  type AuthenticatedApiClient,
  ApiClientResponseError,
} from "../identity/apiClient";

export const WORKSPACE_PROJECT_NAVIGATION_UNAVAILABLE_REASON =
  "workspace_project_api_not_available";

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

export function clearSelectedWorkspace(
  navigation: WorkspaceProjectNavigationState
): WorkspaceProjectNavigationState {
  return {
    status: "ready",
    selectedWorkspaceId: null,
    selectedProjectId: null,
    workspaces: navigation.workspaces,
    projects: [],
  };
}

export async function fetchWorkspaceNavigation(
  apiClient: AuthenticatedApiClient
): Promise<WorkspaceNavigationItem[]> {
  try {
    const data = await apiClient.getJson<WorkspaceNavigationListResponse>(
      "/api/v1/projects/workspaces"
    );
    return data.items;
  } catch (error) {
    if (error instanceof ApiClientResponseError) {
      throw new Error(`workspace_navigation_request_failed:${error.statusCode}`);
    }
    throw error;
  }
}

export async function fetchProjectNavigation(
  apiClient: AuthenticatedApiClient,
  workspaceId: string
): Promise<ProjectNavigationItem[]> {
  try {
    const data = await apiClient.getJson<ProjectNavigationListResponse>(
      `/api/v1/projects/workspaces/${workspaceId}/projects`
    );
    return data.items;
  } catch (error) {
    if (error instanceof ApiClientResponseError) {
      throw new Error(`project_navigation_request_failed:${error.statusCode}`);
    }
    throw error;
  }
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
