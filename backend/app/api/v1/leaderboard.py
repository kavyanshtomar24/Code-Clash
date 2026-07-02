"""
Global leaderboard API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.services.leaderboard_service import get_global_leaderboard

router = APIRouter()


@router.get("/", summary="Global leaderboard top 100")
async def global_leaderboard(
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Return top users ranked by platform rating."""
    return await get_global_leaderboard(db, limit=limit)
