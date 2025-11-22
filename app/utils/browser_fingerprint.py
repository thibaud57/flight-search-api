"""Générateur automatique de fingerprint navigateur (headers + cookies)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from playwright.async_api import async_playwright

if TYPE_CHECKING:
    from crawl4ai import BrowserConfig


class BrowserFingerprintError(Exception):
    """Erreur lors de la capture du fingerprint navigateur."""


async def capture_browser_headers(url: str) -> dict[str, str]:
    """Capture headers HTTP réels depuis Chrome via Playwright."""
    captured_headers: dict[str, str] = {}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="fr-FR",
            )
            page = await context.new_page()

            async def capture_request(route, request):
                if "browserinfo" in request.url or request.url == url:
                    captured_headers.update(request.headers)
                await route.continue_()

            await page.route("**/*", capture_request)
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)

            await browser.close()
    except Exception as e:
        msg = f"Échec capture headers navigateur: {e}"
        raise BrowserFingerprintError(msg) from e

    if not captured_headers:
        msg = "Aucun header capturé depuis le navigateur"
        raise BrowserFingerprintError(msg)

    if "user-agent" not in captured_headers:
        msg = "Header User-Agent manquant dans la capture"
        raise BrowserFingerprintError(msg)

    return captured_headers


async def capture_google_cookies(
    url: str = "https://www.google.com/travel/flights",
    *,
    incognito: bool = True,
) -> list[dict[str, str]]:
    """Capture cookies Google depuis navigation privée."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "locale": "fr-FR",
            }
            if incognito:
                context_options["storage_state"] = None

            context = await browser.new_context(**context_options)
            page = await context.new_page()

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(5000)

            raw_cookies = await context.cookies()
            await browser.close()
    except Exception as e:
        msg = f"Échec capture cookies Google: {e}"
        raise BrowserFingerprintError(msg) from e

    google_cookies = [
        {"name": c["name"], "value": c["value"], "url": url}
        for c in raw_cookies
        if c["domain"] in (".google.com", "google.com")
        and c["name"] in ("SOCS", "AEC", "CONSENT")
    ]

    if not google_cookies:
        msg = "Aucun cookie Google capturé (SOCS, AEC, CONSENT)"
        raise BrowserFingerprintError(msg)

    return google_cookies


def build_browser_config_from_fingerprint(
    url: str,
    headers: dict[str, str],
    cookies: list[dict[str, str]],
    proxy_config: dict[str, str] | None = None,
) -> dict[str, object]:
    """Construit BrowserConfig dict depuis fingerprint capturé."""
    essential_headers = {
        "Accept": headers.get("accept", "*/*"),
        "Accept-Language": headers.get("accept-language", "fr-FR,fr;q=0.9"),
        "Accept-Encoding": headers.get("accept-encoding", "gzip, deflate, br, zstd"),
        "User-Agent": headers.get("user-agent", ""),
        "Referer": url,
        "Origin": "https://www.google.com",
    }

    client_hints = {
        k: v
        for k, v in headers.items()
        if k.startswith("sec-ch-ua") or k.startswith("sec-fetch")
    }
    essential_headers.update(client_hints)

    google_specific = {
        "x-same-domain": "1",
        "x-browser-channel": "stable",
        "x-browser-copyright": "Copyright 2025 Google LLC. All Rights reserved.",
        "x-browser-year": "2025",
    }
    essential_headers.update(google_specific)

    return {
        "headless": False,
        "enable_stealth": False,
        "proxy_config": proxy_config,
        "headers": essential_headers,
        "cookies": cookies,
        "viewport_width": 1920,
        "viewport_height": 1080,
    }


async def generate_fresh_browser_config(
    url: str,
    proxy_config: dict[str, str] | None = None,
) -> dict[str, object]:
    """Génère BrowserConfig complet avec headers/cookies frais capturés automatiquement."""
    headers, cookies = await asyncio.gather(
        capture_browser_headers(url),
        capture_google_cookies(),
    )

    return build_browser_config_from_fingerprint(url, headers, cookies, proxy_config)
