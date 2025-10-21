import traceback

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.requests import Request


def configure_exception_middleware(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            f"Unhandled exception: {exc} | "
            f"Request: {request.method} {request.url} | "
            f"Traceback: {traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )
