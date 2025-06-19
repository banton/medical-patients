#!/usr/bin/env python3
"""
Test script to verify demo API key functionality.
"""

import json
import requests
import sys


def test_demo_key(base_url="http://localhost:8000"):
    """Test the demo API key."""
    demo_key = "DEMO_MILMED_2025_50_PATIENTS"
    
    print(f"Testing demo API key at {base_url}...")
    print(f"Demo key: {demo_key}")
    print()
    
    # Test 1: Get configurations (should work without auth)
    print("1. Testing public endpoint (no auth)...")
    response = requests.get(f"{base_url}/api/v1/configurations/reference/nationalities/")
    if response.status_code == 200:
        print(f"   ✓ Public endpoint works: {len(response.json())} nationalities")
    else:
        print(f"   ✗ Public endpoint failed: {response.status_code}")
    
    # Test 2: Generate patients with demo key
    print("\n2. Testing generation with demo key...")
    headers = {"X-API-Key": demo_key}
    data = {
        "configuration": {
            "name": "Demo Test",
            "total_patients": 5
        },
        "output_formats": ["json"]
    }
    
    response = requests.post(
        f"{base_url}/api/v1/generation/",
        json=data,
        headers=headers
    )
    
    if response.status_code in [200, 201, 202]:
        result = response.json()
        print(f"   ✓ Generation started: job_id={result.get('job_id')}")
        print(f"   ✓ Status: {result.get('status')}")
    else:
        print(f"   ✗ Generation failed: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test 3: Try exceeding demo limits
    print("\n3. Testing demo key limits...")
    data["configuration"]["total_patients"] = 100  # Exceeds 50 patient limit
    
    response = requests.post(
        f"{base_url}/api/v1/generation/",
        json=data,
        headers=headers
    )
    
    if response.status_code == 400:
        print(f"   ✓ Correctly rejected over-limit request")
        error_detail = response.json().get("detail", "")
        print(f"   Message: {error_detail}")
    else:
        print(f"   ✗ Should have rejected request, got: {response.status_code}")
    
    # Test 4: Check response headers
    print("\n4. Checking API key headers...")
    response = requests.get(
        f"{base_url}/api/v1/health",
        headers=headers
    )
    
    if "X-API-Key-Type" in response.headers:
        print(f"   ✓ API Key Type: {response.headers.get('X-API-Key-Type')}")
        print(f"   ✓ Patient Limit: {response.headers.get('X-Patient-Limit')}")
        print(f"   ✓ Daily Limit: {response.headers.get('X-Daily-Limit')}")
    else:
        print("   ✗ API key headers not found")


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_demo_key(base_url)