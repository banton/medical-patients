"""
Main application entry point.
Creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings
from src.api.v1.middleware.metrics import MetricsMiddleware
from src.api.v1.routers import (
    configurations,
    downloads,
    generation,
    health,
    jobs,
    metrics,
    presets,
    streaming,
    visualizations,
)
from src.core.cache import close_cache, get_cache_service, initialize_cache
from src.core.error_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
    validation_exception_handler,
)
from src.domain.repositories.api_key_repository import APIKeyRepository
from src.infrastructure.database_pool import close_pool

# Get settings
settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO if not settings.DEBUG else logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up application...")

    # Initialize cache if enabled
    if settings.CACHE_ENABLED:
        try:
            await initialize_cache(settings.REDIS_URL, settings.CACHE_TTL)
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis cache: %s", e)
            logger.warning("Application will continue without caching")
            # Disable caching for this session to prevent further errors
            settings.CACHE_ENABLED = False

    # Ensure demo API key exists
    try:
        # We need to create a sync context for the database operation
        engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))
        session_local = sessionmaker(bind=engine)

        with session_local() as db:
            repo = APIKeyRepository(db)
            demo_key = repo.create_demo_key_if_not_exists()
            logger.info(f"Demo API key ensured: {demo_key.name}")

        engine.dispose()
    except Exception as e:
        logger.error(f"Failed to ensure demo API key: {e}")
        # Non-critical error - application can continue

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Close database connection pool
    try:
        close_pool()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database pool: {e}")

    # Close cache connection
    if settings.CACHE_ENABLED:
        await close_cache()
        logger.info("Redis cache connection closed")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    # Create FastAPI instance
    app = FastAPI(
        title=settings.APP_NAME, version=settings.VERSION, docs_url="/docs", redoc_url="/redoc", lifespan=lifespan
    )

    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add custom error handlers for standardized responses
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add metrics middleware (EPIC-003)
    app.add_middleware(MetricsMiddleware)

    # Include v1 API routers with consistent prefix
    v1_prefix = "/api/v1"

    # Configuration routers (already use v1 prefix)
    app.include_router(configurations.router, prefix=v1_prefix)
    app.include_router(configurations.reference_router, prefix=v1_prefix)
    app.include_router(configurations.public_router, prefix=v1_prefix)

    # New standardized v1 routers
    app.include_router(generation.router, prefix=v1_prefix)
    app.include_router(jobs.router, prefix=v1_prefix)
    app.include_router(downloads.router, prefix=v1_prefix)
    app.include_router(visualizations.router, prefix=v1_prefix)
    app.include_router(presets.router, prefix=v1_prefix)
    # Timeline router temporarily disabled - requires additional JobService methods
    # app.include_router(timeline.router, prefix=v1_prefix)

    # Health monitoring routers (EPIC-003)
    app.include_router(health.router)

    # Metrics endpoint (EPIC-003)
    app.include_router(metrics.router)

    # Streaming endpoint (EPIC-003 Phase 3)
    app.include_router(streaming.router, prefix=v1_prefix)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Root endpoint - redirect to UI
    @app.get("/")
    async def root():
        """Root endpoint - redirect to main UI."""
        return RedirectResponse(url="/static/index.html")

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        health_status = {"status": "healthy", "services": {}}

        # Check cache health if enabled
        if settings.CACHE_ENABLED:
            cache_service = get_cache_service()
            if cache_service:
                health_status["services"]["redis"] = await cache_service.health_check()
            else:
                health_status["services"]["redis"] = False

        return health_status

    # Ready check endpoint
    @app.get("/ready")
    async def ready_check():
        """Readiness check endpoint."""
        # Could check database connection, etc.
        return {"status": "ready"}

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
