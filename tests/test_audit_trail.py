from fastapi.testclient import TestClient


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
    assert body["processing_region"] == "test-region-a"
    assert body["retry_available"] is False
