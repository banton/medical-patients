import React, { useState, useEffect, useCallback } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar, PieChart, Pie, Cell, Sankey, Scatter, ScatterChart, ZAxis,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { AlertCircle, FilePieChart, Calendar, Activity, Map, Users, ArrowRight, ChevronDown, ChevronUp, ServerCrash } from 'lucide-react';

interface JobSummary {
  job_id: string;
  total_patients: number;
  created_at: string;
  // Add other relevant fields from your job list API if needed
}

interface DashboardData {
  summary: {
    totalPatients: number;
    kia: number;
    rtd: number;
    inTreatment: number;
  };
  nationalityDistribution: Array<{ name: string; value: number }>;
  injuryDistribution: Array<{ name: string; value: number }>;
  frontDistribution: Array<{ name: string; value: number; kiaRate?: number }>;
  statusDistribution: Array<{ name: string; value: number }>;
  triageDistribution: Array<{ name: string; value: number }>;
  patientFlow: {
    nodes: Array<{ name: string }>;
    links: Array<{ source: number; target: number; value: number }>;
  };
  outcomesByTriage: Array<{ name: string; RTD: number; KIA: number; R4: number }>;
  commonTreatments: Array<{ name: string; value: number }>;
  facilityLoadByDay: Array<{ day: string; R1: number; R2: number; R3: number; R4: number }>;
  facilityCapacityRadar: Array<{ subject: string; value: number }>;
  treatmentTimeDistribution: Array<{ facility: string; time: number; count: number }>;
  casualtyFlowByDay: Array<{ day: string; DISEASE: number; NON_BATTLE: number; BATTLE_TRAUMA: number }>;
  triageByDay: Array<{ day: string; T1: number; T2: number; T3: number }>;
  statusRatesByDay: Array<{ day: string; kiaRate: number; rtdRate: number }>;
  patientStatusByDay: Array<{ day: string; POI: number; R1: number; R2: number; R3: number; R4: number; RTD: number; KIA: number }>;
  injuryTypeByFront: Array<{ front: string; DISEASE: number; NON_BATTLE: number; BATTLE_TRAUMA: number }>;
  kiaRateByFront: Array<{ front: string; kiaRate: number }>;
  rtdRateByFront: Array<{ front: string; rtdRate: number }>;
  nationalityByFront: Array<{ front: string; POL?: number; EST?: number; FIN?: number; GBR?: number; USA?: number; LIT?: number; ESP?: number; NLD?: number; }>;
  treatmentComparisonByFront: Array<{ treatment: string; Polish?: number; Estonian?: number; Finnish?: number }>;
}

