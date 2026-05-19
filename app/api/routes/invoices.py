from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.audit import AuditTrailResponse
from app.schemas.invoice import (
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


def service(db: Session = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


@router.post(
    "/validate",
    response_model=InvoiceValidationResponse,
    summary="Validate a normalized invoice",
    description=(
        "Validates invoice JSON against the selected MVP country profile. Belgium uses a Peppol-style "
        "sandbox profile; Germany and Spain use no-network sandbox profiles."
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
    summary="Transform a valid invoice into a sandbox structured document",
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
        "sandbox provider results for Peppol-style or no-network profiles."
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
