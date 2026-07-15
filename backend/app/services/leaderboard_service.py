"""
Global leaderboard service — production-quality SQL implementation.

Uses a CTE with DENSE_RANK() window function to compute global ranks,
LEFT JOIN subquery with COUNT(DISTINCT) for solved counts, and supports
pagination, search filtering, and multi-column sorting.

SQL Concepts Used:
- CTE (Common Table Expression): Encapsulates the ranked dataset so that
  search filters do not recalculate ranks within the filtered subset.
- DENSE_RANK() OVER (...): Window function that assigns consecutive ranks
  without gaps to users sharing the same rating/solved count.
- LEFT JOIN subquery: Aggregates solved counts separately, then joins to
  the users table. This avoids grouping on every user column.
- COUNT(DISTINCT problem_id): Ensures duplicate acceptances for the same
  problem are not double-counted.
- COALESCE: Replaces NULL (users with 0 solves) with 0.
- ILIKE: Case-insensitive pattern matching for username search.
- LIMIT / OFFSET: Server-side pagination.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import UserProblemStats
from app.models.user import User


async def get_global_leaderboard(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    search: str | None = None,
    sort_by: str = "rating",
) -> dict:
    """Return a paginated, filterable, ranked leaderboard.

    Parameters
    ----------
    db : AsyncSession
        Active database session.
    page : int
        1-indexed page number (default 1).
    per_page : int
        Number of rows per page (default 20, max 100).
    search : str | None
        Optional username substring filter (case-insensitive).
    sort_by : str
        Sort column — ``"rating"`` (default) or ``"solved"``.

    Returns
    -------
    dict
        ``{"users": [...], "total_users": int, "page": int,
          "per_page": int, "total_pages": int}``
    """
    per_page = min(per_page, 100)

    # ── 1. Subquery: aggregate distinct solved counts per user ──────────
    solved_sq = (
        select(
            UserProblemStats.user_id,
            func.count(func.distinct(UserProblemStats.problem_id)).label(
                "solved_count"
            ),
        )
        .where(UserProblemStats.solved.is_(True))
        .group_by(UserProblemStats.user_id)
        .subquery("solved_agg")
    )

    # ── 2. CTE: join users ↔ solved_agg, compute DENSE_RANK() ──────────
    total_solved_col = func.coalesce(solved_sq.c.solved_count, 0).label(
        "total_solved"
    )

    ranked_cte = (
        select(
            User.id,
            User.username,
            User.rating,
            User.profile_picture,
            User.codeforces_handle,
            total_solved_col,
            func.dense_rank()
            .over(
                order_by=(
                    User.rating.desc(),
                    func.coalesce(solved_sq.c.solved_count, 0).desc(),
                    User.username.asc(),
                )
            )
            .label("global_rank"),
        )
        .outerjoin(solved_sq, User.id == solved_sq.c.user_id)
        .where(User.is_active.is_(True))
        .cte("ranked_users")
    )

    # ── 3. Select from CTE with optional search filter ──────────────────
    query = select(ranked_cte)

    if search:
        query = query.where(ranked_cte.c.username.ilike(f"%{search}%"))

    # Secondary sort (re-orders the page, global_rank is preserved)
    if sort_by == "solved":
        query = query.order_by(
            ranked_cte.c.total_solved.desc(),
            ranked_cte.c.rating.desc(),
            ranked_cte.c.username.asc(),
        )
    else:
        query = query.order_by(ranked_cte.c.global_rank.asc())

    # ── 4. Pagination metadata ──────────────────────────────────────────
    count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * per_page
    query = query.limit(per_page).offset(offset)

    # ── 5. Execute and build response ───────────────────────────────────
    rows = (await db.execute(query)).all()

    users = [
        {
            "rank": row.global_rank,
            "user_id": row.id,
            "username": row.username,
            "rating": row.rating,
            "profile_picture": row.profile_picture,
            "codeforces_handle": row.codeforces_handle,
            "total_solved": row.total_solved,
        }
        for row in rows
    ]

    return {
        "users": users,
        "total_users": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total_count + per_page - 1) // per_page),
    }
