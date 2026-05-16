"""Declarative base shared by future SQLAlchemy models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for TaskMaster SQLAlchemy models."""


# Import model modules so SQLAlchemy metadata is populated for Alembic discovery.
from taskmaster_backend.identity import models as identity_models  # noqa: E402,F401
from taskmaster_backend.projects import models as project_models  # noqa: E402,F401
