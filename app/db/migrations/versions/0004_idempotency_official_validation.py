"""add idempotency hashes and official validation results

Revision ID: 0004_idempotency_official_validation
Revises: 0003_add_region_aware_tenants
Create Date: 2026-05-20
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_idempotency_official_validation"
down_revision: str | None = "0003_add_region_aware_tenants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("invoices", sa.Column("idempotency_request_hash", sa.String(length=128), nullable=True))
    op.add_column("invoice_submissions", sa.Column("idempotency_request_hash", sa.String(length=128), nullable=True))

    op.create_table(
        "official_validation_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("required_format", sa.String(length=120), nullable=False),
        sa.Column("validator_name", sa.String(length=160), nullable=False),
        sa.Column("configured", sa.Boolean(), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("stdout_excerpt", sa.Text(), nullable=True),
        sa.Column("stderr_excerpt", sa.Text(), nullable=True),
        sa.Column("document_sha256", sa.String(length=128), nullable=False),
        sa.Column("processing_region", sa.String(length=60), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_official_validation_results_invoice_id", "official_validation_results", ["invoice_id"])
    op.create_index("ix_official_validation_results_country", "official_validation_results", ["country"])
    op.create_index("ix_official_validation_results_passed", "official_validation_results", ["passed"])
    op.create_index(
        "ix_official_validation_results_processing_region",
        "official_validation_results",
        ["processing_region"],
    )


def downgrade() -> None:
    op.drop_index("ix_official_validation_results_processing_region", table_name="official_validation_results")
    op.drop_index("ix_official_validation_results_passed", table_name="official_validation_results")
    op.drop_index("ix_official_validation_results_country", table_name="official_validation_results")
    op.drop_index("ix_official_validation_results_invoice_id", table_name="official_validation_results")
    op.drop_table("official_validation_results")

    op.drop_column("invoice_submissions", "idempotency_request_hash")
    op.drop_column("invoices", "idempotency_request_hash")
