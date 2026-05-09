"""Identity API routes."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from taskmaster_backend.identity.schemas import ApiErrorResponse, LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["identity"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
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
