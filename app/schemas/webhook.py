from pydantic import BaseModel


class WebhookTestRequest(BaseModel):
    invoice_id: str
    target_url: str | None = None
    event_type: str = "invoice.status_changed"


class WebhookTestResponse(BaseModel):
    delivered: bool
    event_type: str
    target_url: str | None
    status_code: int | None
    message: str
