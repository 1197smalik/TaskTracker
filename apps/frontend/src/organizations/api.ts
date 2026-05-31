import { type AuthenticatedApiClient } from "../identity/apiClient";

type OrganizationCreateRequest = {
  name: string;
};

type OrganizationApiResponse = {
  organization: {
    id: string;
    name: string;
    created_at: string;
    updated_at: string;
  };
};

type OrganizationApiErrorResponse = {
  error_code?: string;
  message?: string;
  field_errors?: Record<string, string[]>;
  detail?: {
    error_code?: string;
    message?: string;
    field_errors?: Record<string, string[]>;
  };
};

export type CreatedOrganization = {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
};

export class OrganizationCreateError extends Error {
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

export async function createOrganization(
  apiClient: AuthenticatedApiClient,
  name: string
): Promise<CreatedOrganization> {
  const response = await apiClient.request("/api/v1/organizations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      name,
    } satisfies OrganizationCreateRequest),
  });
  const payload = await readJson<OrganizationApiResponse | OrganizationApiErrorResponse>(
    response
  );

  if (!response.ok) {
    const errorPayload = normalizeErrorPayload(payload);
    throw new OrganizationCreateError(
      response.status,
      errorPayload.error_code ?? "organization_create_failed",
      errorPayload.message ?? "Organization creation failed.",
      errorPayload.field_errors ?? {}
    );
  }

  const successPayload = payload as OrganizationApiResponse;
  return {
    id: successPayload.organization.id,
    name: successPayload.organization.name,
    createdAt: successPayload.organization.created_at,
    updatedAt: successPayload.organization.updated_at,
  };
}

async function readJson<T>(response: Response): Promise<T | null> {
  const contentType = response.headers.get("Content-Type") ?? "";
  if (!contentType.includes("application/json")) {
    return null;
  }

  return (await response.json()) as T;
}

function isOrganizationApiErrorResponse(
  payload: OrganizationApiResponse | OrganizationApiErrorResponse | null
): payload is OrganizationApiErrorResponse {
  return payload !== null && ("error_code" in payload || "message" in payload);
}

function normalizeErrorPayload(
  payload: OrganizationApiResponse | OrganizationApiErrorResponse | null
): OrganizationApiErrorResponse {
  if (payload === null) {
    return {};
  }

  if ("detail" in payload && payload.detail !== undefined) {
    return payload.detail;
  }

  if (isOrganizationApiErrorResponse(payload)) {
    return payload;
  }

  return {};
}
