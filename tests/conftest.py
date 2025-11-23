"""Configuration pytest globale pour tous les tests."""

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_search_service
from app.core.config import Settings, get_settings
from app.core.logger import get_logger, setup_logger
from app.main import app
from app.models.google_flight_dto import GoogleFlightDTO
from app.models.response import FlightCombinationResult, SearchResponse, SearchStats


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Settings mocké pour tests avec valeurs par défaut.

    Scope session car Settings sont immuables et identiques pour tous tests.
    """
    return Settings(
        DECODO_USERNAME="customer-test-country-FR",
        DECODO_PASSWORD="test_password",
        LOG_LEVEL="INFO",
    )


@pytest.fixture(scope="function")
def client(test_settings: Settings) -> TestClient:
    """TestClient FastAPI avec Settings + Logger override + cache clear.

    Scope function pour isolation complète entre tests (évite pollution état).

    Override both get_settings AND get_logger to prevent ValidationError in CI.
    get_logger() calls get_settings() directly (not via Depends), so
    app.dependency_overrides[get_settings] alone is not enough.

    Clear caches before and after to avoid flaky tests with @lru_cache.
    Conforms to FastAPI 2025 best practices.
    Cleanup automatique après chaque test.
    """
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()


@pytest.fixture
def valid_search_request_data():
    """Request data valide pour tests search endpoint (2 segments)."""
    tomorrow = date.today() + timedelta(days=1)
    return {
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


@pytest.fixture
def mock_search_service():
    """Mock SearchService pour tests integration endpoint."""
    service = MagicMock()
    tomorrow = date.today() + timedelta(days=1)

    async def mock_search(request):
        results = [
            FlightCombinationResult(
                segment_dates=[
                    tomorrow.isoformat(),
                    (tomorrow + timedelta(days=14)).isoformat(),
                ],
                flights=[
                    GoogleFlightDTO(
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
                total_results=10, search_time_ms=100, segments_count=2
            ),
        )

    service.search_flights = mock_search
    return service


@pytest.fixture(scope="function")
def client_with_mock_search(test_settings: Settings, mock_search_service):
    """TestClient avec SearchService mocke."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger
    app.dependency_overrides[get_search_service] = lambda: mock_search_service

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()


@pytest.fixture
def mock_crawl_result():
    """Mock CrawlResult success (partagé entre tests crawler/proxy)."""
    result = MagicMock()
    result.success = True
    result.html = "<html><body>Valid Google Flights HTML</body></html>"
    result.status_code = 200
    return result


@pytest.fixture
def mock_crawler_success():
    """Mock CrawlerService async avec HTML valide (partagé tests integration)."""
    from unittest.mock import AsyncMock

    from app.services.crawler_service import CrawlResult

    crawler = AsyncMock()
    crawler.crawl_google_flights.return_value = CrawlResult(
        success=True, html="<html>valid</html>", status_code=200
    )
    return crawler


@pytest.fixture
def mock_flight_parser_10_flights():
    """Mock FlightParser retournant 10 vols avec strings (partagé tests integration)."""
    parser = MagicMock()
    parser.parse.return_value = [
        GoogleFlightDTO(
            price=500.0 + i * 100,
            airline="Test Airline",
            departure_time="10:00",
            arrival_time="20:00",
            duration="10h 00min",
            stops=i % 3,
        )
        for i in range(10)
    ]
    return parser


@pytest.fixture
def mock_combination_generator():
    """Mock CombinationGenerator avec 10 DateCombinations (partagé tests unit)."""
    from app.models.request import DateCombination
    from app.services.combination_generator import CombinationGenerator

    generator = MagicMock(spec=CombinationGenerator)
    tomorrow = date.today() + timedelta(days=1)
    generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                tomorrow.isoformat(),
                (tomorrow + timedelta(days=14)).isoformat(),
            ]
        )
        for _ in range(10)
    ]
    return generator


@pytest.fixture
def proxy_pool():
    """Pool de 3 proxies pour tests (partagé unit + integration)."""
    from app.models.proxy import ProxyConfig

    return [
        ProxyConfig(
            host="fr.decodo.com",
            port=40000,
            username="proxy0user",
            password="password0",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40001,
            username="proxy1user",
            password="password1",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40002,
            username="proxy2user",
            password="password2",
            country="FR",
        ),
    ]


@pytest.fixture(autouse=True)
def mock_generate_google_flights_url():
    """Mock automatique de generate_google_flights_url pour tous les tests."""
    from unittest.mock import patch

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        yield mock_url_gen
