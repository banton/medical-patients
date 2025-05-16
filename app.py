import os
import json
import uuid
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter, Depends, Security # Added Depends, Security
from fastapi.security import APIKeyHeader # For basic API key auth
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, validator, root_validator # Added validator, root_validator
from typing import Dict, Any, Optional, List, Callable # Added Callable and other typing imports
import zipfile
from io import BytesIO
import tempfile
from datetime import datetime
import hashlib
import shutil
from collections import Counter

from fastapi.requests import Request # For slowapi

# Import slowapi components
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import our patient generator modules
from patient_generator.app import PatientGeneratorApp
from patient_generator.visualization_data import transform_job_data_for_visualization
from patient_generator.database import Database, ConfigurationRepository # Added ConfigurationRepository
from patient_generator.config_manager import ConfigurationManager # Added ConfigurationManager
from patient_generator.schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB # Added Pydantic models
from patient_generator.nationality_data import NationalityDataProvider # Added

app = FastAPI(title="Military Medical Exercise Patient Generator")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS (should be added after rate limiting middleware if it affects OPTIONS requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add SlowAPI middleware
# from slowapi.middleware import SlowAPIMiddleware # This is for Starlette applications
# For FastAPI, decorating routes or routers is more common, or adding exception handler.
# The exception handler is already added. We can decorate specific routes or routers.
# For now, applying to specific routers or globally via dependencies is an option.
# Let's apply it to the main app for all requests for now.
# However, the more common way with FastAPI is to use Depends on routers/routes.
# The example above adds it to app.state and an exception handler.
# To make it active, routes need to be decorated or a middleware added.
# Let's try adding the middleware for global effect.
from slowapi.middleware import SlowAPIMiddleware
app.add_middleware(SlowAPIMiddleware)


# Serve static files (our single-page application)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Visualization router (will be defined later and included)
visualization_router = APIRouter(prefix="/api/visualizations")
# app.include_router(visualization_router) # Will be included after all routes are defined

# Configuration API Router
API_KEY_NAME = "X-API-KEY" # Standard header name for API keys
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# THIS IS A PLACEHOLDER - DO NOT USE IN PRODUCTION
# In a real app, load from env var, secrets manager, or database (hashed)
EXPECTED_API_KEY = "your_secret_api_key_here" 

async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    if api_key_header == EXPECTED_API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials"
        )

config_api_router = APIRouter(
    prefix="/api/v1/configurations", 
    tags=["Configurations"],
    dependencies=[Depends(get_api_key)] # Apply auth to all routes in this router
)

# Use the globally initialized config_repo
# config_repo = ConfigurationRepository(db) # Already initialized globally

@config_api_router.post("/", response_model=ConfigurationTemplateDB, status_code=201)
async def create_configuration_template(config_in: ConfigurationTemplateCreate):
    """
    Create a new configuration template.
    """
    try:
        # The repository method handles converting Pydantic model to DB storage
        # and returns a Pydantic model representing the DB state.
        created_config = config_repo.create_configuration(config_in)
        return created_config
    except Exception as e:
        # Log the exception e
        raise HTTPException(status_code=400, detail=f"Failed to create configuration: {str(e)}")

@config_api_router.get("/", response_model=List[ConfigurationTemplateDB])
async def list_configuration_templates(skip: int = 0, limit: int = 100):
    """
    List all configuration templates with pagination.
    """
    templates = config_repo.list_configurations(skip=skip, limit=limit)
    return templates

@config_api_router.get("/{config_id}", response_model=ConfigurationTemplateDB)
async def get_configuration_template(config_id: str):
    """
    Retrieve a specific configuration template by its ID.
    """
    template = config_repo.get_configuration(config_id)
    if not template:
        raise HTTPException(status_code=404, detail="Configuration template not found")
    return template

