# patient_generator_sdk.py
import requests
import json
from typing import Optional, List, Dict, Any

class PatientGeneratorClient:
    """Python client for the Military Medical Exercise Patient Generator API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the client with the API base URL and optional API key.
        Args:
            base_url: The base URL of the API (e.g., http://localhost:8000)
            api_key: Optional API key for authentication.
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
# if __name__ == "__main__":
#     client = PatientGeneratorClient(base_url="http://localhost:8000", api_key="your_secret_api_key_here")
#     try:
#         print("Available Nationalities:", client.list_reference_nationalities())
#         print("Available Condition Types:", client.list_reference_condition_types())
        
#         # Example: Create a configuration
#         new_config_payload = {
#             "name": "SDK Test Scenario",
#             "description": "A test scenario created via SDK",
#             "front_configs": [
#                 {"id": "sdk_front1", "name": "SDK Alpha Front", "nationality_distribution": {"USA": 100.0}, "casualty_rate": 0.5}
#             ],
#             "facility_configs": [
#                 {"id": "sdk_r1", "name": "SDK Role 1", "kia_rate": 0.1, "rtd_rate": 0.7},
#                 {"id": "sdk_r2", "name": "SDK Role 2", "kia_rate": 0.05, "rtd_rate": 0.8}
#             ],
#             "total_patients": 50,
#             "injury_distribution": {"BATTLE_TRAUMA": 60.0, "DISEASE": 40.0}
#         }
#         created_template = client.create_configuration(new_config_payload)
#         print("\nCreated Configuration Template:", json.dumps(created_template, indent=2))
#         config_id = created_template["id"]

#         print("\nListing Configurations:")
#         configs = client.list_configurations(limit=5)
#         for cfg in configs:
#             print(f" - {cfg['name']} (ID: {cfg['id']}, Version: {cfg['version']})")

#         print(f"\nGetting Configuration {config_id}:")
#         retrieved_config = client.get_configuration(config_id)
#         print(json.dumps(retrieved_config, indent=2))

#         # Example: Start a generation job
#         job_payload = {
#             "configuration_id": config_id,
#             "output_formats": ["json"],
#             "use_compression": False,
#             "use_encryption": False
#         }
#         job_info = client.start_generation_job(job_payload)
#         job_id = job_info["job_id"]
#         print(f"\nStarted Generation Job: {job_id}, Status: {job_info['status']}")

#         # Poll for job status
#         while True:
#             status_info = client.get_job_status(job_id)
#             print(f"Job {job_id} Status: {status_info['status']}, Progress: {status_info['progress']}%")
#             if status_info['status'] in ['completed', 'failed']:
#                 break
#             time.sleep(2)
        
#         if status_info['status'] == 'completed':
#             print(f"\nJob {job_id} Results Summary:")
#             results = client.get_job_results_summary(job_id)
#             print(json.dumps(results, indent=2))

#             download_path = f"./{job_id}_output.zip"
#             print(f"\nDownloading output for job {job_id} to {download_path}...")
#             client.download_job_output(job_id, download_path)
#             print(f"Downloaded to {download_path}")

#     except Exception as e:
#         print(f"\nAn SDK error occurred: {e}")
