"""add mechanic availability

Revision ID: b38fa043c102
Revises: 702126eb2483
Create Date: 2026-10-12 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b38fa043c102"
down_revision: Union[str, Sequence[str], None] = "702126eb2483"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mechanic_profiles",
        sa.Column("is_online", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("mechanic_profiles", "is_online")
