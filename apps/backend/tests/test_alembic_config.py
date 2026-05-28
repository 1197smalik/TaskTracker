"""Tests for Alembic configuration wiring."""

from alembic_test_utils import (
    MIGRATIONS_DIR,
    load_alembic_config,
    load_script_directory,
)


def test_alembic_config_uses_backend_path() -> None:
    config = load_alembic_config()

    assert config.config_file_name is not None
    assert config.config_file_name.endswith("apps/backend/alembic.ini")
    assert config.get_main_option("script_location") == str(MIGRATIONS_DIR)


def test_alembic_script_directory_loads_baseline_revision() -> None:
    script_directory = load_script_directory()

    revision = script_directory.get_revision("0001_baseline")

    assert revision is not None


def test_alembic_versions_directory_exists() -> None:
    versions_dir = MIGRATIONS_DIR / "versions"

    assert versions_dir.exists()
