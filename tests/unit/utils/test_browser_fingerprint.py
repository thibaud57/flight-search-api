"""Tests unitaires pour browser_fingerprint utilities."""

from crawl4ai import BrowserConfig

from app.utils import (
    build_browser_config_from_fingerprint,
    get_base_browser_config,
)


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

    assert config.proxy_config is not None
    assert config.proxy_config.server == proxy["server"]


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
