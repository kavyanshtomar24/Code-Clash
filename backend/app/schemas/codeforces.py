"""
Codeforces integration schemas.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CodeforcesProfileResponse(BaseModel):
    """Response representing cached Codeforces profile stats."""
    model_config = ConfigDict(from_attributes=True)

    handle: str
    rating: int
    max_rating: int
    rank: str | None = None
    max_rank: str | None = None
    last_synced_at: datetime


class CodeforcesContestResponse(BaseModel):
    """Response representing a Codeforces contest performance."""
    model_config = ConfigDict(from_attributes=True)

    contest_id: int
    contest_name: str
    handle: str
    rank: int
    rating_change: int
    new_rating: int
    contest_date: datetime


class CodeforcesLinkRequest(BaseModel):
    """Payload to link a Codeforces handle."""
    handle: str
