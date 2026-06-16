"""ai_profiles

Revision ID: 0003_ai_profiles
Revises: 0002_student_profiles
Create Date: 2026-06-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ai_profiles"
down_revision: str | None = "0002_student_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _str_array():
    return sa.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "ai_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("personality_type", sa.String(length=80), nullable=False),
        sa.Column("strengths", _str_array(), nullable=False),
        sa.Column("weaknesses", _str_array(), nullable=False),
        sa.Column("recommendations", _str_array(), nullable=False),
        sa.Column("recommended_partner_type", sa.String(length=120), nullable=False),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_profiles_user_id"), "ai_profiles", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_profiles_user_id"), table_name="ai_profiles")
    op.drop_table("ai_profiles")
