"""Tests unitaires pour Settings (Pydantic BaseSettings)."""

import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_load_from_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings charge variables d'environnement."""
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "pr.decodo.com:8080")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "true")

    settings = Settings()

    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.DECODO_USERNAME == "customer-XXX-country-FR"
    assert settings.DECODO_PASSWORD == "password123"
    assert settings.DECODO_PROXY_HOST == "pr.decodo.com:8080"
    assert settings.PROXY_ROTATION_ENABLED is True
    assert settings.CAPTCHA_DETECTION_ENABLED is True


def test_settings_load_from_dotenv_file(tmp_path: Path) -> None:
    """Settings charge depuis fichier .env."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=INFO\n"
        "DECODO_USERNAME=customer-TEST-country-FR\n"
        "DECODO_PASSWORD=testpass123\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
        "PROXY_ROTATION_ENABLED=true\n"
        "CAPTCHA_DETECTION_ENABLED=true\n"
    )

    settings = Settings(_env_file=str(env_file))

    assert settings.LOG_LEVEL == "INFO"
    assert settings.DECODO_USERNAME == "customer-TEST-country-FR"
    assert settings.DECODO_PASSWORD == "testpass123"


def test_settings_env_vars_override_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Env vars prioritaires sur .env."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LOG_LEVEL=DEBUG\n"
        "DECODO_USERNAME=customer-FILE-country-FR\n"
        "DECODO_PASSWORD=filepass\n"
        "DECODO_PROXY_HOST=pr.decodo.com:8080\n"
        "PROXY_ROTATION_ENABLED=true\n"
        "CAPTCHA_DETECTION_ENABLED=true\n"
    )
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

    settings = Settings(_env_file=str(env_file))

    assert settings.LOG_LEVEL == "ERROR"


def test_settings_log_level_literal_validation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """LOG_LEVEL accepte uniquement valeurs valides."""
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "LOG_LEVEL" in str(exc_info.value)


def test_settings_decodo_username_format_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_USERNAME format customer-{key}-country-{code} validé."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "true")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "true")

    settings = Settings()

    assert settings.DECODO_USERNAME == "customer-XXX-country-FR"


def test_settings_decodo_username_format_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_USERNAME format invalide rejeté."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "invalid-format")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "DECODO_USERNAME" in str(exc_info.value)


def test_settings_decodo_proxy_host_format_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_PROXY_HOST format host:port validé."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "pr.decodo.com:8080")

    settings = Settings()

    assert settings.DECODO_PROXY_HOST == "pr.decodo.com:8080"


def test_settings_decodo_proxy_host_format_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DECODO_PROXY_HOST sans port rejeté."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("DECODO_PROXY_HOST", "pr.decodo.com")

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "DECODO_PROXY_HOST" in str(exc_info.value)


def test_settings_boolean_fields_coercion(monkeypatch: pytest.MonkeyPatch) -> None:
    """Booléens acceptent "true"/"false" strings."""
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
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
    monkeypatch.setenv("DECODO_USERNAME", "customer-XXX-country-FR")
    monkeypatch.setenv("DECODO_PASSWORD", "password123")
    monkeypatch.setenv("PROXY_ROTATION_ENABLED", "false")
    monkeypatch.setenv("CAPTCHA_DETECTION_ENABLED", "false")

    with caplog.at_level(logging.WARNING):
        settings = Settings()

    assert settings.PROXY_ROTATION_ENABLED is False
    assert settings.CAPTCHA_DETECTION_ENABLED is False
    assert any("risk" in record.message.lower() for record in caplog.records)
