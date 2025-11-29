#!/usr/bin/env python3
"""Test Redis connection with both regular and SSL connections."""

import asyncio
import os
import sys
from urllib.parse import urlparse

import redis.asyncio as redis
from redis.exceptions import RedisError


async def test_redis_connection(redis_url: str) -> bool:
    """Test Redis connection and basic operations."""
    print(f"\nTesting Redis connection: {redis_url}")

    # Parse URL to check if SSL is needed
    parsed = urlparse(redis_url)
    is_ssl = parsed.scheme == "rediss"

    try:
        # Create connection pool with appropriate SSL settings
        if is_ssl:
            pool = redis.ConnectionPool.from_url(
                redis_url, decode_responses=True, max_connections=10, ssl_cert_reqs="required"
            )
        else:
            pool = redis.ConnectionPool.from_url(redis_url, decode_responses=True, max_connections=10)

        # Create client
        client = redis.Redis(connection_pool=pool)

        # Test basic operations
        print("1. Testing PING...")
        pong = await client.ping()
        print(f"   ✓ PING successful: {pong}")

        print("2. Testing SET/GET...")
        test_key = "test:connection"
        test_value = "Hello from Medical Patients Generator"

        await client.set(test_key, test_value, ex=60)  # 60 second expiry
        retrieved = await client.get(test_key)
        print(f"   ✓ SET/GET successful: {retrieved}")

        print("3. Testing DELETE...")
        deleted = await client.delete(test_key)
        print(f"   ✓ DELETE successful: {deleted} key(s) deleted")

        print("4. Getting server info...")
        info = await client.info("server")
        print(f"   ✓ Redis version: {info.get('redis_version', 'Unknown')}")
        print(f"   ✓ Mode: {info.get('redis_mode', 'Unknown')}")

        # Cleanup
        await client.close()
        await pool.disconnect()

        print("\n✅ Redis connection test PASSED!")
        return True

    except RedisError as e:
        print(f"\n❌ Redis connection test FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


async def main():
    """Main test function."""
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    print("Redis Connection Test")
    print("=" * 50)

    success = await test_redis_connection(redis_url)

    if not success:
        print("\nTroubleshooting tips:")
        print("1. Check if Redis is running (local) or accessible (managed)")
        print("2. Verify the REDIS_URL environment variable")
        print("3. For managed Redis, ensure your IP is in trusted sources")
        print("4. For SSL connections, use 'rediss://' protocol")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
