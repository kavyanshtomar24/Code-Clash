"""
Problem, Tag, ProblemTag, and TestCase ORM models.

Problem is the core entity around which the platform revolves.
Tags provide categorization via a many-to-many through ``ProblemTag``.
TestCases store judge I/O pairs linked to each problem.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_MEMORY_LIMIT_MB, DEFAULT_TIME_LIMIT_MS
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.submission import Submission


class ProblemTag(Base):
    """Association table linking problems to tags (many-to-many)."""

    __tablename__ = "problem_tags"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Tag(Base, UUIDMixin):
    """Problem categorization tag (e.g. DP, Greedy, Graph)."""

    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # --- Relationships ---
    problems: Mapped[list[Problem]] = relationship(
        "Problem",
        secondary="problem_tags",
        back_populates="tags",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name!r}>"


class Problem(Base, UUIDMixin):
    """A competitive programming problem."""

    __tablename__ = "problems"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input_format: Mapped[str] = mapped_column(Text, nullable=False)
    output_format: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    time_limit_ms: Mapped[int] = mapped_column(Integer, default=DEFAULT_TIME_LIMIT_MS)
    memory_limit_mb: Mapped[int] = mapped_column(Integer, default=DEFAULT_MEMORY_LIMIT_MB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # --- Relationships ---
    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary="problem_tags",
        back_populates="problems",
        lazy="selectin",
    )
    test_cases: Mapped[list[TestCase]] = relationship(
        "TestCase",
        back_populates="problem",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="problem",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Problem {self.slug!r}>"


class TestCase(Base, UUIDMixin):
    """Input / expected-output pair used for automated judging."""

    __tablename__ = "test_cases"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    input: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)

    # --- Relationships ---
    problem: Mapped[Problem] = relationship(
        "Problem",
        back_populates="test_cases",
    )

    def __repr__(self) -> str:
        return f"<TestCase problem={self.problem_id!r} sample={self.is_sample}>"
