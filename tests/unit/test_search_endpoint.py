from datetime import date, timedelta
from unittest.mock import Mock

import pytest

from app.main import app
from app.models.response import FlightResult, SearchResponse, SearchStats
from app.services.search_service import SearchService


@pytest.fixture
def mock_search_service():
    """Fixture pour SearchService mocké."""
    service = Mock(spec=SearchService)

    mock_results = [
        FlightResult(
            price=1000.0 + i * 100,
            airline=f"Airline{i}",
            departure_date="2025-06-01",
            segments=[{"from": "Paris", "to": "Tokyo", "date": "2025-06-01"}],
        )
        for i in range(10)
    ]

    mock_stats = SearchStats(
        total_results=10,
        search_time_ms=50,
        segments_count=2,
    )

    service.search_flights.return_value = SearchResponse(
        results=mock_results,
        search_stats=mock_stats,
    )

    return service


def test_endpoint_accepts_valid_request(client):
    """Test 39: Endpoint accepte request valide."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data


def test_endpoint_validates_request_body(client):
    """Test 40: Body invalide rejeté."""
    request_data = {"segments": []}

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_endpoint_returns_10_results(client):
    """Test 41: Endpoint retourne 10 résultats."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 10


def test_endpoint_response_matches_schema(client):
    """Test 42: Response conforme SearchResponse schema."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data

    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0

    first_result = data["results"][0]
    assert "price" in first_result
    assert "airline" in first_result
    assert "departure_date" in first_result
    assert "segments" in first_result

    stats = data["search_stats"]
    assert "total_results" in stats
    assert "search_time_ms" in stats
    assert "segments_count" in stats


def test_endpoint_injects_search_service_dependency(client, mock_search_service):
    """Test 43: SearchService injecté via Depends()."""
    from app.api.routes import get_search_service

    app.dependency_overrides[get_search_service] = lambda: mock_search_service

    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "segments": [
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    }

    response = client.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    mock_search_service.search_flights.assert_called_once()
