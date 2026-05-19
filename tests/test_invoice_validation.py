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


def test_germany_invoice_validates_without_buyer_routing_id(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/validate", json=germany_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["errors"] == []
    assert body["required_format"] == "XRECHNUNG_EN16931_UBL_LIKE"
    assert body["country_profile_used"] == "DE_B2B_EN16931_MVP"
    assert body["metadata"]["delivery_network"] == "CUSTOMER_MANAGED_DELIVERY_MOCK"


def test_germany_invoice_rejects_bad_vat_id_checksum(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    invoice = dict(germany_invoice)
    invoice["seller"] = dict(germany_invoice["seller"])
    invoice["seller"]["vat_id"] = "DE123456789"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_SELLER_VAT_ID_CHECKSUM" in {error["code"] for error in body["errors"]}


def test_germany_invoice_rejects_unsupported_vat_rate(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    invoice = dict(germany_invoice)
    invoice["lines"] = [dict(germany_invoice["lines"][0])]
    invoice["lines"][0]["vat_rate"] = "21"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_VAT_RATE" in {error["code"] for error in body["errors"]}


def test_spain_invoice_validates_and_keeps_local_record_metadata(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/validate", json=spain_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["errors"] == []
    assert body["warnings"] == []
    assert body["required_format"] == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE"
    assert body["country_profile_used"] == "ES_B2B_NON_VERIFACTU_MVP"
    assert body["metadata"]["delivery_model"] == "local_fiscal_record_no_network"


def test_spain_invoice_rejects_bad_tax_id_checksum(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    invoice = dict(spain_invoice)
    invoice["buyer"] = dict(spain_invoice["buyer"])
    invoice["buyer"]["vat_id"] = "ESB87654321"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_BUYER_VAT_ID_CHECKSUM" in {error["code"] for error in body["errors"]}


def test_spain_invoice_warns_when_fiscal_record_chain_metadata_is_missing(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    invoice = dict(spain_invoice)
    invoice["metadata"] = {}

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert {warning["code"] for warning in body["warnings"]} == {
        "MISSING_PREVIOUS_RECORD_HASH",
        "MISSING_SOFTWARE_SYSTEM_ID",
    }


def test_poland_invoice_validates_with_nip_checksum(
    client: TestClient,
    auth_headers: dict[str, str],
    poland_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/validate", json=poland_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["errors"] == []
    assert body["required_format"] == "KSEF_FA3_XML_LIKE"
    assert body["country_profile_used"] == "PL_B2B_KSEF_MVP"
    assert body["metadata"]["delivery_network"] == "KSEF_GOV_SANDBOX_MOCK"


def test_poland_invoice_rejects_bad_nip_checksum(
    client: TestClient,
    auth_headers: dict[str, str],
    poland_invoice: dict,
) -> None:
    invoice = dict(poland_invoice)
    invoice["buyer"] = dict(poland_invoice["buyer"])
    invoice["buyer"]["vat_id"] = "PL5260250275"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_BUYER_VAT_ID_CHECKSUM" in {error["code"] for error in body["errors"]}


def test_romania_invoice_validates_for_government_platform_sandbox(
    client: TestClient,
    auth_headers: dict[str, str],
    romania_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/validate", json=romania_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is True
    assert body["errors"] == []
    assert body["required_format"] == "RO_CIUS_UBL_2_1_XML_LIKE"
    assert body["country_profile_used"] == "RO_B2B_EFACTURA_MVP"
    assert body["metadata"]["delivery_model"] == "direct_government_platform_sandbox"


def test_romania_invoice_rejects_bad_cui_checksum(
    client: TestClient,
    auth_headers: dict[str, str],
    romania_invoice: dict,
) -> None:
    invoice = dict(romania_invoice)
    invoice["buyer"] = dict(romania_invoice["buyer"])
    invoice["buyer"]["vat_id"] = "RO87654321"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_BUYER_VAT_ID_CHECKSUM" in {error["code"] for error in body["errors"]}


def test_romania_invoice_rejects_unsupported_vat_rate(
    client: TestClient,
    auth_headers: dict[str, str],
    romania_invoice: dict,
) -> None:
    invoice = dict(romania_invoice)
    invoice["lines"] = [dict(romania_invoice["lines"][0])]
    invoice["lines"][0]["vat_rate"] = "19"

    response = client.post("/v1/invoices/validate", json=invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["compliant"] is False
    assert "INVALID_VAT_RATE" in {error["code"] for error in body["errors"]}
