"""Configuration pytest globale pour tous les tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.logger import get_logger
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
    """TestClient FastAPI avec Settings override + cache clear.

    Clear caches before and after to avoid flaky tests with @lru_cache.
    Conforms to FastAPI 2025 best practices.
    Cleanup automatique après chaque test.
    """
    get_settings.cache_clear()
    get_logger.cache_clear()

    app.dependency_overrides[get_settings] = lambda: test_settings
    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()
