import os
import json
import uuid
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, APIRouter
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import zipfile
from io import BytesIO
import tempfile
from datetime import datetime
import hashlib
import shutil
from collections import Counter

# Import our patient generator modules
from patient_generator.app import PatientGeneratorApp
from patient_generator.visualization_data import transform_job_data_for_visualization
from patient_generator.database import Database

app = FastAPI(title="Military Medical Exercise Patient Generator")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (our single-page application)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Visualization router (will be defined later and included)
# Forward declaration for clarity, actual definition below other routes
# visualization_router = APIRouter(prefix="/api/visualizations") 
# app.include_router(visualization_router) # Will be moved to after router definition

# Store job states
jobs = {}

# Initialize database
db = Database.get_instance()

# Ensure output directory exists
os.makedirs("output", exist_ok=True)
os.makedirs("temp", exist_ok=True)

class GeneratorConfig(BaseModel):
    """Configuration for the patient generator"""
    total_patients: int = 1440
    polish_front_percent: float = 50.0
    estonian_front_percent: float = 33.3
    finnish_front_percent: float = 16.7
    disease_percent: float = 52.0
    non_battle_percent: float = 33.0
    battle_trauma_percent: float = 15.0
    formats: list = ["json", "xml"]
    use_compression: bool = True
    use_encryption: bool = True
    base_date: str = "2025-06-01"
    encryption_password: str = ""

@app.get("/")
async def get_index():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")

@app.get("/visualizations")
async def get_visualizations_page():
    """Serve the visualizations HTML page"""
    return FileResponse("static/visualizations.html")

@app.post("/api/generate")
async def generate_patients(config: GeneratorConfig, background_tasks: BackgroundTasks):
    """Start a patient generation job"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create job record in memory and database
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "config": config.dict(),
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
    background_tasks.add_task(
        run_generator_job, 
        job_id=job_id, 
        config=config
    )
    
    return {"job_id": job_id, "status": "queued"}

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
async def get_default_config():
    """Get default configuration values"""
    return GeneratorConfig().dict()

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

async def run_generator_job(job_id: str, config: GeneratorConfig):
    """Run the generator job in the background"""
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        db.save_job(jobs[job_id])  # Save to database
        
        # Convert web config to generator config
        generator_config = {
            "total_patients": config.total_patients,
            "front_distribution": {
                "Polish": config.polish_front_percent / 100,
                "Estonian": config.estonian_front_percent / 100,
                "Finnish": config.finnish_front_percent / 100
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
                "DISEASE": config.disease_percent / 100,
                "NON_BATTLE": config.non_battle_percent / 100,
                "BATTLE_TRAUMA": config.battle_trauma_percent / 100
            },
            "output_formats": config.formats,
            "output_directory": f"output/{job_id}",
            "base_date": config.base_date,
            "use_compression": config.use_compression,
            "use_encryption": config.use_encryption
        }
        
        # Set encryption key if provided
        if config.encryption_password:
            # Generate a 32-byte key from the password
            generator_config["encryption_key"] = hashlib.pbkdf2_hmac(
                'sha256', 
                config.encryption_password.encode(), 
                b'salt', 
                100000, 
                dklen=32
            )
        else:
            # Random key if no password provided
            generator_config["encryption_key"] = os.urandom(32)
        
        # Initialize and run the generator
        generator = PatientGeneratorApp(generator_config)
        
        # Update progress callback
        def progress_callback(percent, data=None, progress_info=None):
            jobs[job_id]["progress"] = percent
            
            # Update progress details if provided
            if progress_info:
                jobs[job_id]["progress_details"] = progress_info
            
            # If summary data is provided, update the job summary
            if isinstance(data, dict) and "nationalities" in data:
                jobs[job_id]["summary"] = data
            
            # Save to database (not too frequently to avoid performance issues)
            if percent % 10 == 0 or percent == 100:
                db.save_job(jobs[job_id])
        
        # Run the generator with progress reporting
        patients, bundles = generator.run(progress_callback=progress_callback)
        
        # Store the generated patient objects for potential later use (e.g., detailed visualization)
        # Note: This can consume memory. For very large jobs or many concurrent jobs,
        # consider serializing this data to disk and loading on demand.
        jobs[job_id]["patients_data"] = patients

        # Create a summary of the generation if not already set
        if "total_patients" not in jobs[job_id]["summary"]:
            nationality_counts = Counter([p.nationality for p in patients])
            front_counts = Counter([p.front for p in patients])
            injury_counts = Counter([p.injury_type for p in patients])
            status_counts = Counter([p.current_status for p in patients])
            
            # Update job summary
            jobs[job_id]["summary"] = {
                "total_patients": len(patients),
                "nationalities": {nat: count for nat, count in nationality_counts.items()},
                "fronts": {front: count for front, count in front_counts.items()},
                "injury_types": {injury: count for injury, count in injury_counts.items()},
                "final_status": {status: count for status, count in status_counts.items()},
                "kia_count": status_counts.get("KIA", 0),
                "rtd_count": status_counts.get("RTD", 0),
                "still_in_treatment": sum(status_counts.get(status, 0) for status in ["R1", "R2", "R3", "R4"])
            }
        
        # Update job output files
        output_dir = generator_config["output_directory"]
        jobs[job_id]["output_files"] = os.listdir(output_dir)
        
        # Count file types
        file_types = Counter([os.path.splitext(f)[1] for f in jobs[job_id]["output_files"]])
        jobs[job_id]["file_types"] = {ext: count for ext, count in file_types.items()}
        
        # Calculate total file size
        total_size = sum(os.path.getsize(os.path.join(output_dir, f)) for f in jobs[job_id]["output_files"])
        jobs[job_id]["total_size"] = total_size
        jobs[job_id]["total_size_formatted"] = format_size(total_size)
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        db.save_job(jobs[job_id])  # Save to database
        
    except Exception as e:
        # Update job status on error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        db.save_job(jobs[job_id])  # Save to database
        print(f"Error in job {job_id}: {e}")

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
        db.close()
        print("Database connection closed")
    except Exception as e:
        print(f"Warning: Error closing database connection: {e}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)
