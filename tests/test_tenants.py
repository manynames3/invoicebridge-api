from fastapi.testclient import TestClient


def tenant_payload() -> dict[str, str]:
    return {
        "tenant_id": "acme-eu",
        "name": "Acme EU",
        "home_region": "test-region-a",
        "data_residency_region": "EU",
        "failover_region": "test-region-b",
    }


def test_create_and_resolve_tenant_region(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    created = client.post("/v1/tenants", json=tenant_payload(), headers=auth_headers)
    assert created.status_code == 201
    assert created.json()["tenant_id"] == "acme-eu"
    assert created.json()["home_region"] == "test-region-a"

    decision = client.get("/v1/tenants/acme-eu/region-decision", headers=auth_headers)
    assert decision.status_code == 200
    body = decision.json()
    assert body["current_region"] == "test-region-a"
    assert body["write_region"] == "test-region-a"
    assert body["failover_region"] == "test-region-b"
    assert body["current_region_allowed"] is True
    assert body["accepts_writes"] is True


def test_invoice_with_tenant_persists_tenant_and_region(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    client.post("/v1/tenants", json=tenant_payload(), headers=auth_headers)
    invoice = {**valid_invoice, "tenant_id": "acme-eu"}

    transform = client.post("/v1/invoices/transform", json=invoice, headers=auth_headers)

    assert transform.status_code == 200
    body = transform.json()
    assert body["tenant_id"] == "acme-eu"
    assert body["processing_region"] == "test-region-a"

    status = client.get(f"/v1/invoices/status/{body['invoice_id']}", headers=auth_headers)
    assert status.json()["tenant_id"] == "acme-eu"


def test_tenant_region_mismatch_rejects_invoice_write(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
) -> None:
    client.post(
        "/v1/tenants",
        json={
            "tenant_id": "acme-us",
            "name": "Acme US",
            "home_region": "us-east-1",
            "data_residency_region": "US",
            "failover_region": "us-west-2",
        },
        headers=auth_headers,
    )

    response = client.post(
        "/v1/invoices/transform",
        json={**valid_invoice, "tenant_id": "acme-us"},
        headers=auth_headers,
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "TENANT_REGION_MISMATCH"
