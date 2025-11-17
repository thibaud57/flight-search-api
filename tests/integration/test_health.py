import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_status_code(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body(client: TestClient) -> None:
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
