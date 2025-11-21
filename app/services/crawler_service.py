"""Service de crawling Google Flights avec stealth mode."""

import asyncio
import logging
import time
from dataclasses import dataclass

from crawl4ai import AsyncWebCrawler, BrowserConfig

from app.exceptions import CaptchaDetectedError, NetworkError

logger = logging.getLogger(__name__)

CAPTCHA_PATTERNS = {
    "recaptcha": ["g-recaptcha", 'class="recaptcha"', "grecaptcha"],
    "hcaptcha": ["h-captcha", "hcaptcha"],
}


@dataclass
class CrawlResult:
    """Résultat d'un crawl."""

    success: bool
    html: str
    status_code: int | None = None


class CrawlerService:
    """Service de crawling Google Flights avec stealth mode (POC dev local)."""

    async def crawl_google_flights(self, url: str) -> CrawlResult:
        """Crawl une URL Google Flights en mode POC avec captcha detection."""
        start_time = time.time()
        logger.info("Starting crawl", extra={"url": url, "stealth_mode": True})

        config = BrowserConfig(headless=True, enable_stealth=True)

        try:
            async with AsyncWebCrawler(config=config) as crawler:
                result = await asyncio.wait_for(
                    crawler.arun(url=url),
                    timeout=10.0,
                )
        except TimeoutError as err:
            logger.error("Crawl timeout", extra={"url": url})
            raise NetworkError(url=url, status_code=None) from err

        response_time_ms = int((time.time() - start_time) * 1000)

        if not result.success or result.status_code in (403, 429):
            logger.error(
                "Crawl failed",
                extra={"url": url, "status_code": result.status_code},
            )
            raise NetworkError(url=url, status_code=result.status_code)

        html = result.html or ""
        self._detect_captcha(html, url)

        logger.info(
            "Crawl successful",
            extra={
                "url": url,
                "status_code": result.status_code,
                "html_size": len(html),
                "response_time_ms": response_time_ms,
                "stealth_mode": True,
            },
        )

        return CrawlResult(
            success=True,
            html=html,
            status_code=result.status_code,
        )

    def _detect_captcha(self, html: str, url: str) -> None:
        """Détecte la présence de captcha dans le HTML."""
        html_lower = html.lower()

        for captcha_type, patterns in CAPTCHA_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in html_lower:
                    logger.warning(
                        "Captcha detected",
                        extra={"url": url, "captcha_type": captcha_type},
                    )
                    raise CaptchaDetectedError(url=url, captcha_type=captcha_type)
