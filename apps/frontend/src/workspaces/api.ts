import { type AuthenticatedApiClient } from "../identity/apiClient";
import { type WorkspaceNavigationItem } from "../projects";

type WorkspaceCreateRequest = {
  name: string;
};

type WorkspaceApiResponse = {
  workspace: {
    id: string;
    organization_id: string;
    name: string;
    created_at: string;
    updated_at: string;
  };
};

type WorkspaceApiErrorResponse = {
  error_code?: string;
  message?: string;
  field_errors?: Record<string, string[]>;
  detail?: {
    error_code?: string;
    message?: string;
    field_errors?: Record<string, string[]>;
  };
};

export type CreatedWorkspace = WorkspaceNavigationItem & {
  createdAt: string;
  updatedAt: string;
};

export class WorkspaceCreateError extends Error {
  statusCode: number;
  code: string;
  fieldErrors: Record<string, string[]>;

  constructor(
    statusCode: number,
    code: string,
    message: string,
    fieldErrors: Record<string, string[]>
  ) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

export async function createWorkspace(
  apiClient: AuthenticatedApiClient,
  organizationId: string,
  name: string
): Promise<CreatedWorkspace> {
  const response = await apiClient.request(
    `/api/v1/organizations/${organizationId}/workspaces`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
      } satisfies WorkspaceCreateRequest),
    }
  );
  const payload = await readJson<WorkspaceApiResponse | WorkspaceApiErrorResponse>(
    response
  );

  if (!response.ok) {
    const errorPayload = normalizeErrorPayload(payload);
    throw new WorkspaceCreateError(
      response.status,
      errorPayload.error_code ?? "workspace_create_failed",
      errorPayload.message ?? "Workspace creation failed.",
      errorPayload.field_errors ?? {}
    );
  }

  const successPayload = payload as WorkspaceApiResponse;
  return {
    id: successPayload.workspace.id,
    organizationId: successPayload.workspace.organization_id,
    name: successPayload.workspace.name,
    createdAt: successPayload.workspace.created_at,
    updatedAt: successPayload.workspace.updated_at,
  };
}

async function readJson<T>(response: Response): Promise<T | null> {
  const contentType = response.headers.get("Content-Type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as T;
}

function isWorkspaceApiErrorResponse(
  payload: WorkspaceApiResponse | WorkspaceApiErrorResponse | null
): payload is WorkspaceApiErrorResponse {
  return payload !== null && ("error_code" in payload || "message" in payload);
}

function normalizeErrorPayload(
  payload: WorkspaceApiResponse | WorkspaceApiErrorResponse | null
): WorkspaceApiErrorResponse {
  if (payload === null) {
    return {};
  }

  if ("detail" in payload && payload.detail !== undefined) {
    return payload.detail;
  }

  if (isWorkspaceApiErrorResponse(payload)) {
    return payload;
  }

  return {};
}
