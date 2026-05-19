from fastapi.testclient import TestClient


def test_supported_countries(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get("/v1/countries", headers=auth_headers)
    assert response.status_code == 200
    profiles = {profile["country"]: profile for profile in response.json()}
    assert profiles["BE"]["network"] == "PEPPOL_MOCK"
    assert profiles["BE"]["implementation_status"] == "COMING_SOON_PRODUCTION_ROADMAP"
    assert profiles["DE"]["network"] == "CUSTOMER_MANAGED_DELIVERY_MOCK"
    assert profiles["DE"]["required_format"] == "XRECHNUNG_3_0_UBL"
    assert "german_vat_id_checksum" in profiles["DE"]["capabilities"]
    assert profiles["PL"]["network"] == "KSEF_GOV_MOCK"
    assert profiles["PL"]["required_format"] == "KSEF_FA3_XML_LIKE"
    assert profiles["PL"]["implementation_status"] == "COMING_SOON_PRODUCTION_ROADMAP"
    assert "polish_nip_checksum" in profiles["PL"]["capabilities"]
    assert profiles["RO"]["network"] == "RO_EFACTURA_GOV_MOCK"
    assert profiles["RO"]["required_format"] == "RO_CIUS_UBL_2_1_XML_LIKE"
    assert profiles["RO"]["implementation_status"] == "COMING_SOON_PRODUCTION_ROADMAP"
    assert "romanian_cui_checksum" in profiles["RO"]["capabilities"]
    assert profiles["ES"]["network"] == "LOCAL_FISCAL_RECORD_MOCK"
    assert profiles["ES"]["required_format"] == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE"
    assert "spanish_tax_id_checksum" in profiles["ES"]["capabilities"]
    assert "sha256_record_hash_chain" in profiles["ES"]["capabilities"]
    assert "aeat_registro_alta_field_mapping" in profiles["ES"]["capabilities"]
    assert "aeat_xsd_validation_setup" in profiles["ES"]["capabilities"]
    assert "aeat_qr_payload_draft" in profiles["ES"]["capabilities"]


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
    assert body["required_format"] == "XRECHNUNG_3_0_UBL"
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
    assert body["implementation_status"] == "COMING_SOON_EXTERNAL_VALIDATION_REQUIRED"
    assert body["pdf_allowed_as_compliant_invoice"] is False


def test_poland_mandate_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/v1/mandates/check",
        params={"country": "PL", "transaction_type": "B2B"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "PL"
    assert body["required_format"] == "KSEF_FA3_XML_LIKE"
    assert body["delivery_network"] == "KSEF_GOV_MOCK"
    assert body["implementation_status"] == "COMING_SOON_PRODUCTION_ROADMAP"
    assert "KSeF credentials" in body["production_readiness"]


def test_romania_mandate_check(client: TestClient, auth_headers: dict[str, str]) -> None:
    response = client.get(
        "/v1/mandates/check",
        params={"country": "RO", "transaction_type": "B2B"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["country"] == "RO"
    assert body["required_format"] == "RO_CIUS_UBL_2_1_XML_LIKE"
    assert body["delivery_network"] == "RO_EFACTURA_GOV_MOCK"
    assert body["implementation_status"] == "COMING_SOON_PRODUCTION_ROADMAP"
    assert "ANAF/SPV OAuth" in body["production_readiness"]
