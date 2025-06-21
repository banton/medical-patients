"""
Shared pytest configuration and fixtures
"""

import os
from typing import Union

from fastapi.testclient import TestClient
import httpx
import pytest


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption("--base-url", action="store", default="http://localhost:8000", help="Base URL for the API")
    parser.addoption("--use-running-server", action="store_true", help="Use already running server instead of TestClient")


@pytest.fixture()
def base_url(request):
    """Get base URL from command line option"""
    return request.config.getoption("--base-url")


@pytest.fixture()
def api_headers():
    """Common API headers for tests"""
    return {"X-API-Key": "DEMO_MILMED_2025_50_PATIENTS", "Content-Type": "application/json"}


class HTTPClient:
    """Wrapper to make httpx client compatible with TestClient interface"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url)
    
    def get(self, url: str, **kwargs):
        return self.client.get(url, **kwargs)
    
    def post(self, url: str, **kwargs):
        return self.client.post(url, **kwargs)
    
    def put(self, url: str, **kwargs):
        return self.client.put(url, **kwargs)
    
    def patch(self, url: str, **kwargs):
        return self.client.patch(url, **kwargs)
    
    def delete(self, url: str, **kwargs):
        return self.client.delete(url, **kwargs)
    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


@pytest.fixture()
def client(request) -> Union[TestClient, HTTPClient]:
    """Test client for FastAPI app - uses HTTP client if server is running"""
    # Only use HTTP client if explicitly requested (for integration tests with running server)
    if request.config.getoption("--use-running-server"):
        base_url = request.config.getoption("--base-url")
        client = HTTPClient(base_url)
        yield client
        client.close()
    else:
        # Otherwise use TestClient which runs the app in-process
        from src.main import app
        from src.infrastructure.database_pool import close_pool
        
        # In CI environment, don't close the pool as it affects the running server
        if not os.getenv("CI"):
            # Reset the pool before creating test client
            close_pool()
        
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture()
def test_database_url():
    """Provide test database URL for tests that need it"""
    # Use in-memory SQLite for tests or TEST_DATABASE_URL env var
    return os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
