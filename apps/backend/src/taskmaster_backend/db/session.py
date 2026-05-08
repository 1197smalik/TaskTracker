"""SQLAlchemy engine and session lifecycle utilities."""

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.core.config import get_settings


def _engine_kwargs(database_url: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"pool_pre_ping": True}

    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        if database_url.endswith(":memory:"):
            kwargs["poolclass"] = StaticPool

    return kwargs


@lru_cache(maxsize=None)
def get_engine(database_url: str | None = None) -> Engine:
    resolved_database_url = database_url or get_settings().database_url
    return create_engine(resolved_database_url, **_engine_kwargs(resolved_database_url))


@lru_cache(maxsize=None)
def get_session_factory(
    database_url: str | None = None,
) -> sessionmaker[Session]:
    return sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )


def get_db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def reset_db_caches() -> None:
    get_engine.cache_clear()
    get_session_factory.cache_clear()
