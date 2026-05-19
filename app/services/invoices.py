from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import mask_identifier
from app.core.regions import accepts_regional_writes, current_region
from app.db.models import AuditEvent, Invoice, InvoiceSubmission, Tenant, ValidationResult
from app.schemas.audit import AuditEventResponse, AuditTrailResponse
from app.schemas.compliance import OfficialValidationResponse, SpanishSIFResponsibleDeclarationResponse
from app.schemas.invoice import (
    CreateInvoiceRequest,
    InvoiceStatusResponse,
    InvoiceTotals,
    NormalizedInvoiceInput,
    Party,
    SendInvoiceRequest,
    SendInvoiceResponse,
    TransformInvoiceResponse,
)
from app.schemas.validation import InvoiceValidationResponse
from app.services.audit import create_audit_event
from app.services.checksum import stable_payload_hash
from app.services.money import money
from app.services.official_validation import validate_official_document
from app.services.providers.registry import get_provider_for_network
from app.services.spain_sif import (
    declaration_summary,
    event_record_hash,
    registration_record_hash,
    responsible_declaration_draft,
)
from app.services.spanish_sif_signing import sign_spanish_sif_document
from app.services.tenants import tenant_region_decision
from app.services.transform.registry import get_transformer_for_format
from app.services.validation.registry import get_validator_for_invoice


def model_payload(invoice: NormalizedInvoiceInput) -> dict[str, Any]:
    return invoice.model_dump(mode="json", exclude_none=True)


def validation_payload(validation: InvoiceValidationResponse) -> dict[str, Any]:
    return validation.model_dump(mode="json")


