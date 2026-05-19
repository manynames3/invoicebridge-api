import pytest
from fastapi.testclient import TestClient


def test_region_topology(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.get("/v1/regions", headers=auth_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["active_region"] == "test-region-a"
    assert body["region_role"] == "primary"
    assert body["data_residency_region"] == "test-residency"
    assert body["write_strategy"] == "regional-primary-writes"
    assert body["tenant_routing_strategy"] == "tenant-home-region-with-promoted-failover"
    assert [region["name"] for region in body["supported_regions"]] == ["test-region-a", "test-region-b"]
    assert body["supported_regions"][0]["accepts_writes"] is True
    assert body["supported_regions"][0]["failover_target"] == "test-region-b"


def test_non_writable_region_rejects_new_invoice_writes(
    client: TestClient,
    auth_headers: dict[str, str],
    valid_invoice: dict,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.invoices.accepts_regional_writes", lambda: False)

    response = client.post("/v1/invoices/transform", json=valid_invoice, headers=auth_headers)

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "REGION_NOT_WRITABLE"
