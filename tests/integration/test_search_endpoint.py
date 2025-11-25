"""Tests integration endpoint search."""

from fastapi.testclient import TestClient

from tests.fixtures.helpers import (
    SEARCH_FLIGHTS_ENDPOINT,
    TEMPLATE_URL,
)


def test_end_to_end_search_request_valid(
    client_with_mock_search: TestClient, search_request_factory
) -> None:
    """Request valide retourne 200 avec SearchResponse."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post(SEARCH_FLIGHTS_ENDPOINT, json=request_data)

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


def test_end_to_end_validation_error_empty_segments(
    client_with_mock_search: TestClient,
) -> None:
    """Segments vide retourne 422."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [],
    }
    response = client_with_mock_search.post(SEARCH_FLIGHTS_ENDPOINT, json=request_data)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_end_to_end_validation_error_invalid_dates(
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
    response = client_with_mock_search.post(SEARCH_FLIGHTS_ENDPOINT, json=request_data)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_end_to_end_search_request_exact_dates(
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
    response = client_with_mock_search.post(SEARCH_FLIGHTS_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 10
    assert data["search_stats"]["segments_count"] == 2


def test_end_to_end_validation_error_too_many_segments(
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
    response = client_with_mock_search.post(SEARCH_FLIGHTS_ENDPOINT, json=request_data)

    assert response.status_code == 422
    assert "detail" in response.json()


def test_end_to_end_openapi_schema_includes_endpoint(
    client_with_mock_search: TestClient,
) -> None:
    """OpenAPI schema contient endpoint search-flights."""
    response = client_with_mock_search.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()

    assert "paths" in schema
    assert SEARCH_FLIGHTS_ENDPOINT in schema["paths"]

    endpoint = schema["paths"][SEARCH_FLIGHTS_ENDPOINT]
    assert "post" in endpoint

    post_spec = endpoint["post"]
    assert "requestBody" in post_spec
    assert "responses" in post_spec
