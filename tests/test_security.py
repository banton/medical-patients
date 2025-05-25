"""
Tests for security utilities.
"""

from unittest.mock import patch

from fastapi import HTTPException
import pytest

from src.core.security import verify_api_key


@pytest.mark.asyncio()
async def test_verify_api_key_valid():
    """Test API key verification with valid key."""
    with patch("src.core.security.settings") as mock_settings:
        mock_settings.API_KEY = "test-api-key"

        result = await verify_api_key("test-api-key")
        assert result == "test-api-key"


@pytest.mark.asyncio()
async def test_verify_api_key_invalid():
    """Test API key verification with invalid key."""
    with patch("src.core.security.settings") as mock_settings:
        mock_settings.API_KEY = "test-api-key"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-api-key")

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Invalid API Key"


@pytest.mark.asyncio()
async def test_verify_api_key_empty():
    """Test API key verification with empty key."""
    with patch("src.core.security.settings") as mock_settings:
        mock_settings.API_KEY = "test-api-key"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("")

        assert exc_info.value.status_code == 403
