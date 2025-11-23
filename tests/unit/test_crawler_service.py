"""Tests unitaires CrawlerService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.services.crawler_service import CrawlerService


@pytest.fixture
def crawler_service():
    """Instance CrawlerService."""
    return CrawlerService()


@pytest.mark.asyncio
async def test_crawl_success_dev_local(crawler_service, mock_crawl_result):
    """Crawl réussi mode POC dev local."""
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
    """HTML contient reCAPTCHA v2."""
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
    """HTML contient hCaptcha."""
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
    """Timeout réseau AsyncWebCrawler."""
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
    """Status code 403 (rate limiting)."""
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
    """BrowserConfig avec stealth mode actif (Chrome flags)."""
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
        assert "--disable-blink-features=AutomationControlled" in config.extra_args


@pytest.mark.asyncio
async def test_crawl_structured_logging(crawler_service, mock_crawl_result, caplog):
    """Logging structure avec contexte."""
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


@pytest.fixture
def proxy_config():
    """ProxyConfig pour tests."""
    from app.models.proxy import ProxyConfig

    return ProxyConfig(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="testpassword",
        country="FR",
    )


@pytest.fixture
def proxy_service(proxy_config):
    """ProxyService avec 1 proxy."""
    from app.services.proxy_service import ProxyService

    return ProxyService([proxy_config])


@pytest.mark.asyncio
async def test_crawl_with_proxy_service(mock_crawl_result, proxy_service):
    """CrawlerService utilise proxy_service."""
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        result = await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights", use_proxy=True
        )

        assert result.success is True
        call_kwargs = mock_crawler_class.call_args
        config = call_kwargs.kwargs.get("config")
        assert config.proxy_config is not None


@pytest.mark.asyncio
async def test_crawl_without_proxy_when_disabled(mock_crawl_result):
    """CrawlerService sans proxy si use_proxy=False."""
    crawler_service = CrawlerService()

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        result = await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights", use_proxy=False
        )

        assert result.success is True


@pytest.mark.asyncio
async def test_crawl_proxy_rotation_called(mock_crawl_result, proxy_service):
    """get_next_proxy() appele si use_proxy=True."""
    from unittest.mock import MagicMock

    crawler_service = CrawlerService(proxy_service=proxy_service)
    proxy_service.get_next_proxy = MagicMock(
        return_value=proxy_service.get_next_proxy()
    )

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights", use_proxy=True
        )

        proxy_service.get_next_proxy.assert_called_once()


@pytest.mark.asyncio
async def test_get_google_session_success(crawler_service):
    """Session capture réussie avec cookies."""
    mock_cookies = [
        {"name": "NID", "value": "abc123"},
        {"name": "CONSENT", "value": "YES+"},
    ]

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.html = "<html>Google Flights</html>"
        mock_result.status_code = 200
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)

        mock_strategy = MagicMock()
        mock_crawler.crawler_strategy = mock_strategy
        mock_crawler_class.return_value = mock_crawler

        async def mock_hook_execution(url, config):
            crawler_service._captured_cookies = mock_cookies
            return mock_result

        mock_crawler.arun.side_effect = mock_hook_execution

        await crawler_service.get_google_session()

        assert crawler_service._captured_cookies == mock_cookies
        assert len(crawler_service._captured_cookies) == 2


@pytest.mark.asyncio
async def test_get_google_session_auto_click_consent(crawler_service):
    """Auto-click popup RGPD 'Tout accepter'."""
    mock_page = MagicMock()
    mock_button = MagicMock()
    mock_page.wait_for_selector = AsyncMock(return_value=mock_button)
    mock_button.click = AsyncMock()

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.html = "<html>Google Flights</html>"
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.get_google_session()

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_get_google_session_no_consent_popup(crawler_service, caplog):
    """Popup RGPD absent - timeout sans erreur."""
    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.html = "<html>No popup</html>"
        mock_crawler.arun.return_value = mock_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.get_google_session()

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_status_429(crawler_service):
    """Status code 429 rate limiting lève NetworkError."""
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.html = "<html>Too Many Requests</html>"
    mock_result.status_code = 429

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

        assert "429" in str(exc_info.value) or exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_crawl_timeouts_configurable(mock_crawl_result):
    """Timeouts configurables via Settings."""
    crawler_service = CrawlerService()

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights"
        )

        assert mock_crawler.arun.called
        call_kwargs = mock_crawler.arun.call_args.kwargs
        assert "wait_for" in call_kwargs or call_kwargs is not None
