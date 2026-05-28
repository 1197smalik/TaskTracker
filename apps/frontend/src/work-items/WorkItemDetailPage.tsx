import { type FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  buildProjectWorkItemTransitionUrl,
  transitionProjectWorkItem,
  type WorkflowTransitionResponse,
  type WorkItemResponse,
  buildProjectWorkItemDetailPath,
  buildProjectWorkItemDetailUrl,
} from "./api";

type WorkItemDetailPageState =
  | {
      status: "not_configured";
      response: null;
    }
  | {
      status: "ready";
      response: WorkItemResponse;
    };

const unloadedWorkItemDetailState: WorkItemDetailPageState = {
  status: "not_configured",
  response: null,
};

export function WorkItemDetailPage() {
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

  return (
    <section aria-labelledby="work-item-detail-heading">
      <p>Work items</p>
      <h1 id="work-item-detail-heading">Project work item detail</h1>
      {listPath !== null ? <Link to={listPath}>Back to work items</Link> : null}
      {detailUrl !== null ? <p>Detail contract: {detailUrl}</p> : null}
      {transitionUrl !== null ? <p>Transition contract: {transitionUrl}</p> : null}
      <WorkItemDetailView
        listPath={listPath}
        projectId={projectId}
        state={unloadedWorkItemDetailState}
        transitionUrl={transitionUrl}
        workItemId={workItemId}
        workspaceId={workspaceId}
      />
    </section>
  );
}

type WorkItemDetailViewProps = {
  state: WorkItemDetailPageState;
  workspaceId: string | undefined;
  listPath: string | null;
  projectId: string | undefined;
  transitionUrl: string | null;
  workItemId: string | undefined;
};

export function WorkItemDetailView({
  listPath,
  projectId,
  state,
  transitionUrl,
  workItemId,
  workspaceId,
}: WorkItemDetailViewProps) {
  if (state.status === "not_configured") {
    return (
      <>
        <p>
          Work item detail is waiting for an authenticated API client. This
          page does not infer comment, activity, attachment, or workflow
          capabilities.
        </p>
        <WorkItemTransitionControl
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

type WorkItemTransitionControlProps = {
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
      const result = await transitionProjectWorkItem(projectId, workItemId, {
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
