"""
Analytics and dashboard statistics API endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.analytics import (
    DashboardAnalyticsResponse,
    DifficultyBreakdown,
    SubmissionHeatmap,
    TopicPerformance,
    WeakAreaAnalysis,
)
from app.services import analytics_service

router = APIRouter()


async def _get_analytics(db: AsyncSession, user_id):
    return await analytics_service.get_dashboard_analytics(db=db, user_id=user_id)


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
@router.get("/", response_model=DashboardAnalyticsResponse)
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the aggregated dashboard analytics payload."""
    return await _get_analytics(db, current_user.id)


@router.get("/topics", response_model=list[TopicPerformance])
@router.get("/topic-performance", response_model=list[TopicPerformance])
async def get_topic_performance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve solve statistics per problem topic/tag."""
    analytics = await _get_analytics(db, current_user.id)
    return analytics["topic_performance"]


@router.get("/submission-heatmap", response_model=list[SubmissionHeatmap])
async def get_submission_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve daily submission counts for heatmap calendar visualization."""
    analytics = await _get_analytics(db, current_user.id)
    return analytics["submission_heatmap"]


@router.get("/difficulty-breakdown", response_model=DifficultyBreakdown)
async def get_difficulty_breakdown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve solve stats categorized by easy/medium/hard difficulties."""
    analytics = await _get_analytics(db, current_user.id)
    return analytics["difficulty_breakdown"]


@router.get("/weak-areas", response_model=list[WeakAreaAnalysis])
async def get_weak_areas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve weak topics diagnostic along with practice suggestions."""
    analytics = await _get_analytics(db, current_user.id)
    return analytics["weak_areas"]
