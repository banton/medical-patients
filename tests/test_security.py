"""
Tests for security utilities with enhanced API key system.
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
import pytest
from sqlalchemy.orm import Session

from src.core.security_enhanced import DEMO_API_KEY, verify_api_key, verify_api_key_context
from src.domain.models.api_key import APIKey


@pytest.mark.asyncio()
async def test_verify_api_key_with_demo_key():
    """Test API key verification with demo key."""
    # Create a mock APIKey object
    mock_demo_key = APIKey(
        key=DEMO_API_KEY,
        name="Demo API Key",
        is_active=True,
        is_demo=True,
        max_patients_per_request=50,
        max_requests_per_day=100
    )

    # Mock database session and repository
    mock_db = Mock(spec=Session)

    with patch("src.core.security_enhanced.APIKeyRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_key.return_value = mock_demo_key

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

    with patch("src.core.security_enhanced.APIKeyRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_active_key.return_value = None
        mock_repo.get_by_key.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(api_key="invalid-key-12345", db=mock_db)

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio()
async def test_verify_api_key_context_with_demo_key():
    """Test API key context verification with demo key."""
    # Create a mock APIKey object
    mock_demo_key = APIKey(
        key=DEMO_API_KEY,
        name="Demo API Key",
        is_active=True,
        is_demo=True,
        max_patients_per_request=50,
        max_requests_per_day=100,
        daily_requests=0,
        total_requests=0
    )

    # Mock database session and repository
    mock_db = Mock(spec=Session)

    with patch("src.core.security_enhanced.APIKeyRepository") as MockRepo:
        with patch("src.core.security_enhanced.cache_api_key_limits", new_callable=AsyncMock):
            mock_repo = MockRepo.return_value
            mock_repo.get_by_key.return_value = mock_demo_key

            context = await verify_api_key_context(api_key=DEMO_API_KEY, db=mock_db)
            assert context.api_key.key == DEMO_API_KEY
            assert context.is_demo is True


@pytest.mark.asyncio()
async def test_verify_api_key_legacy_key():
    """Test API key verification with legacy key."""
    # Mock database session
    mock_db = Mock(spec=Session)

    with patch("src.core.security_enhanced.LEGACY_API_KEY", "test-legacy-key"):
        with patch("src.core.security_enhanced.cache_api_key_limits", new_callable=AsyncMock):
            result = await verify_api_key(api_key="test-legacy-key", db=mock_db)
            assert result == "test-legacy-key"
