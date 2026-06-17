"""user_rewards

Revision ID: 0005_user_rewards
Revises: 0004_activity_tasks_focus
Create Date: 2026-06-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_user_rewards"
down_revision: str | None = "0004_activity_tasks_focus"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_rewards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("xp", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("garden_stage", sa.String(length=24), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_rewards_user_id"), "user_rewards", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_rewards_user_id"), table_name="user_rewards")
    op.drop_table("user_rewards")
