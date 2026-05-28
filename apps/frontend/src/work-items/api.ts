export type WorkItemListParams = {
  limit: number;
  offset: number;
};

export type WorkflowTransitionRequest = {
  expected_version: number;
  target_state_id: string;
  source_state_id?: string | null;
};

export type WorkItemApiErrorResponse = {
  error_code: string;
  message: string;
  details: Record<string, string>;
  correlation_id: string;
  field_errors: Record<string, string[]>;
  retry_after: number | null;
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

export type WorkflowTransitionResponse = {
  work_item: WorkItemResponse;
  transition_id: string;
  source_state_id: string;
  target_state_id: string;
};

export type WorkItemTransitionResult =
  | {
      status: "succeeded";
      response: WorkflowTransitionResponse;
    }
  | {
      status: "failed";
      statusCode: number;
      error: WorkItemApiErrorResponse | null;
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

export function buildProjectWorkItemTransitionUrl(
  projectId: string,
  workItemId: string
): string {
  return `/api/v1/projects/${encodeURIComponent(projectId)}/work-items/${encodeURIComponent(workItemId)}/transition`;
}

export async function transitionProjectWorkItem(
  projectId: string,
  workItemId: string,
  request: WorkflowTransitionRequest
): Promise<WorkItemTransitionResult> {
  const response = await fetch(buildProjectWorkItemTransitionUrl(projectId, workItemId), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (response.ok) {
    const payload = (await response.json()) as WorkflowTransitionResponse;
    return {
      status: "succeeded",
      response: payload,
    };
  }

  const error = await parseWorkItemTransitionError(response);
  return {
    status: "failed",
    statusCode: response.status,
    error,
  };
}

async function parseWorkItemTransitionError(
  response: Response
): Promise<WorkItemApiErrorResponse | null> {
  const contentType = response.headers.get("content-type");
  if (contentType === null || !contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as WorkItemApiErrorResponse;
}
