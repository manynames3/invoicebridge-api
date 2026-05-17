from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditEvent
from app.services.checksum import stable_payload_hash


def create_audit_event(
    db: Session,
    *,
    invoice_id: str,
    event_type: str,
    actor: str = "system",
    metadata: dict[str, Any] | None = None,
    payload_for_hash: Any | None = None,
) -> AuditEvent:
    event = AuditEvent(
        invoice_id=invoice_id,
        event_type=event_type,
        actor=actor,
        event_metadata=metadata or {},
        payload_hash=stable_payload_hash(payload_for_hash) if payload_for_hash is not None else None,
    )
    db.add(event)
    db.flush()
    return event
