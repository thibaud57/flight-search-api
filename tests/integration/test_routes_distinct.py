"""Tests integration routes distinctes Google Flights et Kayak."""

from fastapi.testclient import TestClient

from tests.fixtures.helpers import (
    SEARCH_GOOGLE_FLIGHTS_ENDPOINT,
    SEARCH_KAYAK_ENDPOINT,
)


def test_route_google_flights_accessible(
    client_with_mock_search: TestClient, search_request_factory
):
    """Route Google Flights accessible et retourne 200."""
    request_data = search_request_factory(as_dict=True)

    response = client_with_mock_search.post(
        SEARCH_GOOGLE_FLIGHTS_ENDPOINT, json=request_data
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data


def test_route_kayak_accessible(
    client_with_mock_search: TestClient, search_request_factory
):
    """Route Kayak accessible et retourne 200 (mock)."""
    request_data = search_request_factory(as_dict=True)

    response = client_with_mock_search.post(SEARCH_KAYAK_ENDPOINT, json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["results"] == []
    assert "search_stats" in data


def test_old_route_search_flights_404(
    client_with_mock_search: TestClient, search_request_factory
):
    """Ancienne route /search-flights retourne 404."""
    request_data = search_request_factory(as_dict=True)

    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 404


def test_search_request_extra_field_forbidden(
    client_with_mock_search: TestClient, search_request_factory
):
    """SearchRequest avec champ provider extra doit etre rejete."""
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
