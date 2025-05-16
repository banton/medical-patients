// MilitaryMedicalDashboard.tsx
import React, { useState, useEffect, useCallback } from 'react';
import ReactDOM from 'react-dom/client'; // Import ReactDOM
import { 
  Sankey, Tooltip, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';

interface DashboardData {
  summary: {
    total_patients: number;
    total_kia: number;
    total_rtd: number;
    kia_percent: number;
    rtd_percent: number;
  };
  patient_flow: {
    nodes: Array<{ id: string; name: string }>;
    links: Array<{ 
      source: number; 
      target: number; 
      value: number;
      source_id: string;
      target_id: string;
    }>;
  };
  facility_stats: {
    [key: string]: {
      total: number;
      to_kia: number;
      to_rtd: number;
      to_next: number;
      kia_percent: number;
      rtd_percent: number;
      next_percent: number;
    };
  };
}

const MilitaryMedicalDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [jobs, setJobs] = useState<Array<{job_id: string; total_patients: number; created_at: string}>>([]);

  // Fetch job list on component mount
  useEffect(() => {
    const fetchJobList = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/visualizations/job-list');
        if (!response.ok) {
          throw new Error(`Failed to fetch job list: ${response.statusText}`);
        }
        const data = await response.json();
        setJobs(data);
        
        // Set the most recent job as default
        if (data.length > 0) {
          setSelectedJobId(data[0].job_id);
        } else {
          setLoading(false);
        }
      } catch (err) {
        console.error("Error fetching job list:", err);
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    
    fetchJobList();
  }, []);

  // Fetch dashboard data when job is selected
  const fetchDashboardData = useCallback(async () => {
    if (!selectedJobId) {
      setDashboardData(null);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const url = `/api/visualizations/dashboard-data?job_id=${selectedJobId}`;
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch dashboard data: ${response.statusText} - ${errorText}`);
      }
      
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError(err instanceof Error ? err.message : String(err));
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (selectedJobId) {
      fetchDashboardData();
    }
  }, [fetchDashboardData, selectedJobId]);

  // Job selector component
  const JobSelector = () => (
    <div className="mb-3">
      <label htmlFor="jobSelector" className="form-label">Select Exercise Job:</label>
      <select 
        id="jobSelector"
        className="form-select"
        value={selectedJobId || ''}
        onChange={(e) => setSelectedJobId(e.target.value)}
        disabled={jobs.length === 0}
      >
        <option value="">{jobs.length > 0 ? "Select a job..." : "No jobs available"}</option>
        {jobs.map(job => (
          <option key={job.job_id} value={job.job_id}>
            {job.job_id} ({job.total_patients} patients, {new Date(job.created_at).toLocaleDateString()})
          </option>
        ))}
      </select>
    </div>
  );

  // Summary Cards component
  const SummaryCards = ({ data }: { data: DashboardData }) => (
    <div className="row mb-4">
      <div className="col-md-4">
        <div className="card bg-light">
          <div className="card-body text-center">
            <h5 className="card-title">Total Patients</h5>
            <p className="card-text display-4">{data.summary.total_patients}</p>
          </div>
        </div>
      </div>
      <div className="col-md-4">
        <div className="card bg-danger text-white">
          <div className="card-body text-center">
            <h5 className="card-title">Killed in Action (KIA)</h5>
            <p className="card-text display-4">{data.summary.total_kia}</p>
            <p className="card-text">{data.summary.kia_percent}% of total</p>
          </div>
        </div>
      </div>
      <div className="col-md-4">
        <div className="card bg-success text-white">
          <div className="card-body text-center">
            <h5 className="card-title">Return to Duty (RTD)</h5>
            <p className="card-text display-4">{data.summary.total_rtd}</p>
            <p className="card-text">{data.summary.rtd_percent}% of total</p>
          </div>
        </div>
      </div>
    </div>
  );

  // Facility Statistics component
  const FacilityStatistics = ({ data }: { data: DashboardData }) => {
    // Create data for facility outcomes chart
    const facilityData = Object.entries(data.facility_stats).map(([facility, stats]) => ({
      name: facility === "POI" ? "Point of Injury" : `Role ${facility.substring(1)}`,
      code: facility,
      total: stats.total,
      KIA: stats.to_kia,
      RTD: stats.to_rtd,
      "Further Treatment": stats.to_next
    }));

    return (
      <div className="row mb-4">
        <div className="col-12">
          <h4>Facility Outcomes</h4>
          <div className="chart-container" style={{ height: 400 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={facilityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="KIA" fill="#dc3545" name="Killed in Action" />
                <Bar dataKey="RTD" fill="#28a745" name="Return to Duty" />
                <Bar dataKey="Further Treatment" fill="#007bff" name="To Next Level" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  // Custom Sankey Tooltip component
  const CustomSankeyTooltip = ({ active, payload }: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
    if (active && payload && payload.length) {
      const linkPayload = payload[0].payload; // This is the link object from Sankey
      // The actual data for source/target names is in the nodes array,
      // and linkPayload.source and linkPayload.target are node objects.
      // We need to access the original source_id and target_id we added to our links.
      const sourceNodeName = linkPayload.source?.id || linkPayload.source_id || 'Unknown Source';
      const targetNodeName = linkPayload.target?.id || linkPayload.target_id || 'Unknown Target';
      const value = linkPayload.value;

      const total = dashboardData?.summary.total_patients || 0;
      const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
      
      return (
        <div className="custom-tooltip" style={{ 
          backgroundColor: 'rgba(255, 255, 255, 0.9)', 
          padding: '10px',
          border: '1px solid #ddd',
          borderRadius: '4px'
        }}>
          <p><strong>From:</strong> {sourceNodeName} - <strong>To:</strong> {targetNodeName}</p>
          <p><strong>Patients:</strong> {value}</p>
          <p><strong>Percentage:</strong> {percentage}% of total</p>
        </div>
      );
    }
    return null;
  };

  // Patient Flow Sankey component
  const PatientFlowSankey = ({ data }: { data: DashboardData['patient_flow'] }) => {
    // Define custom colors for nodes
    const nodeColors: { [key: string]: string } = {
      "POI": "#6c757d", // Gray
      "R1": "#007bff", // Blue
      "R2": "#17a2b8", // Teal
      "R3": "#6f42c1", // Purple
      "R4": "#fd7e14", // Orange
      "RTD": "#28a745", // Green
      "KIA": "#dc3545"  // Red
    };

    // Recharts Sankey expects nodes and links directly.
    // The 'data' prop for Sankey should be an object like { nodes: [], links: [] }
    const sankeyChartData = {
        nodes: data.nodes.map(node => ({ ...node, name: node.name || node.id })), // Ensure 'name' property for display
        links: data.links
    };

    return (
      <div className="row mb-4">
        <div className="col-12">
          <h4>Patient Flow Through Medical Facilities</h4>
          <div className="card">
            <div className="card-body">
              <div style={{ height: 400 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <Sankey
                    data={sankeyChartData} // Use the structured data
                    nodePadding={50}
                    nodeWidth={20}
                    link={{ 
                      stroke: '#aaa', 
                      strokeWidth: 2, 
                      strokeOpacity: 0.2,
                    }}
                    node={(props: any) => { // eslint-disable-line @typescript-eslint/no-explicit-any
                        const { x, y, width, height, index } = props;
                        const nodeId = sankeyChartData.nodes[index].id;
                        const nodeName = sankeyChartData.nodes[index].name;
                        return (
                          <g>
                            <rect x={x} y={y} width={width} height={height} fill={nodeColors[nodeId] || '#8884d8'} stroke="#000" strokeWidth={1} />
                            <text x={x - 6} y={y + height / 2} textAnchor="end" fill="#333" fontSize="12">
                              {nodeName}
                            </text>
                          </g>
                        );
                    }}
                    margin={{ top: 20, right: 120, bottom: 20, left: 120 }} // Increased margins for labels
                  >
                    <Tooltip content={<CustomSankeyTooltip />} />
                  </Sankey>
                </ResponsiveContainer>
              </div>
              <div className="text-center mt-3">
                <small className="text-muted">
                  Diagram shows patient flow from Point of Injury through medical facilities. 
                  Width of lines represents number of patients.
                </small>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Loading state
  if (loading && !dashboardData) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p>Loading military medical exercise data...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger">
          <h4>Error loading data</h4>
          <p>{error}</p>
        </div>
        <JobSelector /> {/* Show selector even on error to allow trying another job */}
      </div>
    );
  }

  // No data state (or no job selected)
  if (!dashboardData && !loading) { // Check !loading to avoid showing this during initial load
    return (
      <div className="container mt-5">
        <div className="d-flex justify-content-between align-items-center mb-4">
         <h2>Military Medical Exercise Analysis</h2>
         <JobSelector />
        </div>
        <div className="alert alert-info">
          <h4>{jobs.length > 0 && !selectedJobId ? "Please select an exercise job." : "No exercise data available."}</h4>
          <p>{jobs.length === 0 ? "Generate new patient data to see visualizations." : "Select a job from the dropdown above."}</p>
        </div>
      </div>
    );
  }
  
  // Ensure dashboardData is not null before rendering components that depend on it
  if (!dashboardData) {
      return ( // Fallback for safety, though above conditions should catch it
          <div className="container mt-5 text-center">
              <p>Preparing dashboard...</p>
              <JobSelector />
          </div>
      );
  }


  // Main dashboard
  return (
    <div className="container-fluid py-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Military Medical Exercise Analysis</h2>
        <JobSelector />
      </div>

      <SummaryCards data={dashboardData} />
      <PatientFlowSankey data={dashboardData.patient_flow} />
      <FacilityStatistics data={dashboardData} />
    </div>
  );
};

// Mount the React component
const container = document.getElementById('military-medical-dashboard');
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <MilitaryMedicalDashboard />
    </React.StrictMode>
  );
} else {
  console.error("Failed to find the root container for MilitaryMedicalDashboard. Ensure an element with ID 'military-medical-dashboard' exists in your HTML.");
}

export default MilitaryMedicalDashboard;
