import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import router
from app.core import get_logger
from app.exceptions import CaptchaDetectedError, NetworkError, SessionCaptureError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_logger()
    yield


app = FastAPI(title="flight-search-api", version="0.7.0", lifespan=lifespan)


@app.exception_handler(CaptchaDetectedError)
async def captcha_exception_handler(
    request: Request, exc: CaptchaDetectedError
) -> JSONResponse:
    """Gere erreurs captcha avec reponse structuree."""
    logger.error(
        "Captcha detected",
        extra={
            "url": exc.url,
            "captcha_type": exc.captcha_type,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content={
            "detail": "Service temporarily unavailable due to captcha",
            "captcha_type": exc.captcha_type,
        },
    )


@app.exception_handler(NetworkError)
async def network_exception_handler(
    request: Request, exc: NetworkError
) -> JSONResponse:
    """Gere erreurs reseau avec reponse structuree."""
    logger.error(
        "Network error",
        extra={
            "url": exc.url,
            "status_code": exc.status_code,
            "attempts": exc.attempts,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=HTTPStatus.BAD_GATEWAY,
        content={
            "detail": "Failed to fetch flight data from provider",
            "attempts": exc.attempts,
        },
    )


@app.exception_handler(SessionCaptureError)
async def session_exception_handler(
    request: Request, exc: SessionCaptureError
) -> JSONResponse:
    """Gere erreurs session avec reponse structuree."""
    logger.error(
        "Session capture failed",
        extra={
            "provider": exc.provider,
            "reason": exc.reason,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        content={
            "detail": f"Failed to establish session with {exc.provider}",
            "reason": exc.reason,
        },
    )


app.include_router(router)
