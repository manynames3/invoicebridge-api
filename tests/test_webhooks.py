from fastapi.testclient import TestClient


def test_webhook_test_records_event(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    send = client.post("/v1/invoices/send", json={"invoice": valid_invoice}, headers=auth_headers)
    invoice_id = send.json()["invoice_id"]

    response = client.post(
        "/v1/webhooks/test",
        json={"invoice_id": invoice_id, "target_url": "https://example.test/webhook"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["delivered"] is True

    audit = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)
    assert audit.json()["events"][-1]["event_type"] == "webhook_test_delivered"
