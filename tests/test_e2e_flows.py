"""
End-to-End Patient Generation Test
Simple test that verifies the basic workflow works
"""

import json
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)
API_KEY = "DEMO_MILMED_2025_50_PATIENTS"
HEADERS = {"X-API-Key": API_KEY}

pytestmark = [pytest.mark.e2e, pytest.mark.integration]


def test_basic_generation_flow():
    """Test basic flow: create config → generate patients → download results"""
    # Simple test configuration
    config = {
        "name": f"E2E Test {uuid4().hex[:8]}",
        "description": "Basic E2E test",
        "total_patients": 10,  # Small number for quick test
        "injury_distribution": {
            "Disease": 50.0,
            "Non-Battle Injury": 30.0,
            "Battle Injury": 20.0
        },
        "front_configs": [{
            "id": "test_front",
            "name": "Test Front",
            "casualty_rate": 1.0,
            "nationality_distribution": [
                {"nationality_code": "US", "percentage": 100.0}
            ]
        }],
        "facility_configs": [
            {"id": "ROLE_1", "name": "Role 1", "kia_rate": 0.1, "rtd_rate": 0.1, "capacity": 50}
        ]
    }
    
    # Create configuration
    response = client.post("/api/v1/configurations/", json=config, headers=HEADERS)
    assert response.status_code == 201
    config_id = response.json()["id"]
    
    # Generate patients
    generation_request = {
        "configuration_id": config_id,
        "output_formats": ["json"],
        "use_compression": False,
        "use_encryption": False
    }
    
    response = client.post("/api/v1/generation/", json=generation_request, headers=HEADERS)
    assert response.status_code == 201
    job_id = response.json()["job_id"]
    
    # Wait for completion (max 30 seconds for 10 patients)
    for _ in range(30):
        response = client.get(f"/api/v1/jobs/{job_id}", headers=HEADERS)
        assert response.status_code == 200
        job = response.json()
        
        if job["status"] == "completed":
            break
        elif job["status"] == "failed":
            pytest.fail(f"Job failed: {job.get('error')}")
        
        time.sleep(1)
    else:
        pytest.fail("Job did not complete within 30 seconds")
    
    # Download results
    response = client.get(f"/api/v1/downloads/{job_id}", headers=HEADERS)
    assert response.status_code == 200
    
    # Verify we got a ZIP file
    assert response.headers.get("content-type") == "application/zip"
    assert "attachment" in response.headers.get("content-disposition", "")
    assert len(response.content) > 0  # Non-empty file
    
    # For now, just verify the download works
    # In a real test, we'd extract and verify the ZIP contents


def test_unauthorized_access():
    """Test that API requires authentication"""
    response = client.get("/api/v1/configurations/")
    assert response.status_code == 401
    
    response = client.post("/api/v1/generation/", json={})
    assert response.status_code == 401