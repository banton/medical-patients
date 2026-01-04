"""
Health check and monitoring endpoints.
Part of EPIC-003: Production Scalability Improvements
"""

from datetime import datetime
import os
import platform
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import psutil

from src.core.job_resource_manager import get_resource_manager
from src.infrastructure.database_pool import get_pool

router = APIRouter(prefix="/api/v1/health", tags=["health"])


def check_disk_space() -> Dict[str, Any]:
    """Check available disk space."""
    try:
        disk_usage = psutil.disk_usage("/")
        return {
            "status": "healthy" if disk_usage.percent < 90 else "warning",
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round(disk_usage.used / (1024**3), 2),
            "free_gb": round(disk_usage.free / (1024**3), 2),
            "percent_used": disk_usage.percent,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def check_memory_usage() -> Dict[str, Any]:
    """Check system memory usage."""
    try:
        memory = psutil.virtual_memory()
        return {
            "status": "healthy" if memory.percent < 85 else "warning",
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "percent_used": memory.percent,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


def check_database_health() -> Dict[str, Any]:
    """Check database connectivity and pool status."""
    try:
        pool = get_pool()

        # Test database connection
        with pool.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]

        # Get pool status
        pool_status = pool.get_pool_status()

        return {
            "status": "healthy",
            "version": version,
            "pool": pool_status["pool"],
            "metrics": pool_status["metrics"],
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def check_api_health() -> Dict[str, Any]:
    """Check API service health."""
    return {
        "status": "healthy",
        "version": os.getenv("APP_VERSION", "2.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": platform.python_version(),
    }


async def check_job_worker_health() -> Dict[str, Any]:
    """Check job worker health and resource usage."""
    try:
        resource_manager = get_resource_manager()
        active_jobs = resource_manager.get_active_jobs()

        # Calculate total resource usage
        total_memory_mb = sum(job.get("memory_mb", 0) for job in active_jobs.values())
        total_cpu_seconds = sum(job.get("cpu_seconds", 0) for job in active_jobs.values())

        # Check if we can accept new jobs
        can_accept_jobs = resource_manager.can_start_new_job()

        return {
            "status": "healthy" if can_accept_jobs else "warning",
            "active_jobs": len(active_jobs),
            "max_concurrent_jobs": resource_manager.max_concurrent_jobs,
            "can_accept_jobs": can_accept_jobs,
            "resources": {
                "total_memory_mb": round(total_memory_mb, 2),
                "total_cpu_seconds": round(total_cpu_seconds, 2),
                "max_memory_mb": resource_manager.max_memory_mb,
                "max_cpu_seconds": resource_manager.max_cpu_seconds,
            },
            "jobs": {
                job_id: {
                    "runtime_seconds": round(job["runtime_seconds"], 2),
                    "memory_mb": round(job["memory_mb"], 2),
                    "cpu_seconds": round(job["cpu_seconds"], 2),
                }
                for job_id, job in active_jobs.items()
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@router.get("")
async def health_check():
    """
    Comprehensive system health check.

    Returns detailed health status of all system components.
    """
    checks = {
        "api": check_api_health(),
        "database": check_database_health(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage(),
        "job_worker": await check_job_worker_health(),
    }

    # Determine overall status
    statuses = [check.get("status", "unknown") for check in checks.values()]
    if all(status == "healthy" for status in statuses):
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in statuses):
        overall_status = "unhealthy"
    elif any(status == "error" for status in statuses):
        overall_status = "error"
    else:
        overall_status = "warning"

    response = {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks,
    }

    # Return appropriate status code
    status_code = 200 if overall_status in ["healthy", "warning"] else 503

    return JSONResponse(content=response, status_code=status_code)


@router.get("/live")
async def liveness_probe():
    """
    Simple liveness check for load balancers.

    Returns 200 if the service is alive.

    NOTE: This endpoint intentionally does NOT query the database.
    This allows serverless PostgreSQL (Neon) to auto-suspend when idle.
    Use /ready for database connectivity checks.
    """
    return {"status": "alive"}


@router.get("/ready")
async def readiness_probe():
    """
    Readiness check - can the service handle requests?

    Returns 200 if ready, 503 if not ready.
    """
    try:
        # Quick database check
        pool = get_pool()
        with pool.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()

        return {"status": "ready"}

    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "not_ready", "error": str(e)})


@router.get("/database")
async def database_health():
    """
    Check database connectivity and pool status.

    Returns detailed database and connection pool metrics.
    """
    try:
        pool = get_pool()

        # Test query
        with pool.cursor() as cur:
            cur.execute("SELECT version(), current_database(), current_user")
            result = cur.fetchone()
            db_info = {
                "version": result[0],
                "database": result[1],
                "user": result[2],
            }

        # Get pool status
        pool_status = pool.get_pool_status()

        return {
            "status": "healthy",
            "database": db_info,
            "pool": pool_status["pool"],
            "metrics": pool_status["metrics"],
            "config": pool_status["config"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
            },
        )


@router.get("/metrics")
async def get_metrics():
    """
    Get application metrics.

    Returns metrics in a format suitable for monitoring systems.
    """
    try:
        pool = get_pool()
        pool_metrics = pool.get_pool_status()["metrics"]

        # Format metrics for monitoring
        return {
            "database": {
                "connections_created_total": pool_metrics["connections"]["created"],
                "connections_active": pool_metrics["connections"]["active"],
                "queries_total": pool_metrics["queries"]["total"],
                "queries_slow_total": pool_metrics["queries"]["slow_count"],
                "query_duration_avg_ms": pool_metrics["queries"]["avg_time_ms"],
                "checkout_duration_avg_ms": pool_metrics["checkouts"]["avg_time_ms"],
                "checkout_failures_total": pool_metrics["checkouts"]["failed"],
            },
            "system": {
                "memory_percent": psutil.virtual_memory().percent,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "disk_percent": psutil.disk_usage("/").percent,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})
