"""Tests for minimal organization ownership persistence behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from taskmaster_backend.db.base import Base
from taskmaster_backend.identity.models import Organization, User
from taskmaster_backend.identity.organization_ownership import backfill_organization_owners


def _create_test_session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def test_backfill_organization_owners_assigns_earliest_active_user_to_legacy_organizations(
) -> None:
    session_factory = _create_test_session_factory()
    earliest_created_at = datetime.now(UTC)

    with session_factory() as session:
        session.add_all(
            [
                User(
                    id="user-early",
                    email="early@example.com",
                    password_hash="hash",
                    created_at=earliest_created_at,
                    updated_at=earliest_created_at,
                ),
                User(
                    id="user-late",
                    email="late@example.com",
                    password_hash="hash",
                    created_at=earliest_created_at + timedelta(minutes=5),
                    updated_at=earliest_created_at + timedelta(minutes=5),
                ),
                Organization(id="org-1", name="Acme"),
                Organization(id="org-2", name="Globex"),
            ]
        )

        updated_count = backfill_organization_owners(session)
        session.commit()

        organizations = session.scalars(
            select(Organization).order_by(Organization.id.asc())
        ).all()

    assert updated_count == 2
    assert [organization.owner_user_id for organization in organizations] == [
        "user-early",
        "user-early",
    ]


def test_backfill_organization_owners_preserves_existing_owner_assignments() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        session.add_all(
            [
                User(
                    id="user-early",
                    email="early@example.com",
                    password_hash="hash",
                ),
                User(
                    id="user-owner",
                    email="owner@example.com",
                    password_hash="hash",
                ),
                Organization(id="org-1", name="Acme", owner_user_id="user-owner"),
                Organization(id="org-2", name="Globex"),
            ]
        )

        updated_count = backfill_organization_owners(session)
        session.commit()

        organizations = {
            organization.id: organization.owner_user_id
            for organization in session.scalars(select(Organization)).all()
        }

    assert updated_count == 1
    assert organizations == {
        "org-1": "user-owner",
        "org-2": "user-early",
    }


def test_backfill_organization_owners_skips_when_no_active_user_exists() -> None:
    session_factory = _create_test_session_factory()

    with session_factory() as session:
        session.add(
            Organization(id="org-1", name="Acme")
        )

        updated_count = backfill_organization_owners(session)
        session.commit()

        organization = session.scalar(select(Organization).where(Organization.id == "org-1"))

    assert updated_count == 0
    assert organization is not None
    assert organization.owner_user_id is None
