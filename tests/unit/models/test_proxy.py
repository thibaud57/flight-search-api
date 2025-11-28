"""Tests unitaires pour ProxyConfig."""

import pytest
from pydantic import ValidationError


def test_proxy_config_valid_fields(proxy_config_factory) -> None:
    """ProxyConfig avec tous champs valides."""
    config = proxy_config_factory()

    assert config.host == "proxy.example.com"
    assert config.port == 40000
    assert config.username == "testuser"
    assert config.password.get_secret_value() == "testpass"
    assert config.country == "FR"


def test_proxy_config_username_too_short(proxy_config_factory) -> None:
    """Username trop court leve ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        proxy_config_factory(username="abc")

    assert "at least 5 characters" in str(exc_info.value).lower()


def test_proxy_config_invalid_port(proxy_config_factory) -> None:
    """Port invalide (hors plage 1-65535) leve ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        proxy_config_factory(port=0)

    assert "port" in str(exc_info.value).lower()


def test_proxy_config_generate_url_format(proxy_config_factory) -> None:
    """get_proxy_url() genere URL correcte."""
    config = proxy_config_factory()

    assert config.get_proxy_url() == "http://testuser:testpass@proxy.example.com:40000"


def test_proxy_config_country_uppercase_conversion(proxy_config_factory) -> None:
    """Country automatiquement converti en uppercase."""
    config = proxy_config_factory(country="fr")

    assert config.country == "FR"
