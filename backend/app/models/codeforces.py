"""
Codeforces integration ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class CodeforcesProfile(Base, UUIDMixin):
    """Stores cached Codeforces profile data for a linked user."""

    __tablename__ = "codeforces_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    handle: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_rating: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rank: Mapped[str | None] = mapped_column(String(100), nullable=True)
    max_rank: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # --- Relationships ---
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<CodeforcesProfile {self.handle} User: {self.user_id}>"


class CodeforcesContest(Base, UUIDMixin):
    """Stores historical contest participations of a linked user on Codeforces."""

    __tablename__ = "codeforces_contests"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    contest_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contest_name: Mapped[str] = mapped_column(String(255), nullable=False)
    handle: Mapped[str] = mapped_column(String(100), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_change: Mapped[int] = mapped_column(Integer, nullable=False)
    new_rating: Mapped[int] = mapped_column(Integer, nullable=False)
    contest_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # --- Relationships ---
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<CodeforcesContest {self.contest_id} User: {self.user_id} Rank: {self.rank}>"
