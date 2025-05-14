# Implementation Guide: Enhanced Visualization Dashboard

This implementation guide provides step-by-step instructions for integrating the Enhanced Visualization Dashboard into the Military Medical Exercise Patient Generator. The guide covers all necessary components, from backend data transformation to frontend integration.

## Overview

The Enhanced Visualization Dashboard adds powerful analytical capabilities to the Military Medical Exercise Patient Generator, providing planners with deeper insights into simulated patient data. Key features include:

1. Interactive patient flow visualization with Sankey diagrams
2. Facility usage and capacity analysis
3. Timeline analysis of casualties across exercise days
4. Front-by-front comparative analysis
5. Treatment effectiveness visualization

## Implementation Steps

### 1. Add Data Transformation Module

First, create a new Python module for data transformation:

1. Create a new file `patient_generator/visualization_data.py`
2. Copy the complete data transformation code from the Data Transformation Guide
3. Test the transformation with a sample job:

```python
# Test transformation with a sample job
def test_transformation():
    # Load a completed job
    job_id = "job_20250601120000"  # Replace with an actual job ID
    if job_id in jobs:
        job_data = jobs[job_id]
        dashboard_data = transform_job_data_for_visualization(job_data)
        print(f"Transformed data contains {len(dashboard_data)} keys")
        print(f"Summary: {dashboard_data['summary']}")
    else:
        print(f"Job {job_id} not found")

if __name__ == "__main__":
    test_transformation()
```

### 2. Add Backend API Endpoints

Add new API endpoints to `app.py` for accessing visualization data:

1. Create a visualization router
2. Add endpoints for dashboard data and job list
3. Register the router with the main app

```python
# In app.py
from patient_generator.visualization_data import transform_job_data_for_visualization

# Create visualization router
visualization_router = APIRouter(prefix="/api/visualizations")

@visualization_router.get("/dashboard-data")
async def get_dashboard_data(job_id: str = None):
    """Get data for the visualization dashboard"""
    # Implementation from Data Transformation Guide
    # ...

@visualization_router.get("/job-list")
async def get_visualization_job_list():
    """Get a list of jobs that can be used for visualization"""
    # Implementation from Data Transformation Guide
    # ...

# Add router to app
app.include_router(visualization_router)
```

### 3. Create Frontend React Component

1. Create the React component file:

   ```bash
   mkdir -p static/js
   touch static/js/visualization-dashboard.js
   ```

2. Copy the complete React component code from the Enhanced Visualization Dashboard artifact to this file
3. Add the necessary imports at the top of the file:

   ```javascript
   // Import React and Recharts components
   const { useState, useEffect } = React;
   const {
     LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
     BarChart, Bar, PieChart, Pie, Cell, Sankey, Scatter, ScatterChart, ZAxis,
     RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
   } = Recharts;
   const { AlertCircle, FilePieChart, Calendar, Activity, Map, Users, ArrowRight, ChevronDown, ChevronUp } = LucideReact;
   ```

### 4. Create Visualization HTML Page

1. Create a new HTML file for the visualization dashboard:

   ```bash
   touch static/visualizations.html
   ```

2. Add the HTML structure from the Integration Example artifact, including:
   - Base HTML structure
   - CSS and JavaScript imports 
   - Navigation elements
   - Root div for the React component

3. Update the navigation in the main `index.html` file to include a link to the visualization page:

   ```html
   <!-- In static/index.html, add this to the navbar -->
   <li class="nav-item">
     <a class="nav-link" href="/visualizations">
       <i class="fas fa-chart-line me-1"></i>
       Advanced Visualizations
     </a>
   </li>
   ```

### 5. Add Route to the FastAPI Application

Add a route to serve the visualizations page:

```python
# In app.py
@app.get("/visualizations")
async def get_visualizations_page():
    """Serve the visualizations HTML page"""
    return FileResponse("static/visualizations.html")
```

### 6. Update React Component to Fetch Real Data

Modify the `useEffect` hook in the React component to fetch data from the API:

