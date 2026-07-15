"""
Rating history service.

Fetches chronological rating changes for users from the rating_history table.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.rating_history import RatingHistory
from app.models.user import User


async def get_rating_history(
    db: AsyncSession, user_id: uuid.UUID
) -> list[dict]:
    """Return chronological rating history for a user."""
    stmt = (
        select(RatingHistory)
        .where(RatingHistory.user_id == user_id)
        .order_by(RatingHistory.recorded_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        {
            "id": row.id,
            "rating": row.rating,
            "rating_change": row.rating_change,
            "battle_id": row.battle_id,
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
        }
        for row in rows
    ]


async def get_rating_history_by_username(
    db: AsyncSession, username: str
) -> list[dict]:
    """Return chronological rating history by username lookup."""
    user_stmt = select(User).where(User.username == username)
    user_res = await db.execute(user_stmt)
    user = user_res.scalars().first()
    if not user:
        raise NotFoundException("User not found")
    return await get_rating_history(db, user.id)
