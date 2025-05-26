"""
Security utilities for the application.
Handles API key validation and other security concerns.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from config import get_settings

# Initialize settings
settings = get_settings()

# API Key configuration
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the request header.

    Args:
        api_key: The API key from the request header

    Returns:
        The verified API key

    Raises:
        HTTPException: If the API key is invalid
    """
    if api_key == settings.API_KEY:
        return api_key
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
