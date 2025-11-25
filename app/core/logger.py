"""Configure logger avec format JSON structuré."""

import logging
import sys
from functools import lru_cache
from typing import ClassVar

from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]


class SensitiveDataFilter(logging.Filter):
    """Filtre pour masquer données sensibles dans logs."""

    SENSITIVE_KEYS: ClassVar[list[str]] = ["password", "api_key", "secret", "token"]

    def filter(self, record: logging.LogRecord) -> bool:
        """Masque champs sensibles dans record.args et __dict__."""
        for key in self.SENSITIVE_KEYS:
            if hasattr(record, key):
                setattr(record, key, "***")
        return True


def setup_logger(log_level: str) -> logging.Logger:
    """Configure logger avec format JSON structuré."""
    app_logger = logging.getLogger("app")
    app_logger.setLevel(log_level)
    app_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())
    app_logger.addHandler(handler)

    return app_logger


@lru_cache
def get_logger() -> logging.Logger:
    """Retourne instance Logger cached configurée avec Settings."""
    # Import local pour éviter circular import (config → logger → config)
    from app.core.config import get_settings

    settings = get_settings()
    return setup_logger(settings.LOG_LEVEL)
