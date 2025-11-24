"""Tests integration SearchService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import SearchRequest
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlResult
from app.services.search_service import SearchService
from tests.fixtures.helpers import TEMPLATE_URL


@pytest.mark.asyncio
async def test_integration_search_two_segments_success(
    mock_crawler_success, flight_parser_mock_10_flights_factory, search_request_factory
):
    """Orchestration complete 2 segments (7x6=42 combinaisons)."""
    request = search_request_factory(days_segment1=6, days_segment2=5)
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        response = await service.search_flights(request)

        assert len(response.results) == 10
        for i in range(len(response.results) - 1):
            assert (
                response.results[i].flights[0].price
                <= response.results[i + 1].flights[0].price
            )
        assert mock_crawler_success.crawl_google_flights.call_count == 42


@pytest.mark.asyncio
async def test_integration_search_five_segments_asymmetric(
    mock_crawler_success, flight_parser_mock_10_flights_factory, date_range_factory
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

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        response = await service.search_flights(request)

        assert len(response.results) == 10
        assert mock_crawler_success.crawl_google_flights.call_count == 240


@pytest.mark.asyncio
async def test_integration_search_with_captcha_partial_failures(
    flight_parser_mock_10_flights_factory, search_request_factory
):
    """40% echecs captcha."""
    from app.exceptions import CaptchaDetectedError

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

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        response = await service.search_flights(request)

        assert len(response.results) <= 10
        assert response.search_stats.total_results > 0


@pytest.mark.asyncio
async def test_integration_search_dates_ranking(
    mock_crawler_success, search_request_factory
):
    """Ranking par prix avec dates differentes."""
    request = search_request_factory(days_segment1=6, days_segment2=5)
    call_count = [0]
    mock_parser = MagicMock()

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        price = 800.0 + (idx % 10) * 100
        return [
            GoogleFlightDTO(
                price=price,
                airline="Test",
                departure_time="10:00",
                arrival_time="20:00",
                duration="10h 00min",
                stops=0,
            )
        ]

    mock_parser.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=mock_parser,
    )

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        response = await service.search_flights(request)

        assert len(response.results) == 10
        assert (
            response.results[0].flights[0].price
            <= response.results[-1].flights[0].price
        )


def test_integration_end_to_end_search_endpoint(
    client_with_mock_search, search_request_factory
):
    """Endpoint POST /api/v1/search-flights."""
    request_data = search_request_factory(
        days_segment1=6, days_segment2=5, as_dict=True
    )
    response = client_with_mock_search.post("/api/v1/search-flights", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data
    assert len(data["results"]) <= 10
