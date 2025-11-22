from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield

app = FastAPI(title="flight-search-api", version="0.5.0", lifespan=lifespan)

app.include_router(router)
