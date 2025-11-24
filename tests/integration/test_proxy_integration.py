"""Tests integration pour proxy rotation."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.models.proxy import ProxyConfig
from app.services.crawler_service import CrawlerService
from app.services.proxy_service import ProxyService


@pytest.mark.asyncio
async def test_integration_crawler_with_proxy_rotation(
    mock_proxy_pool: list[ProxyConfig],
    mock_crawl_result: MagicMock,
) -> None:
    """CrawlerService exécute 3 crawls successifs avec ProxyService."""
    proxy_service = ProxyService(mock_proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        for _ in range(3):
            await crawler_service.crawl_google_flights(
                "https://www.google.com/travel/flights",
                use_proxy=True,
            )

        assert mock_crawler.arun.call_count == 3


def test_integration_settings_load_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings charge depuis env avec proxy_config valide."""
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
    mock_proxy_pool: list[ProxyConfig],
    mock_crawl_result: MagicMock,
) -> None:
    """get_next_proxy() retourne proxies différents (rotation round-robin)."""
    proxy_service = ProxyService(mock_proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        first_proxy = proxy_service.get_next_proxy()
        await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights",
            use_proxy=True,
        )
        second_proxy = proxy_service.get_next_proxy()

        assert first_proxy.username != second_proxy.username


@pytest.mark.asyncio
async def test_integration_proxy_rotation_logging_observability(
    mock_proxy_pool: list[ProxyConfig],
    mock_crawl_result: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Logs ne contiennent pas 'password' (sécurité)."""
    proxy_service = ProxyService(mock_proxy_pool)
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
                "https://www.google.com/travel/flights",
                use_proxy=True,
            )

    log_text = " ".join(record.message for record in caplog.records)
    assert "password" not in log_text.lower()


@pytest.mark.asyncio
async def test_integration_proxy_service_disabled_no_injection(
    mock_crawl_result: MagicMock,
) -> None:
    """CrawlerService sans proxy si proxy_service=None."""
    crawler_service = CrawlerService(proxy_service=None)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler = AsyncMock()
        mock_crawler.arun.return_value = mock_crawl_result
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_class.return_value = mock_crawler

        result = await crawler_service.crawl_google_flights(
            "https://www.google.com/travel/flights",
            use_proxy=True,
        )

        assert result.success is True
        call_kwargs = mock_crawler_class.call_args
        config = call_kwargs.kwargs.get("config")
        assert config.proxy_config is None
