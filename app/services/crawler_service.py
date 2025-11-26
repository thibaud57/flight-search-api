"""Service de crawling avec stealth mode et proxy rotation."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from playwright.async_api import BrowserContext, Cookie, Page, Response
from tenacity import retry

from app.core import get_settings
from app.exceptions import CaptchaDetectedError, NetworkError
from app.models import ProxyConfig
from app.services.retry_strategy import RetryStrategy
from app.utils import (
    build_browser_config_from_fingerprint,
    get_base_browser_config,
)

if TYPE_CHECKING:
    from app.services.proxy_service import ProxyService

logger = logging.getLogger(__name__)

SESSION_URLS = {
    "google": "https://www.google.com/travel/flights",
    "kayak": "https://www.kayak.fr/flights",
}
CAPTCHA_PATTERNS = {
    "recaptcha": ["g-recaptcha", 'class="recaptcha"', "grecaptcha"],
    "hcaptcha": ["h-captcha", "hcaptcha"],
}
CONSENT_SELECTORS = {
    "google": [
        'button:has-text("Tout accepter")',
        'button:has-text("Accept all")',
    ],
    "kayak": [
        'button:has-text("Tout accepter")',
        'button:has-text("Accept all")',
    ],
}


@dataclass
class CrawlResult:
    """Resultat d'un crawl."""

    success: bool
    html: str
    status_code: int | None = None


