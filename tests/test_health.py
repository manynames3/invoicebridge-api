from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_v1_requires_api_key(client: TestClient) -> None:
    response = client.get("/v1/countries")
    assert response.status_code == 401
