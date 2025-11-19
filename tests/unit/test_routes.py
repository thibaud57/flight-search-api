import time

from fastapi.testclient import TestClient

from app.main import app
from app.models.response import HealthResponse


def test_health_check_returns_ok_status() -> None:
    """Verifie comportement nominal : app running → status ok."""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/health")

    # Assert
    assert response.json()["status"] == "ok"


def test_health_check_returns_200_status_code() -> None:
    """Verifie conformite HTTP : succes → 200 OK."""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/health")

    # Assert
    assert response.status_code == 200


def test_health_check_response_matches_schema() -> None:
    """Verifie type safety : champ status existe et est Literal["ok", "error"]."""
    # Arrange
    client = TestClient(app)

    # Act
    response = client.get("/health")
    data = response.json()

    # Assert
    validated_response = HealthResponse.model_validate(data)
    assert validated_response.status in ["ok", "error"]


def test_health_check_response_time_fast() -> None:
    """Verifie contrainte performance : endpoint ultra-rapide sans calcul."""
    # Arrange
    client = TestClient(app)
    num_calls = 10
    times: list[float] = []

    # Act
    for _ in range(num_calls):
        start = time.perf_counter()
        client.get("/health")
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    # Assert
    avg_time = sum(times) / len(times)
    assert avg_time < 100, f"Average response time {avg_time:.2f}ms exceeds 100ms"
