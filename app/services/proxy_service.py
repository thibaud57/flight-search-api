"""Service de gestion et rotation de proxies residentiels Decodo."""

import itertools
import logging
import random

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
        self._current_index = 0

    def get_next_proxy(self) -> ProxyConfig:
        """Retourne prochain proxy selon rotation round-robin."""
        proxy = next(self._cycle)
        logger.info(
            "Proxy selected",
            extra={
                "proxy_host": proxy.host,
                "proxy_country": proxy.country,
                "current_index": self._current_index,
                "pool_size": self.pool_size,
            },
        )
        self._current_index = (self._current_index + 1) % len(self._proxy_pool)
        return proxy

    def get_random_proxy(self) -> ProxyConfig:
        """Retourne proxy aleatoire depuis pool."""
        return random.choice(self._proxy_pool)

    def reset_pool(self) -> None:
        """Reinitialise cycle rotation."""
        self._cycle = itertools.cycle(self._proxy_pool)
        self._current_index = 0

    @property
    def current_proxy_index(self) -> int:
        """Retourne index actuel dans cycle rotation."""
        return self._current_index

    @property
    def pool_size(self) -> int:
        """Retourne taille du pool de proxies."""
        return len(self._proxy_pool)
