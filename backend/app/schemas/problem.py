"""
Problem, Tag, and TestCase request/response schemas.

Provides list-level summaries for browsing, full detail views for the
problem page, and creation payloads for seeding or admin endpoints.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagResponse(BaseModel):
    """Tag metadata returned inside problem responses."""

    id: uuid.UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class TestCaseResponse(BaseModel):
    """Sample test case shown on the problem detail page."""

    id: uuid.UUID
    input: str
    expected_output: str
    is_sample: bool

    model_config = ConfigDict(from_attributes=True)


class TestCaseCreate(BaseModel):
    """Payload for creating a test case alongside a problem."""

    input: str
    expected_output: str
    is_sample: bool = False


class ProblemListItem(BaseModel):
    """Compact problem representation for the problem-list page."""

    id: uuid.UUID
    title: str
    slug: str
    difficulty: str
    tags: list[TagResponse] = Field(default_factory=list)
    solved_by_user: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class ProblemDetailResponse(BaseModel):
    """Full problem detail including sample test cases."""

    id: uuid.UUID
    title: str
    slug: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    difficulty: str
    tags: list[TagResponse] = Field(default_factory=list)
    test_cases: list[TestCaseResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProblemCreateRequest(BaseModel):
    """Payload for creating a new problem."""

    title: str
    description: str
    input_format: str
    output_format: str
    constraints: str
    difficulty: str
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    tag_ids: list[uuid.UUID] = Field(default_factory=list)
    test_cases: list[TestCaseCreate] = Field(default_factory=list)


class ProblemFilterParams(BaseModel):
    """Query parameters for filtering and paginating the problem list."""

    difficulty: str | None = None
    tag: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
