import os
import json
import uuid
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
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

# Store job states
jobs = {}

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

@app.post("/api/generate")
async def generate_patients(config: GeneratorConfig, background_tasks: BackgroundTasks):
    """Start a patient generation job"""
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Create job record
    jobs[job_id] = {
        "status": "queued",
        "config": config.dict(),
        "created_at": datetime.now().isoformat(),
        "output_files": [],
        "progress": 0,
        "summary": {},
    }
    
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
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

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

@app.on_event("startup")
async def startup_event():
    """Startup event to clean temporary files"""
    if os.path.exists("temp"):
        try:
            shutil.rmtree("temp")
            os.makedirs("temp")
        except Exception as e:
            print(f"Warning: Could not clean temp directory: {e}")

async def run_generator_job(job_id: str, config: GeneratorConfig):
    """Run the generator job in the background"""
    try:
        # Update job status
        jobs[job_id]["status"] = "running"
        
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
        def progress_callback(percent, patient_data=None):
            jobs[job_id]["progress"] = percent
            
            # If patient data is provided, update the job summary
            if patient_data:
                jobs[job_id]["summary"] = patient_data
        
        # Run the generator with progress reporting
        patients, bundles = generator.run(progress_callback=progress_callback)
        
        # Create a summary of the generation
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
        
    except Exception as e:
        # Update job status on error
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"Error in job {job_id}: {e}")

def format_size(size_bytes):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

if __name__ == "__main__":
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)