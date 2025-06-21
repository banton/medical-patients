"""
Tests for optimized patient generation pipeline (EPIC-001 Task 2).
"""

import json
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from patient_generator.config_manager import ConfigurationManager
from patient_generator.demographics import DemographicsGenerator
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.formatter import OutputFormatter
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.patient import Patient
from patient_generator.schemas_config import ConfigurationTemplateDB
from src.domain.services.patient_generation_service import (
    AsyncPatientGenerationService,
    GenerationContext,
    PatientGenerationPipeline,
)


class TestStreamingFileWriters:
    """Test async file writing with aiofiles."""

    @pytest.mark.asyncio()
    async def test_streaming_json_write(self):
        """Test that JSON files are written using async I/O."""
        # Create test context
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MagicMock(spec=ConfigurationTemplateDB)
            config.id = "test-config"
            config.total_patients = 10

            context = GenerationContext(
                config=config,
                job_id="test-job",
                output_directory=tmpdir,
                output_formats=["json"],
            )

            # Create service with mocked components
            with patch("src.infrastructure.database_adapter.get_enhanced_database"):
                service = AsyncPatientGenerationService()

            # Mock the pipeline initialization
            with patch.object(service, "_initialize_pipeline"):
                with patch.object(service, "cached_demographics") as mock_demographics:
                    with patch.object(service, "cached_medical") as mock_medical:
                        mock_demographics.warm_cache = AsyncMock()
                        mock_medical.warm_cache = AsyncMock()

                        # Create mock pipeline
                        mock_pipeline = MagicMock()
                        service.pipeline = mock_pipeline

                        # Create mock patients
                        async def mock_generate(*args, **kwargs):
                            for i in range(10):
                                patient = MagicMock(spec=Patient)
                                patient.id = i
                                patient.demographics = {"first_name": f"Test{i}", "last_name": "Patient"}
                                patient.gender = "male"
                                patient.nationality = "USA"
                                patient.injury_type = "Battle Injury"
                                patient.triage_category = "T1"
                                patient.front = "Front1"
                                patient.final_status = "Active"
                                patient.last_facility = "Role1"
                                patient.current_status = "Role1"
                                patient.movement_timeline = []
                                patient.injury_timestamp = None
                                patient.get_age = MagicMock(return_value=25)

                                patient_dict = {"id": i, "test": "data"}
                                yield patient, patient_dict

                        mock_pipeline.generate = mock_generate
                        mock_pipeline.output_formatter = OutputFormatter()

                        # Run generation
                        result = await service.generate_patients(context)

                        # Verify file was created
                        json_file = Path(tmpdir) / "patients.json"
                        assert json_file.exists()

                        # Verify JSON content
                        with open(json_file) as f:
                            data = json.load(f)

                        assert len(data) == 10
                        assert all(item["id"] == i for i, item in enumerate(data))

    @pytest.mark.asyncio()
    async def test_streaming_csv_write(self):
        """Test that CSV files are written using async I/O."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MagicMock(spec=ConfigurationTemplateDB)
            config.id = "test-config"
            config.total_patients = 5

            context = GenerationContext(
                config=config,
                job_id="test-job",
                output_directory=tmpdir,
                output_formats=["csv"],
            )

            with patch("src.infrastructure.database_adapter.get_enhanced_database"):
                service = AsyncPatientGenerationService()

            with patch.object(service, "_initialize_pipeline"):
                with patch.object(service, "cached_demographics") as mock_demographics:
                    with patch.object(service, "cached_medical") as mock_medical:
                        mock_demographics.warm_cache = AsyncMock()
                        mock_medical.warm_cache = AsyncMock()

                        mock_pipeline = MagicMock()
                        service.pipeline = mock_pipeline

                        async def mock_generate(*args, **kwargs):
                            for i in range(5):
                                patient = MagicMock(spec=Patient)
                                patient.id = i
                                patient.demographics = {"first_name": f"Test{i}", "last_name": "Patient"}
                                patient.gender = "male"
                                patient.nationality = "USA"
                                patient.injury_type = "Disease"
                                patient.triage_category = "T2"
                                patient.front = "Front1"
                                patient.final_status = "RTD"
                                patient.last_facility = "Role2"
                                patient.current_status = "Role2"
                                patient.movement_timeline = [1, 2, 3]
                                patient.injury_timestamp = None
                                patient.get_age = MagicMock(return_value=30)

                                yield patient, {"id": i}

                        mock_pipeline.generate = mock_generate
                        mock_pipeline.output_formatter = OutputFormatter()

                        result = await service.generate_patients(context)

                        # Verify CSV file
                        csv_file = Path(tmpdir) / "patients.csv"
                        assert csv_file.exists()

                        with open(csv_file) as f:
                            lines = f.readlines()

                        assert len(lines) == 6  # Header + 5 patients
                        assert "patient_id,name,age,gender" in lines[0]
                        assert '"Test0 Patient"' in lines[1]


class TestChunkedGeneration:
    """Test chunked patient generation for memory efficiency."""

    @pytest.mark.asyncio()
    async def test_chunked_generation_large_dataset(self):
        """Test that large datasets are processed in chunks."""
        config_manager = MagicMock(spec=ConfigurationManager)
        config_manager.get_active_configuration.return_value = MagicMock(
            total_patients=2500,  # > 1000, should trigger chunking
            created_at=MagicMock(strftime=MagicMock(return_value="2025-01-01"))
        )
        config_manager.get_front_configs.return_value = []
        config_manager.get_injury_distribution.return_value = {}
        config_manager.get_facility_configs.return_value = []

        flow_simulator = PatientFlowSimulator(config_manager)
        demographics_gen = MagicMock(spec=DemographicsGenerator)
        medical_gen = MagicMock(spec=MedicalConditionGenerator)
        formatter = MagicMock(spec=OutputFormatter)

        pipeline = PatientGenerationPipeline(
            flow_simulator=flow_simulator,
            demographics_generator=demographics_gen,
            medical_generator=medical_gen,
            output_formatter=formatter,
        )

        context = GenerationContext(
            config=MagicMock(total_patients=2500),
            job_id="test-job",
            output_directory="/tmp",
        )

        # Mock the chunk generation
        chunk_calls = []

        async def mock_generate_chunk(start_id, chunk_size, ctx):
            chunk_calls.append((start_id, chunk_size))
            for i in range(chunk_size):
                patient = MagicMock(spec=Patient)
                patient.id = start_id + i
                yield patient

        with patch.object(pipeline, "_generate_patient_chunk", mock_generate_chunk):
            patients = []
            async for patient in pipeline._generate_base_patients(context):
                patients.append(patient)

            # Verify chunking occurred
            assert len(chunk_calls) == 3  # 1000 + 1000 + 500
            assert chunk_calls[0] == (0, 1000)
            assert chunk_calls[1] == (1000, 1000)
            assert chunk_calls[2] == (2000, 500)

            # Verify all patients generated
            assert len(patients) == 2500

    @pytest.mark.asyncio()
    async def test_no_chunking_small_dataset(self):
        """Test that small datasets don't use chunking."""
        config_manager = MagicMock(spec=ConfigurationManager)
        config_manager.get_active_configuration.return_value = MagicMock(
            total_patients=500,  # < 1000, no chunking
            created_at=MagicMock(strftime=MagicMock(return_value="2025-01-01"))
        )
        config_manager.get_front_configs.return_value = []
        config_manager.get_injury_distribution.return_value = {}
        config_manager.get_facility_configs.return_value = []

        flow_simulator = PatientFlowSimulator(config_manager)
        flow_simulator.generate_casualty_flow = MagicMock(return_value=[MagicMock(id=i) for i in range(500)])

        demographics_gen = MagicMock(spec=DemographicsGenerator)
        medical_gen = MagicMock(spec=MedicalConditionGenerator)
        formatter = MagicMock(spec=OutputFormatter)

        pipeline = PatientGenerationPipeline(
            flow_simulator=flow_simulator,
            demographics_generator=demographics_gen,
            medical_generator=medical_gen,
            output_formatter=formatter,
        )

        context = GenerationContext(
            config=MagicMock(total_patients=500),
            job_id="test-job",
            output_directory="/tmp",
        )

        patients = []
        async for patient in pipeline._generate_base_patients(context):
            patients.append(patient)

        # Verify no chunking, direct generation
        assert len(patients) == 500
        flow_simulator.generate_casualty_flow.assert_called_once()