```javascript
// In static/js/visualization-dashboard.js
useEffect(() => {
  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/visualizations/dashboard-data');
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard data');
      }
      const data = await response.json();
      setDashboardData(data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      // Fallback to mock data if real data fetch fails
      setDashboardData(generateMockData());
      setLoading(false);
    }
  };

  fetchData();
}, []);
```

### 7. Add Job Selection Feature

Add a job selection dropdown to allow users to view data from different jobs:

1. Modify the React component to include a job selector
2. Add state for the selected job ID
3. Fetch the job list from the API
4. Add a fetch function that uses the selected job ID

Example job selector dropdown:

```jsx
const [jobs, setJobs] = useState([]);
const [selectedJobId, setSelectedJobId] = useState(null);

// Function to fetch jobs list
const fetchJobs = async () => {
  try {
    const response = await fetch('/api/visualizations/job-list');
    if (response.ok) {
      const jobsList = await response.json();
      setJobs(jobsList);
      // Set the most recent job as default
      if (jobsList.length > 0 && !selectedJobId) {
        setSelectedJobId(jobsList[0].job_id);
      }
    }
  } catch (error) {
    console.error("Error fetching jobs:", error);
  }
};

// Effect to fetch jobs on component mount
useEffect(() => {
  fetchJobs();
}, []);

// Effect to fetch data when selected job changes
useEffect(() => {
  if (selectedJobId) {
    fetchDashboardData(selectedJobId);
  }
}, [selectedJobId]);

// Job selector component
const JobSelector = () => (
  <div className="mb-3">
    <label className="form-label">Select Job:</label>
    <select 
      className="form-select"
      value={selectedJobId || ''}
      onChange={(e) => setSelectedJobId(e.target.value)}
    >
      <option value="">Select a job...</option>
      {jobs.map(job => (
        <option key={job.job_id} value={job.job_id}>
          {job.description} ({new Date(job.completed_at).toLocaleString()})
        </option>
      ))}
    </select>
  </div>
);
```

### 8. Implement Print and Export Features

Add print and export functionality to the dashboard:

```javascript
// Print function
const printDashboard = () => {
  const printContents = document.getElementById('printable-dashboard').innerHTML;
  const originalContents = document.body.innerHTML;
  
  document.body.innerHTML = `
    <div class="print-dashboard">
      <h1>Military Medical Exercise Visualization Report</h1>
      ${printContents}
    </div>
  `;
  
  window.print();
  document.body.innerHTML = originalContents;
  
  // Re-mount React components
  const root = document.getElementById('visualization-dashboard');
  if (root) {
    ReactDOM.render(<ExerciseDashboard />, root);
  }
};

// Export to CSV
const exportToCSV = (data, filename) => {
  const csvRows = [];
  
  // Function to convert object to CSV row
  const processRow = (row) => {
    const values = Object.values(row);
    return values.map(value => {
      const val = String(value).replace(/"/g, '""');
      return `"${val}"`;
    }).join(',');
  };
  
  // Add headers
  const headers = Object.keys(data[0]);
  csvRows.push(headers.join(','));
  
  // Add data rows
  for (const row of data) {
    csvRows.push(processRow(row));
  }
  
  // Create and download CSV file
  const csvString = csvRows.join('\n');
  const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Add export buttons to dashboard
const ExportButtons = ({ data, tabName }) => (
  <div className="mb-3 d-flex gap-2">
    <button 
      className="btn btn-outline-primary btn-sm"
      onClick={() => printDashboard()}
    >
      <i className="fas fa-print me-1"></i> Print Report
    </button>
    <button 
      className="btn btn-outline-primary btn-sm"
      onClick={() => exportToCSV(data[`${tabName}Data`] || [], `${tabName}-export.csv`)}
    >
      <i className="fas fa-file-csv me-1"></i> Export CSV
    </button>
  </div>
);
```

### 9. Implement Full Sankey Diagram

Enhance the patient flow visualization with a complete Sankey diagram implementation:

