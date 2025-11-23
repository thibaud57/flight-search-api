import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.core.logger import get_logger

    get_logger()
    yield


app = FastAPI(title="flight-search-api", version="0.6.0", lifespan=lifespan)

app.include_router(router)
