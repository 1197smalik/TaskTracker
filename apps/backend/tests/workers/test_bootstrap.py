"""Tests for background worker bootstrap primitives."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from taskmaster_backend.db.session import get_session_factory, reset_db_caches
from taskmaster_backend.workers import BackgroundWorker, WorkerConfig
from taskmaster_backend.workers.worker import Sleeper


class RecordingWorker(BackgroundWorker):
    """Worker implementation used to exercise the bootstrap lifecycle."""

    def __init__(
        self,
        config: WorkerConfig,
        *,
        database_url: str | None = None,
        session_factory: sessionmaker[Session] | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        super().__init__(
            config,
            database_url=database_url,
            session_factory=session_factory,
            sleeper=sleeper,
        )
        self.processed_counts: list[int] = []
        self.raise_on_batch: Exception | None = None

    def execute_batch(self, session: Session) -> int:
        session.execute(text("SELECT 1"))
        if self.raise_on_batch is not None:
            raise self.raise_on_batch
        processed_count = self.config.batch_size
        self.processed_counts.append(processed_count)
        return processed_count


class RecordingSleeper:
    """Sleep adapter that stops the worker after one loop in tests."""

    def __init__(self, worker: BackgroundWorker | None = None) -> None:
        self.worker = worker
        self.delays: list[float] = []

    def sleep(self, seconds: float) -> None:
        self.delays.append(seconds)
        if self.worker is not None:
            self.worker.stop()


@pytest.fixture(autouse=True)
def clear_db_caches() -> Iterator[None]:
    reset_db_caches()
    yield
    reset_db_caches()


def test_worker_config_defaults_and_retry_delay() -> None:
    config = WorkerConfig(name="outbox-bootstrap")

    assert config.enabled is True
    assert config.poll_interval_seconds == 5.0
    assert config.batch_size == 10
    assert config.max_retries == 3
    assert config.retry_delay_seconds(1) == 1.0
    assert config.retry_delay_seconds(3) == 4.0


@pytest.mark.parametrize(
    ("config_factory", "message"),
    [
        (lambda: WorkerConfig(name=""), "worker name is required"),
        (lambda: WorkerConfig(name="worker", poll_interval_seconds=0), "poll interval"),
        (lambda: WorkerConfig(name="worker", batch_size=0), "batch size"),
        (lambda: WorkerConfig(name="worker", max_retries=-1), "max retries"),
        (
            lambda: WorkerConfig(name="worker", retry_backoff_base_seconds=0),
            "retry backoff base",
        ),
        (
            lambda: WorkerConfig(name="worker", retry_backoff_multiplier=0),
            "retry backoff multiplier",
        ),
    ],
)
def test_worker_config_rejects_invalid_values(
    config_factory: Callable[[], WorkerConfig],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        config_factory()


def test_run_once_commits_successful_batch(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path}/worker.db"
    worker = RecordingWorker(
        WorkerConfig(name="bootstrap", batch_size=3),
        database_url=database_url,
    )

    worker.initialize()
    processed_count = worker.run_once()

    assert processed_count == 3
    assert worker.processed_counts == [3]


def test_run_once_rolls_back_failed_batch(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path}/worker.db"
    worker = RecordingWorker(
        WorkerConfig(name="bootstrap"),
        database_url=database_url,
    )
    worker.initialize()
    worker.raise_on_batch = RuntimeError("batch failed")

    with pytest.raises(RuntimeError, match="batch failed"):
        worker.run_once()


def test_disabled_worker_skips_batch(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path}/worker.db"
    worker = RecordingWorker(
        WorkerConfig(name="bootstrap", enabled=False),
        database_url=database_url,
    )
    worker.initialize()

    assert worker.run_once() == 0
    assert worker.processed_counts == []


def test_run_initializes_and_stops_after_poll_interval(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path}/worker.db"
    sleeper = RecordingSleeper()
    worker = RecordingWorker(
        WorkerConfig(name="bootstrap", poll_interval_seconds=0.25),
        database_url=database_url,
        sleeper=sleeper,
    )
    sleeper.worker = worker

    worker.run()

    assert worker.processed_counts == [10]
    assert sleeper.delays == [0.25]
    assert worker.stopped is True


def test_worker_uses_injected_session_factory(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path}/worker.db"
    session_factory = get_session_factory(database_url)
    worker = RecordingWorker(
        WorkerConfig(name="bootstrap"),
        session_factory=session_factory,
    )

    worker.initialize()

    assert worker.run_once() == 10
