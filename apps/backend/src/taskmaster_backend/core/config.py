"""Environment-based configuration for backend infrastructure."""

import os
from dataclasses import dataclass
from functools import lru_cache

DEFAULT_DATABASE_URL = "sqlite+pysqlite:///./taskmaster.db"
DEFAULT_JWT_ALGORITHM = "HS256"
DEFAULT_JWT_ISSUER = "taskmaster-backend"
DEFAULT_JWT_AUDIENCE = "taskmaster-api"
DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS = 900


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_issuer: str
    jwt_audience: str
    jwt_access_token_ttl_seconds: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("TASKMASTER_DATABASE_URL", DEFAULT_DATABASE_URL),
        jwt_secret=os.getenv("TASKMASTER_JWT_SECRET", "taskmaster-dev-secret"),
        jwt_algorithm=os.getenv("TASKMASTER_JWT_ALGORITHM", DEFAULT_JWT_ALGORITHM),
        jwt_issuer=os.getenv("TASKMASTER_JWT_ISSUER", DEFAULT_JWT_ISSUER),
        jwt_audience=os.getenv("TASKMASTER_JWT_AUDIENCE", DEFAULT_JWT_AUDIENCE),
        jwt_access_token_ttl_seconds=int(
            os.getenv(
                "TASKMASTER_JWT_ACCESS_TOKEN_TTL_SECONDS",
                str(DEFAULT_JWT_ACCESS_TOKEN_TTL_SECONDS),
            ),
        ),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