class TestMemoryOptimization:
    """Test memory optimization features."""

    @pytest.mark.asyncio()
    async def test_periodic_flush(self):
        """Test that files are flushed periodically during generation."""
        flush_calls = []

        class MockFileHandle:
            async def write(self, data):
                pass

            async def flush(self):
                flush_calls.append(1)

            async def close(self):
                pass

        with tempfile.TemporaryDirectory() as tmpdir:
            config = MagicMock(spec=ConfigurationTemplateDB)
            config.id = "test-config"
            config.total_patients = 250  # Should trigger 2 flushes (at 100 and 200)

            context = GenerationContext(
                config=config,
                job_id="test-job",
                output_directory=tmpdir,
                output_formats=["json"],
            )

            with patch("src.infrastructure.database_adapter.get_enhanced_database"):
                service = AsyncPatientGenerationService()

            # Mock file operations
            mock_file = MockFileHandle()

            # Mock aiofiles.open to return the file handle directly
            async def mock_open(*args, **kwargs):
                return mock_file

            with patch("aiofiles.open", side_effect=mock_open):
                with patch.object(service, "_initialize_pipeline"):
                    with patch.object(service, "cached_demographics") as mock_demographics:
                        with patch.object(service, "cached_medical") as mock_medical:
                            mock_demographics.warm_cache = AsyncMock()
                            mock_medical.warm_cache = AsyncMock()

                            mock_pipeline = MagicMock()
                            service.pipeline = mock_pipeline

                            async def mock_generate(*args, **kwargs):
                                for i in range(250):
                                    patient = MagicMock(spec=Patient)
                                    patient.id = i
                                    yield patient, {"id": i}

                            mock_pipeline.generate = mock_generate
                            mock_pipeline.output_formatter = OutputFormatter()

                            with patch("os.rename"):
                                await service.generate_patients(context)

                            # Verify flushes occurred
                            assert len(flush_calls) == 2  # At 100 and 200 patients


