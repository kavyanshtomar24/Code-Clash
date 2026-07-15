"""add rating and solved indexes

Revision ID: 002
Revises: 001
Create Date: 2026-07-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Index for rating-based sorting on users table
    op.create_index("ix_users_rating", "users", ["rating"])
    # 2. Partial index for solved count aggregation on user_problem_stats
    op.create_index(
        "ix_user_problem_stats_solved_partial",
        "user_problem_stats",
        ["user_id"],
        postgresql_where="solved = TRUE"
    )


def downgrade() -> None:
    op.drop_index("ix_users_rating", table_name="users")
    op.drop_index("ix_user_problem_stats_solved_partial", table_name="user_problem_stats")
