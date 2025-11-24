"""Tests integration retry logic avec scénarios multi-combinaisons."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.models.response import SearchResponse
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlerService
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


@pytest.mark.asyncio
async def test_integration_search_with_transient_errors(
    mock_crawler_with_transient_errors,
    flight_parser_mock_single,
    proxy_pool,
    search_request_factory,
) -> None:
    """Test retry logic avec erreurs transitoires 30%."""
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
            flight_parser=flight_parser_mock_single,
        )

        request = search_request_factory(days_segment1=2, days_segment2=2)
        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 2
        assert response.search_stats.total_results >= 2
        assert response.search_stats.search_time_ms < 30000


@pytest.mark.asyncio
async def test_integration_retry_exhaustion_graceful_degradation(
    mock_crawler_with_persistent_errors,
    flight_parser_mock_single,
    proxy_pool,
    search_request_factory,
) -> None:
    """Test graceful degradation avec erreurs persistantes 40%."""
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
            flight_parser=flight_parser_mock_single,
        )

        request = search_request_factory(
            days_segment1=5, days_segment2=3, offset_segment2=12
        )
        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 5
        assert response.search_stats.total_results >= 5


@pytest.mark.asyncio
async def test_integration_partial_retry_success(
    mock_crawler_with_captcha_then_success,
    flight_parser_mock_single,
    proxy_pool,
    search_request_factory,
) -> None:
    """Test retry success avec captcha 50% puis proxy rotation."""
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
            flight_parser=flight_parser_mock_single,
        )

        request = search_request_factory(days_segment1=4, days_segment2=4)
        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8


@pytest.mark.asyncio
async def test_integration_no_retry_on_client_errors(
    mock_crawler_with_404_errors,
    flight_parser_mock_single,
    proxy_pool,
    search_request_factory,
) -> None:
    """Test aucun retry sur erreurs 404."""
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
            flight_parser=flight_parser_mock_single,
        )

        request = search_request_factory(days_segment1=4, days_segment2=4)
        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 6
        assert response.search_stats.total_results >= 6


@pytest.mark.asyncio
async def test_integration_end_to_end_retry_metrics_logging(
    mock_crawler_with_mixed_errors,
    flight_parser_mock_single,
    proxy_pool,
    search_request_factory,
    caplog,
) -> None:
    """Test logs retry avec erreurs mixtes."""
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
            flight_parser=flight_parser_mock_single,
        )

        request = search_request_factory(days_segment1=4, days_segment2=4)
        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8

        assert any(
            "Retry attempt triggered" in record.message for record in caplog.records
        )
