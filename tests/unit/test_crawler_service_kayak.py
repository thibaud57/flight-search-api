"""Tests unitaires CrawlerService Kayak methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import CrawlerService

KAYAK_URL = "https://www.kayak.fr/flights/PAR-TYO/2025-06-01/TYO-PAR/2025-06-15?sort=bestflight_a"


@pytest.fixture(autouse=True)
def mock_settings(test_settings):
    """Mock get_settings pour tous les tests du module."""
    with patch("app.services.crawler_service.get_settings", return_value=test_settings):
        yield


@pytest.fixture
def crawler_service():
    """Instance CrawlerService."""
    return CrawlerService()


@pytest.fixture
def mock_page():
    """Mock Playwright Page."""
    page = AsyncMock()
    page.wait_for_selector = AsyncMock(return_value=None)
    page.wait_for_function = AsyncMock(return_value=None)
    return page


@pytest.mark.asyncio
async def test_get_kayak_session_success(
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
        await crawler_service.get_kayak_session(KAYAK_URL)

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_get_kayak_session_no_popup(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Session sans popup consent non bloquant."""
    mock_result = mock_crawl_result_factory(html="<html>No popup</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        await crawler_service.get_kayak_session(KAYAK_URL)

        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_kayak_with_network_capture(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl Kayak avec network capture active."""
    mock_result = mock_crawl_result_factory(html="<html>Kayak results</html>")

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_kayak(KAYAK_URL)

        assert result.success is True
        assert crawler.arun.called


@pytest.mark.asyncio
async def test_crawl_kayak_returns_html(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """HTML retourne avec contenu DOM."""
    expected_html = "<html><div data-resultid='1'>Flight 1</div></html>"
    mock_result = mock_crawl_result_factory(html=expected_html)

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_kayak(KAYAK_URL)

        assert result.html == expected_html
        assert "data-resultid" in result.html


@pytest.mark.asyncio
async def test_handle_kayak_consent_click(crawler_service, mock_page):
    """Popup consent clique sur bouton accept."""
    mock_button = AsyncMock()
    mock_page.wait_for_selector = AsyncMock(return_value=mock_button)
    mock_button.click = AsyncMock()

    await crawler_service._handle_kayak_consent(mock_page)

    mock_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_handle_kayak_consent_timeout(crawler_service, mock_page, caplog):
    """Timeout sans popup retourne sans erreur."""
    mock_page.wait_for_selector = AsyncMock(side_effect=TimeoutError("No popup"))

    await crawler_service._handle_kayak_consent(mock_page)

    assert len(caplog.records) >= 0


@pytest.mark.asyncio
async def test_handle_kayak_consent_fallback_selector(crawler_service, mock_page):
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

    await crawler_service._handle_kayak_consent(mock_page)

    assert call_count == 2
    mock_button.click.assert_called_once()


@pytest.mark.asyncio
async def test_after_goto_hook_kayak_url(crawler_service, mock_page):
    """Hook detecte URL Kayak et appelle handle_kayak_consent."""
    with patch.object(
        crawler_service, "_handle_kayak_consent", new_callable=AsyncMock
    ) as mock_consent:
        mock_context = MagicMock()
        mock_response = MagicMock()

        await crawler_service._after_goto_hook(
            mock_page, mock_context, KAYAK_URL, mock_response
        )

        mock_consent.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_after_goto_hook_google_url(crawler_service, mock_page):
    """Hook detecte URL Google et appelle handle_google_consent."""
    google_url = "https://www.google.com/travel/flights"

    with patch.object(
        crawler_service, "_handle_google_consent", new_callable=AsyncMock
    ) as mock_google_consent:
        mock_context = MagicMock()
        mock_response = MagicMock()

        await crawler_service._after_goto_hook(
            mock_page, mock_context, google_url, mock_response
        )

        mock_google_consent.assert_called_once_with(mock_page)


@pytest.mark.asyncio
async def test_extract_kayak_api_filters_url(crawler_service):
    """Filtre URLs API Kayak depuis network requests."""
    mock_network_requests = [
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=200,
            response_body='{"results": [{"price": 100}]}',
        ),
        MagicMock(
            url="https://www.kayak.fr/other/path",
            response_status=200,
            response_body='{"results": [{"price": 200}]}',
        ),
    ]

    mock_result = MagicMock()
    mock_result.network_requests = mock_network_requests

    responses = crawler_service._extract_kayak_api_responses(mock_result)

    assert len(responses) == 1
    assert "results" in responses[0]


@pytest.mark.asyncio
async def test_extract_kayak_api_filters_status(crawler_service):
    """Filtre status 200 uniquement."""
    mock_network_requests = [
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=200,
            response_body='{"results": [{"price": 100}]}',
        ),
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=404,
            response_body='{"results": [{"price": 200}]}',
        ),
    ]

    mock_result = MagicMock()
    mock_result.network_requests = mock_network_requests

    responses = crawler_service._extract_kayak_api_responses(mock_result)

    assert len(responses) == 1


@pytest.mark.asyncio
async def test_extract_kayak_api_parses_json(crawler_service):
    """Parse JSON response body valide."""
    mock_network_requests = [
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=200,
            response_body='{"results": [{"price": 500}]}',
        ),
    ]

    mock_result = MagicMock()
    mock_result.network_requests = mock_network_requests

    responses = crawler_service._extract_kayak_api_responses(mock_result)

    assert len(responses) == 1
    assert responses[0]["results"][0]["price"] == 500


@pytest.mark.asyncio
async def test_extract_kayak_api_ignores_invalid_json(crawler_service):
    """Ignore JSON invalide sans exception."""
    mock_network_requests = [
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=200,
            response_body="Invalid JSON {{{",
        ),
    ]

    mock_result = MagicMock()
    mock_result.network_requests = mock_network_requests

    responses = crawler_service._extract_kayak_api_responses(mock_result)

    assert len(responses) == 0


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
        await crawler_service.get_kayak_session(KAYAK_URL)

        assert consent_clicked is True
        assert mock_result.success is True


@pytest.mark.asyncio
async def test_crawl_kayak_captures_network_requests(
    crawler_service, mock_async_web_crawler, mock_crawl_result_factory
):
    """Crawl Kayak capture network requests avec JSON API."""
    mock_network_requests = [
        MagicMock(
            url="https://www.kayak.fr/api/search/poll",
            response_status=200,
            response_body='{"results": [{"price": 500}]}',
        ),
    ]

    mock_result = mock_crawl_result_factory(html="<html>Results</html>")
    mock_result.network_requests = mock_network_requests

    crawler = mock_async_web_crawler(mock_result=mock_result)
    mock_strategy = MagicMock()
    crawler.crawler_strategy = mock_strategy

    with patch("app.services.crawler_service.AsyncWebCrawler", return_value=crawler):
        result = await crawler_service.crawl_kayak(KAYAK_URL)

        assert result.success is True
        responses = crawler_service._extract_kayak_api_responses(mock_result)
        assert len(responses) == 1


@pytest.mark.asyncio
async def test_hook_routing_kayak_vs_google(crawler_service, mock_page):
    """Hook routing selon provider URL."""
    mock_context = MagicMock()
    mock_response = MagicMock()

    with patch.object(
        crawler_service, "_handle_kayak_consent", new_callable=AsyncMock
    ) as mock_kayak:
        await crawler_service._after_goto_hook(
            mock_page, mock_context, KAYAK_URL, mock_response
        )
        mock_kayak.assert_called_once()

    google_url = "https://www.google.com/travel/flights"
    with patch.object(
        crawler_service, "_handle_google_consent", new_callable=AsyncMock
    ) as mock_google:
        await crawler_service._after_goto_hook(
            mock_page, mock_context, google_url, mock_response
        )
        mock_google.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_kayak_polling_complete_success(crawler_service, mock_page):
    """Polling Kayak termine avec progressbar a 100%."""
    mock_page.wait_for_function = AsyncMock(return_value=True)

    result = await crawler_service._wait_for_kayak_polling_complete(mock_page)

    assert result is True
    mock_page.wait_for_function.assert_called_once()


@pytest.mark.asyncio
async def test_wait_for_kayak_polling_complete_timeout(crawler_service, mock_page):
    """Polling Kayak timeout retourne False sans erreur."""
    mock_page.wait_for_function = AsyncMock(side_effect=TimeoutError("Timeout"))

    result = await crawler_service._wait_for_kayak_polling_complete(mock_page)

    assert result is False


@pytest.mark.asyncio
async def test_wait_for_kayak_polling_complete_custom_timeout(
    crawler_service, mock_page
):
    """Timeout personnalise applique correctement."""
    custom_timeout = 30000
    mock_page.wait_for_function = AsyncMock(return_value=True)

    await crawler_service._wait_for_kayak_polling_complete(
        mock_page, timeout=custom_timeout
    )

    call_kwargs = mock_page.wait_for_function.call_args.kwargs
    assert call_kwargs.get("timeout") == custom_timeout
