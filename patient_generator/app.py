import os
import random
import datetime
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
    
    def run(self, progress_callback=None):
        """Run the patient generator with optional progress reporting"""
        total_patients = self.config['total_patients']
        
        # Report initial progress
        if progress_callback:
            progress_callback(0)
        
        # Initialize the patient flow simulator
        flow_simulator = PatientFlowSimulator(self.config)
        
        # Generate patient flow (20% of progress)
        patients = flow_simulator.generate_casualty_flow(total_patients)
        if progress_callback:
            progress_callback(20)
        
        # Initialize the demographics generator
        demographics_generator = DemographicsGenerator()
        
        # Initialize the medical condition generator
        condition_generator = MedicalConditionGenerator()
        
        # Enhance patients with detailed demographics and conditions (30% of progress)
        for i, patient in enumerate(patients):
            # Generate demographics
            demographics = demographics_generator.generate_person(patient.nationality, patient.gender)
            patient.set_demographics(demographics)
            
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
            
            # Report progress and patient data summary periodically
            if progress_callback and i % 100 == 0:
                progress = 20 + int((i / total_patients) * 30)
                
                # Create a summary of current patient data
                nationality_counts = Counter([p.nationality for p in patients[:i+1]])
                front_counts = Counter([p.front for p in patients[:i+1]])
                injury_counts = Counter([p.injury_type for p in patients[:i+1]])
                status_counts = Counter([p.current_status for p in patients[:i+1]])
                
                patient_data = {
                    "processed_patients": i + 1,
                    "total_patients": total_patients,
                    "nationalities": {nat: count for nat, count in nationality_counts.items()},
                    "fronts": {front: count for front, count in front_counts.items()},
                    "injury_types": {injury: count for injury, count in injury_counts.items()},
                    "status": {status: count for status, count in status_counts.items()}
                }
                
                progress_callback(min(50, progress), patient_data)
        
        # Generate FHIR bundles (40% of progress)
        bundle_generator = FHIRBundleGenerator(demographics_generator)
        bundles = []
        
        for i, patient in enumerate(patients):
            bundle = bundle_generator.create_patient_bundle(patient)
            bundles.append(bundle)
            
            # Report progress
            if progress_callback and i % 100 == 0:
                progress = 50 + int((i / total_patients) * 40)
                progress_callback(min(90, progress))
        
        # Format outputs (final 10% of progress)
        formatter = OutputFormatter()
        
        # Create output files
        output_files = formatter.create_output_files(
            bundles,
            self.config["output_directory"],
            formats=self.config.get("output_formats", ["json", "xml"]),
            use_compression=self.config.get("use_compression", True),
            use_encryption=self.config.get("use_encryption", True),
            encryption_key=self.config.get("encryption_key")
        )
        
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
            progress_callback(100, summary)
        
        return patients, bundles

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