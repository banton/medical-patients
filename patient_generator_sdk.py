# patient_generator_sdk.py
"""
Python SDK for interacting with the Military Medical Exercise Patient Generator API.

This client provides methods to manage configuration templates, start patient generation jobs,
monitor job status, download results, and access reference data.
"""
import requests
import json
import time # Added for time.sleep in example
from typing import Optional, List, Dict, Any

class PatientGeneratorClient:
    """Python client for the Military Medical Exercise Patient Generator API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the client with the API base URL and optional API key.
        Args:
            base_url: The base URL of the API (e.g., http://localhost:8000)
            api_key: Optional API key for authentication. This key should match the one
                     configured in the backend (e.g., in `dashboard_auth.toml` or environment variables
                     for a production setup, or the development key if running locally).
        """
        if not base_url.endswith('/'):
            base_url += '/'
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Accept": "application/json"}
        if self.api_key:
            self.headers["X-API-KEY"] = self.api_key # Matches APIKeyHeader name in app.py

    def _request(self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, 
                 data: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Any:
        """Helper method to make HTTP requests."""
        url = f"{self.base_url}{endpoint.lstrip('/')}"
        try:
            response = requests.request(method, url, params=params, data=data, json=json_data, headers=self.headers)
            response.raise_for_status() # Raises HTTPError for bad responses (4XX or 5XX)
            if response.status_code == 204: # No Content
                return None
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - {http_err.response.text}")
            # Attempt to parse error detail from response if JSON
            try:
                error_detail = http_err.response.json().get("detail", http_err.response.text)
                raise Exception(f"API Error: {error_detail}") from http_err
            except json.JSONDecodeError:
                raise Exception(f"API Error: {http_err.response.status_code} - {http_err.response.text}") from http_err
        except requests.exceptions.RequestException as req_err:
            print(f"Request exception occurred: {req_err}")
            raise Exception(f"Request failed: {req_err}") from req_err
        except json.JSONDecodeError as json_err:
            # This case might be tricky if response.text was already used above.
            # For safety, let's assume response might not be available or already consumed.
            print(f"JSON decode error: {json_err}")
            raise Exception(f"Failed to decode JSON response: {json_err}") from json_err


    # Configuration Template Endpoints
    def create_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new configuration template.
        Args:
            config_data: A dictionary matching the ConfigurationTemplateCreate schema.
        Returns:
            The created configuration template.
        """
        return self._request("POST", "api/v1/configurations/", json_data=config_data)

    def list_configurations(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all configuration templates.
        """
        return self._request("GET", "api/v1/configurations/", params={"skip": skip, "limit": limit})

    def get_configuration(self, config_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific configuration template by ID.
        """
        return self._request("GET", f"api/v1/configurations/{config_id}")

    def update_configuration(self, config_id: str, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing configuration template.
        """
        return self._request("PUT", f"api/v1/configurations/{config_id}", json_data=config_data)

    def delete_configuration(self, config_id: str) -> None:
        """
        Delete a configuration template by ID.
        """
        self._request("DELETE", f"api/v1/configurations/{config_id}")
        return None 

    def validate_configuration(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a configuration template without saving.
        """
        return self._request("POST", "api/v1/configurations/validate/", json_data=config_data)

    # Generation Job Endpoints
    def start_generation_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start a new patient generation job.
        Args:
            payload: A dictionary matching GenerationRequestPayload schema.
        """
        return self._request("POST", "api/generate", json_data=payload)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a generation job.
        """
        return self._request("GET", f"api/jobs/{job_id}")

    def get_job_results_summary(self, job_id: str) -> Dict[str, Any]:
        """
        Get the results summary of a completed job.
        """
        return self._request("GET", f"api/jobs/{job_id}/results")

    def download_job_output(self, job_id: str, output_path: str) -> str:
        """
        Download the ZIP archive of a completed job's output files.
        Args:
            job_id: The ID of the job.
            output_path: The local path (including filename) to save the downloaded ZIP file.
        Returns:
            The path where the file was saved.
        """
        url = f"{self.base_url}api/download/{job_id}"
        headers = self.headers.copy() 
        
        try:
            with requests.get(url, headers=headers, stream=True) as r:
                r.raise_for_status()
                with open(output_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            return output_path
        except requests.exceptions.HTTPError as http_err:
            error_content = http_err.response.text
            try:
                error_detail = http_err.response.json().get("detail", error_content)
            except json.JSONDecodeError:
                error_detail = error_content
            raise Exception(f"API Error downloading file: {error_detail}") from http_err
        except requests.exceptions.RequestException as req_err:
            raise Exception(f"Request failed downloading file: {req_err}") from req_err

    # Reference Data Endpoints
    def list_reference_nationalities(self) -> List[Dict[str, str]]:
        """Lists available nationalities for configuration."""
        return self._request("GET", "api/v1/configurations/reference/nationalities/")

    def list_reference_condition_types(self) -> List[str]:
        """Lists available condition types for injury distribution."""
        return self._request("GET", "api/v1/configurations/reference/condition-types/")

# Example Usage (can be run if the API server is running):
if __name__ == "__main__":
    # It's recommended to manage API keys securely, e.g., via environment variables or a config file.
    # For this example, we'll use a placeholder. Replace with your actual API key if required.
    # The development server (app.py) uses a hardcoded key "dev_api_key" if no dashboard_auth.toml is found or properly configured.
    # For a deployed instance, this key would be managed securely.
    API_KEY = "dev_api_key" # Replace with your actual API key or None if API key is not enforced for all endpoints
    BASE_URL = "http://localhost:8000"

    client = PatientGeneratorClient(base_url=BASE_URL, api_key=API_KEY)

    try:
        print("--- Reference Data ---")
        nationalities = client.list_reference_nationalities()
        print("Available Nationalities:", json.dumps(nationalities[:5], indent=2) + "..." if nationalities else "[]") # Print first 5
        
        condition_types = client.list_reference_condition_types()
        print("Available Condition Types:", condition_types)
        
        print("\n--- Configuration Template Management ---")
        # Example: Create a new configuration template
        # Note: Ensure this payload matches the latest Pydantic schemas (ConfigurationTemplateCreate)
        # especially for nested structures like FrontConfigCreate, FacilityConfigCreate.
        new_config_payload = {
            "name": "SDK Example Scenario",
            "description": "A comprehensive test scenario created via the Python SDK.",
            "version": 1, # Initial version
            # parent_config_id can be None for a new base configuration
            "total_patients": 100,
            "base_date": "2025-06-01",
            "front_configs": [
                {
                    "name": "Alpha Front",
                    "casualty_rate": 0.6,
                    # Nationality distribution as a list of objects
                    "nationality_distribution": [
                        {"nationality_code": "USA", "percentage": 70.0},
                        {"nationality_code": "GBR", "percentage": 30.0}
                    ],
                    "facility_chain": ["facility_r1_alpha", "facility_r2_alpha", "facility_r3_common"]
                }
            ],
            "facility_configs": [
                {
                    "id": "facility_r1_alpha", # Client-defined ID for linking in facility_chain
                    "name": "Role 1 Alpha",
                    "facility_type": "R1",
                    "capacity": 50,
                    "rtd_rate": 0.7,
                    "died_rate": 0.1, # Renamed from kia_rate in some older examples
                    "evacuation_rate": 0.2,
                    "avg_treatment_time_minutes": 60
                },
                {
                    "id": "facility_r2_alpha",
                    "name": "Role 2 Alpha",
                    "facility_type": "R2",
                    "capacity": 30,
                    "rtd_rate": 0.6,
                    "died_rate": 0.05,
                    "evacuation_rate": 0.35,
                    "avg_treatment_time_minutes": 240
                },
                {
                    "id": "facility_r3_common",
                    "name": "Role 3 Common",
                    "facility_type": "R3",
                    "capacity": 20,
                    "rtd_rate": 0.5,
                    "died_rate": 0.02,
                    "evacuation_rate": 0.48, # To R4 or definitive care
                    "avg_treatment_time_minutes": 720
                }
            ],
            # Injury distribution with fixed keys, summing to 100
            "injury_distribution": {
                "Battle Injury": 60.0,
                "Disease": 25.0,
                "Non-Battle Injury": 15.0
            }
            # Other fields like 'medical_condition_probabilities', 'specific_condition_configs' can be added
        }

        print("\nAttempting to create configuration...")
        created_template = client.create_configuration(new_config_payload)
        print("Created Configuration Template:", json.dumps(created_template, indent=2))
        config_id = created_template["id"]

        print("\nListing top 5 configurations:")
        configs = client.list_configurations(limit=5)
        for cfg in configs:
            print(f"  - Name: {cfg['name']}, ID: {cfg['id']}, Version: {cfg.get('version', 'N/A')}")

        print(f"\nRetrieving configuration {config_id} by ID:")
        retrieved_config = client.get_configuration(config_id)
        print(json.dumps(retrieved_config, indent=2))

        # Example: Update the configuration (e.g., change description and total_patients)
        # Note: For updates, you typically need to provide the complete model.
        # The API might support partial updates (PATCH), but this SDK method uses PUT.
        # Let's assume we fetch the config, modify it, and then update.
        config_to_update = retrieved_config.copy() # Make a copy to modify
        config_to_update["description"] = "Updated description via SDK."
        config_to_update["total_patients"] = 120
        # Ensure 'id' is not in the payload for update if API expects it only in URL
        # However, Pydantic models for update usually expect the full model.
        # Let's assume the update payload should be the full model without the ID.
        # update_payload = {k: v for k, v in config_to_update.items() if k != 'id'}

        # The update endpoint expects the full model, including potentially 'name', 'version' etc.
        # The backend schema for update is ConfigurationTemplateUpdate.
        # For simplicity, let's just update the description.
        # A proper update might require fetching, modifying, and then sending the whole object.
        # The current `update_configuration` sends the `config_data` as JSON body.
        # Let's assume `config_data` for update should be the fields that can be updated.
        # For a robust update, one might need a specific `ConfigurationTemplateUpdateSchema` for the payload.
        # The current API takes `ConfigurationTemplateUpdate` which inherits from `ConfigurationTemplateBase`.
        
        update_payload_example = {
            "name": config_to_update["name"], # Name is usually required
            "description": "Updated description for SDK Example Scenario.",
            "version": config_to_update.get("version", 1), # Version might be required
            "total_patients": 125,
            "front_configs": config_to_update["front_configs"], # Send existing or modified
            "facility_configs": config_to_update["facility_configs"],
            "injury_distribution": config_to_update["injury_distribution"],
            "base_date": config_to_update.get("base_date", "2025-06-01")
        }
        print(f"\nAttempting to update configuration {config_id}...")
        updated_template = client.update_configuration(config_id, update_payload_example)
        print("Updated Configuration Template:", json.dumps(updated_template, indent=2))


        print("\n--- Patient Generation Job ---")
        # Example: Start a patient generation job using the created/updated configuration
        job_payload = {
            "configuration_id": config_id, # Use the ID of the configuration template
            # "configuration_data": new_config_payload, # Alternatively, provide ad-hoc config
            "output_formats": ["json", "xml"],
            "use_compression": True,
            "use_encryption": False, # Set to True and provide password if testing encryption
            # "encryption_password": "supersecretpassword" # Only if use_encryption is True
        }
        print("\nStarting generation job with payload:", json.dumps(job_payload, indent=2))
        job_info = client.start_generation_job(job_payload)
        job_id = job_info["job_id"]
        print(f"Generation Job Started: ID = {job_id}, Initial Status = {job_info['status']}")

        # Poll for job status until completed or failed
        print("\nPolling job status...")
        while True:
            status_info = client.get_job_status(job_id)
            print(f"  Job '{job_id}' Status: {status_info['status']}, Progress: {status_info.get('progress', 0)}%")
            if status_info['status'] == "completed":
                print("Job completed successfully!")
                break
            elif status_info['status'] == "failed":
                print(f"Job failed. Reason: {status_info.get('error_message', 'Unknown error')}")
                break
            time.sleep(5) # Poll every 5 seconds

        # If job completed, get results summary and download output
        if status_info['status'] == "completed":
            print(f"\nFetching results summary for job {job_id}...")
            results_summary = client.get_job_results_summary(job_id)
            print("Results Summary:", json.dumps(results_summary, indent=2))

            download_filename = f"./{job_id}_patient_data.zip"
            print(f"\nDownloading output for job {job_id} to '{download_filename}'...")
            saved_path = client.download_job_output(job_id, download_filename)
            print(f"Output successfully downloaded to: {saved_path}")

        # Example: Delete the configuration template
        # print(f"\nAttempting to delete configuration {config_id}...")
        # client.delete_configuration(config_id)
        # print(f"Configuration {config_id} deleted successfully.")
        # print("\nNote: Deletion example is commented out to allow re-running the script.")

    except Exception as e:
        print(f"\n--- SDK Example Error ---")
        import traceback
        traceback.print_exc()
        # print(f"An error occurred: {e}")
