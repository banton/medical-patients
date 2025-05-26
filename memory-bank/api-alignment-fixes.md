# API Alignment Fixes

## Issues Fixed

### 1. API Key Header Case Sensitivity
- **Issue**: Frontend used `X-API-KEY` but backend expects `X-API-Key`
- **Fixed**: Updated `api-config.js` to use correct case-sensitive header

### 2. Jobs List Endpoint
- **Issue**: Frontend called non-existent `/api/visualizations/job-list`
- **Fixed**: Updated to use correct endpoint `/api/jobs/`

### 3. Missing Authentication Headers
- **Issue**: Visualization dashboard didn't include API key in requests
- **Fixed**: Added API key headers to all fetch calls in `visualization-dashboard.js`

### 4. Field Name Mismatches (snake_case vs camelCase)
- **Issue**: Backend returns snake_case fields but frontend expects camelCase
- **Fixed**: Added `transformApiResponse()` function to convert:
  - `nationality_distribution` → `nationalityDistribution`
  - `injury_distribution` → `injuryDistribution`
  - `facility_stats` → `facility_usage`
  - `front_distribution` → `front_comparison`
  - etc.

### 5. Job Description Field
- **Issue**: Frontend expected `job.description` but Job model doesn't have this field
- **Fixed**: Updated to use `job.config?.name` or fallback to job ID and status

### 6. Template Data Completeness
- **Issue**: Template casualty rates didn't add up to 100%
- **Fixed**: Updated all templates to have proper percentage distributions

## API Call Structure Alignment

### Patient Generation Request (Frontend → Backend)
```javascript
{
  "configuration": {
    "name": "Scenario Name",
    "description": "Description",
    "front_configs": [...],
    "facility_configs": [...],
    "total_patients": 100,
    "injury_distribution": {
      "Disease": 50.0,
      "Non-Battle Injury": 30.0,
      "Battle Injury": 20.0
    }
  }
}
```

### Headers Required
```javascript
{
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'X-API-Key': 'your_secret_api_key_here'  // Case-sensitive!
}
```

### Endpoints Used by UI
- GET `/api/jobs/` - List all jobs
- GET `/api/jobs/{job_id}` - Get job status
- GET `/api/visualizations/dashboard-data?job_id={job_id}` - Get dashboard data
- GET `/api/visualizations/patient-detail/{patient_id}?job_id={job_id}` - Get patient details
- POST `/api/generate/ad-hoc` - Generate patients

## Testing
All API calls from the UI now match the expected backend structure and include proper authentication.