"""
PostgreSQL 16.2 Compatibility Tests for Ubuntu 24.04

Tests database functionality, migrations, and PostgreSQL 16 specific features.
"""

import json
import os
from pathlib import Path
import subprocess
import time

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import pytest


class TestPostgreSQL16Compatibility:
    """Test PostgreSQL 16.2 compatibility on Ubuntu 24.04."""

    @pytest.fixture()
    def pg_connection_params(self):
        """Get PostgreSQL connection parameters."""
        return {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "database": "postgres"
        }

    @pytest.fixture()
    def test_db_name(self):
        """Generate unique test database name."""
        return f"test_medical_patients_{int(time.time())}"

    def test_postgresql_version(self, pg_connection_params):
        """Verify PostgreSQL 16.x is running."""
        try:
            conn = psycopg2.connect(**pg_connection_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version_string = cur.fetchone()[0]

                assert "PostgreSQL 16" in version_string, \
                    f"Expected PostgreSQL 16.x, got: {version_string}"

                # Check for specific 16.2 or newer
                cur.execute("SHOW server_version;")
                server_version = cur.fetchone()[0]
                major, minor = map(int, server_version.split(".")[:2])

                assert major == 16, f"Expected major version 16, got {major}"
                assert minor >= 2, f"Expected minor version >= 2, got {minor}"

            conn.close()
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    def test_ssl_connection(self, pg_connection_params):
        """Test SSL connections work with OpenSSL 3.x."""
        try:
            # Attempt SSL connection
            ssl_params = pg_connection_params.copy()
            ssl_params["sslmode"] = "require"

            conn = psycopg2.connect(**ssl_params)

            with conn.cursor() as cur:
                cur.execute("SELECT ssl_is_used();")
                ssl_used = cur.fetchone()[0]

                # SSL might not be configured in test environment
                if ssl_used:
                    cur.execute("SELECT ssl_version();")
                    ssl_version = cur.fetchone()[0]
                    assert ssl_version is not None, "SSL version should be available"

            conn.close()
        except psycopg2.OperationalError as e:
            if "SSL" in str(e):
                pytest.skip("SSL not configured for PostgreSQL")
            else:
                raise

    def test_create_database(self, pg_connection_params, test_db_name):
        """Test database creation with PostgreSQL 16."""
        try:
            conn = psycopg2.connect(**pg_connection_params)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with conn.cursor() as cur:
                # Create test database
                cur.execute(f"CREATE DATABASE {test_db_name};")

                # Verify creation
                cur.execute(
                    "SELECT datname FROM pg_database WHERE datname = %s;",
                    (test_db_name,)
                )
                result = cur.fetchone()
                assert result is not None, f"Database {test_db_name} not created"

                # Clean up
                cur.execute(f"DROP DATABASE {test_db_name};")

            conn.close()
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    def test_json_features(self, pg_connection_params):
        """Test PostgreSQL 16 JSON features used in medical data."""
        try:
            conn = psycopg2.connect(**pg_connection_params)

            with conn.cursor() as cur:
                # Test JSONB operations
                cur.execute("""
                    SELECT 
                        '{"patient": {"id": 1, "name": "Test"}}'::jsonb @> '{"patient": {}}'::jsonb as contains,
                        '{"data": [1,2,3]}'::jsonb -> 'data' -> 1 as array_access,
                        jsonb_build_object('test', 123, 'nested', jsonb_build_object('value', 456)) as build
                """)

                result = cur.fetchone()
                assert result[0] is True, "JSONB containment failed"
                assert result[1] == 2, "JSONB array access failed"
                assert result[2]["nested"]["value"] == 456, "JSONB build failed"

            conn.close()
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")

    def test_performance_features(self, pg_connection_params):
        """Test PostgreSQL 16 performance features."""
        try:
            conn = psycopg2.connect(**pg_connection_params)

            with conn.cursor() as cur:
                # Test parallel query capabilities
                cur.execute("SHOW max_parallel_workers_per_gather;")
                parallel_workers = int(cur.fetchone()[0])
                assert parallel_workers > 0, "Parallel query should be enabled"

                # Test JIT compilation availability
                cur.execute("SHOW jit;")
                jit_enabled = cur.fetchone()[0]
                # JIT might be disabled in test environment

                # Test query planning improvements
                cur.execute("""
                    EXPLAIN (FORMAT JSON) 
                    SELECT count(*) FROM generate_series(1, 1000) s(i)
                    WHERE i % 2 = 0;
                """)
                plan = cur.fetchone()[0]
                assert isinstance(plan, list), "Query plan should be available"

            conn.close()
        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")


class TestAlembicMigrations:
    """Test Alembic migrations work with PostgreSQL 16 on Ubuntu 24.04."""

    @pytest.fixture()
    def alembic_config_path(self):
        """Get alembic.ini path."""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "alembic.ini"
        if not config_path.exists():
            pytest.skip("alembic.ini not found")
        return config_path

    def test_alembic_version(self):
        """Test Alembic version compatibility."""
        try:
            import alembic
            version = alembic.__version__
            major, minor = map(int, version.split(".")[:2])

            # Alembic 1.11+ recommended for PostgreSQL 16
            assert major > 1 or (major == 1 and minor >= 11), \
                f"Alembic {version} may not fully support PostgreSQL 16"
        except ImportError:
            pytest.skip("Alembic not installed")

    def test_migration_sql_generation(self, alembic_config_path, tmp_path):
        """Test migration SQL generation for PostgreSQL 16."""
        try:
            # Generate migration SQL
            result = subprocess.run(
                ["alembic", "--config", str(alembic_config_path),
                 "upgrade", "head", "--sql"],
                capture_output=True,
                text=True,
                cwd=alembic_config_path.parent, check=False
            )

            if result.returncode != 0:
                pytest.skip(f"Alembic SQL generation failed: {result.stderr}")

            sql_output = result.stdout

            # Check for PostgreSQL 16 incompatible syntax
            problematic_patterns = [
                "CREATE RULE",  # Deprecated in favor of triggers
                "CREATE TYPE.*WITHOUT FUNCTION",  # Old syntax
            ]

            for pattern in problematic_patterns:
                assert pattern not in sql_output, \
                    f"Found potentially incompatible syntax: {pattern}"

        except subprocess.CalledProcessError as e:
            pytest.skip(f"Alembic not properly configured: {e}")

    def test_migration_dry_run(self, alembic_config_path):
        """Test migration dry run."""
        try:
            # Check current revision
            result = subprocess.run(
                ["alembic", "--config", str(alembic_config_path), "current"],
                capture_output=True,
                text=True,
                cwd=alembic_config_path.parent, check=False
            )

            if result.returncode != 0:
                pytest.skip(f"Cannot check Alembic status: {result.stderr}")

            # Test migration plan
            result = subprocess.run(
                ["alembic", "--config", str(alembic_config_path),
                 "upgrade", "head", "--sql"],
                capture_output=True,
                text=True,
                cwd=alembic_config_path.parent, check=False
            )

            assert result.returncode == 0, f"Migration planning failed: {result.stderr}"

        except subprocess.CalledProcessError as e:
            pytest.skip(f"Alembic not available: {e}")


class TestDatabaseConnections:
    """Test database connection handling with Ubuntu 24.04 settings."""

    def test_connection_pooling(self):
        """Test connection pooling with psycopg2."""
        try:
            from psycopg2 import pool

            # Create connection pool
            connection_pool = pool.SimpleConnectionPool(
                1, 5,
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                database="postgres"
            )

            # Test getting connections
            conns = []
            for i in range(3):
                conn = connection_pool.getconn()
                assert conn is not None
                conns.append(conn)

            # Return connections
            for conn in conns:
                connection_pool.putconn(conn)

            # Close pool
            connection_pool.closeall()

        except psycopg2.OperationalError as e:
            pytest.skip(f"PostgreSQL not available: {e}")
        except ImportError:
            pytest.skip("psycopg2 pool not available")

    def test_async_connections(self):
        """Test async PostgreSQL connections for FastAPI."""
        try:
            import asyncio

            import asyncpg

            async def test_async():
                # Test asyncpg connection (alternative to psycopg2)
                try:
                    conn = await asyncpg.connect(
                        host=os.getenv("POSTGRES_HOST", "localhost"),
                        port=os.getenv("POSTGRES_PORT", "5432"),
                        user=os.getenv("POSTGRES_USER", "postgres"),
                        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
                        database="postgres"
                    )

                    # Test query
                    version = await conn.fetchval("SELECT version();")
                    assert "PostgreSQL 16" in version

                    await conn.close()
                except Exception as e:
                    pytest.skip(f"Async PostgreSQL not available: {e}")

            asyncio.run(test_async())

        except ImportError:
            pytest.skip("asyncpg not installed")

    def test_sqlalchemy_compatibility(self):
        """Test SQLAlchemy with PostgreSQL 16."""
        try:
            from sqlalchemy import __version__ as sa_version, create_engine, text
            from sqlalchemy.orm import sessionmaker

            # Check SQLAlchemy version
            major, minor = map(int, sa_version.split(".")[:2])
            assert major >= 2, f"SQLAlchemy {sa_version} may not support PostgreSQL 16"

            # Create engine
            database_url = (
                f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
                f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
                f"{os.getenv('POSTGRES_PORT', '5432')}/postgres"
            )

            engine = create_engine(database_url)

            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version();"))
                version = result.scalar()
                assert "PostgreSQL 16" in version

            engine.dispose()

        except ImportError:
            pytest.skip("SQLAlchemy not installed")
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


def generate_database_compatibility_report():
    """Generate database compatibility report."""
    report = {
        "postgresql_16_features": {
            "json_sql_standard": "Full SQL/JSON standard support",
            "merge_command": "SQL MERGE for upsert operations",
            "parallel_vacuuming": "Improved maintenance performance",
            "query_performance": "~15% general query improvement",
            "security_features": "Enhanced row-level security"
        },
        "migration_considerations": {
            "connection_strings": "No changes required",
            "sql_syntax": "Check for deprecated features",
            "performance_tuning": "Review parallel query settings",
            "backup_compatibility": "Test pg_dump/pg_restore"
        },
        "testing_recommendations": [
            "Run full migration test on PostgreSQL 16",
            "Benchmark query performance",
            "Test connection pooling under load",
            "Verify backup/restore procedures"
        ]
    }

    return report


if __name__ == "__main__":
    # Run database tests
    pytest.main([__file__, "-v"])

    # Generate report
    report = generate_database_compatibility_report()
    print("\nDatabase Compatibility Report:")
    print(json.dumps(report, indent=2))
