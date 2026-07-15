"""
Global leaderboard API endpoints.

Supports pagination, search filtering, and multi-column sorting.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.leaderboard_service import get_global_leaderboard

router = APIRouter()


@router.get("/", summary="Global leaderboard (paginated)")
async def global_leaderboard(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Rows per page"),
    search: str | None = Query(None, max_length=50, description="Username search filter"),
    sort_by: str = Query("rating", pattern="^(rating|solved)$", description="Sort by 'rating' or 'solved'"),
    db: AsyncSession = Depends(get_db),
):
    """Return a paginated global leaderboard ranked by platform rating.

    Uses SQL window functions (DENSE_RANK) for rank computation and
    supports optional username search and alternate sort orders.
    """
    return await get_global_leaderboard(
        db,
        page=page,
        per_page=per_page,
        search=search,
        sort_by=sort_by,
    )
