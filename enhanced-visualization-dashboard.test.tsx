import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react'; // Removed act, as explicit usage made it fail
import ExerciseDashboard from './enhanced-visualization-dashboard'; // Adjusted import path

// Mock fetch API
global.fetch = jest.fn();

// Mock dashboard data - ensure this matches the DashboardData interface structure
const mockDashboardData = {
  summary: {
    totalPatients: 1440,
    kia: 276,
    rtd: 824,
    inTreatment: 340
  },
  nationalityDistribution: [
    { name: "POL", value: 522 },
    { name: "EST", value: 389 }
  ],
  injuryDistribution: [
    { name: "Disease", value: 749 },
    { name: "Non-Battle", value: 475 },
  ],
  frontDistribution: [{ name: "Polish", value: 720, kiaRate: 10 }],
  statusDistribution: [{ name: "KIA", value: 276 }],
  triageDistribution: [{ name: "T1", value: 331 }],
  patientFlow: {
    nodes: [{ name: "POI" }, { name: "R1" }],
    links: [{ source: 0, target: 1, value: 100 }]
  },
  outcomesByTriage: [{ name: "T1", RTD: 115, KIA: 156, R4: 60 }],
  commonTreatments: [{ name: "Medication", value: 749 }],
  facilityLoadByDay: [{ day: "Day 1", R1: 230, R2: 64, R3: 20, R4: 12 }],
  facilityCapacityRadar: [{ subject: "Bed Capacity", value: 76 }],
  treatmentTimeDistribution: [{ facility: "R1", time: 3, count: 691 }],
  casualtyFlowByDay: [{ day: "Day 1", DISEASE: 150, NON_BATTLE: 95, BATTLE_TRAUMA: 43 }],
  triageByDay: [{ day: "Day 1", T1: 66, T2: 95, T3: 127 }],
  statusRatesByDay: [{ day: "Day 1", kiaRate: 20.8, rtdRate: 58.3 }],
  patientStatusByDay: [{ day: "Day 1", POI: 0, R1: 20, R2: 22, R3: 16, R4: 14, RTD: 168, KIA: 60 }],
  injuryTypeByFront: [{ front: "Polish", DISEASE: 374, NON_BATTLE: 238, BATTLE_TRAUMA: 108 }],
  kiaRateByFront: [{front: "Polish", kiaRate: 19.2 }],
  rtdRateByFront: [{front: "Polish", rtdRate: 57.5 }],
  nationalityByFront: [{ front: "Polish", POL: 360 }],
  treatmentComparisonByFront: [{ treatment: "First Aid", Polish: 100 }]
};

const mockJobList = [
  { job_id: "job1", total_patients: 1440, created_at: new Date().toISOString() },
  { job_id: "job2", total_patients: 500, created_at: new Date().toISOString() }
];

beforeEach(() => {
  // Reset mocks before each test
  (global.fetch as jest.Mock).mockClear();
  // Default mock for job list, made more explicitly async
  (global.fetch as jest.Mock).mockImplementation(async (url) => {
    if (url === '/api/visualizations/job-list') {
      await new Promise(resolve => setTimeout(resolve, 0)); // Ensure macro task
      return {
        ok: true,
        json: async () => {
          await new Promise(resolve => setTimeout(resolve, 0));
          return mockJobList;
        },
      };
    }
    if (url.startsWith('/api/visualizations/dashboard-data')) {
      await new Promise(resolve => setTimeout(resolve, 0));
      return {
        ok: true,
        json: async () => {
          await new Promise(resolve => setTimeout(resolve, 0));
          return mockDashboardData;
        },
      };
    }
    // Fallback for unhandled URLs
    await new Promise(resolve => setTimeout(resolve, 0));
    return Promise.reject(new Error(`Unhandled fetch URL: ${url}`));
  });
});

test('renders dashboard with loading job list state initially', () => {
  render(<ExerciseDashboard />);
  // The component first tries to load the job list.
  expect(screen.getByText(/Loading job list.../i)).toBeInTheDocument();
});

test('renders dashboard with data after job list and dashboard data load', async () => {
  render(<ExerciseDashboard />);
  
  // Wait for a key piece of data that indicates all initial loading is complete.
  // This includes job list fetch, selection of the first job, and dashboard data fetch for that job.
  expect(await screen.findByText('1,440', {}, { timeout: 4000 })).toBeInTheDocument(); // Total patients from mockDashboardData

  // After the main data is loaded and act has resolved, other elements should be verifiable
  expect(screen.getByRole('combobox', { name: /Exercise Job:/i })).toHaveValue('job1');
  expect(screen.getByText('276')).toBeInTheDocument();  // KIA count
  
  // Tabs should be present
  expect(screen.getByText('Patient Flow')).toBeInTheDocument();
  expect(screen.getByText('Facilities')).toBeInTheDocument();
  expect(screen.getByText('Timeline')).toBeInTheDocument();
  expect(screen.getByText('Comparative')).toBeInTheDocument();
});

test('tab navigation works', async () => {
  render(<ExerciseDashboard />);
  
  await waitFor(() => {
    expect(screen.getByText('Exercise Overview')).toBeInTheDocument();
  }, { timeout: 3000 });
  
  fireEvent.click(screen.getByText('Patient Flow'));
  // Assuming each tab section has a unique identifiable text or heading
  // The actual text might differ based on the tab's content structure
  await waitFor(() => {
    expect(screen.getByText('Patient Flow Analysis')).toBeInTheDocument();
  });
  
  fireEvent.click(screen.getByText('Facilities'));
  await waitFor(() => {
    expect(screen.getByText('Medical Facilities Analysis')).toBeInTheDocument();
  });
});

test('filtering by front works', async () => {
  render(<ExerciseDashboard />);
  
  await waitFor(() => {
    expect(screen.getByText('Exercise Overview')).toBeInTheDocument();
  }, { timeout: 3000 });
  
  const frontSelector = screen.getByLabelText(/Front:/i);
  fireEvent.change(frontSelector, { target: { value: 'Polish' } });
  
  // API should be called with the filter
  // The fetch mock is called multiple times (job list, then dashboard data)
  // We need to check the call for dashboard data specifically.
  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/visualizations/dashboard-data?job_id=job1&front=Polish'));
  });
});

test('job selection works', async () => {
  render(<ExerciseDashboard />);

  await waitFor(() => {
    expect(screen.getByLabelText(/Exercise Job:/i)).toBeInTheDocument();
  }, { timeout: 3000 });

  const jobSelector = screen.getByLabelText(/Exercise Job:/i);
  fireEvent.change(jobSelector, { target: { value: 'job2' } });

  await waitFor(() => {
    expect(global.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/visualizations/dashboard-data?job_id=job2'));
  });
});
