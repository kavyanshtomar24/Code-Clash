"""
User ORM model.

Represents a registered platform user with authentication credentials,
optional Codeforces integration, and relationships to submissions and stats.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_RATING
from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.submission import Submission, UserProblemStats


class User(Base, UUIDMixin):
    """Platform user account."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    profile_picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    codeforces_handle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rating: Mapped[int] = mapped_column(default=DEFAULT_RATING, index=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    # --- Relationships ---
    submissions: Mapped[list[Submission]] = relationship(
        "Submission",
        back_populates="user",
        lazy="selectin",
    )
    user_problem_stats: Mapped[list[UserProblemStats]] = relationship(
        "UserProblemStats",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.username!r}>"
