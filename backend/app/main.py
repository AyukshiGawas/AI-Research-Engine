"""FastAPI application entrypoint for Enterprise AI Research Engine backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.core.rate_limit import limiter
from app.db.session import engine
from app.db.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager performing startup validation and cleanup."""
    configure_logging()
    logger.info("Starting Enterprise AI Research Engine backend...")

    # Startup security validation
    try:
        settings.validate_startup_security()
        logger.info("Startup environment security check passed.")
    except ValueError as err:
        logger.error(f"Startup Configuration Error: {err}")
        # In non-production/dev mode, log warning if validation fails
        if settings.APP_ENV == "production":
            raise err

    # Create tables automatically for dev environment if database connection is available
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database table initialization deferred (Alembic or DB offline): {e}")

    yield

    logger.info("Shutting down Enterprise AI Research Engine backend...")


app = FastAPI(
    title="Enterprise AI Research Engine API",
    description="Enterprise multi-agent research platform backend API.",
    version="0.2.0",
    lifespan=lifespan,
)

# Register Slowapi Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS Middleware
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