def idempotency_value(header_key: str | None, body_key: str | None) -> str | None:
    if header_key and body_key and header_key != body_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "IDEMPOTENCY_KEY_CONFLICT",
                "message": "Idempotency-Key header and body idempotency_key must match when both are provided.",
            },
        )
    return header_key or body_key


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.processing_region = current_region()

    def validate(self, invoice: NormalizedInvoiceInput) -> InvoiceValidationResponse:
        return get_validator_for_invoice(invoice).validate(invoice)

    def transform(
        self,
        invoice: NormalizedInvoiceInput,
        *,
        idempotency_key: str | None = None,
    ) -> TransformInvoiceResponse | InvoiceValidationResponse:
        key = idempotency_value(idempotency_key, invoice.idempotency_key)
        if key:
            existing = self.db.scalar(select(Invoice).where(Invoice.idempotency_key == key))
            if existing:
                self._ensure_idempotency_tenant_matches(existing, invoice.tenant_id)
                if existing.validation_status == "failed":
                    return self._validation_response_from_invoice(existing)
                return self._transform_response_from_invoice(existing)

        tenant = self._resolve_tenant(invoice.tenant_id)
        self._ensure_tenant_region(tenant)
        self._ensure_writable_region()
        validation = self.validate(invoice)
        if not validation.compliant:
            failed_invoice, failed_event = self._record_validation_failure(
                invoice,
                validation,
                tenant=tenant,
                idempotency_key=key,
            )
            return self._validation_response_with_audit(
                validation,
                invoice_id=failed_invoice.id,
                audit_log_id=failed_event.id,
            )

        transformer = get_transformer_for_format(validation.required_format)
        xml = transformer.transform(invoice, validation)
        signing_result = None
        if (invoice.country or "").upper() == "ES":
            try:
                signing_result = sign_spanish_sif_document(xml)
                xml = signing_result.signed_xml
            except RuntimeError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail={"code": "SPANISH_SIF_SIGNING_FAILED", "message": str(exc)},
                ) from exc
        db_invoice = Invoice(
            tenant_id=tenant.id if tenant else None,
            country=(invoice.country or "BE").upper(),
            transaction_type=(invoice.transaction_type or "B2B").upper(),
            invoice_number=invoice.invoice_number or "",
            seller_vat_id=invoice.seller.vat_id if invoice.seller else None,
            buyer_vat_id=invoice.buyer.vat_id if invoice.buyer else None,
            buyer_routing_id=self._buyer_routing_id(invoice),
            status="transformed",
            validation_status="passed",
            delivery_status="not_submitted",
            required_format=validation.required_format,
            processing_region=self.processing_region,
            idempotency_key=key,
            original_payload=model_payload(invoice),
            transformed_xml=xml,
            validation_result=validation_payload(validation),
        )
        self.db.add(db_invoice)
        self.db.flush()

        create_audit_event(
            self.db,
            invoice_id=db_invoice.id,
            event_type="invoice_received",
            metadata={
                "invoice_number": invoice.invoice_number,
                "tenant_id": db_invoice.tenant_id,
                "seller_vat_id_masked": mask_identifier(db_invoice.seller_vat_id),
                "buyer_vat_id_masked": mask_identifier(db_invoice.buyer_vat_id),
            },
            payload_for_hash=model_payload(invoice),
        )
        create_audit_event(
            self.db,
            invoice_id=db_invoice.id,
            event_type="validation_passed",
            metadata={"profile": validation.country_profile_used, "required_format": validation.required_format},
            payload_for_hash=validation_payload(validation),
        )
        validation_record = ValidationResult(
            invoice_id=db_invoice.id,
            compliant=validation.compliant,
            errors=[issue.model_dump(mode="json") for issue in validation.errors],
            warnings=[issue.model_dump(mode="json") for issue in validation.warnings],
            normalized_totals=validation.normalized_totals.model_dump(mode="json"),
            required_format=validation.required_format,
            country_profile_used=validation.country_profile_used,
        )
        self.db.add(validation_record)
        transformed_event = create_audit_event(
            self.db,
            invoice_id=db_invoice.id,
            event_type="transformed",
            metadata={"format": validation.required_format, "xml_bytes": len(xml.encode("utf-8"))},
            payload_for_hash=xml,
        )
        if db_invoice.country == "ES":
            record_hash = registration_record_hash(invoice, validation)
            sif_event_hash = event_record_hash(invoice)
            create_audit_event(
                self.db,
                invoice_id=db_invoice.id,
                event_type="sif_record_generated",
                metadata={
                    "record_type": "REGISTRO_FACTURACION_ALTA",
                    "record_hash": record_hash,
                    "event_hash": sif_event_hash,
                    "hash_algorithm": "SHA-256",
                    "sif_mode": invoice.metadata.get("sif_mode"),
                    "declaration": declaration_summary(invoice),
                },
                payload_for_hash={"record_hash": record_hash, "event_hash": sif_event_hash},
            )
            if signing_result and signing_result.configured:
                create_audit_event(
                    self.db,
                    invoice_id=db_invoice.id,
                    event_type="sif_record_signed",
                    metadata={
                        "signature_reference": signing_result.signature_reference,
                        "message": signing_result.message,
                    },
                    payload_for_hash=xml,
                )
        self.db.commit()
        self.db.refresh(db_invoice)
        return TransformInvoiceResponse(
            invoice_id=db_invoice.id,
            tenant_id=db_invoice.tenant_id,
            status=db_invoice.status,
            format=db_invoice.required_format,
            processing_region=db_invoice.processing_region,
            xml_preview=(db_invoice.transformed_xml or "")[:2000],
            document_url=self._document_url(db_invoice.id),
            document_sha256=stable_payload_hash(db_invoice.transformed_xml or ""),
            warnings=validation.warnings,
            audit_log_id=transformed_event.id,
        )

    def send(
        self,
        request: SendInvoiceRequest,
        *,
        idempotency_key: str | None = None,
    ) -> SendInvoiceResponse | InvoiceValidationResponse:
        key = idempotency_value(idempotency_key, request.idempotency_key)
        self._validate_send_request_shape(request)
        if key:
            existing_submission = self.db.scalar(
                select(InvoiceSubmission).where(InvoiceSubmission.idempotency_key == key)
            )
            if existing_submission:
                return self._send_response_from_submission(existing_submission)

        invoice = self._resolve_invoice_for_send(request, key)
        if isinstance(invoice, InvoiceValidationResponse):
            return invoice
        self._ensure_sendable(invoice)

        provider = get_provider_for_network(self._network_for_invoice(invoice))
        prior_submission = self._latest_submission(invoice.id)
        if prior_submission and invoice.delivery_status in {"accepted", "pending"}:
            return self._send_response_from_submission(prior_submission)
        self._ensure_tenant_region(self._resolve_tenant(invoice.tenant_id))
        self._ensure_writable_region()
        if prior_submission:
            create_audit_event(
                self.db,
                invoice_id=invoice.id,
                event_type="retried",
                metadata={
                    "previous_submission_id": prior_submission.id,
                    "previous_delivery_status": prior_submission.delivery_status,
                },
                payload_for_hash={"invoice_id": invoice.id, "previous_submission_id": prior_submission.id},
            )

        submitted_event = create_audit_event(
            self.db,
            invoice_id=invoice.id,
            event_type="submitted",
            metadata={"network": provider.network},
            payload_for_hash={"invoice_id": invoice.id, "provider": provider.network},
        )
        result = provider.submit(
            invoice,
            simulate_rejection=request.simulate_rejection
            or bool(request.invoice and request.invoice.simulate_rejection),
            simulate_pending=request.simulate_pending or bool(request.invoice and request.invoice.simulate_pending),
        )
        submission = InvoiceSubmission(
            invoice_id=invoice.id,
            network=result.network,
            delivery_status=result.delivery_status,
            provider_reference=result.provider_reference,
            rejection_reason=result.rejection_reason,
            processing_region=self.processing_region,
            idempotency_key=key,
            request_payload={"invoice_id": invoice.id},
            response_payload=result.response_payload,
        )
        self.db.add(submission)

        invoice.status = result.delivery_status
        invoice.delivery_status = result.delivery_status
        invoice.provider_reference = result.provider_reference
        invoice.last_error = result.rejection_reason

        terminal_event = create_audit_event(
            self.db,
            invoice_id=invoice.id,
            event_type=result.delivery_status,
            metadata={
                "network": result.network,
                "provider_reference": result.provider_reference,
                "rejection_reason": result.rejection_reason,
                "submitted_event_id": submitted_event.id,
            },
            payload_for_hash=result.response_payload,
        )
        self.db.commit()
        self.db.refresh(submission)
        return SendInvoiceResponse(
            invoice_id=invoice.id,
            tenant_id=invoice.tenant_id,
            submission_id=submission.id,
            network=submission.network,
            delivery_status=submission.delivery_status,
            provider_reference=submission.provider_reference,
            processing_region=submission.processing_region,
            rejection_reason=submission.rejection_reason,
            provider_metadata=submission.response_payload.get("metadata", {}),
            audit_log_id=terminal_event.id,
        )

    def status(self, invoice_id: str) -> InvoiceStatusResponse:
        invoice = self._get_invoice(invoice_id)
        return InvoiceStatusResponse(
            invoice_id=invoice.id,
            tenant_id=invoice.tenant_id,
            current_status=invoice.status,
            validation_status=invoice.validation_status,
            delivery_status=invoice.delivery_status,
            provider_reference=invoice.provider_reference,
            processing_region=invoice.processing_region,
            created_at=invoice.created_at,
            updated_at=invoice.updated_at,
            last_error=invoice.last_error,
            retry_available=invoice.delivery_status in {"rejected", "pending"},
        )

    def audit_trail(self, invoice_id: str) -> AuditTrailResponse:
        invoice = self._get_invoice(invoice_id)
        events = [
            AuditEventResponse(
                event_id=event.id,
                timestamp=event.created_at,
                actor=event.actor,
                event_type=event.event_type,
                processing_region=event.processing_region,
                metadata=event.event_metadata,
                payload_hash=event.payload_hash,
            )
            for event in invoice.audit_events
        ]
        return AuditTrailResponse(invoice_id=invoice.id, events=events)

    def transformed_document(self, invoice_id: str) -> str:
        invoice = self._get_invoice(invoice_id)
        if not invoice.transformed_xml:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "INVOICE_DOCUMENT_NOT_AVAILABLE",
                    "message": "A transformed XML document is only available after successful transformation.",
                },
            )
        return invoice.transformed_xml

    def official_validate(self, invoice_id: str) -> OfficialValidationResponse:
        invoice = self._get_invoice(invoice_id)
        if not invoice.transformed_xml:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "INVOICE_DOCUMENT_NOT_AVAILABLE",
                    "message": "Official validation requires a successfully transformed XML document.",
                },
            )
        return validate_official_document(invoice, invoice.transformed_xml)

    def spain_responsible_declaration(self, invoice_id: str) -> SpanishSIFResponsibleDeclarationResponse:
        invoice = self._get_invoice(invoice_id)
        if invoice.country != "ES":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "RESPONSIBLE_DECLARATION_NOT_AVAILABLE",
                    "message": "Responsible declaration draft output is only available for Spain SIF invoices.",
                },
            )
        payload = NormalizedInvoiceInput.model_validate(invoice.original_payload)
        draft = responsible_declaration_draft(payload)
        return SpanishSIFResponsibleDeclarationResponse(
            invoice_id=invoice.id,
            country=invoice.country,
            status=str(draft["status"]),
            declaration_reference=draft.get("declaration_reference"),
            producer=draft["producer"],
            software=draft["software"],
            statement=str(draft["statement"]),
            external_requirements=draft["external_requirements"],
        )

    def create_from_scratch(
        self,
        request: CreateInvoiceRequest,
        *,
        idempotency_key: str | None = None,
    ) -> TransformInvoiceResponse | InvoiceValidationResponse:
        lines: list[dict[str, Any]] = []
        tax_exclusive_amount = Decimal("0")
        tax_amount = Decimal("0")
        for index, item in enumerate(request.items, start=1):
            line_extension = money(item.quantity * item.unit_price)
            line_tax = money(line_extension * item.vat_rate / Decimal("100"))
            lines.append(
                {
                    "line_id": str(index),
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "vat_rate": item.vat_rate,
                    "line_extension_amount": line_extension,
                    "tax_amount": line_tax,
                    "total_amount": money(line_extension + line_tax),
                }
            )
            tax_exclusive_amount = money(tax_exclusive_amount + line_extension)
            tax_amount = money(tax_amount + line_tax)
        tax_inclusive_amount = money(tax_exclusive_amount + tax_amount)
        invoice = NormalizedInvoiceInput(
            country="BE",
            transaction_type="B2B",
            invoice_number=f"IB-{date.today().strftime('%Y%m%d')}-{request.seller_id}-{request.buyer_id}",
            issue_date=date.today(),
            currency=request.currency,
            seller=Party(
                name=f"Seller {request.seller_id}",
                vat_id="BE0123456789",
                routing_id="0208:BE0123456789",
            ),
            buyer=Party(
                name=f"Buyer {request.buyer_id}",
                vat_id="BE0987654321",
                routing_id="0208:BE0987654321",
            ),
            lines=lines,
            totals=InvoiceTotals(
                tax_exclusive_amount=tax_exclusive_amount,
                tax_amount=tax_amount,
                tax_inclusive_amount=tax_inclusive_amount,
                payable_amount=tax_inclusive_amount,
            ),
            payment_terms=request.payment_terms,
            idempotency_key=request.idempotency_key,
            tenant_id=request.tenant_id,
        )
        return self.transform(invoice, idempotency_key=idempotency_key)

    def _resolve_invoice_for_send(
        self,
        request: SendInvoiceRequest,
        idempotency_key_for_transform: str | None,
    ) -> Invoice | InvoiceValidationResponse:
        if request.invoice_id:
            return self._get_invoice(request.invoice_id)
        if request.invoice:
            transformed = self.transform(request.invoice, idempotency_key=idempotency_key_for_transform)
            if isinstance(transformed, InvoiceValidationResponse):
                return transformed
            return self._get_invoice(transformed.invoice_id)
        raise AssertionError("send request shape should be validated before resolving invoice")

    def _validate_send_request_shape(self, request: SendInvoiceRequest) -> None:
        has_invoice_id = bool(request.invoice_id)
        has_invoice_payload = request.invoice is not None
        if has_invoice_id == has_invoice_payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SEND_INPUT",
                    "message": "Provide exactly one of invoice_id or invoice payload.",
                },
            )

    def _ensure_sendable(self, invoice: Invoice) -> None:
        if invoice.validation_status != "passed" or not invoice.transformed_xml:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "INVOICE_NOT_READY_FOR_SUBMISSION",
                    "message": "Only successfully transformed invoices can be submitted.",
                },
            )

    def _ensure_writable_region(self) -> None:
        if accepts_regional_writes():
            return
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "REGION_NOT_WRITABLE",
                "message": "This deployment region is not accepting invoice writes. Retry against the active region.",
                "processing_region": self.processing_region,
            },
        )

    def _resolve_tenant(self, tenant_id: str | None) -> Tenant | None:
        if tenant_id is None:
            return None
        tenant = self.db.get(Tenant, tenant_id)
        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TENANT_NOT_FOUND",
                    "message": "Tenant was not found.",
                    "tenant_id": tenant_id,
                },
            )
        if not tenant.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "TENANT_INACTIVE",
                    "message": "Tenant is inactive.",
                    "tenant_id": tenant_id,
                },
            )
        return tenant

    def _ensure_tenant_region(self, tenant: Tenant | None) -> None:
        if tenant is None:
            return
        decision = tenant_region_decision(tenant)
        if decision.current_region_allowed:
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "TENANT_REGION_MISMATCH",
                "message": "Tenant invoice writes must be processed in the tenant home or failover region.",
                "tenant_id": tenant.id,
                "current_region": decision.current_region,
                "home_region": decision.write_region,
                "failover_region": decision.failover_region,
            },
        )

    def _ensure_idempotency_tenant_matches(self, invoice: Invoice, requested_tenant_id: str | None) -> None:
        if invoice.tenant_id == requested_tenant_id:
            return
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "IDEMPOTENCY_KEY_TENANT_CONFLICT",
                "message": "Idempotency key is already associated with a different tenant context.",
                "existing_tenant_id": invoice.tenant_id,
                "requested_tenant_id": requested_tenant_id,
            },
        )

    def _get_invoice(self, invoice_id: str) -> Invoice:
        invoice = self.db.get(Invoice, invoice_id)
        if invoice is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "INVOICE_NOT_FOUND", "message": "Invoice was not found."},
            )
        return invoice

    def _buyer_routing_id(self, invoice: NormalizedInvoiceInput) -> str | None:
        if not invoice.buyer:
            return None
        return invoice.buyer.routing_id or invoice.buyer.peppol_id

    def _transform_response_from_invoice(self, invoice: Invoice) -> TransformInvoiceResponse:
        latest_event = self._latest_event(invoice.id, "transformed")
        validation = invoice.validation_result or {}
        warnings = validation.get("warnings", [])
        return TransformInvoiceResponse(
            invoice_id=invoice.id,
            tenant_id=invoice.tenant_id,
            status=invoice.status,
            format=invoice.required_format,
            processing_region=invoice.processing_region,
            xml_preview=(invoice.transformed_xml or "")[:2000],
            document_url=self._document_url(invoice.id),
            document_sha256=stable_payload_hash(invoice.transformed_xml or ""),
            warnings=warnings,
            audit_log_id=latest_event.id if latest_event else "",
        )

    def _record_validation_failure(
        self,
        invoice: NormalizedInvoiceInput,
        validation: InvoiceValidationResponse,
        *,
        tenant: Tenant | None,
        idempotency_key: str | None,
    ) -> tuple[Invoice, AuditEvent]:
        db_invoice = Invoice(
            tenant_id=tenant.id if tenant else None,
            country=(invoice.country or "BE").upper(),
            transaction_type=(invoice.transaction_type or "B2B").upper(),
            invoice_number=invoice.invoice_number or "UNNUMBERED",
            seller_vat_id=invoice.seller.vat_id if invoice.seller else None,
            buyer_vat_id=invoice.buyer.vat_id if invoice.buyer else None,
            buyer_routing_id=self._buyer_routing_id(invoice),
            status="validation_failed",
            validation_status="failed",
            delivery_status="not_submitted",
            required_format=validation.required_format,
            processing_region=self.processing_region,
            idempotency_key=idempotency_key,
            original_payload=model_payload(invoice),
            transformed_xml=None,
            validation_result=validation_payload(validation),
            last_error="; ".join(error.code for error in validation.errors) or None,
        )
        self.db.add(db_invoice)
        self.db.flush()
        create_audit_event(
            self.db,
            invoice_id=db_invoice.id,
            event_type="invoice_received",
            metadata={
                "invoice_number": invoice.invoice_number,
                "tenant_id": db_invoice.tenant_id,
                "seller_vat_id_masked": mask_identifier(db_invoice.seller_vat_id),
                "buyer_vat_id_masked": mask_identifier(db_invoice.buyer_vat_id),
            },
            payload_for_hash=model_payload(invoice),
        )
        validation_record = ValidationResult(
            invoice_id=db_invoice.id,
            compliant=False,
            errors=[issue.model_dump(mode="json") for issue in validation.errors],
            warnings=[issue.model_dump(mode="json") for issue in validation.warnings],
            normalized_totals=validation.normalized_totals.model_dump(mode="json"),
            required_format=validation.required_format,
            country_profile_used=validation.country_profile_used,
        )
        self.db.add(validation_record)
        failed_event = create_audit_event(
            self.db,
            invoice_id=db_invoice.id,
            event_type="validation_failed",
            metadata={
                "profile": validation.country_profile_used,
                "error_codes": [error.code for error in validation.errors],
            },
            payload_for_hash=validation_payload(validation),
        )
        self.db.commit()
        self.db.refresh(db_invoice)
        return db_invoice, failed_event

    def _validation_response_from_invoice(self, invoice: Invoice) -> InvoiceValidationResponse:
        validation = InvoiceValidationResponse.model_validate(invoice.validation_result or {})
        latest_event = self._latest_event(invoice.id, "validation_failed")
        return self._validation_response_with_audit(
            validation,
            invoice_id=invoice.id,
            audit_log_id=latest_event.id if latest_event else None,
        )

    def _validation_response_with_audit(
        self,
        validation: InvoiceValidationResponse,
        *,
        invoice_id: str,
        audit_log_id: str | None,
    ) -> InvoiceValidationResponse:
        metadata = {**validation.metadata, "invoice_id": invoice_id}
        if audit_log_id:
            metadata["audit_log_id"] = audit_log_id
        return validation.model_copy(update={"metadata": metadata})

    def _send_response_from_submission(self, submission: InvoiceSubmission) -> SendInvoiceResponse:
        latest_event = self._latest_event(submission.invoice_id, submission.delivery_status)
        return SendInvoiceResponse(
            invoice_id=submission.invoice_id,
            tenant_id=submission.invoice.tenant_id,
            submission_id=submission.id,
            network=submission.network,
            delivery_status=submission.delivery_status,
            provider_reference=submission.provider_reference,
            processing_region=submission.processing_region,
            rejection_reason=submission.rejection_reason,
            provider_metadata=submission.response_payload.get("metadata", {}),
            audit_log_id=latest_event.id if latest_event else "",
        )

    def _latest_submission(self, invoice_id: str) -> InvoiceSubmission | None:
        return self.db.scalar(
            select(InvoiceSubmission)
            .where(InvoiceSubmission.invoice_id == invoice_id)
            .order_by(InvoiceSubmission.created_at.desc())
        )

    def _latest_event(self, invoice_id: str, event_type: str) -> AuditEvent | None:
        return self.db.scalar(
            select(AuditEvent)
            .where(AuditEvent.invoice_id == invoice_id, AuditEvent.event_type == event_type)
            .order_by(AuditEvent.created_at.desc())
        )

    def _network_for_invoice(self, invoice: Invoice) -> str:
        validation = invoice.validation_result or {}
        metadata = validation.get("metadata", {})
        return metadata.get("delivery_network", "PEPPOL_MOCK")

    def _document_url(self, invoice_id: str) -> str:
        return f"/v1/invoices/{invoice_id}/document"