// Main Dashboard Component
const ExerciseDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [jobList, setJobList] = useState<JobSummary[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [selectedFront, setSelectedFront] = useState('all');
  const [expandedSections, setExpandedSections] = useState({
    overview: true,
    patientFlow: true,
    facilities: true,
    timeline: true,
    comparative: true
  });

  // Fetch job list on component mount
  useEffect(() => {
    const fetchJobList = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/visualizations/job-list');
        if (!response.ok) {
          throw new Error(`Failed to fetch job list: ${response.statusText}`);
        }
        const data: JobSummary[] = await response.json();
        setJobList(data);
        if (data.length > 0) {
          setSelectedJobId(data[0].job_id); 
        } else {
          setLoading(false); 
          setDashboardData(null); 
        }
      } catch (err) {
        console.error("Error fetching job list:", err);
        setError(err instanceof Error ? err.message : String(err));
        setLoading(false);
      }
    };
    fetchJobList();
  }, []);

  const fetchDashboardData = useCallback(async () => {
    if (!selectedJobId) {
      setDashboardData(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ job_id: selectedJobId });
      if (selectedFront !== 'all') {
        params.append('front', selectedFront);
      }
      const response = await fetch(`/api/visualizations/dashboard-data?${params.toString()}`);
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Failed to fetch dashboard data: ${response.statusText} - ${errorText}`);
      }
      const data: DashboardData = await response.json();
      setDashboardData(data);
    } catch (err) {
      console.error("Error fetching dashboard data:", err);
      setError(err instanceof Error ? err.message : String(err));
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  }, [selectedJobId, selectedFront]);

  useEffect(() => {
    if (selectedJobId) {
      fetchDashboardData();
    }
  }, [fetchDashboardData, selectedJobId]);

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleFrontChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedFront(e.target.value);
  };

  const handleJobChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedJobId(e.target.value);
  };

  if (loading && jobList.length === 0 && !error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Loading job list...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 p-4 text-center">
        <ServerCrash size={48} className="text-red-500 mb-4" />
        <h3 className="text-xl font-semibold text-red-700 mb-2">Error Accessing Data</h3>
        <p className="text-gray-600 mb-4">We encountered an issue. Please try again later or check the console for details.</p>
        <pre className="text-xs text-left bg-red-50 p-2 border border-red-200 rounded w-full max-w-lg overflow-auto">{error}</pre>
      </div>
    );
  }
  
  if (jobList.length === 0 && !loading) {
    return (
      <div className="flex flex-col items-center justify-center h-96 p-4 text-center">
        <AlertCircle size={48} className="text-gray-500 mb-4" />
        <h3 className="text-xl font-semibold text-gray-700 mb-2">No Exercise Jobs Found</h3>
        <p className="text-gray-600">There are no exercise jobs available to visualize. Please generate some data first.</p>
      </div>
    );
  }

  if (loading && selectedJobId && !dashboardData && !error) {
     return (
      <div className="flex items-center justify-center h-96">
        <div className="text-lg text-gray-600">Loading visualization data for job: {selectedJobId}...</div>
      </div>
    );
  }

  if (selectedJobId && !dashboardData && !loading && !error) {
    return (
      <div className="flex flex-col items-center justify-center h-96 p-4 text-center">
        <AlertCircle size={48} className="text-yellow-500 mb-4" />
        <h3 className="text-xl font-semibold text-yellow-700 mb-2">No Data Available</h3>
        <p className="text-gray-600">No visualization data found for the selected job ({selectedJobId}) or filters.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
      <div className="bg-blue-600 text-white p-4">
        <h2 className="text-xl font-bold">Military Medical Exercise Visualization Dashboard</h2>
        <p className="text-sm opacity-80">Interactive analytics and visualizations for exercise planning</p>
      </div>

      <div className="bg-gray-100 border-b">
        <div className="flex overflow-x-auto">
          {['overview', 'patientFlow', 'facilities', 'timeline', 'comparative'].map(tab => (
            <button 
              key={tab}
              className={`px-4 py-2 font-medium text-sm ${activeTab === tab ? 'bg-white border-b-2 border-blue-600' : 'text-gray-600 hover:bg-gray-200'}`}
              onClick={() => setActiveTab(tab)}>
              {tab.charAt(0).toUpperCase() + tab.slice(1).replace('Flow', ' Flow')}
            </button>
          ))}
        </div>
      </div>

      <div className="p-3 bg-gray-50 border-b">
        <div className="flex flex-wrap gap-4 items-center">
          <label htmlFor="jobSelect" className="flex items-center gap-2 text-sm font-medium">
            <span>Exercise Job:</span>
            <select
              id="jobSelect"
              value={selectedJobId || ''}
              onChange={handleJobChange}
              className="border rounded p-1 text-sm"
              disabled={jobList.length === 0 || loading}
            >
              {jobList.length === 0 && <option>No jobs available</option>}
              {jobList.map(job => (
                <option key={job.job_id} value={job.job_id}>
                  {job.job_id} (Patients: {job.total_patients}, Created: {new Date(job.created_at).toLocaleDateString()})
                </option>
              ))}
            </select>
          </label>

          <label htmlFor="frontSelect" className="flex items-center gap-2 text-sm font-medium">
            <span>Front:</span>
            <select
              id="frontSelect"
              value={selectedFront}
              onChange={handleFrontChange}
              className="border rounded p-1 text-sm"
              disabled={!dashboardData || loading}
            >
              <option value="all">All Fronts</option>
              <option value="Polish">Polish Front</option>
              <option value="Estonian">Estonian Front</option>
              <option value="Finnish">Finnish Front</option>
            </select>
          </label>
          
          {dashboardData && dashboardData.summary && (
            <div className="ml-auto flex items-center text-xs text-gray-500">
              <AlertCircle size={14} className="mr-1" />
              <span>Data based on {dashboardData.summary.totalPatients?.toLocaleString()} simulated patients</span>
            </div>
          )}
        </div>
      </div>

      {dashboardData && !loading && (
        <div className="p-4">
          {activeTab === 'overview' && (
            <OverviewTab 
              data={dashboardData} 
              expanded={expandedSections.overview}
              toggleExpanded={() => toggleSection('overview')} 
            />
          )}
          {activeTab === 'patientFlow' && (
            <PatientFlowTab 
              data={dashboardData} 
              front={selectedFront}
              expanded={expandedSections.patientFlow}
              toggleExpanded={() => toggleSection('patientFlow')} 
            />
          )}
          {activeTab === 'facilities' && (
            <FacilitiesTab 
              data={dashboardData} 
              front={selectedFront}
              expanded={expandedSections.facilities}
              toggleExpanded={() => toggleSection('facilities')} 
            />
          )}
          {activeTab === 'timeline' && (
            <TimelineTab 
              data={dashboardData} 
              front={selectedFront}
              expanded={expandedSections.timeline}
              toggleExpanded={() => toggleSection('timeline')} 
            />
          )}
          {activeTab === 'comparative' && (
            <ComparativeTab 
              data={dashboardData}
              expanded={expandedSections.comparative}
              toggleExpanded={() => toggleSection('comparative')} 
            />
          )}
        </div>
      )}
    </div>
  );
};

// Props interfaces for Tab components
interface TabProps {
  data: DashboardData;
  expanded: boolean;
  toggleExpanded: () => void;
}

interface FilterableTabProps extends TabProps {
  front: string;
}

const OverviewTab = ({ data, expanded, toggleExpanded }: TabProps) => {
  return (
    <div className="space-y-4">
      <SectionHeader 
        title="Exercise Overview" 
        icon={<FilePieChart size={18} />} 
        expanded={expanded}
        toggleExpanded={toggleExpanded}
      />
      {expanded && data.summary && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <SummaryCard title="Total Patients" value={data.summary.totalPatients?.toLocaleString() || 'N/A'} color="blue" />
            <SummaryCard title="KIA" value={data.summary.kia?.toLocaleString() || 'N/A'} color="red" />
            <SummaryCard title="RTD" value={data.summary.rtd?.toLocaleString() || 'N/A'} color="green" />
            <SummaryCard title="In Treatment" value={data.summary.inTreatment?.toLocaleString() || 'N/A'} color="yellow" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {data.nationalityDistribution && data.nationalityDistribution.length > 0 && (
            <ChartContainer title="Nationality Distribution">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={data.nationalityDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                    {data.nationalityDistribution.map((entry, index) => (<Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [value, 'Patients']} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
            )}
            {data.injuryDistribution && data.injuryDistribution.length > 0 && (
            <ChartContainer title="Injury Type Distribution">
              <ResponsiveContainer width="100%" height={250}>
                <PieChart>
                  <Pie data={data.injuryDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                    {data.injuryDistribution.map((entry, index) => (<Cell key={`cell-${index}`} fill={INJURY_COLORS[index % INJURY_COLORS.length]} />))}
                  </Pie>
                  <Tooltip formatter={(value: number) => [value, 'Patients']} />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
            )}
            {data.kiaRateByFront && data.kiaRateByFront.length > 0 && (
            <ChartContainer title="KIA Rate by Front">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.kiaRateByFront}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Bar dataKey="kiaRate" fill="#F44336" name="KIA Rate (%)" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
            )}
            {data.rtdRateByFront && data.rtdRateByFront.length > 0 && (
            <ChartContainer title="RTD Rate by Front">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.rtdRateByFront}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Bar dataKey="rtdRate" fill="#4CAF50" name="RTD Rate (%)" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
            )}
          </div>
          {data.nationalityByFront && data.nationalityByFront.length > 0 && (
          <ChartContainer title="Nationality Distribution Comparison by Front">
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={data.nationalityByFront}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="POL" fill="#E91E63" name="Polish" /><Bar dataKey="EST" fill="#9C27B0" name="Estonian" /><Bar dataKey="FIN" fill="#2196F3" name="Finnish" />
                <Bar dataKey="GBR" fill="#3F51B5" name="British" /><Bar dataKey="USA" fill="#F44336" name="American" /><Bar dataKey="LIT" fill="#FF9800" name="Lithuanian" />
                <Bar dataKey="ESP" fill="#FFEB3B" name="Spanish" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          )}
          {data.treatmentComparisonByFront && data.treatmentComparisonByFront.length > 0 && (
          <ChartContainer title="Medical Treatment Comparison by Front">
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart outerRadius={90} data={data.treatmentComparisonByFront}>
                <PolarGrid /><PolarAngleAxis dataKey="treatment" /><PolarRadiusAxis angle={30} domain={[0, 100]} /><Tooltip /><Legend />
                <Radar name="Polish Front" dataKey="Polish" stroke="#E91E63" fill="#E91E63" fillOpacity={0.3} />
                <Radar name="Estonian Front" dataKey="Estonian" stroke="#2196F3" fill="#2196F3" fillOpacity={0.3} />
                <Radar name="Finnish Front" dataKey="Finnish" stroke="#4CAF50" fill="#4CAF50" fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </ChartContainer>
          )}
        </>
      )}
    </div>
  );
};

const PatientFlowTab = ({ data, front, expanded, toggleExpanded }: FilterableTabProps) => {
  const flowData = front === 'all' || !data.patientFlow ? data.patientFlow : filterPatientFlowByFront(data.patientFlow, front);
  return (
    <div className="space-y-4">
      <SectionHeader title="Patient Flow Analysis" icon={<Activity size={18} />} expanded={expanded} toggleExpanded={toggleExpanded}/>
      {expanded && data.patientFlow && (
        <>
          <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md text-sm">
            <p className="font-semibold">Patient Flow Visualization</p>
            <p>This sankey diagram shows how patients flow through the medical treatment chain. The width of each flow represents the number of patients.</p>
          </div>
          <ChartContainer title="Patient Flow Through Medical Facilities">
            <div className="h-96 w-full"><PatientFlowSankey data={flowData} /></div>
          </ChartContainer>
          {data.triageDistribution && data.outcomesByTriage && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartContainer title="Triage Categories">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={data.triageDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({name, percent}) => `${name} (${(percent * 100).toFixed(0)}%)`}>
                      {data.triageDistribution.map((entry, index) => (<Cell key={`cell-${index}`} fill={TRIAGE_COLORS[entry.name as keyof typeof TRIAGE_COLORS] || '#8884d8'} />))}
                    </Pie>
                    <Tooltip formatter={(value: number) => [value, 'Patients']} />
                  </PieChart>
                </ResponsiveContainer>
              </ChartContainer>
              <ChartContainer title="Outcomes by Triage Category">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.outcomesByTriage}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Legend />
                    <Bar dataKey="RTD" stackId="a" fill="#4CAF50" name="Return to Duty" /><Bar dataKey="KIA" stackId="a" fill="#F44336" name="Killed in Action" /><Bar dataKey="R4" stackId="a" fill="#9C27B0" name="Role 4" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          )}
          {data.commonTreatments && (
            <ChartContainer title="Most Common Treatments">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart layout="vertical" data={data.commonTreatments}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis dataKey="name" type="category" width={200} tick={{fontSize: 12}} /><Tooltip formatter={(value: number) => [value, 'Patients']} /><Bar dataKey="value" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
        </>
      )}
    </div>
  );
};

const PatientFlowSankey = ({ data }: { data: DashboardData['patientFlow'] | undefined }) => {
  if (!data || !data.nodes || !data.links || data.nodes.length === 0) { // Added check for empty nodes
    return <div className="text-center p-4 h-96 flex items-center justify-center bg-gray-50 border rounded-lg">Sankey data not available or nodes are empty.</div>;
  }
  return (
    <ResponsiveContainer width="100%" height="100%">
      <Sankey data={data} nodePadding={15} nodeWidth={20} linkCurvature={0.5} iterations={32} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
        <Tooltip />
      </Sankey>
    </ResponsiveContainer>
  );
};

const FacilitiesTab = ({ data, front, expanded, toggleExpanded }: FilterableTabProps) => {
  return (
    <div className="space-y-4">
      <SectionHeader title="Medical Facilities Analysis" icon={<Map size={18} />} expanded={expanded} toggleExpanded={toggleExpanded}/>
      {expanded && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <FacilityCard facility="R1" data={{ patients: data.facilityLoadByDay?.reduce((sum, day) => sum + (day.R1 || 0), 0) || 0, capacity: 1500, avgStay: "3.2 hours", peakLoad: `Day ${data.facilityLoadByDay?.reduce((max, day) => (day.R1 || 0) > (max.val || 0) ? {day: day.day, val: day.R1} : max, {day:'', val:0}).day || 'N/A'}`, rtdRate: "60%", color: "green"}} />
            <FacilityCard facility="R2" data={{ patients: data.facilityLoadByDay?.reduce((sum, day) => sum + (day.R2 || 0), 0) || 0, capacity: 400, avgStay: "18.5 hours", peakLoad: `Day ${data.facilityLoadByDay?.reduce((max, day) => (day.R2 || 0) > (max.val || 0) ? {day: day.day, val: day.R2} : max, {day:'', val:0}).day || 'N/A'}`, rtdRate: "55%", color: "yellow"}} />
            <FacilityCard facility="R3" data={{ patients: data.facilityLoadByDay?.reduce((sum, day) => sum + (day.R3 || 0), 0) || 0, capacity: 200, avgStay: "2.7 days", peakLoad: `Day ${data.facilityLoadByDay?.reduce((max, day) => (day.R3 || 0) > (max.val || 0) ? {day: day.day, val: day.R3} : max, {day:'', val:0}).day || 'N/A'}`, rtdRate: "30%", color: "orange"}} />
          </div>
          {data.facilityLoadByDay && (
            <ChartContainer title="Facility Load Over Exercise Timeline">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={data.facilityLoadByDay}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Tooltip /><Legend />
                  <Line type="monotone" dataKey="R1" stroke="#4CAF50" activeDot={{ r: 8 }} name="Role 1" /><Line type="monotone" dataKey="R2" stroke="#FFC107" activeDot={{ r: 8 }} name="Role 2" />
                  <Line type="monotone" dataKey="R3" stroke="#FF9800" activeDot={{ r: 8 }} name="Role 3" /><Line type="monotone" dataKey="R4" stroke="#9C27B0" activeDot={{ r: 8 }} name="Role 4" />
                </LineChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
          {data.facilityCapacityRadar && data.treatmentTimeDistribution && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartContainer title="Treatment Capacity Analysis">
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart outerRadius={90} data={data.facilityCapacityRadar}>
                    <PolarGrid /><PolarAngleAxis dataKey="subject" /><PolarRadiusAxis angle={30} domain={[0, 100]} /><Radar name="Capacity Used (%)" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} /><Legend /><Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </ChartContainer>
              <ChartContainer title="Patient Treatment Time Distribution">
                <ResponsiveContainer width="100%" height={300}>
                  <ScatterChart>
                    <CartesianGrid /><XAxis type="category" dataKey="facility" name="Facility" /><YAxis type="number" dataKey="time" name="Hours" unit="h"/><ZAxis type="number" dataKey="count" range={[40, 200]} name="Patients" /><Tooltip cursor={{ strokeDasharray: '3 3' }} /><Legend /><Scatter name="Treatment Time" data={data.treatmentTimeDistribution} fill="#8884d8" />
                  </ScatterChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const FacilityCard = ({ facility, data }: { facility: string, data: { patients: number, capacity: number, avgStay: string, peakLoad: string, rtdRate: string, color: string } }) => {
  const { patients, capacity, avgStay, peakLoad, rtdRate, color } = data;
  const utilizationPercent = capacity > 0 ? Math.round((patients / capacity) * 100) : 0;
  const colorClasses = { green: "bg-green-100 border-green-300 text-green-800", yellow: "bg-yellow-100 border-yellow-300 text-yellow-800", orange: "bg-orange-100 border-orange-300 text-orange-800", red: "bg-red-100 border-red-300 text-red-800", purple: "bg-purple-100 border-purple-300 text-purple-800" };
  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color as keyof typeof colorClasses] || 'bg-gray-100 border-gray-300'}`}>
      <div className="flex justify-between items-center mb-3"><h3 className="text-lg font-bold">Role {facility}</h3><span className="text-xs font-semibold uppercase px-2 py-1 rounded bg-white">{utilizationPercent}% Utilized</span></div>
      <div className="space-y-2 text-sm">
        <div className="flex justify-between"><span>Patients Treated:</span><span className="font-semibold">{patients.toLocaleString()}</span></div>
        <div className="flex justify-between"><span>Capacity:</span><span className="font-semibold">{capacity.toLocaleString()}</span></div>
        <div className="flex justify-between"><span>Avg Stay:</span><span className="font-semibold">{avgStay}</span></div>
        <div className="flex justify-between"><span>Peak Load:</span><span className="font-semibold">{peakLoad}</span></div>
        <div className="flex justify-between"><span>RTD Rate:</span><span className="font-semibold">{rtdRate}</span></div>
      </div>
      <div className="mt-3 h-2 bg-white rounded-full overflow-hidden"><div className={`h-full ${utilizationPercent > 90 ? 'bg-red-500' : utilizationPercent > 70 ? 'bg-yellow-500' : 'bg-green-500'}`} style={{ width: `${utilizationPercent}%` }}></div></div>
    </div>
  );
};

