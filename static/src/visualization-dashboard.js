// Import React and Recharts components
const { useState, useEffect, StrictMode } = React; // Added StrictMode for good practice
// Recharts components will be destructured inside the main component
// to ensure window.Recharts is available.
// Assuming LucideReact is available globally or via another import mechanism if not using a bundler
// If LucideReact is meant to be imported from a module, this would need adjustment based on project setup.
// For a static HTML setup, ensure LucideReact is loaded via a script tag.
// const { AlertCircle, FilePieChart, Calendar, Activity, Map, Users, ArrowRight, ChevronDown, ChevronUp } = LucideReact;

// Placeholder for Lucide icons if LucideReact is not globally available
const IconPlaceholder = ({ name, size = 24, color = "currentColor" }) => (
  <i className={`fas fa-${name}`} style={{ fontSize: size, color: color, marginRight: '0.25em' }}></i>
);

const AlertCircle = (props) => <IconPlaceholder name="exclamation-circle" {...props} />;
const FilePieChart = (props) => <IconPlaceholder name="chart-pie" {...props} />;
const Calendar = (props) => <IconPlaceholder name="calendar-alt" {...props} />;
const Activity = (props) => <IconPlaceholder name="heartbeat" {...props} />; // Or 'activity' if a suitable FontAwesome icon exists
const MapIcon = (props) => <IconPlaceholder name="map-marked-alt" {...props} />; // Renamed to avoid conflict with Map global
const Users = (props) => <IconPlaceholder name="users" {...props} />;
const ArrowRight = (props) => <IconPlaceholder name="arrow-right" {...props} />;
const ChevronDown = (props) => <IconPlaceholder name="chevron-down" {...props} />;
const ChevronUp = (props) => <IconPlaceholder name="chevron-up" {...props} />;


// Mock data generation function (as a fallback)
// Transform snake_case API response to camelCase for frontend
const transformApiResponse = (data) => {
  if (!data) return data;
  
  // Map API field names to frontend field names
  const fieldMapping = {
    nationality_distribution: 'nationalityDistribution',
    injury_distribution: 'injuryDistribution',
    triage_distribution: 'triageDistribution',
    patient_flow: 'patient_flow',  // Keep as is
    facility_stats: 'facility_usage',
    front_distribution: 'front_comparison',
    timeline_data: 'timeline_analysis',
    flow_data: 'patient_flow',
    casualty_flow_by_day: 'casualtyFlowByDay'
  };
  
  const transformed = {};
  
  // Copy and transform fields
  Object.keys(data).forEach(key => {
    const mappedKey = fieldMapping[key] || key;
    transformed[mappedKey] = data[key];
  });
  
  // Transform specific fields to match expected format
  if (data.nationality_distribution) {
    transformed.nationalityDistribution = data.nationality_distribution.map(item => ({
      name: item.nationality || item.name,
      value: item.count || item.value || item.percentage
    }));
  }
  
  if (data.injury_distribution) {
    transformed.injuryDistribution = data.injury_distribution.map(item => ({
      name: item.injury_type || item.name,
      value: item.count || item.value || item.percentage
    }));
  }
  
  if (data.facility_stats) {
    transformed.facility_usage = Object.entries(data.facility_stats).map(([name, stats]) => ({
      name,
      capacity: 100,  // Default capacity, adjust based on actual data
      used: Math.round((stats.treated || 0) / 100 * 100)  // Percentage
    }));
  }
  
  return transformed;
};

