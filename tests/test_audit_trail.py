from fastapi.testclient import TestClient

from app.core.config import get_settings


def test_audit_trail_contains_transformation_and_submission_events(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    send = client.post("/v1/invoices/send", json={"invoice": valid_invoice}, headers=auth_headers)
    invoice_id = send.json()["invoice_id"]

    response = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    event_types = [event["event_type"] for event in body["events"]]
    assert event_types == [
        "invoice_received",
        "validation_passed",
        "transformed",
        "submitted",
        "accepted",
    ]
    assert all(event["payload_hash"] for event in body["events"])
    assert {event["processing_region"] for event in body["events"]} == {"test-region-a"}


def test_status_after_send(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    send = client.post("/v1/invoices/send", json={"invoice": valid_invoice}, headers=auth_headers)
    invoice_id = send.json()["invoice_id"]

    response = client.get(f"/v1/invoices/status/{invoice_id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["current_status"] == "accepted"
    assert body["validation_status"] == "passed"
    assert body["delivery_status"] == "accepted"
    assert body["official_validation_status"] == "not_run"
    assert body["official_validation_result_id"] is None
    assert body["processing_region"] == "test-region-a"
    assert body["retry_available"] is False


def test_spain_audit_trail_contains_sif_record_event(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    transform = client.post("/v1/invoices/transform", json=spain_invoice, headers=auth_headers)
    invoice_id = transform.json()["invoice_id"]

    response = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    sif_event = next(event for event in body["events"] if event["event_type"] == "sif_record_generated")
    assert len(sif_event["metadata"]["record_hash"]) == 64
    assert len(sif_event["metadata"]["event_hash"]) == 64
    assert sif_event["metadata"]["declaration"]["verifactu_capable"] is True


def test_spain_signing_command_creates_signed_audit_event(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SPANISH_SIF_SIGNING_COMMAND", "cat {xml}")
    get_settings.cache_clear()

    transform = client.post("/v1/invoices/transform", json=spain_invoice, headers=auth_headers)
    invoice_id = transform.json()["invoice_id"]
    response = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)

    get_settings.cache_clear()

    event_types = [event["event_type"] for event in response.json()["events"]]
    assert "sif_record_signed" in event_types