@config_api_router.put("/{config_id}", response_model=ConfigurationTemplateDB)
async def update_configuration_template(config_id: str, config_in: ConfigurationTemplateCreate):
    """
    Update an existing configuration template.
    """
    updated_template = config_repo.update_configuration(config_id, config_in)
    if not updated_template:
        raise HTTPException(status_code=404, detail="Configuration template not found for update")
    return updated_template

@config_api_router.delete("/{config_id}", status_code=204) # 204 No Content for successful deletion
async def delete_configuration_template(config_id: str):
    """
    Delete a configuration template by its ID.
    """
    deleted = config_repo.delete_configuration(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Configuration template not found for deletion")
    return # No content to return

@config_api_router.post("/validate/", summary="Validate Configuration Syntax")
async def validate_configuration_syntax(config_in: ConfigurationTemplateCreate):
    """
    Validates the syntax and structure of a provided configuration template
    without saving it. Pydantic models handle most validations.
    """
    # The act of parsing config_in into ConfigurationTemplateCreate already performs
    # many validations defined in the Pydantic models (required fields, types, custom validators).
    # If it parses successfully, the basic structure is valid.
    # More complex business logic validation could be added here if needed.
    return {"valid": True, "message": "Configuration syntax is valid."}

@config_api_router.get("/reference/nationalities/", response_model=List[Dict[str, str]], summary="List Available Nationalities")
async def list_available_nationalities_for_config():
    """
    Lists all available NATO nationalities that can be used in configurations.
    Uses the global nationality_provider instance.
    """
    return nationality_provider.list_available_nationalities()

@config_api_router.get("/reference/condition-types/", response_model=List[str], summary="List Available Condition Types")
async def list_available_condition_types():
    """
    Lists the basic medical condition categories used for injury distribution.
    """
    # These are the keys expected in the injury_distribution dict of a ConfigurationTemplate
    return ["DISEASE", "NON_BATTLE", "BATTLE_TRAUMA"]

# Store job states
jobs: Dict[str, Any] = {} # Added type hint

# Initialize database and other singletons
db = Database.get_instance()
nationality_provider = NationalityDataProvider() # Instantiate once
config_repo = ConfigurationRepository(db) # Instantiate once

# Ensure output directory exists
os.makedirs("output", exist_ok=True)
os.makedirs("temp", exist_ok=True)

class GenerationRequestPayload(BaseModel):
    """Payload for the generation request API"""
    configuration_id: Optional[str] = None
    # Allow providing a full configuration ad-hoc, or use a saved one by ID
    configuration: Optional[ConfigurationTemplateCreate] = None 
    
    output_formats: List[str] = ["json", "xml"]
    use_compression: bool = True
    use_encryption: bool = True
    encryption_password: Optional[str] = None

    # For Pydantic v2, use model_validator.
    from pydantic import model_validator

    @model_validator(mode='after')
    def check_config_source_root(self) -> 'GenerationRequestPayload': # Changed cls, model to self
        if self.configuration_id is None and self.configuration is None:
            raise ValueError("Either configuration_id or an ad-hoc configuration object must be provided.")
        if self.configuration_id is not None and self.configuration is not None:
            raise ValueError("Provide either configuration_id or an ad-hoc configuration, not both.")
        return self

@app.get("/")
async def get_index():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/visualizations")
async def get_visualizations_page():
    """Serve the visualizations HTML page"""
    return FileResponse("static/visualizations.html")

@app.post("/api/generate")
async def generate_patients(payload: GenerationRequestPayload, background_tasks: BackgroundTasks):
    """Start a patient generation job using a saved configuration ID or an ad-hoc configuration."""
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Prepare for ConfigurationManager
    # db_instance will be available globally as `db`
    # nationality_provider is also global
    
    # The actual config that will be used for the job
    # This will be populated after loading/validating the config from payload
    effective_config_dict: Optional[Dict[str, Any]] = None 

    # Create job record in memory and database (initial status)
    job_data: Dict[str, Any] = {
        "job_id": job_id,
        "status": "initializing", # New initial status
        "config_source_payload": payload.model_dump(), # Store what was received
        "config_used": None, # Will be filled after loading
        "created_at": datetime.now().isoformat(),
        "output_files": [],
        "progress": 0,
        "progress_details": {
            "current_phase": "Queued",
            "phase_description": "Job is queued for processing",
            "phase_progress": 0,
            "time_estimates": {"total": None, "phase": None}
        },
        "summary": {},
    }
    
    # Store in memory (keep for backward compatibility)
    jobs[job_id] = job_data
    
    # Store in database
    db.save_job(job_data)
    
    # Start generation task in background
    # Pass the full payload to run_generator_job, it will handle config loading
    background_tasks.add_task(
        run_generator_job, 
        job_id=job_id, 
        request_payload=payload # Pass the whole payload
    )
    
    return {"job_id": job_id, "status": "initializing"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a generation job"""
    # Try to get job from memory first
    if job_id in jobs:
        return jobs[job_id]
    
    # If not in memory, try to get from database
    job_data = db.get_job(job_id)
    if job_data:
        # Cache in memory for faster access
        jobs[job_id] = job_data
        return job_data
    
    # Not found in either place
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/api/jobs")
async def list_all_jobs():
    """List all jobs known to the server (from in-memory cache)."""
    # Sort jobs by creation time, most recent first
    sorted_jobs = sorted(list(jobs.values()), key=lambda j: str(j.get("created_at", "")), reverse=True)
    return sorted_jobs

@app.get("/api/jobs/{job_id}/results", summary="Get Job Results Summary")
async def get_job_results(job_id: str):
    """
    Get the results summary of a completed generation job.
    """
    job_data = db.get_job(job_id) # Fetch latest from DB
    if not job_data:
        # Fallback to in-memory cache if DB somehow doesn't have it but memory does
        if job_id in jobs:
            job_data = jobs[job_id]
        else:
            raise HTTPException(status_code=404, detail="Job not found")

    if job_data.get("status") != "completed":
        raise HTTPException(status_code=400, detail=f"Job {job_id} is not yet completed. Current status: {job_data.get('status')}")

    summary = job_data.get("summary")
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary not available for job {job_id}.")
    
    return summary

@app.get("/api/download/{job_id}")
async def download_job_output(job_id: str):
    """Download the generated files as a ZIP archive"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    
    # Create a ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        output_dir = f"output/{job_id}"
        for file_name in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file_name)
            zip_file.write(file_path, file_name)
    
    # Seek to the beginning of the buffer
    zip_buffer.seek(0)
    
    # Create a temporary file to serve
    temp_file_path = f"temp/patients_{job_id}.zip"
    with open(temp_file_path, "wb") as f:
        f.write(zip_buffer.getvalue())
    
    # Return the file response
    return FileResponse(
        path=temp_file_path,
        filename=f"patients_{job_id}.zip",
        media_type="application/zip"
    )

@app.get("/api/config/defaults")
async def get_default_config_info():
    """Provides info on how to get a default configuration."""
    # Actual default config should be a saved template in the DB.
    # This endpoint can guide the user or return a predefined "default" template ID.
    # For now, returning a placeholder.
    # In future, could load a config template marked as 'default' from DB.
    return {
        "message": "Default configurations are managed as templates in the database.",
        "example_default_id": "default_scenario_v1" 
        # This ID would need to exist in the configuration_templates table.
    }

# Visualization API Endpoints
visualization_router = APIRouter(prefix="/api/visualizations")

@visualization_router.get("/dashboard-data")
async def get_dashboard_data(job_id: str = None):
    """Get data for the visualization dashboard"""
    target_job_data = None
    if job_id:
        if job_id in jobs and jobs[job_id]["status"] == "completed":
            target_job_data = jobs[job_id]
        else:
            # If job_id is provided but not found or not completed, it's an error
            raise HTTPException(status_code=404, detail=f"Completed job {job_id} not found or not completed.")
    else:
        # Find the most recent completed job if no job_id is specified
        completed_jobs_list = [j for j in jobs.values() if j["status"] == "completed" and j.get("completed_at")]
        if completed_jobs_list:
            target_job_data = max(completed_jobs_list, key=lambda j: str(j.get("completed_at", "")))
        else:
            # No job_id provided and no completed jobs exist
            raise HTTPException(status_code=404, detail="No completed jobs available for visualization.")

    if not target_job_data:
        # This case should be covered, but as a fallback
        raise HTTPException(status_code=404, detail="No suitable job data found for visualization.")
    
    try:
        # The transform_job_data_for_visualization function expects the full job dictionary
        dashboard_data = transform_job_data_for_visualization(target_job_data)
        return dashboard_data
    except Exception as e:
        print(f"Error transforming data for job {target_job_data.get('job_id', 'unknown')}: {e}")
        raise HTTPException(status_code=500, detail="Failed to transform data for visualization.")

@visualization_router.get("/job-list")
async def get_visualization_job_list():
    """Get a list of jobs that can be used for visualization"""
    # Get completed jobs from database (faster than filtering in-memory jobs)
    db_jobs = db.get_all_jobs(status="completed")
    
    job_list = []
    for job_data in db_jobs:
        total_patients = job_data.get("summary", {}).get("total_patients")
        if total_patients is None:  # Fallback to config if summary not detailed
            total_patients = job_data.get("config", {}).get("total_patients", 0)
        
        job_list.append({
            "job_id": job_data["job_id"],
            "total_patients": total_patients,
            "created_at": job_data.get("created_at", "")
        })
        
    return job_list

@visualization_router.get("/patient-detail/{patient_id}")
async def get_patient_detail(patient_id: str, job_id: str = None):
    """Get detailed data for a specific patient"""
    target_job = None
    if job_id and job_id in jobs and jobs[job_id]["status"] == "completed":
        target_job = jobs[job_id]
    else:
        completed_jobs_list = [j for j in jobs.values() if j["status"] == "completed" and j.get("completed_at")]
        if completed_jobs_list:
            target_job = max(completed_jobs_list, key=lambda j: str(j.get("completed_at", "")))
    
    if not target_job:
        raise HTTPException(status_code=404, detail="No completed jobs found to retrieve patient data from.")
    
    # In a real implementation, you would extract the specific patient from the target_job data.
    # For now, return a mock patient as per the guide
    patient_data = {
        "id": patient_id,
        "nationality": "POL",
        "front": "Polish",
        "age": 28,
        "gender": "male",
        "day_of_injury": "Day 2",
        "injury_type": "BATTLE_TRAUMA",
        "triage_category": "T2",
        "current_status": "RTD",
        "demographics": {
            "given_name": "Jakub",
            "family_name": "Kowalski",
            "gender": "male",
            "birthdate": "1997-03-15",
            "id_number": "97031512345",
            "blood_type": "A",
            "weight": 82.4
        },
        "primary_condition": {
            "code": "125689001",
            "display": "Shrapnel injury",
            "severity": "Moderate",
            "severity_code": "371924009"
        },
        "additional_conditions": [
            {
                "code": "125605004",
                "display": "Traumatic shock",
                "severity": "Mild to moderate",
                "severity_code": "371923003"
            }
        ],
        "treatment_history": [
            {
                "facility": "POI",
                "date": "2025-06-02T08:30:00Z",
                "treatments": [],
                "observations": []
            },
            {
                "facility": "R1",
                "date": "2025-06-02T09:15:00Z",
                "treatments": [
                    {"code": "225317000", "display": "Initial dressing of wound"}
                ],
                "observations": [
                    {"code": "8310-5", "display": "Body temperature", "value": 36.8, "unit": "Cel"},
                    {"code": "8867-4", "display": "Heart rate", "value": 102, "unit": "/min"},
                    {"code": "8480-6", "display": "Systolic blood pressure", "value": 115, "unit": "mm[Hg]"}
                ]
            },
            {
                "facility": "R2",
                "date": "2025-06-02T11:45:00Z",
                "treatments": [
                    {"code": "225358003", "display": "Wound care"},
                    {"code": "385968004", "display": "Fluid management"}
                ],
                "observations": [
                    {"code": "8310-5", "display": "Body temperature", "value": 37.1, "unit": "Cel"},
                    {"code": "8867-4", "display": "Heart rate", "value": 88, "unit": "/min"},
                    {"code": "8480-6", "display": "Systolic blood pressure", "value": 125, "unit": "mm[Hg]"},
                    {"code": "718-7", "display": "Hemoglobin", "value": 13.5, "unit": "g/dL"}
                ]
            },
            {
                "facility": "RTD",
                "date": "2025-06-03T14:20:00Z",
                "treatments": [],
                "observations": []
            }
        ]
    }
    return patient_data

app.include_router(visualization_router)
app.include_router(config_api_router) # Include the new configuration router

@app.on_event("startup")
async def startup_event():
    """Startup event to clean temporary files and load jobs from database"""
    # Existing code for temp directory cleanup
    if os.path.exists("temp"):
        try:
            shutil.rmtree("temp")
            os.makedirs("temp")
        except Exception as e:
            print(f"Warning: Could not clean temp directory: {e}")
    
    # Load jobs from database and synchronize with filesystem
    try:
        # Step 1: Get ALL jobs from DB to check against filesystem
        all_db_jobs_for_sync = db.get_all_jobs(limit=None) # Get all jobs, no limit
        
        deleted_count = 0
        for job_entry in all_db_jobs_for_sync:
            job_id_to_check = job_entry["job_id"]
            expected_output_dir = f"output/{job_id_to_check}"
            if not os.path.isdir(expected_output_dir):
                print(f"Output directory {expected_output_dir} not found for job {job_id_to_check}. Removing from database.")
                db.delete_job(job_id_to_check)
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"Synchronized database: Removed {deleted_count} orphaned job entries.")

        # Step 2: Load remaining jobs into memory (e.g., recent 100)
        # This now loads from a potentially cleaned-up database
        db_jobs_to_load = db.get_all_jobs(limit=100) 
        for job_data in db_jobs_to_load:
            jobs[job_data["job_id"]] = job_data
        print(f"Loaded {len(db_jobs_to_load)} jobs into memory from database after sync.")

    except Exception as e:
        print(f"Warning: Could not load/synchronize jobs from database: {e}")

