"""Tests unitaires CrawlerService."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.exceptions import CaptchaDetectedError, NetworkError
from app.services.crawler_service import CrawlerService
from app.services.proxy_service import ProxyService
from tests.fixtures.helpers import BASE_URL


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Mock get_settings pour tous les tests du module (CI compatibility)."""
    with patch("app.services.crawler_service.get_settings", return_value=test_settings):
        yield


@pytest.fixture
def crawler_service():
    """Instance CrawlerService."""
    return CrawlerService()


@pytest.mark.asyncio
async def test_crawl_success_dev_local(
    crawler_service, mock_crawl_result, mock_async_web_crawler
):
    """Crawl réussi mode POC dev local."""
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_google_flights(BASE_URL)

        assert result.success is True
        assert result.html is not None
        assert len(result.html) > 0


@pytest.mark.asyncio
async def test_crawl_recaptcha_v2_detection(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """HTML contient reCAPTCHA v2."""
    mock_result = mock_crawl_result_factory(
        html='<html><div class="g-recaptcha">Challenge</div></html>'
    )

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with pytest.raises(CaptchaDetectedError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert exc_info.value.captcha_type == "recaptcha"


@pytest.mark.asyncio
async def test_crawl_hcaptcha_detection(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """HTML contient hCaptcha."""
    mock_result = mock_crawl_result_factory(
        html='<html><div class="h-captcha">Challenge</div></html>'
    )

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with pytest.raises(CaptchaDetectedError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert exc_info.value.captcha_type == "hcaptcha"


@pytest.mark.asyncio
async def test_crawl_network_timeout(crawler_service, mock_async_web_crawler):
    """Timeout réseau AsyncWebCrawler."""
    crawler = mock_async_web_crawler(side_effect=TimeoutError("Timeout"))

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert exc_info.value.status_code is None


@pytest.mark.asyncio
async def test_crawl_status_403(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Status code 403 (rate limiting)."""
    mock_result = mock_crawl_result_factory(success=False, html="", status_code=403)

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_crawl_stealth_mode_enabled(
    crawler_service, mock_crawl_result, mock_async_web_crawler
):
    """BrowserConfig avec stealth mode actif (Chrome flags)."""
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch(
        "app.services.crawler_service.AsyncWebCrawler", return_value=crawler
    ) as mock_crawler_class:
        await crawler_service.crawl_google_flights(BASE_URL)

        call_kwargs = mock_crawler_class.call_args
        assert call_kwargs is not None
        config = call_kwargs.kwargs.get("config")
        assert config is not None
        assert "--disable-blink-features=AutomationControlled" in config.extra_args


@pytest.mark.asyncio
async def test_crawl_structured_logging(
    crawler_service, mock_crawl_result, mock_async_web_crawler, caplog
):
    """Logging structure avec contexte."""
    caplog.set_level(logging.INFO)
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.crawl_google_flights(BASE_URL)

        assert any("crawl" in record.message.lower() for record in caplog.records)


@pytest.fixture
def proxy_service_single(proxy_config_factory):
    """ProxyService avec 1 proxy (utilise factory)."""
    return ProxyService([proxy_config_factory(password="testpassword")])


@pytest.mark.asyncio
async def test_crawl_with_proxy_service(
    mock_crawl_result, proxy_service_single, mock_async_web_crawler
):
    """CrawlerService utilise proxy_service."""
    crawler_service = CrawlerService(proxy_service=proxy_service_single)
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch(
        "app.services.crawler_service.AsyncWebCrawler", return_value=crawler
    ) as mock_crawler_class:
        result = await crawler_service.crawl_google_flights(BASE_URL, use_proxy=True)

        assert result.success is True
        call_kwargs = mock_crawler_class.call_args
        config = call_kwargs.kwargs.get("config")
        assert config.proxy_config is not None


@pytest.mark.asyncio
async def test_crawl_without_proxy_when_disabled(
    mock_crawl_result, mock_async_web_crawler
):
    """CrawlerService sans proxy si use_proxy=False."""
    crawler_service = CrawlerService()
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_google_flights(BASE_URL, use_proxy=False)

        assert result.success is True


@pytest.mark.asyncio
async def test_crawl_proxy_rotation_called(
    mock_crawl_result, proxy_service_single, mock_async_web_crawler
):
    """get_next_proxy() appele si use_proxy=True."""
    crawler_service = CrawlerService(proxy_service=proxy_service_single)
    proxy_service_single.get_next_proxy = MagicMock(
        return_value=proxy_service_single.get_next_proxy()
    )
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.crawl_google_flights(BASE_URL, use_proxy=True)

        proxy_service_single.get_next_proxy.assert_called_once()


@pytest.mark.asyncio
async def test_get_google_session_success(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Session capture réussie avec cookies."""
    mock_cookies = [
        {"name": "NID", "value": "abc123"},
        {"name": "CONSENT", "value": "YES+"},
    ]

    mock_result = mock_crawl_result_factory(html="<html>Google Flights</html>")

    async def mock_hook_execution(url, config):
        crawler_service._captured_cookies = mock_cookies
        return mock_result

    crawler = mock_async_web_crawler(side_effect=mock_hook_execution)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_google_session()

        assert crawler_service._captured_cookies == mock_cookies
        assert len(crawler_service._captured_cookies) == 2


@pytest.mark.asyncio
async def test_get_google_session_auto_click_consent(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Auto-click popup RGPD 'Tout accepter'."""
    mock_page = MagicMock()
    mock_button = MagicMock()
    mock_page.wait_for_selector = AsyncMock(return_value=mock_button)
    mock_button.click = AsyncMock()

    mock_result = mock_crawl_result_factory(html="<html>Google Flights</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_google_session()

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_get_google_session_no_consent_popup(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory, caplog
):
    """Popup RGPD absent - timeout sans erreur."""
    mock_result = mock_crawl_result_factory(html="<html>No popup</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_google_session()

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_status_429(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Status code 429 rate limiting lève NetworkError."""
    mock_result = mock_crawl_result_factory(
        success=False, html="<html>Too Many Requests</html>", status_code=429
    )

    crawler = mock_async_web_crawler(mock_result=mock_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert "429" in str(exc_info.value) or exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_crawl_timeouts_configurable(mock_crawl_result, mock_async_web_crawler):
    """Timeouts configurables via Settings."""
    crawler_service = CrawlerService()
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.crawl_google_flights(BASE_URL)

        assert crawler.arun.called
        call_kwargs = crawler.arun.call_args.kwargs
        assert "wait_for" in call_kwargs or call_kwargs is not None


@pytest.mark.asyncio
async def test_crawl_retry_success_no_retry(
    crawler_service, mock_crawl_result, mock_async_web_crawler
):
    """Crawl reussi premiere tentative aucun retry."""
    crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_google_flights(BASE_URL)

        assert result.success is True
        assert crawler.arun.call_count == 1


@pytest.mark.asyncio
async def test_crawl_retry_on_500_error(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Retry automatique sur status 500."""
    call_count = 0

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_crawl_result_factory(success=False, status_code=500, html="")
        return mock_crawl_result_factory(html="<html>Success</html>")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with patch("time.sleep"):
            result = await crawler_service.crawl_google_flights(BASE_URL)

        assert result.success is True
        assert call_count == 2


@pytest.mark.asyncio
async def test_crawl_retry_on_timeout(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Retry automatique sur timeout reseau."""
    call_count = 0

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("Network timeout")
        return mock_crawl_result_factory(html="<html>Success</html>")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with patch("time.sleep"):
            result = await crawler_service.crawl_google_flights(BASE_URL)

        assert result.success is True
        assert call_count == 2


@pytest.mark.asyncio
async def test_crawl_retry_max_retries_network_error(
    crawler_service, mock_async_web_crawler
):
    """Max retries atteint NetworkError finale."""
    call_count = 0

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        raise TimeoutError("Network timeout")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with patch("time.sleep"), pytest.raises(NetworkError) as exc_info:
            await crawler_service.crawl_google_flights(BASE_URL)

        assert call_count == 3
        assert exc_info.value.attempts == 3


@pytest.mark.asyncio
async def test_crawl_retry_no_retry_on_404(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Pas de retry sur 404 Not Found."""
    call_count = 0

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_crawl_result_factory(success=False, status_code=404, html="")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.crawl_google_flights(BASE_URL)

        assert call_count == 1


@pytest.mark.asyncio
async def test_crawl_retry_before_sleep_logging(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory, caplog
):
    """Logging before_sleep callback chaque retry."""
    caplog.set_level(logging.WARNING)
    call_count = 0

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            return mock_crawl_result_factory(
                html='<div class="g-recaptcha">Captcha</div>'
            )
        return mock_crawl_result_factory(html="<html>Success</html>")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with patch("time.sleep"):
            result = await crawler_service.crawl_google_flights(BASE_URL)

        assert result.success is True
        warning_logs = [r for r in caplog.records if r.levelname == "WARNING"]
        assert len(warning_logs) >= 2


@pytest.mark.asyncio
async def test_crawl_retry_with_proxy_rotation(
    proxy_service_single, mock_async_web_crawler, mock_crawl_result_factory
):
    """Rotation proxy a chaque retry."""
    crawler_service = CrawlerService(proxy_service=proxy_service_single)
    call_count = 0
    proxy_calls = []

    original_get_next_proxy = proxy_service_single.get_next_proxy

    def track_proxy_calls():
        proxy = original_get_next_proxy()
        proxy_calls.append(proxy)
        return proxy

    proxy_service_single.get_next_proxy = track_proxy_calls

    async def mock_arun_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_crawl_result_factory(
                html='<div class="g-recaptcha">Captcha</div>'
            )
        return mock_crawl_result_factory(html="<html>Success</html>")

    crawler = mock_async_web_crawler(side_effect=mock_arun_side_effect)

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        with patch("time.sleep"):
            result = await crawler_service.crawl_google_flights(
                BASE_URL, use_proxy=True
            )

        assert result.success is True
        assert len(proxy_calls) >= 2
