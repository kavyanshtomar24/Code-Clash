"""
User profile and statistics API endpoints.

Provides public profile views, profile editing, stats dashboards,
and user search.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.user import (
    UserProfileUpdate,
    UserPublicResponse,
    UserResponse,
    UserSearchResult,
    UserStatsResponse,
)
from app.services import user_service

router = APIRouter()


@router.get(
    "/profile/{username}",
    response_model=UserPublicResponse,
    summary="Public user profile",
)
async def get_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch the public-facing profile of any user by username."""
    return await user_service.get_user_profile(db, username)


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="Update own profile",
)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Edit the authenticated user's bio, picture, or CF handle."""
    return await user_service.update_user_profile(db, current_user.id, data)


@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="Own statistics dashboard",
)
async def get_own_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated solve statistics for the authenticated user."""
    return await user_service.get_user_stats(db, current_user.id)


@router.get(
    "/stats/{username}",
    response_model=UserStatsResponse,
    summary="Public user statistics",
)
async def get_user_stats(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Return aggregated solve statistics for any user by username."""
    return await user_service.get_user_stats_by_username(db, username)


@router.get(
    "/search",
    response_model=list[UserSearchResult],
    summary="Search users",
)
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    db: AsyncSession = Depends(get_db),
):
    """Case-insensitive username search returning lightweight results."""
    return await user_service.search_users(db, q)


@router.get(
    "/rating-history",
    summary="Own rating history",
)
async def get_own_rating_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return chronological rating changes for the authenticated user."""
    from app.services.rating_history_service import get_rating_history
    return await get_rating_history(db, current_user.id)


@router.get(
    "/rating-history/{username}",
    summary="Public rating history",
)
async def get_user_rating_history(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """Return chronological rating changes for any user by username."""
    from app.services.rating_history_service import get_rating_history_by_username
    return await get_rating_history_by_username(db, username)


@router.get(
    "/battle-history",
    summary="Own battle history",
)
async def get_own_battle_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return paginated battle history for the authenticated user."""
    from app.services.battle_history_service import get_battle_history
    return await get_battle_history(db, current_user.id, page, per_page)
