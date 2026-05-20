from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import JSON as SQLJSON
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def uuid_string() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    home_region: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    data_residency_region: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    failover_region: Mapped[str | None] = mapped_column(String(60), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    tenant_metadata: Mapped[dict] = mapped_column(SQLJSON, nullable=False, default=dict)

    invoices: Mapped[list["Invoice"]] = relationship(back_populates="tenant")
    api_keys: Mapped[list["TenantApiKey"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class TenantApiKey(Base):
    __tablename__ = "tenant_api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="Default tenant key")
    key_prefix: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="api_keys")


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    tenant_id: Mapped[str | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    seller_vat_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    buyer_vat_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    buyer_routing_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="received", index=True)
    validation_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_validated")
    delivery_status: Mapped[str] = mapped_column(String(40), nullable=False, default="not_submitted")
    provider_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    required_format: Mapped[str] = mapped_column(String(120), nullable=False)
    processing_region: Mapped[str] = mapped_column(String(60), nullable=False, default="local-dev", index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(180), nullable=True, unique=True)
    idempotency_request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_payload: Mapped[dict] = mapped_column(SQLJSON, nullable=False)
    transformed_xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_result: Mapped[dict | None] = mapped_column(SQLJSON, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    submissions: Mapped[list["InvoiceSubmission"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", order_by="AuditEvent.created_at"
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    tenant: Mapped[Tenant | None] = relationship(back_populates="invoices")


class InvoiceSubmission(Base, TimestampMixin):
    __tablename__ = "invoice_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    network: Mapped[str] = mapped_column(String(80), nullable=False)
    delivery_status: Mapped[str] = mapped_column(String(40), nullable=False)
    provider_reference: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_region: Mapped[str] = mapped_column(String(60), nullable=False, default="local-dev", index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(180), nullable=True)
    idempotency_request_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_payload: Mapped[dict | None] = mapped_column(SQLJSON, nullable=True)
    response_payload: Mapped[dict] = mapped_column(SQLJSON, nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="submissions")

    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_invoice_submissions_idempotency_key"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    actor: Mapped[str] = mapped_column(String(80), nullable=False, default="system")
    event_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    processing_region: Mapped[str] = mapped_column(String(60), nullable=False, default="local-dev", index=True)
    event_metadata: Mapped[dict] = mapped_column(SQLJSON, nullable=False, default=dict)
    payload_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    invoice: Mapped[Invoice] = relationship(back_populates="audit_events")


class CountryProfile(Base, TimestampMixin):
    __tablename__ = "country_profiles"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    required_format: Mapped[str] = mapped_column(String(120), nullable=False)
    delivery_network: Mapped[str] = mapped_column(String(80), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    mandated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pdf_allowed_as_compliant_invoice: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    implementation_status: Mapped[str] = mapped_column(String(80), nullable=False)
    profile_metadata: Mapped[dict] = mapped_column(SQLJSON, nullable=False, default=dict)


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    errors: Mapped[list] = mapped_column(SQLJSON, nullable=False, default=list)
    warnings: Mapped[list] = mapped_column(SQLJSON, nullable=False, default=list)
    normalized_totals: Mapped[dict] = mapped_column(SQLJSON, nullable=False, default=dict)
    required_format: Mapped[str] = mapped_column(String(120), nullable=False)
    country_profile_used: Mapped[str] = mapped_column(String(80), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="validation_results")


class OfficialValidationResult(Base):
    __tablename__ = "official_validation_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_string)
    invoice_id: Mapped[str] = mapped_column(ForeignKey("invoices.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    required_format: Mapped[str] = mapped_column(String(120), nullable=False)
    validator_name: Mapped[str] = mapped_column(String(160), nullable=False)
    configured: Mapped[bool] = mapped_column(Boolean, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, index=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    stdout_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_sha256: Mapped[str] = mapped_column(String(128), nullable=False)
    processing_region: Mapped[str] = mapped_column(String(60), nullable=False, default="local-dev", index=True)

    invoice: Mapped[Invoice] = relationship()
