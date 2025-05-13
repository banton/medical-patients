# CLI Commands and Utilities

## Command Reference

This document provides a reference for command-line utilities, scripts, and operations available in the Military Medical Exercise Patient Generator.

### Basic Commands

1. **Running the Web Application**

   Start the web application server:
   ```bash
   python app.py
   ```
   
   This will start the FastAPI server on http://localhost:8000 by default.

2. **Running the Demo Script**

   Generate a small demonstration dataset:
   ```bash
   python demo.py
   ```
   
   This will create a sample of 10 patients and save them to the `demo_output` directory.

3. **Running Tests**

   Execute the test suite:
   ```bash
   python -m unittest tests.py
   ```
   
   Run specific test cases:
   ```bash
   python -m unittest tests.TestPatientGenerator.test_patient_creation
   ```

### Installation Commands

1. **Setting Up Development Environment**

   Create and activate a virtual environment:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Installing Dependencies**

   Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. **Installing in Development Mode**

   Install the package for development:
   ```bash
   pip install -e .
   ```

### Python Module Usage

1. **Importing Core Components**

   ```python
   from patient_generator.app import PatientGeneratorApp
   from patient_generator.patient import Patient
   from patient_generator.flow_simulator import PatientFlowSimulator
   from patient_generator.demographics import DemographicsGenerator
   from patient_generator.medical import MedicalConditionGenerator
   from patient_generator.fhir_generator import FHIRBundleGenerator
   from patient_generator.formatter import OutputFormatter
   ```

2. **Basic Generation Script**

   ```python
   from patient_generator.app import PatientGeneratorApp
   
   # Create configuration
   config = {
       "total_patients": 100,
       "output_directory": "my_output",
       "output_formats": ["json"]
   }
   
   # Initialize and run generator
   generator = PatientGeneratorApp(config)
   patients, bundles = generator.run()
   
   # Print summary
   print(f"Generated {len(patients)} patients")
   ```

3. **Custom Progress Callback**

   ```python
   def my_progress_callback(percent, data=None):
       print(f"Progress: {percent}%")
       if data:
           print(f"Processed patients: {data.get('processed_patients', 0)}")
   
   generator = PatientGeneratorApp(config)
   patients, bundles = generator.run(progress_callback=my_progress_callback)
   ```

### Configuration Examples

1. **Basic Configuration**

   ```python
   config = {
       "total_patients": 1440,  # Number of patients to generate
       "output_formats": ["json", "xml"],  # Output formats
       "output_directory": "output",  # Where to save files
       "use_compression": True,  # Generate compressed files
       "use_encryption": False  # Don't encrypt files
   }
   ```

2. **Custom Distribution Configuration**

   ```python
   config = {
       "total_patients": 1000,
       "front_distribution": {
           "Polish": 0.60,    # 60% from Polish front
           "Estonian": 0.25,  # 25% from Estonian front
           "Finnish": 0.15    # 15% from Finnish front
       },
       "injury_distribution": {
           "DISEASE": 0.40,
           "NON_BATTLE": 0.40,
           "BATTLE_TRAUMA": 0.20
       },
       "output_directory": "custom_output"
   }
   ```

3. **Encryption Configuration**

   ```python
   import hashlib
   
   # Generate a key from password
   password = "secure-password"
   encryption_key = hashlib.pbkdf2_hmac(
       'sha256', 
       password.encode(), 
       b'salt', 
       100000, 
       dklen=32
   )
   
   config = {
       "total_patients": 500,
       "use_encryption": True,
       "encryption_key": encryption_key,
       "output_directory": "encrypted_output"
   }
   ```

### Direct API Endpoint Usage

1. **Starting a Generation Job**

   ```bash
   curl -X POST "http://localhost:8000/api/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "total_patients": 100,
       "polish_front_percent": 50,
       "estonian_front_percent": 33.3,
       "finnish_front_percent": 16.7,
       "disease_percent": 52,
       "non_battle_percent": 33,
       "battle_trauma_percent": 15,
       "formats": ["json", "xml"],
       "use_compression": true,
       "use_encryption": false
     }'
   ```

2. **Checking Job Status**

   ```bash
   curl -X GET "http://localhost:8000/api/jobs/job_20250601120000"
   ```

3. **Downloading Job Results**

   ```bash
   curl -X GET "http://localhost:8000/api/download/job_20250601120000" \
     -o patients.zip
   ```

4. **Getting Default Configuration**

   ```bash
   curl -X GET "http://localhost:8000/api/config/defaults"
   ```

### Advanced Operations

1. **Custom Medical Condition Generator**

   ```python
   from patient_generator.medical import MedicalConditionGenerator
   
   class CustomMedicalConditionGenerator(MedicalConditionGenerator):
       def __init__(self):
           super().__init__()
           # Add custom battle trauma conditions
           self.battle_trauma_conditions.extend([
               {"code": "125689001", "display": "Shrapnel injury to abdomen"},
               {"code": "125604005", "display": "Chemical burns"}
           ])
           # Add custom medications
           self.medication_list.extend([
               {"code": "387458008", "display": "Ketamine"},
               {"code": "387495008", "display": "Tranexamic acid"}
           ])
   
   # Use custom generator
   generator = CustomMedicalConditionGenerator()
   condition = generator.generate_condition("BATTLE_TRAUMA", "T1")
   ```

