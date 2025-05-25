"""
Database Integration Tests
Uses testcontainers to spin up PostgreSQL for isolated testing
"""
import pytest
import asyncio
from contextlib import contextmanager
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
import psycopg2
from psycopg2.extras import RealDictCursor
import redis
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patient_generator.database import Database
from patient_generator.config_manager import ConfigurationManager
from patient_generator.models_db import ConfigurationTemplateDBModel
from src.domain.services.job_service import JobService
from src.domain.models.job import Job, JobStatus
from src.core.cache import CacheService


@pytest.fixture(scope="session")
def postgres_container():
    """Create a PostgreSQL test container"""
    with PostgresContainer(
        image="postgres:14-alpine",
        user="test_user",
        password="test_pass",
        dbname="test_db"
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def redis_container():
    """Create a Redis test container"""
    with RedisContainer(image="redis:7-alpine") as redis_cont:
        yield redis_cont


@pytest.fixture
def db_connection(postgres_container):
    """Get a database connection to the test container"""
    connection = psycopg2.connect(
        host=postgres_container.get_container_host_ip(),
        port=postgres_container.get_exposed_port(5432),
        database="test_db",
        user="test_user",
        password="test_pass",
        cursor_factory=RealDictCursor
    )
    yield connection
    connection.close()


@pytest.fixture
def redis_client(redis_container):
    """Get a Redis client for the test container"""
    client = redis.Redis(
        host=redis_container.get_container_host_ip(),
        port=redis_container.get_exposed_port(6379),
        decode_responses=True
    )
    yield client
    client.flushall()


@pytest.fixture
def test_database_url(postgres_container):
    """Get the test database URL"""
    return (
        f"postgresql://test_user:test_pass@"
        f"{postgres_container.get_container_host_ip()}:"
        f"{postgres_container.get_exposed_port(5432)}/test_db"
    )


@pytest.fixture
def test_redis_url(redis_container):
    """Get the test Redis URL"""
    return (
        f"redis://{redis_container.get_container_host_ip()}:"
        f"{redis_container.get_exposed_port(6379)}/0"
    )


def run_migrations(db_connection):
    """Run database migrations for testing"""
    cursor = db_connection.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config_templates (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            template_data JSONB NOT NULL,
            description TEXT,
            version VARCHAR(50),
            parent_id UUID REFERENCES config_templates(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result JSONB,
            error TEXT,
            progress INTEGER DEFAULT 0,
            total_items INTEGER,
            metadata JSONB
        );
    """)
    
    db_connection.commit()
    cursor.close()


class TestDatabaseIntegration:
    """Test database operations with real PostgreSQL"""
    
    def test_database_connection(self, db_connection):
        """Test basic database connectivity"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result['?column?'] == 1
        cursor.close()
    
    def test_config_template_crud(self, db_connection):
        """Test configuration template CRUD operations"""
        run_migrations(db_connection)
        
        cursor = db_connection.cursor()
        
        # Create
        template_data = {
            "name": "Test Template",
            "total_patients": 100,
            "front_configs": [{
                "name": "Test Front",
                "casualty_rate": 0.3,
                "nationality_distribution": [
                    {"nationality_code": "US", "percentage": 100}
                ]
            }]
        }
        
        cursor.execute("""
            INSERT INTO config_templates (name, template_data, description)
            VALUES (%s, %s, %s)
            RETURNING id, name, template_data
        """, ("Test Template", json.dumps(template_data), "Test description"))
        
        created = cursor.fetchone()
        assert created['name'] == "Test Template"
        assert created['template_data']['total_patients'] == 100
        
        # Read
        cursor.execute("SELECT * FROM config_templates WHERE id = %s", (created['id'],))
        fetched = cursor.fetchone()
        assert fetched['name'] == "Test Template"
        
        # Update
        cursor.execute("""
            UPDATE config_templates 
            SET description = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ("Updated description", created['id']))
        
        cursor.execute("SELECT description FROM config_templates WHERE id = %s", (created['id'],))
        updated = cursor.fetchone()
        assert updated['description'] == "Updated description"
        
        # Delete
        cursor.execute("DELETE FROM config_templates WHERE id = %s", (created['id'],))
        cursor.execute("SELECT COUNT(*) as count FROM config_templates WHERE id = %s", (created['id'],))
        deleted = cursor.fetchone()
        assert deleted['count'] == 0
        
        db_connection.commit()
        cursor.close()
    
    def test_job_lifecycle(self, db_connection):
        """Test job creation and status updates"""
        run_migrations(db_connection)
        
        cursor = db_connection.cursor()
        
        # Create job
        cursor.execute("""
            INSERT INTO jobs (status, total_items, metadata)
            VALUES (%s, %s, %s)
            RETURNING id, status, created_at
        """, ("pending", 1000, json.dumps({"type": "patient_generation"})))
        
        job = cursor.fetchone()
        job_id = job['id']
        assert job['status'] == "pending"
        
        # Update progress
        cursor.execute("""
            UPDATE jobs 
            SET status = %s, progress = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ("running", 250, job_id))
        
        cursor.execute("SELECT status, progress FROM jobs WHERE id = %s", (job_id,))
        updated = cursor.fetchone()
        assert updated['status'] == "running"
        assert updated['progress'] == 250
        
        # Complete job
        result_data = {"files": ["patients.json"], "total": 1000}
        cursor.execute("""
            UPDATE jobs 
            SET status = %s, progress = %s, result = %s, 
                completed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, ("completed", 1000, json.dumps(result_data), job_id))
        
        cursor.execute("SELECT status, result FROM jobs WHERE id = %s", (job_id,))
        completed = cursor.fetchone()
        assert completed['status'] == "completed"
        assert completed['result']['total'] == 1000
        
        db_connection.commit()
        cursor.close()


class TestRedisIntegration:
    """Test Redis cache operations"""
    
    def test_redis_connection(self, redis_client):
        """Test basic Redis connectivity"""
        redis_client.set("test_key", "test_value")
        value = redis_client.get("test_key")
        assert value == "test_value"
    
    def test_cache_operations(self, redis_client):
        """Test cache set/get/delete operations"""
        # Set with TTL
        redis_client.setex("ttl_key", 60, "ttl_value")
        assert redis_client.get("ttl_key") == "ttl_value"
        assert redis_client.ttl("ttl_key") > 0
        
        # JSON data
        data = {"name": "Test", "values": [1, 2, 3]}
        redis_client.set("json_key", json.dumps(data))
        retrieved = json.loads(redis_client.get("json_key"))
        assert retrieved["name"] == "Test"
        assert retrieved["values"] == [1, 2, 3]
        
        # Delete
        redis_client.delete("json_key")
        assert redis_client.get("json_key") is None
    
    def test_cache_patterns(self, redis_client):
        """Test common caching patterns"""
        # Set multiple keys
        prefix = "test:demographics:"
        redis_client.set(f"{prefix}US", json.dumps({"name": "United States"}))
        redis_client.set(f"{prefix}UK", json.dumps({"name": "United Kingdom"}))
        redis_client.set(f"{prefix}FR", json.dumps({"name": "France"}))
        
        # Get all keys with pattern
        keys = redis_client.keys(f"{prefix}*")
        assert len(keys) == 3
        
        # Batch get
        values = redis_client.mget(keys)
        assert len(values) == 3
        assert all(v is not None for v in values)
        
        # Clear by pattern
        for key in keys:
            redis_client.delete(key)
        assert len(redis_client.keys(f"{prefix}*")) == 0


class TestCacheServiceIntegration:
    """Test the CacheService with real Redis"""
    
    @pytest.mark.asyncio
    async def test_cache_service_operations(self, test_redis_url):
        """Test CacheService with test Redis container"""
        # Override Redis URL
        os.environ['REDIS_URL'] = test_redis_url
        
        cache = CacheService(test_redis_url)
        await cache.initialize()
        
        try:
            # Test set and get
            await cache.set("test_key", {"data": "test"})
            result = await cache.get("test_key")
            assert result == {"data": "test"}
            
            # Test TTL
            await cache.set("ttl_test", "value", ttl=5)
            assert await cache.get("ttl_test") == "value"
            
            # Test delete
            await cache.delete("test_key")
            assert await cache.get("test_key") is None
            
            # Test clear pattern
            await cache.set("pattern:1", "value1")
            await cache.set("pattern:2", "value2")
            await cache.set("other:1", "other")
            
            await cache.invalidate_pattern("pattern:*")
            assert await cache.get("pattern:1") is None
            assert await cache.get("pattern:2") is None
            assert await cache.get("other:1") == "other"
        finally:
            await cache.close()


class TestDatabaseWithCache:
    """Test database operations with caching"""
    
    def test_cached_config_retrieval(self, db_connection, redis_client):
        """Test configuration retrieval with caching"""
        run_migrations(db_connection)
        
        # Insert test configuration
        cursor = db_connection.cursor()
        template_data = {
            "name": "Cached Template",
            "total_patients": 500
        }
        
        cursor.execute("""
            INSERT INTO config_templates (name, template_data)
            VALUES (%s, %s)
            RETURNING id
        """, ("Cached Template", json.dumps(template_data)))
        
        config_id = cursor.fetchone()['id']
        db_connection.commit()
        
        # First retrieval - from database
        cursor.execute("SELECT * FROM config_templates WHERE id = %s", (config_id,))
        config = cursor.fetchone()
        
        # Cache the result
        cache_key = f"config:{config_id}"
        redis_client.setex(cache_key, 300, json.dumps({
            "id": str(config['id']),
            "name": config['name'],
            "template_data": config['template_data']
        }))
        
        # Second retrieval - from cache
        cached = redis_client.get(cache_key)
        assert cached is not None
        cached_data = json.loads(cached)
        assert cached_data['name'] == "Cached Template"
        
        cursor.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])