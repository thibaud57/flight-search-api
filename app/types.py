"""Type aliases centralisés pour le projet."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from tenacity import RetryCallState
    from tenacity.retry import RetryBaseT
    from tenacity.stop import StopBaseT
    from tenacity.wait import WaitBaseT

    from app.models.request import DateCombination
    from app.services.crawler_service import CrawlResult


type CrawlResultTuple = tuple[DateCombination, CrawlResult | None]


class TenacityRetryConfig(TypedDict):
    """Config retry type-safe pour @retry(**config) - requis par mypy strict."""

    stop: StopBaseT
    wait: WaitBaseT
    retry: RetryBaseT
    before_sleep: Callable[[RetryCallState], None]
    reraise: bool
