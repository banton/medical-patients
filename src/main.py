"""
Main application entry point.
Creates and configures the FastAPI application.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import get_settings
from src.api.v1.routers import configurations, downloads, generation, jobs, visualizations
from src.core.cache import close_cache, get_cache_service, initialize_cache

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
            logger.error(f"Failed to initialize Redis cache: {e}")
            logger.warning("Application will continue without caching")

    yield

    # Shutdown
    logger.info("Shutting down application...")

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

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    app.include_router(configurations.router)
    app.include_router(configurations.reference_router)
    app.include_router(generation.router)
    app.include_router(jobs.router)
    app.include_router(downloads.router)
    app.include_router(visualizations.router)

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"name": settings.APP_NAME, "version": settings.VERSION, "docs": "/docs"}

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

    # New UI endpoint
    @app.get("/ui")
    async def new_ui():
        """Redirect to new UI."""
        return RedirectResponse(url="/static/new-ui/index.html")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
