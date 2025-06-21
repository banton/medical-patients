"""
Test API standardization and response models.
Testing API-first principles with proper versioning and response validation.
"""

from datetime import datetime

import pytest

# Use the demo API key which is always available
API_KEY = "DEMO_MILMED_2025_50_PATIENTS"

pytestmark = [pytest.mark.integration]


class TestAPIVersioningStandardization:
    """Test that all API endpoints follow consistent versioning standards."""

    def test_all_endpoints_should_use_v1_prefix(self, client):
        """All API endpoints should use /api/v1/ prefix for consistency."""
        # This test should FAIL initially - we expect inconsistent versioning
        response = client.get("/openapi.json")
        openapi_spec = response.json()

        endpoints = list(openapi_spec["paths"].keys())
        non_v1_endpoints = [
            ep
            for ep in endpoints
            if ep.startswith("/api/")
            and not ep.startswith("/api/v1/")
            and ep not in ["/health", "/ready", "/"]  # Exclude health/system endpoints
        ]

        # This assertion should FAIL - we expect to find non-v1 endpoints
        assert len(non_v1_endpoints) == 0, f"Found non-v1 endpoints: {non_v1_endpoints}"

    def test_generation_endpoint_should_be_versioned(self, client):
        """Generation endpoint should use /api/v1/generation/ instead of /api/generate."""
        # Test old endpoint is deprecated (should return 404)
        response = client.post(
            "/api/generate",
            headers={"X-API-Key": API_KEY},
            json={"configuration_id": "test", "output_formats": ["json"]},
        )
        assert response.status_code == 404  # Old endpoint should be gone

        # Test new versioned endpoint works
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={"configuration": {"count": 5}, "output_formats": ["json"]},
        )
        assert response.status_code in [200, 201, 422], f"Expected success, got {response.status_code}"


class TestJobResponseModels:
    """Test that job endpoints return properly structured response models."""

    def test_job_status_should_return_structured_response(self, client):
        """Job status endpoint should return a proper JobResponse model."""
        # First create a job
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={"configuration": {"count": 5}, "output_formats": ["json"]},
        )
        assert response.status_code in [200, 201]
        job_id = response.json()["job_id"]

        # Get job status
        response = client.get(f"/api/v1/jobs/{job_id}", headers={"X-API-Key": API_KEY})
        assert response.status_code == 200

        job_data = response.json()

        # Test response structure (this should FAIL initially)
        required_fields = [
            "job_id",
            "status",
            "created_at",
            "progress",
            "config",
            "completed_at",
            "error",
            "output_files",
            "progress_details",
            "summary",
        ]

        for field in required_fields:
            assert field in job_data, f"Missing required field: {field}"

        # Test field types
        assert isinstance(job_data["job_id"], str)
        assert job_data["status"] in ["pending", "running", "completed", "failed"]
        assert isinstance(job_data["progress"], int)
        assert 0 <= job_data["progress"] <= 100
        assert isinstance(job_data["config"], dict)
        assert isinstance(job_data["output_files"], list)

    def test_generation_response_should_be_standardized(self, client):
        """Generation endpoint should return standardized GenerationResponse."""
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={"configuration": {"count": 5}, "output_formats": ["json"]},
        )

        assert response.status_code in [200, 201]
        data = response.json()

        # Test standardized response structure (should FAIL initially)
        required_fields = ["job_id", "status", "message", "estimated_duration"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        assert isinstance(data["job_id"], str)
        assert data["status"] in ["pending", "running"]
        assert isinstance(data["message"], str)
        assert data["estimated_duration"] is None or isinstance(data["estimated_duration"], int)


class TestInputValidationEnhancement:
    """Test enhanced input validation for API endpoints."""

    def test_generation_request_should_validate_output_formats(self, client):
        """Generation request should validate output_formats field."""
        # Test invalid format (should return validation error)
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={"configuration": {"count": 5}, "output_formats": ["invalid_format"]},
        )
        # Should return 422 with validation error
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "Invalid output format" in str(error_detail)

    def test_generation_request_should_validate_encryption_password(self, client):
        """Generation request should validate encryption password when encryption is enabled."""
        # Test encryption enabled without password
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={
                "configuration": {"count": 5},
                "output_formats": ["json"],
                "use_encryption": True,
                # Missing encryption_password
            },
        )
        # Should return 422 with validation error
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "encryption_password" in str(error_detail)

    def test_generation_request_should_validate_min_password_length(self, client):
        """Generation request should validate minimum password length."""
        # Test password too short
        response = client.post(
            "/api/v1/generation/",
            headers={"X-API-Key": API_KEY},
            json={
                "configuration": {"count": 5},
                "output_formats": ["json"],
                "use_encryption": True,
                "encryption_password": "123",  # Too short
            },
        )
        # Should return 422 with validation error
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert "8" in str(error_detail)  # Minimum length mentioned


class TestErrorResponseStandardization:
    """Test that all endpoints return standardized error responses."""

    def test_not_found_errors_should_be_standardized(self, client):
        """All 404 errors should return standardized ErrorResponse format."""
        # Test non-existent job
        response = client.get("/api/v1/jobs/nonexistent-job-id", headers={"X-API-Key": API_KEY})
        assert response.status_code == 404

        error_data = response.json()

        # Test standardized error format (should FAIL initially)
        required_fields = ["error", "detail", "timestamp", "request_id"]
        for field in required_fields:
            assert field in error_data, f"Missing error field: {field}"

        assert error_data["error"] == "Not Found"
        assert isinstance(error_data["detail"], str)
        assert isinstance(error_data["timestamp"], str)

        # Validate timestamp format
        datetime.fromisoformat(error_data["timestamp"].replace("Z", "+00:00"))

    def test_unauthorized_errors_should_be_standardized(self, client):
        """Unauthorized errors should return standardized format."""
        # Test without API key
        response = client.post("/api/v1/generation/", json={"test": "data"})
        assert response.status_code == 401

        error_data = response.json()

        # Test standardized error format (should FAIL initially)
        required_fields = ["error", "detail", "timestamp"]
        for field in required_fields:
            assert field in error_data, f"Missing error field: {field}"

        assert error_data["error"] == "Unauthorized"


class TestAPIDocumentationConsistency:
    """Test that API documentation is complete and consistent."""

    def test_all_endpoints_should_have_response_models(self, client):
        """All endpoints should have proper response models defined."""
        response = client.get("/openapi.json")
        openapi_spec = response.json()

        endpoints_without_response_models = []

        for path, methods in openapi_spec["paths"].items():
            if path in ["/", "/health", "/ready"]:  # Skip system endpoints
                continue

            for method, details in methods.items():
                if method.lower() in ["get", "post", "put", "delete"]:
                    responses = details.get("responses", {})
                    success_response = responses.get("200") or responses.get("201") or responses.get("204")

                    # For 204 No Content, we don't expect content
                    if responses.get("204"):
                        continue  # 204 is valid without content
                    if not success_response or "content" not in success_response:
                        endpoints_without_response_models.append(f"{method.upper()} {path}")
                    elif "application/json" in success_response["content"]:
                        json_content = success_response["content"]["application/json"]
                        if "schema" not in json_content:
                            endpoints_without_response_models.append(f"{method.upper()} {path}")

        # This should FAIL initially - some endpoints lack proper response models
        assert len(endpoints_without_response_models) == 0, (
            f"Endpoints without response models: {endpoints_without_response_models}"
        )
