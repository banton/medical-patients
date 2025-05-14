import unittest
import datetime
from patient_generator.patient import Patient
from patient_generator.demographics import DemographicsGenerator
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.visualization_data import transform_job_data_for_visualization

# For API tests
import pytest
from fastapi.testclient import TestClient
from app import app # Assuming app.py in root contains FastAPI app instance
import time

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

class TestVisualizationData(unittest.TestCase):
    def setUp(self):
        # Create a mock job with realistic summary data
        self.mock_job = {
            "summary": {
                "total_patients": 1440,
                "kia_count": 276,
                "rtd_count": 824,
                "still_in_treatment": 340,
                "nationalities": {
                    "POL": 522,
                    "EST": 389,
                    "GBR": 176,
                    "FIN": 145
                },
                "injury_types": {
                    "DISEASE": 749,
                    "NON_BATTLE": 475,
                    "BATTLE_TRAUMA": 216
                },
                "fronts": {
                    "Polish": 720,
                    "Estonian": 480,
                    "Finnish": 240
                },
                "final_status": {
                    "KIA": 276,
                    "RTD": 824,
                    "R1": 98,
                    "R2": 102,
                    "R3": 76,
                    "R4": 64
                }
            }
            # Assuming transform_job_data_for_visualization might also need patient_data for detailed views
            # If so, this mock_job might need to be augmented or the function needs to be robust.
            # For now, sticking to the user-provided test structure.
        }
    
    def test_basic_transformation(self):
        """Test that basic transformation works without errors"""
        result = transform_job_data_for_visualization(self.mock_job)
        self.assertIsNotNone(result)
        self.assertIn("summary", result)
        self.assertIn("nationalityDistribution", result)
        self.assertIn("injuryDistribution", result)
        self.assertIn("frontDistribution", result)
        self.assertIn("statusDistribution", result)
    
    def test_summary_transformation(self):
        """Test that summary data is transformed correctly"""
        result = transform_job_data_for_visualization(self.mock_job)
        summary = result["summary"]
        
        self.assertEqual(summary["totalPatients"], 1440)
        self.assertEqual(summary["kia"], 276)
        self.assertEqual(summary["rtd"], 824)
        self.assertEqual(summary["inTreatment"], 340)
    
    def test_distribution_transformation(self):
        """Test that distribution data is transformed correctly"""
        result = transform_job_data_for_visualization(self.mock_job)
        
        # Check nationality distribution
        self.assertEqual(len(result["nationalityDistribution"]), 4)
        # Note: The user's test assumes a specific order. Dictionaries are unordered by default in older Python.
        # transform_job_data_for_visualization should ideally sort by name or value for consistent test results.
        # For now, I'll find items by name.
        pol_data = next(item for item in result["nationalityDistribution"] if item["name"] == "POL")
        self.assertEqual(pol_data["value"], 522)
        
        # Check injury distribution
        self.assertEqual(len(result["injuryDistribution"]), 3)
        disease_data = next(item for item in result["injuryDistribution"] if item["name"] == "Disease") # Assuming "DISEASE" becomes "Disease"
        self.assertEqual(disease_data["value"], 749)
    
    def test_advanced_data_generation(self):
        """Test that advanced data is generated"""
        # This test assumes transform_job_data_for_visualization can generate these
        # from just the summary. This might require the function to have access to
        # the full patient list or more detailed data within the job object.
        # If it only uses summary, these might be empty or default.
        # The user's test implies these keys should be present.
        
        # To make this test pass with the current mock_job (summary only),
        # transform_job_data_for_visualization would need to:
        # 1. Either derive these from summary (unlikely for patientFlow, facilityLoadByDay etc.)
        # 2. Or the mock_job in setUp needs to include 'patients_data' if that's what the function uses
        #    for these detailed sections.
        # The original TestVisualizationData used 'patients_data'.
        # For now, I will keep the user's test structure. If it fails,
        # it indicates transform_job_data_for_visualization needs more data than just summary
        # for these "advanced" fields, or the function needs to be adapted.

        # Let's assume for now that if 'patients_data' is missing, these are initialized to empty/default structures.
        mock_job_for_advanced = {
            "summary": self.mock_job["summary"],
            "patients_data": [] # Add empty patient data to allow function to run if it expects this key
        }
        result = transform_job_data_for_visualization(mock_job_for_advanced)
        
        self.assertIn("triageDistribution", result)
        self.assertIn("patientFlow", result)
        self.assertIn("facilityLoadByDay", result)
        self.assertIn("casualtyFlowByDay", result)
        self.assertIn("injuryTypeByFront", result)
        
        # Check structure of patient flow data (assuming default/empty state)
        self.assertIn("nodes", result["patientFlow"])
        self.assertIn("links", result["patientFlow"])
        # If patients_data is empty, nodes should still be default, links empty.
        self.assertEqual(len(result["patientFlow"]["nodes"]), 7)  # POI, R1-R4, RTD, KIA (default nodes)
        self.assertEqual(len(result["patientFlow"]["links"]), 0)


