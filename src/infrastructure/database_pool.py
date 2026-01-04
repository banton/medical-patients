"""
Enhanced database connection pool with monitoring and optimization.
Part of EPIC-003: Production Scalability Improvements

Serverless PostgreSQL (Neon) optimizations are ON by default:
- Zero minimum connections (DB_POOL_MIN=0) - allows database to sleep
- Idle connection timeout (DB_IDLE_TIMEOUT=60) - closes unused connections
- Graceful shutdown

Set DB_ALWAYS_ON=true to disable serverless optimizations and keep connections warm.
"""

from contextlib import contextmanager
import logging
import os
import threading
import time
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extensions import connection
import psycopg2.extras
import psycopg2.pool

from src.core.metrics import db_connections_active, db_connections_total, db_query_duration

logger = logging.getLogger(__name__)


class ConnectionPoolMetrics:
    """Tracks connection pool metrics for monitoring."""

    def __init__(self):
        self.lock = threading.Lock()
        self._reset_metrics()

    def _reset_metrics(self):
        """Reset all metrics to initial state."""
        self.total_connections_created = 0
        self.total_connections_closed = 0
        self.total_checkouts = 0
        self.total_checkins = 0
        self.total_checkout_time = 0.0
        self.failed_checkouts = 0
        self.connection_errors = 0
        self.query_count = 0
        self.query_time = 0.0
        self.slow_queries = 0
        self.start_time = time.time()

    def record_connection_created(self):
        """Record a new connection creation."""
        with self.lock:
            self.total_connections_created += 1
            # Update Prometheus metric
            db_connections_total.inc()

    def record_connection_closed(self):
        """Record a connection closure."""
        with self.lock:
            self.total_connections_closed += 1

    def record_checkout(self, duration: float):
        """Record a successful connection checkout."""
        with self.lock:
            self.total_checkouts += 1
            self.total_checkout_time += duration

    def record_checkin(self):
        """Record a connection checkin."""
        with self.lock:
            self.total_checkins += 1

    def record_checkout_failure(self):
        """Record a failed connection checkout."""
        with self.lock:
            self.failed_checkouts += 1

    def record_connection_error(self):
        """Record a connection error."""
        with self.lock:
            self.connection_errors += 1

    def record_query(self, duration: float, slow_threshold: float = 1.0):
        """Record query execution metrics."""
        with self.lock:
            self.query_count += 1
            self.query_time += duration
            if duration > slow_threshold:
                self.slow_queries += 1
            # Update Prometheus metric
            db_query_duration.observe(duration)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self.lock:
            uptime = time.time() - self.start_time
            avg_checkout_time = self.total_checkout_time / self.total_checkouts if self.total_checkouts > 0 else 0
            avg_query_time = self.query_time / self.query_count if self.query_count > 0 else 0

            return {
                "uptime_seconds": uptime,
                "connections": {
                    "created": self.total_connections_created,
                    "closed": self.total_connections_closed,
                    "active": self.total_connections_created - self.total_connections_closed,
                },
                "checkouts": {
                    "total": self.total_checkouts,
                    "failed": self.failed_checkouts,
                    "avg_time_ms": avg_checkout_time * 1000,
                },
                "checkins": {
                    "total": self.total_checkins,
                },
                "queries": {
                    "total": self.query_count,
                    "avg_time_ms": avg_query_time * 1000,
                    "slow_count": self.slow_queries,
                },
                "errors": {
                    "connection": self.connection_errors,
                },
            }


