"""
Submission request and response schemas.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreateRequest(BaseModel):
    """Payload for POST /api/v1/submissions/."""

    problem_id: uuid.UUID
    language: str
    source_code: str = Field(..., alias="code")

    model_config = ConfigDict(populate_by_name=True)


class SubmissionRunRequest(BaseModel):
    """Payload for POST /api/v1/submissions/run (sample execution)."""

    problem_id: uuid.UUID
    language: str
    source_code: str = Field(..., alias="code")
    input: str = ""

    model_config = ConfigDict(populate_by_name=True)


class SubmissionResponse(BaseModel):
    """Single submission record returned to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    problem_id: uuid.UUID
    language: str
    source_code: str
    verdict: str
    execution_time_ms: int | None = None
    memory_used_kb: int | None = None
    test_results: Any | None = None
    submitted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionListResponse(BaseModel):
    """Paginated submission history."""

    submissions: list[SubmissionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int = 0


class SubmissionRunResponse(BaseModel):
    """Result of a sample run against custom input."""

    stdout: str
    stderr: str
    verdict: str
    execution_time_ms: int
