import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint_accessible(client: TestClient) -> None:
    """Given application FastAPI running, when GET /health, then status 200 + JSON ok."""
    # Given: Application FastAPI running avec TestClient
    # (fixture client)

    # When: GET /health
    response = client.get("/health")

    # Then: Status code 200 + JSON response {"status": "ok"}
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_response_content_type_json(client: TestClient) -> None:
    """Given TestClient configure, when GET /health, then header Content-Type application/json."""
    # Given: TestClient configuré
    # (fixture client)

    # When: GET /health
    response = client.get("/health")

    # Then: Header Content-Type: application/json present
    assert "application/json" in response.headers.get("content-type", "")


def test_health_endpoint_no_authentication_required(client: TestClient) -> None:
    """Given TestClient sans headers auth, when GET /health, then status 200 (endpoint public)."""
    # Given: TestClient sans headers auth
    # (aucun header Authorization fourni)

    # When: GET /health sans authentification
    response = client.get("/health")

    # Then: Status code 200 (endpoint public, pas de 401 Unauthorized)
    assert response.status_code == 200
    assert response.status_code != 401


def test_health_docker_healthcheck_compatible(client: TestClient) -> None:
    """Given application running, when Docker HEALTHCHECK curl /health, then exit code 0 si healthy."""
    # Given: Application running en mode Docker
    # (simule avec TestClient)

    # When: Docker HEALTHCHECK execute curl http://localhost:8000/health
    response = client.get("/health")

    # Then: Exit code 0 (healthy) si status ok
    # Docker considere healthy si status code 200
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
