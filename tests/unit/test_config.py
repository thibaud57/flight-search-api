"""Tests unitaires pour Settings (Pydantic BaseSettings)."""

import logging

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_from_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings charge variables d'environnement."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "true")

    settings = Settings()

    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DECODO_USERNAME == "spierhheqr"
    assert settings.DECODO_PASSWORD.get_secret_value() == "password123"
    assert settings.DECODO_PROXY_HOST == "fr.decodo.com:40000"
    assert settings.PROXY_ROTATION_ENABLED is True
    assert settings.CAPTCHA_DETECTION_ENABLED is True


def test_settings_log_level_literal_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LOG_LEVEL accepte uniquement valeurs valides."""
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "LOG_LEVEL" in str(exc_info.value)


def test_settings_decodo_username_format_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_USERNAME min 5 chars valide."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "true")

    settings = Settings()

    assert settings.DECODO_USERNAME == "spierhheqr"


def test_settings_decodo_username_format_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_USERNAME trop court rejete."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "abc")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "DECODO_USERNAME" in str(exc_info.value)


def test_settings_decodo_proxy_host_format_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_PROXY_HOST format host:port valide."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")

    settings = Settings()

    assert settings.DECODO_PROXY_HOST == "fr.decodo.com:40000"


def test_settings_decodo_proxy_host_format_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_PROXY_HOST sans port rejete."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "DECODO_PROXY_HOST" in str(exc_info.value)


def test_settings_boolean_fields_coercion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Booleens acceptent true/false strings."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "false")

    settings = Settings()

    assert settings.PROXY_ROTATION_ENABLED is True
    assert settings.CAPTCHA_DETECTION_ENABLED is False


def test_settings_model_validator_warns_risky_config(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Configuration à risque loggée (rotation+captcha disabled)."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "false")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "false")

    with caplog.at_level(logging.WARNING):
        settings = Settings()

    assert settings.PROXY_ROTATION_ENABLED is False
    assert settings.CAPTCHA_DETECTION_ENABLED is False
    assert any("risk" in record.message.lower() for record in caplog.records)


def test_settings_proxy_config_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    """model_validator genere ProxyConfig depuis env vars."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("DECODO_PROXY_ENABLED", "true")

    settings = Settings()

    assert settings.proxy_config is not None
    assert settings.proxy_config.host == "fr.decodo.com"
    assert settings.proxy_config.port == 40000
    assert settings.proxy_config.username == "spierhheqr"


def test_settings_proxy_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Proxies desactives genere None."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("DECODO_PROXY_ENABLED", "false")

    settings = Settings()

    assert settings.proxy_config is None


def test_settings_username_too_short(monkeypatch: pytest.MonkeyPatch) -> None:
    """Username trop court rejette Settings."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "abc")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("DECODO_PROXY_ENABLED", "true")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "DECODO_USERNAME" in str(exc_info.value)


def test_settings_secret_str_password_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecretStr masque password dans logs."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "spierhheqr")
    monkeypatch.setenv("DECODO_PASSWORD", "secret123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "fr.decodo.com:40000")
    monkeypatch.setenv("DECODO_PROXY_ENABLED", "true")

    settings = Settings()

    assert str(settings.DECODO_PASSWORD) == "**********"
    assert settings.DECODO_PASSWORD.get_secret_value() == "secret123"
