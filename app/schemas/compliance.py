from pydantic import BaseModel, Field


class ComplianceRequirementResponse(BaseModel):
    code: str
    status: str
    message: str
    evidence: dict[str, str | bool] = Field(default_factory=dict)


class CountryProductionReadinessResponse(BaseModel):
    country: str
    transaction_type: str
    profile_name: str
    production_ready: bool
    no_paid_network_path: bool
    required_format: str
    delivery_network: str
    requirements: list[ComplianceRequirementResponse]
    blocker_summary: list[str]


class OfficialValidationResponse(BaseModel):
    invoice_id: str
    validation_result_id: str | None = None
    country: str
    required_format: str
    validator_name: str
    configured: bool
    passed: bool
    exit_code: int | None = None
    message: str
    document_sha256: str | None = None
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None


class SpanishSIFResponsibleDeclarationResponse(BaseModel):
    invoice_id: str
    country: str
    status: str
    declaration_reference: str | None = None
    producer: dict[str, object]
    software: dict[str, object]
    statement: str
    external_requirements: list[str]
