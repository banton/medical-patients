import os
import random
import datetime
import time
import concurrent.futures
import tempfile
import shutil
import atexit
import logging
from collections import Counter
from tqdm import tqdm
import multiprocessing
import psutil

# Use absolute imports instead of relative imports
try:
    # Try relative import first (when used as a package)
    from .flow_simulator import PatientFlowSimulator
    from .demographics import DemographicsGenerator
    from .medical import MedicalConditionGenerator
    from .fhir_generator import FHIRBundleGenerator
    from .formatter import OutputFormatter
except ImportError:
    # Fall back to absolute imports (when run directly)
    from patient_generator.flow_simulator import PatientFlowSimulator
    from patient_generator.demographics import DemographicsGenerator
    from patient_generator.medical import MedicalConditionGenerator
    from patient_generator.fhir_generator import FHIRBundleGenerator
    from patient_generator.formatter import OutputFormatter

class PatientGeneratorApp:
    """Main application class for the patient generator with performance optimizations"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.start_time = None
        self.phase_start_time = None
        self.total_patients = 0
        
        # Set up logging
        self.logger = logging.getLogger("PatientGeneratorApp")
        
        # Create a temp directory that will be cleaned up when the program exits
        self.temp_dir = tempfile.mkdtemp(prefix="patient_gen_app_")
        
        # Register cleanup function to ensure temp files are removed
        atexit.register(self._cleanup_temp_files)
        
        # Track all temporary files created
        self.temp_files = []
        
        # Determine optimal number of worker threads based on system resources
        self.num_workers = self._determine_worker_count()
        
        # Determine batch size based on total patients and system memory
        self.batch_size = self._determine_batch_size()
        
        # Shared generators that can be re-used across workers
        self.demographics_generator = DemographicsGenerator()
        self.condition_generator = MedicalConditionGenerator()
        
        self.logger.info(f"Initialized PatientGeneratorApp with {self.num_workers} workers and batch size {self.batch_size}")
    
    def _cleanup_temp_files(self):
        """Clean up all temporary files and the temp directory"""
        # Remove individual temp files first
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temp file {temp_file}: {e}")
        
        # Then remove the temp directory
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"Failed to remove temp directory {self.temp_dir}: {e}")
    
    def _create_temp_file(self, suffix=None):
        """Create a new temporary file and track it for cleanup"""
        fd, temp_path = tempfile.mkstemp(dir=self.temp_dir, suffix=suffix)
        os.close(fd)  # Close the file descriptor
        self.temp_files.append(temp_path)
        return temp_path
    
    def _determine_worker_count(self):
        """Determine optimal number of worker threads based on system resources"""
        # Check if explicitly set in configuration
        if self.config.get("performance", {}).get("num_workers"):
            return self.config["performance"]["num_workers"]
        
        # Check environment variable
        env_threads = os.environ.get("PATIENT_GENERATOR_THREADS")
        if env_threads and env_threads.isdigit():
            return int(env_threads)
        
        # Auto-detect based on CPU count
        try:
            cpu_count = multiprocessing.cpu_count()
            # Use 75% of available CPUs, but at least 2 and at most 8
            return min(8, max(2, int(cpu_count * 0.75)))
        except:
            # Default if detection fails
            return 4
    
    def _determine_batch_size(self):
        """Determine optimal batch size based on available memory and total patients"""
        # Check if explicitly set in configuration
        if self.config.get("performance", {}).get("batch_size"):
            return self.config["performance"]["batch_size"]
        
        total_patients = self.config.get('total_patients', 1440)
        
        # Check environment variable for max memory
        env_max_memory = os.environ.get("PATIENT_GENERATOR_MAX_MEMORY")
        max_memory_mb = None
        if env_max_memory and env_max_memory.isdigit():
            max_memory_mb = int(env_max_memory)
        elif self.config.get("performance", {}).get("max_memory_mb"):
            max_memory_mb = self.config["performance"]["max_memory_mb"]
        
        # Get available memory in bytes
        try:
            # If max memory is set, use that as the limit
            if max_memory_mb:
                available_memory = max_memory_mb * 1024 * 1024
            else:
                # Otherwise use 50% of available system memory
                available_memory = psutil.virtual_memory().available * 0.5
        except:
            # Default to 1GB if detection fails
            available_memory = 1024 * 1024 * 1024
        
        # Estimate memory per patient (conservative estimate: 50KB per patient)
        estimated_memory_per_patient = 50 * 1024
        
        # Calculate batch size based on available memory
        memory_based_batch_size = int(available_memory / estimated_memory_per_patient)
        
        # Cap batch size to reasonable limits
        min_batch_size = 50
        max_batch_size = 500
        
        # Use smaller batches for more workers to improve load balancing
        worker_adjusted_size = max(min_batch_size, int(total_patients / (self.num_workers * 2)))
        
        # Final batch size is minimum of memory-based and worker-adjusted size, capped at max_batch_size
        batch_size = min(memory_based_batch_size, worker_adjusted_size, max_batch_size)
        
        return batch_size
    
    def _default_config(self):
        """Create default configuration"""
        return {
            "total_patients": 1440,
            "front_distribution": {
                "Polish": 0.50,    # 50% of casualties from Polish front
                "Estonian": 0.333, # 33.3% of casualties from Estonian front
                "Finnish": 0.167   # 16.7% of casualties from Finnish front
            },
            "nationality_distribution": {
                "Polish": {
                    "POL": 0.50,
                    "GBR": 0.10,
                    "LIT": 0.30,
                    "USA": 0.05,
                    "ESP": 0.05
                },
                "Estonian": {
                    "EST": 0.70,
                    "GBR": 0.30
                },
                "Finnish": {
                    "FIN": 0.40,
                    "USA": 0.60
                }
            },
            "injury_distribution": {
                "DISEASE": 0.52,
                "NON_BATTLE": 0.33,
                "BATTLE_TRAUMA": 0.15
            },
            "encryption_key": os.urandom(32),  # Generate a random encryption key
            "output_formats": ["json", "xml"],
            "output_directory": "output",
            "base_date": "2025-06-01",  # Base date for the exercise
            "use_compression": True,
            "use_encryption": True
        }
    
    def _estimate_remaining_time(self, progress_percent, phase_progress=None):
        """Estimate remaining time for current phase and overall process"""
        now = time.time()
        elapsed_total = now - self.start_time
        
        if progress_percent <= 0:
            return {"total": None, "phase": None}
        
        # Estimate total remaining time
        total_remaining = (elapsed_total / progress_percent) * (100 - progress_percent)
        
        # Estimate phase remaining time if phase_progress is provided
        phase_remaining = None
        if phase_progress is not None and phase_progress > 0:
            elapsed_phase = now - self.phase_start_time
            phase_remaining = (elapsed_phase / phase_progress) * (100 - phase_progress)
            
        return {
            "total": int(total_remaining),
            "phase": int(phase_remaining) if phase_remaining is not None else None
        }
    
    def _start_new_phase(self):
        """Reset the phase timer for a new processing phase"""
        self.phase_start_time = time.time()
    
    def _process_patient_batch(self, patients, phase):
        """Process a batch of patients for enhanced demographics and medical conditions"""
        # Process each patient in the batch
        for patient in patients:
            if phase == "demographics":
                # Generate demographics
                demographics = self.demographics_generator.generate_person(patient.nationality, patient.gender)
                patient.set_demographics(demographics)
            
            elif phase == "medical":
                # Determine if the patient should have multiple conditions
                # More severe triage categories and battle trauma are more likely to have multiple conditions
                multiple_conditions_chance = 0.0
                
                if patient.triage_category == "T1":
                    multiple_conditions_chance = 0.7  # 70% chance for T1
                elif patient.triage_category == "T2":
                    multiple_conditions_chance = 0.4  # 40% chance for T2
                elif patient.triage_category == "T3":
                    multiple_conditions_chance = 0.2  # 20% chance for T3
                
                # Increase chance for battle trauma
                if patient.injury_type == "BATTLE_TRAUMA":
                    multiple_conditions_chance += 0.2
                
                # Generate conditions
                if random.random() < multiple_conditions_chance:
                    # Generate 2-3 conditions of the same injury type
                    condition_count = random.randint(2, 3)
                    primary_conditions = self.condition_generator.generate_multiple_conditions(
                        patient.injury_type, 
                        patient.triage_category,
                        condition_count
                    )
                    patient.primary_conditions = primary_conditions
                    # Set the first one as the primary for backward compatibility
                    patient.primary_condition = primary_conditions[0] if primary_conditions else None
                else:
                    # Generate a single primary condition (existing behavior)
                    primary_condition = self.condition_generator.generate_condition(
                        patient.injury_type, 
                        patient.triage_category
                    )
                    patient.primary_condition = primary_condition
                    patient.primary_conditions = [primary_condition] if primary_condition else []
                
                # Generate additional conditions (potentially from other categories)
                additional_count = 0
                if patient.triage_category == "T1":
                    additional_count = random.randint(1, 2)
                elif patient.triage_category == "T2":
                    additional_count = random.randint(0, 1)
                    
                if patient.primary_condition:  # Ensure we have at least one primary condition
                    patient.additional_conditions = self.condition_generator.generate_additional_conditions(
                        patient.primary_condition, 
                        additional_count
                    )
                else:
                    patient.additional_conditions = []
                
                # Generate medications
                conditions = patient.primary_conditions + patient.additional_conditions
                medication_count = random.randint(1, 3) if patient.triage_category == "T1" else random.randint(0, 2)
                patient.medications = self.condition_generator.generate_medications(conditions, medication_count)
                
                # Generate allergies (10% chance of having allergies)
                if random.random() < 0.1:
                    allergy_count = random.randint(1, 2)
                    patient.allergies = self.condition_generator.generate_allergies(allergy_count)
                else:
                    patient.allergies = []
        
        return patients
    
    def _create_fhir_bundles_batch(self, patients):
        """Create FHIR bundles for a batch of patients"""
        bundle_generator = FHIRBundleGenerator(self.demographics_generator)
        return [bundle_generator.create_patient_bundle(patient) for patient in patients]
    
    def run(self, progress_callback=None):
        """Run the patient generator with parallel processing and performance optimizations"""
        self.start_time = time.time()
        self.phase_start_time = time.time()
        self.total_patients = self.config['total_patients']
        
        # Define phases with their relative weights for progress calculation
        phases = [
            {"name": "Initializing", "weight": 5, "description": "Setting up simulation environment"},
            {"name": "Generating Patient Flow", "weight": 15, "description": "Simulating casualty flow through treatment facilities"},
            {"name": "Creating Demographics", "weight": 20, "description": "Generating patient personal information"},
            {"name": "Adding Medical Conditions", "weight": 15, "description": "Adding realistic medical conditions and treatments"},
            {"name": "Creating FHIR Bundles", "weight": 25, "description": "Converting to HL7 FHIR format"},
            {"name": "Formatting Output", "weight": 10, "description": "Preparing JSON and XML files"},
            {"name": "Compressing Data", "weight": 5, "description": "Applying compression to output files"},
            {"name": "Encrypting Data", "weight": 5, "description": "Securing data with AES-256-GCM encryption"}
        ]
        
        # Calculate cumulative weights for progress tracking
        cumulative_weight = 0
        for phase in phases:
            phase["start_progress"] = cumulative_weight
            cumulative_weight += phase["weight"]
            phase["end_progress"] = cumulative_weight
        
        # Report initial progress with system configuration details
        if progress_callback:
            system_info = {
                "workers": self.num_workers,
                "batch_size": self.batch_size,
                "available_memory": f"{psutil.virtual_memory().available / (1024**3):.2f} GB"
            }
            
            progress_info = {
                "current_phase": phases[0]["name"],
                "phase_description": phases[0]["description"],
                "phase_progress": 0,
                "time_estimates": self._estimate_remaining_time(0),
                "overall_progress": 0,
                "system_info": system_info,
                "total_patients": self.total_patients
            }
            progress_callback(0, progress_info)
        
        # PHASE 1: Initialization
        current_phase = 0
        self._update_progress(progress_callback, current_phase, 50, phases)
        
        # Initialize the patient flow simulator
        flow_simulator = PatientFlowSimulator(self.config)
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 2: Generate patient flow
        current_phase = 1
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases)
        
        # Generate patient flow
        patients = flow_simulator.generate_casualty_flow(self.total_patients)
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 3: Demographics processing with parallelization
        current_phase = 2
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases, {"processed_patients": 0})
        
        # Process patients in batches using multiple threads
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split patients into batches
            patient_batches = [patients[i:i + self.batch_size] for i in range(0, len(patients), self.batch_size)]
            
            # Submit demographics processing jobs
            future_to_batch = {
                executor.submit(self._process_patient_batch, batch, "demographics"): batch 
                for batch in patient_batches
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    processed_batch = future.result()
                    # Update progress
                    processed_count += len(processed_batch)
                    phase_progress = min(100, int((processed_count / len(patients)) * 100))
                    self._update_progress(
                        progress_callback, 
                        current_phase, 
                        phase_progress, 
                        phases,
                        {"processed_patients": processed_count}
                    )
                except Exception as e:
                    print(f"Demographics generation error: {e}")
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 4: Medical condition processing with parallelization
        current_phase = 3
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases, {"processed_patients": 0})
        
        # Process medical conditions in batches
        processed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split patients into batches
            patient_batches = [patients[i:i + self.batch_size] for i in range(0, len(patients), self.batch_size)]
            
            # Submit medical condition processing jobs
            future_to_batch = {
                executor.submit(self._process_patient_batch, batch, "medical"): batch 
                for batch in patient_batches
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    processed_batch = future.result()
                    # Update progress
                    processed_count += len(processed_batch)
                    phase_progress = min(100, int((processed_count / len(patients)) * 100))
                    self._update_progress(
                        progress_callback, 
                        current_phase, 
                        phase_progress, 
                        phases,
                        {"processed_patients": processed_count}
                    )
                except Exception as e:
                    print(f"Medical condition generation error: {e}")
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 5: Generate FHIR bundles with parallelization
        current_phase = 4
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases, {"processed_patients": 0})
        
        # Process FHIR bundles in batches
        bundles = []
        processed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split patients into batches
            patient_batches = [patients[i:i + self.batch_size] for i in range(0, len(patients), self.batch_size)]
            
            # Submit FHIR bundle creation jobs
            future_to_batch = {
                executor.submit(self._create_fhir_bundles_batch, batch): batch 
                for batch in patient_batches
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                try:
                    batch_bundles = future.result()
                    bundles.extend(batch_bundles)
                    
                    # Update progress
                    processed_count += len(batch)
                    phase_progress = min(100, int((processed_count / len(patients)) * 100))
                    self._update_progress(
                        progress_callback, 
                        current_phase, 
                        phase_progress, 
                        phases,
                        {"processed_patients": processed_count}
                    )
                except Exception as e:
                    print(f"FHIR bundle creation error: {e}")
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 6: Format outputs
        current_phase = 5
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases)
        
        formatter = OutputFormatter()
        
        # Progress updates for formatting phase
        self._update_progress(progress_callback, current_phase, 50, phases)
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 7: Compression (if enabled)
        if self.config.get("use_compression", True):
            current_phase = 6
            self._start_new_phase()
            self._update_progress(progress_callback, current_phase, 0, phases)
            self._update_progress(progress_callback, current_phase, 50, phases)
            self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 8: Encryption (if enabled)
        if self.config.get("use_encryption", True):
            current_phase = 7
            self._start_new_phase()
            self._update_progress(progress_callback, current_phase, 0, phases)
            self._update_progress(progress_callback, current_phase, 50, phases)
        
        # Create output files (combines formatting, compression, and encryption)
        # Use memory-efficient chunked processing for large datasets
        if len(bundles) > 1000:
            # Process large datasets in chunks to reduce memory pressure
            chunk_size = min(500, max(100, len(bundles) // 10))
            output_files = []
            
            # Process chunks 
            for i in range(0, len(bundles), chunk_size):
                chunk = bundles[i:i + chunk_size]
                chunk_files = formatter.create_output_files(
                    chunk,
                    self.config["output_directory"],
                    formats=self.config.get("output_formats", ["json", "xml"]),
                    use_compression=self.config.get("use_compression", True),
                    use_encryption=self.config.get("use_encryption", True),
                    encryption_key=self.config.get("encryption_key"),
                    is_chunk=(i > 0),  # Flag subsequent chunks
                    chunk_index=i // chunk_size
                )
                output_files.extend(chunk_files)
        else:
            # For smaller datasets, process all at once
            output_files = formatter.create_output_files(
                bundles,
                self.config["output_directory"],
                formats=self.config.get("output_formats", ["json", "xml"]),
                use_compression=self.config.get("use_compression", True),
                use_encryption=self.config.get("use_encryption", True),
                encryption_key=self.config.get("encryption_key")
            )
        
        if self.config.get("use_encryption", True):
            self._update_progress(progress_callback, current_phase, 100, phases)
        
        # Create final summary
        nationality_counts = Counter([p.nationality for p in patients])
        front_counts = Counter([p.front for p in patients])
        injury_counts = Counter([p.injury_type for p in patients])
        status_counts = Counter([p.current_status for p in patients])
        
        # Calculate performance metrics
        total_time = time.time() - self.start_time
        patients_per_second = len(patients) / total_time if total_time > 0 else 0
        
        summary = {
            "total_patients": len(patients),
            "nationalities": {nat: count for nat, count in nationality_counts.items()},
            "fronts": {front: count for front, count in front_counts.items()},
            "injury_types": {injury: count for injury, count in injury_counts.items()},
            "final_status": {status: count for status, count in status_counts.items()},
            "kia_count": status_counts.get("KIA", 0),
            "rtd_count": status_counts.get("RTD", 0),
            "still_in_treatment": sum(status_counts.get(status, 0) for status in ["R1", "R2", "R3", "R4"]),
            "performance": {
                "total_time_seconds": round(total_time, 2),
                "patients_per_second": round(patients_per_second, 2),
                "thread_count": self.num_workers,
                "batch_size": self.batch_size
            }
        }
        
        # Report completion
        if progress_callback:
            progress_info = {
                "current_phase": "Complete",
                "phase_description": "Generation process completed successfully",
                "phase_progress": 100,
                "time_estimates": {"total": 0, "phase": 0},
                "overall_progress": 100,
                "performance": summary["performance"]
            }
            progress_callback(100, summary, progress_info)
        
        return patients, bundles
    
    def _update_progress(self, progress_callback, current_phase_index, phase_progress, phases, extra_info=None):
        """Update progress with detailed information about the current phase"""
        if not progress_callback:
            return
            
        current_phase = phases[current_phase_index]
        
        # Calculate overall progress based on phase weights
        phase_contribution = ((phase_progress / 100) * current_phase["weight"])
        overall_progress = current_phase["start_progress"] + phase_contribution
        
        # Format progress to integer
        overall_progress = int(overall_progress)
        
        # Create progress information dictionary
        progress_info = {
            "current_phase": current_phase["name"],
            "phase_description": current_phase["description"],
            "phase_progress": phase_progress,
            "time_estimates": self._estimate_remaining_time(overall_progress, phase_progress),
            "overall_progress": overall_progress
        }
        
        # Add patient count info
        if current_phase_index >= 1:
            progress_info["total_patients"] = self.total_patients
        
        # Add any extra information
        if extra_info:
            progress_info.update(extra_info)
        
        # Call the progress callback
        progress_callback(overall_progress, progress_info)

if __name__ == "__main__":
    # Simple command-line usage example
    import sys
    
    print("Military Medical Exercise Patient Generator")
    print("------------------------------------------")
    
    # Default configuration
    config = {
        "total_patients": 1440,
        "output_directory": "output",
        "output_formats": ["json", "xml"],
        "use_compression": True,
        "use_encryption": True
    }
    
    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        try:
            config["total_patients"] = int(sys.argv[1])
        except ValueError:
            print(f"Invalid patient count: {sys.argv[1]}")
            sys.exit(1)
    
    # Initialize and run the generator
    print(f"Generating {config['total_patients']} patients...")
    generator = PatientGeneratorApp(config)
    
    print(f"Using {generator.num_workers} worker threads with batch size of {generator.batch_size}")
    
    start_time = time.time()
    patients, bundles = generator.run()
    end_time = time.time()
    
    # Print summary statistics
    status_counts = Counter([p.current_status for p in patients])
    print(f"\nGenerated {len(patients)} patient records:")
    print(f"  - Killed in Action (KIA): {status_counts.get('KIA', 0)}")
    print(f"  - Returned to Duty (RTD): {status_counts.get('RTD', 0)}")
    print(f"  - Still in treatment: {sum(status_counts.get(status, 0) for status in ['R1', 'R2', 'R3', 'R4'])}")
    
    # Print performance metrics
    total_time = end_time - start_time
    print(f"\nPerformance metrics:")
    print(f"  - Total generation time: {total_time:.2f} seconds")
    print(f"  - Patients per second: {len(patients) / total_time:.2f}")
    print(f"  - Worker threads: {generator.num_workers}")
    print(f"  - Batch size: {generator.batch_size}")
    
    print(f"\nOutput files saved to {config['output_directory']} directory.")
