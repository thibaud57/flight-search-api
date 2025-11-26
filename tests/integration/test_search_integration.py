"""Tests integration SearchService."""

from unittest.mock import AsyncMock

import pytest

from app.exceptions import CaptchaDetectedError
from app.models import SearchRequest
from app.services import CombinationGenerator, CrawlResult, SearchService
from tests.fixtures.helpers import (
    TEMPLATE_URL,
    assert_results_sorted_by_price,
)


@pytest.mark.asyncio
async def test_integration_search_two_segments_success(
    mock_crawler_success,
    flight_parser_mock_10_flights_factory,
    search_request_factory,
    mock_generate_google_flights_url,
):
    """Orchestration complete 2 segments (7x6=42 combinaisons)."""
    request = search_request_factory(days_segment1=6, days_segment2=5)
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(request)

    assert len(response.results) == 10
    assert_results_sorted_by_price(response.results)
    assert mock_crawler_success.crawl_google_flights.call_count == 42


@pytest.mark.asyncio
async def test_integration_search_five_segments_asymmetric(
    mock_crawler_success,
    flight_parser_mock_10_flights_factory,
    date_range_factory,
    mock_generate_google_flights_url,
):
    """5 segments asymetriques (15x2x2x2x2=240 combinaisons)."""
    request = SearchRequest(
        template_url=TEMPLATE_URL,
        segments_date_ranges=[
            date_range_factory(start_offset=1, duration=14),
            date_range_factory(start_offset=20, duration=1),
            date_range_factory(start_offset=25, duration=1),
            date_range_factory(start_offset=30, duration=1),
            date_range_factory(start_offset=35, duration=1),
        ],
    )
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(request)

    assert len(response.results) == 10
    assert mock_crawler_success.crawl_google_flights.call_count == 240


@pytest.mark.asyncio
async def test_integration_search_with_captcha_partial_failures(
    flight_parser_mock_10_flights_factory,
    search_request_factory,
    mock_generate_google_flights_url,
):
    """40% echecs captcha."""
    request = search_request_factory(days_segment1=9, days_segment2=7)
    call_count = [0]
    mock_crawler = AsyncMock()

    async def mock_crawl(url, use_proxy=True):
        idx = call_count[0]
        call_count[0] += 1
        if idx % 5 < 2:
            raise CaptchaDetectedError(url=url, captcha_type="recaptcha")
        return CrawlResult(success=True, html="<html>valid</html>", status_code=200)

    mock_crawler.crawl_google_flights.side_effect = mock_crawl
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(request)

    assert len(response.results) <= 10
    assert response.search_stats.total_results > 0


@pytest.mark.asyncio
async def test_integration_search_dates_ranking(
    mock_crawler_success,
    search_request_factory,
    flight_dto_factory,
    flight_parser_mock_factory,
    mock_generate_google_flights_url,
):
    """Ranking par prix avec dates differentes."""
    request = search_request_factory(days_segment1=6, days_segment2=5)
    call_count = [0]
    mock_parser = flight_parser_mock_factory(num_flights=1)

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        price = 800.0 + (idx % 10) * 100
        return [flight_dto_factory(price=price)]

    mock_parser.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=mock_parser,
    )

    response = await service.search_flights(request)

    assert len(response.results) == 10
    assert_results_sorted_by_price(response.results)
