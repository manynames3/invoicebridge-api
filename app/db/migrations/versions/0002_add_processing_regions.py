"""add processing region columns

Revision ID: 0002_add_processing_regions
Revises: 0001_initial
Create Date: 2026-05-19
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_add_processing_regions"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "invoices",
        sa.Column("processing_region", sa.String(length=60), server_default="local-dev", nullable=False),
    )
    op.create_index("ix_invoices_processing_region", "invoices", ["processing_region"])

    op.add_column(
        "invoice_submissions",
        sa.Column("processing_region", sa.String(length=60), server_default="local-dev", nullable=False),
    )
    op.create_index("ix_invoice_submissions_processing_region", "invoice_submissions", ["processing_region"])

    op.add_column(
        "audit_events",
        sa.Column("processing_region", sa.String(length=60), server_default="local-dev", nullable=False),
    )
    op.create_index("ix_audit_events_processing_region", "audit_events", ["processing_region"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_processing_region", table_name="audit_events")
    op.drop_column("audit_events", "processing_region")
    op.drop_index("ix_invoice_submissions_processing_region", table_name="invoice_submissions")
    op.drop_column("invoice_submissions", "processing_region")
    op.drop_index("ix_invoices_processing_region", table_name="invoices")
    op.drop_column("invoices", "processing_region")
