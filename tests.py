import unittest
from patient_generator.patient import Patient
from patient_generator.demographics import DemographicsGenerator
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.flow_simulator import PatientFlowSimulator

class TestPatientGenerator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            "front_distribution": {
                "Polish": 0.50,
                "Estonian": 0.33,
                "Finnish": 0.17
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
            "base_date": "2025-06-01"
        }
        
    def test_patient_creation(self):
        """Test that a patient can be created with basic attributes"""
        patient = Patient(1)
        self.assertEqual(patient.id, 1)
        self.assertEqual(patient.current_status, "POI")
        
        # Test adding treatment
        import datetime
        treatment_date = datetime.datetime.now()
        patient.add_treatment("R1", treatment_date, ["Treatment 1"], ["Observation 1"])
        
        self.assertEqual(patient.current_status, "R1")
        self.assertEqual(len(patient.treatment_history), 1)
        self.assertEqual(patient.treatment_history[0]["facility"], "R1")
        self.assertEqual(patient.treatment_history[0]["date"], treatment_date)
    
    def test_demographics_generator(self):
        """Test that demographics can be generated for different nationalities"""
        generator = DemographicsGenerator()
        
        # Test different nationalities
        for nationality in ["POL", "EST", "FIN", "GBR", "USA", "LIT", "ESP", "NLD"]:
            # Generate male and female profiles
            male_profile = generator.generate_person(nationality, "male")
            female_profile = generator.generate_person(nationality, "female")
            
            # Check basic properties
            self.assertEqual(male_profile["gender"], "male")
            self.assertEqual(female_profile["gender"], "female")
            self.assertEqual(male_profile["nationality"], nationality)
            self.assertEqual(female_profile["nationality"], nationality)
            
            # Check that names are from appropriate lists
            self.assertIn(male_profile["given_name"], generator.first_names[nationality]["male"])
            self.assertIn(female_profile["given_name"], generator.first_names[nationality]["female"])
            self.assertIn(male_profile["family_name"], generator.last_names[nationality])
            self.assertIn(female_profile["family_name"], generator.last_names[nationality])
    
    def test_medical_condition_generator(self):
        """Test that medical conditions can be generated"""
        generator = MedicalConditionGenerator()
        
        # Test different injury types and triage categories
        for injury_type in ["BATTLE_TRAUMA", "NON_BATTLE", "DISEASE"]:
            for triage in ["T1", "T2", "T3"]:
                condition = generator.generate_condition(injury_type, triage)
                
                # Check that condition has basic properties
                self.assertIn("code", condition)
                self.assertIn("display", condition)
                self.assertIn("severity", condition)
                self.assertIn("severity_code", condition)
                
                # Check that severity is appropriate for triage
                if triage == "T1":
                    self.assertEqual(condition["severity"], "Severe")
                elif triage == "T3":
                    self.assertEqual(condition["severity"], "Mild to moderate")
    
    def test_flow_simulator(self):
        """Test that patient flow can be simulated"""
        simulator = PatientFlowSimulator(self.config)
        
        # Generate a small number of patients
        patients = simulator.generate_casualty_flow(100)
        
        # Check basic properties
        self.assertEqual(len(patients), 100)
        
        # Check that patients have treatment history
        for patient in patients:
            self.assertIsNotNone(patient.nationality)
            self.assertIsNotNone(patient.front)
            self.assertIsNotNone(patient.injury_type)
            self.assertIsNotNone(patient.triage_category)
            self.assertGreaterEqual(len(patient.treatment_history), 1)
            
            # Check that the final status is one of the terminal states
            self.assertIn(patient.current_status, ["POI", "R1", "R2", "R3", "R4", "RTD", "KIA"])

if __name__ == '__main__':
    unittest.main()