const TimelineTab = ({ data, front, expanded, toggleExpanded }: FilterableTabProps) => {
  return (
    <div className="space-y-4">
      <SectionHeader title="Exercise Timeline Analysis" icon={<Calendar size={18} />} expanded={expanded} toggleExpanded={toggleExpanded}/>
      {expanded && data.casualtyFlowByDay && (
        <>
          <ChartContainer title="Casualty Flow by Day">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.casualtyFlowByDay}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="DISEASE" stackId="a" fill="#4CAF50" name="Disease" /><Bar dataKey="NON_BATTLE" stackId="a" fill="#2196F3" name="Non-Battle Injury" /><Bar dataKey="BATTLE_TRAUMA" stackId="a" fill="#F44336" name="Battle Trauma" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          {data.triageByDay && data.statusRatesByDay && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartContainer title="Triage Categories by Day">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.triageByDay}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Tooltip /><Legend />
                    <Bar dataKey="T1" stackId="a" fill="#F44336" name="T1 (Immediate)" /><Bar dataKey="T2" stackId="a" fill="#FFC107" name="T2 (Urgent)" /><Bar dataKey="T3" stackId="a" fill="#4CAF50" name="T3 (Delayed)" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
              <ChartContainer title="KIA and RTD Rates by Day">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={data.statusRatesByDay}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Tooltip /><Legend />
                    <Line type="monotone" dataKey="kiaRate" stroke="#F44336" name="KIA Rate (%)" /><Line type="monotone" dataKey="rtdRate" stroke="#4CAF50" name="RTD Rate (%)" />
                  </LineChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          )}
          {data.patientStatusByDay && (
            <ChartContainer title="Patient Status Distribution Over Time">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={data.patientStatusByDay}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="day" /><YAxis /><Tooltip /><Legend />
                  <Bar dataKey="POI" stackId="a" fill="#2196F3" name="Point of Injury" /><Bar dataKey="R1" stackId="a" fill="#4CAF50" name="Role 1" /><Bar dataKey="R2" stackId="a" fill="#FFC107" name="Role 2" />
                  <Bar dataKey="R3" stackId="a" fill="#FF9800" name="Role 3" /><Bar dataKey="R4" stackId="a" fill="#9C27B0" name="Role 4" /><Bar dataKey="RTD" stackId="a" fill="#3F51B5" name="Return to Duty" />
                  <Bar dataKey="KIA" stackId="a" fill="#F44336" name="Killed in Action" />
                </BarChart>
              </ResponsiveContainer>
            </ChartContainer>
          )}
        </>
      )}
    </div>
  );
};

