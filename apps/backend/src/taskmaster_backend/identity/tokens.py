"""JWT access token helpers for the authentication foundation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from jwt import exceptions as jwt_exceptions

from taskmaster_backend.core.config import get_settings


@dataclass(frozen=True)
class AccessTokenClaims:
    sub: str
    exp: int
    iss: str
    aud: str


class InvalidTokenError(ValueError):
    """Raised when a JWT is malformed, invalid, or expired."""


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for the given subject."""

    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(seconds=settings.jwt_access_token_ttl_seconds)
    payload = {
        "sub": subject,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> AccessTokenClaims:
    """Decode and validate a signed JWT access token."""

    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={
                "require": ["sub", "exp", "iss", "aud"],
            },
        )
    except jwt_exceptions.ExpiredSignatureError as exc:
        raise InvalidTokenError("JWT has expired") from exc
    except jwt_exceptions.MissingRequiredClaimError as exc:
        if exc.claim == "sub":
            raise InvalidTokenError("JWT subject claim is required") from exc
        if exc.claim == "exp":
            raise InvalidTokenError("JWT expiry claim is required") from exc
        if exc.claim == "iss":
            raise InvalidTokenError("JWT issuer claim is required") from exc
        if exc.claim == "aud":
            raise InvalidTokenError("JWT audience claim is required") from exc
        raise InvalidTokenError(f"JWT claim is required: {exc.claim}") from exc
    except jwt_exceptions.InvalidIssuerError as exc:
        raise InvalidTokenError("Invalid JWT issuer") from exc
    except jwt_exceptions.InvalidAudienceError as exc:
        raise InvalidTokenError("Invalid JWT audience") from exc
    except jwt_exceptions.InvalidSignatureError as exc:
        raise InvalidTokenError("Invalid JWT signature") from exc
    except jwt_exceptions.PyJWTError as exc:
        raise InvalidTokenError("Malformed JWT") from exc

    subject = payload.get("sub")
    expires_at = payload.get("exp")
    issuer = payload.get("iss")
    audience = payload.get("aud")
    if not isinstance(subject, str) or subject == "":
        raise InvalidTokenError("JWT subject claim is required")
    if not isinstance(expires_at, int):
        raise InvalidTokenError("JWT expiry claim is required")
    if not isinstance(issuer, str) or issuer == "":
        raise InvalidTokenError("JWT issuer claim is required")
    if not isinstance(audience, str) or audience == "":
        raise InvalidTokenError("JWT audience claim is required")

    return AccessTokenClaims(
        sub=subject,
        exp=expires_at,
        iss=issuer,
        aud=audience,
    )
