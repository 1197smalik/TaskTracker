import { type AuthenticatedApiClient } from "../identity/apiClient";

import { type ProjectNavigationItem } from "./navigation";

type ProjectCreateRequest = {
  key: string;
  name: string;
};

type ProjectApiResponse = {
  project: {
    id: string;
    workspace_id: string;
    key: string;
    name: string;
    created_at: string;
    updated_at: string;
  };
};

type ProjectApiErrorResponse = {
  error_code?: string;
  message?: string;
  field_errors?: Record<string, string[]>;
  detail?: {
    error_code?: string;
    message?: string;
    field_errors?: Record<string, string[]>;
  };
};

export type CreatedProject = ProjectNavigationItem & {
  createdAt: string;
  updatedAt: string;
};

export class ProjectCreateError extends Error {
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

export async function createProject(
  apiClient: AuthenticatedApiClient,
  workspaceId: string,
  key: string,
  name: string
): Promise<CreatedProject> {
  const response = await apiClient.request(
    `/api/v1/projects/workspaces/${workspaceId}/projects`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        key,
        name,
      } satisfies ProjectCreateRequest),
    }
  );
  const payload = await readJson<ProjectApiResponse | ProjectApiErrorResponse>(response);

  if (!response.ok) {
    const errorPayload = normalizeErrorPayload(payload);
    throw new ProjectCreateError(
      response.status,
      errorPayload.error_code ?? "project_create_failed",
      errorPayload.message ?? "Project creation failed.",
      errorPayload.field_errors ?? {}
    );
  }

  const successPayload = payload as ProjectApiResponse;
  return {
    id: successPayload.project.id,
    workspaceId: successPayload.project.workspace_id,
    key: successPayload.project.key,
    name: successPayload.project.name,
    createdAt: successPayload.project.created_at,
    updatedAt: successPayload.project.updated_at,
  };
}

async function readJson<T>(response: Response): Promise<T | null> {
  const contentType = response.headers.get("Content-Type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as T;
}

function isProjectApiErrorResponse(
  payload: ProjectApiResponse | ProjectApiErrorResponse | null
): payload is ProjectApiErrorResponse {
  return payload !== null && ("error_code" in payload || "message" in payload);
}

function normalizeErrorPayload(
  payload: ProjectApiResponse | ProjectApiErrorResponse | null
): ProjectApiErrorResponse {
  if (payload === null) {
    return {};
  }

  if ("detail" in payload && payload.detail !== undefined) {
    return payload.detail;
  }

  if (isProjectApiErrorResponse(payload)) {
    return payload;
  }

  return {};
}
