import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import type { AuthenticatedApiClient } from "../identity/apiClient";
import type { AuthSession } from "../identity/session";
import {
  buildProjectWorkItemDetailPath,
  fetchProjectWorkItems,
  type WorkItemListResponse,
  buildProjectWorkItemListUrl,
} from "./api";

const DEFAULT_WORK_ITEM_LIST_LIMIT = 50;

type WorkItemListPageState =
  | {
      status: "loading";
      response: null;
      message: string;
    }
  | {
      status: "ready";
      response: WorkItemListResponse;
      message: null;
    }
  | {
      status: "failed";
      response: null;
      message: string;
    };

const loadingWorkItemListState: WorkItemListPageState = {
  status: "loading",
  response: null,
  message: "Loading work items from the backend.",
};

type WorkItemListPageProps = {
  apiClient: AuthenticatedApiClient;
  sessionStatus: AuthSession["status"];
};

export function WorkItemListPage({
  apiClient,
  sessionStatus,
}: WorkItemListPageProps) {
  const { projectId, workspaceId } = useParams();
  const listUrl =
    projectId === undefined
      ? null
      : buildProjectWorkItemListUrl(projectId, {
          limit: DEFAULT_WORK_ITEM_LIST_LIMIT,
          offset: 0,
        });
  const [state, setState] = useState<WorkItemListPageState>(loadingWorkItemListState);

  useEffect(() => {
    if (projectId === undefined) {
      setState({
        status: "failed",
        response: null,
        message: "Project route context is required before loading work items.",
      });
      return;
    }

    if (sessionStatus === "checking") {
      setState(loadingWorkItemListState);
      return;
    }

    if (sessionStatus !== "authenticated") {
      setState({
        status: "failed",
        response: null,
        message: "Sign in to load project work items.",
      });
      return;
    }

    let cancelled = false;
    setState(loadingWorkItemListState);

    void fetchProjectWorkItems(apiClient, projectId, {
      limit: DEFAULT_WORK_ITEM_LIST_LIMIT,
      offset: 0,
    })
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
          message: describeWorkItemListFailure(
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
          message: describeWorkItemListRequestFailure(error),
        });
      });

    return () => {
      cancelled = true;
    };
  }, [apiClient, projectId, sessionStatus]);

  return (
    <section aria-labelledby="work-item-list-heading">
      <p>Work items</p>
      <h1 id="work-item-list-heading">Project work items</h1>
      {listUrl !== null ? <p>List contract: {listUrl}</p> : null}
      <WorkItemListView
        projectId={projectId}
        state={state}
        workspaceId={workspaceId}
      />
    </section>
  );
}

type WorkItemListViewProps = {
  state: WorkItemListPageState;
  workspaceId: string | undefined;
  projectId: string | undefined;
};

export function WorkItemListView({
  projectId,
  state,
  workspaceId,
}: WorkItemListViewProps) {
  if (state.status === "loading") {
    return <p>{state.message}</p>;
  }

  if (state.status === "failed") {
    return <p>{state.message}</p>;
  }

  if (state.response.items.length === 0) {
    return <p>No work items returned for this project.</p>;
  }

  return (
    <table>
      <caption>
        Showing {state.response.items.length} of {state.response.total} work
        items
      </caption>
      <thead>
        <tr>
          <th scope="col">Type</th>
          <th scope="col">Title</th>
          <th scope="col">Status</th>
          <th scope="col">Priority</th>
          <th scope="col">Updated</th>
        </tr>
      </thead>
      <tbody>
        {state.response.items.map((item) => (
          <tr key={item.id}>
            <td>{item.type}</td>
            <td>
              {workspaceId !== undefined && projectId !== undefined ? (
                <Link
                  to={buildProjectWorkItemDetailPath(
                    workspaceId,
                    projectId,
                    item.id
                  )}
                >
                  {item.title}
                </Link>
              ) : (
                item.title
              )}
            </td>
            <td>{item.status}</td>
            <td>{item.priority ?? "Unprioritized"}</td>
            <td>{item.updated_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function describeWorkItemListFailure(
  statusCode: number,
  backendMessage: string | null
): string {
  if (backendMessage !== null && backendMessage !== "") {
    return backendMessage;
  }

  switch (statusCode) {
    case 401:
      return "Your session is no longer valid. Sign in again to load work items.";
    case 403:
      return "You are not authorized to access this project's work items.";
    case 404:
      return "This project was not found.";
    default:
      return "TaskMaster could not load work items from the backend.";
  }
}

function describeWorkItemListRequestFailure(error: unknown): string {
  if (
    error instanceof Error &&
    error.message === "Protected API requests require an authenticated session."
  ) {
    return "Sign in to load project work items.";
  }

  return "TaskMaster could not load work items from the backend.";
}
