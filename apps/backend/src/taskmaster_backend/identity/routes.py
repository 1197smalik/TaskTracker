"""Identity API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from taskmaster_backend.db.session import get_db_session
from taskmaster_backend.identity.auth_service import (
    ExpiredSessionError,
    InvalidCredentialsError,
    InvalidSessionError,
    RevokedSessionError,
    authenticate_user,
    issue_login_tokens,
    refresh_login_tokens,
    revoke_refresh_token,
)
from taskmaster_backend.identity.schemas import (
    ApiErrorResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
)

router = APIRouter(prefix="/auth", tags=["identity"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiErrorResponse,
            "description": "Login rate limit exceeded.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Credentials are invalid.",
        },
    },
    summary="Login with email and password",
    description=(
        "Authenticate with email and password and issue a bearer access token plus "
        "a refresh token for session continuity."
    ),
)
def login(
    request: LoginRequest,
    db_session: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse | JSONResponse:
    try:
        user = authenticate_user(
            db_session,
            email=request.email,
            password=request.password,
        )
        tokens = issue_login_tokens(db_session, user=user)
    except InvalidCredentialsError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="invalid_credentials",
            message="Email or password is incorrect.",
        )

    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in=tokens.expires_in,
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiErrorResponse,
            "description": "Refresh token rate limit exceeded.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Refresh token is invalid, expired, or revoked.",
        },
    },
    summary="Exchange refresh token",
    description=(
        "Rotate a valid refresh token and issue a new bearer access token."
    ),
)
def refresh_token(
    request: RefreshTokenRequest,
    db_session: Annotated[Session, Depends(get_db_session)],
) -> RefreshTokenResponse | JSONResponse:
    try:
        tokens = refresh_login_tokens(db_session, refresh_token=request.refresh_token)
    except InvalidSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="invalid_session",
            message="Session is invalid. Sign in again.",
        )
    except ExpiredSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="expired_session",
            message="Session expired. Sign in again.",
        )
    except RevokedSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="revoked_session",
            message="Session was revoked. Sign in again.",
        )

    return RefreshTokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type="bearer",
        expires_in=tokens.expires_in,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": ApiErrorResponse,
            "description": "Refresh token is invalid, expired, or revoked.",
        },
    },
    summary="Logout and revoke refresh token",
    description=(
        "Revoke the refresh token currently backing the frontend session."
    ),
)
def logout(
    request: LogoutRequest,
    db_session: Annotated[Session, Depends(get_db_session)],
) -> LogoutResponse | JSONResponse:
    try:
        revoke_refresh_token(db_session, refresh_token=request.refresh_token)
    except InvalidSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="invalid_session",
            message="Session is invalid. Sign in again.",
        )
    except ExpiredSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="expired_session",
            message="Session expired. Sign in again.",
        )
    except RevokedSessionError:
        return _error_response(
            status.HTTP_401_UNAUTHORIZED,
            error_code="revoked_session",
            message="Session was revoked. Sign in again.",
        )

    return LogoutResponse(revoked=True)


def _error_response(
    status_code: int,
    *,
    error_code: str,
    message: str,
) -> JSONResponse:
    error = ApiErrorResponse(
        error_code=error_code,
        message=message,
        correlation_id=str(uuid4()),
    )
    return JSONResponse(status_code=status_code, content=error.model_dump())
