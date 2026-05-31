"""Database-backed authentication and refresh-session helpers."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from taskmaster_backend.core.config import get_settings
from taskmaster_backend.identity.models import RefreshToken, User
from taskmaster_backend.identity.passwords import verify_password
from taskmaster_backend.identity.tokens import create_access_token


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int


class InvalidCredentialsError(ValueError):
    """Raised when the supplied credentials cannot authenticate a user."""


class InvalidSessionError(ValueError):
    """Raised when a refresh token is unknown or malformed."""


class ExpiredSessionError(ValueError):
    """Raised when a refresh token has expired."""


class RevokedSessionError(ValueError):
    """Raised when a refresh token has been revoked."""


def authenticate_user(
    db_session: Session,
    *,
    email: str,
    password: str,
) -> User:
    normalized_email = email.strip().lower()
    user = db_session.scalar(select(User).where(User.email == normalized_email))
    if user is None or not user.is_active:
        raise InvalidCredentialsError("Credentials are invalid.")
    if not verify_password(password, user.password_hash):
        raise InvalidCredentialsError("Credentials are invalid.")
    return user


def issue_login_tokens(db_session: Session, *, user: User) -> AuthTokens:
    refresh_token = _generate_refresh_token()
    db_session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=_refresh_token_expiry(),
        )
    )
    db_session.commit()
    return AuthTokens(
        access_token=create_access_token(user.id),
        refresh_token=refresh_token,
        expires_in=get_settings().jwt_access_token_ttl_seconds,
    )


def refresh_login_tokens(db_session: Session, *, refresh_token: str) -> AuthTokens:
    stored_token = _require_active_refresh_token(db_session, refresh_token=refresh_token)
    stored_token.revoked_at = _utc_now()

    rotated_refresh_token = _generate_refresh_token()
    db_session.add(
        RefreshToken(
            user_id=stored_token.user_id,
            token_hash=hash_refresh_token(rotated_refresh_token),
            expires_at=_refresh_token_expiry(),
        )
    )
    db_session.commit()

    return AuthTokens(
        access_token=create_access_token(stored_token.user_id),
        refresh_token=rotated_refresh_token,
        expires_in=get_settings().jwt_access_token_ttl_seconds,
    )


def revoke_refresh_token(db_session: Session, *, refresh_token: str) -> bool:
    stored_token = _require_active_refresh_token(db_session, refresh_token=refresh_token)
    stored_token.revoked_at = _utc_now()
    db_session.commit()
    return True


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def _require_active_refresh_token(
    db_session: Session,
    *,
    refresh_token: str,
) -> RefreshToken:
    stored_token = db_session.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(refresh_token)
        )
    )
    if stored_token is None:
        raise InvalidSessionError("Refresh token is invalid.")
    if stored_token.revoked_at is not None:
        raise RevokedSessionError("Refresh token has been revoked.")
    if _coerce_utc(stored_token.expires_at) <= _utc_now():
        stored_token.revoked_at = _utc_now()
        db_session.commit()
        raise ExpiredSessionError("Refresh token has expired.")
    return stored_token


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def _refresh_token_expiry() -> datetime:
    settings = get_settings()
    return _utc_now() + timedelta(seconds=settings.refresh_token_ttl_seconds)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
