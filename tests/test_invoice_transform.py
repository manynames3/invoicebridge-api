from xml.etree import ElementTree as ET

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
    assert body["document_url"] == f"/v1/invoices/{body['invoice_id']}/document"
    assert len(body["document_sha256"]) == 64
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
    assert body["document_url"] == f"/v1/invoices/{body['invoice_id']}/document"


def test_transform_germany_invoice_uses_xrechnung_like_format(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/transform", json=germany_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert body["format"] == "XRECHNUNG_3_0_UBL"
    assert "urn:cen.eu:en16931:2017#compliant#urn:xeinkauf.de:kosit:xrechnung_3.0" in body["xml_preview"]
    assert "DE-BUYER-REF-2026-0001" in body["xml_preview"]


def test_transformed_document_endpoint_returns_full_xml(
    client: TestClient,
    auth_headers: dict[str, str],
    germany_invoice: dict,
) -> None:
    transformed = client.post("/v1/invoices/transform", json=germany_invoice, headers=auth_headers)

    assert transformed.status_code == 200
    invoice_id = transformed.json()["invoice_id"]
    response = client.get(f"/v1/invoices/{invoice_id}/document", headers=auth_headers)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    root = ET.fromstring(response.text)
    ns = {
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }
    assert root.tag == "{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice"
    assert root.findtext("{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}BuyerReference") == (
        "DE-BUYER-REF-2026-0001"
    )
    assert root.findtext("cac:Delivery/cbc:ActualDeliveryDate", namespaces=ns) == germany_invoice["issue_date"]
    assert root.findtext("cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:Telephone", namespaces=ns)
    assert germany_invoice["invoice_number"] in response.text


def test_transform_spain_invoice_uses_local_fiscal_record_format(
    client: TestClient,
    auth_headers: dict[str, str],
    spain_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/transform", json=spain_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert body["format"] == "NON_VERIFACTU_FISCAL_RECORD_XML_LIKE"
    document = client.get(body["document_url"], headers=auth_headers)
    assert document.status_code == 200
    root = ET.fromstring(document.text)
    assert root.tag == "InvoiceBridgeSpanishSIFRecord"
    assert root.get("certification_status") == "not_certified"
    assert root.findtext("RecordType") == "NON_VERIFACTU_LOCAL_SIF_RECORD"
    assert root.findtext("SIFMode") == "NO_VERIFACTU"
    assert root.findtext("SoftwareSystem/SoftwareSystemID") == "IB-SANDBOX-SIF-001"
    assert root.findtext("RecordChain/PreviousRecordHash") == "0" * 64
    assert len(root.findtext("RecordChain/CurrentRecordHash") or "") == 64
    assert "huella=" in (root.findtext("QRCodePayloadCandidate") or "")


def test_transform_poland_invoice_uses_ksef_like_format(
    client: TestClient,
    auth_headers: dict[str, str],
    poland_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/transform", json=poland_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert body["format"] == "KSEF_FA3_XML_LIKE"
    assert "InvoiceBridgeKSeFInvoice" in body["xml_preview"]
    assert "FA(3)" in body["xml_preview"]


def test_transform_romania_invoice_uses_ro_cius_like_format(
    client: TestClient,
    auth_headers: dict[str, str],
    romania_invoice: dict,
) -> None:
    response = client.post("/v1/invoices/transform", json=romania_invoice, headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "transformed"
    assert body["format"] == "RO_CIUS_UBL_2_1_XML_LIKE"
    assert "InvoiceBridgeSandboxInvoice" in body["xml_preview"]
    assert "RO_CIUS/UBL 2.1" in body["xml_preview"]
