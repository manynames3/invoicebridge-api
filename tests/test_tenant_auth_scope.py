from fastapi.testclient import TestClient


def _tenant_payload(tenant_id: str = "acme-eu") -> dict[str, str]:
    return {
        "tenant_id": tenant_id,
        "name": tenant_id,
        "home_region": "test-region-a",
        "data_residency_region": "EU",
        "failover_region": "test-region-b",
    }


def _create_tenant_key(client: TestClient, auth_headers: dict[str, str], tenant_id: str) -> str:
    response = client.post("/v1/tenants", json=_tenant_payload(tenant_id), headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["api_key"].startswith("ib_tenant_")
    assert body["api_key_prefix"] == body["api_key"][:16]
    return str(body["api_key"])


def test_tenant_key_is_returned_once_and_scopes_invoice_writes(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    tenant_key = _create_tenant_key(client, auth_headers, "acme-eu")
    tenant_headers = {"X-API-Key": tenant_key}

    tenant = client.get("/v1/tenants/acme-eu", headers=tenant_headers)
    assert tenant.status_code == 200
    assert "api_key" not in tenant.json()

    transformed = client.post("/v1/invoices/transform", json=valid_invoice, headers=tenant_headers)
    assert transformed.status_code == 200
    body = transformed.json()
    assert body["tenant_id"] == "acme-eu"

    status = client.get(f"/v1/invoices/status/{body['invoice_id']}", headers=tenant_headers)
    assert status.status_code == 200
    assert status.json()["tenant_id"] == "acme-eu"


def test_tenant_key_cannot_cross_tenant_boundaries(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    tenant_a_key = _create_tenant_key(client, auth_headers, "tenant-a")
    tenant_b_key = _create_tenant_key(client, auth_headers, "tenant-b")

    denied_write = client.post(
        "/v1/invoices/transform",
        json={**valid_invoice, "tenant_id": "tenant-b"},
        headers={"X-API-Key": tenant_a_key},
    )
    assert denied_write.status_code == 403
    assert denied_write.json()["detail"]["code"] == "TENANT_ACCESS_DENIED"

    transformed = client.post(
        "/v1/invoices/transform",
        json={**valid_invoice, "tenant_id": "tenant-a"},
        headers={"X-API-Key": tenant_a_key},
    )
    assert transformed.status_code == 200
    invoice_id = transformed.json()["invoice_id"]

    denied_read = client.get(f"/v1/invoices/status/{invoice_id}", headers={"X-API-Key": tenant_b_key})
    assert denied_read.status_code == 404
    assert denied_read.json()["detail"]["code"] == "INVOICE_NOT_FOUND"


def test_tenant_key_cannot_register_tenants(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    tenant_key = _create_tenant_key(client, auth_headers, "acme-eu")

    response = client.post(
        "/v1/tenants",
        json=_tenant_payload("other-tenant"),
        headers={"X-API-Key": tenant_key},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ADMIN_API_KEY_REQUIRED"


def test_archive_redacts_payload_and_document_but_keeps_audit_evidence(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    tenant_key = _create_tenant_key(client, auth_headers, "acme-eu")
    tenant_headers = {"X-API-Key": tenant_key}
    transformed = client.post("/v1/invoices/transform", json=valid_invoice, headers=tenant_headers)
    assert transformed.status_code == 200
    invoice_id = transformed.json()["invoice_id"]

    document = client.get(f"/v1/invoices/{invoice_id}/document", headers=tenant_headers)
    assert document.status_code == 200

    archived = client.post(
        f"/v1/invoices/{invoice_id}/archive",
        json={"reason": "customer retention request"},
        headers=tenant_headers,
    )
    assert archived.status_code == 200
    archived_body = archived.json()
    assert archived_body["status"] == "archived"
    assert archived_body["redacted_payload"] is True
    assert archived_body["redacted_document"] is True

    status_response = client.get(f"/v1/invoices/status/{invoice_id}", headers=tenant_headers)
    assert status_response.status_code == 200
    assert status_response.json()["current_status"] == "archived"

    redacted_document = client.get(f"/v1/invoices/{invoice_id}/document", headers=tenant_headers)
    assert redacted_document.status_code == 409

    audit = client.get(f"/v1/invoices/{invoice_id}/audit-trail", headers=tenant_headers)
    assert audit.status_code == 200
    archived_event = next(event for event in audit.json()["events"] if event["event_type"] == "archived")
    assert archived_event["metadata"]["redacted_payload"] is True
    assert archived_event["metadata"]["document_sha256"]

