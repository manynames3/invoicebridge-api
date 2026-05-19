"""add region aware tenants

Revision ID: 0003_add_region_aware_tenants
Revises: 0002_add_processing_regions
Create Date: 2026-05-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_add_region_aware_tenants"
down_revision: str | None = "0002_add_processing_regions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("home_region", sa.String(length=60), nullable=False),
        sa.Column("data_residency_region", sa.String(length=60), nullable=False),
        sa.Column("failover_region", sa.String(length=60), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("tenant_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_home_region", "tenants", ["home_region"])
    op.create_index("ix_tenants_data_residency_region", "tenants", ["data_residency_region"])

    with op.batch_alter_table("invoices") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", sa.String(length=80), nullable=True))
        batch_op.create_foreign_key(
            "fk_invoices_tenant_id_tenants",
            "tenants",
            ["tenant_id"],
            ["id"],
        )
        batch_op.create_index("ix_invoices_tenant_id", ["tenant_id"])


def downgrade() -> None:
    with op.batch_alter_table("invoices") as batch_op:
        batch_op.drop_index("ix_invoices_tenant_id")
        batch_op.drop_constraint("fk_invoices_tenant_id_tenants", type_="foreignkey")
        batch_op.drop_column("tenant_id")
    op.drop_index("ix_tenants_data_residency_region", table_name="tenants")
    op.drop_index("ix_tenants_home_region", table_name="tenants")
    op.drop_table("tenants")