# API Endpoint Tests (pytest style)
client = TestClient(app)

def test_dashboard_data_endpoint():
    """Test that the dashboard data endpoint returns correct data"""
    # Create a mock job first
    mock_job_response = client.post(
        "/api/generate",
        json={
            "total_patients": 100,
            "polish_front_percent": 50.0,
            "estonian_front_percent": 33.3,
            "finnish_front_percent": 16.7,
            "disease_percent": 52.0,
            "non_battle_percent": 33.0,
            "battle_trauma_percent": 15.0,
            "formats": ["json"],
            "use_compression": False,
            "use_encryption": False,
            "encryption_password": "" # Ensure all required fields for GeneratorConfig are present
        }
    )
    assert mock_job_response.status_code == 200
    job_id = mock_job_response.json()["job_id"]
    
    # Poll until job is complete
    max_wait = 60  # seconds
    start_time = time.time()
    job_complete = False
    
    while not job_complete and time.time() - start_time < max_wait:
        job_status_response = client.get(f"/api/jobs/{job_id}")
        # Ensure the request was successful before trying to access .json()
        if job_status_response.status_code != 200:
            # Handle error or fail test, e.g.
            pytest.fail(f"Failed to get job status for {job_id}: {job_status_response.status_code} {job_status_response.text}")
        
        job_status = job_status_response.json()
        if job_status["status"] == "completed":
            job_complete = True
            break
        time.sleep(1)
    
    assert job_complete, f"Job {job_id} failed to complete within timeout. Last status: {job_status.get('status') if 'job_status' in locals() else 'unknown'}"
    
    # Test dashboard data endpoint
    response = client.get(f"/api/visualizations/dashboard-data?job_id={job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "summary" in data
    assert "nationalityDistribution" in data
    assert "injuryDistribution" in data
    # Check against the total_patients we set for the job
    assert data["summary"]["total_patients"] == 100

def test_job_list_endpoint():
    """Test that the job list endpoint returns a list of jobs"""
    response = client.get("/api/visualizations/job-list")
    assert response.status_code == 200
    
    jobs = response.json()
    assert isinstance(jobs, list)
    # If there are jobs, check their structure
    if jobs:
        # Assuming the job created in test_dashboard_data_endpoint might be here
        # or other pre-existing jobs.
        # A more robust test might create a known job and then check for it.
        assert "job_id" in jobs[0]
        # The user's test had "total_patients" here.
        # Let's check the structure from memory bank for /api/visualizations/job-list
        # memory-bank/data-structures.md does not define the output for /api/visualizations/job-list
        # Let's assume it returns a list of job summaries or a custom structure.
        # The frontend `visualization-dashboard.js` would fetch this list for a dropdown.
        # A typical job list item might contain job_id and some descriptive info.
        # For now, let's stick to the user's provided assertion if it's simple.
        # The user's test had: assert "total_patients" in jobs[0]
        # This implies the job list items contain total_patients.
        assert "total_patients" in jobs[0] # Keeping user's assertion


if __name__ == '__main__':
    unittest.main()
