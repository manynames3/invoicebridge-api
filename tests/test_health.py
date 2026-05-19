from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["region"] == "test-region-a"
    assert response.headers["X-Deployment-Region"] == "test-region-a"
    assert response.headers["X-Failover-Region"] == "test-region-b"


def test_readiness(client: TestClient) -> None:
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"
    assert body["accepts_writes"] is True


def test_v1_requires_api_key(client: TestClient) -> None:
    response = client.get("/v1/countries")
    assert response.status_code == 401
    assert response.headers["X-Deployment-Region"] == "test-region-a"
