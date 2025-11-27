"""Capture stateless poll_data Kayak via interception réseau."""

from __future__ import annotations

import asyncio
import json
import logging

from playwright.async_api import Page, Response

logger = logging.getLogger(__name__)


class KayakPollCaptureError(Exception):
    """Erreur lors de la capture poll_data Kayak."""


async def capture_kayak_poll_data(
    page: Page,
    *,
    timeout: float = 60.0,
) -> dict[str, object] | None:
    """Capture poll_data Kayak via interception réseau et retourne JSON parsé."""
    poll_responses: list[dict[str, str]] = []
    priceprediction_received = False

    async def intercept_response(response: Response) -> None:
        """Intercepte une response réseau et capture si poll ou priceprediction."""
        nonlocal priceprediction_received
        url = response.url

        if "/poll" in url and response.status == 200:
            try:
                body = await response.text()
                poll_responses.append({"url": url, "body": body})
            except Exception:
                pass

        elif "priceprediction" in url and response.status == 200:
            priceprediction_received = True

    try:
        page.on(
            "response",
            lambda resp: asyncio.create_task(intercept_response(resp)),
        )

        try:
            async with asyncio.timeout(timeout):
                while not priceprediction_received:
                    await asyncio.sleep(0.5)
        except TimeoutError:
            logger.warning("PricePrediction timeout after %.0fs", timeout)

        poll_data_raw = poll_responses[-1]["body"] if poll_responses else None
        poll_data = None
        if poll_data_raw:
            try:
                poll_data = json.loads(poll_data_raw)
            except json.JSONDecodeError as e:
                logger.warning(
                    "Failed to parse poll_data JSON",
                    extra={"error": str(e)},
                )
                poll_data = None

        logger.info(
            "Poll capture completed",
            extra={
                "success": priceprediction_received,
                "polls_captured": len(poll_responses),
                "poll_data_available": poll_data is not None,
            },
        )

        return poll_data

    except Exception as e:
        logger.error(
            "Poll capture failed with unexpected error",
            extra={"error": str(e), "polls_captured": len(poll_responses)},
        )
        raise KayakPollCaptureError(f"Failed to capture poll data: {e}") from e
