"""Tests unitaires pour KayakPollingConfig."""

import pytest
from pydantic import ValidationError

from app.services.kayak_polling_config import KayakPollingConfig


class TestKayakPollingConfig:
    """Tests configuration polling Kayak."""

    def test_config_default_values(self):
        """Config avec valeurs défaut si env vars absentes."""
        # Arrange & Act
        config = KayakPollingConfig()

        # Assert
        assert config.page_load_timeout == 30
        assert config.first_results_wait == 20
        assert config.max_total_wait == 45
        assert config.poll_interval_min == 4
        assert config.poll_interval_max == 8

    def test_config_env_override(self, monkeypatch):
        """Env vars overrides valeurs défaut."""
        # Arrange
        monkeypatch.setenv("KAYAK_MAX_TOTAL_WAIT", "60")

        # Act
        config = KayakPollingConfig()

        # Assert
        assert config.max_total_wait == 60
        assert config.page_load_timeout == 30  # Default preserved

    def test_config_validates_poll_interval(self):
        """Validation poll_interval_max >= min."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakPollingConfig(poll_interval_min=10, poll_interval_max=5)

        assert "poll_interval_max" in str(exc_info.value).lower()

    def test_config_validates_min_timeout(self, caplog):
        """Validation max_total_wait >= 30 (warning)."""
        # Arrange & Act
        config = KayakPollingConfig(max_total_wait=10)

        # Assert
        assert config.max_total_wait == 10
        assert "WARNING" in caplog.text or "warning" in caplog.text.lower()

    def test_config_extra_forbid(self):
        """Champs inconnus rejetés."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            KayakPollingConfig(unknown_field="value")

        error_msg = str(exc_info.value).lower()
        assert (
            "extra inputs are not permitted" in error_msg
            or "extra fields not permitted" in error_msg
        )