const generateMockData = () => {
  console.warn("Using mock data for dashboard.");
  return {
    summary: { total_patients: 100, kia_rate: 0.05, rtd_rate: 0.6, average_treatment_time: 72 },
    patient_flow: {
      nodes: [
        { name: 'POI' }, { name: 'R1' }, { name: 'R2' }, { name: 'R3' }, { name: 'R4' }, { name: 'RTD' }, { name: 'KIA' }
      ],
      links: [
        { source: 0, target: 1, value: 80 }, { source: 1, target: 2, value: 60 },
        { source: 2, target: 3, value: 40 }, { source: 3, target: 4, value: 20 },
        { source: 1, target: 5, value: 15 }, { source: 2, target: 5, value: 15 },
        { source: 3, target: 5, value: 10 }, { source: 4, target: 5, value: 5 },
        { source: 0, target: 6, value: 5 }, { source: 1, target: 6, value: 2 },
      ]
    },
    facility_usage: [
      { name: 'R1', capacity: 100, used: 70 }, { name: 'R2', capacity: 80, used: 50 },
      { name: 'R3', capacity: 60, used: 30 }, { name: 'R4', capacity: 40, used: 15 },
    ],
    timeline_analysis: [
      { day: 'Day 1', casualties: 30 }, { day: 'Day 2', casualties: 45 },
      { day: 'Day 3', casualties: 20 }, { day: 'Day 4', casualties: 15 },
    ],
    front_comparison: [
      { front: 'Polish', casualties: 50, rtd: 30, kia: 5 },
      { front: 'Estonian', casualties: 30, rtd: 18, kia: 3 },
      { front: 'Finnish', casualties: 20, rtd: 12, kia: 2 },
    ],
    treatment_effectiveness: [
      { treatment: 'Tourniquet', effectiveness: 0.9 }, { treatment: 'Chest Seal', effectiveness: 0.8 },
      { treatment: 'IV Fluids', effectiveness: 0.7 },
    ],
    nationalityDistribution: [
        { name: 'POL', value: 40 }, { name: 'EST', value: 30 }, { name: 'USA', value: 20 }, { name: 'GBR', value: 10 }
    ],
    injuryDistribution: [
        { name: 'Battle Trauma', value: 60 }, { name: 'Disease', value: 25 }, { name: 'Non-Battle', value: 15 }
    ],
    triageDistribution: [
        { name: 'T1', value: 10 }, { name: 'T2', value: 40 }, { name: 'T3', value: 30 }, { name: 'T4', value: 20 }
    ],
    casualtyFlowByDay: [
        { day: 'Day 1', POI: 30, R1: 25, R2: 10, R3: 5, R4: 2, RTD: 5, KIA: 1 },
        { day: 'Day 2', POI: 45, R1: 40, R2: 20, R3: 10, R4: 5, RTD: 10, KIA: 2 },
    ]
  };
};


const ExerciseDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary');

  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);

  const [filters, setFilters] = useState({
    nationality: 'all',
    injuryType: 'all',
    triageCategory: 'all',
    timeRange: 'all'
  });
  const [selectedPatient, setSelectedPatient] = useState(null);

  // Function to fetch dashboard data
  const fetchDashboardData = async (jobIdToFetch) => {
    try {
      setLoading(true);
      setError(null);
      const url = jobIdToFetch ? `/api/visualizations/dashboard-data?job_id=${jobIdToFetch}` : '/api/visualizations/dashboard-data';
      const response = await fetch(url, {
        headers: window.API_CONFIG ? window.API_CONFIG.getHeaders() : {
          'X-API-Key': 'your_secret_api_key_here'
        }
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to fetch dashboard data');
      }
      const data = await response.json();
      // Transform API response to match frontend expectations
      const transformedData = transformApiResponse(data);
      setDashboardData(transformedData);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError(err.message);
      setDashboardData(generateMockData()); // Fallback to mock data
    } finally {
      setLoading(false);
    }
  };

  // Function to fetch jobs list
  const fetchJobs = async () => {
    try {
      // Use correct API endpoint: /api/jobs/ instead of /api/visualizations/job-list
      const response = await fetch('/api/jobs/', {
        headers: window.API_CONFIG ? window.API_CONFIG.getHeaders() : {
          'X-API-Key': 'your_secret_api_key_here'
        }
      });
      if (response.ok) {
        const jobsList = await response.json();
        setJobs(jobsList);
        // Set the most recent job as default if not already selected
        if (jobsList.length > 0 && !selectedJobId) {
          setSelectedJobId(jobsList[0].job_id);
        } else if (jobsList.length === 0) {
          // If no jobs, fetch general dashboard data (which might be mock or error)
          fetchDashboardData(null);
        }
      } else {
        console.error("Failed to fetch job list");
        setJobs([]); // Clear jobs if fetch fails
        fetchDashboardData(null); // Attempt to load general data or mock
      }
    } catch (err) {
      console.error("Error fetching jobs:", err);
      setJobs([]);
      fetchDashboardData(null);
    }
  };

  // Effect to fetch jobs on component mount and check for job_id in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const jobIdFromUrl = urlParams.get('job_id');
    
    if (jobIdFromUrl) {
      setSelectedJobId(jobIdFromUrl); // This will trigger the data fetch for this specific job
      // Optionally, still fetch the full job list for the dropdown
      fetchJobs(); 
    } else {
      // If no job_id in URL, fetch jobs and then data for the latest or general
      fetchJobs();
    }
    
    // Listen for job completion events from the main app
    const handleJobCompletion = () => {
      console.log('Job completion detected, refreshing job list...');
      fetchJobs();
    };
    
    window.addEventListener('job-completed', handleJobCompletion);
    
    // Cleanup listener on unmount
    return () => {
      window.removeEventListener('job-completed', handleJobCompletion);
    };
  }, []); // Runs once on mount

  // Effect to fetch data when selected job changes
  useEffect(() => {
    if (selectedJobId) {
      fetchDashboardData(selectedJobId);
    } else if (jobs.length === 0 && !loading && !new URLSearchParams(window.location.search).get('job_id')) { 
        // If no job is selected, no jobs in list, not loading, and no job_id in URL
        fetchDashboardData(null); // Fetch general/mock data
    }
  }, [selectedJobId, jobs, loading]); // Added loading to dependencies to avoid potential race conditions


  const handleFilterChange = (filter, value) => {
    setFilters(prevFilters => ({
      ...prevFilters,
      [filter]: value
    }));
  };
  
  // Filter application function (placeholder - needs full implementation based on data structure)
  const applyFilters = (data, currentFilters) => {
    if (!data) return null;
    // Deep clone data to avoid mutating original
    let filteredData = JSON.parse(JSON.stringify(data));
    
    // Example: Apply time range filter to casualtyFlowByDay
    if (currentFilters.timeRange !== 'all' && filteredData.casualtyFlowByDay) {
      const dayMap = { 'day1': 'Day 1', 'day2': 'Day 2', 'day4': 'Day 4', 'day8': 'Day 8' };
      const dayFilter = dayMap[currentFilters.timeRange];
      if (dayFilter) {
        filteredData.casualtyFlowByDay = filteredData.casualtyFlowByDay.filter(
          item => item.day === dayFilter
        );
      }
    }
    // Add more filter logic here for nationality, injuryType, triageCategory
    // This will heavily depend on how these filters should affect each part of the dashboardData
    
    return filteredData;
  };

  const displayedData = dashboardData ? applyFilters(dashboardData, filters) : null;

  // Patient selection handler
  const handlePatientSelect = (patientId) => {
    const fetchPatientDetails = async (id) => {
      try {
        setLoading(true); // Reuse loading state or add a specific one for patient details
        // Ensure job_id is passed if available and relevant for the endpoint
        const patientDetailUrl = selectedJobId 
            ? `/api/visualizations/patient-detail/${id}?job_id=${selectedJobId}`
            : `/api/visualizations/patient-detail/${id}`;
        const response = await fetch(patientDetailUrl, {
          headers: window.API_CONFIG ? window.API_CONFIG.getHeaders() : {
            'X-API-Key': 'your_secret_api_key_here'
          }
        });
        if (response.ok) {
          const patientData = await response.json();
          setSelectedPatient(patientData);
        } else {
          const errorData = await response.json();
          console.error(`Error fetching patient ${id} details:`, errorData.detail);
          setSelectedPatient({ id: id, error: errorData.detail || "Failed to load patient details." });
        }
      } catch (err) {
        console.error(`Error fetching patient ${id} details:`, err);
        setSelectedPatient({ id: id, error: "An unexpected error occurred." });
      } finally {
        setLoading(false);
      }
    };
    fetchPatientDetails(patientId);
  };


  // Print function
  const printDashboard = () => {
    const printableElement = document.getElementById('printable-dashboard');
    if (!printableElement) {
        console.error("Printable dashboard element not found");
        return;
    }
    const printContents = printableElement.innerHTML;
    const originalContents = document.body.innerHTML;
    
    // Create a new window or iframe for printing to isolate styles
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Military Medical Exercise Visualization Report</title>
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css">
          <style>
            body { margin: 20px; font-family: sans-serif; }
            .print-dashboard { width: 100%; }
            /* Add any print-specific styles here */
            .card { border: 1px solid #ccc; margin-bottom: 1rem; }
            .card-header { background-color: #f8f9fa; padding: 0.5rem 1rem; }
            h1, h2, h3, h4, h5, h6 { margin-top: 0; }
            /* Ensure charts are not cut off - this might need more specific selectors */
            .recharts-responsive-container, .sankey-container { width: 100% !important; height: auto !important; page-break-inside: avoid; }
            svg { max-width: 100%; }
          </style>
        </head>
        <body>
          <div class="print-dashboard">
            <h1>Military Medical Exercise Visualization Report</h1>
            ${printContents}
          </div>
          <script>
            // Ensure images and charts are loaded before printing
            window.onload = function() {
              window.print();
              window.close();
            }
          </script>
        </body>
      </html>
    `);
    printWindow.document.close();
  };

  // Export to CSV
  const exportToCSV = (dataToExport, filename) => {
    if (!dataToExport || dataToExport.length === 0) {
      alert("No data available to export.");
      return;
    }
    const csvRows = [];
    const processRow = (row) => {
      const values = Object.values(row);
      return values.map(value => {
        const val = String(value).replace(/"/g, '""'); // Escape double quotes
        return `"${val}"`; // Enclose in double quotes
      }).join(',');
    };
    const headers = Object.keys(dataToExport[0]);
    csvRows.push(headers.join(','));
    for (const row of dataToExport) {
      csvRows.push(processRow(row));
    }
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
    URL.revokeObjectURL(url);
  };

  // Destructure Recharts components here, assuming window.Recharts is now populated.
  const {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, PieChart, Pie, Cell, Sankey: RechartsSankey, Scatter, ScatterChart, ZAxis,
    RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
  } = window.Recharts || {}; // Fallback to empty object if Recharts is somehow still not there

  if (loading && !dashboardData) return <div className="container mt-5 text-center"><div className="spinner-border text-primary" role="status"><span className="visually-hidden">Loading...</span></div><p>Loading dashboard...</p></div>;
  if (error && !dashboardData) return <div className="container mt-5"><div className="alert alert-danger" role="alert"><AlertCircle /> {error}</div></div>;
  
  // Check if Recharts components are available before trying to render charts
  if (!LineChart && selectedJobId) { // Check one component as a proxy for all
    return <div className="container mt-5"><div className="alert alert-danger" role="alert"><AlertCircle /> Recharts library not loaded correctly. Dashboard cannot be displayed.</div></div>;
  }

  if (!displayedData) return <div className="container mt-5"><div className="alert alert-info" role="alert">No data available to display. Please select a job or generate new data.</div></div>;


  // Components for different tabs
  const SummaryView = ({ data }) => (
    <div className="card">
      <div className="card-header">Overall Summary</div>
      <div className="card-body">
        <p>Total Patients: {data.summary?.total_patients || 'N/A'}</p>
        <p>KIA Rate: {data.summary?.kia_rate !== undefined ? (data.summary.kia_rate * 100).toFixed(1) + '%' : 'N/A'}</p>
        <p>RTD Rate: {data.summary?.rtd_rate !== undefined ? (data.summary.rtd_rate * 100).toFixed(1) + '%' : 'N/A'}</p>
        {/* Add more summary points */}
      </div>
    </div>
  );

  const PatientFlowSankey = ({ data }) => {
    if (!data || !data.nodes || !data.links || data.nodes.length === 0) {
      return <div className="alert alert-warning">Patient flow data is not available or incomplete for Sankey diagram.</div>;
    }
    const nodes = data.nodes.map(node => ({ name: typeof node === 'string' ? node : node.name }));
    const links = data.links.map(link => ({
      source: typeof link.source === 'number' ? link.source : nodes.findIndex(n => n.name === link.source.name),
      target: typeof link.target === 'number' ? link.target : nodes.findIndex(n => n.name === link.target.name),
      value: link.value
    })).filter(link => typeof link.source === 'number' && typeof link.target === 'number' && link.source < nodes.length && link.target < nodes.length);


    const nodeColors = {
      'POI': '#3F51B5', 'R1': '#4CAF50', 'R2': '#FFC107', 'R3': '#FF9800',
      'R4': '#9C27B0', 'RTD': '#2196F3', 'KIA': '#F44336'
    };

    return (
      <div className="sankey-container" style={{ height: '500px', width: '100%' }}>
        <ResponsiveContainer>
          <RechartsSankey
            nodes={nodes}
            links={links}
            width={900} // ResponsiveContainer will manage this
            height={500} // ResponsiveContainer will manage this
            nodeWidth={15}
            nodePadding={10}
            margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            align="justify"
            // layout={24} // layout is iterations, might not be needed with react-vis Sankey
            nodeStyle={(d, i) => ({ fill: nodeColors[d.name] || '#ccc' })}
            // name (for title) is often derived from the node object itself
            link={{ style: { opacity: 0.4 } }}
          >
            <Tooltip />
          </RechartsSankey>
        </ResponsiveContainer>
      </div>
    );
  };
  
  const FacilityUsageView = ({ data }) => (
    <div className="card">
      <div className="card-header">Facility Usage</div>
      <div className="card-body">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.facility_usage}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="used" fill="#8884d8" name="Patients" />
            <Bar dataKey="capacity" fill="#82ca9d" name="Capacity" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const TimelineAnalysisView = ({ data }) => (
     <div className="card">
        <div className="card-header">Casualty Timeline</div>
        <div className="card-body">
            <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.timeline_analysis}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="day" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="casualties" stroke="#8884d8" activeDot={{ r: 8 }} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    </div>
  );

  const CustomPieTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload; // The data object is in payload
      const total = payload[0].payload.total || payload.reduce((sum, entry) => sum + entry.value, 0); // Calculate total if not provided
      return (
        <div className="custom-tooltip bg-white p-2 border shadow-sm rounded">
          <p className="fw-bold mb-1">{data.name}</p>
          <p className="mb-0">Count: {data.value}</p>
          {total > 0 && <p className="mb-0">Percentage: {((data.value / total) * 100).toFixed(1)}%</p>}
        </div>
      );
    }
    return null;
  };
  
  const NationalityDistributionView = ({ data }) => {
    if (!data || !data.nationalityDistribution || data.nationalityDistribution.length === 0) {
        return <div className="alert alert-info">No nationality distribution data available.</div>;
    }
    const totalNationalities = data.nationalityDistribution.reduce((sum, item) => sum + item.value, 0);
    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF19AF'];

    return (
        <div className="card">
            <div className="card-header">Nationality Distribution</div>
            <div className="card-body">
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={data.nationalityDistribution.map(d => ({...d, total: totalNationalities}))}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {data.nationalityDistribution.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomPieTooltip />} />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
  };


  // Job selector component
  const JobSelector = () => (
    <div className="mb-3">
      <label htmlFor="jobSelector" className="form-label">Select Job:</label>
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
            {job.config?.name || `Job ${job.job_id} - ${job.status || 'Unknown'}`}
          </option>
        ))}
      </select>
    </div>
  );

  // Export buttons component
  const ExportButtons = ({ data, tabName }) => {
    // Determine what data to export based on the active tab
    let exportData;
    switch(tabName) {
        case 'summary': // Example: summary might not be tabular, or you might format it
            exportData = data.summary ? [data.summary] : []; // Needs to be an array of objects
            break;
        case 'patientFlow': // Sankey data is complex, decide what's exportable
            exportData = data.patient_flow?.links || []; // Export links for example
            break;
        case 'facilityUsage':
            exportData = data.facility_usage || [];
            break;
        case 'timelineAnalysis':
            exportData = data.timeline_analysis || [];
            break;
        // Add cases for other tabs
        default:
            exportData = [];
    }

    return (
      <div className="my-3 d-flex gap-2">
        <button 
          className="btn btn-outline-primary btn-sm"
          onClick={() => printDashboard()}
        >
          <i className="fas fa-print me-1"></i> Print Report
        </button>
        <button 
          className="btn btn-outline-success btn-sm"
          onClick={() => exportToCSV(exportData, `${tabName}-export.csv`)}
          disabled={!exportData || exportData.length === 0}
        >
          <i className="fas fa-file-csv me-1"></i> Export CSV for {tabName}
        </button>
      </div>
    );
  };

  // Advanced Filters Component
  const AdvancedFilters = ({ onFilterChange, dashboardData, currentFilters }) => {
    const nationalities = [...new Set(dashboardData?.nationalityDistribution?.map(item => item.name) || [])];
    const injuryTypes = [...new Set(dashboardData?.injuryDistribution?.map(item => item.name) || [])];
    const triageCategories = [...new Set(dashboardData?.triageDistribution?.map(item => item.name) || [])];
    
    return (
      <div className="card mb-3">
        <div className="card-header bg-light">
          <h5><i className="fas fa-filter me-2"></i>Advanced Filters</h5>
        </div>
        <div className="card-body">
          <div className="row g-3">
            <div className="col-md-3">
              <label htmlFor="nationalityFilter" className="form-label">Nationality:</label>
              <select 
                id="nationalityFilter"
                className="form-select form-select-sm"
                value={currentFilters.nationality}
                onChange={(e) => onFilterChange('nationality', e.target.value)}
              >
                <option value="all">All Nationalities</option>
                {nationalities.map(nat => (<option key={nat} value={nat}>{nat}</option>))}
              </select>
            </div>
            <div className="col-md-3">
              <label htmlFor="injuryFilter" className="form-label">Injury Type:</label>
              <select 
                id="injuryFilter"
                className="form-select form-select-sm"
                value={currentFilters.injuryType}
                onChange={(e) => onFilterChange('injuryType', e.target.value)}
              >
                <option value="all">All Injury Types</option>
                {injuryTypes.map(type => (<option key={type} value={type}>{type}</option>))}
              </select>
            </div>
            <div className="col-md-3">
              <label htmlFor="triageFilter" className="form-label">Triage Category:</label>
              <select 
                id="triageFilter"
                className="form-select form-select-sm"
                value={currentFilters.triageCategory}
                onChange={(e) => onFilterChange('triageCategory', e.target.value)}
              >
                <option value="all">All Triage Categories</option>
                {triageCategories.map(cat => (<option key={cat} value={cat}>{cat}</option>))}
              </select>
            </div>
            <div className="col-md-3">
              <label htmlFor="timeFilter" className="form-label">Time Range:</label>
              <select 
                id="timeFilter"
                className="form-select form-select-sm"
                value={currentFilters.timeRange}
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

  // Patient Detail Modal
  const PatientDetailModal = ({ patient, onClose }) => {
    if (!patient) return null;

    if (patient.error) {
        return (
            <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
                <div className="modal-dialog modal-sm">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h5 className="modal-title text-danger">Error</h5>
                            <button type="button" className="btn-close" onClick={onClose}></button>
                        </div>
                        <div className="modal-body">
                            <p>{patient.error}</p>
                        </div>
                        <div className="modal-footer">
                            <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
      <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
        <div className="modal-dialog modal-lg modal-dialog-scrollable">
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">Patient Detail: {patient.demographics?.given_name} {patient.demographics?.family_name} (ID: {patient.id})</h5>
              <button type="button" className="btn-close" onClick={onClose}></button>
            </div>
            <div className="modal-body">
              {/* Demographics */}
              <div className="mb-4">
                <h6 className="border-bottom pb-2 mb-2">Demographics</h6>
                <div className="row">
                  <div className="col-md-6">
                    <p><strong>Gender:</strong> {patient.demographics?.gender}</p>
                    <p><strong>Nationality:</strong> {patient.nationality}</p>
                    <p><strong>Age:</strong> {patient.age}</p>
                  </div>
                  <div className="col-md-6">
                    <p><strong>Blood Type:</strong> {patient.demographics?.blood_type}</p>
                    <p><strong>Weight:</strong> {patient.demographics?.weight} kg</p>
                    <p><strong>DOB:</strong> {patient.demographics?.birthdate}</p>
                  </div>
                </div>
              </div>
              {/* Medical Info */}
              <div className="mb-4">
                <h6 className="border-bottom pb-2 mb-2">Medical Information</h6>
                <p><strong>Primary Condition:</strong> {patient.primary_condition?.display} ({patient.primary_condition?.severity})</p>
                <p><strong>Triage Category:</strong> {patient.triage_category}</p>
                <p><strong>Injury Type:</strong> {patient.injury_type}</p>
                {patient.additional_conditions?.length > 0 && (
                  <div>
                    <strong>Additional Conditions:</strong>
                    <ul className="list-unstyled mb-0 ps-3">
                      {patient.additional_conditions.map((condition, idx) => (
                        <li key={idx}>{condition.display}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              {/* Treatment History */}
              <div>
                <h6 className="border-bottom pb-2 mb-2">Treatment History</h6>
                {patient.treatment_history?.length > 0 ? (
                  <div className="timeline">
                    {patient.treatment_history.map((treatment, idx) => (
                      <div key={idx} className="timeline-item mb-3">
                        <div className="timeline-marker" style={{backgroundColor: idx === 0 ? '#0d6efd' : '#6c757d'}}></div>
                        <div className="timeline-content card card-body shadow-sm p-3">
                          <h6 className="mb-1">{treatment.facility} - {new Date(treatment.date).toLocaleString()}</h6>
                          {treatment.treatments?.length > 0 && (
                            <div>
                              <strong>Treatments:</strong>
                              <ul className="list-unstyled ps-3 mb-1">
                                {treatment.treatments.map((t, i) => (<li key={i}>{t.display}</li>))}
                              </ul>
                            </div>
                          )}
                          {treatment.observations?.length > 0 && (
                            <div>
                              <strong>Observations:</strong>
                              <ul className="list-unstyled ps-3 mb-0">
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
                ) : <p>No treatment history available.</p>}
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
  
  // Example of how to trigger patient detail view (e.g., from a list of patients)
  // This part would be integrated into one of the views, like a patient list table.
  // For now, just a button to test:
  const TestPatientDetailButton = () => (
    <button className="btn btn-info btn-sm" onClick={() => handlePatientSelect("PATIENT_MOCK_ID_123")}>
      Show Mock Patient Detail
    </button>
  );


  const renderTabContent = () => {
    if (!displayedData) return <div className="alert alert-light">Select a job to view data.</div>;
    switch (activeTab) {
      case 'summary':
        return <SummaryView data={displayedData} />;
      case 'patientFlow':
        return <PatientFlowSankey data={displayedData.patient_flow} />;
      case 'facilityUsage':
        return <FacilityUsageView data={displayedData} />;
      case 'timeline':
        return <TimelineAnalysisView data={displayedData} />;
      case 'nationality':
        return <NationalityDistributionView data={displayedData} />;
      // Add cases for other tabs
      default:
        return <SummaryView data={displayedData} />;
    }
  };

  return (
    <div className="container-fluid mt-3" id="printable-dashboard">
      <div className="row">
        <div className="col-12">
          <h2 className="mb-3"><FilePieChart /> Enhanced Visualization Dashboard</h2>
          <JobSelector />
          {loading && selectedJobId && <div className="text-center my-3"><div className="spinner-border text-secondary" role="status"><span className="visually-hidden">Loading job data...</span></div><p>Loading data for {selectedJobId}...</p></div>}
          {error && <div className="alert alert-danger"><AlertCircle /> {error}</div>}
        </div>
      </div>

      {displayedData && (
        <>
          <AdvancedFilters onFilterChange={handleFilterChange} dashboardData={dashboardData} currentFilters={filters} />
          <ExportButtons data={displayedData} tabName={activeTab} />
          {/* Test button for patient detail - remove or integrate properly later */}
          {/* <TestPatientDetailButton />  */}


          <ul className="nav nav-tabs mb-3">
            <li className="nav-item"><a className={`nav-link ${activeTab === 'summary' ? 'active' : ''}`} href="#" onClick={(e) => {e.preventDefault(); setActiveTab('summary');}}>Summary</a></li>
            <li className="nav-item"><a className={`nav-link ${activeTab === 'patientFlow' ? 'active' : ''}`} href="#" onClick={(e) => {e.preventDefault(); setActiveTab('patientFlow');}}>Patient Flow</a></li>
            <li className="nav-item"><a className={`nav-link ${activeTab === 'facilityUsage' ? 'active' : ''}`} href="#" onClick={(e) => {e.preventDefault(); setActiveTab('facilityUsage');}}>Facility Usage</a></li>
            <li className="nav-item"><a className={`nav-link ${activeTab === 'timeline' ? 'active' : ''}`} href="#" onClick={(e) => {e.preventDefault(); setActiveTab('timeline');}}>Timeline</a></li>
            <li className="nav-item"><a className={`nav-link ${activeTab === 'nationality' ? 'active' : ''}`} href="#" onClick={(e) => {e.preventDefault(); setActiveTab('nationality');}}>Nationalities</a></li>
            {/* Add more tabs here */}
          </ul>
          
          {renderTabContent()}
        </>
      )}
      {selectedPatient && <PatientDetailModal patient={selectedPatient} onClose={() => setSelectedPatient(null)} />}
    </div>
  );
};

// Mount the React component
const domContainer = document.querySelector('#visualization-dashboard');
if (domContainer) {
  const root = ReactDOM.createRoot(domContainer);
  root.render(
    <StrictMode>
      <ExerciseDashboard />
    </StrictMode>
  );
} else {
  console.error('Dashboard container not found.');
}
