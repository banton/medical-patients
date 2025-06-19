"""
Tests for streaming patient generation endpoint.
Part of EPIC-003: Production Scalability Improvements - Phase 3
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from patient_generator.schemas_config import ConfigurationTemplateDB

# Skip all tests in this module due to TestClient compatibility issue
pytestmark = pytest.mark.skip(reason="TestClient compatibility issue with current starlette version")


class TestStreamingEndpoint:
    """Test streaming patient generation functionality."""

    @pytest.fixture()
    def client(self):
        """Create test client."""
        # Import here to avoid circular imports
        from fastapi.testclient import TestClient

        from src.main import app

        return TestClient(app)

    @pytest.fixture()
    def mock_config(self):
        """Create mock configuration."""
        return ConfigurationTemplateDB(
            id="test-config-123",
            name="Test Config",
            description="Test configuration for streaming",
            total_patients=5,
            injury_distribution={"Disease": 0.5, "Non-Battle Injury": 0.3, "Battle Injury": 0.2},
            front_configs=[],
            facility_configs=[],
        )

    @pytest.fixture()
    def mock_patient_data(self):
        """Create mock patient data."""
        patients = []
        for i in range(5):
            patients.append(
                {
                    "id": i + 1,
                    "name": f"Patient {i + 1}",
                    "nationality": "USA",
                    "gender": "male" if i % 2 == 0 else "female",
                    "injury_type": "Disease",
                    "triage_category": "T2",
                    "demographics": {
                        "first_name": f"John{i}",
                        "last_name": f"Doe{i}",
                        "age": 25 + i,
                    },
                }
            )
        return patients

    @patch("src.api.v1.routers.streaming.verify_api_key")
    @patch("src.api.v1.routers.streaming.Database")
    def test_streaming_endpoint_success(self, mock_db_class, mock_verify, client, mock_config, mock_patient_data):
        """Test successful streaming response."""
        # Setup mocks
        mock_verify.return_value = "test-user"

        # Mock database
        mock_db = MagicMock()
        mock_db_class.get_instance.return_value = mock_db

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_configuration.return_value = mock_config

        with patch("src.api.v1.routers.streaming.ConfigurationRepository", return_value=mock_repo):
            # Mock generation service
            with patch("src.api.v1.routers.streaming.get_patient_generation_service") as mock_gen_service:
                # Create mock service
                mock_service = AsyncMock()
                mock_gen_service.return_value = mock_service

                # Mock cached services
                mock_service.cached_demographics = AsyncMock()
                mock_service.cached_medical = AsyncMock()

                # Mock pipeline generation
                async def mock_generate(context):
                    for patient_data in mock_patient_data:
                        mock_patient = MagicMock()
                        yield mock_patient, patient_data

                mock_pipeline = MagicMock()
                mock_pipeline.generate = mock_generate
                mock_service.pipeline = mock_pipeline
                mock_service._initialize_pipeline = MagicMock()

                # Make request
                response = client.get(
                    "/api/v1/streaming/generate",
                    params={"configuration_id": "test-config-123", "batch_size": 2},
                    headers={"Authorization": "Bearer test-token"},
                )

                # Check response
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/json"
                assert response.headers["x-patient-count"] == "5"
                assert response.headers["x-batch-size"] == "2"

                # Parse streaming response
                response_data = response.json()
                assert "patients" in response_data
                assert len(response_data["patients"]) == 5
                assert response_data["total_patients"] == 5

                # Verify patient data
                for i, patient in enumerate(response_data["patients"]):
                    assert patient["id"] == i + 1
                    assert patient["name"] == f"Patient {i + 1}"

    @patch("src.api.v1.routers.streaming.verify_api_key")
    @patch("src.api.v1.routers.streaming.Database")
    def test_streaming_endpoint_not_found(self, mock_db_class, mock_verify, client):
        """Test streaming with non-existent configuration."""
        # Setup mocks
        mock_verify.return_value = "test-user"

        # Mock database
        mock_db = MagicMock()
        mock_db_class.get_instance.return_value = mock_db

        # Mock repository returning None
        mock_repo = MagicMock()
        mock_repo.get_configuration.return_value = None

        with patch("src.api.v1.routers.streaming.ConfigurationRepository", return_value=mock_repo):
            with patch("src.api.v1.routers.streaming.get_patient_generation_service"):
                # Make request
                response = client.get(
                    "/api/v1/streaming/generate",
                    params={"configuration_id": "non-existent"},
                    headers={"Authorization": "Bearer test-token"},
                )

                # Check error response
                assert response.status_code == 404
                assert "not found" in response.json()["detail"]

    @patch("src.api.v1.routers.streaming.verify_api_key")
    def test_streaming_invalid_batch_size(self, mock_verify, client):
        """Test streaming with invalid batch size."""
        mock_verify.return_value = "test-user"

        # Test batch size too small
        response = client.get(
            "/api/v1/streaming/generate",
            params={"configuration_id": "test-config", "batch_size": 0},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
        assert "between 1 and 1000" in response.json()["detail"]

        # Test batch size too large
        response = client.get(
            "/api/v1/streaming/generate",
            params={"configuration_id": "test-config", "batch_size": 1001},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422
        assert "between 1 and 1000" in response.json()["detail"]

    @patch("src.api.v1.routers.streaming.verify_api_key")
    @patch("src.api.v1.routers.streaming.Database")
    def test_streaming_with_inline_config(self, mock_db_class, mock_verify, client, mock_patient_data):
        """Test streaming with inline configuration."""
        # Setup mocks
        mock_verify.return_value = "test-user"

        # Mock database
        mock_db = MagicMock()
        mock_db_class.get_instance.return_value = mock_db

        # Mock repository
        mock_repo = MagicMock()
        mock_config = ConfigurationTemplateDB(
            id="temp-config-123",
            name="Streaming Configuration",
            description="Temporary configuration for streaming",
            total_patients=3,
            injury_distribution={"Disease": 0.5, "Non-Battle Injury": 0.3, "Battle Injury": 0.2},
            front_configs=[],
            facility_configs=[],
        )
        mock_repo.create_configuration.return_value = mock_config
        mock_repo.get_configuration.return_value = mock_config

        with patch("src.api.v1.routers.streaming.ConfigurationRepository", return_value=mock_repo):
            # Mock generation service
            with patch("src.api.v1.routers.streaming.get_patient_generation_service") as mock_gen_service:
                # Create mock service
                mock_service = AsyncMock()
                mock_gen_service.return_value = mock_service

                # Mock cached services
                mock_service.cached_demographics = AsyncMock()
                mock_service.cached_medical = AsyncMock()

                # Mock pipeline generation (only 3 patients)
                async def mock_generate(context):
                    for patient_data in mock_patient_data[:3]:
                        mock_patient = MagicMock()
                        yield mock_patient, patient_data

                mock_pipeline = MagicMock()
                mock_pipeline.generate = mock_generate
                mock_service.pipeline = mock_pipeline
                mock_service._initialize_pipeline = MagicMock()

                # Make request with inline config
                config_data = {
                    "name": "Test Streaming",
                    "total_patients": 3,
                    "injury_distribution": {"Disease": 0.5, "Non-Battle Injury": 0.3, "Battle Injury": 0.2},
                }

                response = client.post(
                    "/api/v1/streaming/generate",
                    json=config_data,
                    params={"batch_size": 2},
                    headers={"Authorization": "Bearer test-token"},
                )

                # Check response
                assert response.status_code == 200
                assert response.headers["content-type"] == "application/json"
                assert response.headers["x-patient-count"] == "3"

                # Parse streaming response
                response_data = response.json()
                assert "patients" in response_data
                assert len(response_data["patients"]) == 3
                assert response_data["total_patients"] == 3

    @patch("src.api.v1.routers.streaming.verify_api_key")
    @patch("src.api.v1.routers.streaming.Database")
    @patch("src.api.v1.routers.streaming.gc")
    def test_streaming_garbage_collection(self, mock_gc, mock_db_class, mock_verify, client, mock_config):
        """Test that garbage collection is called during streaming."""
        # Setup mocks
        mock_verify.return_value = "test-user"

        # Mock database
        mock_db = MagicMock()
        mock_db_class.get_instance.return_value = mock_db

        # Mock repository
        mock_repo = MagicMock()
        mock_repo.get_configuration.return_value = mock_config

        with patch("src.api.v1.routers.streaming.ConfigurationRepository", return_value=mock_repo):
            # Mock generation service
            with patch("src.api.v1.routers.streaming.get_patient_generation_service") as mock_gen_service:
                # Create mock service
                mock_service = AsyncMock()
                mock_gen_service.return_value = mock_service

                # Mock cached services
                mock_service.cached_demographics = AsyncMock()
                mock_service.cached_medical = AsyncMock()

                # Mock pipeline generation (enough to trigger GC)
                async def mock_generate(context):
                    for i in range(150):  # More than batch_size
                        mock_patient = MagicMock()
                        patient_data = {"id": i + 1, "name": f"Patient {i + 1}"}
                        yield mock_patient, patient_data

                mock_pipeline = MagicMock()
                mock_pipeline.generate = mock_generate
                mock_service.pipeline = mock_pipeline
                mock_service._initialize_pipeline = MagicMock()

                # Make request with batch_size=100
                response = client.get(
                    "/api/v1/streaming/generate",
                    params={"configuration_id": "test-config-123", "count": 150, "batch_size": 100},
                    headers={"Authorization": "Bearer test-token"},
                )

                # Check response
                assert response.status_code == 200

                # Verify garbage collection was called
                assert mock_gc.collect.called
                assert mock_gc.collect.call_count >= 1  # Should be called at least once
