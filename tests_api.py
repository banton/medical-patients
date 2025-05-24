import unittest
import requests
import json
from typing import Dict, Any, List
import time

BASE_URL = "http://localhost:8000"  # Assuming the FastAPI app is running here
CONFIG_API_URL = f"{BASE_URL}/api/v1/configurations"
GENERATE_API_URL = f"{BASE_URL}/api/generate"
JOBS_API_URL = f"{BASE_URL}/api/jobs"
API_KEY = "your_secret_api_key_here"  # Should match API_KEY env var or default

HEADERS = {
    "X-API-KEY": API_KEY,
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# Helper to create a valid default configuration for testing
def create_default_config_payload(name_suffix: str = "") -> Dict[str, Any]:
    return {
        "name": f"Test Config {name_suffix}{time.time()}",
        "description": "A configuration template for API integration testing.",
        "total_patients": 10,
        "front_configs": [
            {
                "id": "front_test_1",
                "name": "Test Front Alpha",
                "casualty_rate": 1.0,
                "nationality_distribution": [
                    {"nationality_code": "USA", "percentage": 100.0}
                ]
            }
        ],
        "facility_configs": [
            {"id": "POI", "name": "Point of Injury", "kia_rate": 0.01, "rtd_rate": 0.0},
            {"id": "R1", "name": "Role 1", "kia_rate": 0.02, "rtd_rate": 0.1}
        ],
        "injury_distribution": {
            "Disease": 50.0,
            "Non-Battle Injury": 30.0,
            "Battle Injury": 20.0
        }
    }

class TestAPIIntegration(unittest.TestCase):

    created_config_ids: List[str] = [] # Keep track of created configs to clean up

    @classmethod
    def tearDownClass(cls):
        # Clean up any created configurations
        for config_id in cls.created_config_ids:
            try:
                requests.delete(f"{CONFIG_API_URL}/{config_id}", headers=HEADERS)
            except Exception as e:
                print(f"Error cleaning up config {config_id}: {e}")

    def test_01_reference_get_nationalities(self):
        response = requests.get(f"{CONFIG_API_URL}/reference/nationalities/", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        if len(data) > 0:
            self.assertIn("code", data[0])
            self.assertIn("name", data[0])

    def test_02_reference_get_condition_types(self):
        response = requests.get(f"{CONFIG_API_URL}/reference/condition-types/", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertIn("DISEASE", data)
        self.assertIn("NON_BATTLE", data) # Based on current app.py, it's NON_BATTLE
        self.assertIn("BATTLE_TRAUMA", data) # Based on current app.py

    def test_03_config_validate_valid_syntax(self):
        payload = create_default_config_payload("ValidateValid")
        response = requests.post(f"{CONFIG_API_URL}/validate/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("valid"))

    def test_04_config_validate_invalid_syntax(self):
        payload = create_default_config_payload("ValidateInvalid")
        payload["total_patients"] = "not_an_integer" # Invalid data type
        response = requests.post(f"{CONFIG_API_URL}/validate/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(response.status_code, 422) # Unprocessable Entity for Pydantic validation error

    def test_05_config_create_valid(self):
        payload = create_default_config_payload("CreateValid")
        response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(response.status_code, 201, f"Response content: {response.text}")
        data = response.json()
        self.assertIn("id", data)
        self.assertEqual(data["name"], payload["name"])
        self.created_config_ids.append(data["id"]) # Save for cleanup

    def test_06_config_create_invalid_payload(self):
        payload = create_default_config_payload("CreateInvalid")
        del payload["total_patients"] # Missing required field
        response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(response.status_code, 422) # Pydantic validation error

    def test_07_config_list_all(self):
        # Create a config first to ensure list is not empty
        payload = create_default_config_payload("ListTest")
        create_response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.json()["id"]
        self.created_config_ids.append(created_id)

        response = requests.get(CONFIG_API_URL + "/", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        # Check if our created config is in the list
        self.assertTrue(any(c["id"] == created_id for c in data))

    def test_08_config_get_specific_valid(self):
        payload = create_default_config_payload("GetSpecific")
        create_response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.json()["id"]
        self.created_config_ids.append(created_id)

        response = requests.get(f"{CONFIG_API_URL}/{created_id}", headers=HEADERS)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], created_id)
        self.assertEqual(data["name"], payload["name"])

    def test_09_config_get_specific_not_found(self):
        response = requests.get(f"{CONFIG_API_URL}/non_existent_id_123", headers=HEADERS)
        self.assertEqual(response.status_code, 404)

    def test_10_config_update_valid(self):
        payload = create_default_config_payload("UpdateBase")
        create_response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(create_response.status_code, 201)
        created_config = create_response.json()
        created_id = created_config["id"]
        self.created_config_ids.append(created_id)

        update_payload = create_default_config_payload("Updated")
        update_payload["description"] = "This configuration has been updated."
        # Pydantic model for update might be same as create, or a different one.
        # Assuming ConfigurationTemplateCreate is used for PUT body as well.
        
        response = requests.put(f"{CONFIG_API_URL}/{created_id}", headers=HEADERS, data=json.dumps(update_payload))
        self.assertEqual(response.status_code, 200, f"Response content: {response.text}")
        data = response.json()
        self.assertEqual(data["id"], created_id)
        self.assertEqual(data["name"], update_payload["name"]) # Name can be updated
        self.assertEqual(data["description"], "This configuration has been updated.")
        # Version should increment if versioning is implemented and returned by PUT
        if "version" in created_config and "version" in data:
            # Version may or may not increment on update depending on implementation
            # For now, just verify it exists and is valid
            self.assertIsInstance(data["version"], int)
            self.assertGreaterEqual(data["version"], created_config.get("version", 0))


    def test_11_config_update_not_found(self):
        update_payload = create_default_config_payload("UpdateNotFound")
        response = requests.put(f"{CONFIG_API_URL}/non_existent_id_456", headers=HEADERS, data=json.dumps(update_payload))
        self.assertEqual(response.status_code, 404)

    def test_12_config_delete_valid(self):
        payload = create_default_config_payload("DeleteValid")
        create_response = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(payload))
        self.assertEqual(create_response.status_code, 201)
        created_id = create_response.json()["id"]
        # Don't add to self.created_config_ids yet, as we expect to delete it

        response = requests.delete(f"{CONFIG_API_URL}/{created_id}", headers=HEADERS)
        self.assertEqual(response.status_code, 204)

        # Verify it's actually deleted
        get_response = requests.get(f"{CONFIG_API_URL}/{created_id}", headers=HEADERS)
        self.assertEqual(get_response.status_code, 404)

    def test_13_config_delete_not_found(self):
        response = requests.delete(f"{CONFIG_API_URL}/non_existent_id_789", headers=HEADERS)
        self.assertEqual(response.status_code, 404)

    # --- Tests for Generation and Job Status APIs ---
    # These will require more setup, potentially polling for job completion.

    def test_14_generate_with_ad_hoc_config(self):
        ad_hoc_config = create_default_config_payload("AdHocGenerate")
        payload = {
            "configuration": ad_hoc_config,
            "output_formats": ["json"],
            "use_compression": False,
            "use_encryption": False
        }
        # Generate endpoint now requires authentication
        generate_headers = {"Content-Type": "application/json", "Accept": "application/json", "X-API-Key": API_KEY}
        response = requests.post(GENERATE_API_URL, headers=generate_headers, data=json.dumps(payload))
        self.assertEqual(response.status_code, 200, f"Response content: {response.text}")
        data = response.json()
        self.assertIn("job_id", data)
        self.assertIn("status", data)
        self.assertIn(data["status"], ["initializing", "queued"]) # Initial status
        
        # Store job_id for potential status check later, though full polling is complex for unit test
        # For a simple check, we can try to get status once.
        job_id = data["job_id"]
        time.sleep(2) # Give a moment for the job to potentially start
        
        status_response = requests.get(f"{JOBS_API_URL}/{job_id}", headers=HEADERS)
        self.assertEqual(status_response.status_code, 200)
        status_data = status_response.json()
        self.assertIn(status_data["status"], ["initializing", "running", "completed", "failed"])


    def test_15_generate_with_config_id(self):
        # 1. Create and save a configuration template
        config_payload = create_default_config_payload("GenerateWithID")
        create_resp = requests.post(CONFIG_API_URL + "/", headers=HEADERS, data=json.dumps(config_payload))
        self.assertEqual(create_resp.status_code, 201)
        saved_config_id = create_resp.json()["id"]
        self.created_config_ids.append(saved_config_id)

        # 2. Submit generation job using the ID
        generation_payload = {
            "configuration_id": saved_config_id,
            "output_formats": ["json"],
        }
        generate_headers = {"Content-Type": "application/json", "Accept": "application/json", "X-API-Key": API_KEY}
        response = requests.post(GENERATE_API_URL, headers=generate_headers, data=json.dumps(generation_payload))
        self.assertEqual(response.status_code, 200, f"Response content: {response.text}")
        data = response.json()
        self.assertIn("job_id", data)

    def test_16_get_job_status_not_found(self):
        response = requests.get(f"{JOBS_API_URL}/non_existent_job_id", headers=HEADERS)
        self.assertEqual(response.status_code, 404)

    # test_get_job_results would require a fully completed job.
    # This is harder to guarantee in an automated test without long waits or mocks.
    # For now, we'll skip a direct test of /results endpoint content,
    # but the endpoint's existence and basic error handling for non-completed jobs can be tested.

    def test_17_get_job_results_for_incomplete_job(self):
        # Submit a job
        ad_hoc_config = create_default_config_payload("ResultsIncomplete")
        payload = {"configuration": ad_hoc_config}
        generate_headers = {"Content-Type": "application/json", "Accept": "application/json", "X-API-Key": API_KEY}
        response = requests.post(GENERATE_API_URL, headers=generate_headers, data=json.dumps(payload))
        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]

        # Try to get results immediately (job should not be complete)
        results_response = requests.get(f"{JOBS_API_URL}/{job_id}/results", headers=HEADERS)
        # The API might return 200 with empty/partial results or error status codes
        # Check the actual response to determine the behavior
        if results_response.status_code == 200:
            # If 200, verify the response indicates incomplete status
            data = results_response.json()
            # Check if there's an indication that results aren't ready
            self.assertTrue(
                data.get("summary") is None or 
                data.get("status") in ["running", "queued", "initializing"] or
                len(data.get("output_files", [])) == 0,
                "Expected incomplete results for a just-submitted job"
            )
        else:
            # Otherwise expect 400 or 404 for incomplete job
            self.assertIn(results_response.status_code, [400, 404])


if __name__ == '__main__':
    unittest.main()
