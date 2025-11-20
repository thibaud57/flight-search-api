"""Exports core configuration."""

from app.core.config import Settings
from app.core.logger import setup_logger

settings = Settings()  # type: ignore[call-arg]
logger = setup_logger(settings.LOG_LEVEL)

__all__ = ["Settings", "logger", "settings", "setup_logger"]
