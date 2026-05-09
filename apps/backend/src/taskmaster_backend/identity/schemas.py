"""API schemas for identity endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ApiErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)
    correlation_id: str
    field_errors: dict[str, list[str]] = Field(default_factory=dict)
    retry_after: int | None = None


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"]
    expires_in: int
