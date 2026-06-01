import { type FormEvent, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { AuthenticatedApiClient } from "../identity/apiClient";
import type { AuthSession } from "../identity/session";
import {
  buildProjectWorkItemTransitionUrl,
  fetchProjectWorkItemDetail,
  transitionProjectWorkItem,
  type WorkflowTransitionResponse,
  type WorkItemResponse,
  buildProjectWorkItemDetailPath,
  buildProjectWorkItemDetailUrl,
} from "./api";

type WorkItemDetailPageState =
  | {
      status: "loading";
      response: null;
      message: string;
    }
  | {
      status: "ready";
      response: WorkItemResponse;
      message: null;
    }
  | {
      status: "failed";
      response: null;
      message: string;
    };

const loadingWorkItemDetailState: WorkItemDetailPageState = {
  status: "loading",
  response: null,
  message: "Loading work item detail from the backend.",
};

type WorkItemDetailPageProps = {
  apiClient: AuthenticatedApiClient;
  sessionStatus: AuthSession["status"];
};

export function WorkItemDetailPage({
  apiClient,
  sessionStatus,
}: WorkItemDetailPageProps) {
  const { workspaceId, projectId, workItemId } = useParams();
  const detailUrl =
    projectId === undefined || workItemId === undefined
      ? null
      : buildProjectWorkItemDetailUrl(projectId, workItemId);
  const listPath =
    workspaceId === undefined || projectId === undefined
      ? null
      : `/workspace/${encodeURIComponent(workspaceId)}/projects/${encodeURIComponent(projectId)}/work-items`;
  const transitionUrl =
    projectId === undefined || workItemId === undefined
      ? null
      : buildProjectWorkItemTransitionUrl(projectId, workItemId);
  const [state, setState] = useState<WorkItemDetailPageState>(
    loadingWorkItemDetailState
  );

  useEffect(() => {
    if (projectId === undefined || workItemId === undefined) {
      setState({
        status: "failed",
        response: null,
        message:
          "Project and work item route context are required before loading detail.",
      });
      return;
    }

    if (sessionStatus === "checking") {
      setState(loadingWorkItemDetailState);
      return;
    }

    if (sessionStatus !== "authenticated") {
      setState({
        status: "failed",
        response: null,
        message: "Sign in to load work item detail.",
      });
      return;
    }

    let cancelled = false;
    setState(loadingWorkItemDetailState);

    void fetchProjectWorkItemDetail(apiClient, projectId, workItemId)
      .then((result) => {
        if (cancelled) {
          return;
        }

        if (result.status === "succeeded") {
          setState({
            status: "ready",
            response: result.response,
            message: null,
          });
          return;
        }

        setState({
          status: "failed",
          response: null,
          message: describeWorkItemDetailFailure(
            result.statusCode,
            result.error?.message ?? null
          ),
        });
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return;
        }

        setState({
          status: "failed",
          response: null,
          message: describeWorkItemDetailRequestFailure(error),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [apiClient, projectId, sessionStatus, workItemId]);

  return (
    <section aria-labelledby="work-item-detail-heading">
      <p>Work items</p>
      <h1 id="work-item-detail-heading">Project work item detail</h1>
      {listPath !== null ? <Link to={listPath}>Back to work items</Link> : null}
      {detailUrl !== null ? <p>Detail contract: {detailUrl}</p> : null}
      {transitionUrl !== null ? <p>Transition contract: {transitionUrl}</p> : null}
      <WorkItemDetailView
        apiClient={apiClient}
        listPath={listPath}
        projectId={projectId}
        state={state}
        transitionUrl={transitionUrl}
        workItemId={workItemId}
        workspaceId={workspaceId}
      />
    </section>
  );
}

type WorkItemDetailViewProps = {
  apiClient: AuthenticatedApiClient;
  state: WorkItemDetailPageState;
  workspaceId: string | undefined;
  listPath: string | null;
  projectId: string | undefined;
  transitionUrl: string | null;
  workItemId: string | undefined;
};

export function WorkItemDetailView({
  apiClient,
  listPath,
  projectId,
  state,
  transitionUrl,
  workItemId,
  workspaceId,
}: WorkItemDetailViewProps) {
  if (state.status === "loading") {
    return <p>{state.message}</p>;
  }

  if (state.status === "failed") {
    return (
      <>
        <p>{state.message}</p>
        <WorkItemTransitionControl
          apiClient={apiClient}
          currentStateId={null}
          expectedVersion={null}
          projectId={projectId}
          transitionUrl={transitionUrl}
          workItemId={workItemId}
        />
      </>
    );
  }

  const detailPath =
    workspaceId === undefined
      ? null
      : buildProjectWorkItemDetailPath(
          workspaceId,
          state.response.project_id,
          state.response.id
        );

  return (
    <article aria-label="Work item detail record">
      <p>{state.response.type}</p>
      <h2>{state.response.title}</h2>
      {detailPath !== null ? <p>Route path: {detailPath}</p> : null}
      <dl>
        <dt>Status</dt>
        <dd>{state.response.status}</dd>
        <dt>Priority</dt>
        <dd>{state.response.priority ?? "Unprioritized"}</dd>
        <dt>Assignee</dt>
        <dd>{state.response.assignee_id ?? "Unassigned"}</dd>
        <dt>Description</dt>
        <dd>{state.response.description ?? "No description provided."}</dd>
        <dt>Version</dt>
        <dd>{state.response.version}</dd>
        <dt>Workflow state</dt>
        <dd>{state.response.current_state_id ?? "Backend state not assigned"}</dd>
        <dt>Updated</dt>
        <dd>{state.response.updated_at}</dd>
      </dl>
      <WorkItemTransitionControl
        apiClient={apiClient}
        currentStateId={state.response.current_state_id}
        expectedVersion={state.response.version}
        projectId={state.response.project_id}
        transitionUrl={transitionUrl}
        workItemId={state.response.id}
      />
      <p>
        Comments, attachments, and activity are handled by later frontend
        stories.
      </p>
      {listPath !== null ? <Link to={listPath}>Return to list</Link> : null}
    </article>
  );
}

function describeWorkItemDetailFailure(
  statusCode: number,
  backendMessage: string | null
): string {
  if (backendMessage !== null && backendMessage !== "") {
    return backendMessage;
  }

  switch (statusCode) {
    case 401:
      return "Your session is no longer valid. Sign in again to load work item detail.";
    case 403:
      return "You are not authorized to access this work item.";
    case 404:
      return "This work item was not found.";
    default:
      return "TaskMaster could not load work item detail from the backend.";
  }
}

function describeWorkItemDetailRequestFailure(error: unknown): string {
  if (
    error instanceof Error &&
    error.message === "Protected API requests require an authenticated session."
  ) {
    return "Sign in to load work item detail.";
  }

  return "TaskMaster could not load work item detail from the backend.";
}

type WorkItemTransitionControlProps = {
  apiClient: AuthenticatedApiClient;
  transitionUrl: string | null;
  expectedVersion: number | null;
  currentStateId: string | null;
  projectId?: string;
  workItemId?: string;
};

type WorkItemTransitionControlState =
  | {
      status: "idle";
      message: null;
      response: null;
    }
  | {
      status: "submitting";
      message: string;
      response: null;
    }
  | {
      status: "succeeded";
      message: string;
      response: WorkflowTransitionResponse;
    }
  | {
      status: "failed";
      message: string;
      response: null;
    };

function WorkItemTransitionControl({
  apiClient,
  currentStateId,
  expectedVersion,
  projectId,
  workItemId,
  transitionUrl,
}: WorkItemTransitionControlProps) {
  const [targetStateId, setTargetStateId] = useState("");
  const [transitionState, setTransitionState] =
    useState<WorkItemTransitionControlState>({
      status: "idle",
      message: null,
      response: null,
    });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (
      projectId === undefined ||
      workItemId === undefined ||
      expectedVersion === null ||
      targetStateId.trim() === ""
    ) {
      setTransitionState({
        status: "failed",
        message:
          "Transition requires backend route context, expected_version, and target_state_id.",
        response: null,
      });
      return;
    }

    setTransitionState({
      status: "submitting",
      message: "Submitting backend workflow transition request.",
      response: null,
    });

    try {
      const result = await transitionProjectWorkItem(apiClient, projectId, workItemId, {
        expected_version: expectedVersion,
        source_state_id: currentStateId,
        target_state_id: targetStateId.trim(),
      });

      if (result.status === "succeeded") {
        setTransitionState({
          status: "succeeded",
          message:
            "Backend confirmed the workflow transition and returned the updated work item version.",
          response: result.response,
        });
        return;
      }

      setTransitionState({
        status: "failed",
        message: describeTransitionFailure(result.statusCode, result.error?.message ?? null),
        response: null,
      });
    } catch {
      setTransitionState({
        status: "failed",
        message: "Transition request failed before the backend returned a response.",
        response: null,
      });
    }
  }

  const confirmedStateId =
    transitionState.status === "succeeded"
      ? transitionState.response.work_item.current_state_id
      : currentStateId;
  const confirmedVersion =
    transitionState.status === "succeeded"
      ? transitionState.response.work_item.version
      : expectedVersion;

  return (
    <section aria-labelledby="work-item-transition-heading">
      <h3 id="work-item-transition-heading">Workflow transition control</h3>
      {transitionUrl !== null ? <p>Transition contract: {transitionUrl}</p> : null}
      <p>
        This control does not infer allowed transitions or fake workflow
        execution. Backend validation owns 400 validation, 404 not found, and
        409 conflict outcomes.
      </p>
      <form onSubmit={handleSubmit}>
        <label>
          expected_version
          <input
            name="expected_version"
            readOnly
            value={confirmedVersion === null ? "" : String(confirmedVersion)}
          />
        </label>
        <label>
          source_state_id
          <input
            name="source_state_id"
            readOnly
            value={confirmedStateId ?? ""}
          />
        </label>
        <label>
          target_state_id
          <input
            name="target_state_id"
            placeholder="backend state id required"
            value={targetStateId}
            onChange={(event) => setTargetStateId(event.target.value)}
          />
        </label>
        <button
          disabled={
            transitionState.status === "submitting" ||
            expectedVersion === null ||
            transitionUrl === null
          }
          type="submit"
        >
          Transition via backend
        </button>
      </form>
      {transitionState.message !== null ? <p>{transitionState.message}</p> : null}
      {transitionState.status === "failed" ? (
        <p>
          This transition remains backend-owned. 400 validation, 404 not found,
          and 409 conflict responses are rendered without local workflow
          inference.
        </p>
      ) : null}
    </section>
  );
}

function describeTransitionFailure(
  statusCode: number,
  backendMessage: string | null
): string {
  if (statusCode === 409) {
    return backendMessage ?? "Backend returned 409 conflict for expected_version mismatch.";
  }

  if (statusCode === 400) {
    return backendMessage ?? "Backend returned 400 validation for this workflow transition.";
  }

  if (statusCode === 404) {
    return backendMessage ?? "Backend returned 404 because the work item is unavailable.";
  }

  return backendMessage ?? `Backend returned HTTP ${statusCode} for the transition request.`;
}