const ComparativeTab = ({ data, expanded, toggleExpanded }: TabProps) => {
  return (
    <div className="space-y-4">
      <SectionHeader title="Comparative Analysis" icon={<Users size={18} />} expanded={expanded} toggleExpanded={toggleExpanded}/>
      {expanded && data.injuryTypeByFront && (
        <>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-sm mb-4">
            <p className="font-semibold">Front-by-Front Comparison</p>
            <p>This section compares key metrics across different operational fronts to identify patterns and variations.</p>
          </div>
          <ChartContainer title="Casualty Types by Front">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.injuryTypeByFront}>
                <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Legend />
                <Bar dataKey="DISEASE" fill="#4CAF50" name="Disease" /><Bar dataKey="NON_BATTLE" fill="#2196F3" name="Non-Battle Injury" /><Bar dataKey="BATTLE_TRAUMA" fill="#F44336" name="Battle Trauma" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          {data.kiaRateByFront && data.rtdRateByFront && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ChartContainer title="KIA Rate by Front">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.kiaRateByFront}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Bar dataKey="kiaRate" fill="#F44336" name="KIA Rate (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
              <ChartContainer title="RTD Rate by Front">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={data.rtdRateByFront}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="front" /><YAxis /><Tooltip /><Bar dataKey="rtdRate" fill="#4CAF50" name="RTD Rate (%)" />
                  </BarChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const SectionHeader = ({ title, icon, expanded, toggleExpanded }: { title: string, icon: React.ReactNode, expanded: boolean, toggleExpanded: () => void }) => {
  return (
    <div className="flex items-center justify-between bg-gray-100 p-3 rounded-lg cursor-pointer" onClick={toggleExpanded}>
      <div className="flex items-center gap-2">{icon}<h3 className="text-lg font-bold">{title}</h3></div>
      <button className="text-gray-500 hover:text-gray-700">{expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</button>
    </div>
  );
};

const ChartContainer = ({ title, children }: { title: string, children: React.ReactNode }) => {
  return (
    <div className="border rounded-lg overflow-hidden">
      <div className="bg-gray-50 p-3 border-b"><h3 className="font-medium">{title}</h3></div>
      <div className="p-4">{children}</div>
    </div>
  );
};

const SummaryCard = ({ title, value, color }: { title: string, value: string | number, color: string }) => {
  const colorClasses = { blue: "bg-blue-50 border-blue-200 text-blue-800", red: "bg-red-50 border-red-200 text-red-800", green: "bg-green-50 border-green-200 text-green-800", yellow: "bg-yellow-50 border-yellow-200 text-yellow-800" };
  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color as keyof typeof colorClasses] || 'bg-gray-50 border-gray-200'}`}>
      <p className="text-sm font-medium">{title}</p>
      <p className="text-2xl font-bold mt-2">{value}</p>
    </div>
  );
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#A4DE6C', '#8884D8', '#FF6666'];
const FRONT_COLORS = ['#E91E63', '#2196F3', '#4CAF50'];
const INJURY_COLORS = ['#4CAF50', '#2196F3', '#F44336'];
const TRIAGE_COLORS = { 'T1': '#F44336', 'T2': '#FFC107', 'T3': '#4CAF50' };
const STATUS_COLORS = { 'KIA': '#F44336', 'RTD': '#4CAF50', 'R1': '#2196F3', 'R2': '#FFC107', 'R3': '#FF9800', 'R4': '#9C27B0', 'POI': '#3F51B5' };

const filterPatientFlowByFront = (flowData: DashboardData['patientFlow'], front: string): DashboardData['patientFlow'] => {
  console.warn(`filterPatientFlowByFront for front '${front}' is not fully implemented. Returning original data.`);
  return flowData;
};

export default ExerciseDashboard;

// Add rendering logic for browser execution
import ReactDOM from 'react-dom/client';

const container = document.getElementById('visualization-dashboard');
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <ExerciseDashboard />
    </React.StrictMode>
  );
} else {
  console.error('Failed to find the root element for React dashboard. Ensure an element with id="visualization-dashboard" exists.');
}
