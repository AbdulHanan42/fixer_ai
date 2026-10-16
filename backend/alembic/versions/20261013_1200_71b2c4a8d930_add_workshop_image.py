"""add mechanic workshop image URL

Revision ID: 71b2c4a8d930
Revises: 8c2d5f91a710
Create Date: 2026-10-13 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "71b2c4a8d930"
down_revision: Union[str, Sequence[str], None] = "8c2d5f91a710"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mechanic_profiles", sa.Column("workshop_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("mechanic_profiles", "workshop_image_url")
