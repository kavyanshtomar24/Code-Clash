"""
Authentication API endpoints.

Provides registration, login, token refresh, and current-user retrieval.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new user account with hashed password storage."""
    user = await auth_service.register_user(db, data)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive tokens",
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate credentials and return an access / refresh token pair."""
    return await auth_service.authenticate_user(db, data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh(data: RefreshRequest):
    """Exchange a valid refresh token for a new token pair."""
    return await auth_service.refresh_access_token(data.refresh_token)


@router.post(
    "/logout",
    summary="Logout and revoke tokens",
)
async def logout(data: LogoutRequest):
    """Blacklist access and/or refresh tokens (JWT JTI revocation)."""
    if data.access_token:
        await auth_service.logout_token(data.access_token)
    if data.refresh_token:
        await auth_service.logout_token(data.refresh_token)
    return {"status": "success", "message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current user profile",
)
async def me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user
