"""Service de gestion et rotation de proxies residentiels Decodo."""

import itertools
import logging

from app.models.proxy import ProxyConfig

logger = logging.getLogger(__name__)


class ProxyService:
    """Service de gestion et rotation de proxies residentiels Decodo."""

    def __init__(self, proxy_pool: list[ProxyConfig]) -> None:
        """Initialise service avec pool de proxies."""
        if not proxy_pool:
            raise ValueError("Proxy pool cannot be empty")
        self._proxy_pool = proxy_pool
        self._cycle = itertools.cycle(proxy_pool)

    def get_next_proxy(self) -> ProxyConfig:
        """Retourne prochain proxy selon rotation round-robin."""
        proxy = next(self._cycle)
        logger.debug(
            "Proxy rotated",
            extra={
                "proxy_host": proxy.host,
                "proxy_country": proxy.country,
            },
        )
        return proxy
