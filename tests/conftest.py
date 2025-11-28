"""Configuration pytest globale - Config de base uniquement."""

import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_search_service
from app.core import Settings, get_logger, get_settings, setup_logger
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
        PROXY_USERNAME="customer-test-country-FR",
        PROXY_PASSWORD="test_password",
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


@pytest.fixture
def client_with_network_error(test_settings: Settings, mock_search_service_network_error):
    """TestClient avec SearchService qui lève NetworkError."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger
    app.dependency_overrides[get_search_service] = (
        lambda: mock_search_service_network_error
    )

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()


@pytest.fixture
def client_with_session_error(test_settings: Settings, mock_search_service_session_error):
    """TestClient avec SearchService qui lève SessionCaptureError."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger
    app.dependency_overrides[get_search_service] = (
        lambda: mock_search_service_session_error
    )

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()


@pytest.fixture
def client_with_captcha_error(test_settings: Settings, mock_search_service_captcha_error):
    """TestClient avec SearchService qui lève CaptchaDetectedError."""
    get_settings.cache_clear()
    get_logger.cache_clear()

    test_logger = setup_logger(test_settings.LOG_LEVEL)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_logger] = lambda: test_logger
    app.dependency_overrides[get_search_service] = (
        lambda: mock_search_service_captcha_error
    )

    yield TestClient(app)

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_logger.cache_clear()
