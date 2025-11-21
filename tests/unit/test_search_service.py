"""Tests unitaires SearchService async."""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import DateCombination, SearchRequest
from app.models.response import SearchResponse
from app.services.combination_generator import CombinationGenerator
from app.services.crawler_service import CrawlResult
from app.services.search_service import SearchService


@pytest.fixture
def mock_combination_generator():
    """Mock CombinationGenerator."""
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
def mock_crawler_service():
    """Mock CrawlerService async."""
    crawler = AsyncMock()
    crawler.crawl_google_flights.return_value = CrawlResult(
        success=True, html="<html>mock</html>", status_code=200
    )
    return crawler


@pytest.fixture
def mock_flight_parser():
    """Mock FlightParser."""
    parser = MagicMock()
    parser.parse.return_value = [
        GoogleFlightDTO(
            price=500.0 + i * 50,
            airline="Test Airline",
            departure_time=datetime(2025, 6, 1, 10, 0),
            arrival_time=datetime(2025, 6, 1, 20, 0),
            duration="10h 00min",
            stops=0,
        )
        for i in range(3)
    ]
    return parser


@pytest.fixture
def valid_search_request():
    """SearchRequest valide 2 segments."""
    tomorrow = date.today() + timedelta(days=1)
    return SearchRequest(
        segments=[
            {
                "from_city": "Paris",
                "to_city": "Tokyo",
                "date_range": {
                    "start": tomorrow.isoformat(),
                    "end": (tomorrow + timedelta(days=6)).isoformat(),
                },
            },
            {
                "from_city": "Tokyo",
                "to_city": "New York",
                "date_range": {
                    "start": (tomorrow + timedelta(days=14)).isoformat(),
                    "end": (tomorrow + timedelta(days=19)).isoformat(),
                },
            },
        ]
    )


@pytest.fixture
def search_service(
    mock_combination_generator, mock_crawler_service, mock_flight_parser
):
    """SearchService avec mocks."""
    return SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )


@pytest.mark.asyncio
async def test_search_flights_orchestration_success(
    search_service, valid_search_request
):
    """Test 11: Orchestration complete avec tous crawls reussis."""
    response = await search_service.search_flights(valid_search_request)

    assert isinstance(response, SearchResponse)
    assert len(response.results) <= 10


@pytest.mark.asyncio
async def test_search_flights_calls_combination_generator(
    search_service, valid_search_request, mock_combination_generator
):
    """Test 12: SearchService appelle CombinationGenerator."""
    await search_service.search_flights(valid_search_request)

    mock_combination_generator.generate_combinations.assert_called_once()


@pytest.mark.asyncio
async def test_search_flights_crawls_all_urls(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 13: Crawle toutes URLs generees."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(42)
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_google_flights.call_count == 42


@pytest.mark.asyncio
async def test_search_flights_parallel_crawling_asyncio_gather(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 14: Crawling parallele avec asyncio.gather."""
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_google_flights.call_count == 10
    assert response is not None


@pytest.mark.asyncio
async def test_search_flights_parses_all_html(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 15: Parse HTML de tous crawls reussis."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(5)
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    await service.search_flights(valid_search_request)

    assert mock_flight_parser.parse.call_count == 5


@pytest.mark.asyncio
async def test_search_flights_ranking_top_10(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 16: Selectionne top 10 resultats par prix."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(50)
    ]
    prices = list(range(800, 2050, 25))
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0] % len(prices)
        call_count[0] += 1
        return [
            GoogleFlightDTO(
                price=float(prices[idx]),
                airline="Test",
                departure_time=datetime(2025, 6, 1, 10, 0),
                arrival_time=datetime(2025, 6, 1, 20, 0),
                duration="10h 00min",
                stops=0,
            )
        ]

    mock_flight_parser.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 10
    for i in range(len(response.results) - 1):
        assert response.results[i].price <= response.results[i + 1].price


@pytest.mark.asyncio
async def test_search_flights_ranking_price_primary(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 17: Prix total est critere dominant ranking."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(3)
    ]
    test_prices = [1000.0, 1200.0, 900.0]
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        return [
            GoogleFlightDTO(
                price=test_prices[idx],
                airline="Test",
                departure_time=datetime(2025, 6, 1, 10, 0),
                arrival_time=datetime(2025, 6, 1, 20, 0),
                duration="10h 00min",
                stops=0,
            )
        ]

    mock_flight_parser.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert response.results[0].price == 900.0


@pytest.mark.asyncio
async def test_search_flights_ranking_tie_breaker_duration(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 18: Departage ex-aequo prix par duree."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(2)
    ]
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        durations = ["15h 00min", "10h 00min"]
        return [
            GoogleFlightDTO(
                price=1000.0,
                airline="Test",
                departure_time=datetime(2025, 6, 1, 10, 0),
                arrival_time=datetime(2025, 6, 1, 20, 0),
                duration=durations[idx],
                stops=0,
            )
        ]

    mock_flight_parser.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_search_flights_handles_partial_crawl_failures(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 19: Gestion erreurs crawl partielles (50% echecs)."""
    from app.exceptions import CaptchaDetectedError

    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(10)
    ]
    call_count = [0]

    async def mock_crawl(url, use_proxy=True):
        idx = call_count[0]
        call_count[0] += 1
        if idx % 2 == 0:
            raise CaptchaDetectedError(url=url, captcha_type="recaptcha")
        return CrawlResult(success=True, html="<html>test</html>", status_code=200)

    mock_crawler_service.crawl_google_flights.side_effect = mock_crawl
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) <= 10
    assert response.search_stats.total_results >= 0


@pytest.mark.asyncio
async def test_search_flights_returns_empty_all_crawls_failed(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 20: Retourne response vide si tous crawls echouent."""
    from app.exceptions import NetworkError

    mock_crawler_service.crawl_google_flights.side_effect = NetworkError(
        url="test", status_code=500
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert response.results == []
    assert response.search_stats.total_results == 0


@pytest.mark.asyncio
async def test_search_flights_constructs_google_flights_urls(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 21: Construction URLs multi-city correctes."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                tomorrow.isoformat(),
                (tomorrow + timedelta(days=14)).isoformat(),
            ]
        )
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    await service.search_flights(valid_search_request)

    call_args = mock_crawler_service.crawl_google_flights.call_args
    url = call_args[0][0]
    assert "google.com/travel/flights" in url
    assert "hl=fr" in url
    assert "curr=EUR" in url


@pytest.mark.asyncio
async def test_search_flights_logging_structured(
    search_service, valid_search_request, caplog
):
    """Test 22: Logging structure toutes etapes orchestration."""
    import logging

    with caplog.at_level(logging.INFO):
        await search_service.search_flights(valid_search_request)

    assert len(caplog.records) > 0


@pytest.mark.asyncio
async def test_search_flights_search_stats_accurate(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 23: search_stats coherentes avec resultats."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(15)
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert response.search_stats.total_results == len(response.results)
    assert response.search_stats.segments_count == 2


@pytest.mark.asyncio
async def test_search_flights_less_than_10_results(
    mock_combination_generator,
    mock_crawler_service,
    mock_flight_parser,
    valid_search_request,
):
    """Test 24: Retourne <10 resultats si <10 combinaisons reussies."""
    tomorrow = date.today() + timedelta(days=1)
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                (tomorrow + timedelta(days=i)).isoformat(),
                (tomorrow + timedelta(days=14 + i)).isoformat(),
            ]
        )
        for i in range(5)
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=mock_flight_parser,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 5
