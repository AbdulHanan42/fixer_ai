"""allow mechanics to create profile-specific services

Revision ID: 42d7f30a1c6b
Revises: 71b2c4a8d930
Create Date: 2026-10-14 09:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "42d7f30a1c6b"
down_revision: Union[str, Sequence[str], None] = "71b2c4a8d930"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("services_name_key", "services", type_="unique")
    op.add_column(
        "services",
        sa.Column("owner_mechanic_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_services_owner_mechanic_id_mechanic_profiles",
        "services",
        "mechanic_profiles",
        ["owner_mechanic_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "uq_services_catalog_name",
        "services",
        ["name"],
        unique=True,
        postgresql_where=sa.text("owner_mechanic_id IS NULL"),
    )
    op.create_index(
        "uq_services_mechanic_name",
        "services",
        ["owner_mechanic_id", "name"],
        unique=True,
        postgresql_where=sa.text("owner_mechanic_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_services_mechanic_name", table_name="services")
    op.drop_index("uq_services_catalog_name", table_name="services")
    op.drop_constraint("fk_services_owner_mechanic_id_mechanic_profiles", "services", type_="foreignkey")
    op.drop_column("services", "owner_mechanic_id")
    op.create_unique_constraint("services_name_key", "services", ["name"])
