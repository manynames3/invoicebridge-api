from fastapi.testclient import TestClient


def test_valid_invoice_validation(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/validate", json=valid_invoice, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["errors"] == []
    assert body["normalized_totals"]["payable_amount"] == "295.00"
    assert body["country_profile_used"] == "BE_B2B_PEPPOL_MVP"


def test_invalid_invoice_validation_returns_structured_errors(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    invalid_invoice = dict(valid_invoice)
    invalid_invoice["buyer"] = dict(valid_invoice["buyer"])
    invalid_invoice["buyer"].pop("routing_id")
    invalid_invoice["lines"] = [dict(valid_invoice["lines"][0])]
    invalid_invoice["lines"][0]["vat_rate"] = "17"
    invalid_invoice["totals"] = dict(valid_invoice["totals"])
    invalid_invoice["totals"]["payable_amount"] = "999.00"

    response = client.post("/v1/invoices/validate", json=invalid_invoice, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    codes = {error["code"] for error in body["errors"]}
    assert body["compliant"] is False
    assert "MISSING_BUYER_ROUTING_ID" in codes
    assert "INVALID_VAT_RATE" in codes
    assert "TOTAL_PAYABLE_MISMATCH" in codes


def test_missing_document_totals_are_not_compliant(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    invoice = dict(valid_invoice)
    invoice.pop("totals")

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert {error["code"] for error in body["errors"]} == {"MISSING_TOTALS"}
