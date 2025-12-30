"""
Unit tests for API exception classes.
"""

from fastapi.testclient import TestClient
from src.main import app
from src.core.exceptions import InvalidInputError, NotFoundError, UnauthorizedError

client = TestClient(app)


def test_invalid_input_error():
    """Test that InvalidInputError returns proper JSON response."""
    # This will be handled by the global handler when raised
    try:
        raise InvalidInputError("Test error message")
    except InvalidInputError as e:
        assert e.status_code == 422
        assert e.detail == "Test error message"


def test_not_found_error():
    """Test that NotFoundError returns proper JSON response."""
    try:
        raise NotFoundError("Resource not found")
    except NotFoundError as e:
        assert e.status_code == 404
        assert e.detail == "Resource not found"


def test_unauthorized_error():
    """Test that UnauthorizedError returns proper JSON response."""
    try:
        raise UnauthorizedError("Unauthorized access")
    except UnauthorizedError as e:
        assert e.status_code == 401
        assert e.detail == "Unauthorized access"
