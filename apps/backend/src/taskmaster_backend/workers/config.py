"""Background worker configuration primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkerConfig:
    """Configuration for background worker processes."""

    name: str
    enabled: bool = True
    poll_interval_seconds: float = 5.0
    batch_size: int = 10
    max_retries: int = 3
    retry_backoff_base_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("worker name is required")
        if self.poll_interval_seconds <= 0:
            raise ValueError("poll interval must be greater than zero")
        if self.batch_size < 1:
            raise ValueError("batch size must be at least one")
        if self.max_retries < 0:
            raise ValueError("max retries cannot be negative")
        if self.retry_backoff_base_seconds <= 0:
            raise ValueError("retry backoff base must be greater than zero")
        if self.retry_backoff_multiplier < 1:
            raise ValueError("retry backoff multiplier must be at least one")

    def retry_delay_seconds(self, failed_attempt: int) -> float:
        """Return the delay before retrying a failed batch."""
        if failed_attempt < 1:
            raise ValueError("failed attempt must be at least one")
        return self.retry_backoff_base_seconds * (
            self.retry_backoff_multiplier ** (failed_attempt - 1)
        )
