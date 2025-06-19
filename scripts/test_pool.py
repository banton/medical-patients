#!/usr/bin/env python3
"""
Test script for enhanced database connection pool.
Part of EPIC-003: Production Scalability Improvements
"""

import concurrent.futures
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.infrastructure.database_pool import EnhancedConnectionPool


def test_basic_functionality():
    """Test basic pool functionality."""
    print("Testing basic functionality...")

    # Create pool with test database
    pool = EnhancedConnectionPool(
        dsn=os.getenv("DATABASE_URL", "postgresql://medgen_user:medgen_password@localhost:5432/medgen_db"),
        minconn=2,
        maxconn=5,
        pool_recycle=60,
        pre_ping=True,
    )

    try:
        # Test single query
        with pool.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()
            assert result[0] == 1
            print("✓ Single query successful")

        # Test pool status
        status = pool.get_pool_status()
        print(f"✓ Pool status: {status['pool']}")
        print(f"✓ Metrics: {status['metrics']}")

        # Test concurrent queries
        def run_query(n):
            with pool.cursor() as cur:
                cur.execute("SELECT %s", (n,))
                return cur.fetchone()[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_query, i) for i in range(10)]
            results = [f.result() for f in futures]

        assert results == list(range(10))
        print("✓ Concurrent queries successful")

        # Check final metrics
        final_status = pool.get_pool_status()
        metrics = final_status["metrics"]
        print("\nFinal metrics:")
        print(f"  - Total queries: {metrics['queries']['total']}")
        print(f"  - Avg query time: {metrics['queries']['avg_time_ms']:.2f}ms")
        print(f"  - Total checkouts: {metrics['checkouts']['total']}")
        print(f"  - Connections created: {metrics['connections']['created']}")

        print("\n✅ All tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        pool.close()


def test_performance():
    """Test pool performance under load."""
    print("\nTesting performance under load...")

    # Create pool
    pool = EnhancedConnectionPool(
        dsn=os.getenv("DATABASE_URL", "postgresql://medgen_user:medgen_password@localhost:5432/medgen_db"),
        minconn=5,
        maxconn=20,
        pool_recycle=300,
        pre_ping=True,
    )

    try:
        # Warm up the pool
        for _ in range(5):
            with pool.cursor() as cur:
                cur.execute("SELECT 1")

        # Performance test
        start_time = time.time()
        query_count = 100

        def run_queries():
            for _ in range(10):
                with pool.cursor() as cur:
                    cur.execute("SELECT pg_sleep(0.01)")  # Simulate work

        # Run with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_queries) for _ in range(10)]
            for f in futures:
                f.result()

        duration = time.time() - start_time

        # Get metrics
        status = pool.get_pool_status()
        metrics = status["metrics"]

        print("\nPerformance results:")
        print(f"  - Total time: {duration:.2f}s")
        print(f"  - Queries/second: {query_count / duration:.2f}")
        print(f"  - Avg query time: {metrics['queries']['avg_time_ms']:.2f}ms")
        print(
            f"  - Pool efficiency: {metrics['connections']['created']} connections for {metrics['checkouts']['total']} checkouts"
        )

        # Check for connection reuse
        efficiency = (
            (metrics["checkouts"]["total"] - metrics["connections"]["created"]) / metrics["checkouts"]["total"] * 100
        )
        print(f"  - Connection reuse: {efficiency:.1f}%")

        if efficiency > 80:
            print("\n✅ Performance test passed!")
        else:
            print(f"\n⚠️  Low connection reuse efficiency: {efficiency:.1f}%")

    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        raise
    finally:
        pool.close()


if __name__ == "__main__":
    print("Enhanced Connection Pool Test Script")
    print("=" * 40)

    # Check if database is available
    try:
        test_basic_functionality()
        test_performance()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure the database is running:")
        print("  docker-compose up -d postgres")
        sys.exit(1)
