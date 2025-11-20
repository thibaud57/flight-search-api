"""Configuration pytest globale pour tous les tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app


@pytest.fixture
def test_settings() -> Settings:
    """Settings mocké pour tests avec valeurs par défaut."""
    return Settings(
        DECODO_USERNAME="customer-test-country-FR",
        DECODO_PASSWORD="test_password",
        LOG_LEVEL="INFO",
    )


@pytest.fixture
def client(test_settings: Settings) -> TestClient:
    """TestClient FastAPI avec Settings override.

    Utilise app.dependency_overrides pour injecter Settings mocké,
    conformément aux best practices FastAPI 2025.
    Cleanup automatique après chaque test.
    """
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield TestClient(app)
    app.dependency_overrides.clear()
