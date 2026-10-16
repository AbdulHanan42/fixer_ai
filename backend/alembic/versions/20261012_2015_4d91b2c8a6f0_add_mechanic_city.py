"""add city to mechanic profiles

Revision ID: 4d91b2c8a6f0
Revises: b38fa043c102
Create Date: 2026-10-12 20:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4d91b2c8a6f0"
down_revision: Union[str, Sequence[str], None] = "b38fa043c102"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mechanic_profiles", sa.Column("city", sa.String(length=100), nullable=True))
    op.create_index("ix_mechanic_profiles_city", "mechanic_profiles", ["city"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_mechanic_profiles_city", table_name="mechanic_profiles")
    op.drop_column("mechanic_profiles", "city")
