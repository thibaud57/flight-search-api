"""Configure logger avec format JSON structuré."""

import logging
import sys
from typing import ClassVar

from pythonjsonlogger import jsonlogger  # type: ignore


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
    logger = logging.getLogger("flight-search-api")
    logger.setLevel(log_level)
    logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger enfant du logger principal."""
    return logging.getLogger(f"flight-search-api.{name}")
