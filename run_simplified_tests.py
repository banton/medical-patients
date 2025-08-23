#!/usr/bin/env python3
"""
Simplified test runner that groups tests by their dependencies
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {cmd}")
    print("="*60)

    result = subprocess.run(cmd, check=False, shell=True)
    return result.returncode == 0

def main():
    """Run test suites grouped by requirements"""

    # Unit tests (no external dependencies)
    unit_tests = [
        ("Core business logic", "pytest tests/test_evacuation_times.py -v"),
        ("Patient memory optimization", "pytest tests/test_patient_memory.py -v"),
        ("Metrics recording", "pytest tests/test_metrics.py -v"),
        ("Cache functionality", "pytest tests/test_cache.py -v"),
    ]

    # Integration tests (need database/redis)
    integration_tests = [
        ("API contract validation", "pytest tests/test_api_standardization.py -v -m integration"),
        ("Simple API workflow", "pytest tests/test_simple_api.py -v"),
        ("Security and auth", "pytest tests/test_security.py tests/test_api_key_management.py -v"),
        ("End-to-end flow", "pytest tests/test_e2e_flows.py -v"),
    ]

    # Quick smoke tests
    smoke_tests = [
        ("Deployment smoke tests", "pytest tests/test_smoke.py -v"),
    ]

    print("SIMPLIFIED TEST SUITE")
    print("====================")
    print("\nThis test suite focuses on core functionality:")
    print("- API contracts work correctly")
    print("- Patients are generated with valid data")
    print("- Security (API keys) works")
    print("- System doesn't crash under normal use")

    # Run unit tests
    print("\n\n1. UNIT TESTS (No external dependencies)")
    unit_passed = 0
    for desc, cmd in unit_tests:
        if run_command(cmd, desc):
            unit_passed += 1

    print(f"\n✅ Unit tests passed: {unit_passed}/{len(unit_tests)}")

    # Check if we should run integration tests
    if "--unit-only" in sys.argv:
        print("\n⚠️  Skipping integration tests (--unit-only flag)")
        return

    print("\n\n2. INTEGRATION TESTS (Requires database/redis)")
    print("⚠️  These tests require services to be running: docker-compose up -d")

    response = input("\nAre services running? (y/n): ")
    if response.lower() != "y":
        print("Skipping integration tests. Run 'docker-compose up -d' first.")
        return

    integration_passed = 0
    for desc, cmd in integration_tests:
        if run_command(cmd, desc):
            integration_passed += 1

    print(f"\n✅ Integration tests passed: {integration_passed}/{len(integration_tests)}")

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Unit tests: {unit_passed}/{len(unit_tests)}")
    print(f"Integration tests: {integration_passed}/{len(integration_tests)}")
    print(f"Total: {unit_passed + integration_passed}/{len(unit_tests) + len(integration_tests)}")

    if unit_passed + integration_passed == len(unit_tests) + len(integration_tests):
        print("\n✅ All tests passed! The system is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the output above.")

if __name__ == "__main__":
    main()
