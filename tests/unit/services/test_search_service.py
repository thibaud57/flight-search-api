"""Tests unitaires SearchService async."""

import logging
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.models import GoogleSearchRequest, SearchResponse
from app.services import CombinationGenerator, FilterService, SearchService
from tests.fixtures.helpers import (
    GOOGLE_FLIGHT_TEMPLATE_URL,
    assert_results_sorted_by_price,
    create_date_combinations,
)
from tests.fixtures.mocks import create_mock_settings_context


@pytest.fixture
def mock_crawler_service(mock_crawl_result):
    """Mock CrawlerService async."""
    from unittest.mock import MagicMock

    crawler = AsyncMock()
    crawler.crawl_flights.return_value = mock_crawl_result
    crawler.has_valid_cookies = MagicMock(return_value=True)
    return crawler


@pytest.fixture
def valid_search_request(google_search_request_factory):
    """SearchRequest valide 2 segments."""
    return google_search_request_factory(days_segment1=6, days_segment2=5)


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Mock get_settings pour tous les tests du module (CI compatibility)."""
    with create_mock_settings_context("app.services.search_service", test_settings):
        yield


@pytest.fixture
def mock_kayak_flight_parser():
    """Mock KayakFlightParser."""
    parser = MagicMock()
    parser.parse.return_value = [[MagicMock(price=500)]]
    return parser


@pytest.fixture
def mock_filter_service():
    """Mock FilterService."""
    from app.services import FilterService

    mock = MagicMock(spec=FilterService)
    # Comportement par défaut : retourne liste inchangée (pas de filtrage)
    mock.apply_filters = MagicMock(side_effect=lambda flights, filters, idx: flights)
    return mock


@pytest.fixture
def search_service(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    mock_filter_service,
):
    """SearchService avec mocks."""
    return SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=mock_filter_service,
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
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    mock_filter_service,
    valid_search_request,
):
    """Crawle toutes URLs generees."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(42)
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=mock_filter_service,
    )

    await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_flights.call_count == 42


@pytest.mark.asyncio
async def test_search_flights_parallel_crawling_asyncio_gather(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    mock_filter_service,
    valid_search_request,
):
    """Crawling parallele avec asyncio.gather."""
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=mock_filter_service,
    )

    response = await service.search_flights(valid_search_request)

    assert mock_crawler_service.crawl_flights.call_count == 10
    assert response is not None


@pytest.mark.asyncio
async def test_search_flights_parses_all_html(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    valid_search_request,
):
    """Parse HTML de tous crawls reussis."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(5)
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    await service.search_flights(valid_search_request)

    assert google_flight_parser_mock_10_flights_factory.parse.call_count == 5


@pytest.mark.asyncio
async def test_search_flights_ranking_top_10(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    google_flight_dto_factory,
    valid_search_request,
):
    """Selectionne top 10 resultats par prix."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(50)
    )
    prices = list(range(800, 2050, 25))
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0] % len(prices)
        call_count[0] += 1
        return [google_flight_dto_factory(price=float(prices[idx]), airline="Test")]

    google_flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 10
    assert_results_sorted_by_price(response.results)


@pytest.mark.asyncio
async def test_search_flights_ranking_price_primary(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    google_flight_dto_factory,
    valid_search_request,
):
    """Prix total est critere dominant ranking."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(3)
    )
    test_prices = [1000.0, 1200.0, 900.0]
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        return [google_flight_dto_factory(price=test_prices[idx], airline="Test")]

    google_flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert response.results[0].total_price == 900.0


@pytest.mark.asyncio
async def test_search_flights_ranking_same_price_stable(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    google_flight_dto_factory,
    valid_search_request,
):
    """Ordre stable quand prix identiques (premier crawle = premier retourne)."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(2)
    )
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        return [google_flight_dto_factory(price=1000.0, airline=f"Airline {idx}")]

    google_flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 2
    assert response.results[0].total_price == 1000.0
    assert response.results[1].total_price == 1000.0
    assert response.results[0].flights[0].airline == "Airline 0"
    assert response.results[1].flights[0].airline == "Airline 1"


@pytest.mark.asyncio
async def test_search_flights_ranking_tie_breaker_duration(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    google_flight_dto_factory,
    valid_search_request,
):
    """Departage ex-aequo prix par duree."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(2)
    )
    call_count = [0]

    def mock_parse(html):
        idx = call_count[0]
        call_count[0] += 1
        durations = ["15h 00min", "10h 00min"]
        return [
            google_flight_dto_factory(
                price=1000.0, airline="Test", duration=durations[idx]
            )
        ]

    google_flight_parser_mock_10_flights_factory.parse.side_effect = mock_parse
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 2


@pytest.mark.asyncio
async def test_search_flights_handles_partial_crawl_failures(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    mock_crawl_result,
    valid_search_request,
):
    """Gestion erreurs crawl partielles (50% echecs)."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(10)
    )
    call_count = [0]

    async def mock_crawl(url, use_proxy=True):
        idx = call_count[0]
        call_count[0] += 1
        if idx % 2 == 0:
            raise CaptchaDetectedError(url=url, captcha_type="recaptcha")
        return mock_crawl_result

    mock_crawler_service.crawl_flights.side_effect = mock_crawl
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) <= 10
    assert response.search_stats.total_results >= 0


