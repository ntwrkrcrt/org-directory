from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from api import buildings_router, organizations_router
from api.health import health_check
from core.cache.redis import init_redis, shutdown_redis
from middleware import (
    configure_cors_middleware,
    configure_exception_middleware,
    configure_monitoring_middleware,
)
from models.database import init_db, shutdown_db


async def _startup_db() -> None:
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    await _startup_db()
    await init_redis()

    yield

    logger.info("Shutting down application...")

    await shutdown_db()
    await shutdown_redis()


def _configure_middleware(app: FastAPI) -> None:
    configure_monitoring_middleware(app)
    configure_cors_middleware(app)
    configure_exception_middleware(app)


def _register_routes(app: FastAPI) -> None:
    app.add_api_route("/health", health_check, methods=["GET"])
    app.include_router(organizations_router)
    app.include_router(buildings_router)


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=lifespan,
        title="Organization Catalog API",
        description="",
        version="1.0.0",
    )

    _configure_middleware(app)
    _register_routes(app)

    return app


app = create_app()
