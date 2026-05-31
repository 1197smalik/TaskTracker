import { type FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { AuthenticatedApiClient } from "../identity/apiClient";
import {
  buildProjectBoardPath,
  buildProjectWorkflowStatesUrl,
  buildProjectWorkItemListUrl,
  transitionProjectWorkItem,
  type ProjectWorkflowStateCatalogResponse,
  type ProjectWorkflowStateResponse,
  type WorkItemListResponse,
  type WorkItemResponse,
} from "./api";

const DEFAULT_BOARD_WORK_ITEM_LIMIT = 100;

type WorkItemBoardPageState =
  | {
      status: "not_configured";
      response: null;
    }
  | {
      status: "ready";
      response: {
        workflowStates: ProjectWorkflowStateCatalogResponse;
        workItems: WorkItemListResponse;
      };
    };

const unloadedWorkItemBoardState: WorkItemBoardPageState = {
  status: "not_configured",
  response: null,
};

type WorkItemBoardPageProps = {
  apiClient: AuthenticatedApiClient;
};

export function WorkItemBoardPage({ apiClient }: WorkItemBoardPageProps) {
  const { workspaceId, projectId } = useParams();
  const workflowStatesUrl =
    projectId === undefined ? null : buildProjectWorkflowStatesUrl(projectId);
  const workItemsUrl =
    projectId === undefined
      ? null
      : buildProjectWorkItemListUrl(projectId, {
          limit: DEFAULT_BOARD_WORK_ITEM_LIMIT,
          offset: 0,
        });
  const boardPath =
    workspaceId === undefined || projectId === undefined
      ? null
      : buildProjectBoardPath(workspaceId, projectId);

  return (
    <section aria-labelledby="work-item-board-heading">
      <p>Work items</p>
      <h1 id="work-item-board-heading">Project board</h1>
      {boardPath !== null ? <p>Route path: {boardPath}</p> : null}
      {workflowStatesUrl !== null ? (
        <p>Workflow states contract: {workflowStatesUrl}</p>
      ) : null}
      {workItemsUrl !== null ? <p>Work items contract: {workItemsUrl}</p> : null}
      <WorkItemBoardView
        apiClient={apiClient}
        projectId={projectId}
        state={unloadedWorkItemBoardState}
        workspaceId={workspaceId}
      />
    </section>
  );
}

type WorkItemBoardViewProps = {
  apiClient: AuthenticatedApiClient;
  state: WorkItemBoardPageState;
  workspaceId: string | undefined;
  projectId: string | undefined;
};

export function WorkItemBoardView({
  apiClient,
  projectId,
  state,
  workspaceId,
}: WorkItemBoardViewProps) {
  if (state.status === "not_configured") {
    return (
      <p>
        Board data is waiting for authenticated API responses. This board does not infer transition legality or permissions. Backend workflow state catalog and transition responses own those outcomes.
      </p>
    );
  }

  if (projectId === undefined) {
    return <p>Project route context is required before rendering board columns.</p>;
  }

  return (
    <ReadyWorkItemBoard
      apiClient={apiClient}
      projectId={projectId}
      response={state.response}
      workspaceId={workspaceId}
    />
  );
}

type ReadyWorkItemBoardProps = {
  apiClient: AuthenticatedApiClient;
  response: {
    workflowStates: ProjectWorkflowStateCatalogResponse;
    workItems: WorkItemListResponse;
  };
  workspaceId: string | undefined;
  projectId: string;
};

function ReadyWorkItemBoard({
  apiClient,
  projectId,
  response,
  workspaceId,
}: ReadyWorkItemBoardProps) {
  const [boardItems, setBoardItems] = useState<WorkItemResponse[]>(
    response.workItems.items
  );
  const workflowStateIds = new Set(
    response.workflowStates.states.map((state) => state.id)
  );
  const unmappedItems = boardItems.filter(
    (item) =>
      item.current_state_id === null || !workflowStateIds.has(item.current_state_id)
  );

  function replaceConfirmedWorkItem(confirmedWorkItem: WorkItemResponse) {
    setBoardItems((items) =>
      items.map((item) =>
        item.id === confirmedWorkItem.id ? confirmedWorkItem : item
      )
    );
  }

  return (
    <div aria-label="Backend workflow state board">
      <p>Workflow definition: {response.workflowStates.workflow_definition_id}</p>
      <div>
        {response.workflowStates.states.map((workflowState) => {
          const columnItems = boardItems.filter(
            (item) => item.current_state_id === workflowState.id
          );

          return (
            <section key={workflowState.id} aria-labelledby={workflowState.id}>
              <h2 id={workflowState.id}>{workflowState.name}</h2>
              <p>Position {workflowState.position}</p>
              {columnItems.length === 0 ? (
                <p>No work items in this backend workflow state.</p>
              ) : null}
              {columnItems.map((workItem) => (
                <article key={workItem.id} aria-label={workItem.title}>
                  <p>{workItem.type}</p>
                  <h3>{workItem.title}</h3>
                  <p>Version {workItem.version}</p>
                  <p>State {workItem.current_state_id}</p>
                  <BoardTransitionControl
                    apiClient={apiClient}
                    onTransitionConfirmed={replaceConfirmedWorkItem}
                    projectId={projectId}
                    states={response.workflowStates.states}
                    workItem={workItem}
                  />
                </article>
              ))}
            </section>
          );
        })}
      </div>
      {unmappedItems.length > 0 ? (
        <section aria-labelledby="unmapped-work-items-heading">
          <h2 id="unmapped-work-items-heading">Items without backend board column</h2>
          {unmappedItems.map((workItem) => (
            <p key={workItem.id}>{workItem.title}</p>
          ))}
        </section>
      ) : null}
      {workspaceId !== undefined ? (
        <Link to={`/workspace/${workspaceId}/projects/${projectId}/work-items`}>
          View work item list
        </Link>
      ) : null}
    </div>
  );
}

type BoardTransitionControlProps = {
  apiClient: AuthenticatedApiClient;
  projectId: string;
  workItem: WorkItemResponse;
  states: ProjectWorkflowStateResponse[];
  onTransitionConfirmed: (workItem: WorkItemResponse) => void;
};

type BoardTransitionState =
  | {
      status: "idle";
      message: null;
    }
  | {
      status: "submitting";
      message: string;
    }
  | {
      status: "succeeded";
      message: string;
    }
  | {
      status: "failed";
      message: string;
    };

function BoardTransitionControl({
  apiClient,
  onTransitionConfirmed,
  projectId,
  states,
  workItem,
}: BoardTransitionControlProps) {
  const [targetStateId, setTargetStateId] = useState("");
  const [transitionState, setTransitionState] = useState<BoardTransitionState>({
    status: "idle",
    message: null,
  });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (targetStateId === "") {
      setTransitionState({
        status: "failed",
        message: "Failed transition leaves board state unchanged: target_state_id is required.",
      });
      return;
    }

    setTransitionState({
      status: "submitting",
      message: "Submitting backend workflow transition request.",
    });

    try {
      const result = await transitionProjectWorkItem(apiClient, projectId, workItem.id, {
        expected_version: workItem.version,
        source_state_id: workItem.current_state_id,
        target_state_id: targetStateId,
      });

      if (result.status === "succeeded") {
        onTransitionConfirmed(result.response.work_item);
        setTransitionState({
          status: "succeeded",
          message: "Backend confirmed transition and returned updated board item.",
        });
        return;
      }

      setTransitionState({
        status: "failed",
        message: `Failed transition leaves board state unchanged: ${result.error?.message ?? `HTTP ${result.statusCode}`}`,
      });
    } catch {
      setTransitionState({
        status: "failed",
        message: "Failed transition leaves board state unchanged: request did not complete.",
      });
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>
        target_state_id
        <select
          name="target_state_id"
          value={targetStateId}
          onChange={(event) => setTargetStateId(event.target.value)}
        >
          <option value="">Select backend state</option>
          {states.map((state) => (
            <option key={state.id} value={state.id}>
              {state.name}
            </option>
          ))}
        </select>
      </label>
      <button disabled={transitionState.status === "submitting"} type="submit">
        Transition via backend
      </button>
      {transitionState.message !== null ? <p>{transitionState.message}</p> : null}
    </form>
  );
}