class CrawlerService:
    """Service de crawling avec stealth mode et proxy rotation."""

    def __init__(self, proxy_service: ProxyService | None = None) -> None:
        """Initialise service avec ProxyService optionnel."""
        self._proxy_service = proxy_service
        self._settings = get_settings()
        self._captured_cookies: list[Cookie] = []
        self.provider: str = "google"

    async def get_session(
        self,
        provider: str,
        *,
        use_proxy: bool = False,
    ) -> None:
        """Capture session (headers + cookies) via Crawl4AI."""
        self.provider = provider
        url = SESSION_URLS[provider]
        start_time = time.time()
        proxy_config, proxy = self._get_proxy_config(use_proxy)
        self._captured_cookies = []

        logger.info(
            "Starting session capture",
            extra={
                "provider": provider,
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
                    "css:body", provider=provider
                )
                result = await asyncio.wait_for(
                    crawler.arun(url=url, config=run_config),
                    timeout=self._settings.crawler.crawl_global_timeout_s,
                )
        except TimeoutError as err:
            logger.error(
                "Session capture timeout",
                extra={
                    "provider": provider,
                    "url": url,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=None) from err
        except RuntimeError as err:
            logger.error(
                "Session capture failed - Runtime error",
                extra={
                    "provider": provider,
                    "url": url,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                    "error": str(err),
                },
            )
            raise NetworkError(url=url, status_code=None) from err

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (403, 429):
            logger.error(
                "Session capture failed",
                extra={
                    "provider": provider,
                    "url": url,
                    "status_code": result.status_code,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=result.status_code)

        logger.info(
            "Session captured",
            extra={
                "provider": provider,
                "success": result.success,
                "status_code": result.status_code,
                "response_time_ms": response_time_ms,
                "proxy_host": proxy.host if proxy else "no_proxy",
                "cookies_captured": len(self._captured_cookies),
            },
        )

    async def crawl_flights(
        self,
        url: str,
        provider: str,
        *,
        use_proxy: bool = True,
    ) -> CrawlResult:
        """Crawl une URL de recherche vols avec proxy rotation et retry logic."""
        attempt_count = 0

        @retry(**RetryStrategy.get_crawler_retry())  # type: ignore[misc]
        async def _crawl_with_retry() -> CrawlResult:
            nonlocal attempt_count
            attempt_count += 1

            start_time = time.time()
            proxy_config, proxy = self._get_proxy_config(use_proxy)

            logger.info(
                "Starting crawl",
                extra={
                    "provider": provider,
                    "url": url,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                    "proxy_country": proxy.country if proxy else "N/A",
                    "attempt": attempt_count,
                },
            )

            config = build_browser_config_from_fingerprint(
                url,
                self._captured_cookies,
                proxy_config,
            )

            wait_for_selector = (
                "data-resultid" if provider == "kayak" else "css:.pIav2d"
            )
            run_config = self._build_crawler_run_config(
                wait_for_selector, provider=provider
            )

            try:
                async with AsyncWebCrawler(config=config) as crawler:
                    result = await asyncio.wait_for(
                        crawler.arun(url=url, config=run_config),
                        timeout=self._settings.crawler.crawl_global_timeout_s,
                    )
            except TimeoutError as err:
                logger.error(
                    "Crawl timeout",
                    extra={
                        "provider": provider,
                        "url": url,
                        "proxy_host": proxy.host if proxy else "no_proxy",
                    },
                )
                raise NetworkError(
                    url=url, status_code=None, attempts=attempt_count
                ) from err
            except RuntimeError as err:
                logger.error(
                    "Crawl failed - Runtime error",
                    extra={
                        "provider": provider,
                        "url": url,
                        "proxy_host": proxy.host if proxy else "no_proxy",
                        "error": str(err),
                    },
                )
                raise NetworkError(
                    url=url, status_code=None, attempts=attempt_count
                ) from err
            except CaptchaDetectedError:
                if use_proxy and self._proxy_service:
                    self._proxy_service.get_next_proxy()
                    logger.debug("Proxy rotation triggered after captcha")
                raise

            response_time_ms = int((time.time() - start_time) * 1000)

            if not result.success and result.status_code == 404:
                return CrawlResult(success=False, html="", status_code=404)

            if not result.success or result.status_code in (
                500,
                502,
                503,
                504,
                429,
                403,
            ):
                error_msg = "Crawl failed"
                if (
                    result.status_code in (429, 403)
                    and use_proxy
                    and self._proxy_service
                ):
                    self._proxy_service.get_next_proxy()
                    error_msg = "Rate limit/forbidden - proxy rotated"
                logger.error(
                    error_msg,
                    extra={
                        "provider": provider,
                        "url": url,
                        "status_code": result.status_code,
                        "proxy_host": proxy.host if proxy else "no_proxy",
                    },
                )
                raise NetworkError(
                    url=url, status_code=result.status_code, attempts=attempt_count
                )

            html = result.html or ""
            self._detect_captcha(html, url)

            logger.info(
                "Crawl successful",
                extra={
                    "provider": provider,
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

        result: CrawlResult = await _crawl_with_retry()
        return result

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
            "password": proxy.password.get_secret_value(),
        }
        return proxy_config, proxy

    def _build_crawler_run_config(
        self,
        wait_for_selector: str,
        *,
        provider: str = "google",
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
            capture_network_requests=(provider == "kayak"),
        )

    async def _after_goto_hook(
        self,
        page: Page,
        context: BrowserContext,
        url: str,
        response: Response,
        **kwargs: object,
    ) -> Page:
        """Hook apres navigation - gere consent selon provider."""
        await self._handle_consent(page)
        return page

    async def _handle_consent(self, page: Page) -> None:
        """Detecte et ferme popup consent si present."""
        selectors = CONSENT_SELECTORS.get(self.provider, [])

        for selector in selectors:
            try:
                accept_button = await page.wait_for_selector(selector, timeout=1000)
                if accept_button:
                    await accept_button.click()
                    await asyncio.sleep(1)
                    logger.info(
                        "Auto-clicked consent button",
                        extra={
                            "provider": self.provider,
                            "selector": selector,
                        },
                    )
                    return
            except TimeoutError:
                continue
            except Exception as e:
                logger.warning("Could not click consent selector %s: %s", selector, e)
                continue

    async def _extract_cookies_hook(
        self,
        page: Page,
        context: BrowserContext,
        html: str,
        **kwargs: object,
    ) -> None:
        """Hook: Récupère cookies après consentement."""
        cookies = await context.cookies()
        self._captured_cookies = cookies
        logger.info(
            "Cookies extracted via hook",
            extra={"cookies_count": len(cookies)},
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
