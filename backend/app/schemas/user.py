"""
User profile request and response schemas.

Separates full user data (private) from public-facing representations
and provides schemas for profile updates, statistics, and search results.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Full user profile (visible only to the account owner)."""

    id: uuid.UUID
    username: str
    email: str
    bio: str | None = None
    profile_picture: str | None = None
    codeforces_handle: str | None = None
    rating: int
    is_admin: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    """Public-facing user profile (email hidden)."""

    id: uuid.UUID
    username: str
    bio: str | None = None
    profile_picture: str | None = None
    codeforces_handle: str | None = None
    rating: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Editable profile fields (all optional, only set fields are applied)."""

    bio: str | None = None
    profile_picture: str | None = None
    codeforces_handle: str | None = None


class UserStatsResponse(BaseModel):
    """Aggregated statistics for the analytics dashboard."""

    total_solved: int = 0
    total_submissions: int = 0
    easy_solved: int = 0
    medium_solved: int = 0
    hard_solved: int = 0
    accuracy: float = 0.0
    recent_submissions: list = Field(default_factory=list)


class UserSearchResult(BaseModel):
    """Lightweight user representation for search results."""

    id: uuid.UUID
    username: str
    profile_picture: str | None = None
    rating: int

    model_config = ConfigDict(from_attributes=True)
