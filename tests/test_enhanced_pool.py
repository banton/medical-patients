"""
Enhanced tests for database connection pool.
Part of EPIC-003: Production Scalability Improvements
"""

import threading
import time
from unittest.mock import Mock, MagicMock, patch, call

import pytest
import psycopg2

from src.infrastructure.database_pool import ConnectionPoolMetrics, EnhancedConnectionPool, get_pool, close_pool


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
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
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
            maxconn=10
        )
        
        # Verify pool was created
        assert pool._pool == mock_pool
        mock_pool_class.assert_called_once()
        
        # No initial connections should be created with minconn=0
        assert mock_pool.getconn.call_count == 0
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
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
            pre_ping=False  # Disable health check for this test
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
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
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
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=5,
            pre_ping=True
        )
        
        # Get connection - should replace bad with good
        with pool.get_connection() as conn:
            assert conn == good_conn
        
        # Verify bad connection was returned to pool with close=True
        assert mock_pool.putconn.call_count == 2
        mock_pool.putconn.assert_any_call(bad_conn, close=True)
        mock_pool.putconn.assert_any_call(good_conn)
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
    def test_pool_status_reporting(self, mock_pool_class):
        """Test pool status reporting."""
        # Setup mock pool
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        mock_pool.maxconn = 10
        mock_pool.minconn = 2
        mock_pool._pool = [Mock(), Mock(), Mock()]  # 3 available
        
        # Create pool
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=10
        )
        
        # Get pool status
        status = pool.get_pool_status()
        
        # Verify status
        assert status["pool"]["size"] == 10
        assert status["pool"]["minconn"] == 2
        assert status["pool"]["available"] == 3
        assert status["pool"]["in_use"] == 7
        assert "metrics" in status
        assert "config" in status
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
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
        pool = EnhancedConnectionPool(
            dsn="postgresql://test:test@localhost/test",
            minconn=0,
            maxconn=5,
            pre_ping=False
        )
        
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
    
    @pytest.fixture
    def mock_db_env(self, monkeypatch):
        """Mock database environment variables."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/test")
        monkeypatch.setenv("DB_POOL_MIN", "2")
        monkeypatch.setenv("DB_POOL_MAX", "10")
        monkeypatch.setenv("DB_POOL_TIMEOUT", "15")
        monkeypatch.setenv("DB_POOL_RECYCLE", "1800")
        monkeypatch.setenv("DB_POOL_PRE_PING", "true")
        monkeypatch.setenv("DB_QUERY_TIMEOUT", "15000")
    
    @patch('psycopg2.pool.ThreadedConnectionPool')
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
    
    def test_pool_close(self):
        """Test pool closure."""
        # Get pool instance
        pool = get_pool()
        assert pool is not None
        
        # Close pool
        close_pool()
        
        # Verify new instance is created
        new_pool = get_pool()
        assert new_pool is not pool


class TestDatabaseAdapter:
    """Test database adapter for backward compatibility."""
    
    @patch('src.infrastructure.database_adapter.get_pool')
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
    
    @patch('src.infrastructure.database_adapter.get_pool')
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