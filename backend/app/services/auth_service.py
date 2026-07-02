"""
Authentication service.

Handles user registration, credential verification, and JWT
token generation / refresh logic.
"""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.cache_service import cache_service


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    """Create a new user account."""
    stmt = select(User).where(
        or_(User.username == data.username, User.email == data.email)
    )
    result = await db.execute(stmt)
    existing = result.scalars().first()
    if existing is not None:
        if existing.username == data.username:
            raise ConflictException("Username is already taken")
        raise ConflictException("Email is already registered")

    is_admin = data.username in settings.ADMIN_USERNAMES

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        is_admin=is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _token_payload(user: User) -> dict:
    return {"sub": str(user.id), "username": user.username}


def _issue_tokens(user: User) -> TokenResponse:
    token_data = _token_payload(user)
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def authenticate_user(
    db: AsyncSession, data: LoginRequest
) -> TokenResponse:
    """Validate credentials and return a JWT token pair."""
    stmt = select(User).where(
        or_(
            User.username == data.username_or_email,
            User.email == data.username_or_email,
        )
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user is None or user.password_hash is None or not verify_password(
        data.password, user.password_hash
    ):
        raise UnauthorizedException("Invalid credentials")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return _issue_tokens(user)


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """Issue a new token pair from a valid refresh token."""
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise UnauthorizedException("Invalid token type — expected refresh token")

    jti = payload.get("jti")
    if jti and await cache_service.get(f"session:blacklist:{jti}"):
        raise UnauthorizedException("Token has been revoked")

    if jti:
        await blacklist_token_jti(jti, settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    token_data = {"sub": payload["sub"], "username": payload.get("username", "")}
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


async def logout_token(token: str) -> None:
    """Blacklist a token by its JTI claim."""
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti:
        return
    exp = payload.get("exp")
    ttl = 3600
    if exp:
        from datetime import datetime, timezone

        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 60)
    await blacklist_token_jti(jti, ttl)


async def blacklist_token_jti(jti: str, ttl: int) -> None:
    await cache_service.set(f"session:blacklist:{jti}", "1", ttl=ttl)


async def is_token_blacklisted(jti: str | None) -> bool:
    if not jti:
        return False
    return await cache_service.get(f"session:blacklist:{jti}") is not None


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User:
    """Fetch a user by primary key."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise UnauthorizedException("User not found")
    return user
