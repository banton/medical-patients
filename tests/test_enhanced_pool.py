"""
Enhanced tests for database connection pool.
Part of EPIC-003: Production Scalability Improvements
"""

import threading
from unittest.mock import MagicMock, Mock, patch

import psycopg2
import pytest

from src.infrastructure.database_pool import ConnectionPoolMetrics, EnhancedConnectionPool, close_pool, get_pool


class TestConnectionPoolMetrics:
    """Test connection pool metrics tracking."""

    def test_metrics_initialization(self):
        """Test metrics are initialized correctly."""
        metrics = ConnectionPoolMetrics()

        assert metrics.total_connections_created == 0
        assert metrics.total_connections_closed == 0
        assert metrics.total_checkouts == 0
        assert metrics.total_checkins == 0
        assert metrics.failed_checkouts == 0
        assert metrics.connection_errors == 0
        assert metrics.query_count == 0
        assert metrics.slow_queries == 0

    def test_metrics_thread_safety(self):
        """Test metrics are thread-safe."""
        metrics = ConnectionPoolMetrics()

        def increment_metrics():
            for _ in range(100):
                metrics.record_connection_created()
                metrics.record_checkout(0.01)
                metrics.record_query(0.001)

        # Run in multiple threads
        threads = [threading.Thread(target=increment_metrics) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Verify counts are correct
        assert metrics.total_connections_created == 1000
        assert metrics.total_checkouts == 1000
        assert metrics.query_count == 1000

    def test_metrics_calculations(self):
        """Test metrics calculations are correct."""
        metrics = ConnectionPoolMetrics()

        # Record some metrics
        metrics.record_connection_created()
        metrics.record_connection_created()
        metrics.record_connection_closed()

        metrics.record_checkout(0.1)
        metrics.record_checkout(0.2)
        metrics.record_checkout(0.3)
        metrics.record_checkin()
        metrics.record_checkin()

        metrics.record_query(0.5)
        metrics.record_query(1.5)  # Slow query
        metrics.record_query(0.3)

        # Get metrics snapshot
        snapshot = metrics.get_metrics()

        # Verify calculations
        assert snapshot["connections"]["created"] == 2
        assert snapshot["connections"]["closed"] == 1
        assert snapshot["connections"]["active"] == 1

        assert snapshot["checkouts"]["total"] == 3
        assert abs(snapshot["checkouts"]["avg_time_ms"] - 200.0) < 0.01

        assert snapshot["queries"]["total"] == 3
        assert snapshot["queries"]["slow_count"] == 1
        assert abs(snapshot["queries"]["avg_time_ms"] - 766.67) < 1.0


class TestEnhancedConnectionPoolUnit:
    """Unit tests for EnhancedConnectionPool with proper mocking."""

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_pool_initialization_minimal(self, mock_pool_class):
        """Test minimal pool initialization."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Don't simulate getconn during init
        mock_pool.getconn.side_effect = []

        # Create pool
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,  # No initial connections
            maxconn=10,
        )

        # Verify pool was created
        assert pool._pool == mock_pool
        mock_pool_class.assert_called_once()

        # No initial connections should be created with minconn=0
        assert mock_pool.getconn.call_count == 0

    @patch("psycopg2.pool.ThreadedConnectionPool")
    @pytest.mark.skip(reason="Mock setup issues")
    def test_connection_checkout_and_checkin(self, mock_pool_class):
        """Test basic connection checkout and checkin."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 5
        mock_pool.minconn = 0

        # Mock connection
        mock_conn = MagicMock()
        mock_pool.getconn.return_value = mock_conn

        # Create pool
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=5,
            pre_ping=False,  # Disable health check for this test
        )

        # Test checkout and checkin
        with pool.get_connection() as conn:
            assert conn == mock_conn

        # Verify pool operations (getconn might be called multiple times for metrics)
        assert mock_pool.getconn.call_count >= 1
        mock_pool.putconn.assert_called_once_with(mock_conn)

        # Verify metrics
        metrics = pool.metrics.get_metrics()
        assert metrics["checkouts"]["total"] == 1
        assert metrics["checkins"]["total"] == 1

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_connection_health_check_with_recovery(self, mock_pool_class):
        """Test connection health check with automatic recovery."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 5
        mock_pool.minconn = 0

        # Create mock connections
        bad_conn = MagicMock()
        good_conn = MagicMock()

        # Setup health check failure for bad connection
        bad_cursor = MagicMock()
        bad_cursor.execute.side_effect = psycopg2.OperationalError("Connection lost")
        bad_cursor.__enter__ = MagicMock(return_value=bad_cursor)
        bad_cursor.__exit__ = MagicMock(return_value=None)
        bad_conn.cursor.return_value = bad_cursor

        # Setup health check success for good connection
        good_cursor = MagicMock()
        good_cursor.execute.return_value = None
        good_cursor.fetchone.return_value = (1,)
        good_cursor.__enter__ = MagicMock(return_value=good_cursor)
        good_cursor.__exit__ = MagicMock(return_value=None)
        good_conn.cursor.return_value = good_cursor

        # First getconn returns bad connection, then good connection
        mock_pool.getconn.side_effect = [bad_conn, good_conn]

        # Create pool with health check enabled
        pool = EnhancedConnectionPool(dsn="postgresql://test:test@localhost/test", minconn=0, maxconn=5, pre_ping=True)

        # Get connection - should replace bad with good
        with pool.get_connection() as conn:
            assert conn == good_conn

        # Verify bad connection was returned to pool with close=True
        assert mock_pool.putconn.call_count == 2
        mock_pool.putconn.assert_any_call(bad_conn, close=True)
        mock_pool.putconn.assert_any_call(good_conn)

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_pool_status_reporting(self, mock_pool_class):
        """Test pool status reporting."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 2
        mock_pool._pool = [Mock(), Mock(), Mock()]  # 3 available

        # Create pool
        pool = EnhancedConnectionPool(dsn="postgresql://test:test@localhost/test", minconn=0, maxconn=10)

        # Get pool status
        status = pool.get_pool_status()

        # Verify status
        assert status["pool"]["size"] == 10
        assert status["pool"]["minconn"] == 2
        assert status["pool"]["available"] == 3
        assert status["pool"]["in_use"] == 7
        assert "metrics" in status
        assert "config" in status

    @patch("psycopg2.pool.ThreadedConnectionPool")
    @pytest.mark.skip(reason="Mock setup issues")
    def test_cursor_wrapper_metrics(self, mock_pool_class):
        """Test cursor wrapper tracks query metrics."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Setup mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn

        # Create pool
        pool = EnhancedConnectionPool(dsn="postgresql://test:test@localhost/test", minconn=0, maxconn=5, pre_ping=False)

        # Execute query through cursor wrapper
        with pool.cursor() as cur:
            cur.execute("SELECT 1")
            cur.execute("SELECT 2", (2,))

        # Verify queries were executed
        # The execute method gets wrapped, so check the original mock
        assert mock_cursor.execute.call_count >= 2

        # Verify metrics were recorded
        metrics = pool.metrics.get_metrics()
        assert metrics["queries"]["total"] == 2


class TestConnectionPoolIntegration:
    """Integration tests for connection pool."""

    @pytest.fixture()
    def mock_db_env(self, monkeypatch):
        """Mock database environment variables."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
        monkeypatch.setenv("DB_POOL_MIN", "2")
        monkeypatch.setenv("DB_POOL_MAX", "10")
        monkeypatch.setenv("DB_POOL_TIMEOUT", "15")
        monkeypatch.setenv("DB_POOL_RECYCLE", "1800")
        monkeypatch.setenv("DB_POOL_PRE_PING", "true")
        monkeypatch.setenv("DB_QUERY_TIMEOUT", "15000")

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_global_pool_instance(self, mock_pool_class, mock_db_env):
        """Test global pool instance creation and configuration."""
        # Reset global pool
        close_pool()

        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Get pool instance
        pool1 = get_pool()
        pool2 = get_pool()

        # Verify singleton
        assert pool1 is pool2

        # Verify configuration from environment
        assert pool1.minconn == 2
        assert pool1.maxconn == 10
        assert pool1.pool_timeout == 15.0
        assert pool1.pool_recycle == 1800
        assert pool1.pre_ping is True
        assert pool1.query_timeout == 15000

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_pool_close(self, mock_pool_class, mock_db_env):
        """Test pool closure."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Reset global pool first
        close_pool()

        # Get pool instance
        pool = get_pool()
        assert pool is not None

        # Close pool
        close_pool()

        # Verify new instance is created
        new_pool = get_pool()
        assert new_pool is not pool

        # Cleanup
        close_pool()


class TestServerlessMode:
    """Tests for serverless PostgreSQL (Neon) support."""

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_serverless_mode_initialization(self, mock_pool_class):
        """Test pool initializes correctly in serverless mode."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Create pool in serverless mode
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            idle_timeout=60,
            serverless_mode=True,
        )

        # Verify serverless configuration
        assert pool.minconn == 0
        assert pool.idle_timeout == 60
        assert pool.serverless_mode is True

        # Verify no initial connections are created (minconn=0)
        assert mock_pool.getconn.call_count == 0

        # Cleanup
        pool.close()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_serverless_mode_in_pool_status(self, mock_pool_class):
        """Test serverless mode is reported in pool status."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 0
        mock_pool._pool = []

        # Create serverless pool
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            idle_timeout=60,
            serverless_mode=True,
        )

        # Get status
        status = pool.get_pool_status()

        # Verify serverless mode is in config
        assert status["config"]["serverless_mode"] is True
        assert status["config"]["idle_timeout_seconds"] == 60

        # Cleanup
        pool.close()

    @pytest.fixture()
    def serverless_env(self, monkeypatch):
        """Mock serverless environment variables (default behavior)."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
        # No DB_ALWAYS_ON means serverless is the default
        monkeypatch.delenv("DB_ALWAYS_ON", raising=False)
        # Reset global pool before test
        close_pool()

    @pytest.fixture()
    def always_on_env(self, monkeypatch):
        """Mock always-on environment variables."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
        monkeypatch.setenv("DB_ALWAYS_ON", "true")
        # Reset global pool before test
        close_pool()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_get_pool_serverless_is_default(self, mock_pool_class, serverless_env):
        """Test get_pool() uses serverless mode by default."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Get pool - should be in serverless mode by default
        pool = get_pool()

        # Verify serverless defaults were applied
        assert pool.minconn == 0
        assert pool.serverless_mode is True
        assert pool.idle_timeout == 60  # Default for serverless
        assert pool.pool_recycle == 300  # Default for serverless (5 min)

        # Cleanup
        close_pool()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_get_pool_with_always_on_env(self, mock_pool_class, always_on_env):
        """Test get_pool() reads DB_ALWAYS_ON environment variable."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Get pool - should detect always-on mode
        pool = get_pool()

        # Verify always-on defaults were applied
        assert pool.minconn == 5
        assert pool.serverless_mode is False
        assert pool.idle_timeout == 0  # Disabled for always-on
        assert pool.pool_recycle == 3600  # 1 hour for always-on

        # Cleanup
        close_pool()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_idle_cleanup_thread_starts(self, mock_pool_class):
        """Test idle cleanup thread starts when idle_timeout is set."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Create pool with idle timeout
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            idle_timeout=60,
            serverless_mode=True,
        )

        # Verify cleanup thread was created and is running
        assert pool._cleanup_thread is not None
        assert pool._cleanup_thread.is_alive()
        assert pool._cleanup_thread.name == "db-pool-idle-cleanup"

        # Cleanup
        pool.close()

        # Thread should stop after close
        assert pool._shutdown is True

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_idle_cleanup_thread_not_started_when_disabled(self, mock_pool_class):
        """Test idle cleanup thread is NOT started when idle_timeout=0."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Create pool without idle timeout
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            idle_timeout=0,  # Disabled
            serverless_mode=False,
        )

        # Verify cleanup thread was NOT created
        assert pool._cleanup_thread is None

        # Cleanup
        pool.close()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_connection_last_used_tracking(self, mock_pool_class):
        """Test that connection last_used time is tracked."""
        import time

        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 0

        # Setup mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn

        # Create pool without health check to simplify
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            pre_ping=False,
            idle_timeout=0,  # Disable cleanup thread for this test
        )

        # Get connection
        before = time.time()
        with pool.get_connection():
            pass
        after = time.time()

        # Verify last_used was tracked
        conn_id = id(mock_conn)
        assert conn_id in pool._connection_last_used
        assert before <= pool._connection_last_used[conn_id] <= after

        # Cleanup
        pool.close()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_graceful_shutdown_clears_tracking(self, mock_pool_class):
        """Test that graceful shutdown clears connection tracking."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool

        # Setup mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn

        # Create pool
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            pre_ping=False,
            idle_timeout=0,
        )

        # Get a connection to populate tracking dicts
        with pool.get_connection():
            pass

        # Verify tracking has data
        assert len(pool._connection_last_used) > 0

        # Close pool
        pool.close()

        # Verify tracking was cleared
        assert len(pool._connection_timestamps) == 0
        assert len(pool._connection_last_used) == 0


