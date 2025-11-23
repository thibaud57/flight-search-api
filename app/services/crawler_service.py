"""Service de crawling Google Flights avec stealth mode et proxy rotation."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig

from app.core.config import get_settings
from app.exceptions import CaptchaDetectedError, NetworkError
from app.models.proxy import ProxyConfig
from app.utils import (
    build_browser_config_from_fingerprint,
    get_base_browser_config,
    get_static_headers,
)

if TYPE_CHECKING:
    from app.services.proxy_service import ProxyService

logger = logging.getLogger(__name__)

GOOGLE_FLIGHTS_SESSION_ID = "google_flights_session"
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

    def __init__(self, proxy_service: ProxyService | None = None) -> None:
        """Initialise service avec ProxyService optionnel."""
        self._proxy_service = proxy_service
        self._settings = get_settings()
        self._captured_cookies: list[dict[str, Any]] = []

    async def get_google_session(
        self,
        url: str = "https://www.google.com/travel/flights",
        *,
        use_proxy: bool = True,
    ) -> None:
        """Capture session Google (headers + cookies) via Crawl4AI avec persistence."""
        start_time = time.time()
        proxy_config, proxy = self._get_proxy_config(use_proxy)
        self._captured_cookies = []

        logger.info(
            "Starting session capture with Crawl4AI",
            extra={
                "url": url,
                "proxy_host": proxy.host if proxy else "no_proxy",
                "proxy_country": proxy.country if proxy else "N/A",
            },
        )

        browser_config = get_base_browser_config(proxy_config=proxy_config)

        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                crawler.crawler_strategy.set_hook("after_goto", self._after_goto_hook)
                crawler.crawler_strategy.set_hook(
                    "before_return_html", self._extract_cookies_hook
                )
                run_config = self._build_crawler_run_config(
                    wait_for_selector="css:body"
                )
                result = await asyncio.wait_for(
                    crawler.arun(url=url, config=run_config),
                    timeout=self._settings.crawler.crawl_global_timeout_s,
                )
        except TimeoutError as err:
            logger.error(
                "Session capture timeout",
                extra={
                    "url": url,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=None) from err
        except Exception:
            raise

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (403, 429):
            logger.error(
                "Session capture failed",
                extra={
                    "url": url,
                    "status_code": result.status_code,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=result.status_code)

        logger.info(
            "Session captured with Crawl4AI",
            extra={
                "success": result.success,
                "status_code": result.status_code,
                "response_time_ms": response_time_ms,
                "proxy_host": proxy.host if proxy else "no_proxy",
                "cookies_captured": len(self._captured_cookies),
            },
        )

    async def crawl_google_flights(
        self,
        url: str,
        *,
        use_proxy: bool = True,
    ) -> CrawlResult:
        """Crawl une URL Google Flights avec proxy rotation."""
        start_time = time.time()
        proxy_config, proxy = self._get_proxy_config(use_proxy)

        logger.info(
            "Starting crawl",
            extra={
                "url": url,
                "proxy_host": proxy.host if proxy else "no_proxy",
                "proxy_country": proxy.country if proxy else "N/A",
            },
        )

        config = build_browser_config_from_fingerprint(
            url,
            get_static_headers(),
            self._captured_cookies,
            proxy_config,
        )

        try:
            async with AsyncWebCrawler(config=config) as crawler:
                run_config = self._build_crawler_run_config(
                    wait_for_selector="css:.pIav2d",
                )

                result = await asyncio.wait_for(
                    crawler.arun(
                        url=url,
                        config=run_config,
                    ),
                    timeout=self._settings.crawler.crawl_global_timeout_s,
                )
        except TimeoutError as err:
            logger.error(
                "Crawl timeout",
                extra={
                    "url": url,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=None) from err
        except Exception:
            raise

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (403, 429):
            logger.error(
                "Crawl failed",
                extra={
                    "url": url,
                    "status_code": result.status_code,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=result.status_code)

        html = result.html or ""
        self._detect_captcha(html, url)

        logger.info(
            "Crawl successful",
            extra={
                "status_code": result.status_code,
                "html_size": len(html),
                "response_time_ms": response_time_ms,
                "proxy_host": proxy.host if proxy else "no_proxy",
            },
        )

        return CrawlResult(
            success=True,
            html=html,
            status_code=result.status_code,
        )

    async def _after_goto_hook(
        self, page: Any, context: Any, url: str, response: Any, **kwargs: Any
    ) -> Any:
        """Hook combiné: Accept consent popup."""
        try:
            accept_button = await page.wait_for_selector(
                'button:has-text("Tout accepter"), button:has-text("Accept all")',
                timeout=1000,
            )
            if accept_button:
                await accept_button.click()
                await asyncio.sleep(1)
                logger.info("Auto-clicked consent Accept button")
        except Exception as e:
            logger.warning(f"Could not auto-click consent button: {e}")

        return page

    async def _extract_cookies_hook(
        self, page: Any, context: Any, html: str, **kwargs: Any
    ) -> None:
        """Hook: Récupère cookies après consentement Google."""
        cookies = await context.cookies()
        self._captured_cookies = cookies
        logger.info(
            "Cookies extracted via hook",
            extra={"cookies_count": len(cookies)},
        )

    def _get_proxy_config(
        self, use_proxy: bool
    ) -> tuple[dict[str, str] | None, ProxyConfig | None]:
        """Retourne config proxy."""
        if not use_proxy or self._proxy_service is None:
            return None, None

        proxy = self._proxy_service.get_next_proxy()
        proxy_config = {
            "server": f"http://{proxy.host}:{proxy.port}",
            "username": proxy.username,
            "password": proxy.password,
        }
        return proxy_config, proxy

    def _build_crawler_run_config(
        self,
        wait_for_selector: str,
    ) -> CrawlerRunConfig:
        """Construit CrawlerRunConfig avec paramètres communs."""
        return CrawlerRunConfig(
            cache_mode=CacheMode.DISABLED,
            magic=False,
            simulate_user=True,
            override_navigator=True,
            wait_for=wait_for_selector,
            page_timeout=self._settings.crawler.crawl_page_timeout_ms,
            delay_before_return_html=self._settings.crawler.crawl_delay_s,
        )

    def _detect_captcha(self, html: str, url: str) -> None:
        """Detecte la presence de captcha dans le HTML."""
        html_lower = html.lower()

        for captcha_type, patterns in CAPTCHA_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in html_lower:
                    logger.warning(
                        "Captcha detected",
                        extra={"url": url, "captcha_type": captcha_type},
                    )
                    raise CaptchaDetectedError(url=url, captcha_type=captcha_type)
