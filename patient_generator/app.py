import os
import random
import datetime
import time
from .flow_simulator import PatientFlowSimulator
from .demographics import DemographicsGenerator
from .medical import MedicalConditionGenerator
from .fhir_generator import FHIRBundleGenerator
from .formatter import OutputFormatter
from collections import Counter

class PatientGeneratorApp:
    """Main application class for the patient generator"""
    
    def __init__(self, config=None):
        self.config = config or self._default_config()
        self.start_time = None
        self.phase_start_time = None
        self.total_patients = 0
    
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
    
    def run(self, progress_callback=None):
        """Run the patient generator with optional progress reporting"""
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
        
        # Report initial progress
        if progress_callback:
            progress_info = {
                "current_phase": phases[0]["name"],
                "phase_description": phases[0]["description"],
                "phase_progress": 0,
                "time_estimates": self._estimate_remaining_time(0),
                "overall_progress": 0
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
        
        # PHASE 3 & 4: Demographics and medical conditions
        current_phase = 2
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases)
        
        # Initialize the demographics generator
        demographics_generator = DemographicsGenerator()
        
        # Initialize the medical condition generator
        condition_generator = MedicalConditionGenerator()
        
        # Enhance patients with detailed demographics
        for i, patient in enumerate(patients):
            # Generate demographics
            demographics = demographics_generator.generate_person(patient.nationality, patient.gender)
            patient.set_demographics(demographics)
            
            # Update demographics progress
            if (i + 1) == len(patients) // 2:
                self._update_progress(progress_callback, current_phase, 100, phases)
                current_phase = 3
                self._start_new_phase()
                self._update_progress(progress_callback, current_phase, 0, phases)
            
            # Generate primary condition
            primary_condition = condition_generator.generate_condition(
                patient.injury_type, 
                patient.triage_category
            )
            patient.primary_condition = primary_condition
            
            # Generate additional conditions
            additional_count = 0
            if patient.triage_category == "T1":
                additional_count = random.randint(1, 2)
            elif patient.triage_category == "T2":
                additional_count = random.randint(0, 1)
                
            patient.additional_conditions = condition_generator.generate_additional_conditions(
                primary_condition, 
                additional_count
            )
            
            # Generate medications
            conditions = [primary_condition] + patient.additional_conditions
            medication_count = random.randint(1, 3) if patient.triage_category == "T1" else random.randint(0, 2)
            patient.medications = condition_generator.generate_medications(conditions, medication_count)
            
            # Generate allergies (10% chance of having allergies)
            if random.random() < 0.1:
                allergy_count = random.randint(1, 2)
                patient.allergies = condition_generator.generate_allergies(allergy_count)
            else:
                patient.allergies = []
            
            # Report medical progress
            if current_phase == 3 and i % 100 == 0:
                phase_progress = min(100, int((i / len(patients)) * 100))
                self._update_progress(progress_callback, current_phase, phase_progress, phases)
        
        self._update_progress(progress_callback, current_phase, 100, phases)
        
        # PHASE 5: Generate FHIR bundles
        current_phase = 4
        self._start_new_phase()
        self._update_progress(progress_callback, current_phase, 0, phases)
        
        bundle_generator = FHIRBundleGenerator(demographics_generator)
        bundles = []
        
        for i, patient in enumerate(patients):
            bundle = bundle_generator.create_patient_bundle(patient)
            bundles.append(bundle)
            
            # Report progress
            if i % 50 == 0:
                phase_progress = min(100, int((i / len(patients)) * 100))
                self._update_progress(progress_callback, current_phase, phase_progress, phases)
        
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
        
        summary = {
            "total_patients": len(patients),
            "nationalities": {nat: count for nat, count in nationality_counts.items()},
            "fronts": {front: count for front, count in front_counts.items()},
            "injury_types": {injury: count for injury, count in injury_counts.items()},
            "final_status": {status: count for status, count in status_counts.items()},
            "kia_count": status_counts.get("KIA", 0),
            "rtd_count": status_counts.get("RTD", 0),
            "still_in_treatment": sum(status_counts.get(status, 0) for status in ["R1", "R2", "R3", "R4"])
        }
        
        # Report completion
        if progress_callback:
            progress_info = {
                "current_phase": "Complete",
                "phase_description": "Generation process completed successfully",
                "phase_progress": 100,
                "time_estimates": {"total": 0, "phase": 0},
                "overall_progress": 100
            }
            progress_callback(100, summary, progress_info)
        
        return patients, bundles
    
    def _update_progress(self, progress_callback, current_phase_index, phase_progress, phases):
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
    patients, bundles = generator.run()
    
    # Print summary statistics
    status_counts = Counter([p.current_status for p in patients])
    print(f"\nGenerated {len(patients)} patient records:")
    print(f"  - Killed in Action (KIA): {status_counts.get('KIA', 0)}")
    print(f"  - Returned to Duty (RTD): {status_counts.get('RTD', 0)}")
    print(f"  - Still in treatment: {sum(status_counts.get(status, 0) for status in ['R1', 'R2', 'R3', 'R4'])}")
    
    print(f"\nOutput files saved to {config['output_directory']} directory.")