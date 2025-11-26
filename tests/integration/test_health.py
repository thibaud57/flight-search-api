"""Tests integration endpoint health."""

from fastapi.testclient import TestClient


def test_health_returns_200_with_json_ok(client: TestClient) -> None:
    """Health endpoint retourne 200 avec {"status": "ok"}."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_response_content_type_json(client: TestClient) -> None:
    """Health endpoint retourne Content-Type application/json."""
    response = client.get("/health")

    assert "application/json" in response.headers.get("content-type", "")
