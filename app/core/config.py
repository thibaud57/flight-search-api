"""Configuration application chargee depuis variables d'environnement."""

import logging
from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.proxy import ProxyConfig

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Configuration application chargee depuis variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    DECODO_USERNAME: str = Field(..., min_length=5)
    DECODO_PASSWORD: SecretStr
    DECODO_PROXY_HOST: str = "fr.decodo.com:40000"
    DECODO_PROXY_ENABLED: bool = True
    PROXY_ROTATION_ENABLED: bool = True
    CAPTCHA_DETECTION_ENABLED: bool = True

    proxy_config: ProxyConfig | None = None

    @field_validator("DECODO_PROXY_HOST", mode="after")
    @classmethod
    def validate_proxy_host_format(cls, v: str) -> str:
        """Valide format DECODO_PROXY_HOST host:port."""
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError("DECODO_PROXY_HOST must follow format: host:port")
        return v

    @model_validator(mode="after")
    def build_proxy_config(self) -> Self:
        """Genere ProxyConfig depuis variables env si proxies actives."""
        if not self.PROXY_ROTATION_ENABLED and not self.CAPTCHA_DETECTION_ENABLED:
            logger.warning(
                "Risky configuration: Both proxy rotation and captcha detection are disabled"
            )

        if self.DECODO_PROXY_ENABLED:
            host_parts = self.DECODO_PROXY_HOST.split(":")
            self.proxy_config = ProxyConfig(
                host=host_parts[0],
                port=int(host_parts[1]),
                username=self.DECODO_USERNAME,
                password=self.DECODO_PASSWORD.get_secret_value(),
                country="FR",
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Retourne instance Settings cached (singleton via lru_cache)."""
    return Settings()  # type: ignore[call-arg]
