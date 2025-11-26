"""Utilitaires fingerprint navigateur (headers statiques, formatage config)."""

from __future__ import annotations

from crawl4ai import BrowserConfig
from playwright.async_api import Cookie


def get_static_headers() -> dict[str, str]:
    """Retourne headers HTTP statiques Chrome 142 éprouvés."""
    return {
        "Accept": "*/*",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-form-factors": '"Desktop"',
        "sec-ch-ua-full-version": '"142.0.7444.176"',
        "sec-ch-ua-full-version-list": '"Chromium";v="142.0.7444.176", "Google Chrome";v="142.0.7444.176", "Not_A Brand";v="99.0.0.0"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"19.0.0"',
        "sec-ch-ua-wow64": "?0",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "x-same-domain": "1",
        "x-browser-channel": "stable",
        "x-browser-copyright": "Copyright 2025 Google LLC. All Rights reserved.",
        "x-browser-year": "2025",
    }


def get_stealth_browser_args() -> list[str]:
    """Retourne args Chrome pour stealth mode anti-détection + anti-leak geolocation."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-webrtc",
        "--disable-webrtc-multiple-routes",
        "--disable-webrtc-hw-encoding",
        "--enforce-webrtc-ip-permission-check",
    ]


def get_base_browser_config(
    headers: dict[str, str] | None = None,
    cookies: list[Cookie] | None = None,
    proxy_config: dict[str, str] | None = None,
) -> BrowserConfig:
    """Construit BrowserConfig de base avec stealth manuel (Chrome flags)."""
    return BrowserConfig(
        headless=False,
        extra_args=get_stealth_browser_args(),
        headers=headers or get_static_headers(),
        cookies=cookies or [],
        viewport_width=1920,
        viewport_height=1080,
        proxy_config=proxy_config,
        enable_stealth=False,
    )


def build_browser_config_from_fingerprint(
    url: str,
    cookies: list[Cookie],
    proxy_config: dict[str, str] | None = None,
    headers_dict: dict[str, str] | None = None,
) -> BrowserConfig:
    """Construit BrowserConfig depuis session Google capturée."""
    base_headers = headers_dict or get_static_headers()

    headers = {
        "Accept": base_headers.get("Accept", "*/*"),
        "Accept-Language": base_headers.get("Accept-Language", "fr-FR,fr;q=0.9"),
        "Accept-Encoding": base_headers.get(
            "Accept-Encoding", "gzip, deflate, br, zstd"
        ),
        "User-Agent": base_headers.get("User-Agent", ""),
        "Referer": url,
        "Origin": "https://www.google.com",
    }

    client_hints = {
        k: v
        for k, v in base_headers.items()
        if k.startswith("sec-ch-ua") or k.startswith("sec-fetch")
    }
    headers.update(client_hints)

    return get_base_browser_config(
        headers=headers,
        cookies=cookies,
        proxy_config=proxy_config,
    )
