import time
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import get_search_service, router
from app.main import app
from app.models import FlightResult, HealthResponse, SearchResponse, SearchStats
from app.services import SearchService


def test_health_check_returns_ok_status() -> None:
    """Verifie comportement nominal : app running → status ok."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.json()["status"] == "ok"


def test_health_check_returns_200_status_code() -> None:
    """Verifie conformite HTTP : succes → 200 OK."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200


def test_health_check_response_matches_schema() -> None:
    """Verifie type safety : champ status existe et est Literal["ok", "error"]."""
    client = TestClient(app)

    response = client.get("/health")
    data = response.json()

    validated_response = HealthResponse.model_validate(data)
    assert validated_response.status in ["ok", "error"]


def test_health_check_response_time_fast() -> None:
    """Verifie contrainte performance : endpoint ultra-rapide sans calcul."""
    client = TestClient(app)
    num_calls = 10
    times: list[float] = []

    for _ in range(num_calls):
        start = time.perf_counter()
        client.get("/health")
        end = time.perf_counter()
        times.append((end - start) * 1000)

    avg_time = sum(times) / len(times)
    assert avg_time < 100, f"Average response time {avg_time:.2f}ms exceeds 100ms"


@pytest.fixture
def mock_search_service() -> SearchService:
    """Retourne un SearchService mocke."""
    service = MagicMock(spec=SearchService)
    service.search_flights.return_value = SearchResponse(
        results=[
            FlightResult(
                price=825.50,
                airline="Air France",
                departure_date="2025-06-01",
                route=["Paris", "Tokyo"],
            )
        ]
        * 10,
        search_stats=SearchStats(
            total_results=10,
            search_time_ms=50,
            destinations_searched=["Paris", "Tokyo"],
        ),
    )
    return service


@pytest.fixture
def client_with_mock(mock_search_service: SearchService) -> TestClient:
    """Retourne un TestClient FastAPI avec SearchService mocke."""
    test_app = FastAPI()
    test_app.include_router(router)

    test_app.dependency_overrides[get_search_service] = lambda: mock_search_service

    return TestClient(test_app)


@pytest.fixture
def valid_request_data() -> dict[str, str | list[str] | dict[str, str]]:
    """Retourne un body de requete valide."""
    start = (date.today() + timedelta(days=1)).isoformat()
    end = (date.today() + timedelta(days=15)).isoformat()
    return {
        "destinations": ["Paris", "Tokyo"],
        "date_range": {"start": start, "end": end},
    }


class TestSearchFlightsEndpoint:
    def test_endpoint_accepts_valid_request(
        self,
        client_with_mock: TestClient,
        valid_request_data: dict[str, str | list[str] | dict[str, str]],
    ) -> None:
        response = client_with_mock.post(
            "/api/v1/search-flights", json=valid_request_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "search_stats" in data

    def test_endpoint_validates_request_body(
        self, client_with_mock: TestClient
    ) -> None:
        invalid_data = {
            "destinations": [],
            "date_range": {
                "start": (date.today() + timedelta(days=1)).isoformat(),
                "end": (date.today() + timedelta(days=15)).isoformat(),
            },
        }
        response = client_with_mock.post("/api/v1/search-flights", json=invalid_data)
        assert response.status_code == 422

    def test_endpoint_returns_10_results(
        self,
        client_with_mock: TestClient,
        valid_request_data: dict[str, str | list[str] | dict[str, str]],
    ) -> None:
        response = client_with_mock.post(
            "/api/v1/search-flights", json=valid_request_data
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_endpoint_response_matches_schema(
        self,
        client_with_mock: TestClient,
        valid_request_data: dict[str, str | list[str] | dict[str, str]],
    ) -> None:
        response = client_with_mock.post(
            "/api/v1/search-flights", json=valid_request_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
        assert "search_stats" in data
        assert "total_results" in data["search_stats"]
        assert "search_time_ms" in data["search_stats"]
        assert "destinations_searched" in data["search_stats"]

    def test_endpoint_injects_search_service_dependency(
        self,
        client_with_mock: TestClient,
        mock_search_service: SearchService,
        valid_request_data: dict[str, str | list[str] | dict[str, str]],
    ) -> None:
        response = client_with_mock.post(
            "/api/v1/search-flights", json=valid_request_data
        )
        assert response.status_code == 200
        mock_search_service.search_flights.assert_called_once()

    def test_endpoint_logs_search_info(
        self,
        client_with_mock: TestClient,
        valid_request_data: dict[str, str | list[str] | dict[str, str]],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        caplog.set_level(logging.INFO)
        response = client_with_mock.post(
            "/api/v1/search-flights", json=valid_request_data
        )
        assert response.status_code == 200
        assert any(
            "Flight search completed" in record.message for record in caplog.records
        )

    def test_endpoint_handles_edge_case_single_destination(
        self, client_with_mock: TestClient
    ) -> None:
        single_dest_data = {
            "destinations": ["Paris"],
            "date_range": {
                "start": (date.today() + timedelta(days=1)).isoformat(),
                "end": (date.today() + timedelta(days=15)).isoformat(),
            },
        }
        response = client_with_mock.post(
            "/api/v1/search-flights", json=single_dest_data
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10

    def test_endpoint_handles_edge_case_max_destinations(
        self, client_with_mock: TestClient
    ) -> None:
        max_dest_data = {
            "destinations": ["Paris", "Tokyo", "New York", "London", "Dubai"],
            "date_range": {
                "start": (date.today() + timedelta(days=1)).isoformat(),
                "end": (date.today() + timedelta(days=15)).isoformat(),
            },
        }
        response = client_with_mock.post("/api/v1/search-flights", json=max_dest_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 10
