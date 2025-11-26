"""Gestion du popup de consentement cookies Kayak."""

import asyncio
import logging

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class ConsentHandler:
    """Gère le popup de consentement cookies Kayak."""

    def __init__(self, consent_selectors: list[str]) -> None:
        """Initialise handler avec sélecteurs popup."""
        self.consent_selectors = consent_selectors

    async def handle_consent(self, page: Page) -> None:
        """Détecte et ferme popup consent si présent."""
        for selector in self.consent_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    await button.click()
                    logger.info(
                        "Consent popup detected and clicked",
                        extra={"selector": selector, "popup_found": True},
                    )
                    await asyncio.sleep(1)
                    return
            except PlaywrightTimeoutError:
                logger.debug(
                    "Consent selector not found",
                    extra={"selector": selector},
                )
                continue

        logger.info(
            "No consent popup found",
            extra={"selectors_tried": len(self.consent_selectors)},
        )
