from datetime import date

from pydantic import BaseModel


class MandateCheckResponse(BaseModel):
    country: str
    transaction_type: str
    mandated: bool
    effective_date: date | None
    required_format: str
    delivery_network: str
    pdf_allowed_as_compliant_invoice: bool
    notes: str
    implementation_status: str
    capabilities: list[str]
    production_readiness: str


class CountryProfileResponse(BaseModel):
    country: str
    transaction_types: list[str]
    network: str
    required_format: str
    implementation_status: str
    profile_name: str
    notes: str
    capabilities: list[str]
    production_readiness: str
