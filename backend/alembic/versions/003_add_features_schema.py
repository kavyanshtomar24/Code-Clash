"""add features schema

Revision ID: 003
Revises: 002
Create Date: 2026-07-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create rating_history table
    op.create_table(
        "rating_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("battle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("rating_change", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"], ondelete="SET NULL"),
    )
    # Create indexes on rating_history
    op.create_index("ix_rating_history_user_id", "rating_history", ["user_id"])
    op.create_index("ix_rating_history_battle_id", "rating_history", ["battle_id"])
    op.create_index("ix_rating_history_recorded_at", "rating_history", ["recorded_at"])

    # 2. Add indexes on submissions
    op.create_index("ix_submissions_user_submitted_at", "submissions", ["user_id", "submitted_at"])
    op.create_index("ix_submissions_problem_verdict", "submissions", ["problem_id", "verdict"])


def downgrade() -> None:
    op.drop_index("ix_submissions_problem_verdict", table_name="submissions")
    op.drop_index("ix_submissions_user_submitted_at", table_name="submissions")
    op.drop_table("rating_history")
