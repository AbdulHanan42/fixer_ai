"""add AI diagnosis details

Revision ID: 8c2d5f91a710
Revises: 4d91b2c8a6f0
Create Date: 2026-10-13 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "8c2d5f91a710"
down_revision: Union[str, Sequence[str], None] = "4d91b2c8a6f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ai_diagnoses", sa.Column("user_description", sa.Text(), nullable=True))
    op.add_column("ai_diagnoses", sa.Column("ai_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("ai_diagnoses", sa.Column("recommended_service", sa.String(), nullable=True))
    op.add_column(
        "ai_diagnoses",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("ai_diagnoses", "created_at")
    op.drop_column("ai_diagnoses", "recommended_service")
    op.drop_column("ai_diagnoses", "ai_analysis")
    op.drop_column("ai_diagnoses", "user_description")
