from fastapi import FastAPI

app = FastAPI(title="flight-search-api", version="0.3.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint pour monitoring."""
    return {"status": "ok"}
