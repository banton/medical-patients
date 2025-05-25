import atexit
from collections import Counter
import concurrent.futures
import logging

# from tqdm import tqdm # tqdm might be for CLI, not library use directly unless for debug
import multiprocessing
import os
import random
import shutil
import tempfile
import time
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional  # Added Callable for progress_callback

import psutil

if TYPE_CHECKING:
    from patient_generator.schemas_config import ConfigurationTemplateDB

    from .schemas_config import ConfigurationTemplateDB

# Use absolute imports
try:
    from .config_manager import ConfigurationManager  # New import
    from .demographics import DemographicsGenerator
    from .fhir_generator import FHIRBundleGenerator
    from .flow_simulator import PatientFlowSimulator
    from .formatter import OutputFormatter
    from .medical import MedicalConditionGenerator
    from .nationality_data import NationalityDataProvider  # New import
except ImportError:
    from patient_generator.config_manager import ConfigurationManager
    from patient_generator.demographics import DemographicsGenerator
    from patient_generator.fhir_generator import FHIRBundleGenerator
    from patient_generator.flow_simulator import PatientFlowSimulator
    from patient_generator.formatter import OutputFormatter
    from patient_generator.medical import MedicalConditionGenerator
    from patient_generator.nationality_data import NationalityDataProvider


