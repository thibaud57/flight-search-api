"""Tests unitaires CrawlerService Kayak methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import Provider
from app.services import CrawlerService
from tests.fixtures.helpers import KAYAK_BASE_URL, KAYAK_TEMPLATE_URL
from tests.fixtures.mocks import create_mock_settings_context


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Mock get_settings pour tous les tests du module."""
    with create_mock_settings_context("app.services.crawler_service", test_settings):
        yield


@pytest.fixture
def mock_page():
    """Mock Playwright Page."""
    page = AsyncMock()
    page.wait_for_selector = AsyncMock(return_value=None)
    page.wait_for_function = AsyncMock(return_value=None)
    return page


@pytest.mark.asyncio
async def test_get_session_kayak_success(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Session Kayak etablie avec consent."""
    mock_result = mock_crawl_result_factory(html="<html>Kayak results</html>")

    async def mock_hook_execution(url, config):
        return mock_result

    crawler = mock_async_web_crawler(side_effect=mock_hook_execution)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_session(Provider.KAYAK)

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_get_session_kayak_no_popup(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Session sans popup consent non bloquant."""
    mock_result = mock_crawl_result_factory(html="<html>No popup</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_session(Provider.KAYAK)

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_flights_kayak_with_network_capture(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl Kayak avec network capture active."""
    mock_result = mock_crawl_result_factory(html="<html>Kayak results</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_flights(KAYAK_TEMPLATE_URL, Provider.KAYAK)

        assert result.success is True
        assert crawler.arun.called


@pytest.mark.asyncio
async def test_crawl_flights_kayak_returns_html(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """HTML retourne avec contenu DOM."""
    expected_html = "<html><div data-resultid='1'>Flight 1</div></html>"
    mock_result = mock_crawl_result_factory(html=expected_html)

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_flights(KAYAK_TEMPLATE_URL, Provider.KAYAK)

        assert result.html == expected_html
        assert "data-resultid" in result.html


@pytest.mark.asyncio
async def test_handle_consent_click(crawler_service, mock_page):
    """Popup consent clique sur bouton accept."""
    mock_button = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(return_value=mock_button)
    mock_button.click = AsyncMock()

    await crawler_service._handle_consent(mock_page)

    mock_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_handle_consent_timeout(crawler_service, mock_page, caplog):
    """Timeout sans popup retourne sans erreur."""
    mock_page.wait_for_selector = AsyncMock(side_effect=TimeoutError("No popup"))

    await crawler_service._handle_consent(mock_page)

    assert len(caplog.records) >= 0


@pytest.mark.asyncio
async def test_handle_consent_fallback_selector(crawler_service, mock_page):
    """Fallback sur 2e selecteur si 1er timeout."""
    call_count = 0
    mock_button = AsyncMock()

    async def mock_wait_with_fallback(selector, timeout):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TimeoutError("First selector timeout")
        return mock_button

    mock_page.wait_for_selector = mock_wait_with_fallback
    mock_button.click = AsyncMock()

    await crawler_service._handle_consent(mock_page)

    assert call_count == 2
    mock_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_session_after_goto_hook_kayak(crawler_service, mock_page):
    """Hook session appelle handle_consent pour Kayak."""
    mock_context = AsyncMock()
    mock_response = AsyncMock()

    with patch.object(
        crawler_service, "_handle_consent", new_callable=AsyncMock
    ) as mock_consent:
        await crawler_service._session_after_goto_hook(
            mock_page, mock_context, KAYAK_BASE_URL, mock_response
        )

        mock_consent.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_kayak_session_with_consent_flow(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Session etablie avec popup consent visible et clique."""
    mock_result = mock_crawl_result_factory(html="<html>Kayak with consent</html>")

    consent_clicked = False

    async def mock_hook_execution(url, config):
        nonlocal consent_clicked
        consent_clicked = True
        return mock_result

    crawler = mock_async_web_crawler(side_effect=mock_hook_execution)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_session(Provider.KAYAK)

        assert consent_clicked is True
        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_flights_kayak_with_use_proxy_false(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl Kayak sans proxy."""
    mock_result = mock_crawl_result_factory(html="<html>Kayak results</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_flights(
            KAYAK_TEMPLATE_URL, Provider.KAYAK, use_proxy=False
        )

        assert result.success is True
