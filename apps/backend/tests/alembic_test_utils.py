"""Helpers for loading Alembic test config independent of the working directory."""

from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parent.parent
ALEMBIC_INI_PATH = BACKEND_DIR / "alembic.ini"
MIGRATIONS_DIR = BACKEND_DIR / "migrations"


def load_alembic_config() -> Config:
    """Load backend Alembic config with absolute paths for repo-root validation."""
    config = Config(str(ALEMBIC_INI_PATH))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("prepend_sys_path", str(BACKEND_DIR))
    return config


def load_script_directory() -> ScriptDirectory:
    """Return the Alembic script directory using the resolved test config."""
    return ScriptDirectory.from_config(load_alembic_config())
