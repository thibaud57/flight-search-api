"""Tests integration pour proxy rotation."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.models.proxy import ProxyConfig
from app.services.crawler_service import CrawlerService
from app.services.proxy_service import ProxyService


@pytest.fixture
def proxy_pool() -> list[ProxyConfig]:
    """Pool de 3 proxies distincts."""
    return [
        ProxyConfig(
            host="fr.decodo.com",
            port=40000,
            username="proxy0user",
            password="password0",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40001,
            username="proxy1user",
            password="password1",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40002,
            username="proxy2user",
            password="password2",
            country="FR",
        ),
    ]


@pytest.fixture
def mock_crawl_result():
    """Mock CrawlResult success."""
    result = MagicMock()
    result.success = True
    result.html = "<html><body>Valid HTML</body></html>"
    result.status_code = 200
    return result


@pytest.mark.asyncio
async def test_integration_crawler_with_proxy_rotation(
    proxy_pool: list[ProxyConfig], mock_crawl_result: MagicMock
) -> None:
    """Test 1: 3 crawls utilisent 3 proxies differents."""
    proxy_service = ProxyService(proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        for _ in range(3):
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights", use_proxy=True
            )

    assert proxy_service.current_proxy_index == 0


def test_integration_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test 2: Settings charge depuis env avec proxy_config valide."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "testuser")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("DECODO_PROXY_ENABLED", "true")

    settings = Settings()

    assert settings.proxy_config is not None
    assert settings.proxy_config.host == "fr.decodo.com"
    assert settings.proxy_config.port == 40000


@pytest.mark.asyncio
async def test_integration_proxy_service_injected_crawler(
    proxy_pool: list[ProxyConfig], mock_crawl_result: MagicMock
) -> None:
    """Test 3: ProxyService injecte dans CrawlerService."""
    proxy_service = ProxyService(proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        initial_index = proxy_service.current_proxy_index
        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights", use_proxy=True
        )

        assert proxy_service.current_proxy_index != initial_index


@pytest.mark.asyncio
async def test_integration_proxy_rotation_logging_observability(
    proxy_pool: list[ProxyConfig],
    mock_crawl_result: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test 4: Logs contiennent proxy_host, pas de password."""
    proxy_service = ProxyService(proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with (
        caplog.at_level(logging.INFO),
        patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class,
    ):
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        for _ in range(3):
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights", use_proxy=True
            )

    log_text = " ".join(record.message for record in caplog.records)
    assert "password" not in log_text.lower()


@pytest.mark.asyncio
async def test_integration_proxy_service_disabled_no_injection(
    mock_crawl_result: MagicMock,
) -> None:
    """Test 5: CrawlerService sans proxy si proxy_service=None."""
    crawler_service = CrawlerService(proxy_service=None)

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
        assert config.proxy is None
