"""Environment-based configuration for backend infrastructure."""

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///:memory:"


@dataclass(frozen=True)
class Settings:
    database_url: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("TASKMASTER_DATABASE_URL", DEFAULT_DATABASE_URL),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