2. **Extending Demographics Data**

   ```python
   from patient_generator.demographics import DemographicsGenerator
   
   class ExtendedDemographicsGenerator(DemographicsGenerator):
       def __init__(self):
           super().__init__()
           # Add German names
           self.first_names["DEU"] = {
               "male": ["Hans", "Jürgen", "Klaus", "Wolfgang", "Dieter"],
               "female": ["Ursula", "Helga", "Ingrid", "Renate", "Gisela"]
           }
           self.last_names["DEU"] = [
               "Müller", "Schmidt", "Schneider", "Fischer", "Weber"
           ]
           # Add German ID format
           self.id_formats["DEU"] = lambda: f"L{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.randint(0,9)}{random.choice('ABCDEFGHIJKLMNPQRSTUVWXYZ')}"
   ```

3. **Custom Patient Flow Rules**

   ```python
   from patient_generator.flow_simulator import PatientFlowSimulator
   
   class CustomFlowSimulator(PatientFlowSimulator):
       def _determine_next_location(self, patient, current_location):
           # Override for custom logic
           if current_location == "POI":
               # Higher KIA rate for battle trauma
               if patient.injury_type == "BATTLE_TRAUMA":
                   kia_prob = 0.30  # 30% KIA for battle trauma
               else:
                   kia_prob = 0.10  # 10% for others
                   
               if random.random() < kia_prob:
                   return "KIA"
               else:
                   return "R1"
           
           # Use parent class logic for other locations
           return super()._determine_next_location(patient, current_location)
   ```

4. **Custom FHIR Extensions**

   ```python
   from patient_generator.fhir_generator import FHIRBundleGenerator
   
   class ExtendedFHIRGenerator(FHIRBundleGenerator):
       def _create_patient_resource(self, patient):
           # Get base patient resource from parent method
           patient_resource = super()._create_patient_resource(patient)
           
           # Add custom military rank extension
           ranks = ["Private", "Corporal", "Sergeant", "Lieutenant", "Captain"]
           patient_resource["extension"].append({
               "url": "http://example.org/fhir/StructureDefinition/military-rank",
               "valueString": random.choice(ranks)
           })
           
           # Add custom deployment history extension
           patient_resource["extension"].append({
               "url": "http://example.org/fhir/StructureDefinition/deployment-history",
               "valueInteger": random.randint(0, 3)  # Number of previous deployments
           })
           
           return patient_resource
   ```

### Utility Operations

1. **Validating FHIR Output**

   Using the official FHIR validator:
   ```bash
   java -jar org.hl7.fhir.validator.jar output/patients.json
   ```

2. **Converting Between Formats**

   ```python
   from patient_generator.formatter import OutputFormatter
   import json
   
   # Load JSON data
   with open('output/patients.json', 'r') as f:
       data = json.load(f)
       
   # Convert to XML
   formatter = OutputFormatter()
   xml_data = formatter.format_xml(data)
   
   # Save XML file
   with open('converted.xml', 'w') as f:
       f.write(xml_data)
   ```

3. **Extracting Statistics from Generated Data**

   ```python
   import json
   from collections import Counter
   
   # Load generated data
   with open('output/patients.json', 'r') as f:
       bundles = json.load(f)
   
   # Extract patient nationalities
   nationalities = []
   for bundle in bundles:
       for entry in bundle['entry']:
           if entry['resource']['resourceType'] == 'Patient':
               for ext in entry['resource'].get('extension', []):
                   if ext['url'].endswith('nationality'):
                       nationalities.append(ext['valueString'])
   
   # Count by nationality
   nationality_counts = Counter(nationalities)
   print(nationality_counts)
   ```

4. **Creating a Custom Output Directory Structure**

   ```python
   import os
   import shutil
   import json
   
   # Load generated data
   with open('output/patients.json', 'r') as f:
       bundles = json.load(f)
   
   # Create directories by status
   os.makedirs('sorted_output/R1', exist_ok=True)
   os.makedirs('sorted_output/R2', exist_ok=True)
   os.makedirs('sorted_output/R3', exist_ok=True)
   os.makedirs('sorted_output/R4', exist_ok=True)
   os.makedirs('sorted_output/RTD', exist_ok=True)
   os.makedirs('sorted_output/KIA', exist_ok=True)
   
   # Sort bundles by current status
   for i, bundle in enumerate(bundles):
       # Determine status (simplified - would need proper parsing in real use)
       status = "R1"  # Default
       
       # Write to appropriate directory
       with open(f'sorted_output/{status}/patient_{i}.json', 'w') as f:
           json.dump(bundle, f, indent=2)
   ```
