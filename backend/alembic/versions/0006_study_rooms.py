"""study_rooms, room_members

Revision ID: 0006_study_rooms
Revises: 0005_user_rewards
Create Date: 2026-06-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_study_rooms"
down_revision: str | None = "0005_user_rewards"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "study_rooms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("max_users", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "room_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["study_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("room_id", "user_id", name="uq_room_member"),
    )
    op.create_index(op.f("ix_room_members_room_id"), "room_members", ["room_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_room_members_room_id"), table_name="room_members")
    op.drop_table("room_members")
    op.drop_table("study_rooms")
