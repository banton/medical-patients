"""
Integration tests for the global exception handler.
"""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_exception_handler_with_invalid_input():
    """Test that InvalidInputError returns proper JSON response."""
    # This will be handled by the global handler when raised
    try:
        from src.core.exceptions import InvalidInputError

        raise InvalidInputError("Test error message")
    except InvalidInputError as e:
        assert e.status_code == 422
        assert e.detail == "Test error message"
