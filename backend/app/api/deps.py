"""
FastAPI dependency injection functions.

Provides reusable Depends() callables for database sessions and
authenticated user extraction across all route handlers.
"""

import uuid

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.session import get_async_session
from app.services.auth_service import get_user_by_id, is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login/oauth"
)


async def get_db():
    """Yield an async database session."""
    async for session in get_async_session():
        yield session


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Extract and validate the authenticated user from the Bearer token."""

    payload = decode_token(token)

    if await is_token_blacklisted(payload.get("jti")):
        raise UnauthorizedException("Token has been revoked")

    user_id_str: str | None = payload.get("sub")

    if user_id_str is None:
        raise UnauthorizedException("Token payload missing 'sub' claim")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException("Invalid user ID in token")

    user = await get_user_by_id(db, user_id)

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return user


async def get_current_admin(
    current_user=Depends(get_current_user),
):
    """Require an admin user."""

    if not current_user.is_admin:
        raise ForbiddenException("Admin privileges required")

    return current_user


async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Try to extract the authenticated user; return None on failure."""

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    if not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ", 1)[1]

    try:
        payload = decode_token(token)

        if await is_token_blacklisted(payload.get("jti")):
            return None

        user_id_str = payload.get("sub")

        if user_id_str is None:
            return None

        user_id = uuid.UUID(user_id_str)

        return await get_user_by_id(db, user_id)

    except Exception:
        return None