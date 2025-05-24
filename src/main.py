"""
Main application entry point.
Creates and configures the FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from src.api.v1.routers import (
    configurations,
    generation,
    jobs,
    downloads,
    visualizations
)

# Get settings
settings = get_settings()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    # Create FastAPI instance
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc"
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
        return {
            "name": settings.APP_NAME,
            "version": settings.VERSION,
            "docs": "/docs"
        }
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
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
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )