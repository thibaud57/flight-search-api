from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="flight-search-api", version="0.4.0")

app.include_router(router)
