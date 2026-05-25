"""Collaboration-domain API routes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.audit.service import create_outbox_event
from taskmaster_backend.collaboration.events import (
    COLLABORATION_EVENT_PAYLOAD_VERSION,
    COMMENT_CREATED_EVENT_TYPE,
    COMMENT_MENTION_DETECTED_EVENT_TYPE,
    build_comment_created_payload,
    build_comment_mention_detected_payload,
    unresolved_mention_recipients,
)
from taskmaster_backend.collaboration.mentions import extract_mentions
from taskmaster_backend.collaboration.repository import create_comment
from taskmaster_backend.collaboration.schemas import (
    CommentApiErrorResponse,
    CommentCreateRequest,
    CommentResponse,
)
from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.authorization import (
    PermissionRequirement,
    authorize_principal,
    empty_permission_grants,
)
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.identity.models import Workspace
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope
from taskmaster_backend.work_items.repository import get_project, get_project_work_item

router = APIRouter(
    prefix="/projects/{project_id}/work-items/{work_item_id}/comments",
    tags=["comments"],
)


def _work_item_not_found_error() -> CommentApiErrorResponse:
    return CommentApiErrorResponse(
        error_code="work_item_not_found",
        message="Work item was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CommentResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": CommentApiErrorResponse,
            "description": "Bearer authentication is required.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": CommentApiErrorResponse,
            "description": "The authenticated principal lacks comment.create.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": CommentApiErrorResponse,
            "description": "Work item was not found or is inaccessible.",
        },
    },
    summary="Create work item comment",
    description=(
        "Create a user-authored comment on a project-scoped work item and emit "
        "internal collaboration events. Mention recipient resolution, notifications, "
        "activity feed records, and rendered markdown sanitization are handled by "
        "later stories."
    ),
)
def create_work_item_comment(
    project_id: str,
    work_item_id: str,
    request: CommentCreateRequest,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
    grants: Iterable[PermissionGrant] = Depends(empty_permission_grants),
) -> CommentResponse | JSONResponse:
    _authorize_comment_create(project_id, principal, grants)

    work_item = get_project_work_item(session, project_id, work_item_id)
    if work_item is None:
        error = _work_item_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    project = get_project(session, project_id)
    workspace = session.get(Workspace, project.workspace_id) if project is not None else None
    if project is None or workspace is None:
        error = _work_item_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )

    try:
        comment = create_comment(
            session,
            work_item_id=work_item.id,
            author_id=principal.subject,
            request=request,
            commit=False,
        )
        session.flush()
        mentions = extract_mentions(request.body)
        recipient_resolution = unresolved_mention_recipients(mentions)
        correlation_id = str(uuid4())
        occurred_at = datetime.now(timezone.utc)
        create_outbox_event(
            session,
            event_type=COMMENT_CREATED_EVENT_TYPE,
            occurred_at=occurred_at,
            actor_id=principal.subject,
            organization_id=workspace.organization_id,
            workspace_id=workspace.id,
            project_id=project.id,
            entity_type="comment",
            entity_id=comment.id,
            correlation_id=correlation_id,
            payload=build_comment_created_payload(
                comment,
                project_id=project.id,
                mentions=mentions,
                recipient_resolution=recipient_resolution,
            ),
            payload_version=COLLABORATION_EVENT_PAYLOAD_VERSION,
        )
        if mentions:
            create_outbox_event(
                session,
                event_type=COMMENT_MENTION_DETECTED_EVENT_TYPE,
                occurred_at=occurred_at,
                actor_id=principal.subject,
                organization_id=workspace.organization_id,
                workspace_id=workspace.id,
                project_id=project.id,
                entity_type="comment",
                entity_id=comment.id,
                correlation_id=correlation_id,
                payload=build_comment_mention_detected_payload(
                    comment,
                    project_id=project.id,
                    mentions=mentions,
                    recipient_resolution=recipient_resolution,
                ),
                payload_version=COLLABORATION_EVENT_PAYLOAD_VERSION,
            )
        session.commit()
        session.refresh(comment)
    except Exception:
        session.rollback()
        raise

    return CommentResponse.from_model(comment)


def _authorize_comment_create(
    project_id: str,
    principal: AuthenticatedPrincipal,
    grants: Iterable[PermissionGrant],
) -> None:
    authorize_principal(
        principal,
        PermissionRequirement(
            permission="comment.create",
            scope=PermissionScope(scope_type="project", scope_id=project_id),
        ),
        grants,
    )
