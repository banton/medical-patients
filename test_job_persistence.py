"""
Test job persistence in database
"""
import json
import time
import requests

API_URL = "http://localhost:8000/api/v1"
API_KEY = "dev_secret_key_27e9010dd17a442a1cda3a0490a95611"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Test configuration for a moderate-sized job
test_config = {
    "configuration": {
        "name": "Database Persistence Test",
        "description": "Testing job persistence in PostgreSQL",
        "total_patients": 500,
        "injury_distribution": {
            "Disease": 40.0,
            "Battle Injury": 35.0,
            "Non-Battle Injury": 25.0
        },
        "front_configs": [
            {
                "id": "test_front",
                "name": "Test Front",
                "casualty_rate": 1.0,
                "nationality_distribution": [
                    {"nationality_code": "USA", "percentage": 100.0}
                ]
            }
        ],
        "facility_configs": [
            {
                "id": "poi",
                "name": "Point of Injury",
                "capacity": None,
                "kia_rate": 0.025,
                "rtd_rate": 0.10
            },
            {
                "id": "role1",
                "name": "Role 1",
                "capacity": 50,
                "kia_rate": 0.01,
                "rtd_rate": 0.15
            },
            {
                "id": "role2",
                "name": "Role 2",
                "capacity": 100,
                "kia_rate": 0.005,
                "rtd_rate": 0.30
            },
            {
                "id": "role3",
                "name": "Role 3",
                "capacity": 300,
                "kia_rate": 0.002,
                "rtd_rate": 0.25
            },
            {
                "id": "role4",
                "name": "Role 4",
                "capacity": 1000,
                "kia_rate": 0.001,
                "rtd_rate": 0.40
            }
        ]
    },
    "output_formats": ["json"],
    "use_compression": False
}

print("🧪 Testing Job Persistence in Database")
print("=" * 60)

# 1. Create a job
print("1️⃣ Creating job...")
response = requests.post(f"{API_URL}/generation/", headers=HEADERS, json=test_config)
if response.status_code != 201:
    print(f"❌ Failed to create job: {response.status_code}")
    print(response.text)
    exit(1)

job_data = response.json()
job_id = job_data["job_id"]
print(f"✅ Job created: {job_id}")

# 2. Check job appears in list
print("\n2️⃣ Checking job list...")
response = requests.get(f"{API_URL}/jobs/", headers=HEADERS)
if response.status_code == 200:
    jobs = response.json()
    job_found = any(job["job_id"] == job_id for job in jobs)
    if job_found:
        print(f"✅ Job found in list")
    else:
        print(f"❌ Job NOT found in list!")
else:
    print(f"❌ Failed to get job list: {response.status_code}")

# 3. Monitor job progress
print("\n3️⃣ Monitoring job progress...")
for i in range(30):  # Monitor for up to 30 seconds
    response = requests.get(f"{API_URL}/jobs/{job_id}", headers=HEADERS)
    if response.status_code != 200:
        print(f"❌ Failed to get job status: {response.status_code}")
        break
        
    status_data = response.json()
    status = status_data["status"]
    progress = status_data.get("progress", 0)
    
    print(f"   Status: {status} - Progress: {progress}%", end='\r')
    
    if status in ["completed", "failed", "cancelled"]:
        print(f"\n   Final status: {status}")
        break
        
    time.sleep(1)

# 4. Verify job is in database
print("\n4️⃣ Verifying database persistence...")
# This would be done through psql, but we'll check via API
response = requests.get(f"{API_URL}/jobs/{job_id}", headers=HEADERS)
if response.status_code == 200:
    print(f"✅ Job {job_id} is persisted and retrievable")
    job_data = response.json()
    print(f"   Created at: {job_data.get('created_at', 'Unknown')}")
    print(f"   Status: {job_data.get('status', 'Unknown')}")
    print(f"   Progress: {job_data.get('progress', 0)}%")
else:
    print(f"❌ Failed to retrieve job from database")

print("\n" + "="*60)
print("Test Complete!")
print("="*60)