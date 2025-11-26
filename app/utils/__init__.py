"""Utilitaires du projet."""

from app.utils.browser_fingerprint import (
    build_browser_config_from_fingerprint,
    get_base_browser_config,
    get_static_headers,
    get_stealth_browser_args,
)
from app.utils.google_flights_url import (
    GoogleFlightsUrlError,
    generate_google_flights_url,
)
from app.utils.kayak_url import KayakUrlError, generate_kayak_url

__all__ = [
    "GoogleFlightsUrlError",
    "KayakUrlError",
    "build_browser_config_from_fingerprint",
    "generate_google_flights_url",
    "generate_kayak_url",
    "get_base_browser_config",
    "get_static_headers",
    "get_stealth_browser_args",
]
