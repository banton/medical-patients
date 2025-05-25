"""
End-to-end tests for the new UI and API integration.
These tests ensure that UI changes don't break the API contract.
"""

import json
import time
from typing import Any, Dict
import pytest
import requests
from requests.exceptions import RequestException

# Base URL for tests
BASE_URL = "http://localhost:8000"
API_KEY = "your_secret_api_key_here"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


class TestUIAPIIntegration:
    """Test suite for UI and API integration."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Ensure the server is running
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            assert response.status_code == 200
        except RequestException:
            pytest.skip("Server not running. Start with 'make dev'")

    def test_ui_endpoint_accessible(self):
        """Test that the new UI endpoint is accessible."""
        response = requests.get(f"{BASE_URL}/ui", allow_redirects=False)
        assert response.status_code == 307  # Redirect
        assert "/static/new-ui/index.html" in response.headers.get("location", "")

    def test_ui_static_files_accessible(self):
        """Test that UI static files are accessible."""
        files = [
            "/static/new-ui/index.html",
            "/static/new-ui/css/app.css",
            "/static/new-ui/js/app.js",
            "/static/new-ui/js/globals.js",
        ]
        
        for file in files:
            response = requests.get(f"{BASE_URL}{file}")
            assert response.status_code == 200, f"Failed to access {file}"

    def test_reference_endpoints_no_auth(self):
        """Test that reference endpoints work without authentication."""
        endpoints = [
            "/api/v1/configurations/reference/nationalities/",
            "/api/v1/configurations/reference/condition-types/",
            "/api/v1/configurations/reference/facility-types/",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 200, f"Failed to access {endpoint}"
            assert response.json() is not None

    def test_nationalities_format(self):
        """Test that nationalities endpoint returns expected format."""
        response = requests.get(f"{BASE_URL}/api/v1/configurations/reference/nationalities/")
        assert response.status_code == 200
        
        nationalities = response.json()
        assert isinstance(nationalities, list)
        assert len(nationalities) > 0
        
        # Check format
        for nationality in nationalities:
            assert "code" in nationality
            assert "name" in nationality
            assert len(nationality["code"]) == 3
            assert isinstance(nationality["name"], str)

    def test_authenticated_endpoints_require_key(self):
        """Test that authenticated endpoints require API key."""
        endpoints = [
            "/api/jobs/",
            "/api/v1/configurations/",
        ]
        
        for endpoint in endpoints:
            # Without API key
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 403
            
            # With API key
            response = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
            assert response.status_code == 200

    def test_generation_endpoint_format(self):
        """Test the generation endpoint accepts UI format."""
        # Minimal valid configuration in UI format
        ui_config = {
            "configuration": {
                "name": "E2E Test Configuration",
                "description": "Testing UI to API integration",
                "total_patients": 10,
                "front_configs": [
                    {
                        "id": "test_front_1",
                        "name": "Test Front",
                        "casualty_rate": 1.0,
                        "nationality_distribution": [
                            {"nationality_code": "USA", "percentage": 100.0}
                        ]
                    }
                ],
                "facility_configs": [
                    {
                        "id": "POINT_OF_INJURY",
                        "name": "Point of Injury",
                        "description": None,
                        "capacity": None,
                        "kia_rate": 0.025,
                        "rtd_rate": 0.10
                    },
                    {
                        "id": "ROLE_1",
                        "name": "Role 1",
                        "description": None,
                        "capacity": 10,
                        "kia_rate": 0.01,
                        "rtd_rate": 0.15
                    },
                    {
                        "id": "ROLE_2",
                        "name": "Role 2",
                        "description": None,
                        "capacity": 50,
                        "kia_rate": 0.005,
                        "rtd_rate": 0.30
                    },
                    {
                        "id": "ROLE_3",
                        "name": "Role 3",
                        "description": None,
                        "capacity": 200,
                        "kia_rate": 0.002,
                        "rtd_rate": 0.25
                    },
                    {
                        "id": "ROLE_4",
                        "name": "Role 4",
                        "description": None,
                        "capacity": 500,
                        "kia_rate": 0.001,
                        "rtd_rate": 0.40
                    }
                ],
                "injury_distribution": {
                    "Disease": 50.0,
                    "Battle Injury": 10.0,
                    "Non-Battle Injury": 40.0
                }
            },
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/generate",
            headers=HEADERS,
            json=ui_config
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "job_id" in result
        assert "message" in result
        
        # Clean up - cancel the job
        job_id = result["job_id"]
        requests.post(f"{BASE_URL}/api/jobs/{job_id}/cancel", headers=HEADERS)

    def test_job_lifecycle(self):
        """Test complete job lifecycle from UI perspective."""
        # 1. Create a job
        config = self._get_test_config()
        response = requests.post(
            f"{BASE_URL}/api/generate",
            headers=HEADERS,
            json=config
        )
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        try:
            # 2. Check job status
            response = requests.get(f"{BASE_URL}/api/jobs/{job_id}", headers=HEADERS)
            assert response.status_code == 200
            job_data = response.json()
            assert job_data["job_id"] == job_id
            assert job_data["status"] in ["pending", "running", "completed", "failed"]
            
            # 3. List jobs
            response = requests.get(f"{BASE_URL}/api/jobs/", headers=HEADERS)
            assert response.status_code == 200
            jobs = response.json()
            assert any(job["job_id"] == job_id for job in jobs)
            
            # 4. Wait a bit for progress
            time.sleep(2)
            
            # 5. Check progress update
            response = requests.get(f"{BASE_URL}/api/jobs/{job_id}", headers=HEADERS)
            assert response.status_code == 200
            job_data = response.json()
            assert "progress" in job_data
            assert 0 <= job_data["progress"] <= 1
            
        finally:
            # 6. Cancel job (cleanup)
            response = requests.post(
                f"{BASE_URL}/api/jobs/{job_id}/cancel",
                headers=HEADERS
            )
            # Cancel might fail if job already completed, that's ok
            assert response.status_code in [200, 404]

    def test_configuration_crud(self):
        """Test configuration CRUD operations from UI perspective."""
        # 1. Create configuration
        config = {
            "name": "E2E Test Template",
            "description": "Created by E2E tests",
            "total_patients": 20,
            "front_configs": [
                {
                    "id": "test_front",
                    "name": "Test Front",
                    "casualty_rate": 1.0,
                    "nationality_distribution": [
                        {"nationality_code": "USA", "percentage": 50.0},
                        {"nationality_code": "GBR", "percentage": 50.0}
                    ]
                }
            ],
            "facility_configs": self._get_default_facilities(),
            "injury_distribution": {
                "Disease": 40.0,
                "Battle Injury": 20.0,
                "Non-Battle Injury": 40.0
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/configurations/",
            headers=HEADERS,
            json=config
        )
        assert response.status_code == 201
        created = response.json()
        config_id = created["id"]
        
        try:
            # 2. Read configuration
            response = requests.get(
                f"{BASE_URL}/api/v1/configurations/{config_id}",
                headers=HEADERS
            )
            assert response.status_code == 200
            fetched = response.json()
            assert fetched["name"] == config["name"]
            
            # 3. List configurations
            response = requests.get(
                f"{BASE_URL}/api/v1/configurations/",
                headers=HEADERS
            )
            assert response.status_code == 200
            configs = response.json()
            assert any(c["id"] == config_id for c in configs)
            
            # 4. Update configuration
            config["name"] = "E2E Test Template Updated"
            response = requests.put(
                f"{BASE_URL}/api/v1/configurations/{config_id}",
                headers=HEADERS,
                json=config
            )
            assert response.status_code == 200
            
        finally:
            # 5. Delete configuration (cleanup)
            response = requests.delete(
                f"{BASE_URL}/api/v1/configurations/{config_id}",
                headers=HEADERS
            )
            assert response.status_code == 204

    def test_validation_endpoint(self):
        """Test configuration validation endpoint."""
        # Valid configuration
        valid_config = self._get_test_config()["configuration"]
        response = requests.post(
            f"{BASE_URL}/api/v1/configurations/validate/",
            headers=HEADERS,
            json=valid_config
        )
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["errors"] == []
        
        # Invalid configuration (missing required fields)
        invalid_config = {"name": "Invalid"}
        response = requests.post(
            f"{BASE_URL}/api/v1/configurations/validate/",
            headers=HEADERS,
            json=invalid_config
        )
        assert response.status_code == 200
        result = response.json()
        # The endpoint returns 200 even for invalid configs
        # It's up to the UI to handle the validation result

    def test_ui_nationality_mapping(self):
        """Test that UI nationality names map correctly to codes."""
        # Get nationalities from API
        response = requests.get(f"{BASE_URL}/api/v1/configurations/reference/nationalities/")
        assert response.status_code == 200
        nationalities = response.json()
        
        # Create mapping
        name_to_code = {n["name"]: n["code"] for n in nationalities}
        
        # Test common mappings used in UI
        assert name_to_code.get("United States") == "USA"
        assert name_to_code.get("United Kingdom") == "GBR"
        assert name_to_code.get("Germany") == "DEU"
        assert name_to_code.get("France") == "FRA"

    def test_concurrent_job_handling(self):
        """Test that UI can handle multiple concurrent jobs."""
        job_ids = []
        
        try:
            # Start multiple jobs
            for i in range(3):
                config = self._get_test_config()
                config["configuration"]["name"] = f"Concurrent Test {i+1}"
                
                response = requests.post(
                    f"{BASE_URL}/api/generate",
                    headers=HEADERS,
                    json=config
                )
                assert response.status_code == 200
                job_ids.append(response.json()["job_id"])
            
            # Check all jobs are listed
            response = requests.get(f"{BASE_URL}/api/jobs/", headers=HEADERS)
            assert response.status_code == 200
            jobs = response.json()
            
            for job_id in job_ids:
                assert any(job["job_id"] == job_id for job in jobs)
            
        finally:
            # Clean up all jobs
            for job_id in job_ids:
                requests.post(
                    f"{BASE_URL}/api/jobs/{job_id}/cancel",
                    headers=HEADERS
                )

    # Helper methods
    def _get_test_config(self) -> Dict[str, Any]:
        """Get a minimal test configuration."""
        return {
            "configuration": {
                "name": "E2E Test",
                "description": "Minimal test configuration",
                "total_patients": 10,
                "front_configs": [
                    {
                        "id": "test_front",
                        "name": "Test Front",
                        "casualty_rate": 1.0,
                        "nationality_distribution": [
                            {"nationality_code": "USA", "percentage": 100.0}
                        ]
                    }
                ],
                "facility_configs": self._get_default_facilities(),
                "injury_distribution": {
                    "Disease": 50.0,
                    "Battle Injury": 10.0,
                    "Non-Battle Injury": 40.0
                }
            },
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False
        }

    def _get_default_facilities(self) -> list:
        """Get default facility configuration."""
        return [
            {
                "id": "POINT_OF_INJURY",
                "name": "Point of Injury",
                "description": None,
                "capacity": None,
                "kia_rate": 0.025,
                "rtd_rate": 0.10
            },
            {
                "id": "ROLE_1",
                "name": "Role 1",
                "description": None,
                "capacity": 10,
                "kia_rate": 0.01,
                "rtd_rate": 0.15
            },
            {
                "id": "ROLE_2",
                "name": "Role 2",
                "description": None,
                "capacity": 50,
                "kia_rate": 0.005,
                "rtd_rate": 0.30
            },
            {
                "id": "ROLE_3",
                "name": "Role 3",
                "description": None,
                "capacity": 200,
                "kia_rate": 0.002,
                "rtd_rate": 0.25
            },
            {
                "id": "ROLE_4",
                "name": "Role 4",
                "description": None,
                "capacity": 500,
                "kia_rate": 0.001,
                "rtd_rate": 0.40
            }
        ]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])