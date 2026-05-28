export type WorkItemListParams = {
  limit: number;
  offset: number;
};

export type WorkItemResponse = {
  id: string;
  project_id: string;
  parent_id: string | null;
  sprint_id: string | null;
  epic_id: string | null;
  assignee_id: string | null;
  reporter_id: string | null;
  current_state_id: string | null;
  type: string;
  status: string;
  title: string;
  description: string | null;
  priority: string | null;
  severity: string | null;
  estimate: number | null;
  typed_metadata: Record<string, unknown>;
  version: number;
  created_at: string;
  updated_at: string;
};

export type WorkItemListResponse = {
  items: WorkItemResponse[];
  total: number;
  limit: number;
  offset: number;
};

export function buildProjectWorkItemListUrl(
  projectId: string,
  params: WorkItemListParams
): string {
  const query = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });

  return `/api/v1/projects/${encodeURIComponent(projectId)}/work-items?${query}`;
}

export function buildProjectWorkItemDetailUrl(
  projectId: string,
  workItemId: string
): string {
  return `/api/v1/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}`;
}

export function buildProjectWorkItemDetailPath(
  workspaceId: string,
  projectId: string,
  workItemId: string
): string {
  return `/workspace/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}`;
}
