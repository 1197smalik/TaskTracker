"""Persistence helpers for webhook endpoint management."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.identity.models import Organization, Workspace
from taskmaster_backend.integrations.models import WebhookEndpoint


def organization_exists(session: Session, organization_id: str) -> bool:
    return session.get(Organization, organization_id) is not None


def workspace_belongs_to_organization(
    session: Session,
    *,
    organization_id: str,
    workspace_id: str,
) -> bool:
    workspace = session.get(Workspace, workspace_id)
    return workspace is not None and workspace.organization_id == organization_id


def create_webhook_endpoint_record(
    session: Session,
    *,
    webhook_id: str,
    organization_id: str,
    workspace_id: str | None,
    url: str,
    description: str | None,
    event_types: list[str],
    project_filters: list[str],
    secret_hash: str,
    secret_reference: str,
    commit: bool = True,
) -> WebhookEndpoint:
    webhook_endpoint = WebhookEndpoint(
        id=webhook_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        url=url,
        description=description,
        event_types=list(event_types),
        project_filters=list(project_filters),
        secret_hash=secret_hash,
        secret_reference=secret_reference,
    )
    session.add(webhook_endpoint)
    session.flush()

    if commit:
        session.commit()
        session.refresh(webhook_endpoint)

    return webhook_endpoint


def list_webhook_endpoints_for_organization(
    session: Session,
    *,
    organization_id: str,
) -> list[WebhookEndpoint]:
    return list(
        session.scalars(
            select(WebhookEndpoint)
            .where(WebhookEndpoint.organization_id == organization_id)
            .order_by(WebhookEndpoint.created_at.desc(), WebhookEndpoint.id.desc())
        )
    )


def get_webhook_endpoint_for_organization(
    session: Session,
    *,
    organization_id: str,
    webhook_endpoint_id: str,
) -> WebhookEndpoint | None:
    return session.scalars(
        select(WebhookEndpoint).where(
            WebhookEndpoint.id == webhook_endpoint_id,
            WebhookEndpoint.organization_id == organization_id,
        )
    ).first()
