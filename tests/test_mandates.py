from fastapi.testclient import TestClient


def test_supported_countries(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/countries", headers=auth_headers)
    assert response.status_code == 200
    profiles = {profile["country"]: profile for profile in response.json()}
    assert profiles["BE"]["network"] == "PEPPOL_MOCK"
    assert profiles["BE"]["implementation_status"] == "MVP_SANDBOX"
    assert profiles["DE"]["network"] == "CUSTOMER_MANAGED_DELIVERY_MOCK"
    assert profiles["DE"]["required_format"] == "XRECHNUNG_EN16931_UBL_LIKE"
    assert profiles["ES"]["network"] == "LOCAL_FISCAL_RECORD_MOCK"
    assert profiles["ES"]["required_format"] == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE"


def test_mandate_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/v1/mandates/check",
        params={"country": "BE", "transaction_type": "B2B"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mandated"] is True
    assert body["effective_date"] == "2026-01-01"
    assert body["required_format"] == "PEPPOL_BIS_BILLING_3_UBL_LIKE"
    assert body["pdf_allowed_as_compliant_invoice"] is False


def test_germany_mandate_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/v1/mandates/check",
        params={"country": "DE", "transaction_type": "B2B"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "DE"
    assert body["required_format"] == "XRECHNUNG_EN16931_UBL_LIKE"
    assert body["delivery_network"] == "CUSTOMER_MANAGED_DELIVERY_MOCK"
    assert body["pdf_allowed_as_compliant_invoice"] is False


def test_spain_mandate_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/v1/mandates/check",
        params={"country": "ES", "transaction_type": "B2B"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "ES"
    assert body["required_format"] == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE"
    assert body["delivery_network"] == "LOCAL_FISCAL_RECORD_MOCK"
    assert body["implementation_status"] == "MVP_SANDBOX_NO_NETWORK"
    assert body["pdf_allowed_as_compliant_invoice"] is False
