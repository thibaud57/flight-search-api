"""Tests unitaires pour ProxyConfig."""

import pytest
from pydantic import ValidationError

from app.models.proxy import ProxyConfig


def test_proxy_config_valid_fields() -> None:
    """ProxyConfig avec tous champs valides."""
    config = ProxyConfig(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="mypassword",
        country="FR",
    )

    assert config.host == "fr.decodo.com"
    assert config.port == 40000
    assert config.username == "testuser"
    assert config.password == "mypassword"
    assert config.country == "FR"


def test_proxy_config_username_valid() -> None:
    """Username valide (min 5 caracteres)."""
    config = ProxyConfig(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="mypassword",
        country="FR",
    )

    assert config.username == "testuser"


def test_proxy_config_username_too_short() -> None:
    """Username trop court leve ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProxyConfig(
            host="fr.decodo.com",
            port=40000,
            username="abc",
            password="mypassword",
            country="FR",
        )

    assert "at least 5 characters" in str(exc_info.value).lower()


def test_proxy_config_invalid_port() -> None:
    """Port invalide (<1024) leve ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ProxyConfig(
            host="fr.decodo.com",
            port=80,
            username="testuser",
            password="mypassword",
            country="FR",
        )

    assert "port" in str(exc_info.value).lower()


def test_proxy_config_generate_url_format() -> None:
    """get_proxy_url() genere URL correcte."""
    config = ProxyConfig(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="mypassword",
        country="FR",
    )

    assert config.get_proxy_url() == "http://testuser:mypassword@fr.decodo.com:40000"


def test_proxy_config_country_uppercase_conversion() -> None:
    """Country automatiquement converti en uppercase."""
    config = ProxyConfig(
        host="fr.decodo.com",
        port=40000,
        username="testuser",
        password="mypassword",
        country="fr",
    )

    assert config.country == "FR"
