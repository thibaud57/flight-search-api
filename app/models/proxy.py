"""Modele ProxyConfig pour configuration proxy Decodo."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProxyConfig(BaseModel):
    """Configuration d'un proxy residentiel Decodo."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(..., min_length=5)
    port: int
    username: str = Field(..., min_length=5)
    password: str = Field(..., min_length=8, max_length=100)
    country: str = Field(default="FR", min_length=2, max_length=2)

    @field_validator("port", mode="after")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valide port dans plage valide 1-65535."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("country", mode="before")
    @classmethod
    def normalize_country(cls, v: str) -> str:
        """Convertit country en uppercase."""
        if isinstance(v, str):
            return v.upper()
        return v

    def get_proxy_url(self) -> str:
        """Genere URL proxy complete format http://username:password@host:port."""
        return f"http://{self.username}:{self.password}@{self.host}:{self.port}"