class EnhancedConnectionPool:
    """
    Enhanced PostgreSQL connection pool with monitoring and optimization.

    Features:
    - Connection health checks (pre-ping)
    - Connection recycling after timeout
    - Automatic retry on connection failure
    - Comprehensive metrics collection
    - Query timeout enforcement
    - Idle connection timeout (for serverless PostgreSQL like Neon)
    - Graceful shutdown support
    """

    def __init__(
        self,
        dsn: str,
        minconn: int = 5,
        maxconn: int = 20,
        pool_timeout: float = 30.0,
        pool_recycle: int = 3600,
        pre_ping: bool = True,
        query_timeout: int = 30000,  # milliseconds
        application_name: str = "medical_patients_generator",
        idle_timeout: int = 0,  # seconds, 0 = disabled
        serverless_mode: bool = False,
    ):
        """
        Initialize enhanced connection pool.

        Args:
            dsn: Database connection string
            minconn: Minimum number of connections (0 for serverless)
            maxconn: Maximum number of connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
            pre_ping: Test connections before use
            query_timeout: Query timeout in milliseconds
            application_name: Application name for PostgreSQL
            idle_timeout: Close connections idle for this many seconds (0 = disabled)
            serverless_mode: Enable serverless-friendly behavior (Neon auto-suspend)
        """
        self.dsn = dsn
        self.minconn = minconn
        self.maxconn = maxconn
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pre_ping = pre_ping
        self.query_timeout = query_timeout
        self.application_name = application_name
        self.idle_timeout = idle_timeout
        self.serverless_mode = serverless_mode

        self.metrics = ConnectionPoolMetrics()
        self._lock = threading.Lock()
        self._connection_timestamps: Dict[int, float] = {}
        self._connection_last_used: Dict[int, float] = {}
        self._shutdown = False

        # Initialize the pool
        self._pool = self._create_pool()

        # Start idle connection cleanup thread if idle_timeout is set
        self._cleanup_thread: Optional[threading.Thread] = None
        if self.idle_timeout > 0:
            self._start_idle_cleanup_thread()

        mode_str = " (serverless mode)" if serverless_mode else ""
        idle_str = f", idle_timeout={idle_timeout}s" if idle_timeout > 0 else ""
        logger.info(
            f"Enhanced connection pool initialized{mode_str}: "
            f"minconn={minconn}, maxconn={maxconn}, "
            f"recycle={pool_recycle}s, timeout={pool_timeout}s{idle_str}"
        )

    def _create_pool(self) -> psycopg2.pool.ThreadedConnectionPool:
        """Create the underlying connection pool."""
        try:
            # Create pool with custom connection factory
            # Note: statement_timeout is NOT set via options because NeonDB's
            # connection pooler doesn't support startup parameters.
            # Instead, we set it per-connection after checkout.
            pool = psycopg2.pool.ThreadedConnectionPool(
                self.minconn,
                self.maxconn,
                self.dsn,
                connect_timeout=10,
                application_name=self.application_name,
            )

            # Only pre-warm connections if minconn > 0 (not in serverless mode)
            if self.minconn > 0:
                for _ in range(self.minconn):
                    conn = pool.getconn()
                    self._connection_timestamps[id(conn)] = time.time()
                    self._connection_last_used[id(conn)] = time.time()
                    self.metrics.record_connection_created()
                    pool.putconn(conn)

            return pool

        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise

    def _start_idle_cleanup_thread(self):
        """Start background thread to close idle connections."""
        def cleanup_idle_connections():
            logger.info(f"Idle connection cleanup thread started (timeout={self.idle_timeout}s)")
            while not self._shutdown:
                try:
                    # Check every idle_timeout/2 seconds (or minimum 10 seconds)
                    check_interval = max(10, self.idle_timeout // 2)
                    time.sleep(check_interval)

                    if self._shutdown:
                        break

                    self._close_idle_connections()
                except Exception as e:
                    logger.error(f"Error in idle cleanup thread: {e}")

            logger.info("Idle connection cleanup thread stopped")

        self._cleanup_thread = threading.Thread(
            target=cleanup_idle_connections,
            daemon=True,
            name="db-pool-idle-cleanup"
        )
        self._cleanup_thread.start()

    def _close_idle_connections(self):
        """Close connections that have been idle too long."""
        if not self.idle_timeout or self._shutdown:
            return

        current_time = time.time()
        connections_closed = 0

        with self._lock:
            # Get list of connection ids that are idle too long
            # Note: We can only close connections that are in the pool (not checked out)
            if hasattr(self._pool, "_pool"):
                pool_connections = list(self._pool._pool) if self._pool._pool else []

                for conn in pool_connections:
                    conn_id = id(conn)
                    last_used = self._connection_last_used.get(conn_id, current_time)
                    idle_time = current_time - last_used

                    if idle_time > self.idle_timeout:
                        try:
                            # Remove from pool and close
                            self._pool._pool.remove(conn)
                            conn.close()
                            self._connection_timestamps.pop(conn_id, None)
                            self._connection_last_used.pop(conn_id, None)
                            self.metrics.record_connection_closed()
                            connections_closed += 1
                            logger.debug(f"Closed idle connection {conn_id} (idle {idle_time:.1f}s)")
                        except Exception as e:
                            logger.warning(f"Error closing idle connection: {e}")

        if connections_closed > 0:
            logger.info(f"Closed {connections_closed} idle connection(s) to allow database sleep")

    def _is_connection_expired(self, conn: connection) -> bool:
        """Check if connection should be recycled."""
        conn_id = id(conn)
        if conn_id not in self._connection_timestamps:
            return True

        age = time.time() - self._connection_timestamps[conn_id]
        return age > self.pool_recycle

    def _test_connection(self, conn: connection) -> bool:
        """Test if connection is still alive."""
        if not self.pre_ping:
            return True

        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return True
        except Exception:
            return False

    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool with automatic management.

        Yields:
            psycopg2 connection object

        Raises:
            TimeoutError: If unable to get connection within timeout
            ConnectionError: If unable to establish connection
        """
        start_time = time.time()
        conn = None

        try:
            # Get connection with timeout
            conn = self._pool.getconn()
            checkout_time = time.time() - start_time
            self.metrics.record_checkout(checkout_time)

            # Check if connection needs recycling
            if self._is_connection_expired(conn):
                logger.debug(f"Recycling expired connection {id(conn)}")
                self._pool.putconn(conn, close=True)
                self.metrics.record_connection_closed()
                conn = self._pool.getconn()
                self._connection_timestamps[id(conn)] = time.time()
                self.metrics.record_connection_created()

            # Test connection health
            if not self._test_connection(conn):
                logger.warning(f"Connection {id(conn)} failed health check")
                self._pool.putconn(conn, close=True)
                self.metrics.record_connection_closed()
                conn = self._pool.getconn()
                self._connection_timestamps[id(conn)] = time.time()
                self.metrics.record_connection_created()

            # Set statement_timeout per-connection (NeonDB pooler doesn't support it as startup param)
            if self.query_timeout:
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {self.query_timeout}")

            yield conn

        except psycopg2.pool.PoolError as e:
            self.metrics.record_checkout_failure()
            error_message = f"Unable to get connection from pool: {e}"
            raise TimeoutError(error_message)

        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Connection error: {e}")
            error_message = f"Database connection failed: {e}"
            raise ConnectionError(error_message)

        finally:
            if conn:
                try:
                    # Track last used time for idle connection cleanup
                    self._connection_last_used[id(conn)] = time.time()
                    # Return connection to pool
                    self._pool.putconn(conn)
                    self.metrics.record_checkin()
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")

    @contextmanager
    def cursor(self, cursor_factory=psycopg2.extras.DictCursor):
        """
        Get a cursor with automatic connection and metrics management.

        Args:
            cursor_factory: Cursor factory to use

        Yields:
            Database cursor
        """
        with self.get_connection() as conn, conn.cursor(cursor_factory=cursor_factory) as cur:
            # Wrap cursor to track query metrics
            original_execute = cur.execute

            def execute_with_metrics(query, params=None):
                start = time.time()
                try:
                    return original_execute(query, params)
                finally:
                    duration = time.time() - start
                    self.metrics.record_query(duration)

            cur.execute = execute_with_metrics
            yield cur

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics."""
        with self._lock:
            # Get pool stats
            pool_stats = {
                "size": self._pool.maxconn,
                "minconn": self._pool.minconn,
                "available": len(self._pool._pool) if hasattr(self._pool, "_pool") else 0,
                "in_use": self._pool.maxconn - len(self._pool._pool) if hasattr(self._pool, "_pool") else 0,
            }

            # Update Prometheus gauge
            db_connections_active.set(pool_stats["in_use"])

            # Combine with metrics
            return {
                "pool": pool_stats,
                "metrics": self.metrics.get_metrics(),
                "config": {
                    "recycle_seconds": self.pool_recycle,
                    "timeout_seconds": self.pool_timeout,
                    "query_timeout_ms": self.query_timeout,
                    "pre_ping": self.pre_ping,
                    "idle_timeout_seconds": self.idle_timeout,
                    "serverless_mode": self.serverless_mode,
                },
            }

    def close(self):
        """Close all connections in the pool and stop cleanup thread."""
        self._shutdown = True

        # Stop the idle cleanup thread if running
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            logger.info("Stopping idle connection cleanup thread...")
            # Thread will exit on next iteration due to _shutdown flag
            self._cleanup_thread.join(timeout=5)

        # Close all connections in the pool
        if self._pool:
            self._pool.closeall()
            self._connection_timestamps.clear()
            self._connection_last_used.clear()
            logger.info("Connection pool closed")


# Global pool instance
_pool_instance: Optional[EnhancedConnectionPool] = None
_pool_lock = threading.Lock()


def get_pool() -> EnhancedConnectionPool:
    """Get or create the global connection pool instance."""
    global _pool_instance

    if _pool_instance is None:
        with _pool_lock:
            if _pool_instance is None:
                # Get configuration from environment
                dsn = os.getenv("DATABASE_URL")
                if not dsn:
                    error_msg = (
                        "DATABASE_URL environment variable is required. "
                        "For local development, set it in your .env file or docker-compose.yml"
                    )
                    raise ValueError(error_msg)

                # Serverless mode is ON by default; DB_ALWAYS_ON disables it
                always_on = os.getenv("DB_ALWAYS_ON", "false").lower() in ("true", "1", "yes")
                serverless_mode = not always_on

                # Pool configuration - serverless defaults unless DB_ALWAYS_ON is set
                # Serverless: 0 min connections, short recycle, idle timeout enabled
                # Always-on: 5 min connections, long recycle, no idle timeout
                default_minconn = "5" if always_on else "0"
                default_recycle = "3600" if always_on else "300"  # 1 hour vs 5 min
                default_idle_timeout = "0" if always_on else "60"  # disabled vs 60s

                minconn = int(os.getenv("DB_POOL_MIN", default_minconn))
                maxconn = int(os.getenv("DB_POOL_MAX", "20"))
                pool_timeout = float(os.getenv("DB_POOL_TIMEOUT", "30"))
                pool_recycle = int(os.getenv("DB_POOL_RECYCLE", default_recycle))
                pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
                query_timeout = int(os.getenv("DB_QUERY_TIMEOUT", "30000"))
                idle_timeout = int(os.getenv("DB_IDLE_TIMEOUT", default_idle_timeout))

                _pool_instance = EnhancedConnectionPool(
                    dsn=dsn,
                    minconn=minconn,
                    maxconn=maxconn,
                    pool_timeout=pool_timeout,
                    pool_recycle=pool_recycle,
                    pre_ping=pre_ping,
                    query_timeout=query_timeout,
                    idle_timeout=idle_timeout,
                    serverless_mode=serverless_mode,
                )

    return _pool_instance


def close_pool():
    """Close the global connection pool."""
    global _pool_instance

    if _pool_instance:
        with _pool_lock:
            if _pool_instance:
                _pool_instance.close()
                _pool_instance = None
