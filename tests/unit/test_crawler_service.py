"""Tests unitaires CrawlerService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.services.crawler_service import CrawlerService


@pytest.fixture
def mock_crawl_result():
    """Mock CrawlResult success."""
    result = MagicMock()
    result.success = True
    result.html = "<html><body>Valid Google Flights HTML</body></html>"
    result.status_code = 200
    return result


@pytest.fixture
def crawler_service():
    """Instance CrawlerService."""
    return CrawlerService()


@pytest.mark.asyncio
async def test_crawl_success_dev_local(crawler_service, mock_crawl_result):
    """Test 1: Crawl réussi mode POC dev local."""
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        result = await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights?test"
        )

        assert result.success is True
        assert result.html is not None
        assert len(result.html) > 0


@pytest.mark.asyncio
async def test_crawl_recaptcha_v2_detection(crawler_service):
    """Test 2: HTML contient reCAPTCHA v2."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.html = '<html><div class="g-recaptcha">Challenge</div></html>'
    mock_result.status_code = 200

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        with pytest.raises(CaptchaDetectedError) as exc_info:
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights"
            )

        assert exc_info.value.captcha_type == "recaptcha"


@pytest.mark.asyncio
async def test_crawl_hcaptcha_detection(crawler_service):
    """Test 3: HTML contient hCaptcha."""
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.html = '<html><div class="h-captcha">Challenge</div></html>'
    mock_result.status_code = 200

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        with pytest.raises(CaptchaDetectedError) as exc_info:
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights"
            )

        assert exc_info.value.captcha_type == "hcaptcha"


@pytest.mark.asyncio
async def test_crawl_network_timeout(crawler_service):
    """Test 4: Timeout réseau AsyncWebCrawler."""
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.side_effect = TimeoutError("Timeout")
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        with pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights"
            )

        assert exc_info.value.status_code is None


@pytest.mark.asyncio
async def test_crawl_status_403(crawler_service):
    """Test 5: Status code 403 (rate limiting)."""
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.html = ""
    mock_result.status_code = 403

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        with pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights"
            )

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_crawl_stealth_mode_enabled(crawler_service, mock_crawl_result):
    """Test 6: BrowserConfig avec stealth mode actif."""
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights"
        )

        call_kwargs = mock_crawler_class.call_args
        assert call_kwargs is not None
        config = call_kwargs.kwargs.get("config")
        assert config is not None
        assert config.enable_stealth is True


@pytest.mark.asyncio
async def test_crawl_structured_logging(crawler_service, mock_crawl_result, caplog):
    """Test 7: Logging structuré avec contexte."""
    import logging

    caplog.set_level(logging.INFO)
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights?test=1"
        )

        assert any("crawl" in record.message.lower() for record in caplog.records)
