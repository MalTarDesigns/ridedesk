from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine

from ridedesk.api import v1
from ridedesk.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API. Run with `uvicorn --factory ridedesk.main:create_app`."""
    settings = settings or get_settings()
    # A short connect timeout keeps /v1/health answering 503 instead of hanging.
    engine = create_engine(
        settings.database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3}
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(
        title="RideDesk API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/v1/docs",
        openapi_url="/v1/openapi.json",
    )
    app.state.engine = engine
    app.include_router(v1.router)
    return app
