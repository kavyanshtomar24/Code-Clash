"""
Notification ORM model.
"""

from __future__ import annotations

import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class Notification(Base, UUIDMixin):
    """Represents a system or social notification sent to a user."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # friend_request, battle, verdict, system
    reference_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # ID of related object (e.g. battle_id)

    # --- Relationships ---
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Notification {self.id} for User: {self.user_id} [Read: {self.is_read}]>"
