"""
Global leaderboard service backed by Redis sorted sets.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.cache_service import cache_service

LEADERBOARD_KEY = "leaderboard:global"
LEADERBOARD_TTL = 30


async def refresh_leaderboard(db: AsyncSession) -> None:
    """Rebuild the global top-100 leaderboard in Redis."""
    stmt = (
        select(User)
        .where(User.is_active.is_(True))
        .order_by(User.rating.desc())
        .limit(100)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    if users:
        mapping = {str(u.id): float(u.rating) for u in users}
        await cache_service.delete(LEADERBOARD_KEY)
        await cache_service.zadd(LEADERBOARD_KEY, mapping)
    await cache_service.set(f"{LEADERBOARD_KEY}:refreshed", "1", ttl=LEADERBOARD_TTL)


async def get_global_leaderboard(
    db: AsyncSession, limit: int = 100
) -> list[dict]:
    """Return top users by platform rating."""
    cached = await cache_service.get(f"{LEADERBOARD_KEY}:refreshed")
    if cached is None:
        await refresh_leaderboard(db)

    entries = await cache_service.zrevrange_with_scores(
        LEADERBOARD_KEY, 0, limit - 1
    )
    if not entries:
        await refresh_leaderboard(db)
        entries = await cache_service.zrevrange_with_scores(
            LEADERBOARD_KEY, 0, limit - 1
        )

    leaderboard = []
    for rank, (user_id_str, score) in enumerate(entries, start=1):
        uid = uuid.UUID(user_id_str)
        stmt = select(User).where(User.id == uid)
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user:
            leaderboard.append({
                "rank": rank,
                "user_id": user.id,
                "username": user.username,
                "rating": int(score),
                "profile_picture": user.profile_picture,
            })
    return leaderboard
