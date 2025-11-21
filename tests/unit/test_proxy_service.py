"""Tests unitaires pour ProxyService."""

import logging

import pytest

from app.models.proxy import ProxyConfig
from app.services.proxy_service import ProxyService


@pytest.fixture
def proxy_pool() -> list[ProxyConfig]:
    """Pool de 3 proxies pour tests."""
    return [
        ProxyConfig(
            host="fr.decodo.com",
            port=40000,
            username="proxy0user",
            password="password0",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40001,
            username="proxy1user",
            password="password1",
            country="FR",
        ),
        ProxyConfig(
            host="fr.decodo.com",
            port=40002,
            username="proxy2user",
            password="password2",
            country="FR",
        ),
    ]


def test_proxy_service_round_robin_rotation(proxy_pool: list[ProxyConfig]) -> None:
    """Rotation round-robin cycle 3 proxies."""
    service = ProxyService(proxy_pool)

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


def test_proxy_service_random_distribution(proxy_pool: list[ProxyConfig]) -> None:
    """Mode random couvre tous proxies."""
    service = ProxyService(proxy_pool)

    results = {service.get_random_proxy().username for _ in range(100)}

    assert "proxy0user" in results
    assert "proxy1user" in results
    assert "proxy2user" in results


def test_proxy_service_get_next_logging(
    proxy_pool: list[ProxyConfig], caplog: pytest.LogCaptureFixture
) -> None:
    """Logging structure appel get_next_proxy()."""
    service = ProxyService(proxy_pool)

    with caplog.at_level(logging.INFO):
        service.get_next_proxy()

    assert any("proxy" in record.message.lower() for record in caplog.records)


def test_proxy_service_reset_pool(proxy_pool: list[ProxyConfig]) -> None:
    """Reset cycle remet index a 0."""
    service = ProxyService(proxy_pool)

    for _ in range(5):
        service.get_next_proxy()

    service.reset_pool()
    proxy = service.get_next_proxy()

    assert proxy.username == "proxy0user"


def test_proxy_service_empty_pool_error() -> None:
    """Pool vide leve ValueError."""
    with pytest.raises(ValueError) as exc_info:
        ProxyService([])

    assert "empty" in str(exc_info.value).lower()


def test_proxy_service_current_index_property(proxy_pool: list[ProxyConfig]) -> None:
    """Property current_proxy_index retourne index correct."""
    service = ProxyService(proxy_pool)

    for _ in range(4):
        service.get_next_proxy()

    assert service.current_proxy_index == 1
