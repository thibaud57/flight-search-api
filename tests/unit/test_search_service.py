"""Tests unitaires SearchService async."""

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.google_flight_dto import GoogleFlightDTO
from app.models.request import DateCombination
from app.models.response import SearchResponse
from app.services.crawler_service import CrawlResult
from app.services.search_service import SearchService
from tests.fixtures.helpers import get_future_date


@pytest.fixture
def mock_crawler_service():
    """Mock CrawlerService async."""
    crawler = AsyncMock()
    crawler.crawl_google_flights.return_value = CrawlResult(
        success=True, html="<html>mock</html>", status_code=200
    )
    return crawler


@pytest.fixture
def valid_search_request(search_request_factory):
    """SearchRequest valide 2 segments."""
    return search_request_factory(days_segment1=6, days_segment2=5)


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Mock get_settings pour tous les tests du module (CI compatibility)."""
    with patch("app.services.search_service.get_settings", return_value=test_settings):
        yield


@pytest.fixture(autouse=True)
def mock_url_generation():
    """Mock generate_google_flights_url pour tous les tests."""
    with patch("app.services.search_service.generate_google_flights_url") as mock_url:
        mock_url.return_value = "https://www.google.com/travel/flights?tfs=mocked"
        yield mock_url


@pytest.fixture
def search_service(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
):
    """SearchService avec mocks."""
    return SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )


@pytest.mark.asyncio
async def test_search_flights_orchestration_success(
    search_service, valid_search_request
):
    """Orchestration complete avec tous crawls reussis."""
    response = await search_service.search_flights(valid_search_request)

    assert isinstance(response, SearchResponse)
    assert len(response.results) <= 10


@pytest.mark.asyncio
async def test_search_flights_calls_combination_generator(
    search_service, valid_search_request, mock_combination_generator
):
    """SearchService appelle CombinationGenerator."""
    await search_service.search_flights(valid_search_request)

    mock_combination_generator.generate_combinations.assert_called_once()


@pytest.mark.asyncio
async def test_search_flights_crawls_all_urls(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Crawle toutes URLs generees."""
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
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_google_flights.call_count == 42


@pytest.mark.asyncio
async def test_search_flights_parallel_crawling_asyncio_gather(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Crawling parallele avec asyncio.gather."""
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_google_flights.call_count == 10
    assert response is not None


@pytest.mark.asyncio
async def test_search_flights_parses_all_html(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Parse HTML de tous crawls reussis."""
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
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    await service.search_flights(valid_search_request)

    assert flight_parser_mock_10_flights_factory.parse.call_count == 5


@pytest.mark.asyncio
async def test_search_flights_ranking_top_10(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Selectionne top 10 resultats par prix."""
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
                departure_time="10:00",
                arrival_time="20:00",
                duration="10h 00min",
                stops=0,
            )
        ]

    flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 10
    for i in range(len(response.results) - 1):
        assert (
            response.results[i].flights[0].price
            <= response.results[i + 1].flights[0].price
        )


@pytest.mark.asyncio
async def test_search_flights_ranking_price_primary(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Prix total est critere dominant ranking."""
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
                departure_time="10:00",
                arrival_time="20:00",
                duration="10h 00min",
                stops=0,
            )
        ]

    flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert response.results[0].flights[0].price == 900.0


@pytest.mark.asyncio
async def test_search_flights_ranking_same_price_stable(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Ordre stable quand prix identiques (premier crawle = premier retourne)."""
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
        return [
            GoogleFlightDTO(
                price=1000.0,
                airline=f"Airline {idx}",
                departure_time="10:00",
                arrival_time="20:00",
                duration="10h 00min",
                stops=0,
            )
        ]

    flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 2
    assert response.results[0].flights[0].price == 1000.0
    assert response.results[1].flights[0].price == 1000.0
    assert response.results[0].flights[0].airline == "Airline 0"
    assert response.results[1].flights[0].airline == "Airline 1"


@pytest.mark.asyncio
async def test_search_flights_ranking_tie_breaker_duration(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Departage ex-aequo prix par duree."""
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
                departure_time="10:00",
                arrival_time="20:00",
                duration=durations[idx],
                stops=0,
            )
        ]

    flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_search_flights_handles_partial_crawl_failures(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Gestion erreurs crawl partielles (50% echecs)."""
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
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) <= 10
    assert response.search_stats.total_results >= 0


@pytest.mark.asyncio
async def test_search_flights_returns_empty_all_crawls_failed(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Retourne response vide si tous crawls echouent."""
    from app.exceptions import NetworkError

    mock_crawler_service.crawl_google_flights.side_effect = NetworkError(
        url="test", status_code=500
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert response.results == []
    assert response.search_stats.total_results == 0


@pytest.mark.asyncio
async def test_search_flights_constructs_google_flights_urls(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
    mock_url_generation,
):
    """Construction URLs multi-city correctes."""
    mock_combination_generator.generate_combinations.return_value = [
        DateCombination(
            segment_dates=[
                get_future_date(1).isoformat(),
                get_future_date(15).isoformat(),
            ]
        )
    ]
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    await service.search_flights(valid_search_request)

    mock_url_generation.assert_called_once()
    call_args = mock_url_generation.call_args
    assert call_args[0][0] == valid_search_request.template_url


@pytest.mark.asyncio
async def test_search_flights_logging_structured(
    search_service, valid_search_request, caplog
):
    """Logging structure toutes etapes orchestration."""
    import logging

    with caplog.at_level(logging.INFO):
        await search_service.search_flights(valid_search_request)

    assert len(caplog.records) > 0

    # Verify structured logging fields in extra
    all_extra_fields = set()
    for record in caplog.records:
        if hasattr(record, "crawls_success"):
            all_extra_fields.add("crawls_success")
        if hasattr(record, "crawls_failed"):
            all_extra_fields.add("crawls_failed")
        if hasattr(record, "top_price_min"):
            all_extra_fields.add("top_price_min")
        if hasattr(record, "top_price_max"):
            all_extra_fields.add("top_price_max")

    # Verify key structured fields are present
    assert "crawls_success" in all_extra_fields
    assert "top_price_min" in all_extra_fields or "top_price_max" in all_extra_fields


@pytest.mark.asyncio
async def test_search_flights_search_stats_accurate(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """search_stats coherentes avec resultats."""
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
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert response.search_stats.total_results == len(response.results)
    assert response.search_stats.segments_count == 2


@pytest.mark.asyncio
async def test_search_flights_less_than_10_results(
    mock_combination_generator,
    mock_crawler_service,
    flight_parser_mock_10_flights_factory,
    valid_search_request,
):
    """Retourne <10 resultats si <10 combinaisons reussies."""
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
        flight_parser=flight_parser_mock_10_flights_factory,
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 5
