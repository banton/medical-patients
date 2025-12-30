import { useState, useEffect, useMemo } from 'react';
import { AnimatePresence } from 'framer-motion';
import { Patient, PlaybackState, FacilityName } from './types/patient.types';
import { FileUploader } from './components/FileUploader';
import { FacilityColumn } from './components/FacilityColumn';
import { TimelineControls } from './components/TimelineControls';
import { FilterBar, FilterState, filterPatients, initialFilterState } from './components/FilterBar';
import { getTimelineExtent } from './utils/timelineEngine';
import './index.css';

const FACILITIES: FacilityName[] = ['POI', 'Role1', 'Role2', 'Role3', 'Role4'];

function App() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [playbackState, setPlaybackState] = useState<PlaybackState>({
    isPlaying: false,
    currentTime: new Date('2024-01-01T00:00:00Z'),
    speed: 1,
    startTime: new Date('2024-01-01T00:00:00Z'),
    endTime: new Date('2024-01-01T24:00:00Z'),
    isLooping: false
  });
  const [filters, setFilters] = useState<FilterState>(initialFilterState);

  // Filter patients based on current filter state
  const filteredPatients = useMemo(() => {
    return filterPatients(patients, filters, playbackState.currentTime);
  }, [patients, filters, playbackState.currentTime]);

  // Update timeline extent when patients change
  useEffect(() => {
    if (patients.length > 0) {
      const extent = getTimelineExtent(patients);
      setPlaybackState(prev => ({
        ...prev,
        currentTime: extent.start,
        startTime: extent.start,
        endTime: extent.end
      }));
    }
  }, [patients]);

  // Timeline playback effect
  useEffect(() => {
    if (!playbackState.isPlaying) return;

    const interval = setInterval(() => {
      setPlaybackState(prev => {
        // Adjust speed to make timeline much slower - divide by 10 for more realistic playback
        const adjustedSpeed = prev.speed / 10;
        const nextTime = new Date(prev.currentTime.getTime() + (3600000 * adjustedSpeed)); // Advance by 1 hour * adjustedSpeed
        
        // Handle end of timeline
        if (nextTime >= prev.endTime) {
          if (prev.isLooping) {
            // Loop back to start
            return {
              ...prev,
              currentTime: prev.startTime
            };
          } else {
            // Stop at end
            return {
              ...prev,
              currentTime: prev.endTime,
              isPlaying: false
            };
          }
        }
        
        return {
          ...prev,
          currentTime: nextTime
        };
      });
    }, 100); // Update every 100ms for smooth animation

    return () => clearInterval(interval);
  }, [playbackState.isPlaying, playbackState.speed, playbackState.isLooping]);

  // Control handlers
  const handlePlayPause = () => {
    setPlaybackState(prev => ({
      ...prev,
      isPlaying: !prev.isPlaying
    }));
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackState(prev => ({
      ...prev,
      speed
    }));
  };

  const handleReset = () => {
    setPlaybackState(prev => ({
      ...prev,
      currentTime: prev.startTime,
      isPlaying: false
    }));
  };

  const handleTimeSeek = (time: Date) => {
    setPlaybackState(prev => ({
      ...prev,
      currentTime: time,
      isPlaying: false
    }));
  };

  const handleLoopToggle = () => {
    setPlaybackState(prev => ({
      ...prev,
      isLooping: !prev.isLooping
    }));
  };

  const handleLoadPatients = (loadedPatients: Patient[]) => {
    setPatients(loadedPatients);
    console.log(`Loaded ${loadedPatients.length} patients`);
  };

  const handleClearFilters = () => {
    setFilters(initialFilterState);
  };

  // Calculate statistics and cumulative KIA/RTD counts
  const statistics = useMemo(() => {
    if (patients.length === 0) return null;

    const totalPatients = patients.length;
    const filteredCount = filteredPatients.length;

    const finalStatuses = patients.reduce((acc, patient) => {
      acc[patient.final_status] = (acc[patient.final_status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const triageCounts = patients.reduce((acc, patient) => {
      acc[patient.triage_category] = (acc[patient.triage_category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    // Calculate current status counts for filtered patients
    const currentStatuses = { KIA: 0, RTD: 0, Active: 0 };

    filteredPatients.forEach(patient => {
      if (patient.movement_timeline) {
        const injuryTime = patient.injury_timestamp
          ? new Date(patient.injury_timestamp)
          : new Date('2024-01-01T00:00:00Z');
        const currentHours = (playbackState.currentTime.getTime() - injuryTime.getTime()) / (1000 * 60 * 60);

        // Only count patients whose injury has occurred
        if (currentHours >= 0) {
          const eventsSoFar = patient.movement_timeline.filter(
            event => event.hours_since_injury <= currentHours
          );
          const kiaEvent = eventsSoFar.find(event => event.event_type === 'kia');
          const rtdEvent = eventsSoFar.find(event => event.event_type === 'rtd');

          if (kiaEvent) {
            currentStatuses.KIA++;
          } else if (rtdEvent) {
            currentStatuses.RTD++;
          } else {
            currentStatuses.Active++;
          }
        }
      }
    });

    return {
      total: totalPatients,
      filtered: filteredCount,
      finalStatuses,
      triageCounts,
      currentStatuses
    };
  }, [patients, filteredPatients, playbackState.currentTime]);

  // Calculate cumulative KIA/RTD counts up to current time for each facility
  const cumulativeCounts = useMemo(() => {
    if (filteredPatients.length === 0) return {};

    const counts: Record<FacilityName, { kia: number; rtd: number }> = {
      POI: { kia: 0, rtd: 0 },
      Role1: { kia: 0, rtd: 0 },
      Role2: { kia: 0, rtd: 0 },
      Role3: { kia: 0, rtd: 0 },
      Role4: { kia: 0, rtd: 0 }
    };

    filteredPatients.forEach(patient => {
      // Check if patient has ever been KIA or RTD up to this point in time
      if (patient.movement_timeline) {
        const injuryTime = patient.injury_timestamp ? new Date(patient.injury_timestamp) : new Date('2024-01-01T00:00:00Z');
        const currentHours = (playbackState.currentTime.getTime() - injuryTime.getTime()) / (1000 * 60 * 60);
        
        const eventsSoFar = patient.movement_timeline.filter(event => event.hours_since_injury <= currentHours);
        const kiaEvent = eventsSoFar.find(event => event.event_type === 'kia');
        const rtdEvent = eventsSoFar.find(event => event.event_type === 'rtd');
        
        if (kiaEvent) {
          // POI gets all KIAs that happen before Role1 (including at POI)
          const facilityAtDeath = kiaEvent.facility as FacilityName || 'POI';
          
          // Check if patient ever reached Role1 before dying
          const role1Event = eventsSoFar.find(event => 
            event.facility === 'Role1' && event.hours_since_injury < kiaEvent.hours_since_injury
          );
          
          if (!role1Event || facilityAtDeath === 'POI') {
            // Patient died before reaching Role1, or died at POI - count as POI KIA
            counts.POI.kia++;
          } else {
            // Patient died at specific facility after reaching Role1
            if (counts[facilityAtDeath]) {
              counts[facilityAtDeath].kia++;
            }
          }
        } else if (rtdEvent) {
          // RTD always goes to the facility where it happened
          const facilityAtRTD = rtdEvent.facility as FacilityName || 'POI';
          if (counts[facilityAtRTD]) {
            counts[facilityAtRTD].rtd++;
          }
        }
      }
    });

    return counts;
  }, [filteredPatients, playbackState.currentTime]);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 p-2">
        <div className="w-full px-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-gray-900">
              Patient Timeline Visualizer
            </h1>
            <p className="text-sm text-gray-600">
              Military Medical Evacuation Flow Simulator
            </p>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {patients.length === 0 ? (
          // File upload state
          <div className="flex-1 flex items-center justify-center">
            <div className="max-w-2xl w-full px-4">
              <FileUploader onLoad={handleLoadPatients} />
              
              {/* Instructions */}
              <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
                <h3 className="font-semibold text-blue-900 mb-3">How to use:</h3>
                <ol className="list-decimal list-inside space-y-2 text-blue-800 text-sm">
                  <li>Generate patient data from the main application</li>
                  <li>Download the patients.json file</li>
                  <li>Upload the file using the drag-and-drop area above</li>
                  <li>Use the timeline controls to visualize patient flow</li>
                  <li>Watch patients move through POI → Role1 → Role2 → Role3 → Role4</li>
                </ol>
              </div>
            </div>
          </div>
        ) : (
          // Timeline visualization
          <>
            {/* Statistics bar */}
            {statistics && (
              <div className="bg-white border-b border-gray-200 p-2">
                <div className="w-full px-4 flex items-center justify-between">
                  <div className="flex items-center space-x-4 text-sm">
                    <span className="font-medium">
                      Showing: {statistics.filtered}/{statistics.total}
                    </span>
                    <div className="flex space-x-2">
                      <span className="text-red-600">
                        KIA: {statistics.currentStatuses.KIA}
                      </span>
                      <span className="text-green-600">
                        RTD: {statistics.currentStatuses.RTD}
                      </span>
                      <span className="text-blue-600">
                        Active: {statistics.currentStatuses.Active}
                      </span>
                    </div>
                  </div>
                  <div className="flex space-x-2 text-sm">
                    <span className="bg-red-100 text-red-800 px-2 py-0.5 rounded">
                      T1: {statistics.triageCounts.T1 || 0}
                    </span>
                    <span className="bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                      T2: {statistics.triageCounts.T2 || 0}
                    </span>
                    <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded">
                      T3: {statistics.triageCounts.T3 || 0}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Filter bar */}
            <FilterBar
              patients={patients}
              filters={filters}
              onFilterChange={setFilters}
              onClearFilters={handleClearFilters}
            />

            {/* Facility columns */}
            <div className="flex-1 grid grid-cols-5 gap-2 p-2 overflow-hidden">
              <AnimatePresence>
                {FACILITIES.map((facility) => (
                  <FacilityColumn
                    key={facility}
                    name={facility}
                    patients={filteredPatients}
                    currentTime={playbackState.currentTime}
                    cumulativeCounts={(cumulativeCounts as any)[facility] || { kia: 0, rtd: 0 }}
                    className="h-full"
                  />
                ))}
              </AnimatePresence>
            </div>

            {/* Timeline controls */}
            <TimelineControls
              playbackState={playbackState}
              onPlayPause={handlePlayPause}
              onSpeedChange={handleSpeedChange}
              onReset={handleReset}
              onTimeSeek={handleTimeSeek}
              onLoopToggle={handleLoopToggle}
            />
          </>
        )}
      </main>
    </div>
  );
}

export default App;