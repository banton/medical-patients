import os
import random
import datetime
from patient_generator.patient import Patient
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.demographics import DemographicsGenerator
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.fhir_generator import FHIRBundleGenerator
from patient_generator.formatter import OutputFormatter

# Simple demonstration script to show how to use the patient generator directly

def main():
    print("Military Medical Exercise Patient Generator - Demo")
    print("================================================")

    # Create a configuration
    config = {
        "total_patients": 10,  # Small number for demo
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
        "output_formats": ["json", "xml"],
        "output_directory": "demo_output",
        "base_date": "2025-06-01"
    }
    
    # Create output directory
    os.makedirs(config["output_directory"], exist_ok=True)
    
    # Print configuration
    print("\nConfiguration:")
    print(f"- Total patients: {config['total_patients']}")
    print(f"- Base date: {config['base_date']}")
    print(f"- Output directory: {config['output_directory']}")
    
    # Step 1: Generate the patient flow
    print("\nStep 1: Generating patient flow...")
    flow_simulator = PatientFlowSimulator(config)
    patients = flow_simulator.generate_casualty_flow(config["total_patients"])
    print(f"Generated {len(patients)} patients")
    
    # Print a sample patient's flow
    sample_patient = patients[0]
    print(f"\nSample patient (ID: {sample_patient.id}):")
    print(f"- Nationality: {sample_patient.nationality}")
    print(f"- Front: {sample_patient.front}")
    print(f"- Injury type: {sample_patient.injury_type}")
    print(f"- Triage category: {sample_patient.triage_category}")
    print(f"- Treatment history:")
    for treatment in sample_patient.treatment_history:
        print(f"  * {treatment['facility']} on {treatment['date']}")
    
    # Step 2: Add demographics and medical conditions
    print("\nStep 2: Adding demographics and medical conditions...")
    demographics_generator = DemographicsGenerator()
    condition_generator = MedicalConditionGenerator()
    
    for patient in patients:
        # Generate demographics
        demographics = demographics_generator.generate_person(patient.nationality, patient.gender)
        patient.set_demographics(demographics)
        
        # Generate medical conditions
        primary_condition = condition_generator.generate_condition(
            patient.injury_type, 
            patient.triage_category
        )
        patient.primary_condition = primary_condition
        
        # Generate additional conditions
        additional_count = 1 if patient.triage_category == "T1" else 0
        patient.additional_conditions = condition_generator.generate_additional_conditions(
            primary_condition, 
            additional_count
        )
        
        # Generate medications
        conditions = [primary_condition] + patient.additional_conditions
        medication_count = random.randint(1, 2)
        patient.medications = condition_generator.generate_medications(conditions, medication_count)
        
        # Generate allergies (10% chance)
        if random.random() < 0.1:
            patient.allergies = condition_generator.generate_allergies(1)
        else:
            patient.allergies = []
    
    # Print sample patient demographics
    print("\nSample patient demographics:")
    print(f"- Name: {sample_patient.demographics['given_name']} {sample_patient.demographics['family_name']}")
    print(f"- Gender: {sample_patient.demographics['gender']}")
    print(f"- Birthdate: {sample_patient.demographics['birthdate']}")
    print(f"- ID Number: {sample_patient.demographics['id_number']}")
    
    # Print sample patient medical conditions
    print("\nSample patient medical conditions:")
    print(f"- Primary: {sample_patient.primary_condition['display']} ({sample_patient.primary_condition['severity']})")
    for condition in sample_patient.additional_conditions:
        print(f"- Additional: {condition['display']}")
    
    # Step 3: Generate FHIR bundles
    print("\nStep 3: Generating FHIR bundles...")
    bundle_generator = FHIRBundleGenerator(demographics_generator)
    bundles = []
    
    for patient in patients:
        bundle = bundle_generator.create_patient_bundle(patient)
        bundles.append(bundle)
    
    # Step 4: Format and save outputs
    print("\nStep 4: Formatting and saving outputs...")
    formatter = OutputFormatter()
    
    output_files = formatter.create_output_files(
        bundles,
        config["output_directory"],
        formats=config["output_formats"],
        use_compression=True,
        use_encryption=True,
        encryption_key=os.urandom(32)  # Random key for demo
    )
    
    # Print output files
    print("\nGenerated files:")
    for file_path in output_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        print(f"- {file_name} ({file_size} bytes)")
    
    print("\nDemo completed successfully!")

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()