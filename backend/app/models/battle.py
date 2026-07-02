"""
Coding battle ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class Battle(Base, UUIDMixin):
    """Represents a competitive coding battle between two users."""

    __tablename__ = "battles"

    host_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    opponent_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    problem_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("problems.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, index=True
    )
    winner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, default=1800, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    host = relationship("User", foreign_keys=[host_user_id])
    opponent = relationship("User", foreign_keys=[opponent_user_id])
    winner = relationship("User", foreign_keys=[winner_id])
    problem = relationship("Problem")
    submissions = relationship("BattleSubmission", back_populates="battle", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Battle {self.id} | {self.status} | Host: {self.host_user_id} vs Opponent: {self.opponent_user_id}>"


class BattleSubmission(Base, UUIDMixin):
    """Links a user's code submission to a specific battle."""

    __tablename__ = "battle_submissions"

    battle_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("battles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Relationships ---
    battle = relationship("Battle", back_populates="submissions")
    user = relationship("User")
    submission = relationship("Submission")

    def __repr__(self) -> str:
        return f"<BattleSubmission Battle: {self.battle_id} User: {self.user_id} Sub: {self.submission_id}>"
