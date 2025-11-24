"""Tests intégration CrawlerService + FlightParser."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import ParsingError
from app.services.crawler_service import CrawlerService
from app.services.flight_parser import FlightParser
from tests.fixtures.helpers import BASE_URL


@pytest.fixture
def empty_google_flights_html():
    """HTML Google Flights sans vols (cas spécifique parsing error)."""
    return "<html><body><div class='no-results'>Aucun vol trouvé</div></body></html>"


@pytest.mark.asyncio
async def test_integration_crawl_and_parse_success(google_flights_html_factory):
    """Crawl URL → Parse HTML → 10 Flight validés."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.html = google_flights_html_factory(
        num_flights=10, base_price=100.0, price_increment=50.0
    )
    mock_result.status_code = 200

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        crawler_service = CrawlerService()
        crawl_result = await crawler_service.crawl_google_flights(
            BASE_URL
        )

        assert crawl_result.success is True

        parser = FlightParser()
        flights = parser.parse(crawl_result.html)

        assert len(flights) == 10
        for flight in flights:
            assert flight.price > 0
            assert flight.airline is not None
            assert flight.departure_time is not None
            assert flight.arrival_time is not None


@pytest.mark.asyncio
async def test_integration_crawl_success_parse_zero_flights(empty_google_flights_html):
    """Crawl success mais parsing échoue (aucun vol)."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.html = empty_google_flights_html
    mock_result.status_code = 200

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        crawler_service = CrawlerService()
        crawl_result = await crawler_service.crawl_google_flights(
            BASE_URL
        )

        assert crawl_result.success is True

        parser = FlightParser()
        with pytest.raises(ParsingError) as exc_info:
            parser.parse(crawl_result.html)

        assert "No flights found" in str(exc_info.value)