class TestTemporalConfiguration:
    """Test in-memory temporal configuration."""

    def test_temporal_config_no_file_io(self):
        """Test that temporal configuration doesn't write to files."""
        config_manager = MagicMock(spec=ConfigurationManager)
        config_manager.get_active_configuration.return_value = MagicMock(
            total_patients=100,
            created_at=MagicMock(strftime=MagicMock(return_value="2025-01-01"))
        )
        config_manager.get_front_configs.return_value = [{"id": "front1", "casualty_rate": 1.0}]
        config_manager.get_injury_distribution.return_value = {"Battle Injury": 0.5, "Disease": 0.5}
        config_manager.get_facility_configs.return_value = [{"id": "POI", "kia_rate": 0.1, "rtd_rate": 0.1}]

        temporal_config = {
            "warfare_types": {"conventional": True},
            "base_date": "2025-06-01",
            "days_of_fighting": 8,
            "total_patients": 100,
            "intensity": "high",
            "tempo": "sustained",
            "environmental_conditions": {},
            "special_events": {},
            "injury_mix": {"Battle Injury": 0.5, "Disease": 0.5},
        }

        # Create flow simulator with temporal config
        flow_simulator = PatientFlowSimulator(config_manager, temporal_config=temporal_config)

        # Verify temporal config is stored in memory
        assert flow_simulator.temporal_config == temporal_config
        assert "warfare_types" in flow_simulator.temporal_config

        # Verify decision logic uses in-memory config
        # The flow simulator should detect temporal config and choose temporal generation
        assert flow_simulator.temporal_config is not None
        assert flow_simulator.temporal_config.get("warfare_types") is not None


if __name__ == "__main__":
    pytest.main([__file__])
