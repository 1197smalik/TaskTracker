"""Background worker lifecycle bootstrap."""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Protocol

from sqlalchemy.orm import Session, sessionmaker

from taskmaster_backend.db.session import get_session_factory
from taskmaster_backend.workers.config import WorkerConfig

logger = logging.getLogger(__name__)


class Sleeper(Protocol):
    """Clock adapter used to make worker sleep behavior testable."""

    def sleep(self, seconds: float) -> None:
        """Sleep for the requested number of seconds."""
        ...


class BackgroundWorker(ABC):
    """Base class for database-backed background workers."""

    def __init__(
        self,
        config: WorkerConfig,
        *,
        database_url: str | None = None,
        session_factory: sessionmaker[Session] | None = None,
        sleeper: Sleeper | None = None,
    ) -> None:
        self.config = config
        self.database_url = database_url
        self._session_factory = session_factory
        self._sleeper = sleeper or time
        self._stop_event = threading.Event()
        self._started = False

    def initialize(self) -> None:
        """Initialize resources required by the worker."""
        if self._session_factory is None:
            self._session_factory = get_session_factory(self.database_url)
        self._started = True
        logger.info(
            "Worker %s initialized with batch_size=%s poll_interval=%s",
            self.config.name,
            self.config.batch_size,
            self.config.poll_interval_seconds,
        )

    def shutdown(self) -> None:
        """Mark the worker stopped and release lifecycle state."""
        self._stop_event.set()
        self._started = False
        logger.info("Worker %s shutdown complete", self.config.name)

    @abstractmethod
    def execute_batch(self, session: Session) -> int:
        """Execute one batch of work and return the processed item count."""
        ...

    def run_once(self) -> int:
        """Run exactly one transactional worker batch."""
        if not self.config.enabled:
            logger.info("Worker %s is disabled; skipping batch", self.config.name)
            return 0
        if self._session_factory is None:
            raise RuntimeError("worker must be initialized before running")

        with self._session_factory() as session:
            try:
                processed_count = self.execute_batch(session)
                session.commit()
            except Exception:
                session.rollback()
                raise

        logger.debug(
            "Worker %s processed %s item(s)",
            self.config.name,
            processed_count,
        )
        return processed_count

    def run(self) -> None:
        """Run worker batches until stopped."""
        if not self._started:
            self.initialize()

        failed_attempts = 0
        while not self._stop_event.is_set():
            try:
                self.run_once()
                failed_attempts = 0
                self._sleeper.sleep(self.config.poll_interval_seconds)
            except Exception:
                failed_attempts += 1
                if failed_attempts > self.config.max_retries:
                    logger.exception(
                        "Worker %s exceeded max retries",
                        self.config.name,
                    )
                    raise
                retry_delay = self.config.retry_delay_seconds(failed_attempts)
                logger.warning(
                    "Worker %s batch failed; retrying in %s second(s)",
                    self.config.name,
                    retry_delay,
                    exc_info=True,
                )
                self._sleeper.sleep(retry_delay)

    def stop(self) -> None:
        """Signal worker shutdown after the current batch."""
        self._stop_event.set()
        logger.info("Worker %s stop signal sent", self.config.name)

    @property
    def stopped(self) -> bool:
        """Return whether the worker has been asked to stop."""
        return self._stop_event.is_set()
