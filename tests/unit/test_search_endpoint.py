"""Tests unitaires endpoint search."""

from tests.fixtures.helpers import TEMPLATE_URL


def test_endpoint_accepts_valid_request(
    client_with_mock_search, search_request_factory
):
    """Endpoint accepte request valide."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data


def test_endpoint_validates_request_body(client_with_mock_search):
    """Body invalide rejete."""
    request_data = {
        "template_url": TEMPLATE_URL,
        "segments_date_ranges": [],
    }

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_endpoint_returns_10_results(client_with_mock_search, search_request_factory):
    """Endpoint retourne 10 resultats."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) == 10


def test_endpoint_response_matches_schema(
    client_with_mock_search, search_request_factory
):
    """Response conforme SearchResponse schema."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data

    assert isinstance(data["results"], list)
    assert len(data["results"]) > 0

    first_result = data["results"][0]
    assert "segment_dates" in first_result
    assert "flights" in first_result

    stats = data["search_stats"]
    assert "total_results" in stats
    assert "search_time_ms" in stats
    assert "segments_count" in stats


def test_endpoint_injects_search_service_dependency(
    client_with_mock_search, search_request_factory
):
    """SearchService injecte via Depends()."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
