"""Tests integration routes search HTTP."""

from fastapi.testclient import TestClient

from tests.fixtures.helpers import (
    SEARCH_GOOGLE_FLIGHTS_ENDPOINT,
    SEARCH_KAYAK_ENDPOINT,
    TEMPLATE_URL,
)


# === Tests validation HTTP layer (SearchService mocké) ===


def test_search_google_flights_returns_200_with_valid_request(
    client_with_mock_search: TestClient, search_request_factory
) -> None:
    """Request valide retourne 200 avec SearchResponse triee par prix."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert "search_stats" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["total_results"] == 10
    assert data["search_stats"]["segments_count"] == 2
    assert data["search_stats"]["search_time_ms"] > 0

    for i in range(len(data["results"]) - 1):
        assert (
            data["results"][i]["flights"][0]["price"]
            <= data["results"][i + 1]["flights"][0]["price"]
        )


def test_search_google_flights_returns_422_empty_segments(
    client_with_mock_search: TestClient,
) -> None:
    """Segments vide retourne 422."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [],
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_google_flights_returns_422_invalid_dates(
    client_with_mock_search: TestClient, date_range_factory
) -> None:
    """Dates invalides retourne 422."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [
            date_range_factory(start_offset=10, duration=-10, as_dict=True),
            date_range_factory(start_offset=14, duration=5, as_dict=True),
        ],
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_google_flights_returns_422_too_many_segments(
    client_with_mock_search: TestClient, date_range_factory
) -> None:
    """Plus de 5 segments retourne 422."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [
            date_range_factory(start_offset=1 + i * 10, duration=2, as_dict=True)
            for i in range(6)
        ],
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    assert "detail" in response.json()


def test_search_google_flights_exact_dates_accepted(
    client_with_mock_search: TestClient, date_range_factory
) -> None:
    """Request avec dates exactes (start=end) retourne 200."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [
            date_range_factory(start_offset=1, duration=0, as_dict=True),
            date_range_factory(start_offset=6, duration=0, as_dict=True),
        ],
    }

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 2


def test_search_google_flights_extra_field_rejected(
    client_with_mock_search: TestClient, search_request_factory
) -> None:
    """SearchRequest avec champ extra doit etre rejete (extra=forbid)."""
    request_data = search_request_factory(as_dict=True)
    request_data["provider"] = "google_flights"

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any(
        "extra" in str(err).lower() or "forbidden" in str(err).lower()
        for err in error_detail
    )


def test_search_kayak_returns_200_mock_response(
    client_with_mock_search: TestClient, search_request_factory
) -> None:
    """Route Kayak accessible et retourne 200 (mock vide)."""
    request_data = search_request_factory(as_dict=True)

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == []
    assert "search_stats" in data


def test_old_route_search_flights_returns_404(
    client_with_mock_search: TestClient, search_request_factory
) -> None:
    """Ancienne route /search-flights retourne 404."""
    request_data = search_request_factory(as_dict=True)

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 404


def test_openapi_schema_includes_search_endpoints(
    client_with_mock_search: TestClient,
) -> None:
    """OpenAPI schema contient endpoints search."""
    response = client_with_mock_search.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert "paths" in schema
    assert SEARCH_GOOGLE_FLIGHTS_ENDPOINT in schema["paths"]
    assert SEARCH_KAYAK_ENDPOINT in schema["paths"]

    google_endpoint = schema["paths"][SEARCH_GOOGLE_FLIGHTS_ENDPOINT]
    assert "post" in google_endpoint
    assert "requestBody" in google_endpoint["post"]
    assert "responses" in google_endpoint["post"]
