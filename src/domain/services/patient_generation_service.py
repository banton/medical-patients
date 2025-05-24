"""
Async patient generation service for stream-based processing.
"""
import asyncio
from typing import AsyncIterator, Optional, Callable, Tuple, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import os
import tempfile

from patient_generator.patient import Patient
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.demographics import DemographicsGenerator
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.fhir_generator import FHIRBundleGenerator
from patient_generator.formatter import OutputFormatter
from patient_generator.schemas_config import ConfigurationTemplateDB
from patient_generator.config_manager import ConfigurationManager
from patient_generator.database import Database


@dataclass
class GenerationContext:
    """Immutable context for patient generation."""
    config: ConfigurationTemplateDB
    job_id: str
    output_directory: str
    encryption_password: Optional[str] = None
    output_formats: List[str] = None
    use_compression: bool = False
    
    def __post_init__(self):
        if self.output_formats is None:
            self.output_formats = ['json']


class PatientGenerationPipeline:
    """Stream-based patient generation pipeline."""
    
    def __init__(
        self,
        flow_simulator: PatientFlowSimulator,
        demographics_generator: DemographicsGenerator,
        medical_generator: MedicalConditionGenerator,
        fhir_generator: FHIRBundleGenerator,
        output_formatter: OutputFormatter
    ):
        self.flow_simulator = flow_simulator
        self.demographics_generator = demographics_generator
        self.medical_generator = medical_generator
        self.fhir_generator = fhir_generator
        self.output_formatter = output_formatter
    
    async def generate(
        self, 
        context: GenerationContext,
        progress_callback: Optional[Callable] = None
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
            
            # Stage 4: Generate FHIR bundle
            bundle = await self._create_fhir_bundle(patient)
            
            # Yield for streaming processing
            yield patient, bundle
            
            patient_count += 1
            if progress_callback:
                await progress_callback(patient_count, context.config.total_patients)
    
    async def _initialize_generators(self, context: GenerationContext) -> None:
        """Initialize generators with configuration."""
        # This would initialize any necessary state in the generators
        # For now, we'll use the existing synchronous initialization
        pass
    
    async def _generate_base_patients(
        self, 
        context: GenerationContext
    ) -> AsyncIterator[Patient]:
        """Generate base patients in batches."""
        batch_size = min(100, context.config.total_patients)
        total = context.config.total_patients
        
        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            
            # Generate batch asynchronously
            tasks = [
                self._create_patient_async(i, context)
                for i in range(start, end)
            ]
            
            patients = await asyncio.gather(*tasks)
            
            for patient in patients:
                yield patient
    
    async def _create_patient_async(
        self, 
        patient_id: int, 
        context: GenerationContext
    ) -> Patient:
        """Create a single patient asynchronously."""
        # Create patient using the flow simulator's method
        # The flow simulator already has access to the config via config_manager
        return await asyncio.to_thread(
            self.flow_simulator.create_patient,
            patient_id
        )
    
    async def _add_demographics(
        self,
        patient: Patient,
        context: GenerationContext
    ) -> Patient:
        """Add demographics to patient asynchronously."""
        # Get nationality from patient's front
        nationality = patient.nationality_code or "USA"
        gender = "M" if patient.id % 2 == 0 else "F"  # Simple distribution
        
        # Generate demographics
        person_data = await asyncio.to_thread(
            self.demographics_generator.generate_person,
            nationality,
            gender
        )
        
        # Apply demographics to patient
        patient.first_name = person_data.get('first_name')
        patient.last_name = person_data.get('last_name')
        patient.age = person_data.get('age', 25)
        patient.gender = gender
        patient.military_id = f"MIL{patient.id:06d}"
        
        return patient
    
    async def _add_medical_conditions(
        self,
        patient: Patient,
        context: GenerationContext
    ) -> Patient:
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
        
        # Generate condition
        condition = await asyncio.to_thread(
            self.medical_generator.generate_condition,
            condition_type
        )
        
        patient.primary_injury = condition.get('name', 'Unknown Condition')
        patient.injury_type = condition_type
        patient.urgency = condition.get('urgency', 'ROUTINE')
        
        return patient
    
    async def _create_fhir_bundle(self, patient: Patient) -> Dict[str, Any]:
        """Create FHIR bundle asynchronously."""
        return await asyncio.to_thread(
            self.fhir_generator.create_bundle,
            patient
        )


class AsyncPatientGenerationService:
    """Service for managing async patient generation."""
    
    def __init__(self):
        self.pipeline = None
        self.config_manager = None
        self.db = Database()
    
    def _initialize_pipeline(self, config_id: str):
        """Initialize the generation pipeline with required components."""
        # Initialize configuration manager
        self.config_manager = ConfigurationManager(database_instance=self.db)
        self.config_manager.load_configuration(config_id)
        
        # Initialize components with config manager
        self.pipeline = PatientGenerationPipeline(
            flow_simulator=PatientFlowSimulator(self.config_manager),
            demographics_generator=DemographicsGenerator(),
            medical_generator=MedicalConditionGenerator(),
            fhir_generator=FHIRBundleGenerator(),
            output_formatter=OutputFormatter()
        )
    
    async def generate_patients(
        self,
        context: GenerationContext,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Generate patients and save to files."""
        
        # Initialize pipeline with configuration
        self._initialize_pipeline(context.config.id)
        
        # Ensure output directory exists
        os.makedirs(context.output_directory, exist_ok=True)
        
        # Initialize output files
        output_files = {}
        temp_files = {}
        
        # Create temporary files for each format
        for format in context.output_formats:
            temp_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'.{format}',
                dir=context.output_directory,
                delete=False
            )
            temp_files[format] = temp_file
            output_files[format] = temp_file.name
        
        try:
            # Stream patients and write to files
            patients = []
            bundles = []
            
            async for patient, bundle in self.pipeline.generate(context, progress_callback):
                patients.append(patient)
                bundles.append(bundle)
                
                # Write in batches of 100
                if len(patients) >= 100:
                    await self._write_batch(temp_files, patients, bundles, context)
                    patients.clear()
                    bundles.clear()
            
            # Write remaining patients
            if patients:
                await self._write_batch(temp_files, patients, bundles, context)
            
            # Close temporary files
            for temp_file in temp_files.values():
                temp_file.close()
            
            # Rename temp files to final names
            final_files = {}
            for format, temp_path in output_files.items():
                final_path = os.path.join(
                    context.output_directory,
                    f'patients.{format}'
                )
                os.rename(temp_path, final_path)
                final_files[format] = final_path
            
            # Apply compression if needed
            if context.use_compression:
                final_files = await self._compress_files(final_files)
            
            # Apply encryption if needed
            if context.encryption_password:
                final_files = await self._encrypt_files(
                    final_files,
                    context.encryption_password
                )
            
            return {
                "status": "completed",
                "output_files": list(final_files.values()),
                "patient_count": context.config.total_patients
            }
            
        except Exception as e:
            # Clean up temp files on error
            for temp_file in temp_files.values():
                if hasattr(temp_file, 'close'):
                    temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            raise e
    
    async def _write_batch(
        self,
        temp_files: Dict[str, Any],
        patients: List[Patient],
        bundles: List[Dict[str, Any]],
        context: GenerationContext
    ) -> None:
        """Write a batch of patients to files."""
        # Convert to appropriate format and write
        for format, temp_file in temp_files.items():
            if format == 'json':
                import json
                data = {
                    "patients": [p.__dict__ for p in patients],
                    "bundles": bundles
                }
                json.dump(data, temp_file, indent=2)
            elif format == 'xml':
                # Simplified XML output
                temp_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                temp_file.write('<patients>\n')
                for patient in patients:
                    temp_file.write(f'  <patient id="{patient.id}">\n')
                    temp_file.write(f'    <name>{patient.first_name} {patient.last_name}</name>\n')
                    temp_file.write(f'    <injury>{patient.primary_injury}</injury>\n')
                    temp_file.write(f'  </patient>\n')
                temp_file.write('</patients>\n')
    
    async def _compress_files(
        self,
        files: Dict[str, str]
    ) -> Dict[str, str]:
        """Compress files using gzip."""
        import gzip
        compressed_files = {}
        
        for format, filepath in files.items():
            compressed_path = f"{filepath}.gz"
            
            await asyncio.to_thread(self._gzip_file, filepath, compressed_path)
            
            # Remove uncompressed file
            os.unlink(filepath)
            compressed_files[format] = compressed_path
        
        return compressed_files
    
    def _gzip_file(self, source: str, dest: str) -> None:
        """Gzip a file."""
        with open(source, 'rb') as f_in:
            with gzip.open(dest, 'wb') as f_out:
                f_out.writelines(f_in)
    
    async def _encrypt_files(
        self,
        files: Dict[str, str],
        password: str
    ) -> Dict[str, str]:
        """Encrypt files (placeholder for actual encryption)."""
        # This would implement actual encryption
        # For now, just rename with .enc extension
        encrypted_files = {}
        
        for format, filepath in files.items():
            encrypted_path = f"{filepath}.enc"
            os.rename(filepath, encrypted_path)
            encrypted_files[format] = encrypted_path
        
        return encrypted_files