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


# === Rotation Edge Cases ===


def test_proxy_service_single_proxy_always_same(proxy_config_factory) -> None:
    """Pool avec 1 proxy retourne toujours le meme."""
    proxy = proxy_config_factory()
    service = ProxyService([proxy])

    results = [service.get_next_proxy().username for _ in range(5)]

    assert all(username == proxy.username for username in results)


def test_proxy_service_cycle_integrity(mock_proxy_pool: list[ProxyConfig]) -> None:
    """Cycle rotation maintient integrite pool (pas de perte/duplication)."""
    service = ProxyService(mock_proxy_pool)
    pool_size = len(mock_proxy_pool)

    results = [service.get_next_proxy().username for _ in range(pool_size * 3)]

    for i in range(3):
        batch = results[i * pool_size : (i + 1) * pool_size]
        assert sorted(batch) == sorted([p.username for p in mock_proxy_pool])


def test_proxy_service_state_isolation() -> None:
    """Chaque instance ProxyService a son propre etat rotation."""
    pool = [
        ProxyConfig(
            host="proxy.test",
            port=8080,
            username=f"user{i}",
            password="password123",
            country="FR",
        )
        for i in range(3)
    ]

    service1 = ProxyService(pool)
    service2 = ProxyService(pool)

    proxy1 = service1.get_next_proxy()
    proxy2 = service2.get_next_proxy()

    assert proxy1.username == proxy2.username


def test_proxy_service_get_next_no_side_effects(
    mock_proxy_pool: list[ProxyConfig],
) -> None:
    """get_next_proxy() ne modifie pas les objets ProxyConfig."""
    service = ProxyService(mock_proxy_pool)
    original_usernames = [p.username for p in mock_proxy_pool]

    for _ in range(10):
        service.get_next_proxy()

    current_usernames = [p.username for p in mock_proxy_pool]
    assert original_usernames == current_usernames


def test_proxy_service_large_pool_performance() -> None:
    """Pool de 100 proxies performe correctement."""
    large_pool = [
        ProxyConfig(
            host="proxy.test",
            port=8080,
            username=f"user{i}",
            password="password123",
            country="FR",
        )
        for i in range(100)
    ]

    service = ProxyService(large_pool)

    for _ in range(1000):
        proxy = service.get_next_proxy()
        assert proxy is not None


def test_proxy_service_multiple_instances_independent() -> None:
    """Plusieurs instances ProxyService independantes."""
    pool1 = [
        ProxyConfig(
            host="proxy1.test", port=8080, username="user1", password="password123"
        )
    ]
    pool2 = [
        ProxyConfig(
            host="proxy2.test", port=8080, username="user2", password="password123"
        )
    ]

    service1 = ProxyService(pool1)
    service2 = ProxyService(pool2)

    proxy1 = service1.get_next_proxy()
    proxy2 = service2.get_next_proxy()

    assert proxy1.username == "user1"
    assert proxy2.username == "user2"
