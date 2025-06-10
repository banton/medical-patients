"""
Security utilities for the application.
Handles API key validation and other security concerns.
"""

from typing import Optional

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

from config import get_settings

# Initialize settings
settings = get_settings()

# API Key configuration
API_KEY_NAME = "X-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify the API key from the request header.

    Args:
        api_key: The API key from the request header

    Returns:
        The verified API key

    Raises:
        HTTPException: If the API key is missing or invalid
    """
    if api_key is None:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Missing API Key")
    if api_key == settings.API_KEY:
        return api_key
    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")
