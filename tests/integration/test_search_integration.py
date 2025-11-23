"""Tests integration SearchService."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import SearchRequest
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlResult
from app.services.search_service import SearchService


@pytest.mark.asyncio
async def test_integration_search_two_segments_success(
    mock_crawler_success, mock_flight_parser_10_flights
):
    """Orchestration complete 2 segments (7x6=42 combinaisons)."""
    from app.models.request import DateRange

    tomorrow = date.today() + timedelta(days=1)
    request = SearchRequest(
        template_url="https://www.google.com/travel/flights?tfs=test",
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=6)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=14)).isoformat(),
                end=(tomorrow + timedelta(days=19)).isoformat(),
            ),
        ],
    )
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=mock_flight_parser_10_flights,
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
    mock_crawler_success, mock_flight_parser_10_flights
):
    """5 segments asymetriques (15x2x2x2x2=240 combinaisons)."""
    from app.models.request import DateRange

    tomorrow = date.today() + timedelta(days=1)
    request = SearchRequest(
        template_url="https://www.google.com/travel/flights?tfs=test",
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=14)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=20)).isoformat(),
                end=(tomorrow + timedelta(days=21)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=25)).isoformat(),
                end=(tomorrow + timedelta(days=26)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=30)).isoformat(),
                end=(tomorrow + timedelta(days=31)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=35)).isoformat(),
                end=(tomorrow + timedelta(days=36)).isoformat(),
            ),
        ],
    )
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        flight_parser=mock_flight_parser_10_flights,
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
    mock_flight_parser_10_flights,
):
    """40% echecs captcha."""
    from app.exceptions import CaptchaDetectedError
    from app.models.request import DateRange

    tomorrow = date.today() + timedelta(days=1)
    request = SearchRequest(
        template_url="https://www.google.com/travel/flights?tfs=test",
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=9)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=14)).isoformat(),
                end=(tomorrow + timedelta(days=21)).isoformat(),
            ),
        ],
    )
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
        flight_parser=mock_flight_parser_10_flights,
    )

    with patch(
        "app.services.search_service.generate_google_flights_url"
    ) as mock_url_gen:
        mock_url_gen.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        response = await service.search_flights(request)

        assert len(response.results) <= 10
        assert response.search_stats.total_results > 0


@pytest.mark.asyncio
async def test_integration_search_dates_ranking(mock_crawler_success):
    """Ranking par prix avec dates differentes."""
    from app.models.request import DateRange

    tomorrow = date.today() + timedelta(days=1)
    request = SearchRequest(
        template_url="https://www.google.com/travel/flights?tfs=test",
        segments_date_ranges=[
            DateRange(
                start=tomorrow.isoformat(),
                end=(tomorrow + timedelta(days=6)).isoformat(),
            ),
            DateRange(
                start=(tomorrow + timedelta(days=14)).isoformat(),
                end=(tomorrow + timedelta(days=19)).isoformat(),
            ),
        ],
    )
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
    client_with_mock_search, valid_search_request_data
):
    """Endpoint POST /api/v1/search-flights."""
    response = client_with_mock_search.post(
        "/api/v1/search-flights", json=valid_search_request_data
    )

    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "search_stats" in data
    assert len(data["results"]) <= 10