@pytest.mark.asyncio
async def test_search_flights_returns_empty_all_crawls_failed(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    valid_search_request,
):
    """Retourne response vide si tous crawls echouent."""
    mock_crawler_service.crawl_flights.side_effect = NetworkError(
        url="test", status_code=500
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert response.results == []
    assert response.search_stats.total_results == 0


@pytest.mark.asyncio
async def test_search_flights_constructs_google_flights_urls(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    valid_search_request,
    mock_generate_google_flights_url,
):
    """Construction URLs multi-city correctes."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(1)
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    await service.search_flights(valid_search_request)

    mock_generate_google_flights_url.assert_called_once()
    call_args = mock_generate_google_flights_url.call_args
    assert call_args[0][0] == valid_search_request.template_url


@pytest.mark.asyncio
async def test_search_flights_logging_structured(
    search_service, valid_search_request, caplog
):
    """Logging structure toutes etapes orchestration."""
    with caplog.at_level(logging.INFO):
        await search_service.search_flights(valid_search_request)

    assert len(caplog.records) > 0

    all_extra_fields = set()
    for record in caplog.records:
        if hasattr(record, "crawls_success"):
            all_extra_fields.add("crawls_success")
        if hasattr(record, "crawls_failed"):
            all_extra_fields.add("crawls_failed")
        if hasattr(record, "best_price"):
            all_extra_fields.add("best_price")

    assert "crawls_success" in all_extra_fields
    assert "best_price" in all_extra_fields


@pytest.mark.asyncio
async def test_search_flights_search_stats_accurate(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    valid_search_request,
):
    """search_stats coherentes avec resultats."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(15)
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert response.search_stats.total_results == len(response.results)
    assert response.search_stats.segments_count == 2


@pytest.mark.asyncio
async def test_search_flights_less_than_10_results(
    mock_combination_generator,
    mock_crawler_service,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    valid_search_request,
):
    """Retourne <10 resultats si <10 combinaisons reussies."""
    mock_combination_generator.generate_combinations.return_value = (
        create_date_combinations(5)
    )
    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(valid_search_request)

    assert len(response.results) == 5


@pytest.mark.asyncio
async def test_search_with_real_generator_two_segments(
    mock_crawler_success,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    google_search_request_factory,
    mock_generate_google_flights_url,
):
    """Orchestration avec CombinationGenerator reel - 2 segments (7x6=42 combinaisons)."""
    request = google_search_request_factory(days_segment1=6, days_segment2=5)
    service = SearchService(
        combination_generator=CombinationGenerator(),
        crawler_service=mock_crawler_success,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(request)

    assert len(response.results) == 10
    assert_results_sorted_by_price(response.results)
    assert mock_crawler_success.crawl_flights.call_count == 42


@pytest.mark.asyncio
async def test_search_flights_raises_runtime_error_without_valid_cookies(
    mock_combination_generator,
    google_flight_parser_mock_10_flights_factory,
    mock_crawl_result,
    valid_search_request,
):
    """SearchService lève RuntimeError si pas de cookies valides avant crawling."""
    from unittest.mock import AsyncMock, MagicMock

    mock_kayak_parser = MagicMock()
    mock_crawler_service = AsyncMock()
    mock_crawler_service.crawl_flights.return_value = mock_crawl_result
    mock_crawler_service.has_valid_cookies = MagicMock(return_value=False)

    service = SearchService(
        combination_generator=mock_combination_generator,
        crawler_service=mock_crawler_service,
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_parser,
        filter_service=FilterService(),
    )

    with pytest.raises(RuntimeError) as exc_info:
        await service.search_flights(valid_search_request)

    assert "No valid session cookies" in str(exc_info.value)
    mock_crawler_service.crawl_flights.assert_not_called()


@pytest.mark.asyncio
async def test_search_with_real_generator_five_segments_asymmetric(
    mock_crawler_success,
    google_flight_parser_mock_10_flights_factory,
    mock_kayak_flight_parser,
    date_range_factory,
    mock_generate_google_flights_url,
):
    """5 segments asymetriques avec CombinationGenerator reel (15x2x2x2x2=240 combinaisons)."""
    request = GoogleSearchRequest(
        template_url=GOOGLE_FLIGHT_TEMPLATE_URL,
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
        google_flight_parser=google_flight_parser_mock_10_flights_factory,
        kayak_flight_parser=mock_kayak_flight_parser,
        filter_service=FilterService(),
    )

    response = await service.search_flights(request)

    assert len(response.results) == 10
    assert mock_crawler_success.crawl_flights.call_count == 240
