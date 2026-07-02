"""
Codeforces integration service.

Fetches data from the Codeforces public API, updates cached profiles,
syncs contest history, and links/unlinks user accounts.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.codeforces import CodeforcesContest, CodeforcesProfile
from app.models.user import User

logger = logging.getLogger(__name__)


async def fetch_cf_user_info(handle: str) -> dict:
    """Fetch user profile details from the Codeforces API."""
    url = f"{settings.CODEFORCES_API_URL}/user.info"
    params = {"handles": handle}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code != 200:
                raise BadRequestException(f"Codeforces API returned status {response.status_code}")
            data = response.json()
            if data.get("status") != "OK" or not data.get("result"):
                raise BadRequestException(f"Failed to fetch user info for handle '{handle}'")
            return data["result"][0]
    except httpx.RequestError as exc:
        logger.error("Network error while connecting to Codeforces: %s", exc)
        raise BadRequestException("Unable to reach Codeforces API. Please try again later.")


async def fetch_cf_user_rating(handle: str) -> list[dict]:
    """Fetch user contest history from the Codeforces API."""
    url = f"{settings.CODEFORCES_API_URL}/user.rating"
    params = {"handle": handle}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 400:
                # Handle has no contests or is invalid
                return []
            if response.status_code != 200:
                raise BadRequestException(f"Codeforces API returned status {response.status_code}")
            data = response.json()
            if data.get("status") != "OK":
                raise BadRequestException(f"Failed to fetch rating history for handle '{handle}'")
            return data.get("result", [])
    except httpx.RequestError as exc:
        logger.error("Network error while connecting to Codeforces: %s", exc)
        raise BadRequestException("Unable to reach Codeforces API. Please try again later.")


async def link_codeforces_handle(
    db: AsyncSession, user_id: uuid.UUID, handle: str
) -> CodeforcesProfile:
    """Link a Codeforces handle to a platform user and trigger initial sync."""
    # Check if handle is already linked to another user
    stmt = select(CodeforcesProfile).where(CodeforcesProfile.handle.ilike(handle))
    result = await db.execute(stmt)
    existing_profile = result.scalars().first()
    if existing_profile:
        if existing_profile.user_id == user_id:
            return existing_profile
        raise BadRequestException(f"Codeforces handle '{handle}' is already linked to another account")

    # Fetch initial data to verify handle exists
    cf_data = await fetch_cf_user_info(handle)
    verified_handle = cf_data["handle"]  # Keep original casing from CF

    # Find User and update the codeforces_handle on User model too
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    if not user:
        raise NotFoundException("User not found")

    user.codeforces_handle = verified_handle

    # Create profile
    profile_stmt = select(CodeforcesProfile).where(CodeforcesProfile.user_id == user_id)
    profile_res = await db.execute(profile_stmt)
    profile = profile_res.scalars().first()

    rating = cf_data.get("rating", 0)
    max_rating = cf_data.get("maxRating", 0)
    rank = cf_data.get("rank")
    max_rank = cf_data.get("maxRank")

    if profile:
        profile.handle = verified_handle
        profile.rating = rating
        profile.max_rating = max_rating
        profile.rank = rank
        profile.max_rank = max_rank
    else:
        profile = CodeforcesProfile(
            user_id=user_id,
            handle=verified_handle,
            rating=rating,
            max_rating=max_rating,
            rank=rank,
            max_rank=max_rank,
        )
        db.add(profile)

    user.rating = rating  # Set user rating to match Codeforces rating for rankings

    await db.commit()
    await db.refresh(profile)

    # Sync contest history in background / sequentially for initial setup
    await sync_codeforces_data(db, user_id)

    return profile


async def sync_codeforces_data(
    db: AsyncSession, user_id: uuid.UUID
) -> CodeforcesProfile:
    """Fetch fresh profile and contest data from Codeforces and update local db."""
    profile_stmt = select(CodeforcesProfile).where(CodeforcesProfile.user_id == user_id)
    profile_res = await db.execute(profile_stmt)
    profile = profile_res.scalars().first()
    if not profile:
        raise NotFoundException("No Codeforces handle linked to this account")

    # 1. Update profile info
    cf_data = await fetch_cf_user_info(profile.handle)
    profile.rating = cf_data.get("rating", 0)
    profile.max_rating = cf_data.get("maxRating", 0)
    profile.rank = cf_data.get("rank")
    profile.max_rank = cf_data.get("maxRank")
    profile.last_synced_at = datetime.utcnow()

    # Update User rating too
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    if user:
        user.rating = profile.rating

    # 2. Update contests
    contests_data = await fetch_cf_user_rating(profile.handle)

    # Delete existing contests for user to overwrite
    del_stmt = delete(CodeforcesContest).where(CodeforcesContest.user_id == user_id)
    await db.execute(del_stmt)

    for c in contests_data:
        contest_date = datetime.utcfromtimestamp(c["ratingUpdateTimeSeconds"])
        contest = CodeforcesContest(
            user_id=user_id,
            contest_id=c["contestId"],
            contest_name=c["contestName"],
            handle=c["handle"],
            rank=c["rank"],
            rating_change=c["newRating"] - c["oldRating"],
            new_rating=c["newRating"],
            contest_date=contest_date,
        )
        db.add(contest)

    await db.commit()
    await db.refresh(profile)
    return profile


async def get_codeforces_profile(
    db: AsyncSession, user_id: uuid.UUID
) -> CodeforcesProfile:
    """Retrieve the linked Codeforces profile."""
    stmt = select(CodeforcesProfile).where(CodeforcesProfile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()
    if not profile:
        raise NotFoundException("No Codeforces profile linked for this user")
    return profile


async def get_codeforces_contests(
    db: AsyncSession, user_id: uuid.UUID
) -> list[CodeforcesContest]:
    """Retrieve sync'ed Codeforces contest performances."""
    stmt = (
        select(CodeforcesContest)
        .where(CodeforcesContest.user_id == user_id)
        .order_by(CodeforcesContest.contest_date.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def unlink_codeforces_handle(
    db: AsyncSession, user_id: uuid.UUID
) -> None:
    """Unlink Codeforces handle and remove cached data."""
    # Find user
    user_stmt = select(User).where(User.id == user_id)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    if user:
        user.codeforces_handle = None

    # Delete profile and contests
    del_profile = delete(CodeforcesProfile).where(CodeforcesProfile.user_id == user_id)
    del_contests = delete(CodeforcesContest).where(CodeforcesContest.user_id == user_id)

    await db.execute(del_profile)
    await db.execute(del_contests)
    await db.commit()
