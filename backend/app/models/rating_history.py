"""
Rating history ORM model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class RatingHistory(Base, UUIDMixin):
    """Tracks historical rating changes for platform battles."""

    __tablename__ = "rating_history"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    battle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("battles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_change: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True
    )

    # --- Relationships ---
    user = relationship("User", foreign_keys=[user_id])
    battle = relationship("Battle", foreign_keys=[battle_id])

    def __repr__(self) -> str:
        return f"<RatingHistory User: {self.user_id} Rating: {self.rating} Change: {self.rating_change}>"
