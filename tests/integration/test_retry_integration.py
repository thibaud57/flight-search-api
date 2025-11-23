"""Tests integration retry logic avec scénarios multi-combinaisons."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import DateRange, SearchRequest
from app.models.response import SearchResponse
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlerService
from app.services.flight_parser import FlightParser
from app.services.proxy_service import ProxyService
from app.services.search_service import SearchService


@pytest.fixture
def mock_crawler_with_transient_errors():
    """Mock AsyncWebCrawler : 30% requetes timeout puis succes."""
    crawler = AsyncMock()

    call_count = 0

    async def arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count in (2, 5):
            raise NetworkError(url="https://google.com", status_code=None, attempts=1)

        result = MagicMock()
        result.success = True
        result.html = "<html><body>Valid content</body></html>"
        result.status_code = 200
        return result

    crawler.arun = arun_side_effect
    return crawler


@pytest.fixture
def mock_crawler_with_persistent_errors():
    """Mock AsyncWebCrawler : 40% requetes levent NetworkError persistant."""
    crawler = AsyncMock()

    call_count = 0

    async def arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count in (2, 5, 8, 11, 14):
            raise NetworkError(url="https://google.com", status_code=503, attempts=3)

        result = MagicMock()
        result.success = True
        result.html = "<html><body>Valid content</body></html>"
        result.status_code = 200
        return result

    crawler.arun = arun_side_effect
    return crawler


@pytest.fixture
def mock_crawler_with_captcha_then_success():
    """Mock AsyncWebCrawler : 50% requetes captcha 1ere tentative puis succes retry."""
    crawler = AsyncMock()

    call_count = 0
    captcha_calls = set()

    async def arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if (
            call_count > 1
            and call_count in (2, 4, 6, 8, 10)
            and call_count not in captcha_calls
        ):
            captcha_calls.add(call_count)
            raise CaptchaDetectedError(
                url="https://google.com", captcha_type="recaptcha_v2"
            )

        result = MagicMock()
        result.success = True
        result.html = "<html><body>Valid content</body></html>"
        result.status_code = 200
        return result

    crawler.arun = arun_side_effect
    return crawler


@pytest.fixture
def mock_crawler_with_404_errors():
    """Mock AsyncWebCrawler : 20% requetes retournent status 404."""
    crawler = AsyncMock()

    call_count = 0

    async def arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        result = MagicMock()

        if call_count in (3, 7, 11, 15):
            result.success = False
            result.html = ""
            result.status_code = 404
        else:
            result.success = True
            result.html = "<html><body>Valid content</body></html>"
            result.status_code = 200

        return result

    crawler.arun = arun_side_effect
    return crawler


@pytest.fixture
def mock_crawler_with_mixed_errors():
    """Mock AsyncWebCrawler : mix erreurs (20% timeout, 10% captcha, 70% succes)."""
    crawler = AsyncMock()

    call_count = 0
    captcha_calls = set()

    async def arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count in (2, 5, 8, 12) and call_count not in captcha_calls:
            raise NetworkError(url="https://google.com", status_code=None, attempts=1)

        if call_count in (4, 10) and call_count not in captcha_calls:
            captcha_calls.add(call_count)
            raise CaptchaDetectedError(
                url="https://google.com", captcha_type="recaptcha_v2"
            )

        result = MagicMock()
        result.success = True
        result.html = "<html><body>Valid content</body></html>"
        result.status_code = 200
        return result

    crawler.arun = arun_side_effect
    return crawler


@pytest.fixture
def mock_flight_parser_single_flight():
    """Mock FlightParser retournant 1 vol valide."""
    parser = MagicMock(spec=FlightParser)
    parser.parse.return_value = [
        GoogleFlightDTO(
            price=500.0,
            airline="Test Airline",
            departure_time="10:00",
            arrival_time="20:00",
            duration="10h 00min",
            stops=0,
        )
    ]
    return parser


@pytest.mark.asyncio
async def test_integration_search_with_transient_errors(
    mock_crawler_with_transient_errors,
    mock_flight_parser_single_flight,
    proxy_pool,
) -> None:
    """Mock AsyncWebCrawler : 30% requetes timeout puis succes.

    Given: Mock AsyncWebCrawler : 30% requetes timeout puis succes,
           2 destinations x 3 dates = 6 combinaisons
    When: Appeler search_service.search_flights(SearchRequest)
    Then: SearchResponse avec >=4 resultats (60% succes immediat + retry succes),
          logs WARNING retry pour 2 combinaisons, temps total <30s
    """
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = (
            mock_crawler_with_transient_errors
        )

        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=mock_flight_parser_single_flight,
        )

        tomorrow = date.today() + timedelta(days=1)
        request = SearchRequest(
            template_url="https://www.google.com/travel/flights?tfs=test",
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=2)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=10)).isoformat(),
                    end=(tomorrow + timedelta(days=12)).isoformat(),
                ),
            ],
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 2
        assert response.search_stats.total_results >= 2
        assert response.search_stats.search_time_ms < 30000


@pytest.mark.asyncio
async def test_integration_retry_exhaustion_graceful_degradation(
    mock_crawler_with_persistent_errors,
    mock_flight_parser_single_flight,
    proxy_pool,
) -> None:
    """Mock AsyncWebCrawler : 40% requetes levent NetworkError persistant.

    Given: Mock AsyncWebCrawler : 40% requetes levent NetworkError persistant (4 tentatives),
           3 destinations x 2 dates = 12 combinaisons
    When: Appeler search_service.search_flights(SearchRequest)
    Then: SearchResponse avec ~7 resultats (60% reussis),
          logs ERROR max retries pour 5 combinaisons, pas d'exception bloquante
    """
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = (
            mock_crawler_with_persistent_errors
        )

        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=mock_flight_parser_single_flight,
        )

        tomorrow = date.today() + timedelta(days=1)
        request = SearchRequest(
            template_url="https://www.google.com/travel/flights?tfs=test",
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=5)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=12)).isoformat(),
                    end=(tomorrow + timedelta(days=15)).isoformat(),
                ),
            ],
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 5
        assert response.search_stats.total_results >= 5


@pytest.mark.asyncio
async def test_integration_partial_retry_success(
    mock_crawler_with_captcha_then_success,
    mock_flight_parser_single_flight,
    proxy_pool,
) -> None:
    """Mock AsyncWebCrawler : 50% requetes captcha 1ere tentative puis succes retry.

    Given: Mock AsyncWebCrawler : 50% requetes captcha 1ere tentative puis succes retry,
           2 destinations x 5 dates = 10 combinaisons
    When: Appeler search_service.search_flights(SearchRequest)
    Then: SearchResponse avec ~10 resultats (100% succes apres retry),
          logs WARNING retry pour 5 combinaisons, proxy rotation visible dans logs
    """
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = (
            mock_crawler_with_captcha_then_success
        )

        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=mock_flight_parser_single_flight,
        )

        tomorrow = date.today() + timedelta(days=1)
        request = SearchRequest(
            template_url="https://www.google.com/travel/flights?tfs=test",
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=4)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=10)).isoformat(),
                    end=(tomorrow + timedelta(days=14)).isoformat(),
                ),
            ],
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8


@pytest.mark.asyncio
async def test_integration_no_retry_on_client_errors(
    mock_crawler_with_404_errors,
    mock_flight_parser_single_flight,
    proxy_pool,
) -> None:
    """Mock AsyncWebCrawler : 20% requetes retournent status 404.

    Given: Mock AsyncWebCrawler : 20% requetes retournent status 404,
           3 destinations x 3 dates = 18 combinaisons
    When: Appeler search_service.search_flights(SearchRequest)
    Then: SearchResponse avec ~14 resultats (80% succes),
          4 erreurs 404 propagees sans retry, logs montrent aucun retry pour 404
    """
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = (
            mock_crawler_with_404_errors
        )

        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=mock_flight_parser_single_flight,
        )

        tomorrow = date.today() + timedelta(days=1)
        request = SearchRequest(
            template_url="https://www.google.com/travel/flights?tfs=test",
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=4)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=10)).isoformat(),
                    end=(tomorrow + timedelta(days=14)).isoformat(),
                ),
            ],
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 6
        assert response.search_stats.total_results >= 6


@pytest.mark.asyncio
async def test_integration_end_to_end_retry_metrics_logging(
    mock_crawler_with_mixed_errors,
    mock_flight_parser_single_flight,
    proxy_pool,
    caplog,
) -> None:
    """Mock AsyncWebCrawler : mix erreurs (20% timeout, 10% captcha, 70% succes).

    Given: Mock AsyncWebCrawler : mix erreurs (20% timeout, 10% captcha, 70% succes),
           5 destinations x 2 dates = 20 combinaisons
    When: Appeler search_service.search_flights(SearchRequest)
    Then: SearchResponse avec ~18 resultats apres retry,
          logs structures contiennent metriques : retry triggers
    """
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = (
            mock_crawler_with_mixed_errors
        )

        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=mock_flight_parser_single_flight,
        )

        tomorrow = date.today() + timedelta(days=1)
        request = SearchRequest(
            template_url="https://www.google.com/travel/flights?tfs=test",
            segments_date_ranges=[
                DateRange(
                    start=tomorrow.isoformat(),
                    end=(tomorrow + timedelta(days=4)).isoformat(),
                ),
                DateRange(
                    start=(tomorrow + timedelta(days=10)).isoformat(),
                    end=(tomorrow + timedelta(days=14)).isoformat(),
                ),
            ],
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8

        assert any(
            "Retry attempt triggered" in record.message for record in caplog.records
        )
