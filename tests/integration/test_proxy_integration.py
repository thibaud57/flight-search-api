"""Tests integration pour proxy rotation."""

import logging
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import ProxyConfig
from app.services import CrawlerService, ProxyService
from tests.fixtures.helpers import BASE_URL


@dataclass
class ProxyTestContext:
    """Contexte partagé pour tests proxy integration."""

    proxy_service: ProxyService
    crawler_service: CrawlerService
    mock_crawler: AsyncMock
    mock_crawler_class: MagicMock


@pytest.fixture
def proxy_test_setup(
    mock_proxy_pool: list[ProxyConfig],
    mock_crawl_result: MagicMock,
    mock_async_web_crawler,
):
    """Setup commun : ProxyService + CrawlerService + mock AsyncWebCrawler."""
    proxy_service = ProxyService(mock_proxy_pool)
    crawler_service = CrawlerService(proxy_service=proxy_service)
    mock_crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value = mock_crawler
        yield ProxyTestContext(
            proxy_service=proxy_service,
            crawler_service=crawler_service,
            mock_crawler=mock_crawler,
            mock_crawler_class=mock_crawler_class,
        )


@pytest.mark.asyncio
async def test_integration_crawler_with_proxy_rotation(proxy_test_setup) -> None:
    """CrawlerService exécute 3 crawls successifs avec ProxyService."""
    ctx = proxy_test_setup

    for _ in range(3):
        await ctx.crawler_service.crawl_google_flights(BASE_URL, use_proxy=True)

    assert ctx.mock_crawler.arun.call_count == 3


def test_integration_settings_load_from_env(settings_env_factory) -> None:
    """Settings charge depuis env avec proxy_config valide."""
    settings = settings_env_factory(DECODO_PROXY_HOST="fr.decodo.com:40000")

    assert settings.proxy_config is not None
    assert settings.proxy_config.host == "fr.decodo.com"
    assert settings.proxy_config.port == 40000


@pytest.mark.asyncio
async def test_integration_proxy_service_injected_crawler(proxy_test_setup) -> None:
    """get_next_proxy() retourne proxies différents (rotation round-robin)."""
    ctx = proxy_test_setup

    first_proxy = ctx.proxy_service.get_next_proxy()
    await ctx.crawler_service.crawl_google_flights(BASE_URL, use_proxy=True)
    second_proxy = ctx.proxy_service.get_next_proxy()

    assert first_proxy.username != second_proxy.username


@pytest.mark.asyncio
async def test_integration_proxy_rotation_logging_observability(
    proxy_test_setup,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Logs ne contiennent pas 'password' (sécurité)."""
    ctx = proxy_test_setup

    with caplog.at_level(logging.INFO):
        for _ in range(3):
            await ctx.crawler_service.crawl_google_flights(BASE_URL, use_proxy=True)

    log_text = " ".join(record.message for record in caplog.records)
    assert "password" not in log_text.lower()


@pytest.mark.asyncio
async def test_integration_proxy_service_disabled_no_injection(
    mock_crawl_result: MagicMock,
    mock_async_web_crawler,
) -> None:
    """CrawlerService sans proxy si proxy_service=None."""
    crawler_service = CrawlerService(proxy_service=None)
    mock_crawler = mock_async_web_crawler(mock_result=mock_crawl_result)

    with patch("app.services.crawler_service.AsyncWebCrawler") as mock_crawler_class:
        mock_crawler_class.return_value = mock_crawler

        result = await crawler_service.crawl_google_flights(
            BASE_URL,
            use_proxy=True,
        )

        assert result.success is True
        call_kwargs = mock_crawler_class.call_args
        config = call_kwargs.kwargs.get("config")
        assert config.proxy_config is None
