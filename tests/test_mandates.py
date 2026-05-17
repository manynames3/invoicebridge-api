from fastapi.testclient import TestClient


def test_supported_countries(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/countries", headers=auth_headers)
    assert response.status_code == 200
    profiles = response.json()
    assert profiles[0]["country"] == "BE"
    assert profiles[0]["network"] == "PEPPOL_MOCK"
    assert profiles[0]["implementation_status"] == "MVP_SANDBOX"


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
