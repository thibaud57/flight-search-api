"""Tests unitaires pour Settings (Pydantic BaseSettings)."""

import logging

import pytest
from pydantic import ValidationError


def test_settings_load_from_env_vars(settings_env_factory) -> None:
    """Settings charge variables d'environnement."""
    settings = settings_env_factory(LOG_LEVEL="DEBUG")

    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.PROXY_USERNAME == "testuser"
    assert settings.PROXY_PASSWORD.get_secret_value() == "password123"
    assert settings.PROXY_HOST == "proxy.example.com:40000"
    assert settings.PROXY_ROTATION_ENABLED is True
    assert settings.CAPTCHA_DETECTION_ENABLED is True


def test_settings_log_level_literal_validation(settings_env_factory) -> None:
    """LOG_LEVEL accepte uniquement valeurs valides."""
    with pytest.raises(ValidationError) as exc_info:
        settings_env_factory(LOG_LEVEL="INVALID")

    assert "LOG_LEVEL" in str(exc_info.value)


def test_settings_proxy_username_format_valid(settings_env_factory) -> None:
    """PROXY_USERNAME min 5 chars valide."""
    settings = settings_env_factory()

    assert settings.PROXY_USERNAME == "testuser"


def test_settings_proxy_username_format_invalid(settings_env_factory) -> None:
    """PROXY_USERNAME trop court rejete."""
    with pytest.raises(ValidationError) as exc_info:
        settings_env_factory(PROXY_USERNAME="abc")

    assert "PROXY_USERNAME" in str(exc_info.value)


def test_settings_proxy_host_format_valid(settings_env_factory) -> None:
    """PROXY_HOST format host:port valide."""
    settings = settings_env_factory()

    assert settings.PROXY_HOST == "proxy.example.com:40000"


def test_settings_proxy_host_format_invalid(settings_env_factory) -> None:
    """PROXY_HOST sans port rejete."""
    with pytest.raises(ValidationError) as exc_info:
        settings_env_factory(PROXY_HOST="proxy.example.com")

    assert "PROXY_HOST" in str(exc_info.value)


def test_settings_boolean_fields_coercion(settings_env_factory) -> None:
    """Booleens acceptent true/false strings."""
    settings = settings_env_factory(CAPTCHA_DETECTION_ENABLED="false")

    assert settings.PROXY_ROTATION_ENABLED is True
    assert settings.CAPTCHA_DETECTION_ENABLED is False


def test_settings_model_validator_warns_risky_config(
    settings_env_factory, caplog: pytest.LogCaptureFixture
) -> None:
    """Configuration à risque loggée (rotation+captcha disabled)."""
    with caplog.at_level(logging.WARNING):
        settings = settings_env_factory(
            PROXY_ROTATION_ENABLED="false", CAPTCHA_DETECTION_ENABLED="false"
        )

    assert settings.PROXY_ROTATION_ENABLED is False
    assert settings.CAPTCHA_DETECTION_ENABLED is False
    assert any("risk" in record.message.lower() for record in caplog.records)


def test_settings_proxy_config_generation(settings_env_factory) -> None:
    """model_validator genere ProxyConfig depuis env vars."""
    settings = settings_env_factory()

    assert settings.proxy_config is not None
    assert settings.proxy_config.host == "proxy.example.com"
    assert settings.proxy_config.port == 40000
    assert settings.proxy_config.username == "testuser"


def test_settings_proxy_disabled(settings_env_factory) -> None:
    """Proxies desactives genere None."""
    settings = settings_env_factory(PROXY_ROTATION_ENABLED="false")

    assert settings.proxy_config is None


def test_settings_secret_str_password_masked(settings_env_factory) -> None:
    """SecretStr masque password dans logs."""
    settings = settings_env_factory(PROXY_PASSWORD="secret123")

    assert str(settings.PROXY_PASSWORD) == "**********"
    assert settings.PROXY_PASSWORD.get_secret_value() == "secret123"
