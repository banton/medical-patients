"""
Prometheus metrics collection for monitoring and observability.
Part of EPIC-003: Production Scalability Improvements - Phase 2
"""

from contextlib import contextmanager
import time
from typing import Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry

# Create a custom registry to avoid conflicts
registry = CollectorRegistry()

# Request metrics
request_count = Counter(
    "api_requests_total", "Total number of API requests", ["method", "endpoint", "status"], registry=registry
)

request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint", "method"],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Database metrics
db_connections_active = Gauge("db_connections_active", "Number of active database connections", registry=registry)

db_connections_total = Counter(
    "db_connections_total", "Total number of database connections created", registry=registry
)

db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

db_query_errors = Counter(
    "db_query_errors_total", "Total number of database query errors", ["error_type"], registry=registry
)

# Patient generation metrics
patients_generated = Counter(
    "patients_generated_total", "Total number of patients generated", ["format"], registry=registry
)

generation_duration = Histogram(
    "patient_generation_duration_seconds",
    "Patient generation duration in seconds",
    ["format"],
    registry=registry,
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

generation_errors = Counter(
    "patient_generation_errors_total", "Total number of patient generation errors", ["error_type"], registry=registry
)

# Job metrics
job_queue_size = Gauge("job_queue_size", "Number of jobs in the queue", ["status"], registry=registry)

job_execution_time = Histogram(
    "job_execution_seconds",
    "Job execution time in seconds",
    ["job_type"],
    registry=registry,
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0),
)

job_status_changes = Counter(
    "job_status_changes_total", "Total number of job status changes", ["from_status", "to_status"], registry=registry
)

# System resource metrics
memory_usage_bytes = Gauge(
    "process_memory_usage_bytes",
    "Process memory usage in bytes",
    ["type"],  # rss, vms, available
    registry=registry,
)

cpu_usage_percent = Gauge("process_cpu_usage_percent", "Process CPU usage percentage", registry=registry)

# Cache metrics
cache_hits = Counter("cache_hits_total", "Total number of cache hits", ["cache_type"], registry=registry)

cache_misses = Counter("cache_misses_total", "Total number of cache misses", ["cache_type"], registry=registry)

cache_evictions = Counter(
    "cache_evictions_total", "Total number of cache evictions", ["cache_type", "reason"], registry=registry
)


class MetricsCollector:
    """Central metrics collector for the application."""

    def __init__(self):
        """Initialize the metrics collector."""
        self.start_time = time.time()

    @contextmanager
    def track_request(self, method: str, endpoint: str):
        """
        Context manager to track request metrics.

        Args:
            method: HTTP method
            endpoint: API endpoint path
        """
        start_time = time.time()
        status = "500"  # Default to error

        try:
            yield
            status = "200"  # Success
        except Exception as e:
            # Determine status based on exception type
            if hasattr(e, "status_code"):
                status = str(getattr(e, "status_code", 500))
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            request_count.labels(method=method, endpoint=endpoint, status=status).inc()
            request_duration.labels(endpoint=endpoint, method=method).observe(duration)

    @contextmanager
    def track_db_query(self):
        """Context manager to track database query metrics."""
        start_time = time.time()

        try:
            yield
        except Exception as e:
            # Record error
            error_type = type(e).__name__
            db_query_errors.labels(error_type=error_type).inc()
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            db_query_duration.observe(duration)

    @contextmanager
    def track_generation(self, format_type: str, patient_count: int):
        """
        Context manager to track patient generation metrics.

        Args:
            format_type: Output format (json, xml, fhir)
            patient_count: Number of patients to generate
        """
        start_time = time.time()

        try:
            yield
            # Record successful generation
            patients_generated.labels(format=format_type).inc(patient_count)
        except Exception as e:
            # Record error
            error_type = type(e).__name__
            generation_errors.labels(error_type=error_type).inc()
            raise
        finally:
            # Record duration
            duration = time.time() - start_time
            generation_duration.labels(format=format_type).observe(duration)

    @contextmanager
    def track_job_execution(self, job_type: str):
        """
        Context manager to track job execution metrics.

        Args:
            job_type: Type of job being executed
        """
        start_time = time.time()

        try:
            yield
        finally:
            # Record execution time
            duration = time.time() - start_time
            job_execution_time.labels(job_type=job_type).observe(duration)

    def record_job_status_change(self, from_status: str, to_status: str):
        """Record a job status change."""
        job_status_changes.labels(from_status=from_status, to_status=to_status).inc()

    def update_job_queue_size(self, status: str, size: int):
        """Update the job queue size for a given status."""
        job_queue_size.labels(status=status).set(size)

    def track_job_started(self, job_id: str):
        """Track job start."""
        self.active_jobs: set = getattr(self, "active_jobs", set())
        self.active_jobs.add(job_id)
        job_queue_size.labels(status="running").inc()

    def track_job_completed(self, job_id: str, runtime_seconds: float = 0):
        """Track job completion."""
        # Use job_execution_time histogram which is already defined
        if runtime_seconds > 0:
            job_execution_time.labels(job_type="patient_generation").observe(runtime_seconds)

        # Track completion as a status change
        self.record_job_status_change("running", "completed")

        if hasattr(self, "active_jobs"):
            self.active_jobs.discard(job_id)
        job_queue_size.labels(status="running").dec()

    def track_job_failed(self, job_id: str, error_type: str):
        """Track job failure."""
        # Track as generation error
        generation_errors.labels(error_type=error_type).inc()

        # Track as status change
        self.record_job_status_change("running", "failed")

        if hasattr(self, "active_jobs"):
            self.active_jobs.discard(job_id)
        job_queue_size.labels(status="running").dec()

    def track_resource_usage(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Track resource usage metrics."""
        # For now, we'll use the existing resource metrics
        if metric_name == "job_memory_mb":
            memory_usage_bytes.labels(type="job").set(value * 1024 * 1024)
        elif metric_name == "job_cpu_seconds":
            # Could add a specific job CPU metric if needed
            pass

    def track_generation_error(self, error_type: str):
        """Track generation errors."""
        generation_errors.labels(error_type=error_type).inc()

    def update_connection_pool_metrics(self, pool_status: Dict):
        """Update database connection pool metrics."""
        if "pool" in pool_status:
            pool = pool_status["pool"]
            db_connections_active.set(pool.get("in_use", 0))

        if "metrics" in pool_status:
            metrics = pool_status["metrics"]
            connections = metrics.get("connections", {})
            if connections.get("created"):
                # Set the total connections created
                # Note: We can't directly set a Counter, so we track the delta
                pass

    def update_resource_metrics(self, memory_info: Optional[Dict] = None, cpu_percent: Optional[float] = None):
        """Update system resource metrics."""
        if memory_info:
            memory_usage_bytes.labels(type="rss").set(memory_info.get("rss", 0))
            memory_usage_bytes.labels(type="vms").set(memory_info.get("vms", 0))
            memory_usage_bytes.labels(type="available").set(memory_info.get("available", 0))

        if cpu_percent is not None:
            cpu_usage_percent.set(cpu_percent)

    def record_cache_hit(self, cache_type: str):
        """Record a cache hit."""
        cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str):
        """Record a cache miss."""
        cache_misses.labels(cache_type=cache_type).inc()

    def record_cache_eviction(self, cache_type: str, reason: str):
        """Record a cache eviction."""
        cache_evictions.labels(cache_type=cache_type, reason=reason).inc()

    def get_metrics(self) -> bytes:
        """
        Get current metrics in Prometheus format.

        Returns:
            Prometheus formatted metrics
        """
        return generate_latest(registry)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
