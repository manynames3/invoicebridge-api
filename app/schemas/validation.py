from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    field: str | None = None
    message: str


class NormalizedTotals(BaseModel):
    tax_exclusive_amount: Decimal
    tax_amount: Decimal
    tax_inclusive_amount: Decimal
    payable_amount: Decimal
    currency: str


class InvoiceValidationResponse(BaseModel):
    compliant: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    normalized_totals: NormalizedTotals
    required_format: str
    country_profile_used: str
    idempotency_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
