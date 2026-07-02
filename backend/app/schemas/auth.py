"""
Authentication request and response schemas.
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload for POST /api/v1/auth/register."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Payload for POST /api/v1/auth/login."""

    username_or_email: str
    password: str


class TokenResponse(BaseModel):
    """JWT token pair returned on successful authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Payload for POST /api/v1/auth/refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Payload for POST /api/v1/auth/logout."""

    access_token: str | None = None
    refresh_token: str | None = None


class TokenPayload(BaseModel):
    """Decoded JWT payload claims."""

    sub: str
    exp: int | None = None
    type: str = "access"
    username: str | None = None
