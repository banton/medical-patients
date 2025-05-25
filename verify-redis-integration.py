#!/usr/bin/env python3
"""
Verification script for Redis integration across all operational aspects.
This script checks that PERF-001 is properly integrated everywhere.
"""

import sys
from pathlib import Path

def check_docker_compose_files():
    """Check that Redis is present in all docker-compose files."""
    print("🐳 Checking Docker Compose files...")
    
    compose_files = list(Path('.').glob('docker-compose*.yml'))
    results = []
    
    for file in compose_files:
        with open(file, 'r') as f:
            content = f.read()
            has_redis = 'redis' in content.lower()
            results.append((file.name, has_redis))
            status = "✅" if has_redis else "❌"
            print(f"  {status} {file.name}: {'Redis found' if has_redis else 'Redis missing'}")
    
    return all(has_redis for _, has_redis in results)

def check_requirements():
    """Check that Redis dependencies are in requirements.txt."""
    print("\n📦 Checking Python dependencies...")
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
        has_redis = 'redis' in content
        has_hiredis = 'hiredis' in content
        
    print(f"  {'✅' if has_redis else '❌'} redis package: {'found' if has_redis else 'missing'}")
    print(f"  {'✅' if has_hiredis else '❌'} hiredis package: {'found' if has_hiredis else 'missing'}")
    
    return has_redis and has_hiredis

def check_cache_service():
    """Check that cache service files exist."""
    print("\n🧠 Checking cache service files...")
    
    files_to_check = [
        'src/core/cache.py',
        'src/core/cache_utils.py',
        'src/domain/services/cached_demographics_service.py',
        'src/domain/services/cached_medical_service.py'
    ]
    
    all_exist = True
    for file in files_to_check:
        exists = Path(file).exists()
        all_exist = all_exist and exists
        status = "✅" if exists else "❌"
        print(f"  {status} {file}: {'exists' if exists else 'missing'}")
    
    return all_exist

def check_config_integration():
    """Check that Redis configuration is in config.py."""
    print("\n⚙️  Checking configuration integration...")
    
    with open('config.py', 'r') as f:
        content = f.read()
        has_redis_url = 'REDIS_URL' in content
        has_cache_ttl = 'CACHE_TTL' in content
        has_cache_enabled = 'CACHE_ENABLED' in content
    
    print(f"  {'✅' if has_redis_url else '❌'} REDIS_URL: {'configured' if has_redis_url else 'missing'}")
    print(f"  {'✅' if has_cache_ttl else '❌'} CACHE_TTL: {'configured' if has_cache_ttl else 'missing'}")
    print(f"  {'✅' if has_cache_enabled else '❌'} CACHE_ENABLED: {'configured' if has_cache_enabled else 'missing'}")
    
    return has_redis_url and has_cache_ttl and has_cache_enabled

def check_main_integration():
    """Check that main.py includes Redis initialization."""
    print("\n🚀 Checking main application integration...")
    
    with open('src/main.py', 'r') as f:
        content = f.read()
        has_cache_import = 'from src.core.cache import' in content
        has_lifespan = 'lifespan' in content
        has_health_check = 'redis' in content.lower()
    
    print(f"  {'✅' if has_cache_import else '❌'} Cache imports: {'found' if has_cache_import else 'missing'}")
    print(f"  {'✅' if has_lifespan else '❌'} Lifespan management: {'found' if has_lifespan else 'missing'}")
    print(f"  {'✅' if has_health_check else '❌'} Health check integration: {'found' if has_health_check else 'missing'}")
    
    return has_cache_import and has_lifespan and has_health_check

def check_test_integration():
    """Check that tests include Redis functionality."""
    print("\n🧪 Checking test integration...")
    
    test_files = [
        'tests/test_cache_service.py',
        'tests/test_cached_services.py'
    ]
    
    files_exist = all(Path(file).exists() for file in test_files)
    
    # Check if API tests include health check
    api_test_has_redis = False
    if Path('tests_api.py').exists():
        with open('tests_api.py', 'r') as f:
            content = f.read()
            api_test_has_redis = 'redis' in content.lower()
    
    print(f"  {'✅' if files_exist else '❌'} Cache test files: {'exist' if files_exist else 'missing'}")
    print(f"  {'✅' if api_test_has_redis else '❌'} API tests include Redis: {'yes' if api_test_has_redis else 'no'}")
    
    return files_exist and api_test_has_redis

def check_makefile_integration():
    """Check that Makefile includes Redis commands."""
    print("\n🔨 Checking Makefile integration...")
    
    with open('Makefile', 'r') as f:
        content = f.read()
        has_test_cache = 'test-cache' in content
        has_cache_commands = 'cache-flush' in content or 'cache-info' in content
        has_redis_command = 'redis:' in content
    
    print(f"  {'✅' if has_test_cache else '❌'} Cache test target: {'found' if has_test_cache else 'missing'}")
    print(f"  {'✅' if has_cache_commands else '❌'} Cache management commands: {'found' if has_cache_commands else 'missing'}")
    print(f"  {'✅' if has_redis_command else '❌'} Redis service command: {'found' if has_redis_command else 'missing'}")
    
    return has_test_cache and has_cache_commands and has_redis_command

def check_documentation():
    """Check that documentation includes Redis information."""
    print("\n📚 Checking documentation...")
    
    with open('CLAUDE.md', 'r') as f:
        content = f.read()
        has_redis_env_vars = 'REDIS_URL' in content
        has_cache_section = 'Caching Layer' in content
        has_cache_commands = 'cache-flush' in content
    
    print(f"  {'✅' if has_redis_env_vars else '❌'} Redis environment variables: {'documented' if has_redis_env_vars else 'missing'}")
    print(f"  {'✅' if has_cache_section else '❌'} Caching layer documentation: {'found' if has_cache_section else 'missing'}")
    print(f"  {'✅' if has_cache_commands else '❌'} Cache commands in help: {'found' if has_cache_commands else 'missing'}")
    
    return has_redis_env_vars and has_cache_section and has_cache_commands

def main():
    """Run all verification checks."""
    print("🔍 PERF-001 Redis Integration Verification")
    print("=" * 50)
    
    checks = [
        ("Docker Compose Files", check_docker_compose_files),
        ("Python Dependencies", check_requirements),
        ("Cache Service Files", check_cache_service),
        ("Configuration Integration", check_config_integration),
        ("Main Application Integration", check_main_integration),
        ("Test Integration", check_test_integration),
        ("Makefile Integration", check_makefile_integration),
        ("Documentation", check_documentation)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error checking {name}: {e}")
            results.append((name, False))
    
    # Summary
    print("\n📊 Summary")
    print("=" * 30)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! PERF-001 is fully integrated.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())