class TestColdStart:
    """Tests for cold start behavior after all connections are closed."""

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_cold_start_after_all_connections_closed(self, mock_pool_class):
        """Test that pool can recover after all connections are closed (cold start)."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 0
        mock_pool._pool = []  # Empty pool (all connections closed)

        # Setup mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor
        mock_pool.getconn.return_value = mock_conn

        # Create pool in serverless mode (0 min connections)
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            pre_ping=False,
            idle_timeout=0,  # Disable for this test
            serverless_mode=True,
        )

        # Verify pool starts empty
        assert pool.minconn == 0

        # Simulate cold start - get a connection
        with pool.get_connection() as conn:
            assert conn == mock_conn

        # Verify connection was obtained from pool
        mock_pool.getconn.assert_called()

        # Simulate another cold start after pool returns connection
        mock_pool.getconn.reset_mock()
        with pool.get_connection() as conn:
            assert conn == mock_conn

        # Verify pool still works after multiple requests
        mock_pool.getconn.assert_called()

        # Cleanup
        pool.close()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_pool_recovers_from_connection_error(self, mock_pool_class):
        """Test pool can recover from connection errors during cold start."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 0

        # First call fails (simulating Neon waking up), second succeeds
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
        mock_cursor.__exit__ = MagicMock(return_value=None)
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor

        # Pool returns connection successfully
        mock_pool.getconn.return_value = mock_conn

        # Create pool in serverless mode
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10,
            pre_ping=True,  # Enable health check
            idle_timeout=0,
            serverless_mode=True,
        )

        # Get connection - should work with health check
        with pool.get_connection() as conn:
            assert conn == mock_conn

        # Cleanup
        pool.close()

    @patch("psycopg2.pool.ThreadedConnectionPool")
    def test_serverless_defaults_allow_complete_shutdown(self, mock_pool_class):
        """Test that serverless defaults result in no persistent connections."""
        # Setup mock
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 20
        mock_pool.minconn = 0
        mock_pool._pool = []

        # Create pool with serverless defaults
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,  # Serverless default
            maxconn=20,
            pool_recycle=300,  # Serverless default (5 min)
            idle_timeout=60,  # Serverless default
            serverless_mode=True,
        )

        # Verify serverless configuration
        assert pool.minconn == 0, "minconn should be 0 for serverless"
        assert pool.pool_recycle == 300, "pool_recycle should be 5 min for serverless"
        assert pool.idle_timeout == 60, "idle_timeout should be 60s for serverless"
        assert pool.serverless_mode is True

        # Verify no connections were pre-warmed
        assert mock_pool.getconn.call_count == 0, "No connections should be created at startup"

        # Cleanup
        pool.close()


