"""Service de crawling Google Flights avec stealth mode et proxy rotation."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from crawl4ai import AsyncWebCrawler, BrowserConfig

from app.exceptions import CaptchaDetectedError, NetworkError

if TYPE_CHECKING:
    from app.services.proxy_service import ProxyService

CAPTCHA_PATTERNS = {
    "recaptcha": ["g-recaptcha", 'class="recaptcha"', "grecaptcha"],
    "hcaptcha": ["h-captcha", "hcaptcha"],
}


@dataclass
class CrawlResult:
    """Resultat d'un crawl."""

    success: bool
    html: str
    status_code: int | None = None


class CrawlerService:
    """Service de crawling Google Flights avec stealth mode et proxy rotation."""

    def __init__(
        self,
        proxy_service: ProxyService | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialise service avec ProxyService et Logger optionnels."""
        self._proxy_service = proxy_service
        self._logger = logger or logging.getLogger(__name__)

    async def crawl_google_flights(
        self, url: str, *, use_proxy: bool = True
    ) -> CrawlResult:
        """Crawl une URL Google Flights avec proxy rotation."""
        start_time = time.time()

        browser_proxy_config: dict[str, str] | None = None
        proxy_host = "no_proxy"
        proxy_country = "N/A"

        if use_proxy and self._proxy_service is not None:
            proxy = self._proxy_service.get_next_proxy()
            browser_proxy_config = {
                "server": f"http://{proxy.host}:{proxy.port}",
                "username": proxy.username,
                "password": proxy.password,
            }
            proxy_host = proxy.host
            proxy_country = proxy.country

        self._logger.info(
            "Starting crawl",
            extra={
                "url": url,
                "stealth_mode": True,
                "proxy_host": proxy_host,
                "proxy_country": proxy_country,
                "use_proxy": use_proxy and self._proxy_service is not None,
            },
        )

        config = BrowserConfig(
            headless=True, enable_stealth=True, proxy_config=browser_proxy_config
        )

        try:
            async with AsyncWebCrawler(config=config) as crawler:
                result = await asyncio.wait_for(
                    crawler.arun(url=url),
                    timeout=10.0,
                )
        except TimeoutError as err:
            self._logger.error("Crawl timeout", extra={"url": url, "proxy_host": proxy_host})
            raise NetworkError(url=url, status_code=None) from err

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (403, 429):
            self._logger.error(
                "Crawl failed",
                extra={
                    "url": url,
                    "status_code": result.status_code,
                    "proxy_host": proxy_host,
                },
            )
            raise NetworkError(url=url, status_code=result.status_code)

        html = result.html or ""
        self._detect_captcha(html, url)

        self._logger.info(
            "Crawl successful",
            extra={
                "url": url,
                "status_code": result.status_code,
                "html_size": len(html),
                "response_time_ms": response_time_ms,
                "stealth_mode": True,
                "proxy_host": proxy_host,
                "proxy_country": proxy_country,
            },
        )

        return CrawlResult(
            success=True,
            html=html,
            status_code=result.status_code,
        )

    def _detect_captcha(self, html: str, url: str) -> None:
        """Detecte la presence de captcha dans le HTML."""
        html_lower = html.lower()

        for captcha_type, patterns in CAPTCHA_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in html_lower:
                    self._logger.warning(
                        "Captcha detected",
                        extra={"url": url, "captcha_type": captcha_type},
                    )
                    raise CaptchaDetectedError(url=url, captcha_type=captcha_type)
