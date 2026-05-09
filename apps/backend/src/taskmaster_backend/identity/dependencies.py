"""FastAPI authentication dependencies for identity routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from taskmaster_backend.identity.tokens import InvalidTokenError, decode_access_token

bearer_auth = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Token-authenticated principal without database-backed user hydration."""

    subject: str
    issuer: str
    audience: str
    expires_at: int


def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_auth)],
) -> AuthenticatedPrincipal:
    if credentials is None:
        raise _unauthenticated("missing_bearer_token", "Bearer access token is required.")
    if credentials.scheme.lower() != "bearer":
        raise _unauthenticated("invalid_auth_scheme", "Bearer authentication is required.")

    try:
        claims = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise _unauthenticated("invalid_bearer_token", "Bearer access token is invalid.") from exc

    return AuthenticatedPrincipal(
        subject=claims.sub,
        issuer=claims.iss,
        audience=claims.aud,
        expires_at=claims.exp,
    )


def _unauthenticated(error_code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_code": error_code,
            "message": message,
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
