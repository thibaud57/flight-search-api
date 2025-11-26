"""Tests unitaires pour ProxyService."""

import logging

import pytest

from app.models import ProxyConfig
from app.services import ProxyService


def test_proxy_service_round_robin_rotation(mock_proxy_pool: list[ProxyConfig]) -> None:
    """Rotation round-robin cycle 3 proxies."""
    service = ProxyService(mock_proxy_pool)

    results = [service.get_next_proxy().username for _ in range(6)]

    expected = [
        "proxy0user",
        "proxy1user",
        "proxy2user",
        "proxy0user",
        "proxy1user",
        "proxy2user",
    ]

    assert results == expected


def test_proxy_service_get_next_logging(
    mock_proxy_pool: list[ProxyConfig], caplog: pytest.LogCaptureFixture
) -> None:
    """get_next_proxy() log DEBUG contient mot-clé 'proxy'."""
    service = ProxyService(mock_proxy_pool)

    with caplog.at_level(logging.DEBUG, logger="app.services.proxy_service"):
        service.get_next_proxy()

    assert len(caplog.records) > 0
    assert any(record.levelname == "DEBUG" for record in caplog.records)


def test_proxy_service_empty_pool_error() -> None:
    """Pool vide leve ValueError."""
    with pytest.raises(ValueError) as exc_info:
        ProxyService([])

    assert "empty" in str(exc_info.value).lower()
