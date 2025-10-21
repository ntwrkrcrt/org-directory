import time

from fastapi import FastAPI
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request


class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        start_time = time.time()

        logger.debug(f"Request started: {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            if process_time > 5:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {process_time:.2f}s"
                )
            elif process_time > 30:
                logger.error(
                    f"Very slow request: {request.method} {request.url.path} "
                    f"took {process_time:.2f}s - consider optimizing"
                )

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"after {process_time:.2f}s - Error: {e}"
            )
            raise


def configure_monitoring_middleware(app: FastAPI) -> None:
    app.add_middleware(MonitoringMiddleware)
