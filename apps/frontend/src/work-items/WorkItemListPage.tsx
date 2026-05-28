import { Link, useParams } from "react-router-dom";

import {
  buildProjectWorkItemDetailPath,
  type WorkItemListResponse,
  buildProjectWorkItemListUrl,
} from "./api";

const DEFAULT_WORK_ITEM_LIST_LIMIT = 50;

type WorkItemListPageState =
  | {
      status: "not_configured";
      response: null;
    }
  | {
      status: "ready";
      response: WorkItemListResponse;
    };

const unloadedWorkItemListState: WorkItemListPageState = {
  status: "not_configured",
  response: null,
};

export function WorkItemListPage() {
  const { projectId, workspaceId } = useParams();
  const listUrl =
    projectId === undefined
      ? null
      : buildProjectWorkItemListUrl(projectId, {
          limit: DEFAULT_WORK_ITEM_LIST_LIMIT,
          offset: 0,
        });

  return (
    <section aria-labelledby="work-item-list-heading">
      <p>Work items</p>
      <h1 id="work-item-list-heading">Project work items</h1>
      {listUrl !== null ? <p>List contract: {listUrl}</p> : null}
      <WorkItemListView
        projectId={projectId}
        state={unloadedWorkItemListState}
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
  if (state.status === "not_configured") {
    return (
      <p>
        Work item data is waiting for an authenticated API client. This page
        does not infer project access or fake work item persistence.
      </p>
    );
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
