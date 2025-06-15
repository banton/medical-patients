"""
Prometheus metrics endpoint.
Part of EPIC-003: Production Scalability Improvements - Phase 2
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST

from src.core.metrics import get_metrics_collector

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def get_metrics():
    """
    Expose metrics in Prometheus format.

    This endpoint returns all collected metrics in the Prometheus
    text exposition format, suitable for scraping by Prometheus.

    Returns:
        Prometheus formatted metrics
    """
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()

    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
