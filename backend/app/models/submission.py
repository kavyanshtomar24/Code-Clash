"""
Submission and UserProblemStats ORM models.

Submission tracks every code submission a user makes to a problem.
UserProblemStats aggregates per-user-per-problem solve information.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.problem import Problem
    from app.models.user import User


class Submission(Base, UUIDMixin):
    """A single code submission against a problem."""

    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_user_problem", "user_id", "problem_id"),
        Index("ix_submissions_user_submitted_at", "user_id", "submitted_at"),
        Index("ix_submissions_problem_verdict", "problem_id", "verdict"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String(20), default="PENDING")
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_used_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    test_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # --- Relationships ---
    user: Mapped[User] = relationship(
        "User",
        back_populates="submissions",
    )
    problem: Mapped[Problem] = relationship(
        "Problem",
        back_populates="submissions",
    )

    def __repr__(self) -> str:
        return f"<Submission {self.id!r} verdict={self.verdict!r}>"


class UserProblemStats(Base, UUIDMixin):
    """Aggregated solve statistics per user per problem."""

    __tablename__ = "user_problem_stats"
    __table_args__ = (
        UniqueConstraint("user_id", "problem_id", name="uq_user_problem"),
        Index(
            "ix_user_problem_stats_solved_partial",
            "user_id",
            postgresql_where=text("solved = TRUE")
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="CASCADE"),
        nullable=False,
    )
    solved: Mapped[bool] = mapped_column(Boolean, default=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    first_solved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --- Relationships ---
    user: Mapped[User] = relationship(
        "User",
        back_populates="user_problem_stats",
    )
    problem: Mapped[Problem] = relationship(
        "Problem",
    )

    def __repr__(self) -> str:
        return (
            f"<UserProblemStats user={self.user_id!r} "
            f"problem={self.problem_id!r} solved={self.solved}>"
        )
