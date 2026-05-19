from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    timestamp: datetime
    actor: str
    event_type: str
    processing_region: str
    metadata: dict[str, Any]
    payload_hash: str | None = None


class AuditTrailResponse(BaseModel):
    invoice_id: str
    events: list[AuditEventResponse]
