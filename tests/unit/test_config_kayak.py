"""Tests unitaires KayakConfig."""

import pytest
from pydantic import ValidationError

from app.core.config import KayakConfig


def test_kayak_config_defaults():
    """Valeurs par defaut sans env vars."""
    config = KayakConfig()

    assert config.consent_timeout == 5000
    assert config.wait_for_results_timeout == 60000
    assert config.delay_before_return == 45.0
    assert config.results_selector == "[data-resultid]"
    assert config.progress_bar_selector == '[role="progressbar"]'


def test_kayak_config_env_override(monkeypatch):
    """Override via env variables."""
    monkeypatch.setenv("KAYAK_CONSENT_TIMEOUT", "10000")
    monkeypatch.setenv("KAYAK_DELAY_BEFORE_RETURN", "30.0")
    monkeypatch.setenv("KAYAK_RESULTS_SELECTOR", ".flight-card")

    config = KayakConfig()

    assert config.consent_timeout == 10000
    assert config.delay_before_return == 30.0
    assert config.results_selector == ".flight-card"


def test_kayak_config_extra_forbid():
    """Champ inconnu rejete avec extra=forbid."""
    with pytest.raises(ValidationError) as exc_info:
        KayakConfig(unknown_field="value")

    assert (
        "extra" in str(exc_info.value).lower()
        or "unknown_field" in str(exc_info.value).lower()
    )


def test_kayak_config_results_selector(monkeypatch):
    """Selecteur configurable via env."""
    monkeypatch.setenv("KAYAK_RESULTS_SELECTOR", ".custom-selector")

    config = KayakConfig()

    assert config.results_selector == ".custom-selector"
