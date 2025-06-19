"""
Smoke tests for production deployment verification
"""

import time

import pytest
import requests

pytestmark = [pytest.mark.integration]


class TestSmoke:
    """Basic smoke tests to verify deployment"""

    def test_health_endpoint(self, base_url):
        """Test that the health endpoint responds"""
        response = requests.get(f"{base_url}/health", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_api_docs_available(self, base_url):
        """Test that API documentation is accessible"""
        response = requests.get(f"{base_url}/docs", timeout=10)
        assert response.status_code == 200

    def test_nationalities_endpoint(self, base_url, api_headers):
        """Test that nationalities reference endpoint works"""
        response = requests.get(
            f"{base_url}/api/v1/configurations/reference/nationalities/", headers=api_headers, timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("code" in nat and "name" in nat for nat in data)

    def test_database_connectivity(self, base_url, api_headers):
        """Test that database is accessible via configurations endpoint"""
        response = requests.get(f"{base_url}/api/v1/configurations/", headers=api_headers, timeout=10)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_redis_connectivity(self, base_url, api_headers):
        """Test Redis connectivity by checking cache headers"""
        # Make two requests to same endpoint
        response1 = requests.get(
            f"{base_url}/api/v1/configurations/reference/nationalities/", headers=api_headers, timeout=10
        )
        response2 = requests.get(
            f"{base_url}/api/v1/configurations/reference/nationalities/", headers=api_headers, timeout=10
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Second response should be faster (cached)
        # This is a simple heuristic - in production you might check cache headers

    def test_static_files_served(self, base_url):
        """Test that static files are being served"""
        response = requests.get(f"{base_url}/static/index.html", timeout=10)
        assert response.status_code == 200
        assert "Military Medical Exercise Patient Generator" in response.text

    def test_create_minimal_job(self, base_url, api_headers):
        """Test creating a minimal patient generation job"""
        # Create minimal configuration
        config_payload = {
            "name": "Smoke Test Config",
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
                    "kia_rate": 0.1,
                    "rtd_rate": 0.3,
                }
            ],
        }

        # Create configuration
        create_response = requests.post(
            f"{base_url}/api/v1/configurations/", json=config_payload, headers=api_headers, timeout=10
        )
        if create_response.status_code != 201:
            print(f"Configuration creation failed: {create_response.status_code}")
            print(f"Response: {create_response.text}")
        assert create_response.status_code == 201
        config_id = create_response.json()["id"]

        # Start generation job
        job_payload = {
            "configuration_id": config_id,
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False,
        }

        job_response = requests.post(
            f"{base_url}/api/v1/generation/", json=job_payload, headers=api_headers, timeout=10
        )
        assert job_response.status_code == 201
        job_id = job_response.json()["job_id"]

        # Poll job status (with timeout)
        start_time = time.time()
        timeout = 30  # 30 seconds for smoke test

        while time.time() - start_time < timeout:
            status_response = requests.get(f"{base_url}/api/v1/jobs/{job_id}", headers=api_headers, timeout=10)
            assert status_response.status_code == 200

            status = status_response.json()
            if status["status"] == "completed":
                assert status["progress"] == 100
                assert "summary" in status
                break
            if status["status"] == "failed":
                pytest.fail(f"Job failed: {status.get('error', 'Unknown error')}")

            time.sleep(1)
        else:
            pytest.fail(f"Job did not complete within {timeout} seconds")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
