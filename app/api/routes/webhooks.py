from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.webhook import WebhookTestRequest, WebhookTestResponse
from app.services.audit import create_audit_event
from app.services.invoices import InvoiceService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/test",
    response_model=WebhookTestResponse,
    summary="Simulate webhook delivery",
    description="Records a mock webhook delivery event. No outbound HTTP request is sent in the MVP.",
)
def webhook_test(request: WebhookTestRequest, db: Session = Depends(get_db)) -> WebhookTestResponse:
    service = InvoiceService(db)
    service.status(request.invoice_id)
    event = create_audit_event(
        db,
        invoice_id=request.invoice_id,
        event_type="webhook_test_delivered",
        metadata={"target_url": request.target_url, "webhook_event_type": request.event_type},
        payload_for_hash=request.model_dump(mode="json"),
    )
    db.commit()
    return WebhookTestResponse(
        delivered=True,
        event_type=request.event_type,
        target_url=request.target_url,
        status_code=202,
        message=f"Mock webhook event recorded as audit event {event.id}.",
    )
