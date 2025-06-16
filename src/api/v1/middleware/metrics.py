"""
Metrics collection middleware for API requests.
Part of EPIC-003: Production Scalability Improvements - Phase 2
"""

import time
from typing import Callable, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.metrics import get_metrics_collector, request_count, request_duration


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect request metrics."""

    def __init__(self, app):
        super().__init__(app)
        self.metrics = get_metrics_collector()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and collect metrics.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint

        Returns:
            The response
        """
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Extract method and path
        method = request.method
        path = request.url.path

        # Normalize path for metrics (replace IDs with placeholders)
        # This prevents metric explosion from unique IDs
        normalized_path = self._normalize_path(path)

        # Initialize response status
        status_code = 500

        try:
            # Process request
            response = await call_next(request)
            status_code = response.status_code

            # Add response time header
            response.headers["X-Response-Time"] = f"{(time.time() - start_time) * 1000:.2f}ms"

            return response

        except Exception as e:
            # Log error and re-raise
            if hasattr(e, "status_code"):
                status_code = e.status_code
            raise

        finally:
            # Record metrics
            duration = time.time() - start_time
            request_count.labels(method=method, endpoint=normalized_path, status=str(status_code)).inc()
            request_duration.labels(endpoint=normalized_path, method=method).observe(duration)

    def _normalize_path(self, path: str) -> str:
        """
        Normalize path by replacing dynamic segments with placeholders.

        Args:
            path: The original path

        Returns:
            Normalized path
        """
        # Split path into segments
        segments = path.split("/")
        normalized_segments: List[str] = []

        for i, segment in enumerate(segments):
            # Skip empty segments
            if not segment:
                normalized_segments.append(segment)
                continue

            # Check if segment looks like an ID (UUID, numeric, or job ID)
            if self._is_id_segment(segment):
                # Use placeholder based on previous segment
                if i > 0:
                    prev_segment = segments[i - 1]
                    if prev_segment in ["jobs", "configurations", "downloads"]:
                        normalized_segments.append(f":{prev_segment[:-1]}_id")
                    else:
                        normalized_segments.append(":id")
                else:
                    normalized_segments.append(":id")
            else:
                normalized_segments.append(segment)

        return "/".join(normalized_segments)

    def _is_id_segment(self, segment: str) -> bool:
        """
        Check if a path segment looks like an ID.

        Args:
            segment: Path segment to check

        Returns:
            True if segment appears to be an ID
        """
        # Check if it's a UUID (with or without hyphens)
        if len(segment) in [32, 36] and all(c in "0123456789abcdef-" for c in segment.lower()):
            return True

        # Check if it's numeric
        if segment.isdigit():
            return True

        # Check if it's a job ID format (e.g., job_123456)
        if segment.startswith("job_") and segment[4:].replace("_", "").isdigit():
            return True

        # Check for generic ID pattern (contains letters, numbers, and hyphens)
        # but must have at least one number
        return "-" in segment and any(c.isdigit() for c in segment)
