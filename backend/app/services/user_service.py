"""
User profile and statistics service.

Provides profile CRUD, aggregated solve statistics, and user search.
"""

from __future__ import annotations

import math
import uuid

from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Difficulty, Verdict
from app.core.exceptions import NotFoundException
from app.models.problem import Problem
from app.models.submission import Submission, UserProblemStats
from app.models.user import User
from app.schemas.user import UserProfileUpdate


async def get_user_profile(db: AsyncSession, username: str) -> User:
    """Fetch a user by username.

    Raises:
        NotFoundException: If the username does not exist.
    """
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise NotFoundException(f"User '{username}' not found")
    return user


async def update_user_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: UserProfileUpdate,
) -> User:
    """Apply non-null profile edits and return the updated user."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if user is None:
        raise NotFoundException("User not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def get_user_stats(db: AsyncSession, user_id: uuid.UUID) -> dict:
    """Compute aggregated statistics for the analytics dashboard.

    Returns a dict matching ``UserStatsResponse`` fields.
    """
    # Total submissions
    total_stmt = (
        select(func.count(Submission.id))
        .where(Submission.user_id == user_id)
    )
    total_result = await db.execute(total_stmt)
    total_submissions = total_result.scalar() or 0

    # Accepted count
    accepted_stmt = (
        select(func.count(Submission.id))
        .where(
            Submission.user_id == user_id,
            Submission.verdict == Verdict.ACCEPTED,
        )
    )
    accepted_result = await db.execute(accepted_stmt)
    accepted_count = accepted_result.scalar() or 0

    # Problems solved (unique, via user_problem_stats)
    solved_stmt = (
        select(func.count(UserProblemStats.id))
        .where(
            UserProblemStats.user_id == user_id,
            UserProblemStats.solved.is_(True),
        )
    )
    solved_result = await db.execute(solved_stmt)
    total_solved = solved_result.scalar() or 0

    # Solved per difficulty
    diff_stmt = (
        select(Problem.difficulty, func.count(UserProblemStats.id))
        .join(Problem, UserProblemStats.problem_id == Problem.id)
        .where(
            UserProblemStats.user_id == user_id,
            UserProblemStats.solved.is_(True),
        )
        .group_by(Problem.difficulty)
    )
    diff_result = await db.execute(diff_stmt)
    diff_map = {row[0]: row[1] for row in diff_result.all()}

    # Recent submissions (last 10)
    recent_stmt = (
        select(Submission)
        .where(Submission.user_id == user_id)
        .order_by(Submission.submitted_at.desc())
        .limit(10)
    )
    recent_result = await db.execute(recent_stmt)
    recent = recent_result.scalars().all()

    accuracy = (accepted_count / total_submissions * 100) if total_submissions > 0 else 0.0

    return {
        "total_solved": total_solved,
        "total_submissions": total_submissions,
        "easy_solved": diff_map.get(Difficulty.EASY, 0),
        "medium_solved": diff_map.get(Difficulty.MEDIUM, 0),
        "hard_solved": diff_map.get(Difficulty.HARD, 0),
        "accuracy": round(accuracy, 2),
        "recent_submissions": [
            {
                "id": str(s.id),
                "problem_id": str(s.problem_id),
                "language": s.language,
                "verdict": s.verdict,
                "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            }
            for s in recent
        ],
    }


async def get_user_stats_by_username(db: AsyncSession, username: str) -> dict:
    """Resolve a username to a user_id and return stats."""
    user = await get_user_profile(db, username)
    return await get_user_stats(db, user.id)


async def search_users(
    db: AsyncSession, query: str, limit: int = 20
) -> list[User]:
    """Search users by username (case-insensitive LIKE)."""
    stmt = (
        select(User)
        .where(User.username.ilike(f"%{query}%"))
        .order_by(User.rating.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())
