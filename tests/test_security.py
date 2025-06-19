"""
Tests for security utilities with enhanced API key system.
"""

from unittest.mock import MagicMock, Mock

from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session

from src.core.security_enhanced import verify_api_key, DEMO_API_KEY
from src.domain.models.api_key import APIKey


@pytest.mark.asyncio()
async def test_verify_api_key_with_demo_key():
    """Test API key verification with demo key."""
    # Mock database session
    mock_db = Mock(spec=Session)
    
    # The demo key should work even without database lookup
    result = await verify_api_key(api_key=DEMO_API_KEY, db=mock_db)
    assert result == DEMO_API_KEY


@pytest.mark.asyncio()
async def test_verify_api_key_missing():
    """Test API key verification with missing key."""
    # Mock database session
    mock_db = Mock(spec=Session)
    
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(api_key=None, db=mock_db)
    
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing API Key"


@pytest.mark.asyncio()
async def test_verify_api_key_invalid():
    """Test API key verification with invalid key."""
    # Mock database session
    mock_db = Mock(spec=Session)
    
    # Mock repository to return None for invalid key
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(api_key="invalid-key-12345", db=mock_db)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio()
async def test_verify_api_key_with_database_error():
    """Test API key verification when database is unavailable."""
    # Mock database session that raises an error
    mock_db = Mock(spec=Session)
    mock_db.query.side_effect = Exception("Database connection failed")
    
    # Even with database error, demo key should work
    result = await verify_api_key(api_key=DEMO_API_KEY, db=mock_db)
    assert result == DEMO_API_KEY