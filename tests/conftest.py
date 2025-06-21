"""
Shared pytest configuration and fixtures
"""

import os

from fastapi.testclient import TestClient
import pytest


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption("--base-url", action="store", default="http://localhost:8000", help="Base URL for the API")


@pytest.fixture()
def base_url(request):
    """Get base URL from command line option"""
    return request.config.getoption("--base-url")


@pytest.fixture()
def api_headers():
    """Common API headers for tests"""
    return {"X-API-Key": "DEMO_MILMED_2025_50_PATIENTS", "Content-Type": "application/json"}


@pytest.fixture()
def client():
    """Test client for FastAPI app"""
    from src.main import app
    
    # Close any existing database pool to avoid conflicts
    from src.infrastructure.database_pool import close_pool
    close_pool()
    
    # Create a new test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up after test
    close_pool()


@pytest.fixture()
def test_database_url():
    """Provide test database URL for tests that need it"""
    # Use in-memory SQLite for tests or TEST_DATABASE_URL env var
    return os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
