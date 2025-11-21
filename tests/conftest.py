"""Configuration pytest globale pour tous les tests."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.logger import get_logger, setup_logger
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
    """TestClient FastAPI avec Settings + Logger override + cache clear.

    Override both get_settings AND get_logger to prevent ValidationError in CI.
    get_logger() calls get_settings() directly (not via Depends), so
    app.dependency_overrides[get_settings] alone is not enough.

    Clear caches before and after to avoid flaky tests with @lru_cache.
    Conforms to FastAPI 2025 best practices.
    Cleanup automatique après chaque test.
    """
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()