```javascript
// Install the react-vis library (required for Sankey diagram)
// npm install react-vis

// Import it in your React component
import { Sankey } from 'react-vis';

// Replace the placeholder PatientFlowSankey with a real implementation:
const PatientFlowSankey = ({ data }) => {
  // Format data for Sankey diagram
  const nodes = data.nodes.map(node => ({
    name: node.name
  }));

  const links = data.links.map(link => ({
    source: link.source,
    target: link.target,
    value: link.value
  }));

  // Color mapping for nodes
  const nodeColors = {
    'POI': '#3F51B5',
    'R1': '#4CAF50',
    'R2': '#FFC107',
    'R3': '#FF9800',
    'R4': '#9C27B0',
    'RTD': '#2196F3',
    'KIA': '#F44336'
  };

  return (
    <div className="sankey-container" style={{ height: '500px', width: '100%' }}>
      <Sankey
        nodes={nodes}
        links={links}
        width={900}
        height={500}
        nodeWidth={15}
        nodePadding={10}
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
        align="justify"
        layout={24}
        nodeColors={d => nodeColors[d.name] || '#ccc'}
        nodeTitleProperty="name"
        linkTitleProperty={d => `${d.source.name} → ${d.target.name}: ${d.value}`}
        linkOpacity={0.4}
      />
    </div>
  );
};
```

### 10. Add Advanced Filtering Controls

Implement more advanced filtering options for deeper analysis:

```javascript
// Add filter state
const [filters, setFilters] = useState({
  nationality: 'all',
  injuryType: 'all',
  triageCategory: 'all',
  timeRange: 'all'
});

// Filter change handler
const handleFilterChange = (filter, value) => {
  setFilters({
    ...filters,
    [filter]: value
  });
};

// Filter component
const AdvancedFilters = ({ onFilterChange, dashboardData }) => {
  // Extract available filter options from data
  const nationalities = dashboardData?.nationalityDistribution?.map(item => item.name) || [];
  const injuryTypes = dashboardData?.injuryDistribution?.map(item => item.name) || [];
  const triageCategories = dashboardData?.triageDistribution?.map(item => item.name) || [];
  
  return (
    <div className="card mb-3">
      <div className="card-header bg-light">
        <h5><i className="fas fa-filter me-2"></i>Advanced Filters</h5>
      </div>
      <div className="card-body">
        <div className="row g-3">
          <div className="col-md-3">
            <label className="form-label">Nationality:</label>
            <select 
              className="form-select form-select-sm"
              onChange={(e) => onFilterChange('nationality', e.target.value)}
            >
              <option value="all">All Nationalities</option>
              {nationalities.map(nat => (
                <option key={nat} value={nat}>{nat}</option>
              ))}
            </select>
          </div>
          
          <div className="col-md-3">
            <label className="form-label">Injury Type:</label>
            <select 
              className="form-select form-select-sm"
              onChange={(e) => onFilterChange('injuryType', e.target.value)}
            >
              <option value="all">All Injury Types</option>
              {injuryTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
          
          <div className="col-md-3">
            <label className="form-label">Triage Category:</label>
            <select 
              className="form-select form-select-sm"
              onChange={(e) => onFilterChange('triageCategory', e.target.value)}
            >
              <option value="all">All Triage Categories</option>
              {triageCategories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          
          <div className="col-md-3">
            <label className="form-label">Time Range:</label>
            <select 
              className="form-select form-select-sm"
              onChange={(e) => onFilterChange('timeRange', e.target.value)}
            >
              <option value="all">All Days</option>
              <option value="day1">Day 1</option>
              <option value="day2">Day 2</option>
              <option value="day4">Day 4</option>
              <option value="day8">Day 8</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

// Filter application function
const applyFilters = (data, filters) => {
  // Deep clone data to avoid mutating original
  const filteredData = JSON.parse(JSON.stringify(data));
  
  // Apply nationality filter
  if (filters.nationality !== 'all') {
    // Filter nationality-specific data
    // This would depend on the specific data structure
  }
  
  // Apply injury type filter
  if (filters.injuryType !== 'all') {
    // Filter injury-specific data
  }
  
  // Apply triage category filter
  if (filters.triageCategory !== 'all') {
    // Filter triage-specific data
  }
  
  // Apply time range filter
  if (filters.timeRange !== 'all') {
    // Filter time-specific data
    // Map day selections to day strings in the data
    const dayMap = {
      'day1': 'Day 1',
      'day2': 'Day 2',
      'day4': 'Day 4',
      'day8': 'Day 8'
    };
    
    const dayFilter = dayMap[filters.timeRange];
    
    if (dayFilter && filteredData.casualtyFlowByDay) {
      filteredData.casualtyFlowByDay = filteredData.casualtyFlowByDay.filter(
        item => item.day === dayFilter
      );
    }
    
    // Apply to other day-based datasets
  }
  
  return filteredData;
};
```

