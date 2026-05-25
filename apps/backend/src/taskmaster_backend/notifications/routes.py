"""Notification API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.dependencies import AuthenticatedPrincipal, get_current_principal
from taskmaster_backend.notifications.schemas import (
    NotificationApiErrorResponse,
    NotificationListResponse,
    NotificationResponse,
)
from taskmaster_backend.notifications.service import (
    list_recipient_notifications,
    mark_recipient_notification_read,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _notification_not_found_error() -> NotificationApiErrorResponse:
    return NotificationApiErrorResponse(
        error_code="notification_not_found",
        message="Notification was not found or is inaccessible.",
        correlation_id=str(uuid4()),
    )


@router.get(
    "",
    response_model=NotificationListResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": NotificationApiErrorResponse,
            "description": "Bearer authentication is required.",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Pagination parameters failed validation.",
        },
    },
    summary="List notifications",
    description=(
        "List notifications for the authenticated principal only. Delivery channels, "
        "preferences, deletion, and archive behavior are handled by later stories."
    ),
)
def list_notifications(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> NotificationListResponse:
    notifications, total = list_recipient_notifications(
        session,
        recipient_id=principal.subject,
        limit=limit,
        offset=offset,
    )
    return NotificationListResponse(
        items=[NotificationResponse.from_model(notification) for notification in notifications],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": NotificationApiErrorResponse,
            "description": "Bearer authentication is required.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": NotificationApiErrorResponse,
            "description": "Notification was not found or is inaccessible.",
        },
    },
    summary="Mark notification read",
    description=(
        "Mark one authenticated-principal notification as read. Notification list/read "
        "contracts do not implement delete, archive, preferences, or delivery channels."
    ),
)
def mark_notification_read(
    notification_id: str,
    session: Session = Depends(get_db_session),
    principal: AuthenticatedPrincipal = Depends(get_current_principal),
) -> NotificationResponse | JSONResponse:
    notification = mark_recipient_notification_read(
        session,
        recipient_id=principal.subject,
        notification_id=notification_id,
    )
    if notification is None:
        error = _notification_not_found_error()
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error.model_dump(),
        )
    return NotificationResponse.from_model(notification)
