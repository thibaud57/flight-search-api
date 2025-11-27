"""Tests unitaires pour browser_fingerprint utilities."""

from crawl4ai import BrowserConfig

from app.utils import (
    build_browser_config_from_fingerprint,
    get_base_browser_config,
    get_static_headers,
    get_stealth_browser_args,
)


def test_get_static_headers_returns_dict():
    """Retourne dict headers statiques."""
    headers = get_static_headers()

    assert isinstance(headers, dict)
    assert len(headers) > 0


def test_get_static_headers_contains_user_agent():
    """Headers contiennent User-Agent Chrome."""
    headers = get_static_headers()

    assert "User-Agent" in headers
    assert "Chrome" in headers["User-Agent"]


def test_get_static_headers_contains_accept_language():
    """Headers contiennent Accept-Language fr-FR."""
    headers = get_static_headers()

    assert "Accept-Language" in headers
    assert "fr-FR" in headers["Accept-Language"]


def test_get_stealth_browser_args_returns_list():
    """Retourne liste args Chrome."""
    args = get_stealth_browser_args()

    assert isinstance(args, list)
    assert len(args) > 0


def test_get_stealth_browser_args_contains_anti_automation():
    """Args contiennent flag anti-automation."""
    args = get_stealth_browser_args()

    assert "--disable-blink-features=AutomationControlled" in args


def test_get_stealth_browser_args_contains_no_sandbox():
    """Args contiennent --no-sandbox."""
    args = get_stealth_browser_args()

    assert "--no-sandbox" in args


def test_get_base_browser_config_returns_browserconfig():
    """Retourne instance BrowserConfig."""
    config = get_base_browser_config()

    assert isinstance(config, BrowserConfig)


def test_get_base_browser_config_default_headers():
    """Config utilise headers statiques par défaut."""
    config = get_base_browser_config()

    assert config.headers is not None
    assert "User-Agent" in config.headers


def test_get_base_browser_config_custom_headers():
    """Config accepte headers custom."""
    custom_headers = {"Custom-Header": "test"}

    config = get_base_browser_config(headers=custom_headers)

    assert config.headers == custom_headers


def test_get_base_browser_config_with_proxy():
    """Config accepte proxy_config."""
    proxy = {"server": "http://proxy.com:8080"}

    config = get_base_browser_config(proxy_config=proxy)

    assert config.proxy_config == proxy


def test_build_browser_config_from_fingerprint_adds_referer():
    """Config depuis fingerprint ajoute Referer."""
    url = "https://www.google.com/travel/flights"
    cookies = []

    config = build_browser_config_from_fingerprint(url, cookies)

    assert config.headers is not None
    assert "Referer" in config.headers
    assert config.headers["Referer"] == url


def test_build_browser_config_from_fingerprint_adds_origin():
    """Config depuis fingerprint ajoute Origin Google."""
    url = "https://www.google.com/travel/flights"
    cookies = []

    config = build_browser_config_from_fingerprint(url, cookies)

    assert config.headers is not None
    assert "Origin" in config.headers
    assert config.headers["Origin"] == "https://www.google.com"


def test_build_browser_config_from_fingerprint_preserves_cookies():
    """Config depuis fingerprint preserve cookies."""
    url = "https://www.google.com/travel/flights"
    cookies = [{"name": "test", "value": "cookie"}]

    config = build_browser_config_from_fingerprint(url, cookies)

    assert config.cookies == cookies


def test_build_browser_config_from_fingerprint_custom_headers():
    """Config depuis fingerprint accepte headers custom."""
    url = "https://www.google.com/travel/flights"
    cookies = []
    custom_headers = {"Custom-Header": "test"}

    config = build_browser_config_from_fingerprint(
        url, cookies, headers_dict=custom_headers
    )

    assert config.headers is not None
    assert "Custom-Header" in config.headers
    assert config.headers["Custom-Header"] == "test"
