"""
Coding battle schemas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator


class BattleCreateRequest(BaseModel):
    """Payload to create a new coding battle lobby."""
    problem_id: uuid.UUID
    duration_seconds: int = 1800
    opponent_username: str | None = None


class BattleResponse(BaseModel):
    """Detailed response for a battle."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_user_id: uuid.UUID
    host_username: str
    opponent_user_id: uuid.UUID | None = None
    opponent_username: str | None = None
    problem_id: uuid.UUID
    problem_title: str
    problem_slug: str
    status: str
    winner_id: uuid.UUID | None = None
    winner_username: str | None = None
    duration_seconds: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime


class BattleListItem(BaseModel):
    """Summary item for battle history / lobbies."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    host_username: str
    opponent_username: str | None = None
    problem_title: str
    status: str
    winner_username: str | None = None
    created_at: datetime


class BattleSubmitRequest(BaseModel):
    """Payload to submit a solution within a battle (problem_id comes from the battle)."""
    language: str
    source_code: str

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        allowed = {"python", "cpp", "java"}
        if v not in allowed:
            raise ValueError(f"Unsupported language '{v}'. Must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("source_code")
    @classmethod
    def validate_source_code(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Source code must not be empty")
        return v
