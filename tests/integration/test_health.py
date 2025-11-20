from fastapi.testclient import TestClient


def test_health_endpoint_accessible(client: TestClient) -> None:
    """Given application FastAPI running, when GET /health, then status 200 + JSON ok."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_response_content_type_json(client: TestClient) -> None:
    """Given TestClient configure, when GET /health, then header Content-Type application/json."""
    response = client.get("/health")

    assert "application/json" in response.headers.get("content-type", "")


def test_health_endpoint_no_authentication_required(client: TestClient) -> None:
    """Given TestClient sans headers auth, when GET /health, then status 200 (endpoint public)."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.status_code != 401


def test_health_docker_healthcheck_compatible(client: TestClient) -> None:
    """Given application running, when Docker HEALTHCHECK curl /health, then exit code 0 si healthy."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
