from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.core.security import current_auth_context
from app.db.session import get_db
from app.schemas.audit import AuditTrailResponse
from app.schemas.compliance import OfficialValidationResponse, SpanishSIFResponsibleDeclarationResponse
from app.schemas.invoice import (
    ArchiveInvoiceRequest,
    ArchiveInvoiceResponse,
    CreateInvoiceRequest,
    InvoiceStatusResponse,
    NormalizedInvoiceInput,
    SendInvoiceRequest,
    SendInvoiceResponse,
    TransformInvoiceResponse,
)
from app.schemas.validation import InvoiceValidationResponse
from app.services.invoices import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


def service(request: Request, db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db, auth_context=current_auth_context(request))


@router.post(
    "/validate",
    response_model=InvoiceValidationResponse,
    summary="Validate a normalized invoice",
    description=(
        "Validates invoice JSON against the selected MVP country profile. Legal production support for Belgium, "
        "Poland, Romania, and Spain is coming soon; Germany is usable only when official XRechnung validation passes."
    ),
)
def validate_invoice(
    invoice: NormalizedInvoiceInput,
    invoice_service: InvoiceService = Depends(service),
) -> InvoiceValidationResponse:
    return invoice_service.validate(invoice)


@router.post(
    "/transform",
    response_model=TransformInvoiceResponse,
    responses={422: {"model": InvoiceValidationResponse}},
    summary="Transform a valid invoice into a structured document",
    description=(
        "Runs validation, stores the invoice and audit trail, and produces the configured MVP output format."
    ),
)
def transform_invoice(
    invoice: NormalizedInvoiceInput,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    invoice_service: InvoiceService = Depends(service),
) -> TransformInvoiceResponse | JSONResponse:
    result = invoice_service.transform(invoice, idempotency_key=idempotency_key)
    if isinstance(result, InvoiceValidationResponse):
        return JSONResponse(status_code=422, content=result.model_dump(mode="json"))
    return result


@router.post(
    "/send",
    response_model=SendInvoiceResponse,
    responses={422: {"model": InvoiceValidationResponse}},
    summary="Submit or record an invoice through the configured mock provider",
    description=(
        "Accepts an existing invoice_id or invoice payload, then records deterministic "
        "mock provider results for Peppol-style, no-network, local-record, or government-platform profiles."
    ),
)
def send_invoice(
    request: SendInvoiceRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    invoice_service: InvoiceService = Depends(service),
) -> SendInvoiceResponse | JSONResponse:
    result = invoice_service.send(request, idempotency_key=idempotency_key)
    if isinstance(result, InvoiceValidationResponse):
        return JSONResponse(status_code=422, content=result.model_dump(mode="json"))
    return result


@router.get(
    "/status/{invoice_id}",
    response_model=InvoiceStatusResponse,
    summary="Get invoice processing and delivery status",
    description="Returns validation, delivery, provider reference, and retry availability for an invoice.",
)
def invoice_status(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(service),
) -> InvoiceStatusResponse:
    return invoice_service.status(invoice_id)


@router.get(
    "/{invoice_id}/document",
    response_class=PlainTextResponse,
    summary="Download the transformed XML document",
    description=(
        "Returns the full transformed XML document stored for the invoice. "
        "Production reliance depends on the applicable official validator and provider configuration."
    ),
)
def transformed_document(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(service),
) -> PlainTextResponse:
    xml = invoice_service.transformed_document(invoice_id)
    return PlainTextResponse(content=xml, media_type="application/xml")


@router.post(
    "/{invoice_id}/official-validate",
    response_model=OfficialValidationResponse,
    summary="Run the configured official XML validator for an invoice",
    description=(
        "Runs the deployment-configured official validator command for the invoice country. "
        "If no validator command is configured, the response is explicit and does not mark the invoice compliant."
    ),
)
def official_validate_invoice(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(service),
) -> OfficialValidationResponse:
    return invoice_service.official_validate(invoice_id)


@router.get(
    "/{invoice_id}/spain/responsible-declaration",
    response_model=SpanishSIFResponsibleDeclarationResponse,
    summary="Generate Spain SIF responsible declaration draft evidence",
    description=(
        "Returns a draft evidence object for the Spain SIF responsible declaration. "
        "This is not a legal certification; the producer must review and issue the final declaration."
    ),
)
def spain_responsible_declaration(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(service),
) -> SpanishSIFResponsibleDeclarationResponse:
    return invoice_service.spain_responsible_declaration(invoice_id)


@router.post(
    "/{invoice_id}/archive",
    response_model=ArchiveInvoiceResponse,
    summary="Archive an invoice and optionally redact stored payloads",
    description=(
        "Marks an invoice archived and, by default, removes the stored original payload and transformed XML while "
        "preserving audit evidence and payload/document hashes."
    ),
)
def archive_invoice(
    invoice_id: str,
    request: ArchiveInvoiceRequest | None = None,
    invoice_service: InvoiceService = Depends(service),
) -> ArchiveInvoiceResponse:
    return invoice_service.archive(invoice_id, request or ArchiveInvoiceRequest())


@router.get(
    "/{invoice_id}/audit-trail",
    response_model=AuditTrailResponse,
    summary="Get invoice audit trail",
    description="Returns chronological audit events with metadata and payload hashes.",
)
def audit_trail(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(service),
) -> AuditTrailResponse:
    return invoice_service.audit_trail(invoice_id)


@router.post(
    "/create",
    response_model=TransformInvoiceResponse,
    responses={422: {"model": InvoiceValidationResponse}},
    summary="Create a simple compliant invoice object and transform it",
    description="Secondary MVP endpoint that builds a normalized invoice from seller, buyer, and line items.",
)
def create_invoice(
    request: CreateInvoiceRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    invoice_service: InvoiceService = Depends(service),
) -> TransformInvoiceResponse | JSONResponse:
    result = invoice_service.create_from_scratch(request, idempotency_key=idempotency_key)
    if isinstance(result, InvoiceValidationResponse):
        return JSONResponse(status_code=422, content=result.model_dump(mode="json"))
    return result
