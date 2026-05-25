"""Collaboration-domain API routes."""

from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

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
from taskmaster_backend.identity.rbac import PermissionGrant, PermissionScope
from taskmaster_backend.work_items.repository import get_project_work_item

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
        "Create a user-authored comment on a project-scoped work item. Mention "
        "extraction, notifications, activity feed records, and rendered markdown "
        "sanitization are handled by later stories."
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

    comment = create_comment(
        session,
        work_item_id=work_item.id,
        author_id=principal.subject,
        request=request,
    )
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
