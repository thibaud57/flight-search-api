"""Tests integration endpoint search."""

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_end_to_end_search_request_valid(client_with_mock_search: TestClient) -> None:
    """Request valide retourne 200 avec SearchResponse."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "template_url": "https://www.google.com/travel/flights?tfs=test",
        "segments_date_ranges": [
            {
                "start": tomorrow.isoformat(),
                "end": (tomorrow + timedelta(days=6)).isoformat(),
            },
            {
                "start": (tomorrow + timedelta(days=14)).isoformat(),
                "end": (tomorrow + timedelta(days=19)).isoformat(),
            },
        ],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert "search_stats" in data

    assert len(data["results"]) == 10

    for i in range(len(data["results"]) - 1):
        assert (
            data["results"][i]["flights"][0]["price"]
            <= data["results"][i + 1]["flights"][0]["price"]
        )

    assert data["search_stats"]["total_results"] == 10
    assert data["search_stats"]["segments_count"] == 2
    assert data["search_stats"]["search_time_ms"] > 0


def test_end_to_end_validation_error_empty_segments(
    client_with_mock_search: TestClient,
) -> None:
    """Segments vide retourne 422."""
    request_data = {
        "template_url": "https://www.google.com/travel/flights?tfs=test",
        "segments_date_ranges": [],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_end_to_end_validation_error_invalid_dates(
    client_with_mock_search: TestClient,
) -> None:
    """Dates invalides retourne 422."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "template_url": "https://www.google.com/travel/flights?tfs=test",
        "segments_date_ranges": [
            {
                "start": (tomorrow + timedelta(days=10)).isoformat(),
                "end": tomorrow.isoformat(),
            },
            {
                "start": (tomorrow + timedelta(days=14)).isoformat(),
                "end": (tomorrow + timedelta(days=19)).isoformat(),
            },
        ],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_end_to_end_search_request_exact_dates(
    client_with_mock_search: TestClient,
) -> None:
    """Request avec dates exactes (start=end) retourne 200."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "template_url": "https://www.google.com/travel/flights?tfs=test",
        "segments_date_ranges": [
            {
                "start": tomorrow.isoformat(),
                "end": tomorrow.isoformat(),
            },
            {
                "start": (tomorrow + timedelta(days=6)).isoformat(),
                "end": (tomorrow + timedelta(days=6)).isoformat(),
            },
        ],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200

    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 2


def test_end_to_end_validation_error_too_many_segments(
    client_with_mock_search: TestClient,
) -> None:
    """Plus de 5 segments retourne 422."""
    tomorrow = date.today() + timedelta(days=1)

    request_data = {
        "template_url": "https://www.google.com/travel/flights?tfs=test",
        "segments_date_ranges": [
            {
                "start": (tomorrow + timedelta(days=i * 10)).isoformat(),
                "end": (tomorrow + timedelta(days=i * 10 + 2)).isoformat(),
            }
            for i in range(6)
        ],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422

    data = response.json()
    assert "detail" in data


def test_end_to_end_openapi_schema_includes_endpoint(
    client_with_mock_search: TestClient,
) -> None:
    """OpenAPI schema contient endpoint search-flights."""
    response = client_with_mock_search.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    assert "/api/v1/search-flights" in schema["paths"]

    endpoint = schema["paths"]["/api/v1/search-flights"]
    assert "post" in endpoint

    post_spec = endpoint["post"]
    assert "requestBody" in post_spec
    assert "responses" in post_spec
