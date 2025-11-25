"""Tests integration retry logic avec scénarios multi-combinaisons."""

from contextlib import asynccontextmanager
from unittest.mock import patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.models.response import SearchResponse
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlerService
from app.services.proxy_service import ProxyService
from app.services.search_service import SearchService
from tests.fixtures.helpers import MOCK_URL


@pytest.fixture
def mock_crawler_with_errors_factory(mock_async_web_crawler, mock_crawl_result):
    """Factory pour créer crawlers avec patterns erreurs configurables."""

    def _create(
        error_calls=None,
        error_type="network",
        captcha_calls=None,
        status_404_calls=None,
    ):
        call_count = [0]
        captcha_triggered = set()

        async def arun_side_effect(*args, **kwargs):
            call_count[0] += 1
            current_call = call_count[0]

            if error_calls and current_call in error_calls:
                if error_type == "network":
                    raise NetworkError(url=MOCK_URL, status_code=None, attempts=1)
                elif error_type == "network_persistent":
                    raise NetworkError(url=MOCK_URL, status_code=503, attempts=3)

            if (
                error_type == "captcha"
                and captcha_calls
                and current_call in captcha_calls
                and current_call not in captcha_triggered
            ):
                captcha_triggered.add(current_call)
                raise CaptchaDetectedError(url=MOCK_URL, captcha_type="recaptcha_v2")

            if error_type == "mixed":
                if error_calls and current_call in error_calls:
                    raise NetworkError(url=MOCK_URL, status_code=None, attempts=1)
                if (
                    captcha_calls
                    and current_call in captcha_calls
                    and current_call not in captcha_triggered
                ):
                    captcha_triggered.add(current_call)
                    raise CaptchaDetectedError(
                        url=MOCK_URL, captcha_type="recaptcha_v2"
                    )

            if status_404_calls and current_call in status_404_calls:
                result = mock_async_web_crawler().arun.return_value
                result.success = False
                result.html = ""
                result.status_code = 404
                return result

            return mock_crawl_result

        return mock_async_web_crawler(
            mock_result=mock_crawl_result, side_effect=arun_side_effect
        )

    return _create


@asynccontextmanager
async def _patch_crawler_and_search(crawler, proxy_pool, flight_parser):
    """Context manager : patch AsyncWebCrawler et crée SearchService."""
    proxy_service = ProxyService(proxy_pool)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value.__aenter__.return_value = crawler
        crawler_service = CrawlerService(proxy_service=proxy_service)
        combination_generator = CombinationGenerator()
        search_service = SearchService(
            combination_generator=combination_generator,
            crawler_service=crawler_service,
            flight_parser=flight_parser,
        )
        yield search_service


@pytest.mark.asyncio
async def test_integration_search_with_transient_errors(
    mock_crawler_with_errors_factory,
    flight_parser_mock_single_factory,
    mock_proxy_pool,
    search_request_factory,
) -> None:
    """Test retry logic avec erreurs transitoires 30%."""
    crawler = mock_crawler_with_errors_factory(error_calls=[2, 5], error_type="network")

    async with _patch_crawler_and_search(
        crawler, mock_proxy_pool, flight_parser_mock_single_factory
    ) as search_service:
        request = search_request_factory(days_segment1=2, days_segment2=2)

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 2
        assert response.search_stats.total_results >= 2
        assert response.search_stats.search_time_ms < 30000


@pytest.mark.asyncio
async def test_integration_retry_exhaustion_graceful_degradation(
    mock_crawler_with_errors_factory,
    flight_parser_mock_single_factory,
    mock_proxy_pool,
    search_request_factory,
) -> None:
    """Test graceful degradation avec erreurs persistantes 40%."""
    crawler = mock_crawler_with_errors_factory(
        error_calls=[2, 5, 8, 11, 14], error_type="network_persistent"
    )

    async with _patch_crawler_and_search(
        crawler, mock_proxy_pool, flight_parser_mock_single_factory
    ) as search_service:
        request = search_request_factory(
            days_segment1=5, days_segment2=3, offset_segment2=12
        )

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 5
        assert response.search_stats.total_results >= 5


@pytest.mark.asyncio
async def test_integration_partial_retry_success(
    mock_crawler_with_errors_factory,
    flight_parser_mock_single_factory,
    mock_proxy_pool,
    search_request_factory,
) -> None:
    """Test retry success avec captcha 50% puis proxy rotation."""
    crawler = mock_crawler_with_errors_factory(
        captcha_calls=[2, 4, 6, 8, 10], error_type="captcha"
    )

    async with _patch_crawler_and_search(
        crawler, mock_proxy_pool, flight_parser_mock_single_factory
    ) as search_service:
        request = search_request_factory(days_segment1=4, days_segment2=4)

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8


@pytest.mark.asyncio
async def test_integration_no_retry_on_client_errors(
    mock_crawler_with_errors_factory,
    flight_parser_mock_single_factory,
    mock_proxy_pool,
    search_request_factory,
) -> None:
    """Test aucun retry sur erreurs 404."""
    crawler = mock_crawler_with_errors_factory(status_404_calls=[3, 7, 11, 15])

    async with _patch_crawler_and_search(
        crawler, mock_proxy_pool, flight_parser_mock_single_factory
    ) as search_service:
        request = search_request_factory(days_segment1=4, days_segment2=4)

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 6
        assert response.search_stats.total_results >= 6


@pytest.mark.asyncio
async def test_integration_end_to_end_retry_metrics_logging(
    mock_crawler_with_errors_factory,
    flight_parser_mock_single_factory,
    mock_proxy_pool,
    search_request_factory,
    caplog,
) -> None:
    """Test logs retry avec erreurs mixtes."""
    crawler = mock_crawler_with_errors_factory(
        error_calls=[2, 5, 8, 12], captcha_calls=[4, 10], error_type="mixed"
    )

    async with _patch_crawler_and_search(
        crawler, mock_proxy_pool, flight_parser_mock_single_factory
    ) as search_service:
        request = search_request_factory(days_segment1=4, days_segment2=4)

        response = await search_service.search_flights(request)

        assert isinstance(response, SearchResponse)
        assert len(response.results) >= 8
        assert response.search_stats.total_results >= 8
        assert any(
            "Retry attempt triggered" in record.message for record in caplog.records
        )
