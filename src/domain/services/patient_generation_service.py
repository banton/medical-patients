"""
Async patient generation service for stream-based processing.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import gzip
import os
import sys
import tempfile
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

# Compatibility for Python < 3.9
if sys.version_info >= (3, 9):
    to_thread = asyncio.to_thread
else:

    async def to_thread(func, *args, **kwargs):
        """Backport of asyncio.to_thread for Python < 3.9."""
        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, func, *args, **kwargs)


from patient_generator.config_manager import ConfigurationManager
from patient_generator.database import Database
from patient_generator.demographics import DemographicsGenerator
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.formatter import OutputFormatter
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.patient import Patient
from patient_generator.schemas_config import ConfigurationTemplateDB
from src.domain.services.cached_demographics_service import CachedDemographicsService
from src.domain.services.cached_medical_service import CachedMedicalService


@dataclass
class GenerationContext:
    """Immutable context for patient generation."""

    config: ConfigurationTemplateDB
    job_id: str
    output_directory: str
    encryption_password: Optional[str] = None
    output_formats: Optional[List[str]] = None
    use_compression: bool = False

    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ["json"]


class PatientGenerationPipeline:
    """Stream-based patient generation pipeline."""

    def __init__(
        self,
        flow_simulator: PatientFlowSimulator,
        demographics_generator: DemographicsGenerator,
        medical_generator: MedicalConditionGenerator,
        output_formatter: OutputFormatter,
    ):
        self.flow_simulator = flow_simulator
        self.demographics_generator = demographics_generator
        self.medical_generator = medical_generator
        self.output_formatter = output_formatter

    async def generate(
        self, context: GenerationContext, progress_callback: Optional[Callable] = None
    ) -> AsyncIterator[Tuple[Patient, Dict[str, Any]]]:
        """Generate patients as an async stream."""

        # Initialize generators with config
        await self._initialize_generators(context)

        # Stage 1: Generate base patients
        patient_count = 0
        async for patient in self._generate_base_patients(context):
            # Stage 2: Add demographics
            patient = await self._add_demographics(patient, context)

            # Stage 3: Add medical conditions
            patient = await self._add_medical_conditions(patient, context)

            # Yield for streaming processing
            patient_dict = patient.to_dict()
            yield patient, patient_dict

            patient_count += 1
            if progress_callback:
                # Calculate progress percentage, capped at 100%
                progress = min(patient_count / context.config.total_patients, 1.0)
                phase_description = f"Generated {patient_count} of {context.config.total_patients} patients"

                await progress_callback(
                    {
                        "progress": progress,
                        "processed_patients": patient_count,
                        "total_patients": context.config.total_patients,
                        "phase_description": phase_description,
                        "current_phase": "generating_patients",
                    }
                )

    async def _initialize_generators(self, context: GenerationContext) -> None:
        """Initialize generators with configuration."""
        # This would initialize any necessary state in the generators
        # For now, we'll use the existing synchronous initialization

    async def _generate_base_patients(self, context: GenerationContext) -> AsyncIterator[Patient]:
        """Generate base patients - check for temporal vs legacy generation."""

        # Check if temporal configuration exists by calling the flow simulator's decision logic
        try:
            # Use the flow simulator's generate_casualty_flow method which handles temporal vs legacy decision
            patients = await to_thread(self.flow_simulator.generate_casualty_flow)

            # Yield patients one by one for streaming
            for patient in patients:
                yield patient

        except Exception as e:
            print(f"Error in bulk generation, falling back to individual patient creation: {e}")

            # Fallback to individual patient creation if bulk generation fails
            batch_size = min(100, context.config.total_patients)
            total = context.config.total_patients

            for start in range(0, total, batch_size):
                end = min(start + batch_size, total)

                # Generate batch asynchronously
                tasks = [self._create_patient_async(i, context) for i in range(start, end)]

                patients = await asyncio.gather(*tasks)

                for patient in patients:
                    yield patient

    async def _create_patient_async(self, patient_id: int, context: GenerationContext) -> Patient:
        """Create a single patient asynchronously with complete flow simulation."""
        # Create patient using the flow simulator's method
        # The flow simulator already has access to the config via config_manager
        patient = await to_thread(self.flow_simulator._create_initial_patient, patient_id)

        # CRITICAL: Run the enhanced flow simulation for evacuation timeline tracking
        await to_thread(self.flow_simulator._simulate_patient_flow_single, patient)

        return patient

    async def _add_demographics(self, patient: Patient, context: GenerationContext) -> Patient:
        """Add demographics to patient asynchronously."""
        # Get nationality from patient
        nationality = patient.nationality or "USA"
        gender = "male" if patient.id % 2 == 0 else "female"  # Simple distribution

        # Generate demographics
        person_data = await to_thread(self.demographics_generator.generate_person, nationality, gender)

        # Apply demographics to patient using set_demographics method
        patient.set_demographics(person_data)

        # Set gender if not already set
        if not patient.gender:
            patient.gender = gender

        return patient

    async def _add_medical_conditions(self, patient: Patient, context: GenerationContext) -> Patient:
        """Add medical conditions asynchronously."""
        # Determine condition type based on injury distribution
        injury_dist = context.config.injury_distribution

        # Simple selection logic (would be more sophisticated in production)
        rand_val = patient.id % 100
        if rand_val < injury_dist.get("Disease", 0):
            condition_type = "DISEASE"
        elif rand_val < injury_dist.get("Disease", 0) + injury_dist.get("Non-Battle Injury", 0):
            condition_type = "NON_BATTLE"
        else:
            condition_type = "BATTLE_TRAUMA"

        # Set the injury type on the patient
        patient.injury_type = condition_type

        # Generate triage category based on simple logic
        triage_rand = patient.id % 10
        if triage_rand < 2:
            patient.triage_category = "T1"
        elif triage_rand < 5:
            patient.triage_category = "T2"
        else:
            patient.triage_category = "T3"

        # Generate condition using the medical generator
        condition = await to_thread(
            self.medical_generator.generate_condition, patient.injury_type, patient.triage_category
        )

        # Set primary condition on patient
        patient.primary_condition = condition
        patient.primary_conditions = [condition] if condition else []

        return patient

    # FHIR bundle creation disabled
    # async def _create_fhir_bundle(self, patient: Patient) -> Dict[str, Any]:
    #     """Create FHIR bundle asynchronously."""
    #     return await to_thread(self.fhir_generator.create_patient_bundle, patient)


class AsyncPatientGenerationService:
    """Service for managing async patient generation."""

    def __init__(self):
        self.pipeline = None
        self.config_manager = None
        self.db = Database()
        self.cached_demographics = CachedDemographicsService()
        self.cached_medical = CachedMedicalService()

    def _initialize_pipeline(self, config_id: str):
        """Initialize the generation pipeline with required components."""
        # Initialize configuration manager
        self.config_manager = ConfigurationManager(database_instance=self.db)
        self.config_manager.load_configuration(config_id)

        # Initialize components with config manager
        # Use cached services' generators
        self.pipeline = PatientGenerationPipeline(
            flow_simulator=PatientFlowSimulator(self.config_manager),
            demographics_generator=self.cached_demographics.get_demographics_generator(),
            medical_generator=self.cached_medical._get_condition_generator(),
            output_formatter=OutputFormatter(),
        )

    async def generate_patients(
        self, context: GenerationContext, progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Generate patients and save to files."""

        # Warm up caches before generation
        await self.cached_demographics.warm_cache()
        await self.cached_medical.warm_cache()

        # Initialize pipeline with configuration
        self._initialize_pipeline(context.config.id)

        # Ensure output directory exists
        os.makedirs(context.output_directory, exist_ok=True)

        # Initialize output files
        output_files = {}
        temp_files = {}

        # Create output streams for each format
        output_streams = {}

        for format in context.output_formats or ["json"]:
            if format == "json":
                # JSON needs special handling for streaming
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w", suffix=".json", dir=context.output_directory, delete=False
                )
                temp_file.write("[\n")  # Start JSON array
                temp_files[format] = temp_file
                output_files[format] = temp_file.name
                output_streams[format] = temp_file
            else:
                # Other formats should use text mode for CSV, binary for others
                mode = "w" if format == "csv" else "wb"
                temp_file = tempfile.NamedTemporaryFile(
                    mode=mode, suffix=f".{format}", dir=context.output_directory, delete=False
                )
                temp_files[format] = temp_file
                output_files[format] = temp_file.name
                output_streams[format] = temp_file

        try:
            # Initialize formatter
            formatter = self.pipeline.output_formatter
            first_patient = True
            patient_count = 0

            # Stream patients and write to files
            async for patient, patient_data in self.pipeline.generate(context, progress_callback):
                patient_count += 1

                # Write to each format
                for format in context.output_formats or ["json"]:
                    stream = output_streams[format]

                    if format == "json":
                        # Handle JSON array formatting
                        if not first_patient:
                            stream.write(",\n")

                        # Use patient_data from generator (already converted to dict)

                        import json

                        json.dump(patient_data, stream, indent=2)
                    elif format == "xml":
                        # Use formatter for XML
                        await to_thread(formatter.format_xml, [patient_data], stream)
                    elif format == "csv":
                        # CSV format - write header on first patient
                        if first_patient:
                            stream.write(
                                "patient_id,name,age,gender,nationality,injury,triage,front,final_status,last_facility,total_timeline_events,injury_timestamp\n"
                            )

                        # Extract patient data from demographics and attributes
                        first_name = patient.demographics.get("first_name", "Unknown")
                        last_name = patient.demographics.get("last_name", "Unknown")
                        age = patient.get_age() if hasattr(patient, "get_age") else "Unknown"

                        # Extract evacuation timeline data
                        final_status = patient.final_status or "Active"
                        last_facility = patient.last_facility or patient.current_status
                        timeline_count = len(patient.movement_timeline) if hasattr(patient, "movement_timeline") else 0
                        injury_time = patient.injury_timestamp.isoformat() if patient.injury_timestamp else "Unknown"

                        stream.write(
                            f'{patient.id},"{first_name} {last_name}",{age},{patient.gender},{patient.nationality},{patient.injury_type},{patient.triage_category},{patient.front},{final_status},{last_facility},{timeline_count},{injury_time}\n'
                        )

                first_patient = False

            # Close temporary files properly
            for format, temp_file in temp_files.items():
                if format == "json":
                    temp_file.write("\n]")  # Close JSON array
                temp_file.close()

            # Finalize files
            final_files = await self._finalize_files(output_files, context, patient_count)

            # Apply compression if needed
            if context.use_compression:
                final_files = await self._compress_files(final_files)

            # Apply encryption if needed
            if context.encryption_password:
                final_files = await self._encrypt_files(final_files, context.encryption_password)

            return {
                "status": "completed",
                "output_files": list(final_files.values()),
                "patient_count": context.config.total_patients,
            }

        except Exception as e:
            # Clean up temp files on error
            for temp_file in temp_files.values():
                if hasattr(temp_file, "close"):
                    temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            raise e

    async def _finalize_files(
        self, output_files: Dict[str, str], context: GenerationContext, patient_count: int
    ) -> Dict[str, str]:
        """Finalize output files with proper extensions."""
        final_files = {}

        for format, temp_path in output_files.items():
            # Determine final filename
            if format == "json":
                final_name = "patients.json"
            elif format == "xml":
                final_name = "patients.xml"
            elif format == "csv":
                final_name = "patients.csv"
            else:
                final_name = f"patients.{format}"

            final_path = os.path.join(context.output_directory, final_name)
            os.rename(temp_path, final_path)
            final_files[format] = final_path

        return final_files

    async def _compress_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Compress files using gzip."""
        compressed_files = {}

        for format, filepath in files.items():
            compressed_path = f"{filepath}.gz"

            await to_thread(self._gzip_file, filepath, compressed_path)

            # Remove uncompressed file
            os.unlink(filepath)
            compressed_files[format] = compressed_path

        return compressed_files

    def _gzip_file(self, source: str, dest: str) -> None:
        """Gzip a file."""
        with open(source, "rb") as f_in, gzip.open(dest, "wb") as f_out:
            f_out.writelines(f_in)

    async def _encrypt_files(self, files: Dict[str, str], password: str) -> Dict[str, str]:
        """Encrypt files (placeholder for actual encryption)."""
        # This would implement actual encryption
        # For now, just rename with .enc extension
        encrypted_files = {}

        for format, filepath in files.items():
            encrypted_path = f"{filepath}.enc"
            os.rename(filepath, encrypted_path)
            encrypted_files[format] = encrypted_path

        return encrypted_files
