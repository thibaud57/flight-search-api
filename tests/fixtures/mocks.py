"""Mocks génériques réutilisables pour tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.proxy import ProxyConfig
from app.models.request import DateCombination
from app.models.response import FlightCombinationResult, SearchResponse, SearchStats
from app.services.combination_generator import CombinationGenerator
from tests.fixtures.helpers import GOOGLE_FLIGHTS_MOCKED_URL, get_future_date


@pytest.fixture
def mock_async_web_crawler():
    """Helper pour mocker AsyncWebCrawler avec context manager."""

    def _create(mock_result=None, side_effect=None):
        mock_crawler = AsyncMock()
        if side_effect:
            mock_crawler.arun.side_effect = side_effect
        elif mock_result:
            mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        return mock_crawler

    return _create


@pytest.fixture
def mock_combination_generator():
    """Mock CombinationGenerator avec 10 DateCombinations."""

    generator = MagicMock(spec=CombinationGenerator)
    start_date = get_future_date(1)
    generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                start_date.isoformat(),
                get_future_date(15).isoformat(),
            ]
        )
        for _ in range(10)
    ]
    return generator


@pytest.fixture
def mock_crawl_result():
    """CrawlResult valide mocké."""
    result = MagicMock()
    result.success = True
    result.html = "<html><body>Valid content</body></html>"
    result.status_code = 200
    return result


@pytest.fixture
def mock_search_service(flight_dto_factory):
    """Mock SearchService pour tests integration endpoint."""
    service = MagicMock()
    start_date = get_future_date(1)

    async def mock_search(request):
        results = [
            FlightCombinationResult(
                segment_dates=[
                    start_date.isoformat(),
                    get_future_date(15).isoformat(),
                ],
                flights=[
                    flight_dto_factory(
                        price=800.0 + i * 100,
                        airline="Test Airline",
                        departure_time="10:00",
                        arrival_time="14:00",
                        duration="4h",
                        stops=0,
                        departure_airport="Aéroport de Paris-Charles de Gaulle",
                        arrival_airport="Aéroport international de Tokyo-Haneda",
                    )
                ],
            )
            for i in range(10)
        ]

        return SearchResponse(
            results=results,
            search_stats=SearchStats(
                total_results=len(results),
                search_time_ms=100,
                segments_count=2,
            ),
        )

    service.search_flights = mock_search
    return service


@pytest.fixture
def mock_proxy_pool():
    """Pool de 3 proxies pour tests."""
    return [
        ProxyConfig(
            host=f"proxy{i}.decodo.com",
            port=40000 + i,
            username=f"proxy{i}user",
            password=f"proxy{i}pass",
            country="FR",
        )
        for i in range(3)
    ]


@pytest.fixture
def mock_search_service_full(flight_dto_factory):
    """Mock SearchService avec contrôle avancé (échecs, résultats partiels)."""

    def _create(
        num_results=10,
        base_price=800.0,
        price_increment=100.0,
        search_time_ms=100,
        segments_count=2,
        partial_failure=False,
        failure_rate=0.0,
    ):
        """Crée mock SearchService configurable."""
        service = MagicMock()
        start_date = get_future_date(1)

        async def mock_search(request):
            if failure_rate > 0 and partial_failure:
                actual_results = int(num_results * (1 - failure_rate))
            else:
                actual_results = num_results

            results = [
                FlightCombinationResult(
                    segment_dates=[
                        start_date.isoformat(),
                        get_future_date(15).isoformat(),
                    ],
                    flights=[
                        flight_dto_factory(
                            price=base_price + i * price_increment,
                            airline="Test Airline",
                            departure_time="10:00",
                            arrival_time="14:00",
                            duration="4h",
                            stops=0,
                            departure_airport="Aéroport de Paris-Charles de Gaulle",
                            arrival_airport="Aéroport international de Tokyo-Haneda",
                        )
                    ],
                )
                for i in range(actual_results)
            ]

            return SearchResponse(
                results=results,
                search_stats=SearchStats(
                    total_results=len(results),
                    search_time_ms=search_time_ms,
                    segments_count=segments_count,
                ),
            )

        service.search_flights = mock_search
        return service

    return _create


@pytest.fixture
def mock_generate_google_flights_url():
    """Mock generate_google_flights_url pour tests SearchService."""
    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = GOOGLE_FLIGHTS_MOCKED_URL
        yield mock_url_gen
