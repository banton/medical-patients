#!/usr/bin/env python3
"""Test Redis connection with SSL support for managed Redis."""

import asyncio
import os
import ssl
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import redis.asyncio as redis
from config import get_settings


async def test_redis_connection():
    """Test Redis connection with proper SSL handling."""
    settings = get_settings()
    redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
    
    print(f"Testing Redis connection to: {redis_url}")
    print(f"SSL enabled: {redis_url.startswith('rediss://')}")
    
    try:
        if redis_url.startswith("rediss://"):
            # Create SSL context for managed Redis
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            
            client = redis.from_url(
                redis_url,
                decode_responses=True,
                ssl_cert_reqs="required",
                ssl_context=ssl_context
            )
        else:
            # Regular Redis connection
            client = redis.from_url(redis_url, decode_responses=True)
        
        # Test basic operations
        print("\n1. Testing PING...")
        pong = await client.ping()
        print(f"   ✓ PING successful: {pong}")
        
        print("\n2. Testing SET/GET...")
        await client.set("test:key", "test_value", ex=60)
        value = await client.get("test:key")
        print(f"   ✓ SET/GET successful: {value}")
        
        print("\n3. Testing DELETE...")
        deleted = await client.delete("test:key")
        print(f"   ✓ DELETE successful: {deleted} key(s) deleted")
        
        print("\n4. Testing connection pool...")
        pool_stats = client.connection_pool.connection_kwargs
        print(f"   ✓ Pool config: {pool_stats.get('host', 'N/A')}")
        
        await client.close()
        
        print("\n✅ All Redis tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Redis connection failed: {type(e).__name__}: {e}")
        return False


async def test_cache_service():
    """Test the cache service implementation."""
    from src.core.cache import initialize_cache, get_cache_service, close_cache
    
    settings = get_settings()
    redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
    
    print("\n\nTesting Cache Service...")
    print("=" * 50)
    
    try:
        # Initialize cache
        print("1. Initializing cache service...")
        await initialize_cache(redis_url, 3600)
        cache = get_cache_service()
        
        if not cache:
            print("   ❌ Cache service initialization failed")
            return False
            
        print("   ✓ Cache service initialized")
        
        # Test operations
        print("\n2. Testing cache operations...")
        
        # Set
        success = await cache.set("test:service", {"data": "test"}, 60)
        print(f"   ✓ SET: {success}")
        
        # Get
        value = await cache.get("test:service")
        print(f"   ✓ GET: {value}")
        
        # Exists
        exists = await cache.exists("test:service")
        print(f"   ✓ EXISTS: {exists}")
        
        # TTL
        ttl = await cache.get_ttl("test:service")
        print(f"   ✓ TTL: {ttl} seconds")
        
        # Delete
        deleted = await cache.delete("test:service")
        print(f"   ✓ DELETE: {deleted}")
        
        # Health check
        healthy = await cache.health_check()
        print(f"   ✓ Health check: {healthy}")
        
        # Close
        await close_cache()
        print("\n✅ Cache service tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Cache service test failed: {type(e).__name__}: {e}")
        return False


async def main():
    """Run all tests."""
    print("Redis Connection Test Suite")
    print("=" * 50)
    
    # Test direct Redis connection
    redis_ok = await test_redis_connection()
    
    # Test cache service
    cache_ok = await test_cache_service()
    
    if redis_ok and cache_ok:
        print("\n✅ All tests passed! Redis is properly configured.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check your Redis configuration.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())