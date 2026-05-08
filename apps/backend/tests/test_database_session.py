"""Tests for SQLAlchemy configuration and session lifecycle."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import text

from taskmaster_backend.core import config as config_module
from taskmaster_backend.db import session as session_module
from taskmaster_backend.db.base import Base


def test_settings_read_database_url_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    database_url = "sqlite+pysqlite:///./taskmaster-test.db"
    monkeypatch.setenv("TASKMASTER_DATABASE_URL", database_url)
    config_module.reset_settings_cache()

    settings = config_module.get_settings()

    assert settings.database_url == database_url


def test_base_metadata_starts_without_domain_tables() -> None:
    assert Base.metadata.tables == {}


def test_session_factory_uses_safe_sqlite_settings(tmp_path: Path) -> None:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'taskmaster.db'}"
    session_module.reset_db_caches()
    session_factory = session_module.get_session_factory(database_url)

    with session_factory() as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1


def test_get_db_session_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    class DummySession:
        closed = False

        def close(self) -> None:
            self.closed = True

    dummy_session = DummySession()

    def fake_session_factory() -> DummySession:
        return dummy_session

    monkeypatch.setattr(
        session_module,
        "get_session_factory",
        lambda database_url=None: fake_session_factory,
    )

    session_iterator: Iterator[object] = session_module.get_db_session()
    yielded_session = next(session_iterator)

    assert yielded_session is dummy_session

    with pytest.raises(StopIteration):
        next(session_iterator)

    assert dummy_session.closed is True
