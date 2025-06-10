"""
Custom error handlers for standardized API responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError


def get_error_name(status_code: int) -> str:
    """Get a standardized error name for HTTP status codes."""
    error_names = {
        status.HTTP_400_BAD_REQUEST: "Bad Request",
        status.HTTP_401_UNAUTHORIZED: "Unauthorized",
        status.HTTP_403_FORBIDDEN: "Forbidden",
        status.HTTP_404_NOT_FOUND: "Not Found",
        status.HTTP_422_UNPROCESSABLE_ENTITY: "Validation Error",
        status.HTTP_429_TOO_MANY_REQUESTS: "Too Many Requests",
        status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal Server Error",
    }
    return error_names.get(status_code, "Error")


def create_error_response(status_code: int, detail: str, request_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": get_error_name(status_code),
        "detail": detail,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id or str(uuid.uuid4()),
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized format."""
    error_response = create_error_response(exc.status_code, exc.detail)
    return JSONResponse(status_code=exc.status_code, content=error_response)


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with standardized format."""
    # Convert Pydantic v2 errors to simple format
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"])
        error_details.append(f"{loc}: {error['msg']}")

    detail = "; ".join(error_details)
    error_response = create_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI request validation errors with standardized format."""
    # Convert FastAPI validation errors to simple format
    error_details = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error["loc"] if x != "body")  # Remove 'body' from location
        msg = error["msg"]
        # Clean up common Pydantic v2 prefixes
        if msg.startswith("Value error, "):
            msg = msg[13:]  # Remove "Value error, " prefix
        error_details.append(f"{loc}: {msg}" if loc else msg)

    detail = "; ".join(error_details)
    error_response = create_error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=error_response)
