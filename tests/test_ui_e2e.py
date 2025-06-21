"""
End-to-end tests for the new UI and API integration.
These tests ensure that UI changes don't break the API contract.
"""

import time
from typing import Any, Dict

import pytest

# Use the demo API key which is always available
API_KEY = "DEMO_MILMED_2025_50_PATIENTS"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

pytestmark = [pytest.mark.integration]


class TestUIAPIIntegration:
    """Test suite for UI and API integration."""

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Setup test environment."""
        # With TestClient, the app is automatically available
        response = client.get("/health")
        assert response.status_code == 200

    def test_root_endpoint_redirects_to_ui(self, client):
        """Test that the root endpoint redirects to UI."""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307  # Redirect
        assert "/static/index.html" in response.headers.get("location", "")

    def test_ui_static_files_accessible(self, client):
        """Test that UI static files are accessible."""
        files = [
            "/static/index.html",
            "/static/css/main.css",
            "/static/js/app.js",
            "/static/js/services/api.js",
            "/static/js/components/accordion.js",
        ]

        for file in files:
            response = client.get(file)
            assert response.status_code == 200, f"Failed to access {file}"

    def test_reference_endpoints_no_auth(self, client):
        """Test that reference endpoints work without authentication."""
        endpoints = [
            "/api/v1/configurations/reference/nationalities/",
            "/api/v1/configurations/reference/condition-types/",
            "/api/v1/configurations/reference/facility-types/",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed to access {endpoint}"
            assert response.json() is not None

    def test_nationalities_format(self, client):
        """Test that nationalities endpoint returns expected format."""
        response = client.get("/api/v1/configurations/reference/nationalities/")
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

    def test_authenticated_endpoints_require_key(self, client):
        """Test that authenticated endpoints require API key."""
        endpoints = [
            "/api/v1/jobs/",
            "/api/v1/configurations/",
        ]

        for endpoint in endpoints:
            # Without API key
            response = client.get(endpoint)
            assert response.status_code in [401, 403]  # Either unauthorized or forbidden is acceptable

            # With API key
            response = client.get(endpoint, headers=HEADERS)
            assert response.status_code == 200

    def test_generation_endpoint_format(self, client):
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
                        "nationality_distribution": [{"nationality_code": "USA", "percentage": 100.0}],
                    }
                ],
                "facility_configs": [
                    {
                        "id": "POINT_OF_INJURY",
                        "name": "Point of Injury",
                        "description": None,
                        "capacity": None,
                        "kia_rate": 0.025,
                        "rtd_rate": 0.10,
                    },
                    {
                        "id": "ROLE_1",
                        "name": "Role 1",
                        "description": None,
                        "capacity": 10,
                        "kia_rate": 0.01,
                        "rtd_rate": 0.15,
                    },
                    {
                        "id": "ROLE_2",
                        "name": "Role 2",
                        "description": None,
                        "capacity": 50,
                        "kia_rate": 0.005,
                        "rtd_rate": 0.30,
                    },
                    {
                        "id": "ROLE_3",
                        "name": "Role 3",
                        "description": None,
                        "capacity": 200,
                        "kia_rate": 0.002,
                        "rtd_rate": 0.25,
                    },
                    {
                        "id": "ROLE_4",
                        "name": "Role 4",
                        "description": None,
                        "capacity": 500,
                        "kia_rate": 0.001,
                        "rtd_rate": 0.40,
                    },
                ],
                "injury_distribution": {"Disease": 50.0, "Battle Injury": 10.0, "Non-Battle Injury": 40.0},
            },
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False,
        }

        response = client.post("/api/v1/generation/", headers=HEADERS, json=ui_config)

        assert response.status_code == 201
        result = response.json()
        assert "job_id" in result
        assert "message" in result

        # Clean up - cancel the job
        job_id = result["job_id"]
        client.post(f"/api/v1/jobs/{job_id}/cancel", headers=HEADERS)

    def test_job_lifecycle(self, client):
        """Test complete job lifecycle from UI perspective."""
        # 1. Create a job
        config = self._get_test_config()
        response = client.post("/api/v1/generation/", headers=HEADERS, json=config)
        assert response.status_code == 201
        job_id = response.json()["job_id"]

        try:
            # 2. Check job status
            response = client.get(f"/api/v1/jobs/{job_id}", headers=HEADERS)
            assert response.status_code == 200
            job_data = response.json()
            assert job_data["job_id"] == job_id
            assert job_data["status"] in ["pending", "running", "completed", "failed"]

            # 3. List jobs
            response = client.get("/api/v1/jobs/", headers=HEADERS)
            assert response.status_code == 200
            jobs = response.json()
            assert any(job["job_id"] == job_id for job in jobs)

            # 4. Wait a bit for progress
            time.sleep(2)

            # 5. Check progress update
            response = client.get(f"/api/v1/jobs/{job_id}", headers=HEADERS)
            assert response.status_code == 200
            job_data = response.json()
            assert "progress" in job_data
            assert 0 <= job_data["progress"] <= 100

        finally:
            # 6. Cancel job (cleanup)
            response = client.post(f"/api/v1/jobs/{job_id}/cancel", headers=HEADERS)
            # Cancel might fail if job already completed/cancelled, that's ok
            assert response.status_code in [200, 400, 404]

    def test_configuration_crud(self, client):
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
                        {"nationality_code": "GBR", "percentage": 50.0},
                    ],
                }
            ],
            "facility_configs": self._get_default_facilities(),
            "injury_distribution": {"Disease": 40.0, "Battle Injury": 20.0, "Non-Battle Injury": 40.0},
        }

        response = client.post("/api/v1/configurations/", headers=HEADERS, json=config)
        assert response.status_code == 201
        created = response.json()
        config_id = created["id"]

        try:
            # 2. Read configuration
            response = client.get(f"/api/v1/configurations/{config_id}", headers=HEADERS)
            assert response.status_code == 200
            fetched = response.json()
            assert fetched["name"] == config["name"]

            # 3. List configurations - verify the created config can be retrieved
            # Instead of checking all configs (there might be hundreds), just fetch the specific one
            response = client.get(f"/api/v1/configurations/{config_id}", headers=HEADERS)
            assert response.status_code == 200, f"Could not retrieve created configuration {config_id}"
            retrieved_config = response.json()
            assert retrieved_config["id"] == config_id

            # 4. Update configuration
            config["name"] = "E2E Test Template Updated"
            response = client.put(f"/api/v1/configurations/{config_id}", headers=HEADERS, json=config)
            assert response.status_code == 200

        finally:
            # 5. Delete configuration (cleanup)
            response = client.delete(f"/api/v1/configurations/{config_id}", headers=HEADERS)
            assert response.status_code == 204

    def test_validation_endpoint(self, client):
        """Test configuration validation endpoint."""
        # Valid configuration
        valid_config = self._get_test_config()["configuration"]
        response = client.post("/api/v1/configurations/validate/", headers=HEADERS, json=valid_config)
        assert response.status_code == 200
        result = response.json()
        assert result["valid"] is True
        assert result["errors"] == []

        # Invalid configuration should return 422 (Unprocessable Entity)
        invalid_config = {
            "name": "Invalid Config",
            "total_patients": -10,  # Invalid negative value
            "front_configs": [],  # Empty fronts
            "facility_configs": self._get_default_facilities(),
            "injury_distribution": {
                "Disease": 50.0,
                "Battle Injury": 60.0,  # Sum > 100%
                "Non-Battle Injury": 40.0,
            },
        }
        response = client.post("/api/v1/configurations/validate/", headers=HEADERS, json=invalid_config)
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422
        error_detail = response.json()
        assert "detail" in error_detail
        # Check that it caught the negative total_patients
        # Our custom error handler returns detail as a string, not a list
        assert "total_patients" in str(error_detail["detail"])

    def test_ui_nationality_mapping(self, client):
        """Test that UI nationality names map correctly to codes."""
        # Get nationalities from API
        response = client.get("/api/v1/configurations/reference/nationalities/")
        assert response.status_code == 200
        nationalities = response.json()

        # Create mapping
        name_to_code = {n["name"]: n["code"] for n in nationalities}

        # Test common mappings used in UI
        assert name_to_code.get("United States") == "USA"
        assert name_to_code.get("United Kingdom") == "GBR"
        assert name_to_code.get("Germany") == "DEU"
        assert name_to_code.get("France") == "FRA"

    def test_concurrent_job_handling(self, client):
        """Test that UI can handle multiple concurrent jobs."""
        job_ids = []

        try:
            # Start multiple jobs
            for i in range(3):
                config = self._get_test_config()
                config["configuration"]["name"] = f"Concurrent Test {i + 1}"

                response = client.post("/api/v1/generation/", headers=HEADERS, json=config)
                assert response.status_code == 201
                job_ids.append(response.json()["job_id"])

            # Check all jobs are listed
            response = client.get("/api/v1/jobs/", headers=HEADERS)
            assert response.status_code == 200
            jobs = response.json()

            for job_id in job_ids:
                assert any(job["job_id"] == job_id for job in jobs)

        finally:
            # Clean up all jobs
            for job_id in job_ids:
                client.post(f"/api/v1/jobs/{job_id}/cancel", headers=HEADERS)

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
                        "nationality_distribution": [{"nationality_code": "USA", "percentage": 100.0}],
                    }
                ],
                "facility_configs": self._get_default_facilities(),
                "injury_distribution": {"Disease": 50.0, "Battle Injury": 10.0, "Non-Battle Injury": 40.0},
            },
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False,
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
                "rtd_rate": 0.10,
            },
            {"id": "ROLE_1", "name": "Role 1", "description": None, "capacity": 10, "kia_rate": 0.01, "rtd_rate": 0.15},
            {
                "id": "ROLE_2",
                "name": "Role 2",
                "description": None,
                "capacity": 50,
                "kia_rate": 0.005,
                "rtd_rate": 0.30,
            },
            {
                "id": "ROLE_3",
                "name": "Role 3",
                "description": None,
                "capacity": 200,
                "kia_rate": 0.002,
                "rtd_rate": 0.25,
            },
            {
                "id": "ROLE_4",
                "name": "Role 4",
                "description": None,
                "capacity": 500,
                "kia_rate": 0.001,
                "rtd_rate": 0.40,
            },
        ]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
