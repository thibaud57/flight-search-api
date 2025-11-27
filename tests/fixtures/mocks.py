"""Mocks génériques réutilisables pour tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import (
    DateCombination,
    FlightCombinationResult,
    ProxyConfig,
    SearchResponse,
    SearchStats,
)
from app.services import CombinationGenerator, CrawlerService, CrawlResult
from tests.fixtures.helpers import GOOGLE_FLIGHT_BASE_URL, get_future_date


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
def mock_crawl_result_factory():
    """Factory pour créer CrawlResult mocké personnalisé."""

    def _create(
        html="<html><body>Valid content</body></html>", success=True, status_code=200
    ):
        """Crée CrawlResult mocké avec paramètres configurables."""
        result = MagicMock()
        result.success = success
        result.html = html
        result.status_code = status_code
        return result

    return _create


@pytest.fixture
def mock_search_service(google_flight_dto_factory):
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
                    google_flight_dto_factory(
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
            host=f"proxy{i}.example.com",
            port=40000 + i,
            username=f"proxy{i}user",
            password=f"proxy{i}pass",
            country="FR",
        )
        for i in range(3)
    ]


@pytest.fixture
def mock_crawler_success():
    """Mock CrawlerService async avec HTML valide (partagé tests integration)."""
    crawler = AsyncMock()
    crawler.crawl_flights.return_value = CrawlResult(
        success=True, html="<html>valid</html>", status_code=200
    )
    return crawler


@pytest.fixture
def mock_generate_google_flights_url():
    """Mock generate_google_flights_url pour tests SearchService."""
    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = GOOGLE_FLIGHT_BASE_URL
        yield mock_url_gen


def create_mock_settings_context(module_path: str, test_settings):
    """Helper pour créer context manager mock get_settings (évite duplication fixtures)."""
    return patch(f"{module_path}.get_settings", return_value=test_settings)


@pytest.fixture
def crawler_service():
    """Instance CrawlerService standard (mutualisé pour éviter duplication)."""
    return CrawlerService()
