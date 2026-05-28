"""Identity API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

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
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ApiErrorResponse,
            "description": "Authentication is defined but not implemented yet.",
        },
    },
    summary="Login with email and password",
    description=(
        "Versioned login endpoint contract. Credential verification and token issuance "
        "are intentionally deferred until the authentication service stories."
    ),
)
def login(_request: LoginRequest) -> JSONResponse:
    error = ApiErrorResponse(
        error_code="authentication_not_implemented",
        message="Authentication is not available yet.",
        details={
            "reason": "Credential verification is intentionally deferred to later stories.",
        },
        correlation_id=str(uuid4()),
    )
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        status.HTTP_429_TOO_MANY_REQUESTS: {
            "model": ApiErrorResponse,
            "description": "Refresh token rate limit exceeded.",
        },
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ApiErrorResponse,
            "description": "Refresh token exchange is defined but not implemented yet.",
        },
    },
    summary="Exchange refresh token",
    description=(
        "Versioned refresh token endpoint contract. Refresh token validation, rotation, "
        "and access token issuance are intentionally deferred to later stories."
    ),
)
def refresh_token(_request: RefreshTokenRequest) -> JSONResponse:
    error = ApiErrorResponse(
        error_code="refresh_token_not_implemented",
        message="Refresh token exchange is not available yet.",
        details={
            "reason": "Refresh token validation and rotation are intentionally deferred.",
        },
        correlation_id=str(uuid4()),
    )
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    responses={
        status.HTTP_501_NOT_IMPLEMENTED: {
            "model": ApiErrorResponse,
            "description": "Logout and token revocation are defined but not implemented yet.",
        },
    },
    summary="Logout and revoke refresh token",
    description=(
        "Versioned logout endpoint contract. Refresh token lookup and revocation "
        "are intentionally deferred to later stories."
    ),
)
def logout(_request: LogoutRequest) -> JSONResponse:
    error = ApiErrorResponse(
        error_code="logout_not_implemented",
        message="Logout and token revocation are not available yet.",
        details={
            "reason": "Refresh token lookup and revocation are intentionally deferred.",
        },
        correlation_id=str(uuid4()),
    )
    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content=error.model_dump(),
    )
