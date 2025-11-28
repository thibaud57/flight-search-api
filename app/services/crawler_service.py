"""Service de crawling avec stealth mode et proxy rotation."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING

from crawl4ai import AsyncWebCrawler, CacheMode, CrawlerRunConfig
from crawl4ai import CrawlResult as Crawl4AICrawlResult
from playwright.async_api import BrowserContext, Cookie, Page, Response
from tenacity import retry

from app.core import get_settings
from app.exceptions import CaptchaDetectedError, NetworkError, SessionCaptureError
from app.models import Provider, ProxyConfig
from app.services import RetryStrategy
from app.utils import (
    build_browser_config_from_fingerprint,
    capture_kayak_poll_data,
    get_base_browser_config,
)

if TYPE_CHECKING:
    from app.services.proxy_service import ProxyService

logger = logging.getLogger(__name__)

KAYAK_POLL_TIMEOUT_S = 60.0
CONSENT_BUTTON_WAIT_TIMEOUT_MS = 10000
RETRYABLE_HTTP_STATUS_CODES = (
    HTTPStatus.INTERNAL_SERVER_ERROR,
    HTTPStatus.BAD_GATEWAY,
    HTTPStatus.SERVICE_UNAVAILABLE,
    HTTPStatus.GATEWAY_TIMEOUT,
    HTTPStatus.TOO_MANY_REQUESTS,
    HTTPStatus.FORBIDDEN,
)

SESSION_URLS = {
    Provider.GOOGLE: "https://www.google.com/travel/flights",
    Provider.KAYAK: "https://www.kayak.fr/flights",
}
CAPTCHA_PATTERNS = {
    "recaptcha": ["g-recaptcha", 'class="recaptcha"', "grecaptcha"],
    "hcaptcha": ["h-captcha", "hcaptcha"],
}
CONSENT_SELECTORS = {
    Provider.GOOGLE: [
        'button:has-text("Tout accepter")',
        'button:has-text("Accept all")',
    ],
    Provider.KAYAK: [
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
    poll_data: dict[str, object] | None = None


class CrawlerService:
    """Service de crawling avec stealth mode et proxy rotation."""

    def __init__(self, proxy_service: ProxyService | None = None) -> None:
        """Initialise service avec ProxyService optionnel."""
        self._proxy_service = proxy_service
        self._settings = get_settings()
        self._captured_cookies: list[Cookie] = []
        self.provider: Provider = Provider.GOOGLE
        self._kayak_poll_data: dict[str, object] | None = None

    @retry(**RetryStrategy.get_session_retry())  # type: ignore[misc]  # Tenacity decorator incompatible with mypy strict
    async def get_session(
        self,
        provider: Provider,
        *,
        use_proxy: bool = True,
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
                "provider": provider.value,
                "url": url,
                "proxy_host": proxy.host if proxy else "no_proxy",
                "proxy_country": proxy.country if proxy else "N/A",
            },
        )

        browser_config = get_base_browser_config(proxy_config=proxy_config)

        async with AsyncWebCrawler(config=browser_config) as crawler:

            async def _after_goto_hook(
                page: Page,
                context: BrowserContext,
                url: str,
                response: Response,
                **kwargs: object,
            ) -> Page:
                """Hook get_session : gère consent directement."""
                await self._handle_consent(page)
                return page

            crawler.crawler_strategy.set_hook("after_goto", _after_goto_hook)
            crawler.crawler_strategy.set_hook(
                "before_return_html", self._extract_cookies_hook
            )
            run_config = self._build_crawler_run_config("css:body", provider=provider)
            result = await self._execute_crawl(
                crawler,
                url,
                run_config,
                operation="session capture",
                provider=provider,
                proxy_host=proxy.host if proxy else "no_proxy",
            )

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (
            HTTPStatus.FORBIDDEN,
            HTTPStatus.TOO_MANY_REQUESTS,
        ):
            logger.error(
                "Session capture failed",
                extra={
                    "provider": provider.value,
                    "url": url,
                    "status_code": result.status_code,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise NetworkError(url=url, status_code=result.status_code)

        if not self._captured_cookies:
            logger.warning(
                "Session captured but no cookies found",
                extra={
                    "provider": provider.value,
                    "status_code": result.status_code,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                },
            )
            raise SessionCaptureError(
                provider=provider.value,
                reason="No cookies captured (consent may have failed)",
            )

        logger.info(
            "Session captured",
            extra={
                "provider": provider.value,
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
        provider: Provider,
        *,
        use_proxy: bool = True,
    ) -> CrawlResult:
        """Crawl une URL de recherche vols avec proxy rotation et retry logic."""
        attempt_count = 0
        if provider == Provider.KAYAK:
            self._kayak_poll_data = None

        @retry(**RetryStrategy.get_crawler_retry())  # type: ignore[misc]  # Tenacity decorator incompatible with mypy strict
        async def _crawl_with_retry() -> CrawlResult:
            nonlocal attempt_count
            attempt_count += 1

            start_time = time.time()
            proxy_config, proxy = self._get_proxy_config(use_proxy)

            logger.info(
                "Starting crawl",
                extra={
                    "provider": provider.value,
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

            wait_for_selector = "css:.pIav2d" if provider == Provider.GOOGLE else None
            run_config = self._build_crawler_run_config(
                wait_for_selector, provider=provider
            )

            try:
                async with AsyncWebCrawler(config=config) as crawler:
                    if provider == Provider.KAYAK:
                        crawler.crawler_strategy.set_hook(
                            "after_goto", self._crawl_after_goto_hook
                        )

                    result = await self._execute_crawl(
                        crawler,
                        url,
                        run_config,
                        operation="crawl",
                        provider=provider,
                        proxy_host=proxy.host if proxy else "no_proxy",
                        attempts=attempt_count,
                    )
            except CaptchaDetectedError:
                if use_proxy and self._proxy_service:
                    self._proxy_service.get_next_proxy()
                    logger.debug("Proxy rotation triggered after captcha")
                raise

            response_time_ms = int((time.time() - start_time) * 1000)

            if not result.success and result.status_code == HTTPStatus.NOT_FOUND:
                return CrawlResult(
                    success=False, html="", status_code=HTTPStatus.NOT_FOUND
                )

            if not result.success or result.status_code in RETRYABLE_HTTP_STATUS_CODES:
                error_msg = "Crawl failed"
                if (
                    result.status_code
                    in (HTTPStatus.TOO_MANY_REQUESTS, HTTPStatus.FORBIDDEN)
                    and use_proxy
                    and self._proxy_service
                ):
                    self._proxy_service.get_next_proxy()
                    error_msg = "Rate limit/forbidden - proxy rotated"
                logger.error(
                    error_msg,
                    extra={
                        "provider": provider.value,
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

            poll_data = None
            if provider == Provider.KAYAK:
                poll_data = self._kayak_poll_data

            is_result_valid = (
                provider == Provider.KAYAK and poll_data is not None
            ) or (provider == Provider.GOOGLE and html)

            if not is_result_valid:
                error_reason = (
                    "poll_data is None"
                    if provider == Provider.KAYAK
                    else "HTML is empty or None"
                )
                logger.warning(
                    "Crawl result validation failed - retrying",
                    extra={
                        "provider": provider.value,
                        "url": url,
                        "reason": error_reason,
                        "html_size": len(html),
                        "poll_data_available": poll_data is not None,
                    },
                )
                raise NetworkError(
                    url=url, status_code=result.status_code, attempts=attempt_count
                )

            logger.info(
                "Crawl successful",
                extra={
                    "provider": provider.value,
                    "status_code": result.status_code,
                    "html_size": len(html),
                    "response_time_ms": response_time_ms,
                    "proxy_host": proxy.host if proxy else "no_proxy",
                    "poll_data_available": poll_data is not None,
                },
            )

            return CrawlResult(
                success=True,
                html=html,
                status_code=result.status_code,
                poll_data=poll_data,
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

    def has_valid_cookies(self) -> bool:
        """Vérifie si des cookies valides ont été capturés."""
        return len(self._captured_cookies) > 0

    def _build_crawler_run_config(
        self,
        wait_for_selector: str | None,
        *,
        provider: Provider = Provider.GOOGLE,
    ) -> CrawlerRunConfig:
        """Construit CrawlerRunConfig avec paramètres adaptés au provider."""
        return CrawlerRunConfig(
            cache_mode=CacheMode.DISABLED,
            magic=provider == Provider.KAYAK,
            simulate_user=True,
            override_navigator=True,
            wait_for=wait_for_selector,
            page_timeout=self._settings.crawler.crawl_page_timeout_ms,
            delay_before_return_html=0.0
            if provider == Provider.KAYAK
            else self._settings.crawler.crawl_delay_s,
        )

    async def _crawl_after_goto_hook(
        self,
        page: Page,
        context: BrowserContext,
        url: str,
        response: Response,
        **kwargs: object,
    ) -> Page:
        """Hook crawl_flights : capture poll_data via utilitaire stateless."""
        try:
            self._kayak_poll_data = await capture_kayak_poll_data(
                page,
                timeout=KAYAK_POLL_TIMEOUT_S,
            )
        except Exception as e:
            logger.warning(
                "Poll_data capture failed in hook",
                extra={"error": str(e)},
            )
            self._kayak_poll_data = None

        return page

    async def _handle_consent(self, page: Page) -> None:
        """Detecte et ferme popup consent si present."""
        selectors = CONSENT_SELECTORS.get(self.provider, [])

        for selector in selectors:
            try:
                accept_button = await page.wait_for_selector(
                    selector, timeout=CONSENT_BUTTON_WAIT_TIMEOUT_MS
                )
                if accept_button:
                    await accept_button.click()
                    await asyncio.sleep(1)
                    logger.info(
                        "Auto-clicked consent button",
                        extra={
                            "provider": self.provider.value,
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

    async def _execute_crawl(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        run_config: CrawlerRunConfig,
        *,
        operation: str,
        provider: Provider,
        proxy_host: str,
        attempts: int = 0,
    ) -> Crawl4AICrawlResult:
        """Execute crawl avec gestion centralisée des erreurs TimeoutError et RuntimeError.

        Args:
            crawler: Instance AsyncWebCrawler à utiliser
            url: URL à crawler
            run_config: Configuration du crawl
            operation: Nom de l'opération ("session" ou "crawl")
            provider: Provider utilisé
            proxy_host: Host du proxy ou "no_proxy"
            attempts: Nombre de tentatives (pour crawl), 0 pour session

        Returns:
            Résultat du crawl (Crawl4AICrawlResult)

        Raises:
            NetworkError: En cas de timeout ou erreur runtime
        """
        try:
            result = await asyncio.wait_for(
                crawler.arun(url=url, config=run_config),
                timeout=self._settings.crawler.crawl_global_timeout_s,
            )
            return result
        except TimeoutError as err:
            error_context = {
                "provider": provider.value,
                "url": url,
                "proxy_host": proxy_host,
            }
            logger.error(
                f"{operation.capitalize()} timeout",
                extra=error_context,
            )
            raise NetworkError(url=url, status_code=None, attempts=attempts) from err
        except RuntimeError as err:
            error_context = {
                "provider": provider.value,
                "url": url,
                "proxy_host": proxy_host,
                "error": str(err),
            }
            logger.error(
                f"{operation.capitalize()} failed - Runtime error",
                extra=error_context,
            )
            raise NetworkError(url=url, status_code=None, attempts=attempts) from err

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
