from datetime import date, timedelta

import pytest

from app.models.request import SearchRequest
from app.models.response import SearchResponse
from app.services.search_service import SearchService


@pytest.fixture
def search_service() -> SearchService:
    """Fixture pour SearchService."""
    return SearchService()


@pytest.fixture
def valid_search_request():
    """Fixture pour un SearchRequest valide."""
    tomorrow = date.today() + timedelta(days=1)
    return SearchRequest(
        segments=[
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
    )


def test_search_service_returns_10_results(search_service, valid_search_request):
    """Test 33: Service retourne 10 résultats."""
    response = search_service.search_flights(valid_search_request)

    assert isinstance(response, SearchResponse)
    assert len(response.results) == 10


def test_search_service_results_sorted_by_price(search_service, valid_search_request):
    """Test 34: Résultats triés prix croissant."""
    response = search_service.search_flights(valid_search_request)

    assert response.results[0].price < response.results[9].price

    for i in range(len(response.results) - 1):
        assert response.results[i].price <= response.results[i + 1].price


def test_search_service_segments_match_request(search_service, valid_search_request):
    """Test 35: Segments mock matchent structure request."""
    response = search_service.search_flights(valid_search_request)

    for result in response.results:
        assert len(result.segments) == len(valid_search_request.segments)


def test_search_service_search_stats_accurate(search_service):
    """Test 36: search_stats cohérentes."""
    tomorrow = date.today() + timedelta(days=1)
    request = SearchRequest(
        segments=[
            {
                "from_city": "City1",
                "to_city": "City2",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=2)).isoformat(),
                },
            },
            {
                "from_city": "City2",
                "to_city": "City3",
                "date_range": {
                    "start": (tomorrow + timedelta(days=5)).isoformat(),
                    "end": (tomorrow + timedelta(days=7)).isoformat(),
                },
            },
            {
                "from_city": "City3",
                "to_city": "City4",
                "date_range": {
                    "start": (tomorrow + timedelta(days=10)).isoformat(),
                    "end": (tomorrow + timedelta(days=12)).isoformat(),
                },
            },
        ]
    )

    response = search_service.search_flights(request)

    assert response.search_stats.total_results == 10
    assert response.search_stats.segments_count == 3
    assert response.search_stats.search_time_ms > 0
    assert response.search_stats.search_time_ms < 200


def test_search_service_deterministic_output(search_service, valid_search_request):
    """Test 37: Mock data identique pour inputs identiques."""
    response1 = search_service.search_flights(valid_search_request)
    response2 = search_service.search_flights(valid_search_request)

    for i in range(len(response1.results)):
        assert response1.results[i].price == response2.results[i].price
        assert response1.results[i].airline == response2.results[i].airline
        assert (
            response1.results[i].departure_date == response2.results[i].departure_date
        )


def test_search_service_handles_max_segments(search_service):
    """Test 38: Service gère 5 segments max."""
    tomorrow = date.today() + timedelta(days=1)

    segments = []
    for i in range(5):
        segments.append(
            {
                "from_city": f"City{i}",
                "to_city": f"City{i + 1}",
                "date_range": {
                    "start": (tomorrow + timedelta(days=i * 10)).isoformat(),
                    "end": (tomorrow + timedelta(days=i * 10 + 2)).isoformat(),
                },
            }
        )

    request = SearchRequest(segments=segments)
    response = search_service.search_flights(request)

    for result in response.results:
        assert len(result.segments) == 5
