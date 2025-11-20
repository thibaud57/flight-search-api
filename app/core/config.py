"""Configuration application chargée depuis variables d'environnement."""

import logging
from functools import lru_cache
from typing import Literal, Self

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration application chargée depuis variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    DECODO_USERNAME: str
    DECODO_PASSWORD: str
    DECODO_PROXY_HOST: str = "pr.decodo.com:8080"
    PROXY_ROTATION_ENABLED: bool = True
    CAPTCHA_DETECTION_ENABLED: bool = True

    @field_validator("DECODO_USERNAME", mode="after")
    @classmethod
    def validate_username_format(cls, v: str) -> str:
        """Valide format DECODO_USERNAME customer-{key}-country-{code}."""
        if "customer-" not in v or "-country-" not in v:
            raise ValueError(
                "DECODO_USERNAME must follow format: customer-{key}-country-{code}"
            )
        return v

    @field_validator("DECODO_PROXY_HOST", mode="after")
    @classmethod
    def validate_proxy_host_format(cls, v: str) -> str:
        """Valide format DECODO_PROXY_HOST host:port."""
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("DECODO_PROXY_HOST must follow format: host:port")
        return v

    @model_validator(mode="after")
    def warn_risky_config(self) -> Self:
        """Log warning si configuration à risque (rotation+captcha disabled)."""
        if not self.PROXY_ROTATION_ENABLED and not self.CAPTCHA_DETECTION_ENABLED:
            logger.warning(
                "Risky configuration: Both proxy rotation and captcha detection are disabled"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Retourne instance Settings cached (singleton via lru_cache)."""
    return Settings()  # type: ignore[call-arg]
