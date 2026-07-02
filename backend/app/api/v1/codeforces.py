"""
Codeforces integration API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.codeforces import (
    CodeforcesContestResponse,
    CodeforcesLinkRequest,
    CodeforcesProfileResponse,
)
from app.services import codeforces_service

router = APIRouter()


@router.post("/link", response_model=CodeforcesProfileResponse)
async def link_handle(
    payload: CodeforcesLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link a Codeforces handle to the user's profile and run initial sync."""
    profile = await codeforces_service.link_codeforces_handle(
        db=db, user_id=current_user.id, handle=payload.handle
    )
    return profile


@router.post("/sync", response_model=CodeforcesProfileResponse)
async def sync_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Force sync Codeforces profile and contest data with Codeforces API."""
    profile = await codeforces_service.sync_codeforces_data(
        db=db, user_id=current_user.id
    )
    return profile


@router.get("/profile", response_model=CodeforcesProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the cached Codeforces profile data."""
    profile = await codeforces_service.get_codeforces_profile(
        db=db, user_id=current_user.id
    )
    return profile


@router.get("/contests", response_model=list[CodeforcesContestResponse])
async def get_contests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the synced Codeforces contest performances."""
    contests = await codeforces_service.get_codeforces_contests(
        db=db, user_id=current_user.id
    )
    return contests


@router.delete("/unlink", response_model=dict)
async def unlink_handle(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlink Codeforces handle and delete cached data."""
    await codeforces_service.unlink_codeforces_handle(
        db=db, user_id=current_user.id
    )
    return {"status": "success", "message": "Codeforces account unlinked successfully"}
