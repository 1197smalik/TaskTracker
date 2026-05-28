import { Link, useParams } from "react-router-dom";

import {
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

  return (
    <section aria-labelledby="work-item-detail-heading">
      <p>Work items</p>
      <h1 id="work-item-detail-heading">Project work item detail</h1>
      {listPath !== null ? <Link to={listPath}>Back to work items</Link> : null}
      {detailUrl !== null ? <p>Detail contract: {detailUrl}</p> : null}
      <WorkItemDetailView
        listPath={listPath}
        state={unloadedWorkItemDetailState}
        workspaceId={workspaceId}
      />
    </section>
  );
}

type WorkItemDetailViewProps = {
  state: WorkItemDetailPageState;
  workspaceId: string | undefined;
  listPath: string | null;
};

export function WorkItemDetailView({
  listPath,
  state,
  workspaceId,
}: WorkItemDetailViewProps) {
  if (state.status === "not_configured") {
    return (
      <p>
        Work item detail is waiting for an authenticated API client. This page
        does not infer comment, activity, attachment, or workflow capabilities.
      </p>
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
        <dt>Updated</dt>
        <dd>{state.response.updated_at}</dd>
      </dl>
      <p>
        Comments, attachments, activity, and transition controls are handled by
        later frontend stories.
      </p>
      {listPath !== null ? <Link to={listPath}>Return to list</Link> : null}
    </article>
  );
}