async def run_generator_job(job_id: str, request_payload: GenerationRequestPayload):
    """Run the generator job in the background using ConfigurationManager."""
    
    config_manager = ConfigurationManager(db) # Use global db instance
    loaded_config_template: Optional[ConfigurationTemplateDB] = None

    try:
        if request_payload.configuration_id:
            if not config_manager.load_configuration(request_payload.configuration_id):
                raise HTTPException(status_code=404, detail=f"Configuration ID '{request_payload.configuration_id}' not found.")
            loaded_config_template = config_manager.get_active_configuration()
        elif request_payload.configuration:
            # For ad-hoc configuration, we need to "load" it into the manager.
            # This might involve saving it first if ConfigurationManager strictly works with saved configs,
            # or adapting ConfigurationManager to accept an in-memory Pydantic object.
            # For now, let's assume we might need to save ad-hoc configs to make them "active".
            # This part needs careful design: does an ad-hoc config get saved? Or used transiently?
            # The API proposal implies ad-hoc configs are used directly for a job.
            # Let's adapt ConfigurationManager or create a temporary active config.
            
            # Simplification: If ad-hoc, we create a ConfigurationTemplateDB-like object in memory.
            # This bypasses saving it for now. A more robust solution might save it or have
            # ConfigurationManager accept a ConfigurationTemplateCreate directly.
            now = datetime.utcnow()
            temp_id = f"adhoc_{str(uuid.uuid4())}" # Temporary ID for this ad-hoc config
            loaded_config_template = ConfigurationTemplateDB(
                id=temp_id, # Not saved, just for in-memory representation
                name=request_payload.configuration.name,
                description=request_payload.configuration.description,
                front_configs=request_payload.configuration.front_configs,
                facility_configs=request_payload.configuration.facility_configs,
                total_patients=request_payload.configuration.total_patients,
                injury_distribution=request_payload.configuration.injury_distribution,
                created_at=now,
                updated_at=now
            )
            # "Activate" it in the manager (conceptually)
            config_manager._active_configuration = loaded_config_template 
            config_manager._config_id_loaded = temp_id # Mark as loaded
            print(f"Using ad-hoc configuration: {loaded_config_template.name}")
        else:
            # This case should be caught by Pydantic validator in GenerationRequestPayload
            raise ValueError("No configuration source provided in payload.")

        if not loaded_config_template: # Should not happen if logic above is correct
             raise ValueError("Failed to obtain an effective configuration for the job.")

        jobs[job_id]["status"] = "running"
        jobs[job_id]["config_used"] = loaded_config_template.model_dump(mode='json') # Store the actual config used
        db.save_job(jobs[job_id])
        
        # Initialize PatientGeneratorApp with the configured ConfigurationManager
        # The nationality_provider is already a global instance
        generator = PatientGeneratorApp(config_manager, nationality_provider)
        
        def job_progress_callback(overall_progress: int, details: Dict[str, Any]):
            """Callback to update job progress in memory and DB."""
            jobs[job_id]["progress"] = overall_progress
            jobs[job_id]["progress_details"] = details
            
            # Update summary if present in details (as per PatientGeneratorApp's final callback)
            if "summary" in details:
                jobs[job_id]["summary"] = details["summary"]
            
            if overall_progress % 10 == 0 or overall_progress == 100 : # Save to DB periodically
                db.save_job(jobs[job_id])

        # Runtime output parameters from the payload
        encryption_key_bytes: Optional[bytes] = None
        if request_payload.use_encryption and request_payload.encryption_password:
            encryption_key_bytes = hashlib.pbkdf2_hmac(
                'sha256', 
                request_payload.encryption_password.encode(), 
                b'salt', # TODO: Use a unique salt per job or a configurable salt
                100000, 
                dklen=32
            )
        elif request_payload.use_encryption: # No password, but encryption enabled
            encryption_key_bytes = os.urandom(32)


        # Run the generator
        # The run method now returns patients, bundles, output_files, summary
        _patients, _bundles, output_files_list, job_summary = generator.run(
            output_directory=f"output/{job_id}",
            output_formats=request_payload.output_formats,
            use_compression=request_payload.use_compression,
            use_encryption=request_payload.use_encryption,
            encryption_key=encryption_key_bytes,
            progress_callback=job_progress_callback
        )
        
        # Store patients_data in memory (consider alternatives for very large data)
        # jobs[job_id]["patients_data"] = patients # This was in old code, might be too memory intensive

        jobs[job_id]["output_files"] = output_files_list # Already a list of paths
        jobs[job_id]["summary"] = job_summary # Use summary returned by generator.run()
        
        file_types_counter = Counter([os.path.splitext(f)[1] for f in output_files_list])
        jobs[job_id]["file_types"] = dict(file_types_counter)
        
        total_size_val = sum(os.path.getsize(f) for f in output_files_list if os.path.exists(f))
        jobs[job_id]["total_size"] = total_size_val
        jobs[job_id]["total_size_formatted"] = format_size(total_size_val)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        db.save_job(jobs[job_id])
        
    except HTTPException: # Re-raise HTTPExceptions to be handled by FastAPI
        raise
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        db.save_job(jobs[job_id])
        print(f"Error in job {job_id}: {e}") # Log this properly

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event to close database connection"""
    try:
        db.close_pool() # Changed from db.close()
        print("Database connection pool closed.")
    except Exception as e:
        print(f"Warning: Error closing database connection pool: {e}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
