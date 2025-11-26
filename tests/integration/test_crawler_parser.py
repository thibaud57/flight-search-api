"""Tests intégration CrawlerService + GoogleFlightParser."""

from unittest.mock import patch

import pytest

from app.exceptions import ParsingError
from app.services import CrawlerService, GoogleFlightParser
from tests.fixtures.helpers import BASE_URL, assert_flight_dto_valid

EMPTY_HTML = "<html><body><div class='no-results'>Aucun vol trouvé</div></body></html>"


async def _crawl_with_mock(mock_crawler):
    """Helper : Patch AsyncWebCrawler et retourne crawl_result."""
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value = mock_crawler
        crawler_service = CrawlerService()
        return await crawler_service.crawl_google_flights(BASE_URL)


@pytest.mark.asyncio
async def test_integration_crawl_and_parse_success(
    google_flights_html_factory, mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl URL → Parse HTML → 10 Flight validés."""
    html = google_flights_html_factory(
        num_flights=10, base_price=100.0, price_increment=50.0
    )
    mock_result = mock_crawl_result_factory(html=html)
    mock_crawler = mock_async_web_crawler(mock_result=mock_result)

    crawl_result = await _crawl_with_mock(mock_crawler)

    assert crawl_result.success is True
    parser = GoogleFlightParser()
    flights = parser.parse(crawl_result.html)
    assert len(flights) == 10
    for flight in flights:
        assert_flight_dto_valid(flight)


@pytest.mark.asyncio
async def test_integration_crawl_success_parse_zero_flights(
    mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl success mais parsing échoue (aucun vol)."""
    mock_result = mock_crawl_result_factory(html=EMPTY_HTML)
    mock_crawler = mock_async_web_crawler(mock_result=mock_result)

    crawl_result = await _crawl_with_mock(mock_crawler)

    assert crawl_result.success is True
    parser = GoogleFlightParser()
    with pytest.raises(ParsingError) as exc_info:
        parser.parse(crawl_result.html)
    assert "No flights found" in str(exc_info.value)