class PatientGeneratorApp:
    """Main application class for the patient generator using ConfigurationManager."""

    def __init__(
        self, config_manager: ConfigurationManager, nationality_provider: Optional[NationalityDataProvider] = None
    ):
        self.config_manager = config_manager
        self.active_config: Optional[ConfigurationTemplateDB] = self.config_manager.get_active_configuration()

        if not self.active_config:
            msg = "PatientGeneratorApp requires an active configuration to be loaded in ConfigurationManager."
            raise ValueError(msg)

        self.start_time: Optional[float] = None
        self.phase_start_time: Optional[float] = None
        self.total_patients: int = self.active_config.total_patients

        self.logger = logging.getLogger("PatientGeneratorApp")
        self.temp_dir = tempfile.mkdtemp(prefix="patient_gen_app_")
        atexit.register(self._cleanup_temp_files)
        self.temp_files: List[str] = []

        # Performance settings (can be overridden by env vars or future config options)
        # For now, keep determination logic, but it could also be part of ConfigurationTemplate
        self.num_workers: int = self._determine_worker_count()
        self.batch_size: int = self._determine_batch_size()  # Depends on total_patients

        # Shared generators
        self.nationality_provider = nationality_provider or NationalityDataProvider()
        self.demographics_generator = DemographicsGenerator()  # Removed nationality_provider argument
        self.condition_generator = MedicalConditionGenerator()

        # Initialize FlowSimulator with the ConfigManager
        self.flow_simulator = PatientFlowSimulator(self.config_manager)

        self.logger.info(
            f"Initialized PatientGeneratorApp with {self.num_workers} workers, batch size {self.batch_size} for {self.total_patients} patients."
        )

    def _cleanup_temp_files(self):
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Failed to remove temp directory {self.temp_dir}: {e}")

    def _create_temp_file(self, suffix=None) -> str:
        fd, temp_path = tempfile.mkstemp(dir=self.temp_dir, suffix=suffix)
        os.close(fd)
        self.temp_files.append(temp_path)
        return temp_path

    def _determine_worker_count(self) -> int:
        # TODO: Potentially make this part of ConfigurationTemplate or app-level settings via API
        env_threads = os.environ.get("PATIENT_GENERATOR_THREADS")
        if env_threads and env_threads.isdigit():
            return int(env_threads)
        try:
            cpu_count = multiprocessing.cpu_count()
            return min(8, max(2, int(cpu_count * 0.75)))
        except:
            return 4

    def _determine_batch_size(self) -> int:
        # TODO: Potentially make this part of ConfigurationTemplate
        env_max_memory = os.environ.get("PATIENT_GENERATOR_MAX_MEMORY")
        max_memory_mb = int(env_max_memory) if env_max_memory and env_max_memory.isdigit() else None

        try:
            available_memory = (
                (max_memory_mb * 1024 * 1024) if max_memory_mb else (psutil.virtual_memory().available * 0.5)
            )
        except:
            available_memory = 1024 * 1024 * 1024  # 1GB default

        estimated_memory_per_patient = 50 * 1024  # 50KB
        memory_based_batch_size = int(available_memory / estimated_memory_per_patient)
        worker_adjusted_size = max(50, int(self.total_patients / (self.num_workers * 2)))
        return min(memory_based_batch_size, worker_adjusted_size, 500)  # Cap at 500

    # _default_config method is removed as config comes from ConfigurationManager

    def _estimate_remaining_time(
        self, progress_percent: float, phase_progress: Optional[float] = None
    ) -> Dict[str, Optional[int]]:
        if self.start_time is None or self.phase_start_time is None:
            return {"total": None, "phase": None}
        now = time.time()
        elapsed_total = now - self.start_time
        if progress_percent <= 0:
            return {"total": None, "phase": None}
        total_remaining = (elapsed_total / progress_percent) * (100 - progress_percent)
        phase_remaining = None
        if phase_progress is not None and phase_progress > 0:
            elapsed_phase = now - self.phase_start_time
            phase_remaining = (elapsed_phase / phase_progress) * (100 - phase_progress)
        return {"total": int(total_remaining), "phase": int(phase_remaining) if phase_remaining is not None else None}

    def _start_new_phase(self):
        self.phase_start_time = time.time()

    def _process_patient_batch(self, patients: List[Any], phase: str) -> List[Any]:  # Patient type hint
        for patient in patients:
            if phase == "demographics":
                demographics = self.demographics_generator.generate_person(patient.nationality, patient.gender)
                patient.set_demographics(demographics)
            elif phase == "medical":
                multiple_conditions_chance = 0.0
                if patient.triage_category == "T1":
                    multiple_conditions_chance = 0.7
                elif patient.triage_category == "T2":
                    multiple_conditions_chance = 0.4
                elif patient.triage_category == "T3":
                    multiple_conditions_chance = 0.2
                if patient.injury_type == "BATTLE_TRAUMA":
                    multiple_conditions_chance += 0.2

                if random.random() < multiple_conditions_chance:
                    condition_count = random.randint(2, 3)
                    primary_conditions = self.condition_generator.generate_multiple_conditions(
                        patient.injury_type, patient.triage_category, condition_count
                    )
                    patient.primary_conditions = primary_conditions
                    patient.primary_condition = primary_conditions[0] if primary_conditions else None
                else:
                    primary_condition = self.condition_generator.generate_condition(
                        patient.injury_type, patient.triage_category
                    )
                    patient.primary_condition = primary_condition
                    patient.primary_conditions = [primary_condition] if primary_condition else []

                additional_count = 0
                if patient.triage_category == "T1":
                    additional_count = random.randint(1, 2)
                elif patient.triage_category == "T2":
                    additional_count = random.randint(0, 1)

                if patient.primary_condition:
                    patient.additional_conditions = self.condition_generator.generate_additional_conditions(
                        patient.primary_condition, additional_count
                    )
                else:
                    patient.additional_conditions = []

                conditions = patient.primary_conditions + patient.additional_conditions
                medication_count = random.randint(1, 3) if patient.triage_category == "T1" else random.randint(0, 2)
                patient.medications = self.condition_generator.generate_medications(conditions, medication_count)

                patient.allergies = (
                    self.condition_generator.generate_allergies(random.randint(0, 1)) if random.random() < 0.1 else []
                )
        return patients

    def _create_fhir_bundles_batch(self, patients: List[Any]) -> List[Any]:  # Patient type hint
        bundle_generator = FHIRBundleGenerator(
            self.demographics_generator
        )  # Demographics generator might need nationality provider too
        return [bundle_generator.create_patient_bundle(patient) for patient in patients]

    def run(
        self,
        output_directory: str = "output",
        output_formats: Optional[List[str]] = None,
        use_compression: bool = True,
        use_encryption: bool = True,
        encryption_password: Optional[str] = None,  # Changed from encryption_key: Optional[bytes]
        progress_callback: Optional[Callable[[int, Dict[str, Any]], None]] = None,
    ) -> tuple[List[Any], List[Any], List[str], Dict[str, Any]]:  # patients, bundles, output_files, summary
        self.start_time = time.time()
        self.phase_start_time = time.time()
        # total_patients is already set from active_config in __init__

        # Runtime output parameters
        final_output_formats = output_formats if output_formats is not None else ["json", "xml"]
        # The OutputFormatter now expects a string password for key derivation.
        # If use_encryption is True but no password is provided, encryption will be skipped by OutputFormatter.
        final_encryption_password = encryption_password

        phases = [
            {"name": "Initializing", "weight": 5, "description": "Setting up simulation environment"},
            {"name": "Generating Patient Flow", "weight": 15, "description": "Simulating casualty flow"},
            {"name": "Creating Demographics", "weight": 20, "description": "Generating patient personal info"},
            {"name": "Adding Medical Conditions", "weight": 15, "description": "Adding medical conditions"},
            {"name": "Creating FHIR Bundles", "weight": 25, "description": "Converting to HL7 FHIR"},
            {"name": "Formatting Output", "weight": 10, "description": "Preparing output files"},
            {"name": "Compressing Data", "weight": 5, "description": "Compressing files"},
            {"name": "Encrypting Data", "weight": 5, "description": "Encrypting files"},
        ]
        cumulative_weight = 0
        for phase in phases:
            phase["start_progress"] = cumulative_weight
            cumulative_weight += phase["weight"]
            phase["end_progress"] = cumulative_weight

        if progress_callback:
            system_info = {
                "workers": self.num_workers,
                "batch_size": self.batch_size,
                "available_memory": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
            }
            progress_info: Dict[str, Any] = {
                "current_phase": phases[0]["name"],
                "phase_description": phases[0]["description"],
                "phase_progress": 0,
                "time_estimates": self._estimate_remaining_time(0),
                "overall_progress": 0,
                "system_info": system_info,
                "total_patients": self.total_patients,
            }
            progress_callback(0, progress_info)

        current_phase_idx = 0  # Initializing
        self._update_progress(progress_callback, current_phase_idx, 50, phases)
        # flow_simulator already initialized in __init__
        self._update_progress(progress_callback, current_phase_idx, 100, phases)

        current_phase_idx = 1  # Generating Patient Flow
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase_idx, 0, phases)
        patients = self.flow_simulator.generate_casualty_flow()  # Uses total_patients from config
        self._update_progress(progress_callback, current_phase_idx, 100, phases)

        # Subsequent phases (Demographics, Medical, FHIR, Output)
        for i, phase_name in enumerate(["demographics", "medical"]):
            current_phase_idx = i + 2  # Starts from index 2
            self._start_new_phase()
            self._update_progress(progress_callback, current_phase_idx, 0, phases, {"processed_patients": 0})
            processed_count = 0
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                patient_batches = [patients[j : j + self.batch_size] for j in range(0, len(patients), self.batch_size)]
                future_to_batch = {
                    executor.submit(self._process_patient_batch, batch, phase_name): batch for batch in patient_batches
                }
                for future in concurrent.futures.as_completed(future_to_batch):
                    try:
                        processed_batch = future.result()
                        processed_count += len(processed_batch)
                        phase_prog = min(100, int((processed_count / len(patients)) * 100))
                        self._update_progress(
                            progress_callback,
                            current_phase_idx,
                            phase_prog,
                            phases,
                            {"processed_patients": processed_count},
                        )
                    except Exception as e:
                        self.logger.error(f"Error in phase '{phase_name}': {e}")
            self._update_progress(progress_callback, current_phase_idx, 100, phases)

        current_phase_idx = 4  # Creating FHIR Bundles
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase_idx, 0, phases, {"processed_patients": 0})
        bundles: List[Any] = []
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            patient_batches = [patients[j : j + self.batch_size] for j in range(0, len(patients), self.batch_size)]
            future_to_batch = {
                executor.submit(self._create_fhir_bundles_batch, batch): batch for batch in patient_batches
            }
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    batch_bundles = future.result()
                    bundles.extend(batch_bundles)
                    processed_count += len(future_to_batch[future])  # length of original patient batch
                    phase_prog = min(100, int((processed_count / len(patients)) * 100))
                    self._update_progress(
                        progress_callback,
                        current_phase_idx,
                        phase_prog,
                        phases,
                        {"processed_patients": processed_count},
                    )
                except Exception as e:
                    self.logger.error(f"FHIR bundle creation error: {e}")
        self._update_progress(progress_callback, current_phase_idx, 100, phases)

        formatter = OutputFormatter()
        # Output phase combines formatting, compression, encryption
        output_phase_start_index = 5

        # For simplicity, group these into one progress update block
        self._update_progress(progress_callback, output_phase_start_index, 0, phases)  # Start Formatting

        output_files = formatter.create_output_files(
            bundles,
            output_directory,
            formats=final_output_formats,
            use_compression=use_compression,
            use_encryption=use_encryption,
            encryption_password=final_encryption_password,  # Changed from encryption_key
            # temp_dir_provider is not a parameter of formatter.create_output_files
            # The OutputFormatter manages its own temp files.
        )
        self._update_progress(progress_callback, output_phase_start_index, 100, phases)  # End Formatting
        if use_compression:
            self._update_progress(progress_callback, output_phase_start_index + 1, 100, phases)  # End Compression
        if use_encryption:
            self._update_progress(progress_callback, output_phase_start_index + 2, 100, phases)  # End Encryption

        # Final summary
        nationality_counts = Counter([p.nationality for p in patients])
        front_counts = Counter([p.front for p in patients])
        injury_counts = Counter([p.injury_type for p in patients])
        status_counts = Counter([p.current_status for p in patients])
        total_time_val = time.time() - (self.start_time or time.time())

        summary = {
            "total_patients": len(patients),
            "nationalities": dict(nationality_counts),
            "fronts": dict(front_counts),
            "injury_types": dict(injury_counts),
            "final_status": dict(status_counts),
            "kia_count": status_counts.get("KIA", 0),
            "rtd_count": status_counts.get("RTD", 0),
            "still_in_treatment": sum(
                status_counts.get(s, 0)
                for s in self.flow_simulator._transition_probabilities
                if s not in ["POI", "KIA", "RTD"]
            ),
            "performance": {
                "total_time_seconds": round(total_time_val, 2),
                "patients_per_second": round(len(patients) / total_time_val if total_time_val > 0 else 0, 2),
                "thread_count": self.num_workers,
                "batch_size": self.batch_size,
            },
        }
        if progress_callback:
            progress_info_final: Dict[str, Any] = {
                "current_phase": "Complete",
                "phase_description": "Generation process completed",
                "phase_progress": 100,
                "time_estimates": {"total": 0, "phase": 0},
                "overall_progress": 100,
                "performance": summary["performance"],
                "summary": summary,
            }  # Add summary to details
            progress_callback(100, progress_info_final)

        return patients, bundles, output_files, summary

    def _update_progress(
        self,
        progress_callback: Optional[Callable[[int, Dict[str, Any]], None]],
        current_phase_index: int,
        phase_progress: int,
        phases: List[Dict[str, Any]],
        extra_info: Optional[Dict[str, Any]] = None,
    ):
        if not progress_callback or self.start_time is None:
            return
        current_phase_def = phases[current_phase_index]
        phase_contribution = (phase_progress / 100.0) * current_phase_def["weight"]
        overall_progress = int(current_phase_def["start_progress"] + phase_contribution)

        progress_data: Dict[str, Any] = {
            "current_phase": current_phase_def["name"],
            "phase_description": current_phase_def["description"],
            "phase_progress": phase_progress,
            "time_estimates": self._estimate_remaining_time(overall_progress, phase_progress),
            "overall_progress": overall_progress,
            "total_patients": self.total_patients,
        }
        if extra_info:
            progress_data.update(extra_info)

        # The callback for FastAPI app expects (overall_progress, summary_dict, progress_details_dict)
        # Here, we are calling it with (overall_progress, progress_details_dict)
        # The main app.py will need to adapt how it calls this or how it uses the callback.
        # For now, let's assume the callback signature is flexible or this is an internal callback.
        # If this is the job_progress_callback from main app.py, it expects (job_id, overall_progress, summary, details)
        # This internal _update_progress is simpler.

        # Let's make the callback expect (overall_progress: int, details: Dict[str, Any])
        progress_callback(overall_progress, progress_data)


# Example main removed as this is a library class.
# Instantiation and run will be handled by the main FastAPI app (app.py)
