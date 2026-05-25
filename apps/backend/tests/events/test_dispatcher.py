"""Tests for outbox dispatcher worker behavior."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.audit.models import EventOutbox
from taskmaster_backend.db.base import Base
from taskmaster_backend.db.session import reset_db_caches
from taskmaster_backend.workers import OutboxDispatcherWorker, WorkerConfig


class RecordingHandler:
    def __init__(self) -> None:
        self.handled_event_ids: list[str] = []
        self.error: Exception | None = None

    def handle(self, event: EventOutbox, session: Session) -> None:
        session.execute(select(EventOutbox).where(EventOutbox.id == event.id))
        if self.error is not None:
            raise self.error
        self.handled_event_ids.append(event.event_id)


@pytest.fixture(autouse=True)
def clear_db_caches() -> Iterator[None]:
    reset_db_caches()
    yield
    reset_db_caches()


def _create_session_factory(tmp_path: Path) -> sessionmaker[Session]:
    engine = create_engine(
        f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def _add_event(
    session: Session,
    *,
    event_id: str,
    event_type: str = "work_item.created",
    status: str = "pending",
    retry_count: int = 0,
) -> EventOutbox:
    event = EventOutbox(
        event_id=event_id,
        event_type=event_type,
        occurred_at=datetime.now(timezone.utc),
        actor_id=None,
        organization_id="org-1",
        workspace_id="workspace-1",
        project_id="project-1",
        entity_type="work_item",
        entity_id=f"work-item-{event_id}",
        correlation_id=f"correlation-{event_id}",
        payload={"event_id": event_id},
        status=status,
        retry_count=retry_count,
    )
    session.add(event)
    return event


def test_dispatcher_marks_pending_event_dispatched(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    handler = RecordingHandler()
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher"),
        {"work_item.created": [handler]},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        event = _add_event(session, event_id="event-1")
        session.commit()
        event_id = event.id

    processed_count = worker.run_once()

    with session_factory() as session:
        result = session.scalars(select(EventOutbox).filter_by(id=event_id)).one()

    assert processed_count == 1
    assert handler.handled_event_ids == ["event-1"]
    assert result.status == "dispatched"
    assert result.dispatched_at is not None


def test_dispatcher_respects_batch_size(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    handler = RecordingHandler()
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher", batch_size=2),
        {"work_item.created": [handler]},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        _add_event(session, event_id="event-1")
        _add_event(session, event_id="event-2")
        _add_event(session, event_id="event-3")
        session.commit()

    assert worker.run_once() == 2

    with session_factory() as session:
        dispatched = list(session.scalars(select(EventOutbox).filter_by(status="dispatched")))
        pending = list(session.scalars(select(EventOutbox).filter_by(status="pending")))

    assert len(dispatched) == 2
    assert len(pending) == 1


def test_dispatcher_leaves_event_pending_without_handler(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher"),
        {},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        event = _add_event(session, event_id="event-1")
        session.commit()
        event_id = event.id

    assert worker.run_once() == 0

    with session_factory() as session:
        result = session.scalars(select(EventOutbox).filter_by(id=event_id)).one()

    assert result.status == "pending"
    assert result.retry_count == 0
    assert result.dispatched_at is None


def test_dispatcher_records_retry_after_handler_failure(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    handler = RecordingHandler()
    handler.error = RuntimeError("delivery failed")
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher", max_retries=3),
        {"work_item.created": [handler]},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        event = _add_event(session, event_id="event-1")
        session.commit()
        event_id = event.id

    assert worker.run_once() == 0

    with session_factory() as session:
        result = session.scalars(select(EventOutbox).filter_by(id=event_id)).one()

    assert result.status == "pending"
    assert result.retry_count == 1
    assert result.dispatched_at is None


def test_dispatcher_dead_letters_event_at_retry_limit(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    handler = RecordingHandler()
    handler.error = RuntimeError("delivery failed")
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher", max_retries=3),
        {"work_item.created": [handler]},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        event = _add_event(session, event_id="event-1", retry_count=2)
        session.commit()
        event_id = event.id

    assert worker.run_once() == 0

    with session_factory() as session:
        result = session.scalars(select(EventOutbox).filter_by(id=event_id)).one()

    assert result.status == "dead_letter"
    assert result.retry_count == 3


def test_dispatcher_ignores_non_pending_events(tmp_path: Path) -> None:
    session_factory = _create_session_factory(tmp_path)
    handler = RecordingHandler()
    worker = OutboxDispatcherWorker(
        WorkerConfig(name="outbox-dispatcher"),
        {"work_item.created": [handler]},
        database_url=f"sqlite+pysqlite:///{tmp_path / 'dispatcher.db'}",
    )
    worker.initialize()

    with session_factory() as session:
        _add_event(session, event_id="event-1", status="dispatched")
        session.commit()

    assert worker.run_once() == 0
    assert handler.handled_event_ids == []
