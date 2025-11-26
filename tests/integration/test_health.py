import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def health_response(client: TestClient):
    """Health endpoint response partagé."""
    return client.get("/health")


def test_health_endpoint_accessible(health_response) -> None:
    """Given application FastAPI running, when GET /health, then status 200 + JSON ok."""
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}


def test_health_response_content_type_json(health_response) -> None:
    """Given TestClient configure, when GET /health, then header Content-Type application/json."""
    assert "application/json" in health_response.headers.get("content-type", "")


def test_health_endpoint_no_authentication_required(health_response) -> None:
    """Given TestClient sans headers auth, when GET /health, then status 200 (endpoint public)."""
    assert health_response.status_code == 200


def test_health_docker_healthcheck_compatible(health_response) -> None:
    """Given application running, when Docker HEALTHCHECK curl /health, then exit code 0 si healthy."""
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "ok"
