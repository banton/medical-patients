"""Tests for simplified API usage with JSON configuration."""

import json
from pathlib import Path
import time

import pytest
import requests

BASE_URL = "http://localhost:8000"
API_KEY = "your_secret_api_key_here"

pytestmark = [pytest.mark.integration]


# Load configuration from JSON files
def load_json_config():
    """Load configuration based on the JSON files."""
    project_root = Path(__file__).parent.parent

    # Load fronts config
    with open(project_root / "patient_generator" / "fronts_config.json") as f:
        fronts_data = json.load(f)

    # Load injuries config
    with open(project_root / "patient_generator" / "injuries.json") as f:
        injuries_data = json.load(f)

    # Build configuration
    config = {
        "name": "Test Configuration from JSON",
        "description": "Configuration built from JSON files",
        "total_patients": injuries_data["patients"],
        "injury_distribution": {
            "Disease": injuries_data["Disease"],
            "Non-Battle Injury": injuries_data["Non-Battle Injury"],
            "Battle Injury": injuries_data["Battle Injury"],
        },
        "front_configs": [],
        "facility_configs": [],
    }

    # Convert fronts data
    for front in fronts_data["fronts"]:
        front_config = {
            "id": front["name"].lower().replace(" ", "_"),
            "name": front["name"],
            "casualty_rate": front["ratio"],
            "nationality_distribution": front["nations"],
        }
        config["front_configs"].append(front_config)

        # Create a facility for each front
        facility_config = {
            "id": f"role2_{front['name'].lower()}",
            "name": f"Role 2 {front['name']}",
            "capacity": int(injuries_data["patients"] * front["ratio"]),
            "role": "Role 2",
            "nationality": front["nations"][0]["nationality_code"],  # Use primary nationality
            "front_id": front_config["id"],
            "kia_rate": 0.05,
            "rtd_rate": 0.85,
        }
        config["facility_configs"].append(facility_config)

    return config


class TestSimpleAPI:
    """Test the simplified API workflow."""

    @pytest.fixture()
    def headers(self):
        return {"X-API-Key": API_KEY}

    def test_json_config_generation(self, headers):
        """Test generation with configuration from JSON files."""
        # Load configuration
        config = load_json_config()

        # Start generation
        response = requests.post(f"{BASE_URL}/api/v1/generation/", json={"configuration": config}, headers=headers)
        assert response.status_code in [200, 201]

        job_data = response.json()
        assert "job_id" in job_data
        job_id = job_data["job_id"]

        # Poll for completion
        max_attempts = 60
        for _attempt in range(max_attempts):
            response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", headers=headers)
            assert response.status_code == 200

            status_data = response.json()
            if status_data["status"] == "completed":
                # Success
                assert "result" in status_data or status_data["status"] == "completed"
                break
            if status_data["status"] == "failed":
                pytest.fail(f"Job failed: {status_data.get('error', 'Unknown error')}")

            time.sleep(1)
        else:
            pytest.fail("Job timed out")

        # Test download
        response = requests.get(f"{BASE_URL}/api/v1/downloads/{job_id}", headers=headers)
        assert response.status_code == 200
        assert len(response.content) > 0
        assert response.headers.get("content-type") == "application/zip"

    def test_minimal_config(self, headers):
        """Test with minimal valid configuration."""
        config = {
            "name": "Minimal Test",
            "description": "Minimal configuration test",
            "total_patients": 10,
            "injury_distribution": {"Disease": 0.5, "Non-Battle Injury": 0.3, "Battle Injury": 0.2},
            "front_configs": [
                {
                    "id": "test_front",
                    "name": "Test Front",
                    "casualty_rate": 1.0,
                    "nationality_distribution": [{"nationality_code": "USA", "percentage": 100.0}],
                }
            ],
            "facility_configs": [
                {
                    "id": "test_facility",
                    "name": "Test Facility",
                    "capacity": 10,
                    "role": "Role 2",
                    "nationality": "USA",
                    "front_id": "test_front",
                    "kia_rate": 0.0,
                    "rtd_rate": 1.0,
                }
            ],
        }

        response = requests.post(f"{BASE_URL}/api/v1/generation/", json={"configuration": config}, headers=headers)
        assert response.status_code in [200, 201]

    def test_invalid_injury_keys(self, headers):
        """Test that using wrong injury distribution keys fails."""
        config = load_json_config()
        # Use wrong keys
        config["injury_distribution"] = {
            "disease": 0.5,  # lowercase - wrong!
            "non-battle_injuries": 0.3,  # underscore - wrong!
            "battle_injuries": 0.2,  # underscore - wrong!
        }

        response = requests.post(f"{BASE_URL}/api/v1/generation/", json={"configuration": config}, headers=headers)

        # Should either fail validation or the job should fail
        if response.status_code in [200, 201]:
            # Job was created, check if it fails
            job_id = response.json()["job_id"]

            # Wait for job to process
            time.sleep(2)

            response = requests.get(f"{BASE_URL}/api/v1/jobs/{job_id}", headers=headers)
            assert response.status_code == 200
            status_data = response.json()
            assert status_data["status"] == "failed"
