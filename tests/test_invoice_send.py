from fastapi.testclient import TestClient


def test_send_existing_invoice_accepts_by_default(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    transform = client.post("/v1/invoices/transform", json=valid_invoice, headers=auth_headers)
    invoice_id = transform.json()["invoice_id"]

    response = client.post(
        "/v1/invoices/send",
        json={"invoice_id": invoice_id},
        headers={**auth_headers, "Idempotency-Key": "send-key-1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invoice_id"] == invoice_id
    assert body["network"] == "PEPPOL_MOCK"
    assert body["delivery_status"] == "accepted"
    assert body["processing_region"] == "test-region-a"
    assert body["provider_reference"].startswith("MOCK-PEPPOL-")


def test_send_replays_prior_accepted_submission_without_duplicate_provider_action(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    transform = client.post("/v1/invoices/transform", json=valid_invoice, headers=auth_headers)
    invoice_id = transform.json()["invoice_id"]

    first = client.post("/v1/invoices/send", json={"invoice_id": invoice_id}, headers=auth_headers)
    second = client.post("/v1/invoices/send", json={"invoice_id": invoice_id}, headers=auth_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["submission_id"] == second.json()["submission_id"]

    audit = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)
    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert event_types.count("submitted") == 1


def test_send_payload_transforms_first(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    response = client.post(
        "/v1/invoices/send",
        json={"invoice": valid_invoice},
        headers={**auth_headers, "Idempotency-Key": "send-key-2"},
    )
    assert response.status_code == 200
    assert response.json()["delivery_status"] == "accepted"


def test_send_requires_exactly_one_invoice_reference(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    response = client.post(
        "/v1/invoices/send",
        json={"invoice_id": "existing", "invoice": valid_invoice},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_SEND_INPUT"


def test_send_rejected_invoice_can_be_retried(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    large_invoice = dict(valid_invoice)
    large_invoice["invoice_number"] = "INV-BE-2026-LARGE"
    large_invoice["lines"] = [
        {
            "line_id": "1",
            "description": "Large implementation project",
            "quantity": "2",
            "unit_price": "6000.00",
            "vat_rate": "21",
            "line_extension_amount": "12000.00",
            "tax_amount": "2520.00",
            "total_amount": "14520.00",
        }
    ]
    large_invoice["totals"] = {
        "tax_exclusive_amount": "12000.00",
        "tax_amount": "2520.00",
        "tax_inclusive_amount": "14520.00",
        "payable_amount": "14520.00",
    }

    rejected = client.post(
        "/v1/invoices/send",
        json={"invoice": large_invoice, "simulate_rejection": True},
        headers=auth_headers,
    )
    invoice_id = rejected.json()["invoice_id"]
    retried = client.post("/v1/invoices/send", json={"invoice_id": invoice_id}, headers=auth_headers)

    assert rejected.status_code == 200
    assert rejected.json()["delivery_status"] == "rejected"
    assert retried.status_code == 200
    assert retried.json()["delivery_status"] == "accepted"

    audit = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=auth_headers)
    event_types = [event["event_type"] for event in audit.json()["events"]]
    assert "retried" in event_types


def test_send_can_return_pending(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    invoice = dict(valid_invoice)
    invoice["invoice_number"] = "INV-BE-2026-PENDING"
    response = client.post("/v1/invoices/send", json={"invoice": invoice}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["delivery_status"] == "pending"


def test_send_germany_invoice_records_customer_managed_delivery(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    response = client.post(
        "/v1/invoices/send",
        json={"invoice": germany_invoice},
        headers={**auth_headers, "Idempotency-Key": "send-de-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["network"] == "CUSTOMER_MANAGED_DELIVERY_MOCK"
    assert body["delivery_status"] == "accepted"
    assert body["provider_reference"].startswith("LOCAL-DE-")


def test_send_spain_invoice_records_local_fiscal_record(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    response = client.post(
        "/v1/invoices/send",
        json={"invoice": spain_invoice},
        headers={**auth_headers, "Idempotency-Key": "send-es-001"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["network"] == "LOCAL_FISCAL_RECORD_MOCK"
    assert body["delivery_status"] == "accepted"
    assert body["provider_reference"].startswith("LOCAL-ES-FISCAL-")
