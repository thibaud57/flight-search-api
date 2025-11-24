"""Configuration pytest globale - Config de base uniquement."""

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_search_service
from app.core.config import Settings, get_settings
from app.core.logger import get_logger, setup_logger
from app.main import app

# Load fixtures modules
pytest_plugins = [
    "tests.fixtures.factories",
    "tests.fixtures.mocks",
    "tests.fixtures.helpers",
]


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Settings mocké pour tests avec valeurs par défaut."""
    return Settings(
        DECODO_USERNAME="customer-test-country-FR",
        DECODO_PASSWORD="test_password",
        LOG_LEVEL="INFO",
    )


@pytest.fixture(scope="function")
def client(test_settings: Settings) -> TestClient:
    """TestClient FastAPI avec Settings + Logger override + cache clear."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()


@pytest.fixture
def mock_crawler_success():
    """Mock CrawlerService async avec HTML valide (partagé tests integration)."""
    from unittest.mock import AsyncMock

    from app.services.crawler_service import CrawlResult

    crawler = AsyncMock()
    crawler.crawl_google_flights.return_value = CrawlResult(
        success=True, html="<html>valid</html>", status_code=200
    )
    return crawler


@pytest.fixture
def client_with_mock_search(test_settings: Settings, mock_search_service):
    """TestClient avec mock SearchService."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger
    app.dependency_overrides[get_search_service] = lambda: mock_search_service

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()
