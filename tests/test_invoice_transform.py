from fastapi.testclient import TestClient


def test_transform_valid_invoice(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    response = client.post(
        "/v1/invoices/transform",
        json=valid_invoice,
        headers={**auth_headers, "Idempotency-Key": "transform-key-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert body["format"] == "PEPPOL_BIS_BILLING_3_UBL_LIKE"
    assert body["processing_region"] == "test-region-a"
    assert "InvoiceBridgeSandboxInvoice" in body["xml_preview"]
    assert body["audit_log_id"]


def test_transform_idempotency_replays_existing_invoice(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    headers = {**auth_headers, "Idempotency-Key": "transform-key-2"}
    first = client.post("/v1/invoices/transform", json=valid_invoice, headers=headers)
    second = client.post("/v1/invoices/transform", json=valid_invoice, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["invoice_id"] == second.json()["invoice_id"]


def test_transform_invalid_invoice_returns_422_validation(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    invalid_invoice = dict(valid_invoice)
    invalid_invoice["seller"] = dict(valid_invoice["seller"])
    invalid_invoice["seller"]["vat_id"] = "bad"
    response = client.post("/v1/invoices/transform", json=invalid_invoice, headers=auth_headers)
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "INVALID_SELLER_VAT_ID"
    assert response.json()["metadata"]["invoice_id"]


def test_transform_invalid_invoice_records_validation_failed_audit(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    invalid_invoice = dict(valid_invoice)
    invalid_invoice["buyer"] = dict(valid_invoice["buyer"])
    invalid_invoice["buyer"].pop("routing_id")

    response = client.post("/v1/invoices/transform", json=invalid_invoice, headers=auth_headers)

    assert response.status_code == 422
    invoice_id = response.json()["metadata"]["invoice_id"]
    audit = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)
    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert event_types == ["invoice_received", "validation_failed"]


def test_create_invoice_from_scratch_generates_valid_transform(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/v1/invoices/create",
        json={
            "seller_id": "seller-1",
            "buyer_id": "buyer-1",
            "currency": "EUR",
            "items": [{"description": "Generated service line", "quantity": "2", "unit_price": "25.00"}],
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert "InvoiceBridgeSandboxInvoice" in body["xml_preview"]
