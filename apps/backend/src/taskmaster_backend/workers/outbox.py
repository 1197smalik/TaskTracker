"""Outbox dispatcher worker."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.audit.models import EventOutbox, utc_now
from taskmaster_backend.workers.config import WorkerConfig
from taskmaster_backend.workers.worker import BackgroundWorker, Sleeper

logger = logging.getLogger(__name__)


class OutboxEventHandler(Protocol):
    """Handler contract for outbox event consumers."""

    def handle(self, event: EventOutbox, session: Session) -> None:
        """Dispatch one event within the worker transaction."""
        ...


class OutboxDispatcherWorker(BackgroundWorker):
    """Dispatch pending outbox events to registered handlers."""

    def __init__(
        self,
        config: WorkerConfig,
        handlers: Mapping[str, Sequence[OutboxEventHandler]],
        *,
        database_url: str | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        super().__init__(config, database_url=database_url, sleeper=sleeper)
        self._handlers = handlers

    def execute_batch(self, session: Session) -> int:
        pending_events = list(
            session.scalars(
                select(EventOutbox)
                .where(EventOutbox.status == "pending")
                .order_by(EventOutbox.created_at, EventOutbox.id)
                .limit(self.config.batch_size)
            )
        )

        dispatched_count = 0
        for event in pending_events:
            event_handlers = self._handlers.get(event.event_type, ())
            if not event_handlers:
                logger.debug(
                    "No outbox handlers registered for event_type=%s event_id=%s",
                    event.event_type,
                    event.event_id,
                )
                continue

            try:
                for handler in event_handlers:
                    handler.handle(event, session)
            except Exception:
                self._record_dispatch_failure(event)
                logger.warning(
                    "Outbox dispatch failed for event_type=%s event_id=%s",
                    event.event_type,
                    event.event_id,
                    exc_info=True,
                )
                continue

            event.status = "dispatched"
            event.dispatched_at = utc_now()
            dispatched_count += 1

        return dispatched_count

    def _record_dispatch_failure(self, event: EventOutbox) -> None:
        event.retry_count += 1
        if event.retry_count >= self.config.max_retries:
            event.status = "dead_letter"
        else:
            event.status = "pending"
