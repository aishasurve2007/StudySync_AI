"""student_profiles

Revision ID: 0002_student_profiles
Revises: 0001_initial
Create Date: 2026-06-14
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_student_profiles"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _str_array():
    # text[] on Postgres, JSON elsewhere (mirrors the model's variant)
    return sa.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("course", sa.String(length=160), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("subjects", _str_array(), nullable=False),
        sa.Column("learning_style", sa.String(length=32), nullable=False),
        sa.Column("preferred_study_time", sa.String(length=32), nullable=False),
        sa.Column("study_environment", sa.String(length=32), nullable=False),
        sa.Column("study_intensity", sa.String(length=32), nullable=False),
        sa.Column("current_goal", sa.String(length=280), nullable=True),
        sa.Column("goal_tags", _str_array(), nullable=False),
        sa.Column("daily_goal_hours", sa.Float(), nullable=False),
        sa.Column("motivation_type", sa.String(length=32), nullable=True),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_student_profiles_user_id"), "student_profiles", ["user_id"], unique=True)
    op.create_index(op.f("ix_student_profiles_course"), "student_profiles", ["course"])

    # GIN index for fast array-overlap (subjects && subjects) in the matching
    # candidate pre-filter (§4). Postgres-only; skipped on other dialects.
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.create_index(
            "ix_student_profiles_subjects_gin",
            "student_profiles",
            ["subjects"],
            postgresql_using="gin",
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.drop_index("ix_student_profiles_subjects_gin", table_name="student_profiles")
    op.drop_index(op.f("ix_student_profiles_course"), table_name="student_profiles")
    op.drop_index(op.f("ix_student_profiles_user_id"), table_name="student_profiles")
    op.drop_table("student_profiles")
