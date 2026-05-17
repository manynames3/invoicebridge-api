"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "country_profiles",
        sa.Column("id", sa.String(length=80), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("required_format", sa.String(length=120), nullable=False),
        sa.Column("delivery_network", sa.String(length=80), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("mandated", sa.Boolean(), nullable=False),
        sa.Column("pdf_allowed_as_compliant_invoice", sa.Boolean(), nullable=False),
        sa.Column("implementation_status", sa.String(length=80), nullable=False),
        sa.Column("profile_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_country_profiles_country", "country_profiles", ["country"])
    op.create_index("ix_country_profiles_transaction_type", "country_profiles", ["transaction_type"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("country", sa.String(length=2), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("seller_vat_id", sa.String(length=40), nullable=True),
        sa.Column("buyer_vat_id", sa.String(length=40), nullable=True),
        sa.Column("buyer_routing_id", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("validation_status", sa.String(length=40), nullable=False),
        sa.Column("delivery_status", sa.String(length=40), nullable=False),
        sa.Column("provider_reference", sa.String(length=120), nullable=True),
        sa.Column("required_format", sa.String(length=120), nullable=False),
        sa.Column("idempotency_key", sa.String(length=180), nullable=True),
        sa.Column("original_payload", sa.JSON(), nullable=False),
        sa.Column("transformed_xml", sa.Text(), nullable=True),
        sa.Column("validation_result", sa.JSON(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_invoices_country", "invoices", ["country"])
    op.create_index("ix_invoices_transaction_type", "invoices", ["transaction_type"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor", sa.String(length=80), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("event_metadata", sa.JSON(), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_invoice_id", "audit_events", ["invoice_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])

    op.create_table(
        "invoice_submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("network", sa.String(length=80), nullable=False),
        sa.Column("delivery_status", sa.String(length=40), nullable=False),
        sa.Column("provider_reference", sa.String(length=120), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=180), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_invoice_submissions_idempotency_key"),
    )
    op.create_index("ix_invoice_submissions_invoice_id", "invoice_submissions", ["invoice_id"])
    op.create_index("ix_invoice_submissions_provider_reference", "invoice_submissions", ["provider_reference"])

    op.create_table(
        "validation_results",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("compliant", sa.Boolean(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("warnings", sa.JSON(), nullable=False),
        sa.Column("normalized_totals", sa.JSON(), nullable=False),
        sa.Column("required_format", sa.String(length=120), nullable=False),
        sa.Column("country_profile_used", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_validation_results_invoice_id", "validation_results", ["invoice_id"])


def downgrade() -> None:
    op.drop_index("ix_validation_results_invoice_id", table_name="validation_results")
    op.drop_table("validation_results")
    op.drop_index("ix_invoice_submissions_provider_reference", table_name="invoice_submissions")
    op.drop_index("ix_invoice_submissions_invoice_id", table_name="invoice_submissions")
    op.drop_table("invoice_submissions")
    op.drop_index("ix_audit_events_event_type", table_name="audit_events")
    op.drop_index("ix_audit_events_invoice_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_invoices_invoice_number", table_name="invoices")
    op.drop_index("ix_invoices_transaction_type", table_name="invoices")
    op.drop_index("ix_invoices_country", table_name="invoices")
    op.drop_table("invoices")
    op.drop_index("ix_country_profiles_transaction_type", table_name="country_profiles")
    op.drop_index("ix_country_profiles_country", table_name="country_profiles")
    op.drop_table("country_profiles")
