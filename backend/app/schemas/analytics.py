"""
Analytics and performance tracking schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TopicPerformance(BaseModel):
    """Detailed solve statistics per problem tag/topic."""
    model_config = ConfigDict(from_attributes=True)

    tag_name: str
    solved_count: int
    attempt_count: int
    accuracy: float


class SubmissionHeatmap(BaseModel):
    """Daily submission activity counts for GitHub-style contribution heatmaps."""
    model_config = ConfigDict(from_attributes=True)

    date: str  # YYYY-MM-DD
    count: int


class DifficultyBreakdown(BaseModel):
    """Solve counts grouped by problem difficulty level."""
    model_config = ConfigDict(from_attributes=True)

    easy_solved: int
    medium_solved: int
    hard_solved: int
    easy_total: int
    medium_total: int
    hard_total: int


class WeakAreaAnalysis(BaseModel):
    """Weakness diagnosis per tag/topic with recommended actions."""
    model_config = ConfigDict(from_attributes=True)

    tag_name: str
    accuracy: float
    solved_count: int
    attempt_count: int
    suggestion: str


class DashboardAnalyticsResponse(BaseModel):
    """Aggregated analytics payload for the user dashboard."""
    model_config = ConfigDict(from_attributes=True)

    topic_performance: list[TopicPerformance]
    submission_heatmap: list[SubmissionHeatmap]
    difficulty_breakdown: DifficultyBreakdown
    weak_areas: list[WeakAreaAnalysis]
