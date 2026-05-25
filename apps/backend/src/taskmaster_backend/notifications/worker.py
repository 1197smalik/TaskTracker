"""Notification creation worker wiring for outbox events."""

from __future__ import annotations

from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.collaboration.events import COMMENT_MENTION_DETECTED_EVENT_TYPE
from taskmaster_backend.notifications.service import create_notifications_from_event
from taskmaster_backend.workers.config import WorkerConfig
from taskmaster_backend.workers.outbox import OutboxDispatcherWorker
from taskmaster_backend.workers.worker import Sleeper


class NotificationCreationHandler:
    """Outbox handler that creates durable notification rows."""

    def handle(self, event: EventOutbox, session: Session) -> None:
        create_notifications_from_event(session, event)


class NotificationCreationWorker(OutboxDispatcherWorker):
    """Worker for turning notification source events into notifications."""

    def __init__(
        self,
        config: WorkerConfig,
        *,
        database_url: str | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        super().__init__(
            config,
            {
                COMMENT_MENTION_DETECTED_EVENT_TYPE: [
                    NotificationCreationHandler(),
                ],
            },
            database_url=database_url,
            sleeper=sleeper,
        )