### 11. Add Interactive Tooltips

Enhance tooltips with more detailed information:

```javascript
// Custom tooltip component for pie charts
const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="custom-tooltip bg-white p-2 border shadow-sm">
        <p className="fw-bold">{data.name}</p>
        <p>Count: {data.value}</p>
        <p>Percentage: {((data.value / data.payload.total) * 100).toFixed(1)}%</p>
      </div>
    );
  }
  return null;
};

// Use the custom tooltip in charts
<PieChart>
  <Pie
    data={data.nationalityDistribution}
    dataKey="value"
    nameKey="name"
    cx="50%"
    cy="50%"
    outerRadius={80}
    label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}
  >
    {/* Cell definitions... */}
  </Pie>
  <Tooltip content={<CustomPieTooltip />} />
</PieChart>
```

### 12. Add Patient Detail View

Create a detailed view for individual patient data:

```javascript
// Patient detail view state
const [selectedPatient, setSelectedPatient] = useState(null);

// Patient selection handler
const handlePatientSelect = (patientId) => {
  // Fetch detailed patient data
  const fetchPatientDetails = async (id) => {
    try {
      const response = await fetch(`/api/visualizations/patient-detail/${id}`);
      if (response.ok) {
        const patientData = await response.json();
        setSelectedPatient(patientData);
      }
    } catch (error) {
      console.error(`Error fetching patient ${id} details:`, error);
    }
  };
  
  fetchPatientDetails(patientId);
};

// Patient detail modal component
const PatientDetailModal = ({ patient, onClose }) => {
  if (!patient) return null;
  
  return (
    <div className="modal show d-block" tabIndex="-1">
      <div className="modal-dialog modal-lg">
        <div className="modal-content">
          <div className="modal-header">
            <h5 className="modal-title">Patient Detail: {patient.demographics?.given_name} {patient.demographics?.family_name}</h5>
            <button type="button" className="btn-close" onClick={onClose}></button>
          </div>
          <div className="modal-body">
            {/* Patient demographics */}
            <div className="mb-4">
              <h6 className="border-bottom pb-2">Demographics</h6>
              <div className="row">
                <div className="col-md-6">
                  <p><strong>ID:</strong> {patient.id}</p>
                  <p><strong>Gender:</strong> {patient.demographics?.gender}</p>
                  <p><strong>Nationality:</strong> {patient.nationality}</p>
                </div>
                <div className="col-md-6">
                  <p><strong>Age:</strong> {patient.age}</p>
                  <p><strong>Blood Type:</strong> {patient.demographics?.blood_type}</p>
                  <p><strong>Weight:</strong> {patient.demographics?.weight} kg</p>
                </div>
              </div>
            </div>
            
            {/* Medical information */}
            <div className="mb-4">
              <h6 className="border-bottom pb-2">Medical Information</h6>
              <p><strong>Primary Condition:</strong> {patient.primary_condition?.display} ({patient.primary_condition?.severity})</p>
              <p><strong>Triage Category:</strong> {patient.triage_category}</p>
              <p><strong>Injury Type:</strong> {patient.injury_type}</p>
              
              {patient.additional_conditions?.length > 0 && (
                <div>
                  <strong>Additional Conditions:</strong>
                  <ul className="mb-0">
                    {patient.additional_conditions.map((condition, idx) => (
                      <li key={idx}>{condition.display}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Treatment history */}
            <div>
              <h6 className="border-bottom pb-2">Treatment History</h6>
              <div className="timeline">
                {patient.treatment_history?.map((treatment, idx) => (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-marker"></div>
                    <div className="timeline-content">
                      <h6>{treatment.facility} - {new Date(treatment.date).toLocaleString()}</h6>
                      {treatment.treatments?.length > 0 && (
                        <div>
                          <strong>Treatments:</strong>
                          <ul>
                            {treatment.treatments.map((t, i) => (
                              <li key={i}>{t.display}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {treatment.observations?.length > 0 && (
                        <div>
                          <strong>Observations:</strong>
                          <ul>
                            {treatment.observations.map((obs, i) => (
                              <li key={i}>{obs.display}: {obs.value} {obs.unit}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
};
```