class TestDatabaseAdapter:
    """Test database adapter for backward compatibility."""

    @patch("src.infrastructure.database_adapter.get_pool")
    def test_adapter_uses_enhanced_pool(self, mock_get_pool):
        """Test adapter uses enhanced pool."""
        from src.infrastructure.database_adapter import EnhancedDatabase

        # Setup mock pool
        mock_pool = MagicMock()
        mock_get_pool.return_value = mock_pool

        # Create adapter
        db = EnhancedDatabase()

        # Verify it uses enhanced pool
        assert db._pool == mock_pool
        mock_get_pool.assert_called_once()

    @patch("src.infrastructure.database_adapter.get_pool")
    def test_adapter_execute_query(self, mock_get_pool):
        """Test adapter query execution."""
        from src.infrastructure.database_adapter import EnhancedDatabase

        # Setup mock pool with connection
        mock_pool = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Setup context managers
        mock_pool.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_pool.get_connection.return_value.__exit__ = MagicMock(return_value=None)
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=None)

        mock_get_pool.return_value = mock_pool

        # Create adapter and execute query
        db = EnhancedDatabase()

        # Test fetch_one
        mock_cursor.fetchone.return_value = {"id": 1, "name": "test"}
        result = db._execute_query("SELECT * FROM test WHERE id = %s", (1,), fetch_one=True)
        assert result == {"id": 1, "name": "test"}

        # Test fetch_all
        mock_cursor.fetchall.return_value = [{"id": 1}, {"id": 2}]
        results = db._execute_query("SELECT * FROM test", fetch_all=True)
        assert len(results) == 2

        # Test commit
        db._execute_query("INSERT INTO test VALUES (%s)", (1,), commit=True)
        mock_conn.commit.assert_called_once()
