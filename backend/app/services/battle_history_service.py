"""
Battle history service.

Multi-table JOIN query to fetch paginated battle history with
opponent details, problem info, outcome, and rating changes.
"""

from __future__ import annotations

import math
import uuid

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.battle import Battle
from app.models.problem import Problem
from app.models.rating_history import RatingHistory
from app.models.user import User


async def get_battle_history(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    """Return paginated battle history for a user.

    Uses multi-table JOINs to fetch:
    - Opponent username and profile picture
    - Problem title and slug
    - Win/Loss/Draw outcome
    - Rating change from that battle
    """
    # Aliases for host and opponent user lookups
    HostUser = User.__table__.alias("host_user")
    OpponentUser = User.__table__.alias("opponent_user")

    # Subquery for rating change in this battle for this user
    rating_sq = (
        select(RatingHistory.rating_change)
        .where(
            RatingHistory.user_id == user_id,
            RatingHistory.battle_id == Battle.id,
        )
        .correlate(Battle)
        .limit(1)
        .scalar_subquery()
        .label("rating_change")
    )

    # Base query: battles where user is host or opponent, status = finished
    base = (
        select(
            Battle.id,
            Battle.status,
            Battle.winner_id,
            Battle.duration_seconds,
            Battle.started_at,
            Battle.ended_at,
            Battle.host_user_id,
            Battle.opponent_user_id,
            Problem.title.label("problem_title"),
            Problem.slug.label("problem_slug"),
            rating_sq,
        )
        .join(Problem, Battle.problem_id == Problem.id)
        .where(
            or_(
                Battle.host_user_id == user_id,
                Battle.opponent_user_id == user_id,
            ),
            Battle.status == "finished",
        )
    )

    # Count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    stmt = base.order_by(Battle.ended_at.desc()).offset(offset).limit(per_page)
    rows = (await db.execute(stmt)).all()

    # Fetch opponent usernames in bulk
    opponent_ids = set()
    for row in rows:
        if row.host_user_id == user_id:
            if row.opponent_user_id:
                opponent_ids.add(row.opponent_user_id)
        else:
            opponent_ids.add(row.host_user_id)

    username_map: dict[uuid.UUID, dict] = {}
    if opponent_ids:
        users_stmt = select(User.id, User.username, User.profile_picture).where(
            User.id.in_(list(opponent_ids))
        )
        users_res = (await db.execute(users_stmt)).all()
        for u in users_res:
            username_map[u.id] = {"username": u.username, "profile_picture": u.profile_picture}

    battles = []
    for row in rows:
        opp_id = row.opponent_user_id if row.host_user_id == user_id else row.host_user_id
        opp_info = username_map.get(opp_id, {"username": "Unknown", "profile_picture": None})

        if row.winner_id == user_id:
            outcome = "won"
        elif row.winner_id is None:
            outcome = "draw"
        else:
            outcome = "lost"

        battles.append({
            "battle_id": row.id,
            "opponent_username": opp_info["username"],
            "opponent_picture": opp_info["profile_picture"],
            "problem_title": row.problem_title,
            "problem_slug": row.problem_slug,
            "outcome": outcome,
            "rating_change": row.rating_change or 0,
            "duration_seconds": row.duration_seconds,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "ended_at": row.ended_at.isoformat() if row.ended_at else None,
        })

    return {
        "battles": battles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, math.ceil(total / per_page)),
    }