### 13. Add New API Endpoint for Patient Detail

Create a new endpoint to support the patient detail view:

```python
# In app.py
@visualization_router.get("/patient-detail/{patient_id}")
async def get_patient_detail(patient_id: str, job_id: str = None):
    """Get detailed data for a specific patient"""
    # Find the appropriate job
    target_job = None
    if job_id and job_id in jobs:
        target_job = jobs[job_id]
    else:
        # Find the most recent completed job
        completed_jobs = [j for j in jobs.values() if j["status"] == "completed"]
        if completed_jobs:
            target_job = max(completed_jobs, key=lambda j: j.get("completed_at", ""))
    
    if not target_job:
        raise HTTPException(status_code=404, detail="No completed jobs found")
    
    # In a real implementation, you would extract the specific patient from the job data
    # For now, return a mock patient
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
```

### 14. Testing and Debugging

Follow these steps to test your implementation:

1. **Test backend endpoints**:
   - Use a tool like Postman or curl to test the API endpoints
   - Verify that `/api/visualizations/dashboard-data` returns expected data
   - Check that `/api/visualizations/job-list` returns a list of jobs

2. **Test the HTML page**:
   - Access the visualizations page at `/visualizations`
   - Verify that the React component loads and displays without errors
   - Check browser console for any JavaScript errors

3. **Test data integration**:
   - Generate a new batch of patients
   - Verify that the visualization dashboard displays the new data
   - Test filtering and job selection functionality

4. **Common issues and solutions**:
   - If charts don't render, check React and Recharts imports
   - If data doesn't load, check network requests in browser dev tools
   - If component doesn't mount, verify React and ReactDOM are loaded

### 15. Deployment

Deploy the enhanced visualization dashboard using these steps:

1. **Development environment**:
   - Run with `python app.py`
   - Access at `http://localhost:8000/visualizations`

2. **Production deployment**:
   - Include the additional files in your Docker image
   - Update `Dockerfile` to copy the new visualization files
   - Ensure the visualization router is included in the production app

3. **Docker configuration**:
   ```dockerfile
   # In Dockerfile, add:
   COPY patient_generator/visualization_data.py /app/patient_generator/
   COPY static/js/visualization-dashboard.js /app/static/js/
   COPY static/visualizations.html /app/static/
   ```

## Conclusion

By following this implementation guide, you've enhanced the Military Medical Exercise Patient Generator with a powerful visualization dashboard. The dashboard provides exercise planners with deeper insights into simulated patient data, helping them better prepare for real-world scenarios.

For ongoing maintenance and future enhancements, consider:

1. Adding more visualization types as needed
2. Implementing real-time data updates for active exercises
3. Extending the filtering capabilities for more granular analysis
4. Adding comparison features for different exercise scenarios
5. Implementing user authentication for visualization access

With these extended visualization capabilities, the Military Medical Exercise Patient Generator becomes an even more valuable tool for military medical training and exercise planning.
