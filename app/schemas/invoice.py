from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.validation import InvoiceValidationResponse, ValidationIssue


class Party(BaseModel):
    name: str | None = None
    vat_id: str | None = None
    country_code: str | None = "BE"
    routing_id: str | None = None
    peppol_id: str | None = None
    address: dict[str, Any] | None = None


class InvoiceLine(BaseModel):
    line_id: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    vat_rate: Decimal | None = None
    line_extension_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None

    @field_validator(
        "quantity",
        "unit_price",
        "vat_rate",
        "line_extension_amount",
        "tax_amount",
        "total_amount",
        mode="before",
    )
    @classmethod
    def coerce_decimal(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


class InvoiceTotals(BaseModel):
    tax_exclusive_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    tax_inclusive_amount: Decimal | None = None
    payable_amount: Decimal | None = None


class NormalizedInvoiceInput(BaseModel):
    tenant_id: str | None = None
    country: str | None = "BE"
    transaction_type: str | None = "B2B"
    invoice_number: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    currency: str | None = "EUR"
    seller: Party | None = None
    buyer: Party | None = None
    lines: list[InvoiceLine] = Field(default_factory=list)
    totals: InvoiceTotals | None = None
    payment_terms: str | None = None
    idempotency_key: str | None = None
    simulate_rejection: bool = False
    simulate_pending: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransformInvoiceResponse(BaseModel):
    invoice_id: str
    tenant_id: str | None = None
    status: str
    format: str
    processing_region: str
    xml_preview: str
    warnings: list[ValidationIssue]
    audit_log_id: str


class SendInvoiceRequest(BaseModel):
    invoice_id: str | None = None
    invoice: NormalizedInvoiceInput | None = None
    simulate_rejection: bool = False
    simulate_pending: bool = False
    idempotency_key: str | None = None


class SendInvoiceResponse(BaseModel):
    invoice_id: str
    tenant_id: str | None = None
    submission_id: str
    network: str
    delivery_status: str
    provider_reference: str
    processing_region: str
    rejection_reason: str | None = None
    audit_log_id: str


class InvoiceStatusResponse(BaseModel):
    invoice_id: str
    tenant_id: str | None = None
    current_status: str
    validation_status: str
    delivery_status: str
    provider_reference: str | None = None
    processing_region: str
    created_at: datetime
    updated_at: datetime
    last_error: str | None = None
    retry_available: bool


class CreateInvoiceItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate: Decimal = Decimal("21")


class CreateInvoiceRequest(BaseModel):
    tenant_id: str | None = None
    seller_id: str
    buyer_id: str
    items: list[CreateInvoiceItem]
    currency: str = "EUR"
    payment_terms: str | None = "Payment due within 30 days"
    idempotency_key: str | None = None


class ValidationErrorEnvelope(BaseModel):
    detail: str
    validation: InvoiceValidationResponse
