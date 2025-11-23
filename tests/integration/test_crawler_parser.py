"""Tests intégration CrawlerService + FlightParser."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import ParsingError
from app.services.crawler_service import CrawlerService
from app.services.flight_parser import FlightParser


@pytest.fixture
def valid_google_flights_html():
    """HTML Google Flights avec 10 vols valides."""
    flights_html = ""
    for i in range(10):
        price = 100 + i * 50
        airline = f"Airline {i}"
        flights_html += f"""
        <li class="pIav2d">
            <div aria-label="À partir de {price} euros. Départ de Paris à 10:{i:02d}, arrivée à Tokyo à 14:{i:02d}. Durée totale : 4 h 00 min. Vol direct avec {airline}."></div>
        </li>
        """
    return f"<html><body><ul>{flights_html}</ul></body></html>"


@pytest.fixture
def empty_google_flights_html():
    """HTML Google Flights sans vols."""
    return "<html><body><div class='no-results'>Aucun vol trouvé</div></body></html>"


@pytest.mark.asyncio
async def test_integration_crawl_and_parse_success(valid_google_flights_html):
    """Crawl URL → Parse HTML → 10 Flight validés."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.html = valid_google_flights_html
    mock_result.status_code = 200

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        crawler_service = CrawlerService()
        crawl_result = await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights?test=1"
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
            "https://www.google.com/travel/flights?test=1"
        )

        assert crawl_result.success is True

        parser = FlightParser()
        with pytest.raises(ParsingError) as exc_info:
            parser.parse(crawl_result.html)

        assert "No flights found" in str(exc_info.value)
