from datetime import date, timedelta

import pytest

from app.models.request import DateRange, SearchRequest
from app.services.search_service import SearchService


@pytest.fixture
def valid_search_request() -> SearchRequest:
    """Retourne une requete de recherche valide."""
    start = (date.today() + timedelta(days=1)).isoformat()
    end = (date.today() + timedelta(days=15)).isoformat()
    return SearchRequest(
        destinations=["Paris", "Tokyo"], date_range=DateRange(start=start, end=end)
    )


@pytest.fixture
def search_service() -> SearchService:
    """Retourne une instance SearchService."""
    return SearchService()


class TestSearchServiceMock:
    def test_search_service_returns_10_results(
        self, search_service: SearchService, valid_search_request: SearchRequest
    ) -> None:
        response = search_service.search_flights(valid_search_request)
        assert len(response.results) == 10

    def test_search_service_results_sorted_by_price(
        self, search_service: SearchService, valid_search_request: SearchRequest
    ) -> None:
        response = search_service.search_flights(valid_search_request)
        assert len(response.results) == 10
        assert response.results[0].price < response.results[9].price
        for i in range(len(response.results) - 1):
            assert response.results[i].price <= response.results[i + 1].price

    def test_search_service_route_matches_request_destinations(
        self, search_service: SearchService, valid_search_request: SearchRequest
    ) -> None:
        response = search_service.search_flights(valid_search_request)
        for result in response.results:
            assert result.route == valid_search_request.destinations

    def test_search_service_search_stats_accurate(
        self, search_service: SearchService, valid_search_request: SearchRequest
    ) -> None:
        response = search_service.search_flights(valid_search_request)
        assert response.search_stats.total_results == 10
        assert response.search_stats.destinations_searched == [
            "Paris",
            "Tokyo",
        ]
        assert response.search_stats.search_time_ms > 0
        assert 30 <= response.search_stats.search_time_ms <= 80

    def test_search_service_deterministic_output(
        self, search_service: SearchService, valid_search_request: SearchRequest
    ) -> None:
        response1 = search_service.search_flights(valid_search_request)
        response2 = search_service.search_flights(valid_search_request)

        assert len(response1.results) == len(response2.results)
        for i in range(len(response1.results)):
            assert response1.results[i].price == response2.results[i].price
            assert response1.results[i].airline == response2.results[i].airline
            assert (
                response1.results[i].departure_date
                == response2.results[i].departure_date
            )
            assert response1.results[i].route == response2.results[i].route
