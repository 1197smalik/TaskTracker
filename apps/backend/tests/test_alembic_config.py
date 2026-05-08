"""Tests for Alembic configuration wiring."""

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def test_alembic_config_uses_backend_path() -> None:
    config = Config("alembic.ini")

    assert config.get_main_option("script_location") == "migrations"


def test_alembic_script_directory_loads_baseline_revision() -> None:
    config = Config("alembic.ini")
    script_directory = ScriptDirectory.from_config(config)

    revision = script_directory.get_revision("0001_baseline")

    assert revision is not None


def test_alembic_versions_directory_exists() -> None:
    versions_dir = Path("migrations") / "versions"

    assert versions_dir.exists()
